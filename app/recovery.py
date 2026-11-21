"""One-time recovery credentials and outbound SMTP."""
import hashlib
import re
import secrets
import smtplib
import ssl
import time
from concurrent.futures import ThreadPoolExecutor
from email.errors import HeaderParseError
from email.headerregistry import Address
from email.message import EmailMessage
from threading import BoundedSemaphore
from urllib.parse import urlsplit

from .storage import password_record

LINK_TTL = 30 * 60
TOKEN = re.compile(r'[A-Za-z0-9_-]{43}')
MAIL_WORKERS = ThreadPoolExecutor(max_workers=2, thread_name_prefix='recovery-mail')
MAIL_SLOTS = BoundedSemaphore(8)


def token_hash(token):
    return hashlib.sha256(token.encode('ascii')).hexdigest()


def valid_email(value):
    if (not isinstance(value, str) or len(value) > 254 or
            not re.fullmatch(r'[!-~]+@[!-~]+', value)):
        raise ValueError('Invalid email address')
    try:
        return Address(addr_spec=value).addr_spec
    except (ValueError, HeaderParseError):
        raise ValueError('Invalid email address') from None


def smtp_settings(value, previous):
    if value.get('enabled') is not True:
        return {**previous, 'enabled': False}
    host = value.get('host', '')
    username = value.get('username', '')
    password = value.get('password')
    if password is None:
        password = previous.get('password', '')
        if password and (host, username) != (previous.get('host'), previous.get('username')):
            raise ValueError('Enter the SMTP password for the new server or account')
    if not isinstance(host, str) or not re.fullmatch(r'[A-Za-z0-9.-]{1,253}', host):
        raise ValueError('Invalid SMTP host')
    port = value.get('port')
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError('Invalid SMTP port')
    security = value.get('security')
    if security not in ('starttls', 'tls'):
        raise ValueError('Select SMTP encryption')
    if (not isinstance(username, str) or not isinstance(password, str) or
            len(username) > 254 or len(password) > 1024 or bool(username) != bool(password)):
        raise ValueError('Enter both SMTP username and password, or leave both empty')
    base = value.get('base_url', '')
    if not isinstance(base, str) or re.search(r'[\s\\#?]', base):
        raise ValueError('Invalid public HTTPS address')
    url = urlsplit(base)
    if (url.scheme != 'https' or not url.hostname or url.username is not None or
            url.path not in ('', '/') or url.port == 0):
        raise ValueError('Invalid public HTTPS address')
    return dict(enabled=True, host=host, port=port, security=security, username=username,
                password=password, sender=valid_email(value.get('sender')), base_url=base.rstrip('/'))


def send_mail(config, recipient, subject, body):
    message = EmailMessage()
    message['From'] = config['sender']
    message['To'] = recipient
    message['Subject'] = subject
    message.set_content(body)
    context = ssl.create_default_context()
    args = (config['host'], config['port'])
    connection = (smtplib.SMTP_SSL(*args, timeout=8, context=context)
                  if config['security'] == 'tls' else smtplib.SMTP(*args, timeout=8))
    with connection as smtp:
        if config['security'] == 'starttls':
            smtp.starttls(context=context)
        if config['username']:
            smtp.login(config['username'], config['password'])
        smtp.send_message(message)


def send_reset_mail(config, recipient, token):
    try:
        send_mail(config, recipient, 'NVR Monitor password reset',
                  f"Choose a new password within 30 minutes: {config['base_url']}/#reset={token}\n"
                  "If you did not request this, you can ignore this email.")
    except (OSError, smtplib.SMTPException, ValueError):
        # Public recovery gives the same response even when delivery fails.
        pass
    finally:
        MAIL_SLOTS.release()


