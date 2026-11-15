"""Run explicitly: PYTHONPATH=.:tests python tests/test_onvif_recording.py fixture.mp4."""
import json,os,subprocess,sys,tempfile,time
from pathlib import Path
from app.engine import CameraWorker
from test_onvif import MockCamera

def main():
 root=Path(tempfile.mkdtemp(prefix='nvr-onvif-record-'));source=str(Path(sys.argv[1]).resolve());ff=os.getenv('FFMPEG','ffmpeg');fp=os.getenv('FFPROBE','ffprobe');server=MockCamera(motion_window=(8,12));camera=server.camera();camera['folder']='test';camera['prebuffer']=5;camera['tail']=5;camera['onvif_fallback']=False
 w=CameraWorker(camera,root/'cache',root/'recordings',ff,fp,source=['-re','-stream_loop','-1','-i',source]);start=time.time();w.start()
 try:
  deadline=time.monotonic()+35;clips=[]
  while time.monotonic()<deadline:
   clips=list((root/'recordings').glob('*/*/*.json'))
   if clips:break
   time.sleep(.2)
  assert clips,f'No ONVIF recording: {w.status} {w.error}'
  assert w.detector is None,'ONVIF must not decode a separate RTSP analysis stream'
  assert w.onvif.snapshot()['connected'];assert w.onvif.snapshot()['updates']>0
  meta=json.loads(clips[0].read_text());assert meta['detection_method']=='onvif',meta;assert meta['start']<start+6,meta;assert meta['duration']>=10,meta
  r=subprocess.run([ff,'-v','error','-i',str(clips[0].with_suffix('.mp4')),'-f','null','-'],capture_output=True,text=True,check=True);assert not r.stderr,r.stderr
  print('PASS ONVIF SOAP -> state transitions -> real prebuffer/tail MP4; no RTSP detector process; full decode:',meta)
 finally:w.stop();w.join(60);server.close()
 assert not w.is_alive();assert 'Unsubscribe' in server.calls
 print('PASS ONVIF and FFmpeg clean shutdown/unsubscribe')
if __name__=='__main__':main()
