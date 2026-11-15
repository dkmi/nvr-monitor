"""Integration check: the actual installed RTSP demuxer must accept our options."""
import os, subprocess, unittest
from app.engine import validate_camera,input_args

class RTSPOptionsTest(unittest.TestCase):
    def test_installed_ffmpeg_supports_rtsp_arguments(self):
        c=validate_camera({'host':'127.0.0.1','username':'test','password':'not-a-camera'})
        args=input_args(c)
        result=subprocess.run([os.getenv('FFMPEG','ffmpeg'),'-hide_banner','-h','demuxer=rtsp'],capture_output=True,text=True,check=True)
        for option in (args[0],args[2]):self.assertIn(option+' ',result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
