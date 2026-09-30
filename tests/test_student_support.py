import json
import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock, patch
import httpx
from fastapi.testclient import TestClient
from backend.app import app, windows
from backend.config import settings
from backend.operations.knowledge import KnowledgeOperations
from backend.services.chat import ChatService
from backend.domain.student_support import study_plan, support_request
from backend.infrastructure.llm import generate_support
from tests.test_provider import Chunks, REAL_CLIENT


class StudentSupportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=replace(settings,data_mode='local',vector_enabled=False,llm_key='',llm_model='')
        operations=KnowledgeOperations(cls.config)
        try:cls.records=operations.list_knowledge('student-support-tests')
        finally:operations.close()

    def setUp(self):
        self.operations=SimpleNamespace(list_knowledge=Mock(return_value=self.records),find_related_knowledge=Mock(return_value=[]))
        self.service=ChatService(self.operations,self.config)

    def answer(self,question,history=()):return self.service.answer(question,list(history),'student-tests')

    def sequence(self,questions):
        history=[];results=[]
        for question in questions:
            result=self.answer(question,history);results.append(result)
            history.extend([{'role':'user','content':question},{'role':'assistant','content':result['answer']}])
        return results

    def test_natural_greetings_need_no_database_or_model(self):
        for question in ['Chào Mambot nhé!','Hi bạn 👋','Xin chao ban a','Mambot ơi']:
            result=self.answer(question)
            self.assertIn('Chào bạn',result['answer']);self.assertEqual(result['sources'],[])
        self.operations.list_knowledge.assert_not_called()

    def test_compound_greeting_does_not_hide_the_actual_question(self):
        result=self.answer('Chào Mambot, học phí HUIT năm 2026 thế nào?')
        self.assertEqual(result['sources'][0]['category'],'tuition')

    def test_identity_is_honest_and_help_is_actionable(self):
        result=self.answer('Bạn là ai?')
        self.assertEqual(result['mode'],'support')
        self.assertIn('trợ lý AI',result['answer']);self.assertIn('không truy cập',result['answer'])

    def test_social_turns_preserve_grounded_topic_and_year(self):
        result=self.sequence(['Học phí HUIT 2026?','Chào Mambot','Cảm ơn bạn nhiều nhé!','Còn 2025?'])[-1]
        self.assertEqual(result['mode'],'no-match');self.assertIn('học phí cho năm 2025',result['answer'])

    def test_study_prompt_asks_for_missing_constraints(self):
        result=self.answer('Giúp mình lập kế hoạch ôn thi')
        self.assertEqual(result['mode'],'support');self.assertIn('số ngày',result['answer'])
        self.operations.list_knowledge.assert_not_called()

    def test_study_plan_uses_followup_subject_days_and_daily_budget(self):
        results=self.sequence(['Giúp mình lập kế hoạch ôn thi','Giải tích, 7 ngày, 2 giờ mỗi ngày'])
        answer=results[-1]['answer']
        for part in ['Giải tích','7 ngày · 120 phút/ngày','37 + 37 + 36','2 lần nghỉ 5','không phải lịch thi']:
            self.assertIn(part,answer)
        self.assertEqual(results[-1]['sources'],[])

    def test_shortened_plan_keeps_the_previous_daily_budget(self):
        result=self.sequence(['Lập kế hoạch ôn thi Python 7 ngày, 1,5 giờ mỗi ngày','Còn 3 ngày thôi'])[-1]
        self.assertIn('3 ngày · 90 phút/ngày',result['answer'])

    def test_study_budget_is_bounded_and_zero_is_not_silently_defaulted(self):
        for text,expected in [('ôn thi 0 ngày, 2 giờ','1 đến 90'),('ôn thi 100 ngày, 2 giờ','1 đến 90'),
                              ('ôn thi 7 ngày, 0 phút','10–480'),('ôn thi 7 ngày, 999 giờ','10–480'),
                              ('ôn thi -7 ngày, 2 giờ','1 đến 90'),('ôn thi 7 ngày, -30 phút','10–480')]:
            with self.subTest(text=text):self.assertIn(expected,self.answer(text)['answer'])

    def test_one_day_plan_does_not_invent_more_days(self):
        answer=study_plan(['ôn thi 1 ngày, 30 phút'])
        self.assertIn('Hôm nay',answer);self.assertNotIn('Ngày 2',answer)

    def test_short_plans_keep_a_final_review_day_and_readable_day_labels(self):
        for days in (2,3,7):
            answer=study_plan([f'ôn thi {days} ngày, 30 phút'])
            self.assertIn(f'Ngày {days}: làm bài tổng hợp',answer)
            self.assertNotIn(f'{days}–{days}',answer)

    def test_study_to_tuition_switch_returns_evidence(self):
        result=self.sequence(['Lập kế hoạch ôn thi','7 ngày, 2 giờ mỗi ngày','Học phí HUIT 2026?'])[-1]
        self.assertEqual(result['mode'],'retrieval');self.assertEqual(result['sources'][0]['category'],'tuition')

    def test_unrelated_topic_stops_support_inheritance(self):
        result=self.sequence(['Lập kế hoạch ôn thi','Marketing'])[-1]
        self.assertEqual(result['sources'][0]['category'],'major');self.assertIn('7340115',result['answer'])
        result=self.sequence(['Lập kế hoạch ôn thi','thời tiết Paris'])[-1]
        self.assertEqual(result['mode'],'no-match')

    def test_support_context_does_not_cross_an_intervening_topic(self):
        history=[{'role':'user','content':'Lập kế hoạch ôn thi'}, {'role':'user','content':'Marketing'}]
        self.assertIsNone(support_request('7 ngày, 2 giờ mỗi ngày',history))

    def test_assistant_text_cannot_choose_support_intent(self):
        self.assertIsNone(support_request('7 ngày, 2 giờ', [{'role':'assistant','content':'Lập kế hoạch ôn thi'}]))

    def test_common_student_help_has_no_fake_citations(self):
        for question in ['Soạn email cho giảng viên','Giúp mình chuẩn bị thuyết trình','Nhóm mình cần chia việc',
                         'Mình rất áp lực','Mình là tân sinh viên','Mình chưa biết chọn ngành nào']:
            with self.subTest(question=question):
                result=self.answer(question)
                self.assertEqual(result['mode'],'support');self.assertEqual(result['sources'],[])
                self.assertNotIn('[1]',result['answer']);self.assertGreater(len(result['answer']),150)

    def test_orientation_interests_can_return_to_grounded_programs(self):
        result=self.sequence(['Mình chưa biết chọn ngành nào','Mình thích lập trình game'])[-1]
        self.assertTrue(result['sources']);self.assertEqual(result['sources'][0]['category'],'major')

    def test_private_and_unverified_policies_never_call_a_model(self):
        self.service.settings=replace(self.config,llm_key='test-only',llm_model='test-only')
        with patch('backend.services.chat.generate_support') as provider:
            for question in ['Lịch thi HUIT ngày mai?','Bảng điểm của mình','Hướng dẫn đăng ký tín chỉ',
                             'Quên mật khẩu cổng sinh viên','Điều kiện tốt nghiệp HUIT?',
                             'Giải thích quy chế HUIT','Hướng dẫn đăng ký tín chỉ HUIT']:
                result=self.answer(question)
                self.assertEqual(result['mode'],'support');self.assertIn('chưa có nguồn',result['answer'])
            provider.assert_not_called()
        self.operations.list_knowledge.assert_not_called()

    def test_email_about_policy_remains_a_draft_with_placeholders(self):
        result=self.answer('Soạn email hỏi phòng đào tạo về lịch thi')
        self.assertIn('bản nháp',result['answer']);self.assertIn('[',result['answer'])
        self.assertIn('chưa gửi email',result['answer'])

    def test_email_followup_changes_the_purpose_of_the_draft(self):
        result=self.sequence(['Soạn email cho giảng viên','Xin gia hạn nộp bài'])[-1]
        self.assertIn('Tiêu đề: [Học phần] — xin gia hạn nộp bài',result['answer'])

    def test_official_email_context_stays_local_on_followup(self):
        self.service.settings=replace(self.config,llm_key='test-only',llm_model='test-only')
        with patch('backend.services.chat.generate_support') as provider:
            result=self.sequence(['Soạn email cho phòng đào tạo','Xin gia hạn nộp bài'])[-1]
            self.assertEqual(result['mode'],'support');self.assertIn('xin gia hạn nộp bài',result['answer'])
            provider.assert_not_called()

    def test_local_learning_explanation_contains_a_worked_example(self):
        result=self.answer('Giải thích vòng lặp Python')
        self.assertEqual(result['mode'],'support');self.assertIn('for i in range(3):',result['answer'])
        self.assertIn('0, 1, 2',result['answer'])

    def test_explaining_a_university_major_still_requires_evidence(self):
        result=self.answer('Giải thích ngành Trí tuệ nhân tạo HUIT học gì')
        self.assertEqual(result['mode'],'retrieval');self.assertTrue(result['sources'])

    def test_distress_response_is_local_even_if_model_configured(self):
        self.service.settings=replace(self.config,llm_key='test-only',llm_model='test-only')
        with patch('backend.services.chat.generate_support') as provider:
            result=self.answer('Mình không muốn sống nữa')
            self.assertIn('an toàn',result['answer']);provider.assert_not_called()

    def test_support_can_use_configured_model_without_claiming_sources(self):
        self.service.settings=replace(self.config,llm_key='test-only',llm_model='test-only')
        with patch('backend.services.chat.generate_support',return_value='Một vòng lặp thực hiện lại một nhóm lệnh.'):
            result=self.answer('Giải thích vòng lặp Python')
        self.assertEqual(result['mode'],'conversation');self.assertEqual(result['sources'],[])
        self.operations.list_knowledge.assert_not_called()

    def test_provider_failure_keeps_a_usable_local_answer_and_no_error_details(self):
        self.service.settings=replace(self.config,llm_key='test-only',llm_model='test-only')
        with patch('backend.services.chat.generate_support',side_effect=RuntimeError('secret')):
            result=self.answer('Soạn email cho giảng viên')
        self.assertEqual(result['mode'],'support');self.assertIn('Tiêu đề:',result['answer'])
        self.assertNotIn('secret',json.dumps(result));self.assertTrue(result['warning'])

    def test_fake_citation_link_or_policy_from_support_provider_falls_back(self):
        self.service.settings=replace(self.config,llm_key='test-only',llm_model='test-only')
        for answer in ['Lời khuyên [1]','Mở https://example.org','Học phí là 10 đồng','']:
            with self.subTest(answer=answer),patch('backend.services.chat.generate_support',return_value=answer):
                self.assertEqual(self.answer('Soạn email cho giảng viên')['mode'],'support')

    def test_general_model_has_dedicated_prompt_bounded_user_history_and_budget(self):
        config=replace(self.config,llm_key='test-only',llm_model='test-only')
        def handler(request):
            data=json.loads(request.content);messages=data['messages']
            self.assertEqual(len(messages),6);self.assertEqual(messages[0]['role'],'system')
            self.assertIn('KHÔNG có nguồn',messages[0]['content'])
            self.assertEqual(messages[-1]['content'],'Giải thích vòng lặp')
            self.assertEqual([m['role'] for m in messages[1:]],['user']*5)
            self.assertTrue(all(len(m['content'])<=800 for m in messages[1:]))
            self.assertEqual(data['max_tokens'],700)
            payload={'choices':[{'finish_reason':'stop','message':{'content':'Một vòng lặp lặp lại các lệnh.'}}]}
            return httpx.Response(200,headers={'Content-Type':'application/json'},stream=Chunks([json.dumps(payload).encode()]))
        factory=lambda **kwargs:REAL_CLIENT(transport=httpx.MockTransport(handler),**kwargs)
        with patch('backend.infrastructure.llm.httpx.Client',side_effect=factory):
            result=generate_support(config,'Giải thích vòng lặp',['x'*900]*10)
        self.assertIn('vòng lặp',result)

    def test_new_support_mode_obeys_stream_contract(self):
        windows.clear()
        with TestClient(app) as client:
            reply=client.post('/mambot/api/chat-stream',json={'question':'Giúp mình lập kế hoạch ôn thi'})
        self.assertEqual(reply.status_code,200)
        events=[json.loads(line) for line in reply.text.splitlines()]
        self.assertEqual(events[0]['mode'],'support');self.assertEqual(events[-1]['type'],'done')
        self.assertEqual(events[-2],{'type':'sources','sources':[]})
