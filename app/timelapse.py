"""Motion-triggered JPEG archive, bounded capture jobs and per-camera retention."""
import datetime, json, os, queue, re, shutil, subprocess, threading, time, uuid
from pathlib import Path
import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from requests.utils import parse_dict_header
from .storage import atomic

MAX_JPEG=12*1024*1024
PHOTO_ID=re.compile(r'\d{13,16}-[0-9a-f]{32}')

def camera_jpeg(camera):
    host=camera['host'];host='['+host+']' if ':' in host else host
    url='http://'+host+':'+str(camera.get('onvif_port',80))+'/cgi-bin/snapshot.cgi?channel='+str(camera['channel'])
    with requests.Session() as session:
        session.trust_env=False;headers={'Connection':'close'}
        # Some older firmware never terminates its 401 body. Close it without
        # consuming it, then construct Digest authentication for the exact URL.
        with session.get(url,headers=headers,stream=True,allow_redirects=False,timeout=(3,5)) as response:
            if response.status_code==401:
                challenge=response.headers.get('WWW-Authenticate','')
            else:
                response.raise_for_status();return read_jpeg(response)
        auth=HTTPDigestAuth(camera['username'],camera['password'])
        if challenge.lower().startswith('digest '):
            auth.init_per_thread_state();auth._thread_local.chal=parse_dict_header(challenge[7:])
            headers['Authorization']=auth.build_digest_header('GET',requests.Request('GET',url).prepare().url)
        elif challenge.lower().startswith('basic '):
            prepared=requests.Request('GET',url).prepare();HTTPBasicAuth(camera['username'],camera['password'])(prepared)
            headers['Authorization']=prepared.headers['Authorization']
        else:raise ValueError('Unsupported snapshot authentication')
        with session.get(url,headers=headers,stream=True,allow_redirects=False,timeout=(3,5)) as response:
            response.raise_for_status();return read_jpeg(response)

def read_jpeg(response):
    chunks=[];total=0;deadline=time.monotonic()+10
    for chunk in response.iter_content(65536):
        total+=len(chunk)
        if total>MAX_JPEG or time.monotonic()>deadline:raise ValueError('Snapshot exceeds limit')
        chunks.append(chunk)
    data=b''.join(chunks)
    if not valid_jpeg(data):raise ValueError('Not a JPEG')
    return data

def valid_jpeg(data):return 4<=len(data)<=MAX_JPEG and data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9')

class PhotoArchive:
    def __init__(self,recordings,camera):
        self.root=Path(recordings)/'timelapse'/camera['id'];self.camera=camera;self.lock=threading.RLock();self.rows=None;self.scanned=0
    def save(self,jpeg,thumbnail,captured,method):
        if not valid_jpeg(jpeg) or not valid_jpeg(thumbnail):raise ValueError('Invalid JPEG')
        name=f'{int(captured*1000):013d}-'+uuid.uuid4().hex
        day=time.strftime('%Y-%m-%d',time.localtime(captured));folder=self.root/day;folder.mkdir(parents=True,mode=0o700,exist_ok=True)
        meta={'id':name,'camera_id':self.camera['id'],'camera_name':self.camera['name'],'start':captured,'day':day,'bytes':len(jpeg),'method':method}
        with self.lock:
            try:
                atomic(folder/(name+'.jpg'),jpeg);atomic(folder/(name+'.thumb.jpg'),thumbnail)
                metadata=json.dumps(meta).encode();atomic(folder/(name+'.json'),metadata)
                if self.rows is not None:self.rows.append((captured,len(jpeg)+len(thumbnail)+len(metadata),[folder/(name+suffix) for suffix in ('.jpg','.thumb.jpg','.json')]))
            except Exception:
                for suffix in ('.jpg','.thumb.jpg','.json'):(folder/(name+suffix)).unlink(missing_ok=True)
                raise
            self.prune()
        return meta
    def prune(self):
        with self.lock:
            now=time.time()
            if self.rows is None or now-self.scanned>=60:
                rows=[]
                for day in self.root.glob('????-??-??'):
                    if not day.is_dir():continue
                    for image in day.glob('*.jpg'):
                        if image.name.endswith('.thumb.jpg') or not PHOTO_ID.fullmatch(image.stem):continue
                        try:
                            captured=int(image.stem.split('-')[0])/1000
                            paths=[image,image.with_name(image.stem+'.thumb.jpg'),image.with_suffix('.json')]
                            size=sum(p.stat().st_size for p in paths if p.exists());rows.append((captured,size,paths))
                        except OSError:continue
                self.rows=rows;self.scanned=now
            rows=self.rows
            rows.sort(key=lambda r:r[0]);total=sum(r[1] for r in rows)
            cutoff=now-self.camera.get('timelapse_max_days',30)*86400;limit=self.camera.get('timelapse_max_mb',1024)*1024**2
            kept=[]
            for captured,size,paths in rows:
                if captured<cutoff or total>limit:
                    for p in paths:p.unlink(missing_ok=True)
                    total-=size
                else:kept.append((captured,size,paths))
            self.rows=kept
            for day in self.root.glob('????-??-??'):
                try:day.rmdir()
                except OSError:pass

