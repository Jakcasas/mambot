import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch
from backend.config import settings
from backend.operations.knowledge import KnowledgeOperations
from backend.services.chat import ChatService
from backend.domain.language import requested_topics


class AnswerQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=replace(settings,data_mode='local',vector_enabled=False,llm_key='',llm_model='')
        operations=KnowledgeOperations(cls.config)
        try:cls.records=operations.list_knowledge('quality-tests')
        finally:operations.close()

    def setUp(self):
        self.operations=SimpleNamespace(list_knowledge=lambda request_id:self.records,
                                        find_related_knowledge=lambda query,request_id:[])
        self.service=ChatService(self.operations,self.config)

    def answer(self,q,history=()):return self.service.answer(q,list(history),'quality-tests')

    def sequence(self,questions):
        history=[];results=[]
        for question in questions:
            result=self.answer(question,history);results.append(result)
            history.extend([{'role':'user','content':question},{'role':'assistant','content':result['answer'][:4000]}])
        return results

    def test_year_only_followup_preserves_final_score_warning(self):
        result=self.sequence(['Điểm chuẩn HUIT 2026?','Còn 2025?','2026?'])[-1]
        self.assertTrue(result['answer'].startswith('Mình chưa có điểm chuẩn'))
        self.assertTrue(all(s['category']=='cutoff' for s in result['sources']))

    def test_major_context_does_not_override_score_topic_on_followup(self):
        result=self.sequence(['Ngành CNTT có học bổng không?','Còn điểm chuẩn?','2026?'])[-1]
        self.assertEqual([s['category'] for s in result['sources']],['cutoff'])
        self.assertIn('ĐIỂM SÀN',result['answer'])

    def test_explicit_floor_question_replaces_final_score_request(self):
        result=self.sequence(['Điểm chuẩn CNTT?','Còn điểm sàn?','2026?'])[-1]
        self.assertEqual(result['sources'][0]['category'],'cutoff')
        self.assertFalse(result['answer'].startswith('Mình chưa có điểm chuẩn'))

    def test_unknown_named_major_or_code_never_substitutes_nearby_major(self):
        for question in ['Ngành Y khoa HUIT mã ngành là gì?','Ngành Y khoa học gì?','Mã ngành 9999999?']:
            result=self.answer(question)
            self.assertEqual(result['mode'],'clarification',question)
            self.assertEqual(result['sources'],[],question)
            self.assertNotIn('7540107',result['answer'])

    def test_unknown_major_on_followup_does_not_reuse_previous_known_major(self):
        result=self.sequence(['CNTT học gì?','Còn ngành Y khoa?'])[-1]
        self.assertEqual(result['sources'],[])
        self.assertEqual(result['mode'],'clarification')

    def test_known_major_aliases_still_work_with_code_question(self):
        for question,code in [('Mã ngành data science?','7460108'),('Mã ngành tiếp thị?','7340115')]:
            self.assertIn(code,self.answer(question)['answer'])

    def test_foreign_admission_question_cannot_bypass_scope_using_exam_phrase(self):
        for question in ['Bách Khoa xét tuyển bằng kỳ thi đánh giá năng lực không?',
                         'Đại học Sư phạm xét tuyển bằng đánh giá năng lực không?']:
            result=self.answer(question)
            self.assertEqual(result['mode'],'no-match');self.assertEqual(result['sources'],[])

    def test_huit_exam_issuer_is_not_mistaken_for_foreign_target(self):
        result=self.answer('HUIT xét tuyển bằng kỳ thi đánh giá năng lực của Đại học Sư phạm TP.HCM không?')
        self.assertEqual(result['sources'][0]['category'],'admission')

    def test_two_topics_include_both_evidence_categories_and_citations(self):
        for question,expected in [('Học phí và học bổng HUIT?',['tuition','scholarship']),
                                  ('Học bổng và học phí HUIT?',['scholarship','tuition'])]:
            result=self.answer(question)
            self.assertEqual([s['category'] for s in result['sources']],expected)
            self.assertIn('[1]',result['answer']);self.assertIn('[2]',result['answer'])

    def test_compound_topic_phrases_do_not_create_false_extra_topics(self):
        self.assertEqual(requested_topics('Miễn học phí và học bổng'),['scholarship'])
        self.assertEqual(requested_topics('Điểm sàn xét tuyển HUIT'),['cutoff'])
        self.assertEqual(requested_topics('Hỗ trợ học phí'),['scholarship'])

    def test_missing_topic_does_not_silently_return_only_other_requested_topic(self):
        self.operations.list_knowledge=lambda request_id:[d for d in self.records if d['category']!='scholarship']
        result=self.answer('Học phí và học bổng HUIT?')
        self.assertEqual(result['sources'],[]);self.assertEqual(result['mode'],'no-match')
        self.assertIn('học bổng',result['answer'])

    def test_year_must_be_available_for_every_requested_topic(self):
        self.operations.list_knowledge=lambda request_id:[{**d,'year':2025} if d['category']=='scholarship' else d for d in self.records]
        result=self.answer('Học phí và học bổng năm 2026?')
        self.assertEqual(result['sources'],[]);self.assertEqual(result['mode'],'no-match')

    def test_final_scores_with_another_topic_still_label_floor_first(self):
        result=self.answer('Học phí và điểm chuẩn HUIT?')
        self.assertEqual([s['category'] for s in result['sources']],['tuition','cutoff'])
        self.assertTrue(result['answer'].startswith('Mình chưa có điểm chuẩn'))

    def test_generated_multi_topic_answer_must_cover_all_sources(self):
        self.service=ChatService(self.operations,replace(self.config,llm_key='test-only',llm_model='test-only'))
        with patch('backend.services.chat.generate',return_value='Chỉ có học phí [1]'):
            result=self.answer('Học phí và học bổng HUIT?')
        self.assertEqual(result['mode'],'retrieval');self.assertEqual(len(result['sources']),2)

    def test_thanks_preserves_topic_and_year_without_fabricated_sources(self):
        results=self.sequence(['Học phí HUIT 2026?','Cảm ơn','Còn 2025?'])
        self.assertEqual(results[1]['sources'],[])
        self.assertEqual(results[1]['mode'],'retrieval')
        self.assertIn('học phí cho năm 2025',results[2]['answer'])

    def test_polite_pause_preserves_foreign_school_scope(self):
        result=self.sequence(['Học phí Bách Khoa?','Cảm ơn','Còn học bổng?'])[-1]
        self.assertEqual(result['mode'],'no-match');self.assertEqual(result['sources'],[])

    def test_catalog_count_is_computed_from_current_records_not_hardcoded(self):
        self.operations.list_knowledge=lambda request_id:[d for d in self.records if d['category']=='major'][:2]
        result=self.answer('Trường có những ngành nào?')
        self.assertIn('2 ngành',result['answer']);self.assertIn('Kho tri thức',result['answer'])
        self.assertIn('chưa xác nhận',result['answer'])