class Recovery:
    def __init__(self, store):
        self.store = store

    def status(self, user_id):
        with self.store.lock:
            row = self.store.db.execute(
                'SELECT email, pending_email, key_hash IS NOT NULL FROM recovery WHERE user_id=?',
                (user_id,),
            ).fetchone()
        email, pending, has_key = row or (None, None, False)
        return dict(email=email, pending_email=pending, has_key=bool(has_key))

    def set_key(self, user_id, generate):
        token = secrets.token_urlsafe(32) if generate else None
        with self.store.lock, self.store.db:
            self.store.db.execute('''INSERT INTO recovery(user_id,key_hash) VALUES(?,?)
                ON CONFLICT(user_id) DO UPDATE SET key_hash=excluded.key_hash''',
                (user_id, token_hash(token) if token else None))
        return token

    def set_email(self, user_id, email):
        with self.store.lock, self.store.db:
            if email is None:
                self.store.db.execute('''UPDATE recovery SET email=NULL, pending_email=NULL,
                    verify_hash=NULL, verify_until=NULL, reset_hash=NULL, reset_until=NULL
                    WHERE user_id=?''', (user_id,))
                return None
            token = secrets.token_urlsafe(32)
            self.store.db.execute('''INSERT INTO recovery(user_id,pending_email,verify_hash,verify_until)
                VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET
                pending_email=excluded.pending_email, verify_hash=excluded.verify_hash,
                verify_until=excluded.verify_until''',
                (user_id, email, token_hash(token), time.time() + LINK_TTL))
            return token

    def verify_email(self, token):
        if not isinstance(token, str) or not TOKEN.fullmatch(token):
            return False
        with self.store.lock, self.store.db:
            changed = self.store.db.execute('''UPDATE recovery SET email=pending_email,
                pending_email=NULL, verify_hash=NULL, verify_until=NULL, reset_hash=NULL, reset_until=NULL
                WHERE verify_hash=? AND verify_until>? AND user_id IN (SELECT id FROM users WHERE enabled=1)''',
                (token_hash(token), time.time()))
            return changed.rowcount == 1

    def request_reset(self, username, config):
        if not config.get('enabled') or not MAIL_SLOTS.acquire(blocking=False):
            return
        submitted = False
        try:
            try:
                username = self.store.normalize_username(username)
            except ValueError:
                return
            now = time.time()
            token = secrets.token_urlsafe(32)
            with self.store.lock, self.store.db:
                user = self.store.db.execute('SELECT id FROM users WHERE username=? AND enabled=1',
                                             (username,)).fetchone()
                if not user:
                    return
                user_id = user[0]
                changed = self.store.db.execute('''UPDATE recovery SET reset_hash=?, reset_until=?
                    WHERE email IS NOT NULL AND (reset_until IS NULL OR reset_until<=?)
                    AND user_id IN (SELECT id FROM users WHERE id=? AND enabled=1)''',
                    (token_hash(token), now + LINK_TTL, now + LINK_TTL - 60, user_id))
                if not changed.rowcount:
                    return
                recipient = self.store.db.execute('SELECT email FROM recovery WHERE user_id=?',
                                                  (user_id,)).fetchone()[0]
            MAIL_WORKERS.submit(send_reset_mail, config, recipient, token)
            submitted = True
        finally:
            if not submitted:
                MAIL_SLOTS.release()

    def reset_password(self, token, method, password, username):
        if not isinstance(token, str) or not TOKEN.fullmatch(token):
            return False
        digest = token_hash(token)
        if method == 'key':
            try:
                username = self.store.normalize_username(username)
            except ValueError:
                return False
            lookup = 'u.username=? AND r.key_hash=?'
            parameters = (username, digest)
        elif method == 'email':
            lookup = 'r.reset_hash=? AND r.reset_until>?'
            parameters = (digest, time.time())
        else:
            return False
        with self.store.lock, self.store.db:
            # Serialize password changes with the maintenance CLI as well.
            self.store.db.execute('BEGIN IMMEDIATE')
            row = self.store.db.execute(f'''SELECT u.id FROM users u JOIN recovery r ON r.user_id=u.id
                WHERE u.enabled=1 AND {lookup}''', parameters).fetchone()
            if not row:
                return False
            salt, hashed = password_record(password)
            self.store.db.execute('UPDATE users SET salt=?, password_hash=?, version=version+1 WHERE id=?',
                                  (salt, hashed, row[0]))
            self.store.db.execute('''UPDATE recovery SET reset_hash=NULL, reset_until=NULL, key_hash=NULL,
                pending_email=NULL, verify_hash=NULL, verify_until=NULL WHERE user_id=?''', (row[0],))
            return True
