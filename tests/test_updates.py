import io,json,os,tarfile,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from app.server import create_app
from app.updates import Updates,version_tuple,needs_update
from updater.host import unpack,Host,version

class UpdateTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.queue=self.root/'updates';self.queue.mkdir()
  self.env=patch.dict(os.environ,{'UPDATES_DIR':str(self.queue)});self.env.start()
  self.app=create_app(self.root/'data',self.root/'recordings',self.root/'cache',start_engine=False);self.c=self.app.test_client()
  self.c.post('/api/setup',json={'username':'admin','password':'synthetic-test-password'});self.csrf=self.c.get('/api/state').json['csrf']
 def tearDown(self):self.env.stop();self.tmp.cleanup()
 def test_admin_only_and_csrf(self):
  self.assertEqual(self.c.post('/api/updates',json={'tag':'v9.0.0'}).status_code,403)
  store=self.app.extensions['store'];store.save_user({'username':'viewer','password':'synthetic-test-password','role':'full'})
  c=self.app.test_client();r=c.post('/api/login',json={'username':'viewer','password':'synthetic-test-password'})
  self.assertEqual(c.get('/api/updates?check=1').status_code,403)
  self.assertEqual(c.post('/api/updates',json={'tag':'v9.0.0'},headers={'X-CSRF-Token':r.json['csrf']}).status_code,403)
 def test_queue_latest_only_and_no_duplicate(self):
  (self.queue/'status.json').write_text(json.dumps({'heartbeat':time.time(),'state':'idle'}))
  release={'tag':'v1.4.1','url':'https://github.com/dkmi/nvr-monitor/releases/tag/v1.4.1'}
  with patch('app.updates.latest_release',return_value=release):
   u=Updates(self.queue);self.assertTrue(u.status(check=True)['update_available']);self.assertTrue(u.status()['updater_available'])
   for tag in ['v1.4.0','v1.4.2','../../x','v2.0.0-rc1','https://evil.invalid']:
    with self.assertRaises(ValueError):u.queue(tag)
   r=self.c.post('/api/updates',json={'tag':'v1.4.1'},headers={'X-CSRF-Token':self.csrf});self.assertEqual(r.status_code,202)
   self.assertEqual(json.loads((self.queue/'request.json').read_text()),{'tag':'v1.4.1'})
   with self.assertRaises(ValueError):u.queue('v1.4.1')
 def test_unavailable_and_cache(self):
  with patch('app.updates.latest_release',side_effect=RuntimeError()):
   u=Updates(self.queue);self.assertEqual(u.status(check=True)['error'],'github_unavailable');self.assertFalse(u.status()['updater_available'])
   with self.assertRaises(RuntimeError):u.queue('v1.4.1')
  with patch('app.updates.latest_release',return_value={'tag':'v1.4.1'}) as latest:
   u=Updates(self.queue);u.status(check=True);u.status(check=True);self.assertEqual(latest.call_count,1)
   with self.assertRaises(ValueError):u.queue('v1.4.1')
 def test_archive_safety_and_runtime_exclusion(self):
  def archive(entries):
   stream=io.BytesIO()
   with tarfile.open(fileobj=stream,mode='w:gz') as t:
    for name,kind,text in entries:
     item=tarfile.TarInfo(name);item.type=kind;data=text.encode();item.size=len(data);t.addfile(item,io.BytesIO(data))
   return stream.getvalue()
  for entries in [[('top/app/../../escape',tarfile.REGTYPE,'x')],[('top/app/link',tarfile.SYMTYPE,'')]]:
   with self.assertRaises(ValueError):unpack(archive(entries),self.root/'staging')
  stage=self.root/'valid';stage.mkdir()
  unpack(archive([('top/Dockerfile',tarfile.REGTYPE,'FROM scratch'),('top/app/version.py',tarfile.REGTYPE,"VERSION='1.4.1'"),('top/data/vault.key',tarfile.REGTYPE,'bad'),('top/compose.yaml',tarfile.REGTYPE,'bad'),('top/.env',tarfile.REGTYPE,'bad')]),stage)
  self.assertFalse((stage/'data').exists());self.assertFalse((stage/'compose.yaml').exists());self.assertFalse((stage/'.env').exists())
 def test_request_restrictions(self):
  state=self.root/'state';state.mkdir();h=Host(self.root,state)
  for body in [{'tag':'v1.4.1','command':'bad'},{'tag':'../bad'}, {'tag':'v1.4.1-rc1'}]:
   (self.queue/'request.json').write_text(json.dumps(body))
   with self.assertRaises(ValueError):h.take_request()
  self.assertEqual(version('v1.10.0'),(1,10,0));self.assertGreater(version_tuple('v1.10.0'),version_tuple('v1.9.9'))

