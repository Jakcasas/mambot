import json
import unittest
from dataclasses import replace
from unittest.mock import patch
import httpx
from backend.config import settings
from backend.infrastructure.llm import generate, MAX_RESPONSE_BYTES
from backend.operations.knowledge import KnowledgeOperations
from backend.services.chat import ChatService

REAL_CLIENT=httpx.Client

class Chunks(httpx.SyncByteStream):
    def __init__(self,chunks):self.chunks=chunks;self.closed=False
    def __iter__(self):yield from self.chunks
    def close(self):self.closed=True


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.settings=replace(settings,llm_key='test-only',llm_model='test-only')

    def provider(self,payload=None,headers=None,status=200,chunks=None):
        stream=Chunks(chunks if chunks is not None else [json.dumps(payload,ensure_ascii=False).encode()])
        def handler(request):
            self.assertEqual(request.headers['accept-encoding'],'identity')
            return httpx.Response(status,headers=headers or {'Content-Type':'application/json'},stream=stream)
        factory=lambda **kwargs:REAL_CLIENT(transport=httpx.MockTransport(handler),**kwargs)
        return patch('backend.infrastructure.llm.httpx.Client',side_effect=factory),stream

    def test_complete_answer_is_preserved_and_stream_is_closed(self):
        provider,stream=self.provider({'choices':[{'finish_reason':'stop','message':{'content':' Câu trả lời [1] '}}]})
        with provider:self.assertEqual(generate(self.settings,'question',[],[]),'Câu trả lời [1]')
        self.assertTrue(stream.closed)

    def test_provider_receives_the_year_of_each_evidence_source(self):
        def handler(request):
            payload=json.loads(request.content)
            evidence=json.loads(payload['messages'][-1]['content'].split('\nCâu hỏi:')[0].removeprefix('EVIDENCE: '))
            self.assertEqual([d['year'] for d in evidence],[2025,2026])
            self.assertEqual([d['citation'] for d in evidence],[1,2])
            reply={'choices':[{'finish_reason':'stop','message':{'content':'Hai năm [1] [2]'}}]}
            return httpx.Response(200,headers={'Content-Type':'application/json'},stream=Chunks([json.dumps(reply).encode()]))
        factory=lambda **kwargs:REAL_CLIENT(transport=httpx.MockTransport(handler),**kwargs)
        docs=[{'title':'Cùng tiêu đề','text':'Cùng nội dung','year':year} for year in (2025,2026)]
        with patch('backend.infrastructure.llm.httpx.Client',side_effect=factory):
            self.assertEqual(generate(self.settings,'So sánh hai năm',[],docs),'Hai năm [1] [2]')

    def test_truncated_filtered_empty_and_malformed_answers_are_rejected(self):
        for payload in [None,[],{'choices':[]},{'error':{'message':'unavailable'}},
                        {'choices':[{'finish_reason':'length','message':{'content':'Answer [1]'}}]},
                        {'choices':[{'finish_reason':'content_filter','message':{'content':'Answer [1]'}}]},
                        {'choices':[{'finish_reason':'stop','message':{'content':' '}}]},
                        {'choices':[{'finish_reason':'stop','message':{'content':'x'*6501}}]},
                        {'choices':[{'finish_reason':'stop','message':None}]}]:
            with self.subTest(payload=str(payload)[:60]):
                provider,stream=self.provider(payload)
                with provider:self.assertIsNone(generate(self.settings,'question',[],[]))
                self.assertTrue(stream.closed)

    def test_wrong_mime_compression_and_oversize_header_stop_before_read(self):
        for headers in [{'Content-Type':'text/html'},
                        {'Content-Type':'application/json','Content-Encoding':'gzip'},
                        {'Content-Type':'application/json','Content-Length':str(MAX_RESPONSE_BYTES+1)}]:
            provider,stream=self.provider(None,headers=headers)
            with provider,self.assertRaises(ValueError):generate(self.settings,'question',[],[])
            self.assertTrue(stream.closed)

    def test_chunked_response_size_limit_and_utf8_validation(self):
        for chunks in [[b'x'*70000,b'x'*70000],[b'\xff']]:
            provider,stream=self.provider(chunks=chunks)
            with provider,self.assertRaises(ValueError):generate(self.settings,'question',[],[])
            self.assertTrue(stream.closed)

    def test_total_response_budget_closes_stream(self):
        provider,stream=self.provider(chunks=[b'{',b'}'])
        with provider,patch('backend.infrastructure.llm.time.monotonic',side_effect=[0,1,21]),self.assertRaises(TimeoutError):
            generate(self.settings,'question',[],[])
        self.assertTrue(stream.closed)

    def test_http_failure_closes_stream(self):
        provider,stream=self.provider(None,status=503)
        with provider,self.assertRaises(httpx.HTTPStatusError):generate(self.settings,'question',[],[])
        self.assertTrue(stream.closed)

    def test_truncated_provider_output_falls_back_to_full_source_excerpt(self):
        provider,_=self.provider({'choices':[{'finish_reason':'length','message':{'content':'Mã ngành là 74 [1]'}}]})
        service=ChatService(KnowledgeOperations(settings),self.settings)
        with provider:result=service.answer('Mã ngành công nghệ thông tin?',[],'provider-test')
        self.assertEqual(result['mode'],'retrieval')
        self.assertIn('7480201',result['answer'])
        self.assertTrue(result['warning']);self.assertTrue(result['sources'])
