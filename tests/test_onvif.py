import base64,datetime,hashlib,hmac,json,tempfile,threading,time,unittest,uuid
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from unittest.mock import Mock,patch
import xml.etree.ElementTree as ET
from app.onvif import Client,Events,OnvifError,parse_motion,element,local,DEV,EV,WSN,SOAP,WSSE,WSU,WSA
from app.engine import CameraWorker,validate_camera


def notification(value='true',topic='tns1:RuleEngine/CellMotionDetector/Motion',source='one',operation='Changed'):
 return ET.fromstring(f'<NotificationMessage><Topic>{topic}</Topic><Message PropertyOperation="{operation}"><Source><SimpleItem Name="Rule" Value="{source}"/></Source><Data><SimpleItem Name="IsMotion" Value="{value}"/></Data></Message></NotificationMessage>')

class MockCamera:
 def __init__(self,version='1.2',motion_window=None):
  self.version=version;self.motion_window=motion_window;self.started=time.monotonic();self.calls=[];self.auth_errors=[];self.active=False
  owner=self
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_POST(self):
    payload=self.rfile.read(int(self.headers['Content-Length']));root=ET.fromstring(payload);soap=root.tag.split('}')[0][1:];body=next(e for e in root if local(e.tag)=='Body');method=local(list(body)[0].tag);owner.calls.append(method)
    reply=element(soap,'Envelope');out=ET.SubElement(reply,'{'+soap+'}Body')
    if soap!=SOAP[owner.version]:ET.SubElement(out,'Fault').text='VersionMismatch'
    else:
     if method!='GetSystemDateAndTime':
      try:
       token=next(e for e in root.iter() if local(e.tag)=='UsernameToken');values={local(e.tag):e.text for e in token};created=values['Created'];nonce=base64.b64decode(values['Nonce']);expected=base64.b64encode(hashlib.sha1(nonce+created.encode()+b'camera-test-password').digest()).decode();assert hmac.compare_digest(expected,values['Password']);assert values['Username']=='camera-user';dt=datetime.datetime.fromisoformat(created.replace('Z','+00:00'));assert abs(dt.timestamp()-(time.time()+600))<5
       if method in ('PullMessages','Renew','Unsubscribe','SetSynchronizationPoint'):assert any(local(e.tag)=='SubscriptionId' and e.text=='test-subscription' and e.get('{'+WSA+'}IsReferenceParameter')=='true' for e in root.iter())
      except Exception as exc:owner.auth_errors.append(type(exc).__name__);self.send_response(403);self.end_headers();return
     response=ET.SubElement(out,method+'Response')
     if method=='GetSystemDateAndTime':
      dt=datetime.datetime.fromtimestamp(time.time()+600,datetime.timezone.utc);utc=ET.SubElement(response,'UTCDateTime')
      for k,v in zip(('Year','Month','Day','Hour','Minute','Second'),(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second)):ET.SubElement(utc,k).text=str(v)
     elif method=='GetServices':
      service=ET.SubElement(response,'Service');ET.SubElement(service,'Namespace').text=EV;ET.SubElement(service,'XAddr').text=owner.url+'/events'
     elif method=='CreatePullPointSubscription':
      ref=ET.SubElement(response,'SubscriptionReference');ET.SubElement(ref,'Address').text=owner.url+'/subscription';params=ET.SubElement(ref,'ReferenceParameters');ET.SubElement(params,'{urn:test}SubscriptionId').text='test-subscription'
     elif method=='PullMessages':
      active=owner.active
      if owner.motion_window is not None:active=owner.motion_window[0]<=time.monotonic()-owner.started<=owner.motion_window[1]
      response.append(notification('true' if active else 'false'))
    data=ET.tostring(reply);self.send_response(200);self.send_header('Content-Type','application/soap+xml');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);self.url='http://127.0.0.1:'+str(self.server.server_port);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
 def camera(self):return validate_camera({'id':str(uuid.uuid4()),'host':'127.0.0.1','username':'camera-user','password':'camera-test-password','motion':True,'motion_source':'onvif','onvif_port':self.server.server_port,'onvif_fallback':False,'prebuffer':5,'tail':5})
 def close(self):self.server.shutdown();self.server.server_close();self.thread.join()

