"""Pure language helpers adapted from chatbot2/rag_core.py; see docs/PROVENANCE.md."""
import re
import unicodedata

def _normalize(text):
    text = str(text or "").lower()
    telex_map = [
        (r"\bngnah\b", "nganh"),
        (r"\bnganhj\b", "nganh"),
        (r"\bhocj\b", "hoc"),
        (r"\bphij\b", "phi"),
        (r"\bxetj\b", "xet"),
        (r"\bdiemj\b", "diem"),
        (r"\bdiems\b", "diem"),
        (r"\bdiemd\b", "diem"),
        (r"\bchuanj\b", "chuan"),
        (r"\bsanj\b", "san"),
        (r"\bhocjba\b", "hoc ba"),
        (r"\bhocj ba\b", "hoc ba"),
    ]
    for pattern, repl in telex_map:
        text = re.sub(pattern, repl, text)
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("đ", "d")
    return re.sub(r"\s+", " ", text).strip()

QUERY_ALIASES = {
    "attt": "an toàn thông tin",
    "cntt": "công nghệ thông tin",
    "data science": "khoa học dữ liệu",
    "data": "khoa học dữ liệu",
    "tiếp thị": "marketing",
    "chuỗi cung ứng": "logistics quản lý chuỗi cung ứng",
    "hỗ trợ học phí": "học bổng hỗ trợ học phí",
    # Natural career-orientation language -> official program vocabulary.
    "xử lý nước thải": "công nghệ kỹ thuật môi trường xử lý nước thải kiểm soát ô nhiễm",
    "kiểm soát ô nhiễm": "công nghệ kỹ thuật môi trường kiểm soát ô nhiễm",
    "máy tự động": "công nghệ kỹ thuật điều khiển và tự động hóa robot công nghiệp",
    "dây chuyền tự động": "công nghệ kỹ thuật điều khiển và tự động hóa",
    "phân tích dữ liệu": "khoa học dữ liệu phân tích khai phá dữ liệu thống kê",
    "dữ liệu lớn": "khoa học dữ liệu big data khai phá dữ liệu",
    # Mở rộng hướng nghiệp & các ngành đào tạo HUIT
    "thiết kế váy": "công nghệ dệt may kinh doanh thời trang và dệt may thiết kế rập trang phục",
    "thiết kế áo": "công nghệ dệt may kinh doanh thời trang và dệt may trang phục",
    "thiết kế đầm": "công nghệ dệt may kinh doanh thời trang và dệt may trang phục",
    "thiết kế trang phục": "công nghệ dệt may kinh doanh thời trang và dệt may",
    "thiết kế thời trang": "công nghệ dệt may kinh doanh thời trang và dệt may",
    "may mặc": "công nghệ dệt may thiết kế rập may công nghiệp",
    "may rập": "công nghệ dệt may kỹ sư thiết kế rập",
    "bán hàng thời trang": "kinh doanh thời trang và dệt may marketing thời trang",
    "thời trang": "công nghệ dệt may kinh doanh thời trang và dệt may",
    "lập trình game": "công nghệ thông tin kỹ thuật phần mềm trí tuệ nhân tạo",
    "lập trình app": "công nghệ thông tin kỹ thuật phần mềm",
    "viết app": "công nghệ thông tin kỹ thuật phần mềm",
    "viết code": "công nghệ thông tin kỹ thuật phần mềm",
    "lập trình viên": "công nghệ thông tin kỹ thuật phần mềm",
    "nấu ăn": "quản trị dịch vụ ăn uống và kỹ thuật chế biến món ăn",
    "làm bánh": "quản trị dịch vụ ăn uống và kỹ thuật chế biến món ăn công nghệ thực phẩm",
    "ẩm thực": "quản trị dịch vụ ăn uống và kỹ thuật chế biến món ăn",
    "đầu bếp": "quản trị dịch vụ ăn uống và kỹ thuật chế biến món ăn",
    "mỹ phẩm": "công nghệ kỹ thuật hóa học hóa mỹ phẩm",
    "son môi": "công nghệ kỹ thuật hóa học hóa mỹ phẩm",
    "hóa chất": "công nghệ kỹ thuật hóa học",
    "thiết kế đồ họa": "truyền thông đa phương tiện đồ họa",
    "truyền thông": "truyền thông đa phương tiện marketing",
    "sếp": "quản trị kinh doanh",
    "quản lý": "quản trị kinh doanh",
    "khởi nghiệp": "quản trị kinh doanh kinh doanh thương mại",
    "xuất nhập khẩu": "logistics và quản lý chuỗi cung ứng thương mại quốc tế",
    "dễ xin việc": "công nghệ thông tin công nghệ thực phẩm logistics và quản lý chuỗi cung ứng marketing kế toán công nghệ dệt may",
}

