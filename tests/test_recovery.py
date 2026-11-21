import re
import tempfile
import time
import unittest
from contextlib import closing
from pathlib import Path
from threading import Barrier, Thread
from unittest.mock import patch

from app.recovery import Recovery, send_mail
from app.server import create_app
from app.storage import Store

PASSWORD = 'synthetic-original-password'
NEW_PASSWORD = 'synthetic-replacement-password'
MAIL = {
    'enabled': True, 'host': 'smtp.gmail.com', 'port': 587, 'security': 'starttls',
    'username': 'sender@example.com', 'password': 'synthetic-app-password',
    'sender': 'sender@example.com', 'base_url': 'https://example.com/',
}


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.app = create_app(self.root / 'data', self.root / 'records', self.root / 'cache', False)
        self.store = self.app.extensions['store']
        self.addCleanup(self.store.close)
        self.admin = self.app.test_client()
        self.public = self.app.test_client()
        session = self.admin.post('/api/setup', json={'username': 'owner', 'password': PASSWORD}).json
        self.csrf = {'X-CSRF-Token': session['csrf']}
        self.user = session['user']

    def admin_post(self, path, body):
        return self.admin.post('/api/' + path, headers=self.csrf, json=body)

    def activate_mail(self):
        result = self.admin_post('smtp', MAIL)
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json['has_password'])
        self.assertNotIn('password', result.json)

    def test_smtp_access_secrets_and_test_delivery(self):
        self.assertEqual(self.public.get('/api/smtp').status_code, 401)
        self.store.save_user({'username': 'viewer', 'password': PASSWORD, 'role': 'full'})
        viewer = self.app.test_client()
        login = viewer.post('/api/login', json={'username': 'viewer', 'password': PASSWORD})
        self.assertEqual(viewer.get('/api/smtp').status_code, 403)
        self.assertEqual(viewer.post('/api/smtp/test', json={'recipient': 'owner@example.com'},
                                    headers={'X-CSRF-Token': login.json['csrf']}).status_code, 403)
        self.assertEqual(self.admin.post('/api/smtp', json=MAIL).status_code, 403)
        self.activate_mail()
        self.assertNotIn(MAIL['password'].encode(), (self.root / 'data/config.sqlite').read_bytes())
        changed_host = {key: value for key, value in MAIL.items() if key != 'password'}
        self.assertEqual(self.admin_post('smtp', {**changed_host, 'host': 'relay.example.com'}).status_code, 400)
        self.assertEqual(self.admin_post('smtp', {**MAIL, 'base_url': 'https://example.com@other.example'}).status_code, 400)
        with patch('app.server.send_mail') as deliver:
            self.assertEqual(self.admin_post('smtp/test', {'recipient': 'owner@example.com'}).status_code, 200)
            self.assertEqual(deliver.call_args.args[1], 'owner@example.com')
            self.assertEqual(deliver.call_args.args[0]['password'], MAIL['password'])

    def test_email_confirmation_and_reset_are_one_time(self):
        self.activate_mail()
        recipient = 'owner@example.com'
        with patch('app.server.send_mail') as deliver:
            response = self.admin_post('recovery', {
                'action': 'verify_email', 'password': PASSWORD, 'email': recipient,
            })
            self.assertEqual(response.status_code, 200)
            token = re.search(r'#verify=(\S+)', deliver.call_args.args[3])[1]
            self.assertEqual(deliver.call_args.args[1], recipient)
        with patch('app.recovery.MAIL_WORKERS.submit') as submit:
            unknown = self.public.post('/api/recovery/request', json={'username': 'unknown'})
            pending = self.public.post('/api/recovery/request', json={'username': 'owner'})
            self.assertEqual((unknown.status_code, unknown.json), (pending.status_code, pending.json))
            submit.assert_not_called()
        self.assertEqual(self.public.post('/api/recovery/verify', json={'token': token}).status_code, 200)
        self.assertEqual(self.public.post('/api/recovery/verify', json={'token': token}).status_code, 400)
        with patch('app.recovery.MAIL_WORKERS.submit', side_effect=lambda fn, *args: fn(*args)), \
                patch('app.recovery.send_mail') as deliver:
            response = self.public.post('/api/recovery/request', json={'username': 'owner'},
                                        headers={'Host': 'untrusted.example'})
            self.assertEqual(response.status_code, 202)
            body = deliver.call_args.args[3]
            self.assertIn('https://example.com/#reset=', body)
            reset_token = re.search(r'#reset=(\S+)', body)[1]
        payload = {'token': reset_token, 'method': 'email', 'password': NEW_PASSWORD}
        self.assertEqual(self.public.post('/api/recovery/reset', json=payload).status_code, 200)
        self.assertEqual(self.public.post('/api/recovery/reset', json=payload).status_code, 400)
        self.assertFalse(self.admin.get('/api/state').json['authenticated'])
        self.assertIsNone(self.store.check_user('owner', PASSWORD))
        self.assertIsNotNone(self.store.check_user('owner', NEW_PASSWORD))

    def test_recovery_key_rotation_and_concurrent_reuse(self):
        body = {'action': 'create_key', 'password': PASSWORD}
        self.assertEqual(self.admin_post('recovery', {**body, 'password': 'incorrect'}).status_code, 403)
        old = self.admin_post('recovery', body).json['key']
        key = self.admin_post('recovery', body).json['key']
        self.assertNotIn(key.encode(), (self.root / 'data/config.sqlite').read_bytes())
        self.assertEqual(self.admin.get('/api/recovery').json,
                         {'email': None, 'pending_email': None, 'has_key': True, 'email_available': False})
        self.assertFalse(Recovery(self.store).reset_password(old, 'key', NEW_PASSWORD, 'owner'))
        start = Barrier(2)
        results = []

        def reset():
            with closing(Store(self.root / 'data')) as store:
                start.wait(timeout=5)
                results.append(Recovery(store).reset_password(key, 'key', NEW_PASSWORD, 'owner'))

        threads = [Thread(target=reset) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        self.assertEqual(sorted(results), [False, True])
        self.assertFalse(self.admin.get('/api/state').json['authenticated'])

    def test_expired_tokens_and_password_changes(self):
        recovery = Recovery(self.store)
        key = recovery.set_key(self.user['id'], True)
        with patch('app.recovery.time.time', return_value=time.time() - 1900):
            verify = recovery.set_email(self.user['id'], 'owner@example.com')
        self.assertFalse(recovery.verify_email(verify))
        verify = recovery.set_email(self.user['id'], 'owner@example.com')
        self.assertTrue(recovery.verify_email(verify))
        with patch('app.recovery.time.time', return_value=time.time() - 1900), \
                patch('app.recovery.MAIL_WORKERS.submit', side_effect=lambda fn, *args: fn(*args)), \
                patch('app.recovery.send_mail') as deliver:
            recovery.request_reset('owner', MAIL)
            reset = re.search(r'#reset=(\S+)', deliver.call_args.args[3])[1]
        self.assertFalse(recovery.reset_password(reset, 'email', NEW_PASSWORD, None))
        self.store.save_user({**self.user, 'password': NEW_PASSWORD})
        self.assertFalse(recovery.reset_password(key, 'key', PASSWORD, 'owner'))

    def test_smtp_requires_tls_before_login(self):
        with patch('app.recovery.smtplib.SMTP') as connection:
            smtp = connection.return_value.__enter__.return_value
            send_mail(MAIL, 'owner@example.com', 'Test', 'Message')
            self.assertEqual([call[0] for call in smtp.method_calls], ['starttls', 'login', 'send_message'])
        with patch('app.recovery.smtplib.SMTP_SSL') as connection:
            smtp = connection.return_value.__enter__.return_value
            send_mail({**MAIL, 'security': 'tls', 'port': 465}, 'owner@example.com', 'Test', 'Message')
            self.assertEqual([call[0] for call in smtp.method_calls], ['login', 'send_message'])
