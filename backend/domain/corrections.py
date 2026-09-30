"""Interpret a small, explicit Vietnamese correction grammar, not arbitrary negation."""
import re
import unicodedata
from backend.domain.language import _normalize

NEGATIVE = re.compile(r'\bkh[ôo]ng\s+(?:ph[ảa]i|(?:mu[ốo]n\s+)?h[ỏo]i)\b',re.I)
BOUNDARY = re.compile(r'[,;.!?\n]|\b(?:mà|ma(?!\s+nganh\b))(?:\s+(?:l[àa]|v[ềe]))?\b',re.I)


def effective_question(text):
    """Drop only explicitly rejected clauses; keep original spelling in positive clauses."""
    text=unicodedata.normalize('NFC',text)
    parts=[];cursor=0;corrected=False
    while match:=NEGATIVE.search(text,cursor):
        corrected=True
        parts.append(text[cursor:match.start()])
        end=BOUNDARY.search(text,match.end())
        cursor=end.end() if end else len(text)
    parts.append(text[cursor:])
    value=' '.join(part.strip(' ,;.!?\n') for part in parts if part.strip(' ,;.!?\n')).strip()
    if corrected and _normalize(value) in ('toi','em','minh','toi hoi','em hoi','minh hoi'):value=''
    return value if corrected else text,corrected
