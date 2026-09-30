import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch
from backend.config import settings
from backend.services.chat import ChatService


def document(category,year,text=None,title=None,code=''):
    return {'title':title or f'Học phí HUIT {year}',
            'text':text or f'Bằng chứng học phí thử nghiệm riêng cho năm {year}.',
            'category':category,'year':year,'major_code':code,
            'source_url':f'https://ts.huit.edu.vn/test/{category}/{year}/{code}',
            'retrieved_at':'2026-07-27'}


class EvidenceYearTests(unittest.TestCase):
    def setUp(self):
        self.records=[document('tuition',2025),document('tuition',2026,'Học phí HUIT học phí HUIT năm 2026. '*10)]
        self.operations=SimpleNamespace(list_knowledge=lambda request_id:self.records,
                                        find_related_knowledge=lambda query,request_id:[])
        self.config=replace(settings,data_mode='local',vector_enabled=False,llm_key='',llm_model='')
        self.service=ChatService(self.operations,self.config)

    def answer(self,question):return self.service.answer(question,[],'evidence-year-tests')

    def test_comparing_two_years_keeps_both_even_when_one_ranks_lower(self):
        result=self.answer('So sánh học phí HUIT năm 2025 và 2026?')
        self.assertEqual([s['year'] for s in result['sources']],[2025,2026])
        self.assertIn('[1]',result['answer']);self.assertIn('[2]',result['answer'])

    def test_three_requested_years_all_survive_excerpt_selection(self):
        self.records.append(document('tuition',2024))
        result=self.answer('Học phí năm 2024, 2025 và 2026?')
        self.assertEqual([s['year'] for s in result['sources']],[2024,2025,2026])
        self.assertIn('[3]',result['answer'])

    def test_multiple_topics_and_years_ask_to_split_before_dense_or_provider(self):
        self.records.extend([document('scholarship',year,title=f'Học bổng {year}') for year in (2025,2026)])
        with patch.object(self.operations,'find_related_knowledge') as dense:
            result=self.answer('Học phí và học bổng năm 2025 và 2026?')
        self.assertEqual(result['mode'],'clarification');self.assertEqual(result['sources'],[])
        dense.assert_not_called()

    def test_one_major_compared_across_years_preserves_both_records(self):
        self.records=[document('major',year,f'Marketing: nội dung thử nghiệm {year}.',
                               'Ngành Marketing (HUIT)',code='7340115') for year in (2025,2026)]
        result=self.answer('Ngành Marketing năm 2025 và 2026 học gì?')
        self.assertEqual([s['year'] for s in result['sources']],[2025,2026])
        self.assertIn('Năm 2025\n',result['answer']);self.assertIn('Năm 2026\n',result['answer'])

    def test_provider_must_cite_every_requested_year(self):
        self.service=ChatService(self.operations,replace(self.config,llm_key='test-only',llm_model='test-only'))
        with patch('backend.services.chat.generate',return_value='Chỉ nói về một năm [1]'):
            result=self.answer('Học phí năm 2025 và 2026?')
        self.assertEqual(result['mode'],'retrieval');self.assertEqual(len(result['sources']),2)

    def test_final_score_of_one_year_does_not_hide_floor_of_another(self):
        self.records=[document('cutoff',2025,'Điểm chuẩn: dữ liệu giả lập 2025.','Điểm chuẩn HUIT 2025'),
                      document('cutoff',2026,'Điểm sàn: dữ liệu giả lập 2026.','Điểm sàn HUIT 2026')]
        result=self.answer('Điểm chuẩn HUIT năm 2025 và 2026?')
        self.assertEqual([s['year'] for s in result['sources']],[2025,2026])
        first=result['answer'].split('\n\n')[0]
        self.assertIn('2026',first);self.assertIn('ĐIỂM SÀN',first)

    def test_final_scores_are_selected_before_rank_limit_for_each_year(self):
        self.records=[document('cutoff',2026,'Điểm chuẩn HUIT năm 2026? '*30,f'Điểm sàn HUIT phần {i}') for i in range(4)]
        self.records.append(document('cutoff',2026,'Kết quả được công bố.','Điểm trúng tuyển HUIT 2026'))
        result=self.answer('Điểm chuẩn HUIT năm 2026?')
        self.assertEqual([s['title'] for s in result['sources']],['Điểm trúng tuyển HUIT 2026'])
        self.assertNotIn('ĐIỂM SÀN',result['answer'])

    def test_missing_requested_year_stays_no_match(self):
        result=self.answer('Học phí năm 2025 và 2027?')
        self.assertEqual(result['mode'],'no-match');self.assertEqual(result['sources'],[])
        self.assertIn('2027',result['answer'])

    def test_dense_ranking_cannot_drop_the_other_requested_year(self):
        self.operations.find_related_knowledge=lambda query,request_id:[{**self.records[1],'score':0.99}]
        result=self.answer('So sánh học phí năm 2025 và 2026?')
        self.assertEqual([s['year'] for s in result['sources']],[2025,2026])

    def test_undated_floor_source_is_not_assigned_the_year_of_another_source(self):
        self.records=[document('cutoff',2025,'Điểm chuẩn HUIT.','Điểm chuẩn HUIT 2025'),
                      document('cutoff',None,'Điểm sàn HUIT.','Điểm sàn HUIT')]
        result=self.answer('Điểm chuẩn HUIT?')
        self.assertIn('phần dữ liệu chưa rõ năm',result['answer'].split('\n\n')[0])
        self.assertEqual({s['year'] for s in result['sources']},{2025,None})
