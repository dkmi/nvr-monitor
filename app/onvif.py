"""ONVIF PullPoint events; bounded HTTP, WS-Security, renewal and clean unsubscribe."""
import base64,copy,datetime,hashlib,secrets,socket,threading,time,uuid
from urllib.parse import unquote,urljoin,urlsplit
import xml.etree.ElementTree as ET
from defusedxml.ElementTree import fromstring
import requests
from requests.auth import HTTPDigestAuth

DEV='http://www.onvif.org/ver10/device/wsdl'
EV='http://www.onvif.org/ver10/events/wsdl'
WSN='http://docs.oasis-open.org/wsn/b-2'
WSA='http://www.w3.org/2005/08/addressing'
WSSE='http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd'
WSU='http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd'
SOAP={'1.2':'http://www.w3.org/2003/05/soap-envelope','1.1':'http://schemas.xmlsoap.org/soap/envelope/'}
MAX_XML=512*1024

class OnvifError(Exception):pass

def local(tag):return tag.rsplit('}',1)[-1]
def child_text(element,name,default=''):
    return next((e.text or default for e in element.iter() if local(e.tag)==name),default)
def element(ns,name,text=None):
    e=ET.Element('{'+ns+'}'+name);e.text=text;return e

def parse_motion(root,states):
    """Only motion topics; OR separate rules/sources, retain true until explicit false."""
    updates=0
    for notification in root.iter():
        if local(notification.tag)!='NotificationMessage':continue
        topic='/'.join(part.rsplit(':',1)[-1] for part in child_text(notification,'Topic').split('/'))
        if 'motion' not in topic.lower():continue
        message=next((e for e in notification.iter() if local(e.tag)=='Message' and ('PropertyOperation' in e.attrib or any(local(x.tag)=='Data' for x in e))),None)
        if message is None:continue
        source=next((e for e in message if local(e.tag)=='Source'),None)
        sources=tuple(sorted((e.get('Name',''),e.get('Value','')) for e in source.iter() if local(e.tag)=='SimpleItem')) if source is not None else ()
        data=next((e for e in message if local(e.tag)=='Data'),None)
        if message.get('PropertyOperation')=='Deleted':
            for key in list(states):
                if key[0]==topic and key[1]==sources:states[key]=False;updates+=1
            continue
        if data is None:continue
        for item in data.iter():
            if local(item.tag)!='SimpleItem' or item.get('Name','').lower() not in ('ismotion','motion','state','logicalstate'):continue
            val=item.get('Value','').strip().lower()
            if val not in ('true','false','1','0','active','inactive'):continue
            key=(topic,sources,item.get('Name',''))
            states[key]=False if message.get('PropertyOperation')=='Deleted' else val in ('true','1','active');updates+=1
    return updates

