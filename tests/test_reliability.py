import asyncio
import json
import unittest
from dataclasses import replace
from datetime import datetime
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from backend.app import app, windows
from backend.config import settings
from backend.domain.sources import trusted_source
from backend.domain.retrieval import excerpt, retrieve
from backend.services.chat import ChatService
from backend.db.store import Store
from backend.db.gateway import RegisteredGateway
from backend.infrastructure.http_boundaries import HttpBoundaries, RateLimiter

class ReliabilityTests(unittest.TestCase):
    def setUp(self):
        windows.clear()

    def test_unexpected_exception_is_safe_json_with_correlated_id(self):
        with TestClient(app) as client, patch('backend.services.chat.retrieve',side_effect=RuntimeError('SECRET_DB_PASSWORD')):
            response=client.post('/api/chat',json={'question':'Học phí?'})
            self.assertEqual(response.status_code,500)
            self.assertNotIn('SECRET_DB_PASSWORD',response.text)
            self.assertEqual(response.json()['request_id'],response.headers['x-request-id'])
            self.assertIn('Content-Security-Policy',response.headers)

    def test_success_response_id_matches_transport_and_audit(self):
        with TestClient(app) as client:
            response=client.post('/api/chat',json={'question':'Học phí?'})
            self.assertEqual(response.json()['request_id'],response.headers['x-request-id'])
        records=[json.loads(line) for line in settings.audit_path.read_text(encoding='utf-8').splitlines()]
        self.assertTrue(any(row['request_id']==response.json()['request_id'] for row in records))

    def test_bad_json_returns_safe_validation_error(self):
        with TestClient(app) as client:
            response=client.post('/api/chat',content=b'{bad',headers={'Content-Type':'application/json'})
            self.assertEqual(response.status_code,422)
            self.assertIn('request_id',response.json())

    def test_bad_content_length_rejected_early(self):
        with TestClient(app) as client:
            for length,code in [('-1',400),('wat',400),('9999999999999999999999999999',413)]:
                response=client.post('/api/chat',content=b'{}',headers={'Content-Type':'application/json','Content-Length':length})
                self.assertEqual(response.status_code,code)

    def test_source_url_policy_never_crashes_on_malformed_urls(self):
        for value in ['https://[','https://ts.huit.edu.vn:wrong/a','https://user@ts.huit.edu.vn','https://ts.huit.edu.vn.evil.com','https://ts.huit.edu.vn\\@evil.com',None,'javascript:alert(1)']:
            self.assertFalse(trusted_source(value))
        self.assertTrue(trusted_source('https://huit.edu.vn/'))
        self.assertTrue(trusted_source('https://ts.huit.edu.vn/path'))

    def test_bad_source_does_not_break_chat(self):
        operations=Mock()
        operations.list_knowledge.return_value=[{'source_url':'https://['}]
        operations.find_related_knowledge.return_value=[]
        result=ChatService(operations,settings).answer('hello world',[],'test')
        self.assertEqual(result['mode'],'no-match')

    def test_long_single_paragraph_has_nonempty_excerpt(self):
        result=excerpt('question',{'text':'Long sentence. '*1000},max_chars=150)
        self.assertTrue(result.startswith('Long sentence.'))
        self.assertLess(len(result),230)

    def test_index_cache_refreshes_when_document_content_changes(self):
        record={'title':'Programming','text':'Python programming','source_url':'https://ts.huit.edu.vn/a','year':2026,'category':'major'}
        before=retrieve('Python programming',[record])
        changed={**record,'title':'Tourism','text':'Hotel travel management'}
        after=retrieve('Python programming',[changed])
        self.assertEqual(before[0]['text'],record['text'])
        self.assertEqual(after,[])

    def test_distinct_chunks_same_url_survive_rank_fusion(self):
        common={'source_url':'https://ts.huit.edu.vn/test','year':2026,'category':'major'}
        a={**common,'title':'Computer science','text':'Programming applications'}
        b={**common,'title':'Mathematics','text':'Linear algebra'}
        found=retrieve('Programming applications',[a,b],[{**a,'score':0.9},{**b,'score':0.8}])
        self.assertEqual(len(found),2)
        self.assertEqual(found[0]['text'],a['text'])

    def test_followup_year_overrides_prior_year(self):
        operations=Mock();operations.list_knowledge.return_value=[];operations.find_related_knowledge.return_value=[]
        with patch('backend.services.chat.retrieve',return_value=[]) as search:
            ChatService(operations,settings).answer('Còn học phí năm 2035?', [{'role':'user','content':'Học bổng CNTT 2026'}],'test')
            self.assertNotIn('2026',search.call_args.args[0])
            self.assertEqual(search.call_args.kwargs['intent_question'],'Còn học phí năm 2035?')

    def test_mongo_datetime_normalization_and_cursor_close(self):
        store=Store(replace(settings,data_mode='mongo',mongo_uri='test-only'))
        record={'title':'Title','text':'Text','source_url':'https://ts.huit.edu.vn','retrieved_at':datetime(2026,7,27)}
        cursor=Mock();cursor.__iter__=Mock(return_value=iter([record]));cursor.limit.return_value=cursor;cursor.max_time_ms.return_value=cursor
        store.client=Mock();store.client.__getitem__=Mock(return_value=store.client);store.client.find.return_value=cursor
        authority=RegisteredGateway(settings).resolve('knowledge.snapshot')
        result=store.read(authority,{})
        self.assertEqual(result[0]['retrieved_at'],'2026-07-27T00:00:00+00:00')
        cursor.close.assert_called_once()
        client=store.client;store.close();client.close.assert_called_once();self.assertIsNone(store.client)

class BodyTransportTests(unittest.IsolatedAsyncioTestCase):
    async def exercise(self,chunks,timeout=1):
        output=[];called=[]
        async def endpoint(scope,receive,send):
            called.append((await receive())['body'])
            await send({'type':'http.response.start','status':200,'headers':[]})
            await send({'type':'http.response.body','body':b'ok'})
        async def receive():
            if chunks:
                return chunks.pop(0)
            await asyncio.sleep(10)
        async def send(message):output.append(message)
        scope={'type':'http','method':'POST','path':'/api/chat','scheme':'http','server':('localhost',80),
               'client':('local',1),'headers':[(b'content-type',b'application/json')],'query_string':b''}
        await HttpBoundaries(endpoint,RateLimiter(),body_timeout=timeout)(scope,receive,send)
        return output,called

    async def test_chunked_body_is_replayed_once(self):
        output,called=await self.exercise([{'type':'http.request','body':b'{','more_body':True},{'type':'http.request','body':b'}','more_body':False}])
        self.assertEqual(called,[b'{}']);self.assertEqual(output[0]['status'],200)

    async def test_oversized_chunked_body_cannot_bypass_limit(self):
        output,called=await self.exercise([{'type':'http.request','body':b'x'*25000,'more_body':True},{'type':'http.request','body':b'x'*25000,'more_body':False}])
        self.assertEqual(output[0]['status'],413);self.assertEqual(called,[])

    async def test_slow_body_times_out(self):
        output,called=await self.exercise([],timeout=.01)
        self.assertEqual(output[0]['status'],408);self.assertEqual(called,[])

    async def test_client_disconnect_does_not_call_application(self):
        output,called=await self.exercise([{'type':'http.disconnect'}])
        self.assertEqual(output,[]);self.assertEqual(called,[])
