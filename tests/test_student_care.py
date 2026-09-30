import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock, patch
from backend.config import settings
from backend.domain.student_support import support_request
from backend.domain.student_care import care_reply
from backend.services.chat import ChatService


class StudentCareTests(unittest.TestCase):
    def user(self,text):return {'role':'user','content':text}

    def test_family_followup_and_listening_preference(self):
        h=[self.user('Mình áp lực quá')]
        self.assertIn('gia đình',care_reply('Bố mẹ luôn so sánh điểm của mình',h)['answer'])
        h.append(self.user('Mình chỉ muốn được lắng nghe'))
        self.assertIn('chưa đưa lời khuyên',care_reply('Bố mẹ kỳ vọng quá nhiều',h)['answer'])

    def test_assistant_cannot_create_sensitive_context(self):
        self.assertIsNone(care_reply('Bố mẹ mình',[{'role':'assistant','content':'Mình áp lực'}]))

    def test_topic_change_and_backtracking(self):
        h=[self.user('Mình rất cô đơn'),self.user('Học phí HUIT 2026?')]
        self.assertIsNone(care_reply('Bố mẹ mình',h))
        self.assertIsNone(care_reply('Tạo lịch học cho mình',[self.user('Mình mất ngủ')]))

    def test_sustained_sleep_difficulties_and_no_prescribing(self):
        h=[self.user('Mình bị mất ngủ')]
        self.assertIn('chuyên gia',care_reply('Mấy tuần nay rồi',h)['answer'])
        result=care_reply('Mình nên uống thuốc gì?',h)
        self.assertIn('không thể chẩn đoán',result['answer']);self.assertFalse(result['generate'])

    def test_risk_negation_and_followup(self):
        self.assertEqual(support_request('Mình muốn chết',[])['kind'],'urgent')
        self.assertEqual(support_request('Mình không muốn tự tử, chỉ áp lực thôi',[])['kind'],'wellbeing')
        self.assertEqual(support_request('Mình không muốn tự tử nhưng không muốn sống nữa',[])['kind'],'urgent')
        h=[self.user('Mình không muốn sống nữa')]
        self.assertIn('cấp cứu',care_reply('Mình chưa an toàn, không có ai',h)['answer'])
        self.assertIn('đang an toàn',care_reply('Mình đang an toàn',h)['answer'])

    def test_personal_image_schedule_is_not_official_schedule(self):
        self.assertEqual(support_request('Tạo lịch học bằng ảnh',[])['kind'],'study')
        self.assertEqual(support_request('Lịch học HUIT ngày mai',[])['kind'],'official')

    def test_sensitive_context_never_reaches_either_provider(self):
        ops=SimpleNamespace(list_knowledge=Mock(return_value=[]),find_related_knowledge=Mock(return_value=[]))
        service=ChatService(ops,replace(settings,llm_key='test',llm_model='test'))
        with patch('backend.services.chat.generate_support',return_value='Mình có thể giúp bạn viết rõ ý.') as provider:
            result=service.answer('Mình cảm thấy cô đơn',[],'test')
            self.assertEqual(result['mode'],'support');provider.assert_not_called()
            service.answer('Soạn email cho giảng viên',[self.user('Mình cảm thấy cô đơn')],'test')
            self.assertEqual(provider.call_args.args[2],[])

    def test_grounded_provider_drops_sensitive_history(self):
        from backend.operations.knowledge import KnowledgeOperations
        config=replace(settings,data_mode='local',vector_enabled=False,llm_key='test',llm_model='test')
        ops=KnowledgeOperations(config)
        try:
            with patch('backend.services.chat.generate',return_value='Thông tin tham khảo [1].') as provider:
                ChatService(ops,config).answer('Học phí HUIT 2026?', [self.user('Mình rất áp lực')],'test')
                self.assertTrue(provider.called);self.assertEqual(provider.call_args.args[2],[])
        finally:ops.close()
