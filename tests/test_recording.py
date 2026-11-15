import json, os, subprocess, sys, tempfile, time, uuid
from pathlib import Path
from app.engine import CameraWorker, validate_camera

def main():
    root=Path(tempfile.mkdtemp(prefix='dahua-web-record-test-'));source=str(Path(sys.argv[1]).resolve());ff=os.getenv('FFMPEG','ffmpeg');fp=os.getenv('FFPROBE','ffprobe')
    camera=validate_camera({'name':'Synthetic motion','host':'127.0.0.1','username':'test','password':'not-a-camera','motion':True,'tail':5,'prebuffer':5,'sensitivity':80})
    w=CameraWorker(camera,root/'cache',root/'recordings',ff,fp,source=['-re','-stream_loop','-1','-i',source]);start=time.time();w.start()
    try:
        deadline=time.monotonic()+36
        while time.monotonic()<deadline:
            clips=list((root/'recordings').glob('*/*/*.json'))
            if clips:break
            time.sleep(.5)
        assert clips, f'No exported recording: status={w.status}, error={w.error}'
        meta=json.loads(clips[0].read_text());video=clips[0].with_suffix('.mp4')
        assert meta['start']<start+6, meta
        assert meta['duration']>=10,meta
        probe=json.loads(subprocess.check_output([fp,'-v','error','-show_streams','-of','json',str(video)]))
        assert any(s['codec_name']=='h264' for s in probe['streams'])
        assert any(s['codec_name']=='aac' for s in probe['streams'])
        decode=subprocess.run([ff,'-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True,check=True)
        assert not decode.stderr,decode.stderr
        frames=json.loads(subprocess.check_output([fp,'-v','error','-select_streams','v','-show_entries','frame=best_effort_timestamp_time','-of','json',str(video)]))['frames']
        pts=[float(f['best_effort_timestamp_time']) for f in frames if 'best_effort_timestamp_time' in f]
        assert all(b>a for a,b in zip(pts,pts[1:])), 'Nonmonotonic frame timestamps'
        print('PASS real motion detection, pre-event footage, H264/AAC MP4, full decode, monotonic PTS:',meta)
    finally:
        w.stop();w.join(120);assert not w.is_alive(),'Worker did not shut down'
    print('PASS bounded worker and FFmpeg shutdown; test output:',root)

if __name__=='__main__':main()
