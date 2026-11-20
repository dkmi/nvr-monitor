"""Explicit real-FFmpeg ONVIF photos test; optional --photos-only."""
import json,sys,tempfile,time,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).resolve().parent))
from app.engine import CameraWorker
from test_onvif import MockCamera

def main():
 fixture=str(Path(sys.argv[1]).resolve());photos_only='--photos-only' in sys.argv;server=MockCamera(motion_window=(8,14));camera=server.camera();camera.update(timelapse=True,timelapse_interval=2,motion=not photos_only)
 with tempfile.TemporaryDirectory(prefix='nvr-photo-record-') as tmp:
  root=Path(tmp);worker=CameraWorker(camera,root/'cache',root/'recordings',source=['-re','-stream_loop','-1','-i',fixture]);started=time.monotonic();worker.start()
  try:
   while time.monotonic()-started<6:time.sleep(.1)
   assert not list((root/'recordings/timelapse').rglob('*.json')),'Photos before motion'
   while time.monotonic()-started<25:time.sleep(.1)
   assert worker.detector is None,'ONVIF must not start a software video analyzer'
   photos=sorted((root/'recordings/timelapse').rglob('*.json'));assert len(photos)>=2,(len(photos),worker.photos.error)
   meta=[json.loads(p.read_text()) for p in photos];times=sorted(m['start'] for m in meta);assert all(b-a>=1.5 for a,b in zip(times,times[1:])),times
   for p in photos:
    assert p.with_suffix('.jpg').is_file() and p.with_name(p.stem+'.thumb.jpg').is_file()
    subprocess.run(['ffmpeg','-v','error','-i',str(p.with_suffix('.jpg')),'-frames:v','1','-f','null','-'],check=True,capture_output=True,timeout=10)
   count=len(photos);time.sleep(3);assert len(list((root/'recordings/timelapse').rglob('*.json')))==count,'Photos continued without motion'
   videos=list((root/'recordings').glob('*/*/*.mp4'))
   if photos_only:assert not videos,'Photo-only mode made a video recording'
   else:assert videos,'Video recording lost when enabling photos'
   print('PASS ONVIF -> '+('photos only' if photos_only else 'MP4 and photos')+': no idle photos, interval respected, JPEG and thumbnails decode, no extra analysis decoder',flush=True)
  finally:worker.stop();worker.join(90);server.close()
  assert not worker.is_alive();assert 'Unsubscribe' in server.calls
if __name__=='__main__':main()
