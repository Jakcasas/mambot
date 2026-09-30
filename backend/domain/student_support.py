"""Pure, bounded student-help routing. Advice is separate from university evidence."""
import math
import re
from backend.domain.majors import words
from backend.domain.language import requested_topics, _normalize
from backend.domain.conversation import smalltalk, is_followup
from backend.domain.student_care import care_reply


GREETINGS = {
    'greeting': 'Chào bạn! Mình là Mambot, trợ lý đồng hành cùng sinh viên. Mình có thể cùng bạn lập kế hoạch học, chuẩn bị email cho giảng viên, định hướng ngành học hoặc tra cứu thông tin HUIT có nguồn. Hôm nay bạn muốn mình giúp điều gì?',
    'thanks': 'Rất vui vì giúp được bạn! Bạn cứ hỏi tiếp hoặc nói phần nào còn khó, mình sẽ cùng bạn làm rõ nhé.',
    'goodbye': 'Tạm biệt bạn! Chúc bạn học tốt và có thời gian nghỉ ngơi. Khi cần hỗ trợ, cứ quay lại trò chuyện với Mambot nhé.',
    'help': 'Mình là Mambot, một trợ lý AI dành cho sinh viên trong dự án học tập độc lập. Mình có thể giúp bạn:\n• Lập kế hoạch ôn thi, chia nhỏ bài tập và quản lý thời gian.\n• Soạn email, chuẩn bị thuyết trình và phối hợp làm việc nhóm.\n• Khám phá sở thích để định hướng ngành học.\n• Tra cứu tuyển sinh HUIT từ bản lưu có nguồn.\n\nMình không truy cập tài khoản hay hồ sơ sinh viên và không thay thế bộ phận tư vấn chính thức. Bạn đang cần giúp việc gì nhất?',
    'checkin': 'Mình luôn sẵn sàng trò chuyện cùng bạn. Mình là AI nên không có cảm xúc như con người, nhưng có thể lắng nghe và giúp bạn sắp xếp việc cần làm. Hôm nay việc học của bạn thế nào?',
}

# Institutional and private-record questions must never be answered by the general model.
POLICY = r'\b(?:dang ky (?:hoc phan|mon hoc|tin chi)|(?<!du )lich (?:thi|hoc|nghi)|thoi khoa bieu|diem (?:ren luyen|trung binh|gpa|cua (?:minh|em|toi))|bang diem|quy che|(?:dieu kien|xet|chuan|ho so) tot nghiep|bang tot nghiep|bao luu|chuyen nganh|chuyen truong|hoc lai|thi lai|phuc khao|cong tac sinh vien|phong dao tao|ky tuc xa|hoc vu|canh bao hoc tap|tai khoan|mat khau|ma otp|ma xac thuc|cong sinh vien)\b'
PATTERNS = (
    ('email', r'\b(?:viet|soan|sua|gop y)(?: giup (?:minh|em|toi))?(?: mot)? (?:email|mail|thu)\b'),
    ('study', r'\b(?:ke hoach (?:hoc|on)|lich (?:on|tu hoc)|on thi|on tap|quan ly thoi gian|sap xep (?:viec hoc|thoi gian)|hoc hieu qua|cach (?:hoc|ghi nho)|mat goc|hoc khong vao|(?<!dien )tu hoc)\b'),
    ('presentation', r'\b(?:thuyet trinh|lam slide|chuan bi bai noi)\b'),
    ('teamwork', r'\b(?:lam viec nhom|hoc nhom|bai tap nhom|chia viec|phan cong nhom)\b'),
    ('wellbeing', r'\b(?:ap luc|cang thang|stress|qua tai|lo lang|buon qua|chan nan|met moi|mat dong luc|so truot|so rot)\b'),
    ('onboarding', r'\b(?:tan sinh vien|minh moi nhap hoc|chuan bi (?:vao|di) dai hoc)\b'),
    ('orientation', r'\b(?:chua biet (?:chon|hoc) nganh|khong biet (?:chon|hoc) nganh|tu van huong nghiep|dinh huong ban than)\b'),
    ('learning', r'\b(?:giai thich|huong dan|giup (?:minh|em|toi) hieu|bai tap|bai toan)\b'),
)


def explicit_kind(text):
    normalized=words(text)
    return next((kind for kind,pattern in PATTERNS if re.search(pattern,normalized)),None)


