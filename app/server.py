import hmac, json, os, secrets, signal, threading, time, uuid
from collections import defaultdict, deque
from pathlib import Path
from urllib.parse import urlsplit
from flask import Flask, request, jsonify, send_file, abort, make_response, g
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix
from .storage import Store, atomic
from .engine import Engine, validate_camera
from .updates import Updates
from .version import VERSION


def create_app(data=None, recordings=None, cache=None, start_engine=True):
    base=Path(__file__).resolve().parent.parent
    data=Path(data or os.getenv('DATA_DIR','/data'));recordings=Path(recordings or os.getenv('RECORDINGS_DIR','/recordings'));cache=Path(cache or os.getenv('CACHE_DIR','/cache'))
    app=Flask(__name__,static_folder=str(base/'static'),static_url_path='/static');app.config['MAX_CONTENT_LENGTH']=65536
    if os.getenv('TRUST_PROXY','false').lower()=='true':app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1,x_host=1)
    store=Store(data);engine=Engine(cache,recordings,os.getenv('FFMPEG','ffmpeg'),os.getenv('FFPROBE','ffprobe'))
    updates=Updates(os.getenv('UPDATES_DIR','/updates'))
    sessions={};auth_lock=threading.RLock();write_lock=threading.Lock();attempts=defaultdict(deque)
    setup_file=data/'setup-token'
    if store.users():setup_file.unlink(missing_ok=True)
    app.extensions.update(store=store,engine=engine,sessions=sessions)
    if start_engine:engine.sync(store.cameras())

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
            if request.path not in ('/api/login','/api/setup'):
                _,row=session()
                if not row:abort(401)
                if not hmac.compare_digest(request.headers.get('X-CSRF-Token',''),row['csrf']):abort(403)
        if request.path.startswith(('/api/','/live/','/recordings/')) and request.path not in ('/api/state','/api/login','/api/setup','/api/health'):
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
    def health():return jsonify(ok=True,version=VERSION)

    @app.get('/api/updates')
    def update_status():
        admin_only();return jsonify(updates.status(check=request.args.get('check')=='1'))

    @app.post('/api/updates')
    def install_update():
        admin_only();return jsonify(updates.queue(request.get_json().get('tag'))),202

    def viewing_preferences():
        return store.get('viewing',{'live_delay':max(0,min(60,int(os.getenv('LIVE_DELAY_SECONDS','30'))))})

    @app.get('/api/preferences')
    def preferences():return jsonify(viewing_preferences())

    @app.post('/api/preferences')
    def set_preferences():
        admin_only();delay=request.get_json().get('live_delay')
        if isinstance(delay,bool) or not isinstance(delay,int) or not 0<=delay<=60:abort(400)
        store.put('viewing',{'live_delay':delay})
        return jsonify(live_delay=delay)

    @app.get('/api/state')
    def state():
        _,row=session()
        return jsonify(configured=bool(store.users()),authenticated=bool(row),csrf=row['csrf'] if row else None,user=g.user if row else None,live_delay=viewing_preferences()['live_delay'])

    def rate_limit():
        ip=request.remote_addr
        with auth_lock:
            q=attempts[ip];now=time.monotonic()
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
            visible={k:v for k,v in c.items() if k not in ('password','onvif_password')} if g.user['role']=='admin' else {k:c[k] for k in ('id','name','enabled')}
            out.append({**visible,'has_password':bool(c['password']) if g.user['role']=='admin' else False,'has_onvif_password':bool(c.get('onvif_password')) if g.user['role']=='admin' else False,'detection_mode':w.detection_mode if w else 'disabled','video_mode':('copy' if w.video_copy else 'transcode') if w else 'disabled','source_video':w.source_video if w else {},'onvif_status':listener.snapshot()['status'] if listener else None,'status':w.status if w else 'disabled','error':w.error if w else None})
        return jsonify(out)

    @app.post('/api/cameras')
    def save_camera():
        admin_only()
        value=request.get_json()
        with write_lock:
            cameras=store.cameras();old=next((c for c in cameras if c['id']==value.get('id')),None)
            if old and 'password' not in value:value['password']=old['password']
            if old and 'onvif_password' not in value:value['onvif_password']=old.get('onvif_password','')
            camera=validate_camera(value)
            if not old and len(cameras)>=32:abort(400)
            updated=[c for c in cameras if c['id']!=camera['id']]+[camera]
            store.put('cameras',updated)
            if start_engine:engine.sync(updated)
        return jsonify(ok=True,id=camera['id'])

    @app.post('/api/cameras/<camera_id>/delete')
    def delete_camera(camera_id):
        admin_only()
        with write_lock:
            updated=[c for c in store.cameras() if c['id']!=camera_id];store.put('cameras',updated)
            if start_engine:engine.sync(updated)
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
        rows=[m for m,p in clip_index() if can_camera(m['camera_id']) and (not camera_id or m['camera_id']==camera_id) and m['start']<end and m['start']+m['duration']>=start]
        return jsonify(sorted(rows,key=lambda x:x['start'],reverse=True)[:2000])

    @app.get('/recordings/<clip_id>.mp4')
    def video(clip_id):
        for m,p in clip_index():
            if m['id']==clip_id and can_camera(m['camera_id']):return send_file(p.with_suffix('.mp4'),mimetype='video/mp4',conditional=True,as_attachment=request.args.get('download')=='1',download_name=time.strftime('%Y-%m-%d_%H-%M-%S',time.localtime(m['start']))+'.mp4')
        abort(404)

    return app


def main():
    from waitress import serve
    os.umask(0o077);app=create_app()
    def shutdown(*_):
        app.extensions['engine'].close();os._exit(0)
    signal.signal(signal.SIGTERM,shutdown);signal.signal(signal.SIGINT,shutdown)
    serve(app,host='0.0.0.0',port=int(os.getenv('PORT','8080')),threads=16,max_request_body_size=65536,clear_untrusted_proxy_headers=os.getenv('TRUST_PROXY','false').lower()!='true')

if __name__=='__main__':main()
