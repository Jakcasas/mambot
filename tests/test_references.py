import unittest
from dataclasses import replace
from types import SimpleNamespace
from backend.config import settings
from backend.operations.knowledge import KnowledgeOperations
from backend.services.chat import ChatService


class ReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=replace(settings,data_mode='local',vector_enabled=False,llm_key='',llm_model='')
        operations=KnowledgeOperations(cls.config)
        try:cls.records=operations.list_knowledge('reference-tests')
        finally:operations.close()

    def setUp(self):
        self.service=ChatService(SimpleNamespace(list_knowledge=lambda request_id:self.records,
                                                find_related_knowledge=lambda query,request_id:[]),self.config)

    def sequence(self,questions):
        history=[];result=None
        for question in questions:
            result=self.service.answer(question,history,'reference-tests')
            history.extend([{'role':'user','content':question},{'role':'assistant','content':result['answer'][:4000]}])
        return result

    def test_plural_followup_answers_both_previously_named_majors(self):
        result=self.sequence(['So sánh CNTT và Marketing','Cả hai ngành đó học gì?'])
        self.assertEqual(result['mode'],'retrieval');self.assertEqual(len(result['sources']),2)

    def test_ordinal_selection_uses_user_order_not_ranked_order(self):
        for first,expected in [('So sánh CNTT và Marketing','7340115'),('So sánh Marketing và CNTT','7480201')]:
            result=self.sequence([first,'Ngành thứ hai học gì?'])
            self.assertEqual(len(result['sources']),1);self.assertIn(expected,result['answer'])

    def test_first_and_third_references_select_registered_majors(self):
        for question,code in [('Ngành đầu tiên?','7340115'),('Ngành thứ 3?','7480201')]:
            result=self.sequence(['So sánh Marketing, AI và CNTT',question])
            self.assertEqual(len(result['sources']),1);self.assertIn(code,result['answer'])

    def test_out_of_range_reference_asks_again_without_substituting(self):
        result=self.sequence(['So sánh CNTT và Marketing','Ngành thứ ba học gì?'])
        self.assertEqual(result['mode'],'clarification');self.assertEqual(result['sources'],[])

    def test_reference_without_context_requests_a_named_major(self):
        for question in ['Ngành đó?','Ngành thứ hai?','Cả hai ngành đó?']:
            result=self.sequence([question])
            self.assertEqual(result['mode'],'clarification');self.assertEqual(result['sources'],[])

    def test_bare_answer_to_clarification_keeps_missing_year(self):
        result=self.sequence(['Học phí ngành Y khoa năm 2025?','Marketing'])
        self.assertEqual(result['mode'],'no-match');self.assertEqual(result['sources'],[])
        self.assertIn('học phí cho năm 2025',result['answer'])

    def test_named_answer_to_clarification_keeps_tuition_topic(self):
        result=self.sequence(['So sánh CNTT và Marketing','Học phí ngành đó?','Ngành Marketing'])
        self.assertEqual([s['category'] for s in result['sources']],['tuition'])

    def test_clarification_does_not_hide_a_new_explicit_topic(self):
        result=self.sequence(['So sánh CNTT và Marketing','Học phí ngành đó?','Marketing học gì?'])
        self.assertEqual([s['category'] for s in result['sources']],['major'])
        self.assertIn('7340115',result['answer'])

    def test_reference_selection_preserves_a_requested_year(self):
        result=self.sequence(['So sánh CNTT và Marketing','Cả hai ngành này học phí năm 2025?','Ngành thứ hai'])
        self.assertEqual(result['mode'],'no-match');self.assertEqual(result['sources'],[])
        self.assertIn('2025',result['answer']);self.assertIn('học phí',result['answer'])

    def test_thanks_does_not_erase_pending_clarification(self):
        result=self.sequence(['Học phí ngành Y khoa 2025?','Cảm ơn','Marketing'])
        self.assertEqual(result['mode'],'no-match');self.assertIn('2025',result['answer'])

    def test_unrelated_topic_resets_old_comparison_reference(self):
        result=self.sequence(['So sánh CNTT và Marketing','Địa chỉ HUIT?','Ngành thứ hai?'])
        self.assertEqual(result['mode'],'clarification');self.assertEqual(result['sources'],[])

    def test_followup_after_ordinal_choice_stays_with_selected_major(self):
        result=self.sequence(['So sánh CNTT và Marketing','Ngành thứ hai học gì?','Mã ngành đó?'])
        self.assertEqual(len(result['sources']),1);self.assertIn('7340115',result['answer'])

    def test_two_topics_are_not_mistaken_for_two_majors(self):
        result=self.sequence(['Học phí và học bổng?', 'Còn cả hai chủ đề năm 2025?'])
        self.assertEqual(result['mode'],'no-match');self.assertIn('2025',result['answer'])
        self.assertEqual(result['sources'],[])

    def test_plural_size_must_match_the_available_context(self):
        for first,followup in [('CNTT học gì?','Cả hai ngành đó học gì?'),
                               ('So sánh CNTT và Marketing','Cả ba ngành đó?'),
                               ('So sánh CNTT, Marketing và AI','Cả hai ngành đó?')]:
            result=self.sequence([first,followup])
            self.assertEqual(result['mode'],'clarification');self.assertEqual(result['sources'],[])

    def test_ordinal_and_plural_references_keep_foreign_school_scope(self):
        for followup in ['Ngành thứ hai học gì?','Cả hai ngành đó học gì?']:
            result=self.sequence(['So sánh CNTT và Marketing ở Bách Khoa',followup])
            self.assertEqual(result['mode'],'no-match');self.assertEqual(result['sources'],[])
            self.assertIn('trường khác',result['answer'])
