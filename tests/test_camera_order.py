import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from app.server import create_app
from app.engine import validate_camera

class CameraOrderTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();r=Path(self.tmp.name);self.app=create_app(r/'data',r/'records',r/'cache',False);self.client=self.app.test_client();login=self.client.post('/api/setup',json={'username':'order-admin','password':'synthetic-order-password'});self.csrf=login.json['csrf'];self.store=self.app.extensions['store']
  self.cameras=[validate_camera({'name':str(i),'host':'192.0.2.'+str(i+1),'username':'camera-user','password':'synthetic-camera-password','enabled':i!=1,'motion':True,'timelapse':True,'timelapse_interval':17,'prebuffer':9}) for i in range(3)];self.store.put('cameras',self.cameras)
 def tearDown(self):self.tmp.cleanup()
 def post(self,ids):return self.client.post('/api/cameras/order',json={'ids':ids},headers={'X-CSRF-Token':self.csrf})
 def test_edit_keeps_position_and_new_camera_appends(self):
  original=self.cameras[0];edited={**original,'name':'Renamed'};del edited['password'];r=self.client.post('/api/cameras',json=edited,headers={'X-CSRF-Token':self.csrf});self.assertEqual(r.status_code,200)
  saved=self.store.cameras();self.assertEqual([c['id'] for c in saved],[c['id'] for c in self.cameras]);self.assertEqual(saved[0]['password'],original['password']);self.assertEqual(saved[0]['timelapse_interval'],17)
  r=self.client.post('/api/cameras',json={'host':'192.0.2.99','username':'new-camera','password':'synthetic-camera-password'},headers={'X-CSRF-Token':self.csrf});self.assertEqual(r.status_code,200);self.assertEqual([c['id'] for c in self.store.cameras()[:3]],[c['id'] for c in self.cameras])
 def test_reorder_preserves_all_fields_and_does_not_sync_engine(self):
  ids=[c['id'] for c in reversed(self.cameras)]
  with patch('app.server.Engine.sync') as sync:
   r=Path(self.tmp.name);active=create_app(r/'data',r/'records',r/'cache',True);client=active.test_client();login=client.post('/api/login',json={'username':'order-admin','password':'synthetic-order-password'});sync.reset_mock()
   self.assertEqual(client.post('/api/cameras/order',json={'ids':ids},headers={'X-CSRF-Token':login.json['csrf']}).status_code,200);sync.assert_not_called()
  self.assertEqual(self.store.cameras(),list(reversed(self.cameras)))
  self.assertEqual([c['id'] for c in self.client.get('/api/cameras').json],ids)
  # A late settings edit keeps the new slot and is not overwritten by another reorder.
  edit={**self.cameras[1],'timelapse_interval':25};self.client.post('/api/cameras',json=edit,headers={'X-CSRF-Token':self.csrf});self.post([ids[1],ids[0],ids[2]])
  saved={c['id']:c for c in self.store.cameras()};self.assertEqual(saved[edit['id']]['timelapse_interval'],25)
 def test_bad_payload_stale_membership_and_csrf(self):
  ids=[c['id'] for c in self.cameras]
  for value in (None,'bad',[1],ids+[ids[0]]):self.assertEqual(self.post(value).status_code,400)
  self.assertEqual(self.post(ids[:-1]).status_code,409);self.assertEqual(self.post(ids+['unknown']).status_code,409)
  self.assertEqual(self.client.post('/api/cameras/order',json={'ids':ids}).status_code,403);self.assertEqual(self.store.cameras(),self.cameras)
 def test_nonadmins_cannot_reorder_and_filtered_order_is_consistent(self):
  ids=[c['id'] for c in reversed(self.cameras)];self.post(ids)
  for role in ('full','limited','playback'):
   self.store.save_user({'username':'order-'+role,'password':'synthetic-order-password','role':role,'cameras':[ids[0],ids[2]]});client=self.app.test_client();login=client.post('/api/login',json={'username':'order-'+role,'password':'synthetic-order-password'})
   self.assertEqual(client.post('/api/cameras/order',json={'ids':ids},headers={'X-CSRF-Token':login.json['csrf']}).status_code,403)
   visible=[c['id'] for c in client.get('/api/cameras').json];self.assertEqual(visible,ids if role=='full' else [ids[0],ids[2]])
