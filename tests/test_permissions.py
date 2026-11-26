import json, tempfile, unittest, uuid
from contextlib import closing
from pathlib import Path
from app.server import create_app
from app.storage import Store, atomic

class PermissionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.app=create_app(self.root/'data',self.root/'records',self.root/'cache',False)
        self.addCleanup(self.app.extensions['store'].close)
        self.admin=self.app.test_client()
        r=self.admin.post('/api/setup',json={'username':'owner','password':'owner-password-2026'});self.csrf=r.json['csrf'];self.ids=[]
        for host in ('10.0.0.1','10.0.0.2'):
            r=self.admin.post('/api/cameras',json={'host':host,'username':'camera-user','password':'secret-camera-password'},headers={'X-CSRF-Token':self.csrf});self.ids.append(r.json['id'])
        self.clips=[]
        for cid in self.ids:
            rid=uuid.uuid4().hex;folder=self.root/'records'/cid/cid;folder.mkdir(parents=True)
            (folder/(rid+'.mp4')).write_bytes(b'0123456789');atomic(folder/(rid+'.json'),json.dumps({'id':rid,'camera_id':cid,'camera_name':'Camera','start':1000,'duration':10,'bytes':10}).encode());self.clips.append(rid)
    def add(self,role,all_cameras=False):
        r=self.admin.post('/api/users',json={'username':'test-'+role,'password':'viewer-password-2026','role':role,'all_cameras':all_cameras,'cameras':[self.ids[0]]},headers={'X-CSRF-Token':self.csrf});self.assertEqual(r.status_code,200,r.json)
        client=self.app.test_client();login=client.post('/api/login',json={'username':'test-'+role,'password':'viewer-password-2026'});return client,login.json['csrf'],r.json['user']
    def test_limited_cannot_read_other_media_or_admin_data(self):
        client,csrf,user=self.add('limited');cameras=client.get('/api/cameras').json;self.assertEqual([c['id'] for c in cameras],[self.ids[0]])
        for private in ('username','password','host','motion','folder'):self.assertNotIn(private,cameras[0])
        self.assertEqual(client.get('/api/users').status_code,403)
        self.assertEqual(client.post('/api/cameras',json={'host':'10.0.0.3'},headers={'X-CSRF-Token':csrf}).status_code,403)
        self.assertEqual(client.get('/live/'+self.ids[1]+'/live.m3u8').status_code,403)
        self.assertEqual(client.get('/api/recordings?camera='+self.ids[1]).status_code,403)
        self.assertEqual(len(client.get('/api/recordings').json),1)
        self.assertEqual(client.get('/recordings/'+self.clips[1]+'.mp4').status_code,404)
        response=client.get('/recordings/'+self.clips[0]+'.mp4',headers={'Range':'bytes=1-3'});self.assertEqual(response.status_code,206);response.close()
    def test_full_viewer_cannot_administer(self):
        client,csrf,user=self.add('full');self.assertEqual(len(client.get('/api/cameras').json),2);self.assertEqual(len(client.get('/api/recordings').json),2)
        self.assertEqual(client.post('/api/users',json={'username':'hacker'},headers={'X-CSRF-Token':csrf}).status_code,403)
        self.assertEqual(client.post('/api/cameras/'+self.ids[0]+'/delete',json={},headers={'X-CSRF-Token':csrf}).status_code,403)
    def test_saved_rtsp_url_is_only_returned_to_admin_for_editing(self):
        url = 'rtsp://camera:test-password@192.0.2.20/live'
        saved = self.admin.post('/api/cameras', json={'id': self.ids[0], 'rtsp_url': url},
                                headers={'X-CSRF-Token': self.csrf})
        self.assertEqual(saved.status_code, 200)
        path = '/api/cameras/' + self.ids[0] + '/rtsp-url'
        reader, _, _ = self.add('limited')
        self.assertEqual(reader.get(path).status_code, 403)
        self.assertEqual(self.app.test_client().get(path).status_code, 401)
        self.assertNotIn('rtsp_url', self.admin.get('/api/cameras').json[0])
        response = self.admin.get(path)
        self.assertEqual(response.json, {'rtsp_url': url})
        self.assertIn('no-store', response.headers['Cache-Control'])
    def test_playback_all_or_selected_no_live(self):
        client,csrf,user=self.add('playback');self.assertEqual(len(client.get('/api/recordings').json),1)
        result=client.get('/api/recordings?previews=1&from=1100&to=1200').json
        self.assertEqual(result['clips'], [])
        self.assertEqual(result['previews'], {self.ids[0]: self.clips[0]})
        for cid in self.ids:self.assertEqual(client.get('/live/'+cid+'/init.mp4').status_code,403)
        self.admin.post('/api/users',json={**user,'all_cameras':True},headers={'X-CSRF-Token':self.csrf})
        self.assertEqual(client.get('/api/cameras').status_code,401)
        client.post('/api/login',json={'username':user['username'],'password':'viewer-password-2026'});self.assertEqual(len(client.get('/api/recordings').json),2)
    def test_disable_delete_and_last_admin(self):
        client,csrf,user=self.add('limited');self.admin.post('/api/users',json={**user,'enabled':False},headers={'X-CSRF-Token':self.csrf});self.assertEqual(client.get('/api/cameras').status_code,401)
        self.assertEqual(client.post('/api/login',json={'username':user['username'],'password':'viewer-password-2026'}).status_code,401)
        admin=self.app.extensions['store'].users()[0]
        admin=next(u for u in self.app.extensions['store'].users() if u['role']=='admin')
        r=self.admin.post('/api/users',json={**admin,'role':'limited'},headers={'X-CSRF-Token':self.csrf});self.assertEqual(r.status_code,400)
        self.assertEqual(self.admin.post('/api/setup',json={'username':'another','password':'another-password'}).status_code,409)
    def test_legacy_migration_retains_password_and_cameras(self):
        root = self.root / 'legacy'
        with closing(Store(root)) as legacy:
            legacy.set_password('Ар0м@old-password')
            legacy.put('cameras', [{'id': self.ids[0], 'password': 'camera-password'}])
        with closing(Store(root)) as migrated:
            self.assertTrue(migrated.check_user('admin','Ар0м@old-password'))
            self.assertEqual(migrated.cameras()[0]['password'], 'camera-password')
            self.assertEqual(len(migrated.users()), 1)
        with closing(Store(root)) as reopened:
            self.assertEqual(len(reopened.users()), 1)

if __name__=='__main__':unittest.main()