def needs_official_information(text):
    normalized=words(text)
    return bool(re.search(POLICY,normalized) or requested_topics(text) or
                re.search(r'\b(?:tuyen sinh|ma nganh|diem chuan|(?<!gia )han (?:nop|dong)|quy dinh|chinh sach|hoc bao lau)\b',normalized))


def is_support_detail(kind,text):
    patterns={
        'study':r'\b(?:\d+ (?:ngay|tuan|gio|phut|tieng)|mon|chuong|giai tich|dai so|xac suat|python|tieng anh|vat ly|hoa hoc|kinh te vi mo)\b',
        'email':r'\b(?:xin (?:nghi|phep|gia han)|thay|co|giang vien|nop bai|bai tap|email|mail|thu)\b',
        'presentation':r'\b(?:chu de|noi ve|\d+ phut|slide|trinh bay)\b',
        'teamwork':r'\b(?:nhom|\d+ (?:nguoi|ban|thanh vien)|chia viec|bai tap)\b',
        'wellbeing':r'\b(?:bai vo|ky thi|thi cu|deadline|gia dinh|ban be|minh lo|minh so)\b',
        'learning':r'\b(?:de bai|vi du|khai niem|cong thuc|python|vong lap|ham so|dao ham)\b',
    }
    return bool(re.search(patterns.get(kind,r'(?!)'),words(text)))


def support_context(question,history):
    """Keep only a contiguous help thread; user turns select intent, assistant text cannot."""
    previous=[]
    kind=explicit_kind(question)
    for turn in reversed(history[-10:]):
        if turn['role']!='user':continue
        text=turn['content']
        if smalltalk(text):continue
        if needs_official_information(text) and explicit_kind(text)!='email':break
        prior=explicit_kind(text)
        if prior:
            if kind and kind!=prior:break
            kind=kind or prior
            previous.insert(0,text)
            break
        # Only a short answer to a prior help prompt may carry its context forward.
        if len(text)>160:break
        previous.insert(0,text)
    if not kind:return None,[]
    if previous and (not explicit_kind(previous[0]) or any(not is_support_detail(kind,t) for t in previous[1:])):
        previous=[]
    if not explicit_kind(question):
        normalized=words(question)
        schedule_answer=kind=='study' and bool(re.search(r'\b\d+ (?:ngay|tuan|gio|phut|tieng)\b',normalized))
        if (not previous or not is_support_detail(kind,question) or len(question)>160 or (is_followup(question) and not schedule_answer) or
            re.search(r'\b(?:nganh|huit|hufi|truong|hoc phi|thoi tiet|bitcoin|bo qua|ignore|system)\b',normalized)):
            return None,[]
    return kind,[*previous,question]


