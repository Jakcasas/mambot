import re
import time
from backend.domain.language import _normalize
from backend.domain.retrieval import retrieve, excerpt
from backend.infrastructure.llm import generate, generate_support
from backend.domain.student_support import GREETINGS, support_request, valid_support_answer
from backend.domain.student_care import care_reply
from backend.domain.sources import trusted_source
from backend.domain.corrections import effective_question
from backend.domain.majors import major_key, major_name
from backend.domain.conversation import (resolve_context, other_school_context,
                                        needs_interest_clarification, TOPICS, smalltalk,
                                        asks_major_catalog)

class ChatService:
    def __init__(self, operations, settings):
        self.operations=operations; self.settings=settings

    def answer(self, question, history, request_id):
        started=time.monotonic()
        original_question=question
        question,corrected=effective_question(question)
        def response(answer, sources=None, mode='retrieval', warning=None):
            return {'answer':answer,'sources':sources or [],'mode':mode,'warning':warning,
                    'request_id':request_id,'duration_ms':round((time.monotonic()-started)*1000),
                    'data_mode':self.settings.data_mode}
        if corrected and not question:
            return response('Bạn muốn sửa sang ngành, chủ đề hoặc năm nào? Hãy nêu nội dung đúng để mình tra cứu lại.',mode='clarification')
        social=smalltalk(question)
        if social:
            return response(GREETINGS[social],mode='retrieval' if social in ('greeting','thanks') else 'support')
        support=support_request(question,history)
        # Do not forward a sensitive conversation when the next question changes topic.
        sensitive_history=any(t.get('role')=='user' and care_reply(t.get('content',''),history[:i])
                              for i,t in enumerate(history))
        if support:
            answer=support['answer'];mode='support';warning=None
            if support['generate'] and self.settings.llm_key and self.settings.llm_model:
                try:
                    generated=generate_support(self.settings,question,[] if sensitive_history else support['turns'][:-1])
                    if not valid_support_answer(generated):raise ValueError('Invalid support answer')
                    answer=generated;mode='conversation'
                except Exception:
                    warning='AI chưa trả lời được; đang dùng hướng dẫn có sẵn để bạn tiếp tục.'
            return response(answer,mode=mode,warning=warning)
        if other_school_context(question,history):
            return response('Mambot hiện chỉ có bản lưu về HUIT. Mình chưa có dữ liệu để trả lời cho trường khác và sẽ không dùng thông tin HUIT thay thế. Bạn muốn tìm hiểu nội dung nào của HUIT?',mode='no-match')
        records=self.operations.list_knowledge(request_id)
        # Filter before ranking so invalid high-ranking records cannot crowd out good evidence.
        records=[d for d in records if trusted_source(d.get('source_url'))]
        context=resolve_context(original_question,history,records)
        if context['reference_error']:
            return response('Mình chưa xác định được ngành bạn đang chỉ tới trong ngữ cảnh hiện có. Bạn hãy ghi tên hoặc mã ngành cụ thể; mình sẽ giữ chủ đề và năm bạn vừa hỏi để tra cứu lại.',mode='clarification')
        if needs_interest_clarification(question,context['majors']):
            return response('Mình sẽ gợi ý theo sở thích, môn học bạn mạnh và mục tiêu nghề nghiệp. Giới tính không quyết định ngành phù hợp. Bạn thích tìm hiểu công nghệ, kinh doanh, ngôn ngữ hay lĩnh vực nào khác?',mode='clarification')
        if context['ambiguous']:
            names=', '.join(major_name(d) for d in context['majors'])
            return response(f'Bạn đang muốn hỏi ngành nào trong các ngành vừa nhắc: {names}? Hãy ghi tên ngành để mình tra cứu đúng.',mode='clarification')
        if len(context['majors'])>3:
            return response('Bạn chọn tối đa 3 ngành mỗi lần để mình đối chiếu đủ nguồn và trình bày rõ hơn nhé.',mode='clarification')
        if context['unknown_major']:
            return response('Mình chưa nhận diện được đầy đủ tên hoặc mã ngành bạn hỏi trong kho hiện có. Mình không dùng mã của một ngành gần tên để thay thế hoặc bỏ qua phần chưa nhận ra. Bạn hãy kiểm tra tên tại Kho tri thức → Ngành học, hoặc nêu tên ngành đầy đủ.',mode='clarification')
        topics=context['topics']
        if len(topics)>3:
            return response('Bạn chọn tối đa 3 chủ đề mỗi lần để mình trả lời đủ từng phần, ví dụ học phí, học bổng và xét tuyển.',mode='clarification')
        scoped=[d for d in records if not topics or d['category'] in topics]
        available_years={d['year'] for d in scoped if d.get('year') is not None}
        missing_years=context['years']-available_years
        if len(topics)>1:
            # A year covered by tuition must not hide missing scholarship evidence.
            missing_years=set().union(*(context['years']-{d['year'] for d in scoped if d['category']==topic} for topic in topics))
        if records and missing_years:
            missing=', '.join(str(year) for year in sorted(missing_years))
            available=', '.join(str(year) for year in sorted(available_years))
            topic=', '.join(TOPICS[t] for t in topics) if len(topics)>1 else TOPICS.get(context['intent'],'chủ đề này')
            note=f' Bản lưu về {topic} hiện có năm {available}.' if available else ''
            if len(topics)>1:note=' Một hoặc nhiều chủ đề chưa có bằng chứng cho năm bạn yêu cầu.'
            return response(f'Mình chưa có dữ liệu {topic} cho năm {missing}.{note} Mình không dùng số liệu năm khác để thay thế; bạn có thể hỏi lại với năm có dữ liệu hoặc kiểm tra cổng tuyển sinh HUIT.',mode='no-match')
        if asks_major_catalog(question) and not context['majors'] and not topics:
            catalog={major_key(d) for d in scoped if d['category']=='major' and (not context['years'] or d['year'] in context['years'])}
            return response(f'Kho bản lưu hiện có {len(catalog)} ngành khác nhau. Bạn mở Kho tri thức và chọn bộ lọc Ngành học để xem đầy đủ tên, mã ngành và nguồn. Đây là số ngành trong kho đang dùng, chưa xác nhận là danh sách tuyển sinh hiện hành. Bạn muốn tìm hiểu ngành nào?',mode='clarification')
        query=context['query']
        comparing=len(context['majors'])>1 and context['intent'] not in ('tuition','cutoff','scholarship','admission','contact')
        multi_year=len(context['years'])>1
        subjects=[(topic,[]) for topic in topics] if topics else (
            [(context['intent'],[major_key(d)]) for d in context['majors']] if context['majors'] else [(context['intent'],[])])
        if multi_year and len(subjects)*len(context['years'])>3:
            return response('Bạn chia câu hỏi thành tối đa 3 phần ngành/chủ đề–năm mỗi lần nhé. Ví dụ hỏi một chủ đề trong 2–3 năm, hoặc từng năm riêng nếu cần nhiều chủ đề.',mode='clarification')
        dense=self.operations.find_related_knowledge(query,request_id)
        dense=[d for d in dense if trusted_source(d.get('source_url'))]
        if multi_year:
            docs=[]
            for year in sorted(context['years']):
                for intent,keys in subjects:
                    matches=retrieve(query,records,dense,intent=intent,major_keys=keys,
                                     years={year},score_kind=context['score_kind'])
                    if not matches or matches[0]['similarity']<0.10:
                        return response(f'Mình chưa có đủ bằng chứng cho tất cả các phần bạn hỏi, trong đó có năm {year}. Bạn hãy hỏi riêng từng ngành/chủ đề hoặc chọn năm có dữ liệu.',mode='no-match')
                    docs.append(matches[0])
        elif len(topics)>1:
            docs=[]
            for topic in topics:
                matches=retrieve(query,records,dense,intent=topic,score_kind=context['score_kind'])
                if not matches:
                    return response(f'Mình chưa có đủ bằng chứng cho phần {TOPICS[topic]}. Bạn có thể hỏi riêng từng chủ đề hoặc đối chiếu nguồn HUIT; mình chưa thể trả lời đầy đủ tất cả các phần.',mode='no-match')
                docs.append(matches[0])
        else:
            docs=retrieve(query,records,dense,intent_question=context['intent_question'],
                          major_keys=[major_key(d) for d in context['majors']],intent=context['intent'],score_kind=context['score_kind'])
        if comparing:
            covered={major_key(d) for d in docs if d['category']=='major'}
            missing=[major_name(d) for d in context['majors'] if major_key(d) not in covered]
            if missing:
                period=' cho năm '+', '.join(str(year) for year in sorted(context['years'])) if context['years'] else ''
                return response('Mình chưa có đủ bằng chứng'+period+' cho ngành '+', '.join(missing)+
                                '. Mình chưa thể đối chiếu đủ các ngành bạn hỏi. Bạn có thể đổi năm hoặc hỏi riêng từng ngành.',mode='no-match')
        if not docs or docs[0]['similarity'] < 0.10:
            return response('Mình chưa tìm thấy bằng chứng phù hợp trong kho dữ liệu hiện có. Bạn hãy nêu rõ ngành, chủ đề hoặc năm tuyển sinh. Bạn cũng có thể mở mục Kho tri thức và lọc Ngành học để xem các bản lưu. Thông tin mới nhất cần đối chiếu tại cổng tuyển sinh HUIT.',mode='no-match')
        wants_final=context['score_kind']=='final'
        actual_scores=[d for d in docs if d['category']=='cutoff' and re.search(r'\bdiem (?:chuan|trung tuyen)\b',_normalize(d['title']))]
        score_docs=[d for d in docs if d['category']=='cutoff']
        floor_docs=[d for d in score_docs if 'diem san' in _normalize(d['title'])]
        floor_fallback=wants_final and bool(floor_docs)
        floor_years=sorted({d['year'] for d in floor_docs if d['year'] is not None})
        floor_period=(' cho năm '+', '.join(map(str,floor_years)) if floor_years else ' cho phần dữ liệu chưa rõ năm') if actual_scores and floor_docs else ''
        sources=[{'title':d['title'],'url':d['source_url'],'category':d['category'],'year':d['year'],
                  'retrieved_at':d['retrieved_at'],'similarity':d['similarity']} for d in docs]
        answer=None; warnings=[]
        if corrected:warnings.append('Đã áp dụng nội dung bạn sửa lại.')
        if context['inherited']:
            warnings.append('Ngữ cảnh đang dùng: '+', '.join(major_name(d) for d in context['majors'])+'.')
        if floor_fallback:
            warnings.append('Kho hiện có điểm sàn'+floor_period+', chưa có điểm chuẩn/điểm trúng tuyển tương ứng.')
        complete_coverage=comparing or len(topics)>1 or multi_year or (floor_fallback and bool(actual_scores))
        if self.settings.llm_key and self.settings.llm_model and not floor_fallback:
            try:
                answer=generate(self.settings,query,[] if sensitive_history else history,docs)
                citations=[int(v) for v in re.findall(r'\[(\d+)\]',answer or '')]
                if not citations or any(v<1 or v>len(docs) for v in citations):
                    answer=None
                elif complete_coverage and not set(range(1,len(docs)+1)).issubset(citations):
                    answer=None
            except Exception:
                answer=None
            if answer is None:warnings.append('Mô hình chưa trả lời được; đang hiển thị trích đoạn từ kho tri thức.')
        mode='generated' if answer else 'retrieval'
        if not answer:
            count=len(docs) if complete_coverage else (2 if len(docs)>1 and docs[1]['similarity'] >= docs[0]['similarity']*.85 else 1)
            answer='Mình tìm thấy các trích đoạn liên quan trong bản dữ liệu đã lưu:\n\n'+'\n\n'.join(
                (f"Năm {d['year']}\n" if multi_year else '')+f"{excerpt(query,d)} [{i+1}]" for i,d in enumerate(docs[:count]))
            sources=sources[:count]
        if floor_fallback:
            note=('Mình chưa có điểm chuẩn/điểm trúng tuyển'+floor_period+'. Phần nguồn tương ứng là ĐIỂM SÀN; không dùng thay cho điểm trúng tuyển.' if actual_scores else
                  'Mình chưa có điểm chuẩn/điểm trúng tuyển phù hợp với câu hỏi. Dữ liệu dưới đây là ĐIỂM SÀN; không dùng các mức này thay cho điểm trúng tuyển.')
            answer=note+'\n\n'+answer
        if re.search(r'\b(?:moi nhat|hien nay|hom nay|nam nay)\b',_normalize(question)):
            answer='Mình chưa xác minh thông báo mới nhất. Nội dung dưới đây thuộc bản lưu và có thể đã thay đổi.\n\n'+answer
        answer+='\n\nLưu ý: đây là dữ liệu lưu trữ. Hãy mở nguồn để đối chiếu thông báo hiện hành.'
        return response(answer,sources,mode,' '.join(warnings) or None)
