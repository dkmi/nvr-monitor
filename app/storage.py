"""Authenticated local configuration, atomic metadata and password authentication."""
import base64, hashlib, hmac, json, os, secrets, sqlite3, subprocess, threading
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def atomic(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp-' + secrets.token_hex(6))
    try:
        with open(tmp, 'xb') as f:
            os.chmod(tmp, 0o600); f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 600000)


class Store:
    def __init__(self, root):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True); os.chmod(self.root, 0o700)
        self.lock = threading.RLock()
        keyfile = self.root / 'vault.key'
        if not keyfile.exists(): atomic(keyfile, secrets.token_bytes(32))
        key = keyfile.read_bytes()
        if len(key) != 32: raise ValueError('Invalid vault key')
        # Persisted vault-format labels must survive application renames.
        self.enc_key = hmac.digest(key, b'dahua-web-encryption-v1', 'sha256')
        self.mac_key = hmac.digest(key, b'dahua-web-authentication-v1', 'sha256')
        self.db = sqlite3.connect(self.root / 'config.sqlite', check_same_thread=False)
        try:
            os.chmod(self.root / 'config.sqlite', 0o600)
            self.db.execute('CREATE TABLE IF NOT EXISTS settings (id TEXT PRIMARY KEY, value BLOB NOT NULL)')
            self.db.commit()
            self.init_users()
        except BaseException:
            self.close()
            raise

    def close(self):
        with self.lock:
            self.db.close()

    def seal(self, obj):
        nonce = secrets.token_bytes(12)
        return b'DMW2' + nonce + AESGCM(self.enc_key).encrypt(nonce, json.dumps(obj, ensure_ascii=False).encode(), b'DMW2')

    def unseal(self, data):
        if len(data)<32 or data[:4]!=b'DMW2': raise ValueError('Configuration authentication failed')
        return json.loads(AESGCM(self.enc_key).decrypt(data[4:16], data[16:], b'DMW2'))

    def get(self, key, default=None):
        with self.lock:
            row = self.db.execute('SELECT value FROM settings WHERE id=?', (key,)).fetchone()
            return self.unseal(row[0]) if row else default

    def put(self, key, value):
        with self.lock:
            self.db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', (key,self.seal(value))); self.db.commit()

    def setup(self, password):
        with self.lock:
            if self.get('auth'): raise ValueError('Already configured')
            self.set_password(password)

    def set_password(self, password):
        if not isinstance(password,str) or not 12 <= len(password) <= 256: raise ValueError('Password must have 12–256 characters')
        salt = secrets.token_bytes(24)
        self.put('auth', {'salt':salt.hex(),'hash':password_hash(password,salt).hex()})

    def authenticate(self, password):
        row = self.get('auth')
        return bool(row and hmac.compare_digest(password_hash(password,bytes.fromhex(row['salt'])).hex(),row['hash']))

    def cameras(self): return self.get('cameras', [])

    def init_users(self):
        with self.lock:
            self.db.execute('CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE, salt TEXT NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL, all_cameras INTEGER NOT NULL, enabled INTEGER NOT NULL, version INTEGER NOT NULL DEFAULT 1)')
            self.db.execute('CREATE TABLE IF NOT EXISTS user_cameras (user_id TEXT NOT NULL, camera_id TEXT NOT NULL, PRIMARY KEY(user_id,camera_id))')
            self.db.commit()
            legacy=self.get('auth')
            if legacy and not self.db.execute('SELECT 1 FROM users LIMIT 1').fetchone():
                import uuid
                self.db.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),'admin',legacy['salt'],legacy['hash'],'admin',1,1,1))
                self.db.execute("DELETE FROM settings WHERE id='auth'");self.db.commit()

    def user(self,user_id=None,username=None,private=False):
        with self.lock:
            row=self.db.execute('SELECT id,username,salt,password_hash,role,all_cameras,enabled,version FROM users WHERE '+('id=?' if user_id else 'username=?'),(user_id or self.normalize_username(username),)).fetchone()
            if not row:return None
            out=dict(zip(('id','username','salt','password_hash','role','all_cameras','enabled','version'),row))
            out['all_cameras']=bool(out['all_cameras']);out['enabled']=bool(out['enabled'])
            out['cameras']=[r[0] for r in self.db.execute('SELECT camera_id FROM user_cameras WHERE user_id=?',(out['id'],)).fetchall()]
            if not private:out.pop('salt');out.pop('password_hash')
            return out

    @staticmethod
    def normalize_username(username):
        import re,unicodedata
        if not isinstance(username,str):raise ValueError('Invalid username')
        username=unicodedata.normalize('NFC',username.strip()).casefold()
        if not re.fullmatch(r'[\w.@-]{3,64}',username):raise ValueError('Username: 3–64 letters, numbers, dot, @, underscore or dash')
        return username

    def users(self):
        with self.lock:return [self.user(user_id=r[0]) for r in self.db.execute('SELECT id FROM users ORDER BY username').fetchall()]

    def check_user(self,username,password):
        try:row=self.user(username=username,private=True)
        except ValueError:return None
        if not isinstance(password,str) or len(password)>256:return None
        salt=bytes.fromhex(row['salt']) if row else b'unknown-user-dummy-salt'
        candidate=password_hash(password,salt).hex()
        if not row or not row['enabled'] or not hmac.compare_digest(candidate,row['password_hash']):return None
        return self.user(user_id=row['id'])

    def save_user(self,value,first=False):
        import uuid
        with self.lock:
            if first and self.db.execute('SELECT 1 FROM users LIMIT 1').fetchone():raise ValueError('Already configured')
            username=self.normalize_username(value.get('username',''))
            user_id=str(uuid.UUID(value['id'])) if value.get('id') else str(uuid.uuid4())
            old=self.user(user_id=user_id,private=True)
            if value.get('id') and not old:raise ValueError('Unknown user')
            role='admin' if first else value.get('role','limited')
            if role not in ('admin','full','limited','playback'):raise ValueError('Invalid role')
            enabled=bool(value.get('enabled',True));all_cameras=role in ('admin','full') or (role=='playback' and bool(value.get('all_cameras',False)))
            cameras=sorted(set(str(uuid.UUID(c)) for c in value.get('cameras',[])))
            if old and old['role']=='admin' and old['enabled'] and (role!='admin' or not enabled):
                others=self.db.execute("SELECT count(*) FROM users WHERE role='admin' AND enabled=1 AND id!=?",(user_id,)).fetchone()[0]
                if not others:raise ValueError('Cannot disable or demote the last administrator')
            password=value.get('password')
            if password is None and old:salt=old['salt'];hashed=old['password_hash']
            else:
                if not isinstance(password,str) or not 12<=len(password)<=256:raise ValueError('Password must have 12–256 characters')
                raw=secrets.token_bytes(24);salt=raw.hex();hashed=password_hash(password,raw).hex()
            version=old['version']+1 if old else 1
            try:
                with self.db:
                    self.db.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET username=excluded.username,salt=excluded.salt,password_hash=excluded.password_hash,role=excluded.role,all_cameras=excluded.all_cameras,enabled=excluded.enabled,version=excluded.version',(user_id,username,salt,hashed,role,int(all_cameras),int(enabled),version))
                    self.db.execute('DELETE FROM user_cameras WHERE user_id=?',(user_id,))
                    self.db.executemany('INSERT INTO user_cameras VALUES (?,?)',[(user_id,c) for c in cameras])
            except sqlite3.IntegrityError:raise ValueError('Username already exists')
            return self.user(user_id=user_id)

    def delete_user(self,user_id):
        with self.lock:
            old=self.user(user_id=user_id)
            if not old:raise ValueError('Unknown user')
            if old['role']=='admin' and old['enabled'] and not self.db.execute("SELECT 1 FROM users WHERE role='admin' AND enabled=1 AND id!=?",(user_id,)).fetchone():raise ValueError('Cannot delete the last administrator')
            with self.db:
                self.db.execute('DELETE FROM user_cameras WHERE user_id=?',(user_id,));self.db.execute('DELETE FROM users WHERE id=?',(user_id,))