def study_plan(turns):
    days=None;minutes=None;subject=None
    for text in turns:
        normalized=words(text)
        # Decimal amounts are supported before punctuation is normalized.
        raw=text.lower().replace(',', '.')
        raw=_normalize(raw)
        day=re.search(r'(?<![\d.])(-?\d{1,4})(?![\d.])\s*(ngay|tuan)\b',raw)
        budget=re.search(r'(?<![\d.])(-?\d{1,4}(?:\.\d{1,2})?)(?![\d.])\s*(gio|phut|tieng)\b',raw)
        if day:days=int(day[1])*(7 if day[2]=='tuan' else 1)
        if budget:minutes=round(float(budget[1])*(60 if budget[2] in ('gio','tieng') else 1))
        for pattern,label in ((r'\bgiai tich\b','Giải tích'),(r'\bdai so\b','Đại số'),(r'\bxac suat\b','Xác suất'),
                              (r'\bpython\b','Python'),(r'\btieng anh\b','Tiếng Anh'),(r'\bkinh te vi mo\b','Kinh tế vi mô'),
                              (r'\bhoa hoc\b','Hóa học'),(r'\bvat ly\b','Vật lý')):
            if re.search(pattern,normalized):subject=label
    if days is not None and not 1<=days<=90:
        return 'Mình có thể lập lịch từ 1 đến 90 ngày. Bạn muốn dành bao nhiêu ngày và khoảng bao nhiêu phút học mỗi ngày?'
    if minutes is not None and not 10<=minutes<=480:
        return 'Bạn chọn khoảng 10–480 phút học mỗi ngày để mình chia các buổi có nghỉ nhé. Bạn thực tế có thể dành bao nhiêu phút?'
    if days is None or minutes is None:
        known=(' cho môn '+subject) if subject else ''
        return ('Mình cùng bạn chia nhỏ việc học'+known+' nhé. Hãy cho mình biết môn cần ôn, số ngày còn lại và thời gian học mỗi ngày; ví dụ “Giải tích, 7 ngày, 2 giờ mỗi ngày”.\n\n'
                'Trong lúc chờ, bạn có thể bắt đầu bằng một việc nhỏ: liệt kê các chương, đánh dấu phần chưa hiểu và thử một bài không nhìn đáp án. Mình sẽ dùng kết quả đó để ưu tiên lịch học.')
    first=max(1,math.ceil(days*.3));second=min(days-1,max(first,math.ceil(days*.8)))
    blocks=min(8,max(1,math.ceil(minutes/50)))
    rest=min(5,max(0,(minutes-blocks)//max(1,blocks-1))) if blocks>1 else 0
    learning=minutes-rest*(blocks-1);base,extra=divmod(learning,blocks)
    lengths=[base+(i<extra) for i in range(blocks)]
    daily=' + '.join(str(n) for n in lengths)+' phút học'
    if rest:daily+=f', xen kẽ {blocks-1} lần nghỉ {rest} phút'
    lines=[f'Kế hoạch gợi ý{(" — "+subject) if subject else ""}: {days} ngày · {minutes} phút/ngày.',
           'Mỗi ngày: '+daily+'. Tổng thời gian gồm cả nghỉ là '+str(minutes)+' phút.']
    if days==1:
        lines.append('Hôm nay: chọn phần quan trọng nhất → tự làm bài kiểm tra ngắn → xem lại lỗi. Không cố học toàn bộ nội dung mới cùng lúc.')
    else:
        def period(start,end):return 'Ngày '+(str(start) if start==end else f'{start}–{end}')
        lines.append(f'{period(1,first)}: kiểm tra nền tảng, hệ thống các ý chính và làm bài cơ bản.')
        if second>first:lines.append(f'{period(first+1,second)}: luyện phần còn yếu; tự làm trước khi xem lời giải và ghi lại lỗi.')
        if days>second:lines.append(f'{period(second+1,days)}: làm bài tổng hợp có giới hạn thời gian, chữa lỗi và ôn nhẹ trước buổi thi.')
    lines.append('Cuối mỗi buổi, ghi 1 điều đã hiểu và 1 câu còn vướng để chỉnh lịch ngày sau. Đây là kế hoạch cá nhân gợi ý, không phải lịch thi của trường.')
    lines.append('Bạn đang khó nhất ở chương hoặc dạng bài nào?')
    return '\n\n'.join(lines)


def learning_reply(turns):
    text=words(' '.join(turns))
    if 'python' in text and re.search(r'\b(?:vong lap|for|while)\b',text):
        return ('Vòng lặp trong Python giúp thực hiện một nhóm lệnh nhiều lần. Ví dụ:\n\n'
                'for i in range(3):\n    print(i)\n\n'
                'range(3) lần lượt tạo các giá trị 0, 1, 2. Ở mỗi lượt, i nhận một giá trị và print(i) in nó ra; kết quả là ba dòng 0, 1, 2. Phần thân vòng lặp cần thụt lề.\n\n'
                'Dùng for để duyệt một dãy phần tử. Dùng while khi cần lặp trong lúc một điều kiện còn đúng; nhớ cập nhật điều kiện để tránh lặp vô hạn.\n\n'
                'Bạn thử đổi range(3) thành range(1, 4): kết quả sẽ khác thế nào?')
    if 'dao ham' in text:
        return ('Đạo hàm mô tả tốc độ thay đổi tức thời của một hàm số. Trên đồ thị, đó là hệ số góc của tiếp tuyến tại điểm đang xét.\n\n'
                'Ví dụ f(x) = x² có đạo hàm f′(x) = 2x. Tại x = 3, hệ số góc là 6; với thay đổi rất nhỏ Δx, ta có Δf ≈ 6·Δx. Đây là xấp xỉ gần điểm đó, không phải công thức chính xác cho mọi Δx.\n\n'
                'Bạn đang cần hiểu ý nghĩa, quy tắc tính hay muốn cùng làm một bài cụ thể?')
    return ('Mình có thể giúp bạn hiểu từng bước. Bạn hãy gửi khái niệm hoặc đề bài cụ thể, kèm phần đã thử và chỗ đang vướng (không cần thông tin cá nhân).\n\n'
            'Ta có thể bắt đầu bằng: xác định đề hỏi gì → ghi dữ kiện → thử một ví dụ nhỏ → kiểm tra kết quả. Bản tại máy có một số hướng dẫn nền tảng; các giải thích tự do cần máy chủ được cấu hình AI hội thoại.')


def support_request(question,history):
    normalized=words(question)
    care=care_reply(question,history)
    if care:return care
    if re.search(r'\b(?:(?:tao|lap) lich (?:hoc|tu hoc)|lich hoc (?:bang anh|ca nhan)|thoi khoa bieu ca nhan)\b',normalized):
        return {'kind':'study','generate':False,'turns':[question],'answer':'Mở “Lịch học bằng ảnh” ngay dưới ô chat nhé. Nhập các môn, ngày bắt đầu và khung giờ thực sự rảnh ngoài giờ lên lớp/làm thêm. Mambot sẽ chia phiên học có nghỉ, dành ngày nghỉ theo lựa chọn của bạn và tạo ảnh PNG để tải về. Đây là lịch tự học cá nhân, không phải thời khóa biểu của trường.'}
    kind=explicit_kind(question)
    if kind=='learning' and not re.search(POLICY,normalized) and re.search(r'\b(?:nganh|chuong trinh dao tao|huit|hufi)\b',normalized):return None
    # Drafting an email about a policy is useful, but must use placeholders, never claims.
    if re.search(POLICY,normalized) and kind!='email':
        return {'kind':'official','generate':False,'turns':[question], 'answer':
            'Mình có thể giúp bạn chuẩn bị cách xử lý, nhưng không truy cập tài khoản, bảng điểm hay lịch học cá nhân và chưa có nguồn xác nhận quy định này.\n\n'
            '1. Kiểm tra thông báo và cổng sinh viên bạn đang dùng, đối chiếu học kỳ và ngày ban hành.\n'
            '2. Ghi lại vấn đề, thời điểm và mã lỗi nếu có; liên hệ cố vấn học tập hoặc đơn vị phụ trách qua kênh chính thức của HUIT.\n'
            '3. Không gửi mật khẩu, mã OTP hay giấy tờ cá nhân vào cuộc trò chuyện.\n\n'
            'Nếu bạn học HUIT, mở “Kênh HUIT cho tân sinh viên” bên dưới: Cổng sinh viên để xem lịch và kết quả; Đăng ký học phần để truy cập hệ thống đăng ký; Trung tâm Ký túc xá để đọc thông báo lưu trú. Các đường dẫn không xác nhận hạn đăng ký hay phòng còn trống.\n\n'
            'Bạn đang gặp bước nào? Mình có thể giúp soạn email hỏi bộ phận phụ trách hoặc giải thích phần thông báo đã bỏ thông tin cá nhân.'}
    if needs_official_information(question) and kind!='email':return None
    kind,turns=support_context(question,history)
    if not kind:return None
    answers={
        'email': 'Mình gợi ý một bản nháp; bạn thay các phần trong ngoặc trước khi gửi:\n\n'
                 'Tiêu đề: [Học phần / vấn đề] — đề nghị hỗ trợ\n\n'
                 'Kính gửi Thầy/Cô [tên hoặc bộ phận phụ trách],\n'
                 'Em là [họ tên], thuộc [lớp/học phần]. Em viết email để xin hỗ trợ về [vấn đề cụ thể].\n'
                 'Tình huống em gặp: [mô tả ngắn, thời điểm và những bước đã thử]. Em mong được hướng dẫn về [điều cần xác nhận hoặc đề nghị cụ thể].\n'
                 'Em cảm ơn Thầy/Cô đã dành thời gian hỗ trợ.\nTrân trọng,\n[họ tên]\n\n'
                 'Mình chưa gửi email. Bạn muốn viết cho ai và cần hỗ trợ việc gì? Chỉ cần mô tả, không cần gửi mã số sinh viên hay thông tin đăng nhập.',
        'presentation': 'Mình giúp bạn dựng khung bài thuyết trình nhé:\n\n'
                        '• Mở đầu: một câu hỏi hoặc tình huống liên quan đến người nghe.\n'
                        '• Nội dung: chọn 3 ý chính; mỗi ý đi kèm một ví dụ và nguồn nếu dùng số liệu.\n'
                        '• Kết thúc: nhắc lại thông điệp và dành thời gian cho câu hỏi.\n\n'
                        'Mỗi slide nên phục vụ một ý. Tập nói thành tiếng, bấm giờ và rút gọn phần vượt thời gian. Chủ đề của bạn là gì và có bao nhiêu phút trình bày?',
        'teamwork': 'Mình đề xuất bắt đầu từ một bảng việc đơn giản: việc cần làm · người phụ trách · hạn nội bộ · tiêu chí hoàn thành.\n\n'
                    'Thống nhất đầu ra trước khi chia việc, đặt một lần kiểm tra giữa chặng và dành thời gian ghép bài. Nếu một bạn chưa hoàn thành, hỏi rõ trở ngại rồi thống nhất lại phần việc cụ thể, tránh quy kết.\n\n'
                    'Nhóm bạn có bao nhiêu người, đang làm bài gì và vướng ở khâu chia việc hay phối hợp?',
        'wellbeing': 'Nghe có vẻ bạn đang chịu nhiều áp lực. Bạn không cần giải quyết mọi thứ cùng lúc. Nếu muốn, mình có thể cùng bạn chọn một việc nhỏ để bắt đầu hôm nay và sắp xếp các việc còn lại theo mức ưu tiên.\n\n'
                     'Bạn cũng có thể chia sẻ với một người bạn tin cậy để được đồng hành. Điều khiến bạn lo nhất lúc này là bài vở, kỳ thi hay một chuyện khác?',
        'onboarding': 'Chào mừng bạn đến một chặng đường mới! Đây là checklist gợi ý cho tuần đầu:\n\n'
                      '• Ghi lại các môn, việc cần làm và kênh thông báo chính thức.\n'
                      '• Làm quen một vài bạn cùng lớp; lưu cách liên hệ cố vấn học tập.\n'
                      '• Chuẩn bị góc học, thời gian đi lại và lịch tự học có nghỉ.\n'
                      '• Kiểm tra yêu cầu nhập học trực tiếp trong thông báo của trường; mình chưa xác nhận hồ sơ, khoản thu hoặc hạn nộp hiện hành.\n\n'
                      'Bạn đang cần hỗ trợ việc học, làm quen môi trường mới hay một thủ tục cụ thể?',
        'orientation': 'Mình sẽ cùng bạn khám phá lựa chọn từ sở thích và thế mạnh, không chọn thay bạn hay dựa vào giới tính.\n\n'
                       'Hãy cho mình biết: bạn thích hoạt động nào, môn nào bạn học khá hoặc muốn cải thiện, và điều gì quan trọng với bạn khi đi làm. Chẳng hạn: “Mình thích lập trình và giải quyết vấn đề”. Sau đó mình có thể tìm ngành liên quan trong kho HUIT và cùng bạn đọc chương trình học.',
        'learning': learning_reply(turns),
    }
    answer=study_plan(turns) if kind=='study' else answers[kind]
    if kind=='study':answer+='\n\nMuốn có ảnh lịch 7 ngày? Mở “Lịch học bằng ảnh” dưới ô chat và điền khung giờ rảnh.'
    if kind=='onboarding':answer+='\n\nMở “Kênh HUIT cho tân sinh viên” dưới ô chat: Chuyên trang người học tập hợp các hệ thống chính thức; Cổng sinh viên để xem lịch, kết quả và công nợ; Đăng ký học phần và Học trực tuyến có đường dẫn riêng. Đối chiếu thông báo hiện hành trước khi làm thủ tục.'
    if kind=='email':
        purpose='xin gia hạn nộp bài' if 'gia han' in words(' '.join(turns)) else ('xin phép vắng buổi học' if re.search(r'\bxin (?:nghi|phep)\b',words(' '.join(turns))) else None)
        if purpose:
            answer=answer.replace('[Học phần / vấn đề] — đề nghị hỗ trợ','[Học phần] — '+purpose)
            answer=answer.replace('xin hỗ trợ về [vấn đề cụ thể]',purpose)
            answer=answer.replace('Bạn muốn viết cho ai và cần hỗ trợ việc gì?', 'Bạn có thể bổ sung lý do và thời hạn dự kiến vào chỗ trống.')
    return {'kind':kind,'turns':turns,'answer':answer,
            'generate':kind not in ('study','wellbeing','orientation','onboarding') and not any(needs_official_information(t) for t in turns)}


def valid_support_answer(answer):
    """Reject fake sources and obvious institutional claims; this is not fact verification."""
    return (isinstance(answer,str) and 0<len(answer.strip())<=6500 and
            not re.search(r'\[\d+\]|https?://|www\.|\b(?:huit|hufi)\b',answer,re.I) and
            not needs_official_information(answer))
