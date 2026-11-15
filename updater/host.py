#!/usr/bin/env python3
"""Root-owned host service. No Docker socket or shell commands are exposed to HTTP."""
import argparse, fcntl, hashlib, io, json, os, re, shutil, subprocess, tarfile, threading, time, urllib.request, uuid
from pathlib import Path

API='https://api.github.com/repos/dkmi/nvr-monitor'
SOURCE=('app','static','requirements.txt','Dockerfile','README.md','LICENSE','install.sh','deployment','updater','tests','.gitignore','.dockerignore')
BUSY=('queued','building','backing_up','installing','checking','rolling_back')

def version(tag):
    if not isinstance(tag,str) or not re.fullmatch(r'v?\d{1,5}\.\d{1,5}\.\d{1,5}',tag):raise ValueError('Invalid version')
    return tuple(map(int,tag.lstrip('v').split('.')))

def fetch(url,limit):
    req=urllib.request.Request(url,headers={'Accept':'application/vnd.github+json','User-Agent':'NVR-Monitor-Updater'})
    with urllib.request.urlopen(req,timeout=30) as r:
        body=r.read(limit+1)
    if len(body)>limit:raise ValueError('Download too large')
    return body

def official(tag):
    version(tag);r=json.loads(fetch(API+'/releases/latest',1024*1024))
    if r.get('tag_name')!=tag or r.get('draft') or r.get('prerelease'):raise ValueError('Not the latest stable release')
    commit=json.loads(fetch(API+'/commits/'+tag,1024*1024))['sha']
    if not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('Invalid commit')
    return commit

def unpack(body,dest):
    total=0;count=0
    with tarfile.open(fileobj=io.BytesIO(body),mode='r:gz') as archive:
        for member in archive:
            count+=1;parts=Path(member.name).parts
            if len(parts)<2:continue
            rel=Path(*parts[1:])
            if rel.is_absolute() or '..' in rel.parts or count>10000:raise ValueError('Unsafe archive')
            if rel.parts[0] not in SOURCE:continue
            if member.isdir():continue
            if not member.isfile():raise ValueError('Archive links are not allowed')
            total+=member.size
            if total>100*1024*1024:raise ValueError('Expanded source too large')
            target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True)
            with archive.extractfile(member) as src,target.open('xb') as out:shutil.copyfileobj(src,out)
    if not (dest/'Dockerfile').is_file() or not (dest/'app/version.py').is_file():raise ValueError('Incomplete release')

def atomic(path,value,uid=None):
    tmp=path.with_name('.'+path.name+'-'+uuid.uuid4().hex)
    with tmp.open('x') as f:os.chmod(tmp,0o600);json.dump(value,f);f.flush();os.fsync(f.fileno())
    if uid is not None:os.chown(tmp,uid,uid)
    os.replace(tmp,path)