class OnvifTests(unittest.TestCase):
 def test_motion_states_and_namespace_prefixes(self):
  states={};parse_motion(notification(),states);self.assertTrue(any(states.values()));parse_motion(notification('false',topic='other:RuleEngine/CellMotionDetector/Motion'),states);self.assertFalse(any(states.values()))
  parse_motion(notification('true',source='two'),states);parse_motion(notification('false',source='one'),states);self.assertTrue(any(states.values()))
  before=dict(states);parse_motion(notification('true',topic='RuleEngine/TamperDetector/Tamper'),states);self.assertEqual(before,states)
  deleted=notification(source='two',operation='Deleted');deleted.find('Message').remove(deleted.find('Message/Data'));parse_motion(deleted,states);self.assertFalse(any(states.values()))
 def test_soap_auth_clock_reference_renew_unsubscribe(self):
  for version in ('1.2','1.1'):
   server=MockCamera(version)
   try:
    client=Client(server.camera());client.discover();self.assertEqual(client.version,version);self.assertAlmostEqual(client.offset,600,delta=2);client.subscribe();states={};self.assertEqual(parse_motion(client.pull(),states),1);client.renew();client.close();self.assertIn('Unsubscribe',server.calls);self.assertFalse(server.auth_errors)
   finally:server.close()
 def test_bad_credentials_do_not_retry_other_operations(self):
  server=MockCamera()
  try:
   camera=server.camera();camera['password']='incorrect-password';client=Client(camera)
   with self.assertRaisesRegex(OnvifError,'auth_failed'):client.discover()
   client.close();self.assertEqual(len(server.auth_errors),1);self.assertNotIn('GetCapabilities',server.calls)
  finally:server.close()
 def test_endpoint_limits(self):
  c=Client(validate_camera({'host':'127.0.0.1','username':'u','password':'p'}))
  for url in ('http://evil.example/events','http://user:pass@127.0.0.1/events','https://127.0.0.1/events'):
   with self.assertRaises(OnvifError):c.safe_url(url)
  c.close()
 def test_event_thread_and_shutdown(self):
  server=MockCamera();listener=Events(server.camera());listener.start()
  try:
   deadline=time.monotonic()+5
   while not listener.snapshot()['connected'] and time.monotonic()<deadline:time.sleep(.05)
   self.assertTrue(listener.snapshot()['connected']);server.active=True
   while not listener.snapshot()['active'] and time.monotonic()<deadline:time.sleep(.05)
   self.assertTrue(listener.snapshot()['active'])
  finally:listener.stop();listener.join(5);server.close()
  self.assertFalse(listener.is_alive());self.assertIn('Unsubscribe',server.calls)
 def test_fallback_does_not_restart_video(self):
  with tempfile.TemporaryDirectory() as d:
   camera=validate_camera({'host':'127.0.0.1','motion':True,'motion_source':'onvif'});w=CameraWorker(camera,Path(d)/'cache',Path(d)/'records');state={'connected':False};w.onvif=Mock();w.onvif.snapshot.side_effect=lambda:dict(state);w.producer=object();producer=w.producer
   w.start_detector=Mock(side_effect=lambda:setattr(w,'detector',Mock()))
   try:
    with patch('app.engine.stop_process') as stopped:
     w.reconcile_detection();self.assertEqual(w.detection_mode,'rtsp_fallback');self.assertIsNotNone(w.detector);state['connected']=True;w.reconcile_detection();self.assertEqual(w.detection_mode,'onvif');self.assertIsNone(w.detector);self.assertTrue(stopped.called);self.assertIs(w.producer,producer)
     state['connected']=False;w.camera['onvif_fallback']=False;w.reconcile_detection();self.assertEqual(w.detection_mode,'onvif_connecting');self.assertIsNone(w.detector)
   finally:w.exports.put(None);w.export_thread.join(2)
 def test_validation_defaults(self):
  c=validate_camera({'host':'127.0.0.1'});self.assertEqual(c['motion_source'],'rtsp');self.assertTrue(c['onvif_fallback'])
  for change in ({'motion_source':'bad'},{'onvif_port':0},{'onvif_soap':'2'}):
   with self.assertRaises(ValueError):validate_camera({'host':'127.0.0.1',**change})

if __name__=='__main__':unittest.main()