class HostFlowTests(unittest.TestCase):
 def exercise(self,fail=False):
  import shutil,subprocess
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'updates').mkdir();(root/'data').mkdir();(root/'app').mkdir();(root/'state').mkdir();(root/'recordings').mkdir();(root/'cache').mkdir()
   (root/'app/version.py').write_text("VERSION='1.4.0'");(root/'Dockerfile').write_text('old image');(root/'data/config.sqlite').write_bytes(b'original users and cameras');(root/'data/vault.key').write_bytes(b'original key');(root/'recordings/clip.mp4').write_bytes(b'recording');(root/'.env').write_text('WEB_PORT=1234');(root/'compose.yaml').write_text('original compose')
   stream=io.BytesIO()
   with tarfile.open(fileobj=stream,mode='w:gz') as t:
    for name,text in [('app/version.py',"VERSION='1.4.1'"),('Dockerfile','new image')]:
     item=tarfile.TarInfo('repo/'+name);body=text.encode();item.size=len(body);t.addfile(item,io.BytesIO(body))
   class FakeHost(Host):
    def validate_mounts(self):pass
    def run(self,args,timeout=1800):
     if args[0]=='cp':shutil.copytree(args[2],args[3])
     if args[0]=='mv':shutil.move(args[1],args[2])
    def output(self,args):
     if args[:2]==['docker','inspect']:return 'old-image'
     return 'container-id'
    def healthy(self,expected,revision=None):
     if expected=='1.4.1':
      (self.root/'data/config.sqlite').write_bytes(b'migrated database')
      if fail:raise RuntimeError('Simulated health failure')
   host=FakeHost(root,root/'state')
   with patch('updater.host.official',return_value='a'*40),patch('updater.host.fetch',return_value=stream.getvalue()):host.update('v1.4.1')
   self.assertEqual(host.job['state'],'rolled_back' if fail else 'succeeded')
   self.assertEqual((root/'app/version.py').read_text(),"VERSION='1.4.0'" if fail else "VERSION='1.4.1'")
   self.assertEqual((root/'data/config.sqlite').read_bytes(),b'original users and cameras' if fail else b'migrated database')
   self.assertEqual((root/'data/vault.key').read_bytes(),b'original key')
   self.assertEqual((root/'recordings/clip.mp4').read_bytes(),b'recording');self.assertEqual((root/'.env').read_text(),'WEB_PORT=1234');self.assertEqual((root/'compose.yaml').read_text(),'original compose')
   backup=Path(host.job['backup']);self.assertEqual((backup/'data/config.sqlite').read_bytes(),b'original users and cameras')
 def test_success_preserves_runtime_data(self):self.exercise()
 def test_health_failure_restores_source_image_and_database(self):self.exercise(fail=True)

class RevisionTests(unittest.TestCase):
 def test_same_version_changed_known_and_unknown(self):
  r={'tag':'v1.4.0','revision':'a'*40}
  self.assertTrue(needs_update(r,revision='b'*40))
  self.assertTrue(needs_update(r,revision=None))
  self.assertFalse(needs_update(r,revision='a'*40))
  self.assertFalse(needs_update({'tag':'v1.3.9','revision':'b'*40},revision='a'*40))
  self.assertTrue(needs_update({'tag':'v1.4.1','revision':'a'*40},revision='a'*40))
 def test_same_version_queue_pins_commit_and_rejects_race(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'status.json').write_text(json.dumps({'heartbeat':time.time(),'state':'idle'}))
   release={'tag':'v1.4.0','revision':'b'*40}
   with patch('app.updates.installed_revision',return_value='a'*40),patch('app.updates.latest_release',return_value=release):
    u=Updates(root);self.assertEqual(u.status(check=True)['current_revision'],'a'*40);self.assertTrue(u.status()['update_available'])
    with self.assertRaises(ValueError):u.queue('v1.4.0','c'*40)
    u.queue('v1.4.0','b'*40);self.assertEqual(json.loads((root/'request.json').read_text()),release)
   (root/'request.json').unlink()
   with patch('app.updates.installed_revision',return_value='b'*40),patch('app.updates.latest_release',return_value=release):
    u=Updates(root);self.assertFalse(u.status(check=True)['update_available'])
    with self.assertRaises(ValueError):u.queue('v1.4.0','b'*40)
 def test_discovery_resolves_tag_commit(self):
  from app.updates import latest_release
  from unittest.mock import Mock
  r=Mock();r.json.return_value={'tag_name':'v1.4.0','body':'notes'};commit=Mock();commit.json.return_value={'sha':'c'*40}
  with patch('app.updates.requests.get',side_effect=[r,commit]) as get:
   self.assertEqual(latest_release()['revision'],'c'*40);self.assertTrue(get.call_args.args[0].endswith('/commits/v1.4.0'))
 def test_host_rejects_installed_revision_or_changed_request(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'app').mkdir();(root/'state').mkdir();(root/'app/version.py').write_text("VERSION='1.4.0'")
   h=Host(root,root/'state')
   with patch.object(h,'validate_mounts'),patch.object(h,'installed_revision',return_value='a'*40),patch('updater.host.official',return_value='a'*40),patch.object(h,'run') as run:
    h.update('v1.4.0','a'*40);self.assertEqual(h.job['state'],'failed');run.assert_not_called()
    h.update('v1.4.0','b'*40);self.assertEqual(h.job['state'],'failed');run.assert_not_called()
