"""Independent camera workers: HLS, motion detection, disk pre-roll and event MP4."""
import collections, json, math, os, queue, re, shutil, signal, subprocess, threading, time, uuid
from pathlib import Path
from urllib.parse import quote, urlsplit
from .storage import atomic
from .onvif import Events
from .timelapse import Snapshotter

WIDTH, HEIGHT, FPS = 160, 90, 3
RTSP_PRESETS = {
    'dahua': lambda channel, subtype: f'/cam/realmonitor?channel={channel}&subtype={subtype}',
    'hikvision': lambda channel, subtype: f'/Streaming/Channels/{channel}{subtype + 1:02d}',
    'reolink': lambda channel, subtype: f'/Preview_{channel:02d}_{"sub" if subtype else "main"}',
    'tp_link': lambda channel, subtype: f'/stream{subtype + 1}',
    'axis': lambda channel, subtype: '/axis-media/media.amp?videocodec=h264',
    'hanwha': lambda channel, subtype: f'/profile{channel}/media.smp',
    'bosch': lambda channel, subtype: f'/?inst={subtype + 1}&h26x=4',
    'avigilon': lambda channel, subtype: '/defaultPrimary?streamType=u',
    'pelco': lambda channel, subtype: '/live.sdp',
    'uniview': lambda channel, subtype: f'/media/video{subtype + 1}',
}

RTSP_MODELS = {
    'axis-p3267-lve': 'axis',
    'hanwha-qnv-c8083r': 'hanwha',
    'hanwha-qnv-c6083r': 'hanwha',
    'hikvision-ds-2td2628-10-qa': 'hikvision',
    'bosch-nde-5702-a': 'bosch',
    'axis-p3265-lve-9mm': 'axis',
    'axis-p3265-lv': 'axis',
    'axis-p1455-le-9mm': 'axis',
    'axis-m3216-lve': 'axis',
    'axis-m3086-v': 'axis',
}
RTSP_FAMILIES = {**RTSP_MODELS, 'intelbras': 'dahua'}
SINGLE_STREAM_FAMILIES = {'axis', 'hanwha', 'avigilon', 'pelco'}


def rtsp_family(preset):
    return RTSP_FAMILIES.get(preset, preset)


def parse_rtsp_url(value):
    if (not isinstance(value, str) or not 1 <= len(value) <= 4096 or
            re.search(r'[^\x21-\x7e]|[\\#]|%(?![0-9A-Fa-f]{2})', value)):
        raise ValueError('Invalid RTSP URL')
    try:
        url = urlsplit(value)
        port = url.port
    except ValueError:
        raise ValueError('Invalid RTSP URL') from None
    authority = url.netloc.rsplit('@', 1)[-1]
    if (url.scheme != 'rtsp' or not url.hostname or len(url.hostname) > 253 or port == 0 or
            url.netloc.count('@') > 1 or
            not re.fullmatch(r'(?:\[[0-9A-Fa-f:]+\]|[A-Za-z0-9.-]+)(?::[0-9]+)?', authority)):
        raise ValueError('Invalid RTSP URL')
    return url


