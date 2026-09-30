import unittest
from dataclasses import replace
from types import SimpleNamespace
from backend.config import settings
from backend.operations.knowledge import KnowledgeOperations
from backend.services.chat import ChatService
from backend.domain.majors import major_name, mentioned_majors


class CorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=replace(settings,data_mode='local',vector_enabled=False,llm_key='',llm_model='')
        operations=KnowledgeOperations(cls.config)
        try:cls.records=operations.list_knowledge('correction-tests')
        finally:operations.close()

    def setUp(self):
        self.service=ChatService(SimpleNamespace(list_knowledge=lambda request_id:self.records,
                                                find_related_knowledge=lambda query,request_id:[]),self.config)

    def answer(self,question,history=()):return self.service.answer(question,list(history),'correction-tests')

    def sequence(self,questions):
        history=[];result=None
        for question in questions:
            result=self.answer(question,history)
            history.extend([{'role':'user','content':question},{'role':'assistant','content':result['answer'][:4000]}])
        return result

    def test_major_correction_replaces_rejected_major_and_keeps_topic(self):
        result=self.sequence(['Học phí CNTT 2026?','Không phải CNTT, tôi hỏi Marketing'])
        self.assertEqual([s['category'] for s in result['sources']],['tuition'])

    def test_corrected_major_stays_selected_on_later_followup(self):
        result=self.sequence(['CNTT học gì?','Không phải CNTT mà là Marketing','Mã ngành đó?'])
        self.assertEqual(len(result['sources']),1)
        self.assertIn('7340115',result['answer']);self.assertNotIn('7480201',result['answer'])

    def test_rejected_topic_is_not_answered_as_a_second_topic(self):
        for question in ['Tôi hỏi học phí, không phải học bổng',
                         'Không phải học bổng mà là học phí',
                         'Không hỏi học bổng; tôi hỏi học phí']:
            self.assertEqual([s['category'] for s in self.answer(question)['sources']],['tuition'])

    def test_year_correction_does_not_report_the_rejected_year_as_missing(self):
        result=self.sequence(['Học phí 2025?','Không phải năm 2025 mà là năm 2026'])
        self.assertEqual(result['mode'],'retrieval')
        self.assertEqual([s['year'] for s in result['sources']],[2026])

    def test_correcting_foreign_school_to_huit_removes_foreign_scope(self):
        result=self.sequence(['Học phí Bách Khoa?','Không phải Bách Khoa, tôi hỏi học phí HUIT'])
        self.assertEqual([s['category'] for s in result['sources']],['tuition'])

    def test_correcting_huit_to_foreign_school_does_not_return_huit_data(self):
        result=self.sequence(['Học phí HUIT?','Không phải HUIT mà là học phí Bách Khoa'])
        self.assertEqual(result['mode'],'no-match');self.assertEqual(result['sources'],[])

    def test_not_only_is_additive_not_a_correction(self):
        result=self.answer('Không chỉ CNTT mà còn AI, hai ngành học gì?')
        self.assertEqual(len(result['sources']),2)
        self.assertIn('7480201',result['answer']);self.assertIn('7480107',result['answer'])

    def test_question_negation_does_not_remove_the_requested_major(self):
        result=self.answer('Ngành CNTT có khó học không?')
        self.assertEqual(len(result['sources']),1);self.assertIn('7480201',result['answer'])

    def test_correction_without_replacement_asks_for_the_intended_subject(self):
        result=self.sequence(['CNTT học gì?','Không phải CNTT'])
        self.assertEqual(result['mode'],'clarification');self.assertEqual(result['sources'],[])

    def test_comparison_with_unknown_major_does_not_answer_only_known_part(self):
        for question in ['So sánh CNTT và Y khoa','So sánh Y khoa với Marketing',
                         'So sánh học phí CNTT và Y khoa','Ngành CNTT và Y khoa mã ngành là gì?']:
            result=self.answer(question)
            self.assertEqual(result['mode'],'clarification',question);self.assertEqual(result['sources'],[],question)

    def test_unknown_code_beside_known_code_is_not_silently_ignored(self):
        result=self.answer('So sánh mã ngành 7480201 và 9999999')
        self.assertEqual(result['mode'],'clarification');self.assertEqual(result['sources'],[])

    def test_short_known_name_is_not_a_prefix_match_for_a_different_major(self):
        for question in ['Ngành Luật quốc tế học gì?','Mã ngành Luật quốc tế?']:
            result=self.answer(question)
            self.assertEqual(result['mode'],'clarification',question);self.assertEqual(result['sources'],[])

    def test_supported_short_names_match_registered_major(self):
        for question in ['Mã ngành Logistics?','Ngành TMĐT học gì?','Ngành tmdt học gì?']:
            result=self.answer(question)
            self.assertEqual(result['mode'],'retrieval',question);self.assertEqual(len(result['sources']),1)

    def test_official_names_containing_and_are_not_split_into_unknown_parts(self):
        result=self.answer('So sánh Logistics và quản lý chuỗi cung ứng với Khoa học dinh dưỡng và ẩm thực')
        self.assertEqual(result['mode'],'retrieval');self.assertEqual(len(result['sources']),2)

    def test_unicode_decomposed_correction_is_equivalent_to_composed(self):
        import unicodedata
        q='Không phải CNTT mà là Marketing'
        for form in ('NFC','NFD'):
            result=self.answer(unicodedata.normalize(form,q))
            self.assertEqual(len(result['sources']),1);self.assertIn('7340115',result['answer'])

    def test_every_registered_major_keeps_its_own_source_when_asked_by_full_name(self):
        for record in self.records:
            if record['category']!='major':continue
            with self.subTest(major=record['title']):
                result=self.answer('Ngành '+major_name(record)+' học gì năm 2026?')
                self.assertEqual(len(result['sources']),1)
                self.assertEqual(result['sources'][0]['url'],record['source_url'])

    def test_unaccented_correction_keeps_the_new_major(self):
        result=self.answer('Khong phai CNTT ma la Marketing')
        self.assertEqual(len(result['sources']),1);self.assertIn('7340115',result['answer'])

    def test_unaccented_major_code_label_is_not_mistaken_for_a_correction_separator(self):
        result=self.answer('Khong phai ma nganh 7480201 ma la Marketing')
        self.assertEqual(len(result['sources']),1);self.assertIn('7340115',result['answer'])
        self.assertNotIn('7480201',result['answer'])

    def test_cached_aliases_follow_changed_record_metadata(self):
        original=next(d for d in self.records if d['major_code']=='7340115')
        self.assertEqual(len(mentioned_majors('tiếp thị',[original])),1)
        changed={**original,'title':'Ngành Quan hệ công chúng','major_code':'7320108'}
        self.assertEqual(mentioned_majors('tiếp thị',[changed]),[])
        self.assertEqual(mentioned_majors('7320108',[changed]),[changed])
