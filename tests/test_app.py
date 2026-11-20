import json, os, tempfile, unittest, uuid
from pathlib import Path
from app.storage import Store, atomic
from app.engine import validate_camera, detect, WIDTH, HEIGHT
from app.server import create_app

class AppTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.app=create_app(self.root/'data',self.root/'records',self.root/'cache',start_engine=False)
        self.addCleanup(self.app.extensions['store'].close)
        self.client=self.app.test_client();self.csrf=''
    def post(self,path,value):return self.client.post(path,json=value,headers={'X-CSRF-Token':self.csrf})
    def setup(self):
        r=self.post('/api/setup',{'username':'admin','password':'test-master-password-2026'});self.assertEqual(r.status_code,200);self.csrf=r.json['csrf']
    def camera(self):return {'name':'Вход','host':'192.0.2.20','username':'admin','password':'test-secret','motion':True,'onvif_username':'camera-events','onvif_password':'test-onvif-secret','onvif_use_camera_credentials':False}
    def test_auth_csrf_and_encryption(self):
        self.assertEqual(self.client.get('/api/cameras').status_code,401)
        self.assertEqual(self.post('/api/setup',{'username':'!','password':'a'*16}).status_code,400)
        self.setup();self.assertFalse((self.root/'data/setup-token').exists())
        self.assertEqual(self.client.post('/api/cameras',json=self.camera()).status_code,403)
        r=self.post('/api/cameras',self.camera());self.assertEqual(r.status_code,200)
        cameras=self.client.get('/api/cameras').json;self.assertNotIn('password',cameras[0]);self.assertNotIn('onvif_password',cameras[0]);self.assertTrue(cameras[0]['has_password'])
        raw=(self.root/'data/config.sqlite').read_bytes();self.assertNotIn(b'test-secret',raw);self.assertNotIn(b'test-onvif-secret',raw);self.assertNotIn('Вход'.encode(),raw)
        c=cameras[0];c['name']='Edited';self.assertEqual(self.post('/api/cameras',c).status_code,200);self.assertEqual(self.app.extensions['store'].cameras()[0]['password'],'test-secret');self.assertEqual(self.app.extensions['store'].cameras()[0]['onvif_password'],'test-onvif-secret')
        self.assertEqual(self.post('/api/logout',{}).status_code,200);self.assertEqual(self.client.get('/api/cameras').status_code,401)
    def test_password_rotation_and_sessions(self):
        self.setup();second=self.app.test_client();r=second.post('/api/login',json={'username':'admin','password':'test-master-password-2026'});other=r.json['csrf']
        self.assertEqual(self.post('/api/password',{'old':'wrong','password':'new-password-2026'}).status_code,403)
        r=self.post('/api/password',{'old':'test-master-password-2026','password':'new-password-2026'});self.assertEqual(r.status_code,200);self.csrf=r.json['csrf']
        self.assertEqual(second.get('/api/cameras').status_code,401);self.assertEqual(second.post('/api/login',json={'username':'admin','password':'test-master-password-2026'}).status_code,401)
        self.assertEqual(second.post('/api/login',json={'username':'admin','password':'new-password-2026'}).status_code,200)
    def test_tamper_detection_unicode(self):
        store=self.app.extensions['store'];blob=store.seal({'password':'Ар0м@ пример'});self.assertEqual(store.unseal(blob)['password'],'Ар0м@ пример')
        altered=bytearray(blob);altered[-1]^=1
        with self.assertRaises(Exception):store.unseal(bytes(altered))
    def test_validation_and_zone(self):
        for mutation in [{'host':'x/../../etc'},{'folder':'../escape'},{'prebuffer':31},{'zone':[.8,0,.5,1]},{'zone':[float('nan'),0,1,1]}]:
            with self.assertRaises((ValueError,TypeError)):validate_camera({**self.camera(),**mutation})
        old=bytes(WIDTH*HEIGHT);frame=bytearray(old)
        for y in range(HEIGHT):frame[y*WIDTH:y*WIDTH+WIDTH//4]=bytes([255])*(WIDTH//4)
        self.assertTrue(detect(old,frame,[0,0,.25,1],55));self.assertFalse(detect(old,frame,[.5,0,.5,1],100));self.assertFalse(detect(old,old,[0,0,1,1],100))
    def test_range_and_clip_filter(self):
        self.setup();cid=str(uuid.uuid4());rid=uuid.uuid4().hex;folder=self.root/'records'/cid/cid;folder.mkdir(parents=True)
        (folder/(rid+'.mp4')).write_bytes(b'0123456789');atomic(folder/(rid+'.json'),json.dumps({'id':rid,'camera_id':cid,'camera_name':'Test','start':1000,'duration':10,'bytes':10}).encode())
        self.assertEqual(len(self.client.get('/api/recordings?from=1005&to=1006').json),1)
        self.assertEqual(len(self.client.get('/api/recordings?from=2000&to=3000').json),0)
        r=self.client.get('/recordings/'+rid+'.mp4',headers={'Range':'bytes=2-5'});self.assertEqual(r.status_code,206);self.assertEqual(r.data,b'2345');r.close()
        self.assertEqual(self.client.get('/live/'+cid+'/../../data/vault.key').status_code,404)
        self.assertEqual(self.client.post('/api/cameras',json=self.camera(),headers={'X-CSRF-Token':self.csrf,'Origin':'https://evil.test'}).status_code,403)

if __name__=='__main__':unittest.main()
