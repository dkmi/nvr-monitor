"""Official release discovery and a narrow file queue for the host updater."""
import json, os, re, threading, time
from pathlib import Path
import requests
from .storage import atomic
from .version import VERSION
from .revision import installed_revision

REPOSITORY = 'dkmi/nvr-monitor'
API = 'https://api.github.com/repos/' + REPOSITORY

def version_tuple(tag):
    if not isinstance(tag,str) or not re.fullmatch(r'v?\d{1,5}\.\d{1,5}\.\d{1,5}',tag):
        raise ValueError('Invalid stable version')
    return tuple(map(int,tag.lstrip('v').split('.')))

def latest_release():
    response=requests.get(API+'/releases/latest',headers={'Accept':'application/vnd.github+json'},timeout=(5,15))
    response.raise_for_status();r=response.json();tag=r.get('tag_name')
    version_tuple(tag)
    if r.get('draft') or r.get('prerelease'):raise ValueError('Not a stable release')
    response=requests.get(API+'/commits/'+tag,headers={'Accept':'application/vnd.github+json','Cache-Control':'no-cache'},timeout=(5,15))
    response.raise_for_status();revision=response.json().get('sha')
    if not isinstance(revision,str) or not re.fullmatch('[0-9a-f]{40}',revision):raise ValueError('Invalid release commit')
    return {'revision':revision,'tag':tag,'url':'https://github.com/'+REPOSITORY+'/releases/tag/'+tag,'published_at':r.get('published_at'),'notes':str(r.get('body',''))[:16000]}

def needs_update(release,current=VERSION,revision=None):
    if not release:return False
    remote=version_tuple(release['tag']);local=version_tuple(current)
    return remote>local or (remote==local and bool(release.get('revision')) and release['revision']!=revision)

class Updates:
    def __init__(self,root):
        self.root=Path(root);self.lock=threading.Lock();self.release=None;self.checked=0;self.error=None;self.revision=installed_revision()
    def status(self,check=False):
        with self.lock:
            if check and time.time()-self.checked>=60:
                self.checked=time.time()
                try:self.release=latest_release();self.error=None
                except Exception:self.error='github_unavailable'
            try:host=json.loads((self.root/'status.json').read_text())
            except (OSError,ValueError):host={}
            available=isinstance(host.get('heartbeat'),(int,float)) and 0<=time.time()-host['heartbeat']<30
            return {'current':VERSION,'current_revision':self.revision,'latest':self.release,'checked_at':self.checked or None,'error':self.error,'update_available':needs_update(self.release,revision=self.revision), 'updater_available':available,'job':{k:host.get(k) for k in ('state','tag','message','finished_at')}}
    def queue(self,tag,revision=None):
        with self.lock:
            # Never accept an arbitrary URL, command, prerelease or downgrade.
            release=latest_release()
            if tag!=release['tag'] or not needs_update(release,revision=self.revision):raise ValueError('Only a changed official stable release can be installed')
            if revision is not None and revision!=release.get('revision'):raise ValueError('Release changed; check again')
            try:host=json.loads((self.root/'status.json').read_text())
            except (OSError,ValueError):raise ValueError('Host updater not installed')
            if not 0<=time.time()-host.get('heartbeat',0)<30:raise ValueError('Host updater unavailable')
            if host.get('state') in ('queued','building','backing_up','installing','checking','rolling_back') or (self.root/'request.json').exists():raise ValueError('Update already running')
            payload=json.dumps({'tag':tag,**({'revision':release['revision']} if release.get('revision') else {})}).encode()
            fd=os.open(self.root/'request.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'wb') as f:f.write(payload);f.flush();os.fsync(f.fileno())
            return {'ok':True,'state':'queued','tag':tag}
