"""Vietnamese TF-IDF/cosine inspired by Module 26; optional reciprocal-rank fusion."""
import math
import re
from collections import Counter
from functools import lru_cache
from backend.domain.language import _normalize, expand_query, classify_intent
from backend.domain.conversation import years_in
from backend.domain.majors import major_key

STOP = set('la cua va cac cho toi minh ban ve mot nhung duoc voi trong tai nao bao nhieu hay the co khong huit truong dai hoc nganh em nen thich muon gi sao nu nam'.split())

def tokens(text):
    words = [w for w in re.findall(r'[a-z0-9]+', _normalize(text)) if w not in STOP]
    return words + [' '.join(words[i:i+2]) for i in range(len(words)-1)]

def cosine(a, b):
    norm = math.sqrt(sum(v*v for v in a.values()) * sum(v*v for v in b.values()))
    return sum(v*b.get(k, 0) for k,v in a.items()) / norm if norm else 0.0

@lru_cache(maxsize=4)
def _build_index(documents):
    """Reuse document vectors; the content key invalidates the cache when data changes.

    Only knowledge content is cached, never questions, answers or conversation history.
    """
    counts = [Counter(tokens(title + ' ' + title + ' ' + text)) for title, text in documents]
    frequency = Counter(token for count in counts for token in count)
    idf = {token: math.log((1 + len(documents)) / (1 + count)) + 1 for token, count in frequency.items()}
    vectors = [{token: (1 + math.log(count)) * idf[token] for token, count in document.items()} for document in counts]
    return idf, vectors

def retrieve(question, records, dense=(), intent_question=None, major_keys=(), intent=None, years=None, score_kind=None):
    expanded = expand_query(question)
    idf, document_vectors = _build_index(tuple((d['title'], d['text']) for d in records))
    # OOV words retain weight in the query norm: unknown topics must not look confident.
    vector = lambda c: {t:(1+math.log(n))*idf.get(t,math.log(1+len(records))+1) for t,n in c.items()}
    query = vector(Counter(tokens(expanded)))
    intent = intent or classify_intent(intent_question or question)
    years = years_in(question) if years is None else set(years)
    targeted=intent in ('tuition','cutoff','scholarship','admission','contact')
    def in_scope(record):
        if years and record['year'] not in years:return False
        if targeted:return record['category']==intent
        return not major_keys or (record['category']=='major' and major_key(record) in major_keys)
    final_score=lambda record:bool(re.search(r'\bdiem (?:chuan|trung tuyen)\b',_normalize(record['title'])))
    # Prefer actual admission scores before the top-k cut, independently for each year.
    final_years={d['year'] for d in (*records,*dense) if in_scope(d) and final_score(d)} if intent=='cutoff' and score_kind=='final' else set()
    def eligible(record):
        return in_scope(record) and (record['year'] not in final_years or final_score(record))
    ranked=[]
    for d,document_vector in zip(records,document_vectors):
        if not eligible(d):continue
        score = cosine(query, document_vector)
        if score < 0.055 and not targeted and not major_keys:
            continue
        # Intent selects the type of evidence, not hard-coded answers.
        if targeted:score+=0.24
        elif major_keys:score+=0.30
        ranked.append({**d,'similarity':round(min(score,1),4)})
    ranked.sort(key=lambda x:x['similarity'],reverse=True)
    if dense:
        # A single source page may contain several distinct knowledge chunks.
        identity=lambda d:(d['source_url'],d['title'],d['text'])
        by_key={identity(d):d for d in ranked}; fusion={}
        for rank,d in enumerate(ranked,1): fusion.setdefault(identity(d),1/(60+rank))
        seen=set()
        for rank,d in enumerate(dense,1):
            if not eligible(d):continue
            key=identity(d)
            if key in seen: continue
            seen.add(key); fusion[key]=fusion.get(key,0)+1/(60+rank)
            by_key.setdefault(key,{**d,'similarity':round(d.get('score',0),4)})
        ranked=[by_key[u] for u in sorted(fusion,key=fusion.get,reverse=True)]
    if major_keys and not targeted:
        # A comparison must cover each requested major before extra chunks of one major.
        ordered=[]
        for key in major_keys:
            match=next((d for d in ranked if major_key(d)==key),None)
            if match:ordered.append(match)
        return ordered[:3]
    return ranked[:3]

def excerpt(question, document, max_chars=2300):
    text = re.sub(r'^\[[^\]]+\]\s*', '', document['text']).strip()
    lines = [re.sub(r'^[#*\-\s]+', '', line).strip() for line in text.splitlines() if line.strip()]
    # Preserve contiguous evidence, including complete enumerations and qualifications.
    # Selecting isolated matching lines used to omit fees, major codes and list members.
    value = '\n'.join(lines)
    if len(value)<=max_chars:
        return value
    kept=[];size=0
    for line in lines:
        if size+len(line)>max_chars:
            if not kept:
                kept.append(line[:max_chars].rstrip()+'…')
            break
        kept.append(line);size+=len(line)+1
    return '\n'.join(kept)+'\n[Trích đoạn; mở nguồn để đọc đầy đủ.]'
