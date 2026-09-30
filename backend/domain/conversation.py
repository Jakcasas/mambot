"""Bounded, deterministic context from user turns and registered knowledge metadata."""
import re
from backend.domain.language import classify_intent, requested_topics
from backend.domain.corrections import effective_question
from backend.domain.majors import words, major_name, inspect_major_references, is_major_selection

TOPICS={'tuition':'học phí','cutoff':'điểm tuyển sinh','scholarship':'học bổng',
        'admission':'xét tuyển','contact':'liên hệ','major':'ngành học','career':'ngành học'}
def years_in(text):
    return {int(value) for value in re.findall(r'(?<!\d)((?:19|20|21)\d{2})(?!\d)',text)}


def smalltalk(text):
    normalized=words(text)
    # Match the whole utterance: a greeting followed by a real question must reach retrieval.
    if re.fullmatch(r'(?:xin chao|chao|hello|hi|hey)(?: (?:ban|mambot|bot|ad|nhe|nha|a|oi))*',normalized) or normalized in ('mambot oi','ban oi','chao buoi sang','chao buoi toi'):
        return 'greeting'
    if re.fullmatch(r'(?:cam on|thanks|thank you|ok cam on)(?: (?:ban|mambot|bot|nhieu|rat nhieu|nhe|nha|a))*',normalized) or normalized in ('ok','oke'):
        return 'thanks'
    if normalized in ('tam biet','bye','goodbye','hen gap lai','tam biet mambot'):return 'goodbye'
    if normalized in ('ban la ai','mambot la ai','ban lam duoc gi','ban co the giup gi','ban co the lam gi','giup minh voi','minh can ho tro','tu van giup minh','noi chuyen voi minh','tro chuyen voi minh'):
        return 'help'
    if normalized in ('ban khoe khong','hom nay ban the nao','ban co khoe khong'):return 'checkin'
    return None


def asks_major_catalog(text):
    return bool(re.search(r'\b(?:bao nhieu nganh|nhung nganh nao|cac nganh nao|danh sach (?:cac )?nganh)\b',words(text)))


def is_followup(text):
    normalized=words(text)
    return bool(major_reference(text)[0] is not None or
                re.search(r'\b(?:chuong trinh|nghe) (?:nay|do|ay)\b',normalized) or
                re.search(r'^(?:con|the|vay)\b|\bthi sao\b',normalized) or
                re.fullmatch(r'(?:nam )?(?:19|20|21)\d{2}',normalized) or
                re.fullmatch(r'(?:ra truong lam gi|hoc bao lau|ma nganh(?: la gi)?|hoc phi(?: bao nhieu)?)',normalized))


def major_reference(text):
    """Return a user-list reference, whole-question flag and optional required count."""
    normalized=words(text)
    plural=re.search(r'\b(?:ca (?:hai|ba|2|3) nganh(?: (?:nay|do|ay))?|(?:cac|hai|ba|2|3) nganh (?:nay|do|ay|tren))\b',normalized)
    ordinal=re.search(r'\bnganh (?:thu (mot|hai|ba|1|2|3)|dau tien)\b',normalized)
    singular=re.search(r'\bnganh (?:nay|do|ay)\b',normalized)
    match=plural or ordinal or singular
    if not match:return None,False,None
    count=None
    if plural:reference='all'
    elif ordinal:reference={'mot':0,'hai':1,'ba':2,'1':0,'2':1,'3':2,None:0}[ordinal.group(1)]
    else:reference='one'
    if plural:
        number=re.search(r'\b(hai|ba|2|3)\b',plural.group())
        if number:count={'hai':2,'ba':3,'2':2,'3':3}[number.group(1)]
    remainder=(normalized[:match.start()]+' '+normalized[match.end():]).strip()
    remainder=re.sub(r'\b(?:nam\s+)?(?:19|20|21)\d{2}\b',' ',remainder).strip()
    only=re.fullmatch(r'(?:con|the|vay|thi sao|a|nhe|\s)*',remainder) is not None
    return reference,only,count