def expand_query(question):
    """Add canonical admissions terms without removing the user's wording."""
    normalized = _normalize(question)
    expansions = [
        canonical
        for alias, canonical in QUERY_ALIASES.items()
        if re.search(rf"\b{re.escape(_normalize(alias))}\b", normalized)
    ]
    return f"{question} {' '.join(expansions)}".strip()

INTENT_TERMS = {
    "tuition": (
        "hoc phi", "tin chi", "tien hoc", "muc phi", "chi phi hoc",
        "tien de hoc", "bao nhieu tien de hoc",
    ),
    "cutoff": (
        "diem san", "diem chuan", "diem trung tuyen", "diem nganh",
        "diem cntt", "diem it", "diem nay", "diem xet tuyen", "diem tuyen sinh",
        "diem san xet tuyen", "diem chuan xet tuyen", "diem trung tuyen",
    ),
    "scholarship": ("hoc bong", "giam hoc phi", "mien hoc phi", "ho tro hoc phi"),
    "admission": (
        "phuong thuc xet tuyen", "xet tuyen", "xet hoc ba",
        "danh gia nang luc",
    ),
    "career": (
        "chon nganh", "hoc nganh", "hoc ngnah", "hoc gi", "phu hop",
        "huong nghiep", "nghe nghiep", "thich", "muon hoc", "muon lam",
        "dam me", "con gai nen hoc", "nu nen hoc", "de xin viec",
        "thiet ke", "vay", "dam", "may mac", "lap trinh", "nau an",
        "my pham", "game", "truyen thong", "logistics", "xuat nhap khau",
    ),
    "major": ("ma nganh", "to hop", "nganh hoc", "co hoi viec lam", "nganh"),
    "contact": ("dia chi", "co so", "hotline", "lien he"),
}

def classify_intent(question):
    normalized = _normalize(question)
    matches=lambda term:re.search(rf"\b{re.escape(term)}\b",normalized) is not None
    for intent in ("scholarship", "cutoff", "tuition", "admission", "contact", "career"):
        if any(matches(term) for term in INTENT_TERMS[intent]):
            return intent
    scores = {
        intent: sum(1 for term in terms if matches(term))
        for intent, terms in INTENT_TERMS.items()
    }
    intent, score = max(scores.items(), key=lambda item: item[1])
    return intent if score else "general"


def requested_topics(question):
    """Distinct evidence categories; longest phrases own overlapping keywords."""
    normalized=_normalize(question)
    candidates=[]
    for intent in ('tuition','cutoff','scholarship','admission','contact'):
        for term in INTENT_TERMS[intent]:
            for match in re.finditer(rf'\b{re.escape(term)}\b',normalized):
                candidates.append((match.start(),match.end(),intent))
    occupied=[];selected=[]
    for start,end,intent in sorted(candidates,key=lambda item:-(item[1]-item[0])):
        if any(start<b and end>a for a,b in occupied):continue
        occupied.append((start,end));selected.append((start,intent))
    return list(dict.fromkeys(intent for _,intent in sorted(selected)))
