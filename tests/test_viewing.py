import tempfile,unittest
from pathlib import Path
from app.server import create_app

class ViewingTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name);self.app=create_app(self.root/'d',self.root/'r',self.root/'c',False)
  self.addCleanup(self.app.extensions['store'].close)
  self.client=self.app.test_client();r=self.client.post('/api/setup',json={'username':'owner','password':'owner-password-2026'});self.csrf=r.json['csrf']
 def test_delay_zero_and_persistence(self):
  self.assertEqual(self.client.get('/api/preferences').json['live_delay'],30)
  for value in (0,15,60):
   r=self.client.post('/api/preferences',json={'live_delay':value},headers={'X-CSRF-Token':self.csrf});self.assertEqual(r.status_code,200);self.assertEqual(self.client.get('/api/state').json['live_delay'],value)
  self.assertEqual(self.app.extensions['store'].get('viewing')['live_delay'],60)
  self.assertFalse(self.app.extensions['engine'].workers)
 def test_limits_csrf_and_roles(self):
  for value in (-1,61,True,'30',2.5):self.assertEqual(self.client.post('/api/preferences',json={'live_delay':value},headers={'X-CSRF-Token':self.csrf}).status_code,400)
  self.assertEqual(self.client.post('/api/preferences',json={'live_delay':0}).status_code,403)
  r=self.client.post('/api/users',json={'username':'viewer','password':'viewer-password-2026','role':'full'},headers={'X-CSRF-Token':self.csrf});viewer=self.app.test_client();r=viewer.post('/api/login',json={'username':'viewer','password':'viewer-password-2026'});self.assertEqual(viewer.get('/api/preferences').status_code,200);self.assertEqual(viewer.post('/api/preferences',json={'live_delay':0},headers={'X-CSRF-Token':r.json['csrf']}).status_code,403)
if __name__=='__main__':unittest.main()