def resolve_context(question,history,records):
    majors=[];years=set();intent='general';inherited=False;topics=[];score_kind=None
    unknown=False;awaiting_selection=False;reference_error=False;ambiguous=False
    turns=[turn['content'] for turn in history[-10:] if turn['role']=='user']+[question]
    for text in turns:
        text,corrected=effective_question(text)
        if not text:
            majors=[];years=set();intent='general';topics=[];score_kind=None;inherited=False
            awaiting_selection=False;reference_error=False;ambiguous=False;unknown=False
            continue
        if smalltalk(text):continue
        explicit,unknown=inspect_major_references(text,records)
        reference,reference_only,reference_count=major_reference(text)
        selection=awaiting_selection and len(explicit)==1 and is_major_selection(text,records)
        followup=is_followup(text) or corrected or reference is not None or selection
        previous_majors=majors
        reference_error=False
        if reference is not None and not explicit:
            if (not previous_majors or (isinstance(reference,int) and reference>=len(previous_majors)) or
                    (reference_count is not None and reference_count!=len(previous_majors))):
                reference_error=True
            else:
                unknown=False
                if isinstance(reference,int):explicit=[previous_majors[reference]]
        if re.fullmatch(r'ma nganh(?: la gi)?',words(text)) and majors:unknown=False
        next_intent=classify_intent(text)
        explicit_topics=requested_topics(text)
        if (selection or reference_only) and not explicit_topics:next_intent='general'
        inherited=bool(followup and previous_majors and not unknown and not reference_error and
                       (not explicit or isinstance(reference,int)))
        majors=[] if unknown else (explicit or (majors if followup else []))
        if reference_error:majors=[]
        ambiguous=inherited and len(majors)>1 and reference!='all'
        awaiting_selection=unknown or ambiguous or reference_error
        next_years=years_in(text)
        years=next_years or (years if followup else set())
        intent=next_intent if next_intent!='general' else (intent if followup else 'general')
        topics=explicit_topics or (topics if followup and next_intent=='general' else [])
        if 'cutoff' not in topics:score_kind=None
        elif explicit_topics:
            normalized=words(text)
            score_kind='final' if re.search(r'\bdiem (?:chuan|trung tuyen)\b',normalized) else ('floor' if 'diem san' in normalized else None)
        if intent=='general' and majors:intent='major'
    # Append only recognized entities/topics, never free-form instructions from old turns.
    question,_=effective_question(question)
    query=question
    if majors:query+=' '+ ' '.join(major_name(record) for record in majors)
    if intent in TOPICS:query+=' '+TOPICS[intent]
    if score_kind:query+=' '+('điểm chuẩn' if score_kind=='final' else 'điểm sàn')
    for year in sorted(years-years_in(question)):query+=' '+str(year)
    raw_intent=classify_intent(question)
    return {'query':query[:2400],'majors':majors,'years':years,'intent':intent,'inherited':inherited,
            'intent_question':question if raw_intent!='general' else TOPICS.get(intent,question),
            'ambiguous':ambiguous,'topics':topics,'score_kind':score_kind,'unknown_major':unknown,
            'reference_error':reference_error}


def targets_other_school(question):
    question,_=effective_question(question)
    normalized=words(question)
    exam=re.search(r'\b(?:ky thi|danh gia nang luc)\b',normalized)
    if classify_intent(question)=='admission' and exam:
        # Ignore an exam's issuing university only when HUIT is the explicit target.
        target=normalized[:exam.start()]
        if re.search(r'\b(?:huit|hufi|cong thuong)\b',target):normalized=target
    if re.search(r'\b(?:bach khoa|ueh|uef|hutech|fpt|ton duc thang|van lang)\b',normalized):return True
    for match in re.finditer(r'\b(?:truong(?: dai hoc)?|dai hoc|dh)\s+(.+)',normalized):
        target=match.group(1)
        if re.match(r'(?:huit|hufi|cong thuong|cong nghiep thuc pham)\b',target):continue
        if re.match(r'(?:co|nay|do|ay|minh|nam|la|o|tai|hoc|phi|chinh quy|bao|nao|can|nhu|lam|ra|the|nganh|chuong trinh|hien|nhung|cac)\b',target):continue
        return True
    return False


def other_school_context(question,history):
    question,_=effective_question(question)
    if targets_other_school(question):return True
    if re.search(r'\b(?:huit|hufi|cong thuong)\b',words(question)) or not is_followup(question):return False
    for turn in reversed(history[-10:]):
        if turn['role']!='user':continue
        text,_=effective_question(turn['content'])
        if smalltalk(text):continue
        if targets_other_school(text):return True
        if re.search(r'\b(?:huit|hufi|cong thuong)\b',words(text)) or not is_followup(text):return False
    return False


def needs_interest_clarification(question,majors):
    normalized=words(question)
    gender=re.search(r'\b(?:la|gioi tinh) (?:nam|nu)\b|\b(?:nu|con gai|con trai)\b|\bnam (?:nen|thi|hoc|chon)\b',normalized)
    gender_choice=gender and re.search(r'\b(?:nen hoc|chon nganh|hoc nganh|phu hop)\b',normalized)
    interests=re.search(r'\b(?:thich|dam me|lap trinh|nau an|kinh doanh|thiet ke|ngoai ngu|toan|sinh hoc|hoa hoc)\b',normalized)
    return bool(gender_choice and not interests and not majors)
