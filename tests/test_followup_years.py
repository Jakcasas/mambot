import unittest
from dataclasses import replace
from types import SimpleNamespace
from backend.config import settings
from backend.operations.knowledge import KnowledgeOperations
from backend.services.chat import ChatService


class FollowupYearTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=replace(settings,data_mode='local',vector_enabled=False,llm_key='',llm_model='')
        operations=KnowledgeOperations(cls.config)
        try:cls.records=operations.list_knowledge('followup-year-tests')
        finally:operations.close()

    def setUp(self):
        self.operations=SimpleNamespace(list_knowledge=lambda request_id:self.records,
                                        find_related_knowledge=lambda query,request_id:[])
        self.service=ChatService(self.operations,self.config)

    def sequence(self,questions):
        history=[]
        for question in questions:
            result=self.service.answer(question,history,'followup-year-tests')
            history.extend([{'role':'user','content':question},{'role':'assistant','content':result['answer'][:4000]}])
        return result

    def test_ordinal_with_year_keeps_tuition_instead_of_major_description(self):
        for question in ['Ngành thứ hai năm 2025?', 'nganh thu 2 nam 2025']:
            result=self.sequence(['Học phí CNTT và Marketing năm 2026?',question])
            self.assertEqual(result['mode'],'no-match');self.assertIn('học phí cho năm 2025',result['answer'])
            self.assertEqual(result['sources'],[])

    def test_plural_with_year_preserves_every_requested_topic(self):
        result=self.sequence(['Học phí và học bổng CNTT và Marketing?', 'Cả hai ngành đó năm 2025?'])
        self.assertEqual(result['mode'],'no-match');self.assertIn('học phí, học bổng',result['answer'])

    def test_plural_reference_without_year_keeps_the_current_topic(self):
        for reference in ['Cả hai ngành đó?', 'Cả hai ngành ấy?', 'Cả hai ngành này?']:
            result=self.sequence(['Học phí CNTT và Marketing năm 2026?',reference])
            self.assertEqual([s['category'] for s in result['sources']],['tuition'])

    def test_selection_after_clarification_accepts_an_explicit_new_year(self):
        for question in ['Marketing năm 2025','Em chọn Marketing năm 2025 ạ']:
            result=self.sequence(['Học phí ngành Y khoa 2026?',question])
            self.assertEqual(result['mode'],'no-match');self.assertIn('học phí cho năm 2025',result['answer'])

    def test_reference_and_year_do_not_erase_final_score_warning(self):
        result=self.sequence(['Điểm chuẩn CNTT và Marketing năm 2025?', 'Ngành thứ hai năm 2026?'])
        self.assertTrue(result['answer'].startswith('Mình chưa có điểm chuẩn'))
        self.assertEqual([s['category'] for s in result['sources']],['cutoff'])

    def test_reference_with_new_substantive_request_changes_topic(self):
        result=self.sequence(['Học phí CNTT và Marketing?', 'Ngành thứ hai năm 2026 học gì?'])
        self.assertEqual([s['category'] for s in result['sources']],['major'])
        self.assertIn('7340115',result['answer'])

    def test_explicit_named_new_question_is_not_a_clarification_selection(self):
        result=self.sequence(['Học phí ngành Y khoa?', 'Marketing năm 2026 học gì?'])
        self.assertEqual([s['category'] for s in result['sources']],['major'])

    def test_comparison_never_silently_drops_a_major_missing_the_requested_year(self):
        mixed=[{**d,'year':2025} if d.get('major_code')=='7340115' else d for d in self.records]
        self.operations.list_knowledge=lambda request_id:mixed
        result=self.sequence(['So sánh CNTT và Marketing năm 2026'])
        self.assertEqual(result['mode'],'no-match');self.assertEqual(result['sources'],[])
        self.assertIn('Marketing',result['answer'])

    def test_dense_wrong_year_cannot_fill_missing_comparison_member(self):
        mixed=[{**d,'year':2025} if d.get('major_code')=='7340115' else d for d in self.records]
        self.operations.list_knowledge=lambda request_id:mixed
        self.operations.find_related_knowledge=lambda query,request_id:[
            {**d,'score':0.99} for d in mixed if d.get('major_code')=='7340115']
        result=self.sequence(['So sánh CNTT và Marketing năm 2026'])
        self.assertEqual(result['mode'],'no-match');self.assertEqual(result['sources'],[])
