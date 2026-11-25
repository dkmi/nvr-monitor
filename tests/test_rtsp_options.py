"""Integration check: the actual installed RTSP demuxer must accept our options."""
import json, os, subprocess, unittest
from pathlib import Path
from app.engine import validate_camera,input_args
from app.onvif import Client

class RTSPOptionsTest(unittest.TestCase):
    def test_installed_ffmpeg_supports_rtsp_arguments(self):
        c=validate_camera({'host':'127.0.0.1','username':'test','password':'not-a-camera'})
        args=input_args(c)
        result=subprocess.run([os.getenv('FFMPEG','ffmpeg'),'-hide_banner','-h','demuxer=rtsp'],capture_output=True,text=True,check=True)
        for option in (args[0],args[2]):self.assertIn(option+' ',result.stdout+result.stderr)

    def test_manufacturer_presets_and_legacy_default(self):
        paths = {
            'dahua': ('/cam/realmonitor?channel=2&subtype=0', '/cam/realmonitor?channel=2&subtype=1'),
            'hikvision': ('/Streaming/Channels/201', '/Streaming/Channels/202'),
            'reolink': ('/Preview_02_main', '/Preview_02_sub'),
            'tp_link': ('/stream1', '/stream2'),
        }
        for manufacturer, streams in paths.items():
            for subtype, path in enumerate(streams):
                with self.subTest(manufacturer=manufacturer, subtype=subtype):
                    camera = validate_camera(dict(host='camera.example', channel=2, subtype=subtype,
                                                  rtsp_preset=manufacturer, username='test', password='a@b'))
                    self.assertEqual(input_args(camera)[-1], 'rtsp://test:a%40b@camera.example:554' + path)
        with self.assertRaises(ValueError):
            validate_camera({'host': 'camera.example', 'rtsp_preset': 'unknown'})

    def test_custom_url_preserves_query_and_reuses_credentials_for_onvif(self):
        url = 'rtsp://some%40user:p%23a%3Ass@[2001:db8::1]:10554/live?channel=2&token=test'
        camera = validate_camera({'rtsp_url': url})
        self.assertEqual(camera['host'], '2001:db8::1')
        self.assertEqual(camera['port'], 10554)
        self.assertEqual(input_args(camera)[-1], url)
        client = Client(camera)
        self.addCleanup(client.http.close)
        self.assertEqual(client.device, 'http://[2001:db8::1]:80/onvif/device_service')
        self.assertEqual((client.username, client.password), ('some@user', 'p#a:ss'))
        self.assertEqual(input_args(validate_camera({'rtsp_url': 'rtsp://camera.example/stream1'}))[-1],
                         'rtsp://camera.example/stream1')

    def test_custom_url_rejects_invalid_protocols_and_authorities(self):
        for url in ('file:///tmp/clip.mp4', 'http://camera.example/stream', 'rtsp:///stream1',
                    'rtsp://camera.example:0/live', 'rtsp://[::1]junk/path',
                    'rtsp://camera.example/live#token', 'rtsp://camera.example/a b', 'rtsp://bad%user@camera/live'):
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, '^Invalid RTSP URL$'):
                validate_camera({'rtsp_url': url})

    def test_catalog_templates_work_with_custom_rtsp(self):
        path = Path(__file__).resolve().parents[1] / 'static' / 'camera-catalog.json'
        catalog = json.loads(path.read_text(encoding='utf-8'))
        self.assertTrue(catalog)
        self.assertTrue(any(entry['model'] for entry in catalog))
        self.assertTrue(any(not entry['model'] for entry in catalog))
        seen = set()
        for entry in catalog:
            key = (entry['brand'].casefold(), entry['model'].casefold(), entry['path'], entry['port'])
            self.assertNotIn(key, seen)
            seen.add(key)
            self.assertTrue(entry['path'].startswith('/'), entry)
            stream = (entry['path'].replace('[CHANNEL]', '1')
                      .replace('[USERNAME]', 'test').replace('[PASSWORD]', 'p%40ss'))
            url = f"rtsp://camera.example:{entry['port']}{stream}"
            self.assertEqual(input_args(validate_camera({'rtsp_url': url}))[-1], url)

if __name__=='__main__':unittest.main()
