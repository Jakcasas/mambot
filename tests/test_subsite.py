import unittest
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app import app, windows
from backend.config import settings
from backend.services.library import LibraryService


class SubsiteTests(unittest.TestCase):
    def setUp(self):
        windows.clear()
        parent=FastAPI()
        parent.mount('/portal', app, name='school')
        self.client=TestClient(parent)
        self.addCleanup(self.client.close)

    def test_canonical_redirect_preserves_external_mount(self):
        for path in ['/portal/', '/portal/mambot']:
            result=self.client.get(path, follow_redirects=False)
            self.assertEqual(result.status_code,307)
            self.assertEqual(result.headers['location'],'/portal/mambot/')
        html=self.client.get('/portal/mambot/').text
        self.assertIn('src="./static/js/app.view.js"',html)
        self.assertNotIn('src="/static/',html)

    def test_subsite_assets_api_stream_and_private_files(self):
        for path in ['static/style.css','static/huit-logo.jpg','static/js/features/chat/chat.api.js','api/health','api/library']:
            result=self.client.get('/portal/mambot/'+path)
            self.assertEqual(result.status_code,200,path)
            self.assertEqual(result.headers['Cache-Control'],'no-store' if path.startswith('api/') else 'no-cache')
        result=self.client.post('/portal/mambot/api/chat-stream',json={'question':'Mã ngành CNTT?'})
        self.assertEqual(result.status_code,200)
        self.assertIn('7480201',result.text)
        for path in ['.env','registry/lock.json','backend/config.py','data/knowledge.json']:
            self.assertEqual(self.client.get('/portal/mambot/'+path).status_code,404)

    def test_mounted_prefix_does_not_bypass_transport_controls(self):
        endpoint='/portal/mambot/api/chat'
        self.assertEqual(self.client.post(endpoint,json={'question':'hi'},headers={'Origin':'https://untrusted.invalid'}).status_code,403)
        self.assertEqual(self.client.post(endpoint,content='x'*50000,headers={'Content-Type':'application/json'}).status_code,413)
        windows.clear()
        for i in range(60):
            # Legacy and canonical endpoints must share one quota.
            path='/portal'+('/mambot' if i%2 else '')+'/api/chat'
            self.assertEqual(self.client.post(path,json={'question':'hi'}).status_code,200)
        blocked=self.client.post(endpoint,json={'question':'hi'})
        self.assertEqual(blocked.status_code,429)
        self.assertEqual(blocked.headers['Retry-After'],'60')
        self.assertEqual(blocked.headers['Cache-Control'],'no-store')

    def test_health_counts_only_trusted_records_and_marks_empty(self):
        operations=SimpleNamespace(list_knowledge=lambda request_id:[{'source_url':'https://untrusted.invalid/x'}])
        health=LibraryService(operations,settings).health('test')
        self.assertEqual(health['records'],0)
        self.assertEqual(health['status'],'empty')
        self.assertIsNone(health['snapshot_date'])