def validate_camera(value):
    c = dict(value)
    c['id'] = str(uuid.UUID(c.get('id', str(uuid.uuid4()))))
    c['name'] = str(c.get('name','Camera')).strip()[:80] or 'Camera'
    rtsp_url = c.get('rtsp_url', '')
    preset = c.get('rtsp_preset', 'dahua')
    if not isinstance(preset, str) or rtsp_family(preset) not in RTSP_PRESETS:
        raise ValueError('Invalid RTSP preset')
    if rtsp_url != '':
        url = parse_rtsp_url(rtsp_url)
        c['host'] = url.hostname
        c['port'] = url.port or 554
    family = rtsp_family(preset)
    if not rtsp_url:
        if family == 'hanwha':
            c.setdefault('channel', 2)
        if preset in RTSP_MODELS:
            c.setdefault('motion_source', 'onvif')
            c.setdefault('onvif_use_camera_credentials', family not in ('axis', 'hikvision'))
    host = str(c.get('host','')).strip()
    if not host or len(host)>253 or not re.fullmatch(r'[A-Za-z0-9.:-]+',host): raise ValueError('Invalid host')
    c['host'] = host
    delay = c.get('live_delay', 0)
    if type(delay) is not int or not 0 <= delay <= 60:
        raise ValueError('Invalid live_delay')
    c['live_delay'] = delay
    for key, default, lo, hi in [('timelapse_interval',10,2,3600),('timelapse_max_days',30,1,3650),('timelapse_max_mb',1024,1,1000000),('onvif_port',80,1,65535),('port',554,1,65535),('channel',1,1,64),('subtype',0,0,1),('sensitivity',55,1,100),('prebuffer',5,0,30),('tail',10,5,300),('max_days',30,1,3650),('max_gb',20,1,10000)]:
        n = int(c.get(key,default))
        if not lo <= n <= hi: raise ValueError('Invalid '+key)
        c[key] = n
    for key in ['username','password','onvif_username','onvif_password']:
        c[key] = str(c.get(key,''))
        if len(c[key])>512: raise ValueError('Credential too long')
    c['enabled'] = bool(c.get('enabled',True)); c['motion'] = bool(c.get('motion',False))
    c['timelapse']=bool(c.get('timelapse',False))
    c['folder'] = str(c.get('folder','')).strip()
    if c['folder'] and not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',c['folder']): raise ValueError('Folder: letters, digits, underscore or dash only')
    zone = c.get('zone',[0,0,1,1])
    if not isinstance(zone,list) or len(zone)!=4: raise ValueError('Invalid zone')
    x,y,w,h = map(float,zone)
    if not all(math.isfinite(v) for v in (x,y,w,h)) or min(x,y)<0 or min(w,h)<.02 or x+w>1.001 or y+h>1.001: raise ValueError('Invalid zone')
    c['zone']=[x,y,w,h]
    c['motion_source']=c.get('motion_source','rtsp')
    c['onvif_soap']=c.get('onvif_soap','auto')
    if c['motion_source'] not in ('rtsp','onvif') or c['onvif_soap'] not in ('auto','1.1','1.2'):raise ValueError('Invalid ONVIF mode')
    c['onvif_fallback']=bool(c.get('onvif_fallback',True))
    c['onvif_use_camera_credentials']=bool(c.get('onvif_use_camera_credentials',True))
    validated = {k:c[k] for k in ['live_delay','timelapse','timelapse_interval','timelapse_max_days','timelapse_max_mb','id','name','host','port','channel','subtype','username','password','enabled','motion','sensitivity','prebuffer','tail','max_days','max_gb','folder','zone','motion_source','onvif_port','onvif_soap','onvif_fallback','onvif_use_camera_credentials','onvif_username','onvif_password']}
    if rtsp_url:
        # Preserve the original escaped credentials, path and query.
        validated['rtsp_url'] = 'rtsp:' + rtsp_url.partition(':')[2]
    elif preset != 'dahua':
        validated['rtsp_preset'] = preset
    return validated


def input_args(camera):
    url = camera.get('rtsp_url')
    if not url:
        host=camera['host']; host='['+host+']' if ':' in host else host
        path = RTSP_PRESETS[rtsp_family(camera.get('rtsp_preset', 'dahua'))](camera['channel'], camera['subtype'])
        username = quote(camera['username'], safe='')
        password = quote(camera['password'], safe='')
        url = f"rtsp://{username}:{password}@{host}:{camera['port']}{path}"
    return ['-rtsp_transport','tcp','-timeout','15000000','-i',url]


def detect(previous, frame, zone, sensitivity):
    if previous is None: return False
    x,y,w,h=zone; x0=int(x*WIDTH);x1=min(WIDTH,max(x0+1,int((x+w)*WIDTH)));y0=int(y*HEIGHT);y1=min(HEIGHT,max(y0+1,int((y+h)*HEIGHT)))
    # Ignore tiny sensor noise. Higher sensitivity lowers changed-pixel percentage.
    changed=sum(abs(frame[i]-previous[i])>=18 for row in range(y0,y1) for i in range(row*WIDTH+x0,row*WIDTH+x1))
    return changed/max(1,(x1-x0)*(y1-y0)) >= .005 + (100-sensitivity)*.0015


