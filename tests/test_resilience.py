import asyncio
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from backend.config import settings
from backend.db.store import Store
from backend.db.gateway import RegisteredGateway
from backend.errors import AuthorityError
from backend.infrastructure.http_boundaries import HttpBoundaries, RateLimiter
from support import scratch_directory


class LocalStoreTests(unittest.TestCase):
    def test_local_snapshot_refreshes_and_recovers_after_invalid_edit(self):
        with scratch_directory() as directory:
            root=Path(directory);(root/'data').mkdir()
            path=root/'data/knowledge.json'
            path.write_text('[{"title":"old"}]',encoding='utf-8')
            store=Store(settings)
            op=RegisteredGateway(settings).resolve('knowledge.snapshot')
            with patch('backend.db.store.ROOT',root):
                self.assertEqual(store.read(op,{})[0]['title'],'old')
                path.write_text('[{"title":"new content"}]',encoding='utf-8')
                self.assertEqual(store.read(op,{})[0]['title'],'new content')
                path.write_text('{broken',encoding='utf-8')
                with self.assertRaises((ValueError,AuthorityError)):store.read(op,{})
                path.write_text('[{"title":"fixed"}]',encoding='utf-8')
                self.assertEqual(store.read(op,{})[0]['title'],'fixed')

    def test_missing_file_never_serves_cached_snapshot(self):
        with scratch_directory() as directory:
            root=Path(directory);(root/'data').mkdir()
            path=root/'data/knowledge.json';path.write_text('[]',encoding='utf-8')
            store=Store(settings);op=RegisteredGateway(settings).resolve('knowledge.snapshot')
            with patch('backend.db.store.ROOT',root):
                store.read(op,{})
                path.rename(root/'data/knowledge-unavailable.json')
                with self.assertRaises(FileNotFoundError):store.read(op,{})

    def test_local_file_read_is_bounded_before_json_decode(self):
        with scratch_directory() as directory:
            root=Path(directory);(root/'data').mkdir()
            (root/'data/knowledge.json').write_bytes(b' '*((2*1024*1024)+1))
            store=Store(settings);op=RegisteredGateway(settings).resolve('knowledge.snapshot')
            with patch('backend.db.store.ROOT',root), patch('backend.db.store.json.loads') as decode:
                with self.assertRaises(AuthorityError):store.read(op,{})
                decode.assert_not_called()


class ChatCapacityTests(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_chat_is_rejected_but_health_and_next_chat_work(self):
        entered=asyncio.Event();release=asyncio.Event()
        async def endpoint(scope,receive,send):
            if scope['method']=='POST':entered.set();await release.wait()
            await send({'type':'http.response.start','status':200,'headers':[]})
            await send({'type':'http.response.body','body':b'ok'})
        middleware=HttpBoundaries(endpoint,RateLimiter(),max_chats=1)
        async def call(path,method='POST'):
            messages=[]
            async def receive():return {'type':'http.request','body':b'{}','more_body':False}
            async def send(message):messages.append(message)
            scope={'type':'http','method':method,'path':path,'root_path':'/portal','scheme':'http',
                   'server':('localhost',80),'client':('local',1),'headers':[(b'content-type',b'application/json')],'query_string':b''}
            await middleware(scope,receive,send)
            return messages
        first=asyncio.create_task(call('/portal/mambot/api/chat-stream'))
        try:
            await entered.wait()
            blocked=await call('/portal/api/chat')
            self.assertEqual(blocked[0]['status'],503)
            self.assertEqual(dict(blocked[0]['headers'])[b'retry-after'],b'2')
            self.assertIn('request_id',json.loads(blocked[1]['body']))
            self.assertEqual((await call('/portal/mambot/api/health','GET'))[0]['status'],200)
        finally:
            release.set();await first
        self.assertEqual((await call('/portal/mambot/api/chat'))[0]['status'],200)

    async def test_failed_request_releases_capacity(self):
        attempts=0
        async def endpoint(scope,receive,send):
            nonlocal attempts
            attempts+=1
            if attempts==1:raise RuntimeError('secret error')
            await send({'type':'http.response.start','status':200,'headers':[]})
            await send({'type':'http.response.body','body':b'ok'})
        middleware=HttpBoundaries(endpoint,RateLimiter(),max_chats=1)
        async def call():
            output=[]
            async def receive():return {'type':'http.request','body':b'{}','more_body':False}
            async def send(message):output.append(message)
            scope={'type':'http','method':'POST','path':'/api/chat','scheme':'http','server':('localhost',80),
                   'client':('local',1),'headers':[(b'content-type',b'application/json')],'query_string':b''}
            await middleware(scope,receive,send)
            return output[0]['status']
        self.assertEqual(await call(),500)
        self.assertEqual(await call(),200)
