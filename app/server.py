import hmac, json, math, re, os, secrets, signal, threading, time, uuid
from collections import defaultdict, deque
import logging
from smtplib import SMTPException
from pathlib import Path
from urllib.parse import urlsplit
from flask import Flask, request, jsonify, send_file, abort, make_response, g
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix
from .storage import Store, atomic
from .engine import Engine, validate_camera
from .updates import Updates
from .version import VERSION
from .revision import installed_revision
from .timelapse import latest_photo, photo_index, PHOTO_ID
from .recovery import Recovery, send_mail, smtp_settings, valid_email

PUBLIC_API = {
    '/api/state', '/api/login', '/api/setup', '/api/health',
    '/api/recovery/request', '/api/recovery/reset', '/api/recovery/verify',
}


def create_app(data=None, recordings=None, cache=None, start_engine=True):
    base=Path(__file__).resolve().parent.parent
    data=Path(data or os.getenv('DATA_DIR','/data'));recordings=Path(recordings or os.getenv('RECORDINGS_DIR','/recordings'));cache=Path(cache or os.getenv('CACHE_DIR','/cache'))
    app=Flask(__name__,static_folder=str(base/'static'),static_url_path='/static');app.config['MAX_CONTENT_LENGTH']=65536
    if os.getenv('TRUST_PROXY','false').lower()=='true':app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1,x_host=1)
    store=Store(data);engine=Engine(cache,recordings,os.getenv('FFMPEG','ffmpeg'),os.getenv('FFPROBE','ffprobe'))
    updates=Updates(os.getenv('UPDATES_DIR','/updates'))
    recovery=Recovery(store)
    sessions={};auth_lock=threading.RLock();write_lock=threading.Lock();attempts=defaultdict(deque)
    setup_file=data/'setup-token'
    if store.users():setup_file.unlink(missing_ok=True)
    app.extensions.update(store=store,engine=engine,sessions=sessions)
    def sync_cameras(cameras):
        engine.sync([{key: value for key, value in camera.items() if key != 'live_delay'}
                     for camera in cameras])

    if start_engine:sync_cameras(store.cameras())

    def session():
        token=request.cookies.get('dm_session','')
        with auth_lock:
            row=sessions.get(token)
            if row and row['expires']>time.time():
                user=store.user(user_id=row['user_id'])
                if user and user['enabled'] and user['version']==row['version']:
                    g.user=user
                    return token,row
            sessions.pop(token,None)
        return None,None

    def new_session(user):
        token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(24)
        with auth_lock:
            for key in list(sessions):
                if sessions[key]['expires']<time.time():del sessions[key]
            sessions[token]={'expires':time.time()+12*3600,'csrf':csrf,'user_id':user['id'],'version':user['version']}
        response=jsonify(ok=True,csrf=csrf,user=user)
        response.set_cookie('dm_session',token,max_age=43200,httponly=True,samesite='Strict',secure=os.getenv('COOKIE_SECURE','false').lower()=='true')
        return response

    def admin_only():
        if getattr(g,'user',{}).get('role')!='admin':abort(403)

    def can_camera(camera_id,live=False):
        user=g.user
        if live and user['role']=='playback':return False
        return user['role'] in ('admin','full') or user['all_cameras'] or camera_id in user['cameras']

    @app.before_request
    def security():
        if request.method not in ('GET','HEAD','OPTIONS'):
            if not request.is_json:abort(415)
            origin=request.headers.get('Origin')
            if origin and urlsplit(origin).netloc!=request.host:abort(403)
            if request.path not in PUBLIC_API:
                _,row=session()
                if not row:abort(401)
                if not hmac.compare_digest(request.headers.get('X-CSRF-Token',''),row['csrf']):abort(403)
        if request.path.startswith(('/api/','/live/','/recordings/')) and request.path not in PUBLIC_API:
            if not session()[1]:abort(401)

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options']='nosniff';response.headers['X-Frame-Options']='DENY';response.headers['Referrer-Policy']='same-origin'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self' blob:; worker-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'"
        response.headers['Cache-Control']='no-store'
        return response

    @app.errorhandler(Exception)
    def error(exc):
        if isinstance(exc,HTTPException):return jsonify(error=exc.name),exc.code
        if isinstance(exc,(ValueError,TypeError,KeyError)):return jsonify(error='Invalid settings'),400
        app.logger.error('Request failed (%s)',type(exc).__name__)
        return jsonify(error='Server error'),500

    @app.get('/')
    def index():return send_file(base/'static/index.html')

    @app.get('/api/health')
    def health():return jsonify(ok=True,version=VERSION,revision=installed_revision())

    @app.get('/api/updates')
    def update_status():
        admin_only();return jsonify(updates.status(check=request.args.get('check')=='1'))

    @app.post('/api/updates')
    def install_update():
        admin_only();return jsonify(updates.queue(request.get_json().get('tag'),request.get_json().get('revision'))),202

    @app.get('/api/state')
    def state():
        _,row=session()
        return jsonify(configured=bool(store.users()),authenticated=bool(row),csrf=row['csrf'] if row else None,user=g.user if row else None,email_recovery=bool(store.get('smtp',{}).get('enabled')))

    def rate_limit(scope='login'):
        bucket=(scope,request.remote_addr)
        with auth_lock:
            q=attempts[bucket];now=time.monotonic()
            while q and q[0]<now-60:q.popleft()
            if len(q)>=8:abort(429)
            q.append(now)

    @app.post('/api/setup')
    def setup():
        rate_limit();value=request.get_json()
        with write_lock:
            if store.users():abort(409)
            user=store.save_user(value,first=True);setup_file.unlink(missing_ok=True)
        return new_session(user)

    @app.post('/api/login')
    def login():
        rate_limit();value=request.get_json()
        password=value.get('password','')
        user=store.check_user(value.get('username',''),password)
        if not user:abort(401)
        return new_session(user)

    @app.post('/api/logout')
    def logout():
        with auth_lock:sessions.pop(session()[0],None)
        response=jsonify(ok=True);response.delete_cookie('dm_session');return response

    @app.post('/api/password')
    def password():
        rate_limit();value=request.get_json()
        with write_lock:
            current=g.user
            if not store.check_user(current['username'],value.get('old','')):abort(403)
            updated=store.save_user({**current,'password':value.get('password','')})
        return new_session(updated)

    def recovery_input():
        value = request.get_json()
        if not isinstance(value, dict):
            abort(400)
        return value

    def smtp_public(config):
        return {**{key: item for key, item in config.items() if key != 'password'},
                'has_password': bool(config.get('password'))}

    @app.get('/api/smtp')
    def get_smtp():
        admin_only()
        return jsonify(smtp_public(store.get('smtp', {})))

    @app.post('/api/smtp')
    def save_smtp():
        admin_only()
        with write_lock:
            config = smtp_settings(recovery_input(), store.get('smtp', {}))
            store.put('smtp', config)
        return jsonify(smtp_public(config))

    def deliver_mail(config, recipient, subject, message):
        try:
            send_mail(config, recipient, subject, message)
        except (OSError, SMTPException, ValueError):
            return jsonify(error='SMTP delivery failed. Check the server settings.'), 502
        return jsonify(ok=True)

    @app.post('/api/smtp/test')
    def test_smtp():
        admin_only()
        rate_limit('smtp-test')
        recipient = valid_email(recovery_input().get('recipient'))
        config = store.get('smtp', {})
        if not config.get('enabled'):
            abort(409)
        return deliver_mail(config, recipient, 'NVR Monitor SMTP test',
                            'NVR Monitor can send mail using the saved SMTP settings.')

    @app.get('/api/recovery')
    def get_recovery():
        config = store.get('smtp', {})
        return jsonify(**recovery.status(g.user['id']), email_available=bool(config.get('enabled')))

    @app.post('/api/recovery')
    def set_recovery():
        rate_limit('recovery-settings')
        value = recovery_input()
        action = value.get('action')
        with write_lock:
            user = store.check_user(g.user['username'], value.get('password'))
            if not user or user['id'] != g.user['id'] or user['version'] != g.user['version']:
                abort(403)
            if action in ('create_key', 'remove_key'):
                key = recovery.set_key(user['id'], action == 'create_key')
                return jsonify(ok=True, key=key)
            if action == 'remove_email':
                recovery.set_email(user['id'], None)
                return jsonify(ok=True)
            if action != 'verify_email':
                abort(400)
            config = store.get('smtp', {})
            if not config.get('enabled'):
                abort(409)
            email = valid_email(value.get('email'))
            token = recovery.set_email(user['id'], email)
        return deliver_mail(config, email, 'NVR Monitor recovery email',
                            f"Confirm your recovery email within 30 minutes: {config['base_url']}/#verify={token}")

    @app.post('/api/recovery/request')
    def request_reset():
        rate_limit('recovery-request')
        recovery.request_reset(recovery_input().get('username'), store.get('smtp', {}))
        return jsonify(ok=True), 202

    @app.post('/api/recovery/verify')
    def verify_recovery():
        rate_limit('recovery-verify')
        if not recovery.verify_email(recovery_input().get('token')):
            abort(400)
        return jsonify(ok=True)

    @app.post('/api/recovery/reset')
    def reset_password():
        rate_limit('recovery-reset')
        value = recovery_input()
        method = value.get('method')
        with write_lock:
            if method == 'email' and not store.get('smtp', {}).get('enabled'):
                abort(400)
            if not recovery.reset_password(value.get('token'), method, value.get('password'),
                                           value.get('username')):
                abort(400)
        response = jsonify(ok=True)
        response.delete_cookie('dm_session')
        return response

    @app.get('/api/users')
    def users():
        admin_only();return jsonify(store.users())

    @app.post('/api/users')
    def save_user():
        admin_only()
        try:
            with write_lock:user=store.save_user(request.get_json())
        except ValueError as exc:return jsonify(error=str(exc)),400
        return new_session(user) if user['id']==g.user['id'] else jsonify(ok=True,user=user)

    @app.post('/api/users/<user_id>/delete')
    def delete_user(user_id):
        admin_only()
        if user_id==g.user['id']:abort(400)
        with write_lock:store.delete_user(user_id)
        return jsonify(ok=True)

    @app.get('/api/cameras')
    def cameras():
        out=[]
        for c in store.cameras():
            if not can_camera(c['id']):continue
            w=engine.workers.get(c['id']);listener=w.onvif if w else None
            admin = g.user['role'] == 'admin'
            visible={k:v for k,v in c.items() if k not in ('password','onvif_password','rtsp_url')} if admin else {k:c[k] for k in ('id','name','enabled')}
            visible['live_delay'] = c.get('live_delay', 0)
            if admin:
                visible['has_rtsp_url'] = bool(c.get('rtsp_url'))
            out.append({**visible,'has_password':bool(c['password']) if g.user['role']=='admin' else False,'has_onvif_password':bool(c.get('onvif_password')) if g.user['role']=='admin' else False,'detection_mode':w.detection_mode if w else 'disabled','video_mode':('copy' if w.video_copy else 'transcode') if w else 'disabled','source_video':w.source_video if w else {},'onvif_status':listener.snapshot()['status'] if listener else None,'status':w.status if w else 'disabled','error':w.error if w else None,'photo_error':w.photos.error if w else None,'last_photo':w.photos.last_saved if w else None})
        return jsonify(out)

    @app.post('/api/cameras')
    def save_camera():
        admin_only()
        value=request.get_json()
        with write_lock:
            cameras=store.cameras();old=next((c for c in cameras if c['id']==value.get('id')),None)
            if old and 'password' not in value:value['password']=old['password']
            if old and 'onvif_password' not in value:value['onvif_password']=old.get('onvif_password','')
            if old:
                for key in ('live_delay','timelapse','timelapse_interval','timelapse_max_days','timelapse_max_mb'):
                    if key not in value and key in old:value[key]=old[key]
                if 'rtsp_url' in old:
                    value.setdefault('rtsp_url', old['rtsp_url'])
                if 'rtsp_preset' in old:
                    value.setdefault('rtsp_preset', old['rtsp_preset'])
                if value.get('rtsp_url'):
                    for key in ('username','channel','subtype'):
                        value.setdefault(key, old[key])
            camera=validate_camera(value)
            if not old and len(cameras)>=32:abort(400)
            updated=[camera if c['id']==camera['id'] else c for c in cameras] if old else cameras+[camera]
            store.put('cameras',updated)
            if start_engine:sync_cameras(updated)
        return jsonify(ok=True,id=camera['id'])

    @app.post('/api/cameras/order')
    def camera_order():
        admin_only();ids=request.get_json().get('ids')
        if not isinstance(ids,list) or not all(isinstance(i,str) for i in ids) or len(ids)!=len(set(ids)):abort(400)
        with write_lock:
            current=store.cameras();by_id={c['id']:c for c in current}
            if set(ids)!=set(by_id):abort(409)
            if ids!=[c['id'] for c in current]:store.put('cameras',[by_id[i] for i in ids])
        # A visual-order change must not stop producers, detectors or exports.
        return jsonify(ok=True,ids=ids)

    @app.post('/api/cameras/<camera_id>/delete')
    def delete_camera(camera_id):
        admin_only()
        with write_lock:
            updated=[c for c in store.cameras() if c['id']!=camera_id];store.put('cameras',updated)
            if start_engine:sync_cameras(updated)
        return jsonify(ok=True)

    @app.get('/live/<camera_id>/<filename>')
    def live(camera_id,filename):
        if not can_camera(camera_id,live=True):abort(403)
        if not (filename in ('live.m3u8','init.mp4') or __import__('re').fullmatch(r'segment\d{9}\.m4s',filename)):abort(404)
        w=engine.workers.get(camera_id)
        if not w or not w.session:abort(404)
        path=w.session/filename
        if not path.is_file():abort(404)
        return send_file(path,mimetype='application/vnd.apple.mpegurl' if filename.endswith('m3u8') else 'video/mp4',conditional=True)

    @app.get('/api/timelapse/dashboard')
    def photo_dashboard():
        tiles = []
        for camera in store.cameras():
            if can_camera(camera['id']):
                tiles.append({
                    'id': camera['id'],
                    'name': camera['name'],
                    'preview': latest_photo(recordings, camera['id']),
                })
        return jsonify(tiles)

    @app.get('/api/timelapse')
    def photos():
        camera_id=request.args.get('camera')
        if camera_id:
            uuid.UUID(camera_id)
            if not can_camera(camera_id):abort(403)
        start=float(request.args.get('from',time.time()-86400));end=float(request.args.get('to',time.time()+1))
        limit=int(request.args.get('limit',100));before=request.args.get('before')
        if not all(math.isfinite(v) and 0<=v<=253402214400 for v in (start,end)) or not 0<end-start<=3*86400 or not 1<=limit<=100:abort(400)
        if before and not PHOTO_ID.fullmatch(before):abort(400)
        rows=[]
        for m in photo_index(recordings,start,end,camera_id):
            if not can_camera(m['camera_id']) or (before and m['id']>=before):continue
            rows.append(m)
            if len(rows)>limit:break
        more=len(rows)>limit;rows=rows[:limit]
        return jsonify(photos=rows,next_cursor=rows[-1]['id'] if more else None)

    @app.get('/recordings/timelapse/<camera_id>/<day>/<photo_id>.jpg')
    def photo(camera_id,day,photo_id):
        uuid.UUID(camera_id)
        if not can_camera(camera_id):abort(403)
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',day) or not PHOTO_ID.fullmatch(photo_id):abort(404)
        thumb=request.args.get('thumb')=='1' and request.args.get('download')!='1'
        folder=recordings/'timelapse'/camera_id/day;path=folder/(photo_id+('.thumb.jpg' if thumb else '.jpg'))
        if not path.is_file() or not (folder/(photo_id+'.json')).is_file():abort(404)
        try:return send_file(path,mimetype='image/jpeg',conditional=True,as_attachment=request.args.get('download')=='1',download_name=day+'_'+photo_id+'.jpg')
        except FileNotFoundError:abort(404)

    def clip_index():
        for p in recordings.glob('*/*/*.json'):
            try:
                m=json.loads(p.read_text());uuid.UUID(m['id']);uuid.UUID(m['camera_id'])
                if p.with_suffix('.mp4').is_file():yield m,p
            except (OSError,ValueError,KeyError):continue

    @app.get('/api/recordings')
    def clips():
        camera_id=request.args.get('camera');start=float(request.args.get('from',0));end=float(request.args.get('to',time.time()+86400))
        if camera_id and not can_camera(camera_id):abort(403)
        include_previews = request.args.get('previews') == '1'
        camera_ids = {c['id'] for c in store.cameras()} if include_previews else set()
        previews = {}
        rows = []
        for clip, _ in clip_index():
            cid = clip['camera_id']
            if not can_camera(cid):
                continue
            if cid in camera_ids and (cid not in previews or clip['start'] > previews[cid]['start']):
                previews[cid] = clip
            if (not camera_id or cid == camera_id) and clip['start'] < end and clip['start'] + clip['duration'] >= start:
                rows.append(clip)
        rows = sorted(rows, key=lambda clip: clip['start'], reverse=True)[:2000]
        if include_previews:
            return jsonify(clips=rows, previews={cid: clip['id'] for cid, clip in previews.items()})
        return jsonify(rows)

    @app.get('/recordings/<clip_id>.mp4')
    def video(clip_id):
        for m,p in clip_index():
            if m['id']==clip_id and can_camera(m['camera_id']):return send_file(p.with_suffix('.mp4'),mimetype='video/mp4',conditional=True,as_attachment=request.args.get('download')=='1',download_name=time.strftime('%Y-%m-%d_%H-%M-%S',time.localtime(m['start']))+'.mp4')
        abort(404)

    return app


def main():
    from waitress.server import create_server

    logging.basicConfig()
    os.umask(0o077)
    app = create_app()

    def shutdown(*_):
        # Let Waitress stop accepting requests and begin draining its workers.
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        raise SystemExit(0)

    try:
        server = create_server(
            app, host='0.0.0.0', port=int(os.getenv('PORT','8080')), threads=16,
            max_request_body_size=65536,
            clear_untrusted_proxy_headers=os.getenv('TRUST_PROXY','false').lower()!='true',
        )
        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGINT, shutdown)
        server.print_listen("Serving on http://{}:{}")
        try:
            server.run()
        finally:
            # Requests can outlast Waitress's default five-second drain.
            server.task_dispatcher.shutdown(timeout=float('inf'))
            server.close()
    finally:
        try:
            app.extensions['engine'].close()
        finally:
            app.extensions['store'].close()

if __name__=='__main__':main()
