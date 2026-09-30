"""Major names come from registered metadata; aliases never create a missing record."""
import re
from functools import lru_cache
from backend.domain.language import _normalize

SHORT_NAMES={'cntt':'công nghệ thông tin','attt':'an toàn thông tin','khdl':'khoa học dữ liệu',
             'qtkd':'quản trị kinh doanh','tmdt':'thương mại điện tử',
             'data science':'khoa học dữ liệu','tiếp thị':'marketing',
             'logistics':'logistics và quản lý chuỗi cung ứng'}


def words(text):
    return re.sub(r'[^a-z0-9]+',' ',_normalize(text)).strip()


def major_name(record):
    return re.sub(r'^Ngành\s+','',record['title'].split(' (HUIT')[0],flags=re.I).strip()


def major_key(record):
    return record.get('major_code') or record['source_url']


@lru_cache(maxsize=256)
def _variants(name,code):
    """Cache metadata vocabulary only; changed name/code creates a different key."""
    variants={words(name),words(re.sub(r'\([^)]*\)','',name))}
    variants.update(words(value) for value in re.findall(r'\(([^)]+)\)',name))
    variants.update(words(alias) for alias,canonical in SHORT_NAMES.items() if words(canonical) in variants)
    if code:variants.add(str(code))
    return frozenset(variants)


def _spans(text,records):
    normalized=words(text);candidates=[]
    explicit_ai=bool(re.search(r'\bAI\b',text) or re.search(r'\bnganh ai\b',normalized))
    explicit_it=bool(re.search(r'\bIT\b',text) or re.search(r'\bnganh it\b',normalized))
    for record in records:
        if record['category']!='major':continue
        variants=set(_variants(major_name(record),record.get('major_code')))
        # "ai" is a pronoun too. Do not expand it unless explicitly used as a major.
        if explicit_ai and 'tri tue nhan tao' in variants:variants.add('ai')
        if explicit_it and 'cong nghe thong tin' in variants:variants.add('it')
        for variant in variants:
            if len(variant)<2:continue
            for match in re.finditer(rf'\b{re.escape(variant)}\b',normalized):
                candidates.append((match.start(),match.end(),record))
    selected=[]
    for start,end,record in sorted(candidates,key=lambda item:(-(item[1]-item[0]),item[0])):
        if any(start<b and end>a for a,b,_ in selected):continue
        selected.append((start,end,record))
    return normalized,sorted(selected,key=lambda item:item[0])


def mentioned_majors(text,records):
    _,spans=_spans(text,records);seen=set();result=[]
    for _,_,record in spans:
        key=major_key(record)
        if key not in seen:seen.add(key);result.append(record)
    return result


def is_major_selection(text,records):
    """A short named response can answer a pending clarification without changing topic."""
    normalized,spans=_spans(text,records)
    if len(spans)!=1:return False
    start,end,_=spans[0]
    rest=normalized[:start]+' '+normalized[end:]
    rest=re.sub(r'\b(?:nam\s+)?(?:19|20|21)\d{2}\b',' ',rest)
    rest=re.sub(r'\b(?:nganh|em|toi|minh|chon|la|a|nhe)\b',' ',rest)
    return not rest.strip()


def inspect_major_references(text,records):
    normalized,spans=_spans(text,records)
    majors=[];seen=set();masked=normalized
    for start,end,record in spans:
        if major_key(record) not in seen:seen.add(major_key(record));majors.append(record)
    for start,end,_ in reversed(spans):masked=masked[:start]+' knownmajor '+masked[end:]
    # Unknown codes must not disappear just because another code was recognized.
    if re.search(r'\b\d{7}\b',masked):return majors,True
    catalog=re.search(r'\b(?:bao nhieu nganh|nhung nganh nao|cac nganh nao|danh sach (?:cac )?nganh)\b',masked)
    reference=re.search(r'\bnganh (?:nay|do|ay)\b',masked)
    if catalog or reference:return majors,False
    # Check the requested name zone after masking whole registered names first.
    # This preserves official names containing "và" and exposes a missing comparison member.
    cue=re.search(r'\b(?:so sanh(?: giua)?|(?:ma )?nganh)\s+',masked)
    candidate=masked[cue.end():] if cue else (masked if spans and re.search(r'\b(?:va|voi|hay)\b',masked) else '')
    if candidate:
        candidate=re.sub(r'\b(?:19|20|21)\d{2}\b',' ',candidate)
        candidate=re.sub(r'\b(?:hoc phi|hoc bong|diem chuan|diem san|ma nganh)\b',' ',candidate)
        candidate=re.split(r'\b(?:hoc|ra truong|co|la|nhu|duoc|tai|nam|huit|hufi|nganh nao|phu hop)\b',candidate,maxsplit=1)[0]
        candidate=re.sub(r'\b(?:knownmajor|va|voi|hay|cung|giua|nganh|cua|thi|sao|gi|nao|nay|do|ay|minh|em|toi|ban|tot|de|cho)\b',' ',candidate)
        if candidate.strip():return majors,True
    if not majors and re.search(r'\bma nganh\b',normalized):return majors,True
    return majors,False