def photo_index(recordings,start,end,camera=None):
    root=Path(recordings)/'timelapse'
    days={time.strftime('%Y-%m-%d',time.localtime(t)) for t in (start-86400,start,start+86400,end,end+86400)}
    cameras=[root/camera] if camera else list(root.glob('*'))
    candidates=[]
    for folder in cameras:
        try:uuid.UUID(folder.name)
        except ValueError:continue
        for day in days:candidates.extend((folder/day).glob('*.json'))
    # Timestamp-prefixed filenames permit newest-first pagination without
    # opening every old metadata file on every gallery request.
    for p in sorted(candidates,key=lambda p:p.name,reverse=True):
        try:
            if not PHOTO_ID.fullmatch(p.stem):continue
            m=json.loads(p.read_text());uuid.UUID(m['camera_id'])
            if m['id']!=p.stem or m['camera_id']!=p.parent.parent.name or m['day']!=p.parent.name:continue
            if start<=m['start']<end and p.with_suffix('.jpg').is_file():yield m
        except (OSError,ValueError,KeyError,TypeError):continue

class Snapshotter:
    def __init__(self,camera,recordings,ffmpeg='ffmpeg',synthetic=False):
        self.camera=camera;self.archive=PhotoArchive(recordings,camera);self.ffmpeg=ffmpeg
        self.direct_snapshot = not synthetic and not camera.get('rtsp_url') and camera.get('rtsp_preset', 'dahua') == 'dahua'
        self.jobs=queue.Queue(maxsize=1);self.thread=None;self.next_due=0;self.busy=False;self.lock=threading.Lock()
        self.http_retry=0;self.error=None;self.last_saved=None
    def schedule(self,session,segments):
        if not self.camera.get('timelapse',False):return
        with self.lock:
            now=time.monotonic()
            if self.busy or now<self.next_due:return
            stage=None
            try:
                if segments:
                    item=max(segments.values(),key=lambda s:s['start'])
                    stage=Path(session)/('photo-'+uuid.uuid4().hex);stage.mkdir(mode=0o700)
                    for src,dst in [(Path(session)/'init.mp4',stage/'init.mp4'),(item['path'],stage/'part.m4s')]:
                        try:os.link(src,dst)
                        except OSError:shutil.copyfile(src,dst)
                self.jobs.put_nowait(stage);self.busy=True;self.next_due=now+self.camera.get('timelapse_interval',10)
                if not self.thread:
                    self.thread=threading.Thread(target=self.run,daemon=True,name='photos-'+self.camera['id']);self.thread.start()
            except (OSError,queue.Full):
                if stage:shutil.rmtree(stage,ignore_errors=True)
                self.error='snapshot_failed'
    def fallback(self,stage):
        if not stage:raise ValueError('Video buffer not ready')
        joined=stage/'frame.mp4'
        with joined.open('wb') as out:
            for p in (stage/'init.mp4',stage/'part.m4s'):
                with p.open('rb') as src:shutil.copyfileobj(src,out)
        # Only decode a keyframe from the newest completed HLS segment.
        result=subprocess.run([self.ffmpeg,'-v','error','-threads','1','-skip_frame','nokey','-i',str(joined),'-an','-frames:v','1','-c:v','mjpeg','-threads','1','-q:v','3','-f','image2pipe','pipe:1'],capture_output=True,check=True,timeout=12)
        if not valid_jpeg(result.stdout):raise ValueError('No snapshot frame')
        return result.stdout
    def thumbnail(self,jpeg):
        result=subprocess.run([self.ffmpeg,'-v','error','-threads','1','-i','pipe:0','-vf',"scale=w='min(480,iw)':h=-2",'-frames:v','1','-c:v','mjpeg','-threads','1','-q:v','6','-f','image2pipe','pipe:1'],input=jpeg,capture_output=True,check=True,timeout=8)
        return result.stdout
    def run(self):
        while True:
            stage=self.jobs.get()
            if stage is False:self.jobs.task_done();return
            try:
                jpeg=None;method='stream'
                if self.direct_snapshot and time.monotonic()>=self.http_retry:
                    try:jpeg=camera_jpeg(self.camera);method='camera'
                    except Exception:self.http_retry=time.monotonic()+300
                if jpeg is None:jpeg=self.fallback(stage)
                captured=time.time();thumb=self.thumbnail(jpeg)
                self.archive.save(jpeg,thumb,captured,method);self.last_saved=captured;self.error=None
            except Exception:self.error='snapshot_failed'
            finally:
                if stage:shutil.rmtree(stage,ignore_errors=True)
                with self.lock:self.busy=False
                self.jobs.task_done()
    def close(self):
        if self.thread:self.jobs.join();self.jobs.put(False);self.thread.join(timeout=2)
