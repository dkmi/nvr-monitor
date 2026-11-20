import json,tempfile,time,unittest,uuid,threading
from pathlib import Path
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from app.engine import validate_camera
from app.server import create_app
from app.timelapse import PhotoArchive,Snapshotter,camera_jpeg

JPEG=b'\xff\xd8'+b'x'*100+b'\xff\xd9'
def camera(**extra):return validate_camera({'name':'Photo camera','host':'127.0.0.1','username':'snapshot-user','password':'synthetic-password',**extra})

class PhotoTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name)
 def test_defaults_validation_and_old_client_preservation(self):
  original=camera(motion=True,prebuffer=7);self.assertFalse(original['timelapse']);self.assertEqual(original['prebuffer'],7)
  for key,value in [('timelapse_interval',1),('timelapse_interval',3601),('timelapse_max_days',0),('timelapse_max_mb',0)]:
   with self.assertRaises(ValueError):camera(**{key:value})
  app=create_app(self.root/'data',self.root/'records',self.root/'cache',False)
  self.addCleanup(app.extensions['store'].close)
  c=app.test_client();r=c.post('/api/setup',json={'username':'admin','password':'synthetic-photo-password'});csrf=r.json['csrf']
  original=camera(timelapse=True,timelapse_interval=17,timelapse_max_days=9,timelapse_max_mb=23);app.extensions['store'].put('cameras',[original])
  old_client={k:v for k,v in original.items() if not k.startswith('timelapse') and k not in ('password','onvif_password')};old_client['name']='Renamed'
  r=c.post('/api/cameras',json=old_client,headers={'X-CSRF-Token':csrf});self.assertEqual(r.status_code,200)
  saved=app.extensions['store'].cameras()[0]
  for key in ('timelapse','timelapse_interval','timelapse_max_days','timelapse_max_mb','password','prebuffer'):self.assertEqual(saved[key],original[key])
 def test_retention_age_quota_and_camera_isolation(self):
  a=camera(timelapse_max_days=1,timelapse_max_mb=1);b=camera();other=PhotoArchive(self.root,b);other_photo=other.save(JPEG,JPEG,time.time(),'camera')
  archive=PhotoArchive(self.root,a);archive.save(JPEG,JPEG,time.time()-3*86400,'camera');self.assertFalse(list(archive.root.rglob('*.json')))
  big=b'\xff\xd8'+b'x'*400000+b'\xff\xd9';metas=[archive.save(big,JPEG,time.time()+i,'camera') for i in range(3)]
  remaining=list(archive.root.rglob('*.json'));self.assertEqual(len(remaining),2);self.assertNotIn(metas[0]['id'],[p.stem for p in remaining])
  self.assertTrue(list(other.root.rglob(other_photo['id']+'.jpg')))
  self.assertLessEqual(sum(p.stat().st_size for p in archive.root.rglob('*') if p.is_file()),1024**2)
 def test_interval_and_disabled_no_capture(self):
  c=camera(timelapse=True,timelapse_interval=2);snap=Snapshotter(c,self.root)
  with patch('app.timelapse.camera_jpeg',return_value=JPEG) as fetch,patch.object(snap,'thumbnail',return_value=JPEG),patch('app.timelapse.time.monotonic',return_value=100) as clock:
   snap.schedule(None,{});snap.jobs.join();self.assertEqual(fetch.call_count,1)
   clock.return_value=101;snap.schedule(None,{});self.assertEqual(fetch.call_count,1)
   clock.return_value=102.1;snap.schedule(None,{});snap.jobs.join();self.assertEqual(fetch.call_count,2);snap.close()
  disabled=Snapshotter(camera(timelapse=False),self.root)
  with patch('app.timelapse.camera_jpeg') as fetch:disabled.schedule(None,{});fetch.assert_not_called();self.assertIsNone(disabled.thread)
 def test_legacy_digest_does_not_wait_for_401_body(self):
  class Handler(BaseHTTPRequestHandler):
   protocol_version='HTTP/1.1'
   def log_message(self,*_):pass
   def do_GET(self):
    if self.headers.get('Authorization','').startswith('Digest '):
     self.send_response(200);self.send_header('Content-Length',str(len(JPEG)));self.end_headers();self.wfile.write(JPEG)
    else:
     self.send_response(401);self.send_header('WWW-Authenticate','Digest realm="test", nonce="test-nonce", qop="auth"');self.end_headers()
  server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:self.assertEqual(camera_jpeg(camera(onvif_port=server.server_port)),JPEG)
  finally:server.shutdown();server.server_close();thread.join()
 def test_photo_acl_dates_pagination_download_and_no_video_leak(self):
  app=create_app(self.root/'data',self.root/'records',self.root/'cache',False)
  self.addCleanup(app.extensions['store'].close)
  admin=app.test_client();r=admin.post('/api/setup',json={'username':'admin','password':'synthetic-photo-password'});store=app.extensions['store'];cams=[camera(),camera()];store.put('cameras',cams)
  now=time.time();metas=[]
  for index,c in enumerate(cams):
   archive=PhotoArchive(self.root/'records',c)
   for i in range(3):metas.append(archive.save(JPEG,JPEG,now-index*10-i,'camera'))
  def endpoint(m,extra=''):return '/recordings/timelapse/'+m['camera_id']+'/'+m['day']+'/'+m['id']+'.jpg'+extra
  params={'from':now-100,'to':now+1,'limit':2};r=admin.get('/api/timelapse',query_string=params);self.assertEqual(len(r.json['photos']),2);cursor=r.json['next_cursor'];r2=admin.get('/api/timelapse',query_string={**params,'before':cursor});self.assertFalse({p['id'] for p in r.json['photos']} & {p['id'] for p in r2.json['photos']})
  self.assertEqual(admin.get('/api/recordings').json,[])
  self.assertEqual(app.test_client().get('/api/timelapse').status_code,401);self.assertEqual(app.test_client().get(endpoint(metas[0])).status_code,401)
  for role in ('limited','playback','full'):
   store.save_user({'username':'photo-'+role,'password':'synthetic-photo-password','role':role,'cameras':[cams[0]['id']]});client=app.test_client();client.post('/api/login',json={'username':'photo-'+role,'password':'synthetic-photo-password'})
   photos=client.get('/api/timelapse',query_string=params).json['photos'];self.assertTrue(photos)
   response=client.get(endpoint(metas[0],'?download=1'));self.assertEqual(response.status_code,200);self.assertIn('attachment',response.headers['Content-Disposition']);response.close()
   response=client.get(endpoint(metas[0],'?thumb=1'));self.assertEqual(response.status_code,200);response.close()
   if role!='full':
    self.assertTrue(all(p['camera_id']==cams[0]['id'] for p in photos));self.assertEqual(client.get(endpoint(metas[3])).status_code,403);self.assertEqual(client.get('/api/timelapse',query_string={**params,'camera':cams[1]['id']}).status_code,403)
  for query in [{'from':'nan'},{'from':0,'to':1e15},{'from':now-10*86400,'to':now},{'limit':1000},{'before':'../../etc/passwd'}]:self.assertEqual(admin.get('/api/timelapse',query_string=query).status_code,400)
