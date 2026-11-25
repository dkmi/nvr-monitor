import tempfile
import unittest
from pathlib import Path

from app.server import create_app


class ViewingTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        app = create_app(root / 'data', root / 'recordings', root / 'cache', False)
        self.store = app.extensions['store']
        self.addCleanup(self.store.close)
        self.client = app.test_client()
        response = self.client.post('/api/setup', json={'username': 'owner', 'password': 'owner-password-2026'})
        self.headers = {'X-CSRF-Token': response.json['csrf']}
        self.camera = {'host': '192.0.2.20', 'enabled': False}

    def save(self, **fields):
        return self.client.post('/api/cameras', json={**self.camera, **fields}, headers=self.headers)

    def test_legacy_and_new_cameras_start_at_zero(self):
        older = self.save(name='Existing').json['id']
        saved = self.store.cameras()
        saved[0].pop('live_delay')
        self.store.put('cameras', saved)
        self.store.put('viewing', {'live_delay': 30})
        newer = self.save(name='New').json['id']
        self.assertEqual({c['id']: c['live_delay'] for c in self.client.get('/api/cameras').json},
                         {older: 0, newer: 0})

        for value in (15, 60, 0):
            self.assertEqual(self.save(id=older, live_delay=value).status_code, 200)
            self.assertEqual(self.save(id=older, name='Renamed').status_code, 200)
            self.assertEqual({c['id']: c['live_delay'] for c in self.client.get('/api/cameras').json},
                             {older: value, newer: 0})

    def test_limits_csrf_and_roles(self):
        for value in (-1, 61, True, '30', 2.5, None):
            with self.subTest(value=value):
                self.assertEqual(self.save(live_delay=value).status_code, 400)
        self.assertEqual(self.client.post('/api/cameras', json=self.camera).status_code, 403)
        self.assertEqual(self.save(live_delay=15).status_code, 200)
        self.client.post('/api/users', json={
            'username': 'viewer', 'password': 'viewer-password-2026', 'role': 'full',
        }, headers=self.headers)
        viewer = self.client.application.test_client()
        login = viewer.post('/api/login', json={'username': 'viewer', 'password': 'viewer-password-2026'})
        self.assertEqual(viewer.get('/api/cameras').json[0]['live_delay'], 15)
        self.assertEqual(viewer.post('/api/cameras', json=self.camera, headers={
            'X-CSRF-Token': login.json['csrf'],
        }).status_code, 403)