def stop_process(p):
    if p and p.poll() is None:
        p.send_signal(signal.SIGINT)
        try:p.wait(timeout=8)
        except subprocess.TimeoutExpired:
            p.kill();p.wait(timeout=3)


class CameraWorker(threading.Thread):
    def __init__(self, camera, cache, recordings, ffmpeg='ffmpeg', ffprobe='ffprobe', source=None):
        super().__init__(daemon=True,name='camera-'+camera['id'])
        self.camera=camera;self.cache=Path(cache)/camera['id'];self.recordings=Path(recordings);self.ffmpeg=ffmpeg;self.ffprobe=ffprobe;self.source=source
        self.onvif=None;self.detection_mode='disabled';self.detector_retry=0;self.detector_warmup=0
        self.quit=threading.Event();self.producer=None;self.detector=None;self.frames=queue.Queue(maxsize=2);self.status='connecting';self.error=None
        self.source_video={}
        self.photos=Snapshotter(camera,recordings,ffmpeg,synthetic=source is not None)
        self.force_transcode=(Path(cache)/(camera['id']+'.force-transcode')).exists();self.video_copy=False;self.event=None;self.segments={};self.session=None;self.latest_frame=0;self.active_path=None
        self.exports=queue.Queue(maxsize=8);self.export_thread=threading.Thread(target=self.export_loop,daemon=True);self.export_thread.start()

    def spawn(self,args,**kw):
        return subprocess.Popen([self.ffmpeg,'-hide_banner','-loglevel','error','-nostdin','-threads','2','-filter_threads','1']+args,stdin=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**kw)

    def start_stream(self):
        self.session=self.cache/uuid.uuid4().hex;self.session.mkdir(parents=True,mode=0o700)
        if (self.camera['motion'] or self.camera.get('timelapse',False)) and self.camera.get('motion_source','rtsp')=='onvif':
            self.onvif=Events(self.camera);self.onvif.start()
        args=self.source if self.source else input_args(self.camera)
        # Probe presence of audio; provide silent AAC for cameras with no microphone.
        probe_args=[self.ffprobe,'-v','error','-analyzeduration','1000000','-probesize','1000000']+args+['-show_entries','stream=codec_type,codec_name,pix_fmt,width,height,r_frame_rate','-of','json']
        # ffprobe has no -re or -stream_loop; synthetic test inputs use the actual file.
        if self.source: probe_args=[self.ffprobe,'-v','error','-i',self.source[-1],'-show_entries','stream=codec_type,codec_name,pix_fmt,width,height,r_frame_rate','-of','json']
        copy_video=False
        try:
            probe=subprocess.run(probe_args,capture_output=True,timeout=20,check=True)
            streams=json.loads(probe.stdout)['streams']
            audio=any(s.get('codec_type')=='audio' for s in streams)
            video=next((s for s in streams if s.get('codec_type')=='video'),{})
            self.source_video={k:video.get(k) for k in ('codec_name','width','height','r_frame_rate')}
            copy_video=not self.force_transcode and video.get('codec_name')=='h264' and video.get('pix_fmt') in ('yuv420p','yuvj420p')
        except Exception: audio=True
        silence=[] if audio else ['-re','-f','lavfi','-i','anullsrc=r=48000:cl=mono']
        self.video_copy=copy_video
        video_options=['-c:v','copy','-tag:v','avc1'] if copy_video else ['-vf',"scale=w='min(1280,iw)':h='min(720,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2,fps=15",'-c:v','libx264','-threads','2','-maxrate','2500k','-bufsize','5000k','-preset','superfast','-tune','zerolatency','-profile:v','baseline','-level','3.1','-pix_fmt','yuv420p','-crf','24','-g','30','-keyint_min','30','-sc_threshold','0']
        self.producer=self.spawn(args+silence+['-map','0:v:0','-map','0:a:0' if audio else '1:a:0']+video_options+['-c:a','aac','-b:a','96k','-ar','48000','-ac','1','-f','hls','-hls_time','2','-hls_list_size','48' if copy_video else '90','-hls_delete_threshold','3','-hls_segment_type','fmp4','-hls_flags','delete_segments+independent_segments+temp_file','-hls_segment_filename',str(self.session/'segment%09d.m4s'),str(self.session/'live.m3u8')],stdout=subprocess.DEVNULL)
        self.reconcile_detection()

    def start_detector(self):
        args=self.source if self.source else input_args(self.camera)
        detector_args=args
        if (not self.source and not self.camera.get('rtsp_url') and self.camera['subtype']==0
                and rtsp_family(self.camera.get('rtsp_preset', 'dahua')) not in SINGLE_STREAM_FAMILIES):
            # Motion needs only a tiny frame; avoid decoding the full-resolution main stream twice.
            auxiliary=input_args({**self.camera,'subtype':1})
            try:
                check=subprocess.run([self.ffprobe,'-v','error','-analyzeduration','500000','-probesize','1000000']+auxiliary+['-select_streams','v:0','-show_entries','stream=width,height','-of','json'],capture_output=True,timeout=7,check=True)
                streams=json.loads(check.stdout).get('streams',[])
                if streams and streams[0].get('width',0)>0:detector_args=auxiliary
            except Exception:pass # Cameras without substreams retain the original source.
        self.detector=self.spawn(detector_args+['-an','-vf',f'scale={WIDTH}:{HEIGHT},fps={FPS},format=gray','-f','rawvideo','pipe:1'],stdout=subprocess.PIPE)
        self.latest_frame=time.monotonic();self.detector_warmup=time.monotonic()+3
        threading.Thread(target=self.read_frames,args=(self.detector,),daemon=True).start()

    def reconcile_detection(self):
        if not (self.camera['motion'] or self.camera.get('timelapse',False)):
            self.detection_mode='disabled';return
        state=self.onvif.snapshot() if self.onvif else None
        software=state is None or (not state['connected'] and self.camera.get('onvif_fallback',True))
        if software:
            if self.detector is None and time.monotonic()>=self.detector_retry:
                while not self.frames.empty():
                    try:self.frames.get_nowait()
                    except queue.Empty:break
                self.start_detector()
            self.detection_mode='rtsp_fallback' if state is not None else 'rtsp'
        else:
            if self.detector:
                stop_process(self.detector);self.detector=None
            self.detection_mode='onvif' if state['connected'] else 'onvif_connecting'

    def read_frames(self,p):
        size=WIDTH*HEIGHT
        while not self.quit.is_set():
            frame=p.stdout.read(size)
            if len(frame)!=size:break
            try:self.frames.put_nowait(frame)
            except queue.Full:
                try:self.frames.get_nowait()
                except queue.Empty:pass
                try:self.frames.put_nowait(frame)
                except queue.Full:pass
        p.stdout.close()

    def scan_segments(self):
        playlist=self.session/'live.m3u8'
        try:text=playlist.read_text()
        except OSError:return
        pending=None;items=[]
        for line in text.splitlines():
            if line.startswith('#EXTINF:'):pending=float(line.split(':')[1].split(',')[0])
            elif line.startswith('segment') and pending is not None:
                p=self.session/line
                if p.is_file():items.append((line,p,pending))
                pending=None
        if not items:return
        end=items[-1][1].stat().st_mtime
        for name,p,duration in reversed(items):
            if name not in self.segments:self.segments[name]={'name':name,'path':p,'start':end-duration,'duration':duration}
            end=self.segments[name]['start']
        if self.event:
            for item in sorted(self.segments.values(),key=lambda x:x['start']):
                if item['start']+item['duration']>=self.event['from'] and item['start']<=self.event['until'] and item['name'] not in self.event['pieces']:
                    dest=self.event['stage']/item['name']
                    try:os.link(item['path'],dest)
                    except FileNotFoundError:continue
                    except OSError:shutil.copyfile(item['path'],dest)
                    self.event['pieces'][item['name']]={**item,'path':dest}
        self.segments={k:v for k,v in self.segments.items() if v['path'].exists()}
        total=sum(p.stat().st_size for p in self.session.glob('*') if p.is_file())
        if total>512*1024**2:raise RuntimeError('cache_limit')
        if self.video_copy and not self.force_transcode and any(item['duration']>10 for item in self.segments.values()):
            self.force_transcode=True
            atomic(self.cache.parent/(self.camera['id']+'.force-transcode'),b'long keyframe interval observed')
            raise RuntimeError('long_keyframe_interval')

    def trigger(self,now):
        if self.event is None:
            stage=self.cache/('event-'+uuid.uuid4().hex);stage.mkdir(mode=0o700)
            shutil.copyfile(self.session/'init.mp4',stage/'init.mp4')
            self.event={'from':now-self.camera['prebuffer'],'until':now+self.camera['tail'],'began':now,'stage':stage,'pieces':{},'detector':self.detection_mode}
        else:
            self.event['until']=now+self.camera['tail']
            if self.event['detector']!=self.detection_mode:self.event['detector']='mixed'
        self.status='recording'

    def finish_event(self):
        if not self.event:return
        event=self.event;self.event=None
        if not event['pieces']:shutil.rmtree(event['stage'],ignore_errors=True);return
        try:self.exports.put_nowait(event)
        except queue.Full:
            shutil.rmtree(event['stage'],ignore_errors=True);self.error='export_queue_full'
        self.status='watching' if self.camera['motion'] else 'live'

    def export_loop(self):
        while True:
            event=self.exports.get()
            try:
                if event is None:return
                self.export(event)
            except Exception:self.error='export_failed'
            finally:
                if event:shutil.rmtree(event['stage'],ignore_errors=True)
                self.exports.task_done()

    def export(self,event):
        pieces=sorted(event['pieces'].values(),key=lambda x:x['start'])
        # Each fMP4 chunk belongs to the same init segment; concatenate bytes into one demuxable input.
        joined=event['stage']/'event.mp4'
        with open(joined,'wb') as out:
            for p in [event['stage']/'init.mp4']+[s['path'] for s in pieces]:
                with open(p,'rb') as src:shutil.copyfileobj(src,out)
        folder=self.recordings/(self.camera['folder'] or self.camera['id'])/self.camera['id'];folder.mkdir(parents=True,exist_ok=True)
        name=uuid.uuid4().hex;output=folder/(name+'.mp4');partial=folder/(name+'.partial.mp4')
        self.active_path=partial
        try:
            subprocess.run([self.ffmpeg,'-v','error','-i',str(joined),'-map','0:v:0','-map','0:a:0?','-c','copy','-avoid_negative_ts','make_zero','-movflags','+faststart',str(partial)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=90,check=True)
            probe=subprocess.run([self.ffprobe,'-v','error','-show_entries','format=duration','-of','json',str(partial)],capture_output=True,check=True,timeout=15)
            duration=float(json.loads(probe.stdout)['format']['duration'])
            meta={'id':name,'camera_id':self.camera['id'],'camera_name':self.camera['name'],'start':pieces[0]['start'],'duration':duration,'bytes':partial.stat().st_size,'detection_method':event.get('detector','rtsp')}
            os.replace(partial,output);atomic(output.with_suffix('.json'),json.dumps(meta).encode())
        finally:partial.unlink(missing_ok=True);self.active_path=None
        self.prune()

    def prune(self):
        clips=[]
        for p in self.recordings.glob('*/*/*.json'):
            try:
                m=json.loads(p.read_text());video=p.with_suffix('.mp4')
                if m['camera_id']==self.camera['id'] and video.exists():clips.append((m,p,video))
            except (ValueError,KeyError,OSError):continue
        clips.sort(key=lambda x:x[0]['start']);total=sum(x[2].stat().st_size for x in clips)
        for m,p,v in clips:
            if m['start']<time.time()-self.camera['max_days']*86400 or total>self.camera['max_gb']*1024**3:
                try:total-=v.stat().st_size;v.unlink();p.unlink(missing_ok=True)
                except OSError:pass

    def run(self):
        while not self.quit.is_set():
            previous=None;last_prune=0
            try:
                self.status='connecting';self.start_stream()
                while not self.quit.is_set():
                    if self.producer.poll() is not None:raise RuntimeError('connection_failed')
                    self.reconcile_detection()
                    if self.detector and (self.detector.poll() is not None or time.monotonic()-self.latest_frame>20):
                        stop_process(self.detector);self.detector=None;self.detector_retry=time.monotonic()+5;previous=None;self.error='motion_analysis_failed'
                    now=time.time();motion_active=False
                    try:
                        frame=self.frames.get(timeout=.2);self.latest_frame=time.monotonic()
                        if self.detector is not None and time.monotonic()>self.detector_warmup and detect(previous,frame,self.camera['zone'],self.camera['sensitivity']):motion_active=True
                        previous=frame
                    except queue.Empty:pass
                    if self.onvif and self.detection_mode=='onvif' and self.onvif.snapshot()['active']:motion_active=True
                    self.scan_segments()
                    if motion_active:
                        if self.camera['motion'] and (self.session/'init.mp4').exists():self.trigger(now)
                        self.photos.schedule(self.session,self.segments)
                    if self.segments:self.error=None
                    if self.detection_mode=='onvif_connecting':self.error='onvif_unavailable'
                    if self.event and (now>self.event['until']+3 or now-self.event['began']>=60):self.finish_event()
                    if not self.event:self.status=('watching' if self.camera['motion'] or self.camera.get('timelapse',False) else 'live') if self.segments else 'connecting'
                    if self.detection_mode=='onvif_connecting' and not self.event:self.status='onvif_offline'
                    if now-last_prune>60:
                        self.prune();last_prune=now
                        try:self.photos.archive.prune()
                        except OSError:self.photos.error='snapshot_storage_failed'
            except Exception:self.error='connection_failed';self.status='offline'
            finally:
                stop_process(self.producer);stop_process(self.detector);self.detector=None
                if self.onvif:
                    self.onvif.stop();self.onvif.join(timeout=20);self.onvif=None
                if self.session:
                    try:self.scan_segments()
                    except Exception:pass
                self.finish_event()
                if self.photos.thread:self.photos.jobs.join()
                if self.session:shutil.rmtree(self.session,ignore_errors=True)
                self.segments={}
            if not self.quit.is_set():
                self.status='offline';self.quit.wait(5)
        self.photos.close()
        self.exports.join();self.exports.put(None);self.export_thread.join(timeout=95)
        shutil.rmtree(self.cache,ignore_errors=True)

    def stop(self):self.quit.set()


class Engine:
    def __init__(self,cache,recordings,ffmpeg='ffmpeg',ffprobe='ffprobe'):
        self.cache=Path(cache);self.recordings=Path(recordings);self.ffmpeg=ffmpeg;self.ffprobe=ffprobe;self.workers={};self.lock=threading.RLock()
        self.cache.mkdir(parents=True,exist_ok=True);self.recordings.mkdir(parents=True,exist_ok=True)
        # Single service instance owns this transient cache; old events cannot survive a hard crash.
        for p in self.cache.iterdir():
            if p.is_dir():shutil.rmtree(p)

    def sync(self,cameras):
        with self.lock:
            wanted={c['id']:c for c in cameras if c['enabled']}
            for key,w in list(self.workers.items()):
                if key not in wanted or w.camera!=wanted[key]:
                    w.stop();w.join(timeout=120)
                    if w.is_alive():raise RuntimeError('Camera is still stopping')
                    del self.workers[key]
            for key,c in wanted.items():
                if key not in self.workers:
                    w=CameraWorker(c,self.cache,self.recordings,self.ffmpeg,self.ffprobe);self.workers[key]=w;w.start()

    def close(self):
        with self.lock:
            for w in self.workers.values():w.stop()
            for w in self.workers.values():w.join(timeout=120)