class Client:
    def __init__(self,camera):
        self.camera=camera;host=camera['host'];host='['+host+']' if ':' in host else host
        self.device=f"http://{host}:{camera.get('onvif_port',80)}/onvif/device_service"
        reuse=camera.get('onvif_use_camera_credentials',True)
        if reuse and camera.get('rtsp_url'):
            stream = urlsplit(camera['rtsp_url'])
            self.username = unquote(stream.username or '')
            self.password = unquote(stream.password or '')
        else:
            self.username=camera['username'] if reuse else camera.get('onvif_username','')
            self.password=camera['password'] if reuse else camera.get('onvif_password','')
        self.http=requests.Session();self.http.trust_env=False
        self.http.auth=HTTPDigestAuth(self.username,self.password)
        self.version=camera.get('onvif_soap','auto');self.offset=0;self.subscription=None;self.references=[]
        self.lease_seconds=60;self.events=None;self.allowed={camera['host']}
        try:self.allowed.update(r[4][0] for r in socket.getaddrinfo(camera['host'],None))
        except OSError:pass

    def safe_url(self,url,base=None):
        url=urljoin(base or self.device,url);p=urlsplit(url)
        if p.scheme!='http' or p.hostname not in self.allowed or p.username or p.password:raise OnvifError('unsafe_endpoint')
        return url

    def call(self,url,body,action,*,auth=True,refs=False,version=None,timeout=9):
        url=self.safe_url(url);version=version or self.version
        if version not in SOAP:raise OnvifError('soap_version')
        soap=SOAP[version];root=element(soap,'Envelope');header=ET.SubElement(root,'{'+soap+'}Header')
        header.append(element(WSA,'Action',action));header.append(element(WSA,'MessageID','urn:uuid:'+str(uuid.uuid4())));header.append(element(WSA,'To',url))
        if refs:
            for ref in self.references:
                ref=copy.deepcopy(ref);ref.set('{'+WSA+'}IsReferenceParameter','true');header.append(ref)
        if auth:
            security=ET.SubElement(header,'{'+WSSE+'}Security');token=ET.SubElement(security,'{'+WSSE+'}UsernameToken')
            token.append(element(WSSE,'Username',self.username));nonce=secrets.token_bytes(20)
            created=datetime.datetime.fromtimestamp(time.time()+self.offset,datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
            digest=base64.b64encode(hashlib.sha1(nonce+created.encode()+self.password.encode()).digest()).decode()
            p=element(WSSE,'Password',digest);p.set('Type','http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordDigest');token.append(p)
            n=element(WSSE,'Nonce',base64.b64encode(nonce).decode());n.set('EncodingType','http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary');token.append(n);token.append(element(WSU,'Created',created))
        ET.SubElement(root,'{'+soap+'}Body').append(body)
        headers={'Content-Type':f'application/soap+xml; charset=utf-8; action="{action}"'} if version=='1.2' else {'Content-Type':'text/xml; charset=utf-8','SOAPAction':'"'+action+'"'}
        try:
            with self.http.post(url,data=ET.tostring(root,encoding='utf-8',xml_declaration=True),headers=headers,timeout=(3,timeout),allow_redirects=False,stream=True) as response:
                if response.status_code in (401,403):raise OnvifError('auth_failed')
                if response.status_code in (301,302,303,307,308):raise OnvifError('redirect_rejected')
                data=bytearray()
                for chunk in response.iter_content(8192):
                    data.extend(chunk)
                    if len(data)>MAX_XML:raise OnvifError('response_too_large')
                try:parsed=fromstring(bytes(data))
                except Exception:raise OnvifError('invalid_soap') from None
                if parsed.tag not in ('{'+SOAP['1.1']+'}Envelope','{'+SOAP['1.2']+'}Envelope'):raise OnvifError('invalid_soap')
                fault=next((e for e in parsed.iter() if local(e.tag)=='Fault'),None)
                if fault is not None:
                    texts=' '.join((e.text or '') for e in fault.iter()).lower()
                    if 'notauthorized' in texts or 'not authorized' in texts:raise OnvifError('auth_failed')
                    raise OnvifError('soap_fault')
                if response.status_code>=400:raise OnvifError('http_error')
                return parsed
        except requests.RequestException:raise OnvifError('network_error') from None

    def discover(self):
        if self.camera.get('channel',1)!=1:raise OnvifError('channel_requires_rtsp')
        versions=['1.2','1.1'] if self.version=='auto' else [self.version];last=OnvifError('unsupported')
        for version in versions:
            try:
                clock=self.call(self.device,element(DEV,'GetSystemDateAndTime'),DEV+'/GetSystemDateAndTime',auth=False,version=version,timeout=5)
                if not any(local(e.tag)=='GetSystemDateAndTimeResponse' for e in clock.iter()):raise OnvifError('invalid_soap')
                self.version=version
                utc=next((e for e in clock.iter() if local(e.tag)=='UTCDateTime'),None)
                if utc is not None:
                    try:
                        parts={local(e.tag):e.text for e in utc.iter()};dt=datetime.datetime(*[int(parts[k]) for k in ('Year','Month','Day','Hour','Minute','Second')],tzinfo=datetime.timezone.utc);self.offset=dt.timestamp()-time.time()
                    except (KeyError,ValueError,TypeError):pass
                break
            except OnvifError as exc:
                if str(exc)=='auth_failed':raise
                last=exc
        else:raise last
        body=element(DEV,'GetServices');body.append(element(DEV,'IncludeCapability','false'))
        try:
            services=self.call(self.device,body,DEV+'/GetServices',timeout=5)
            for service in services.iter():
                if local(service.tag)=='Service' and child_text(service,'Namespace')==EV:self.events=self.safe_url(child_text(service,'XAddr'))
        except OnvifError as exc:
            if str(exc)=='auth_failed':raise
        if not self.events:
            try:
                body=element(DEV,'GetCapabilities');body.append(element(DEV,'Category','All'));caps=self.call(self.device,body,DEV+'/GetCapabilities',timeout=5)
                events=next((e for e in caps.iter() if local(e.tag)=='Events'),None)
                if events is not None:self.events=self.safe_url(child_text(events,'XAddr'))
            except OnvifError as exc:
                if str(exc)=='auth_failed':raise
        if not self.events:self.events=urljoin(self.device,'/onvif/event_service')

    def update_lease(self,response):
        try:
            expires=child_text(response,'TerminationTime');current=child_text(response,'CurrentTime')
            if expires.startswith('PT') and expires.endswith('S'):seconds=float(expires[2:-1])
            else:
                end=datetime.datetime.fromisoformat(expires.replace('Z','+00:00')).timestamp()
                now=datetime.datetime.fromisoformat(current.replace('Z','+00:00')).timestamp() if current else time.time()+self.offset
                seconds=end-now
            if seconds<8:raise OnvifError('lease_too_short')
            self.lease_seconds=min(3600,seconds)
        except (ValueError,TypeError):pass

    def subscribe(self):
        body=element(EV,'CreatePullPointSubscription');body.append(element(EV,'InitialTerminationTime','PT60S'))
        response=self.call(self.events,body,EV+'/EventPortType/CreatePullPointSubscriptionRequest')
        self.update_lease(response)
        ref=next((e for e in response.iter() if local(e.tag)=='SubscriptionReference'),None)
        if ref is None:raise OnvifError('subscription_unsupported')
        address=child_text(ref,'Address')
        if not address:raise OnvifError('subscription_unsupported')
        self.subscription=self.safe_url(address,self.events)
        params=next((e for e in ref if local(e.tag)=='ReferenceParameters'),None)
        self.references=list(params) if params is not None else []
        try:self.call(self.subscription,element(EV,'SetSynchronizationPoint'),EV+'/PullPointSubscription/SetSynchronizationPointRequest',refs=True)
        except OnvifError:pass # Optional on older firmware; polling still works.

    def pull(self):
        body=element(EV,'PullMessages');body.append(element(EV,'Timeout','PT5S'));body.append(element(EV,'MessageLimit','64'))
        result=self.call(self.subscription,body,EV+'/PullPointSubscription/PullMessagesRequest',refs=True,timeout=9)
        if not any(local(e.tag)=='PullMessagesResponse' for e in result.iter()):raise OnvifError('invalid_pull_response')
        return result

    def renew(self):
        body=element(WSN,'Renew');body.append(element(WSN,'TerminationTime','PT60S'))
        result=self.call(self.subscription,body,'http://docs.oasis-open.org/wsn/bw-2/SubscriptionManager/RenewRequest',refs=True)
        self.update_lease(result);return result

    def close(self):
        if self.subscription:
            try:self.call(self.subscription,element(WSN,'Unsubscribe'),'http://docs.oasis-open.org/wsn/bw-2/SubscriptionManager/UnsubscribeRequest',refs=True,timeout=3)
            except OnvifError:pass
        self.http.close();self.subscription=None

class Events(threading.Thread):
    def __init__(self,camera,client_factory=Client):
        super().__init__(daemon=True,name='onvif-'+camera['id']);self.camera=camera;self.factory=client_factory;self.quit=threading.Event();self.lock=threading.Lock()
        self.connected=False;self.active=False;self.status='connecting';self.updates=0;self.last_message=0;self.soap=None
    def snapshot(self):
        with self.lock:return {'connected':self.connected,'active':self.active,'status':self.status,'updates':self.updates,'soap':self.soap}
    def run(self):
        retry=2
        while not self.quit.is_set():
            client=self.factory(self.camera);states={}
            try:
                client.discover();client.subscribe();renew_at=time.monotonic()+min(35,client.lease_seconds*.5);retry=2
                while not self.quit.is_set():
                    start=time.monotonic();root=client.pull();updates=parse_motion(root,states)
                    with self.lock:self.connected=True;self.active=any(states.values());self.status='connected';self.updates+=updates;self.last_message=time.monotonic();self.soap=client.version
                    if time.monotonic()>renew_at:client.renew();renew_at=time.monotonic()+min(35,client.lease_seconds*.5)
                    self.quit.wait(max(0,.5-(time.monotonic()-start)))
            except Exception as exc:
                if isinstance(exc,OnvifError) and str(exc)=='auth_failed':retry=60
                with self.lock:self.connected=False;self.active=False;self.status=str(exc) if isinstance(exc,OnvifError) else 'event_error'
            finally:
                with self.lock:self.connected=False;self.active=False
                client.close()
            if not self.quit.is_set():self.quit.wait(retry);retry=min(30,retry*2)
    def stop(self):self.quit.set()