class Host:
    def __init__(self,root,state_dir):
        self.root=root.resolve();self.queue=self.root/'updates';self.state_dir=state_dir
        self.journal=state_dir/'job.json';self.lock=threading.RLock();self.job={'state':'idle'}
        if self.journal.exists():self.job=json.loads(self.journal.read_text())
    def run(self,args,timeout=1800):
        # Logs are root-only; never return command output to the web client.
        with (self.state_dir/'update.log').open('ab') as log:
            subprocess.run(args,cwd=self.root,stdout=log,stderr=log,check=True,timeout=timeout)
    def output(self,args):return subprocess.check_output(args,cwd=self.root,timeout=30,text=True).strip()
    def compose(self,*args):return ['docker','compose',*args]
    def set(self,state,**values):
        with self.lock:self.job.update(values,state=state);atomic(self.journal,self.job)
    def heartbeat(self):
        with self.lock:
            public={k:self.job.get(k) for k in ('state','tag','finished_at')};public['heartbeat']=time.time()
            atomic(self.queue/'status.json',public,uid=10001)
    def installed(self):
        text=(self.root/'app/version.py').read_text()
        match=re.search(r"VERSION\s*=\s*['\"]([^'\"]+)['\"]",text)
        return match.group(1) if match else '1.4.0'
    def validate_mounts(self):
        conf=json.loads(self.output(self.compose('config','--format','json')))
        mounts={v['target']:v for v in conf['services']['monitor']['volumes']}
        for name in ('data','recordings','cache','updates'):
            v=mounts.get('/'+name,{})
            if v.get('type')!='bind' or Path(v.get('source','')).resolve()!=self.root/name:raise ValueError('Unsupported data mounts; manual update required')
    def snapshot(self,backup):
        (backup/'source').mkdir()
        for name in SOURCE:
            src=self.root/name
            if src.is_dir():shutil.copytree(src,backup/'source'/name,symlinks=True)
            elif src.exists():shutil.copy2(src,backup/'source'/name)
        self.run(['cp','-a',str(self.root/'data'),str(backup/'data')])
        for name in ('compose.yaml','.env'):
            if (self.root/name).exists():shutil.copy2(self.root/name,backup/name)
    def replace_source(self,source):
        for name in SOURCE:
            dst=self.root/name;src=source/name
            if dst.is_dir() and not dst.is_symlink():shutil.rmtree(dst)
            elif dst.exists() or dst.is_symlink():dst.unlink()
            if src.is_dir():shutil.copytree(src,dst,symlinks=True)
            elif src.exists():shutil.copy2(src,dst)
        if (self.root/'install.sh').exists():(self.root/'install.sh').chmod(0o755)
    def healthy(self,expected):
        end=time.monotonic()+150
        while time.monotonic()<end:
            try:
                cid=self.output(self.compose('ps','-q','monitor'))
                health=self.output(['docker','inspect','--format','{{.State.Health.Status}}',cid])
                if health=='healthy':
                    script="import json,urllib.request;print(json.load(urllib.request.urlopen('http://127.0.0.1:8080/api/health',timeout=3))['version'])"
                    if self.output(['docker','exec',cid,'python','-c',script])==expected:return
            except (subprocess.SubprocessError,OSError):pass
            time.sleep(3)
        raise RuntimeError('Updated service did not become healthy')
    def rollback(self):
        backup=Path(self.job['backup']);self.set('rolling_back')
        self.run(self.compose('stop','-t','180','monitor'),240)
        self.replace_source(backup/'source')
        if (self.root/'data').exists():self.run(['mv',str(self.root/'data'),str(backup/('failed-data-'+uuid.uuid4().hex))])
        self.run(['cp','-a',str(backup/'data'),str(self.root/'data')])
        self.run(['docker','tag',self.job['old_image'],self.job['image']])
        self.run(self.compose('up','-d','--no-build','--no-deps','monitor'))
        self.healthy(self.job['previous']);self.set('rolled_back',finished_at=time.time())
    def update(self,tag):
        stopped=False;prepared=False
        try:
            self.set('building',tag=tag,finished_at=None)
            if version(tag)<=version(self.installed()):raise ValueError('Downgrade/reinstall refused')
            self.validate_mounts();sha=official(tag)
            backup=self.root/'backups'/('update-'+time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8])
            backup.parent.mkdir(mode=0o700,exist_ok=True);backup.parent.chmod(0o700);backup.mkdir(mode=0o700)
            stage=backup/'release';stage.mkdir()
            unpack(fetch('https://codeload.github.com/dkmi/nvr-monitor/tar.gz/'+sha,30*1024*1024),stage)
            text=(stage/'app/version.py').read_text();match=re.search(r"VERSION\s*=\s*['\"]([^'\"]+)['\"]",text)
            if not match or version(match.group(1))!=version(tag):raise ValueError('Release version mismatch')
            new_image='nvr-monitor-update:'+sha
            self.run(['docker','build','-t',new_image,str(stage)])
            cid=self.output(self.compose('ps','-q','monitor'))
            image=self.output(['docker','inspect','--format','{{.Config.Image}}',cid]);old=self.output(['docker','inspect','--format','{{.Image}}',cid])
            old_tag='nvr-monitor-rollback:'+uuid.uuid4().hex;self.run(['docker','tag',old,old_tag])
            self.set('backing_up',backup=str(backup),image=image,old_image=old_tag,previous=self.installed())
            stopped=True;self.run(self.compose('stop','-t','180','monitor'),240)
            self.snapshot(backup);prepared=True
            self.set('installing',prepared=True)
            self.replace_source(stage);self.run(['docker','tag',new_image,image])
            self.run(self.compose('up','-d','--no-build','--no-deps','monitor'))
            self.set('checking');self.healthy(tag.lstrip('v'))
            self.set('succeeded',finished_at=time.time())
        except Exception as e:
            print('Update failed:',type(e).__name__,str(e),flush=True)
            try:
                if prepared:self.rollback()
                elif stopped:self.run(self.compose('up','-d','--no-build','--no-deps','monitor'))
            except Exception as rollback_error:
                print('ROLLBACK NEEDS ATTENTION:',type(rollback_error).__name__,str(rollback_error),flush=True)
                self.set('failed',finished_at=time.time());return
            if not prepared:self.set('failed',finished_at=time.time())
    def recover(self):
        if self.job.get('state') not in BUSY:return
        if self.job.get('prepared'):self.rollback()
        else:
            self.run(self.compose('up','-d','--no-build','--no-deps','monitor'))
            self.set('failed',finished_at=time.time())
    def take_request(self):
        path=self.queue/'request.json'
        try:fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        except FileNotFoundError:return None
        try:
            import stat
            if not stat.S_ISREG(os.fstat(fd).st_mode):raise ValueError('Invalid request file')
            with os.fdopen(fd,'rb',closefd=False) as f:body=f.read(1025)
            if len(body)>1024:raise ValueError('Request too large')
            request=json.loads(body);version(request.get('tag'))
            if set(request)!={'tag'}:raise ValueError('Unexpected request fields')
            return request['tag']
        finally:os.close(fd);path.unlink(missing_ok=True)
    def serve(self):
        self.recover();worker=None
        while True:
            self.heartbeat()
            if not worker or not worker.is_alive():
                try:tag=self.take_request()
                except Exception as e:print('Request rejected:',type(e).__name__,flush=True);tag=None
                if tag:
                    self.job={'state':'queued','tag':tag};self.set('queued')
                    worker=threading.Thread(target=self.update,args=(tag,),daemon=True);worker.start()
            time.sleep(3)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--project',required=True);args=parser.parse_args()
    root=Path(args.project).resolve()
    if os.geteuid()!=0:raise SystemExit('Run as root')
    state=Path('/var/lib/nvr-monitor-updater')/hashlib.sha256(str(root).encode()).hexdigest()[:16]
    state.mkdir(parents=True,mode=0o700,exist_ok=True);state.chmod(0o700)
    lock=(state/'lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    Host(root,state).serve()
