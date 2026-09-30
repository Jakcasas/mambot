"""Local supportive conversation; not diagnosis, screening or treatment."""
import re
from backend.domain.majors import words

DISTRESS = r'\b(?:ap luc|cang thang|stress|qua tai|lo lang|buon qua|chan nan|met moi|mat dong luc|so truot|so rot|co don|lac long|vo dung|mat ngu|kiet suc|tu van tam ly|tram cam|hoang loan|ton thuong|bat nat)\b'
RISK = r'\b(?:tu tu|tu sat|tu lam hai|khong muon song|muon chet|ket thuc cuoc doi|lam hai ban than|khong con muon song)\b'
DETAIL = r'\b(?:bo me|ba me|gia dinh|ky vong|diem|thi cu|ky thi|deadline|bai vo|ban be|mot minh|ngu|an uong|khong biet bat dau|lang nghe|loi khuyen|ke tiep|vai tuan|may tuan|nhieu ngay|minh so|minh lo|bi so sanh|thuoc|ke don|chan doan|an toan|khong co ai)\b'


def risk(text):
    # Explicit negation is not evidence of immediate intent. Other risk clauses still count.
    value=words(text)
    value=re.sub(r'\b(?:khong|chua|chang) (?:he )?(?:muon|dinh|co y dinh|nghi den) (?:tu tu|tu sat|tu lam hai|lam hai ban than|chet)\b','',value)
    return bool(re.search(RISK,value))


def care_reply(question, history):
    q=words(question)
    prior=[]
    for turn in reversed(history[-10:]):
        if turn.get('role')!='user':continue
        value=words(turn.get('content',''))
        if re.search(DISTRESS,value) or risk(value):
            prior.insert(0,value);break
        if len(value)>180 or not re.search(DETAIL,value):break
        prior.insert(0,value)
    anchored=bool(prior and (re.search(DISTRESS,prior[0]) or risk(prior[0])))
    urgent=risk(question)
    risk_followup=anchored and risk(prior[0]) and bool(re.search(r'\b(?:an toan|mot minh|co nguoi|khong co ai|roi|chua|van muon)\b',q)) and len(q)<160
    if urgent or risk_followup:
        if risk_followup and re.search(r'\b(?:da|dang) an toan\b',q) and not urgent:
            answer='Cảm ơn bạn đã cho mình biết bạn đang an toàn. Hãy tiếp tục ở cạnh người bạn tin cậy và nhờ họ cùng tìm sự hỗ trợ từ chuyên gia sức khỏe tâm thần. Nếu cảm giác muốn làm hại bản thân quay lại, hãy tìm hỗ trợ khẩn cấp ngay. Bạn có thể nhờ ai ở cạnh mình lúc này?'
        else:
            answer='Mình rất tiếc vì bạn đang phải chịu đựng điều này. An toàn của bạn cần được ưu tiên lúc này. Hãy liên hệ ngay một người bạn tin cậy và nhờ họ ở cạnh; di chuyển xa những thứ có thể gây hại nếu làm được an toàn. Nếu bạn đã làm hại bản thân hoặc có nguy hiểm tức thời, hãy gọi dịch vụ cấp cứu tại nơi bạn sống hoặc đến cơ sở cấp cứu gần nhất. Mambot không thể gọi hỗ trợ thay bạn. Hiện bạn có đang ở nơi an toàn và có ai ở cạnh không?'
        return {'kind':'urgent','generate':False,'turns':[question],'answer':answer}
    explicit=bool(re.search(DISTRESS,q))
    # A new academic/administrative task exits the sensitive thread.
    switch=bool(re.search(r'\b(?:soan|viet email|hoc phi|diem chuan|dang ky|tao lich|lap lich|ke hoach|giai thich|python|tuyen sinh)\b',q))
    if not explicit and (not anchored or switch or len(q)>220 or not re.search(DETAIL,q)):return None
    all_text=' '.join([*prior,q])
    if re.search(r'\b(?:thuoc|ke don|chan doan|co bi benh)\b',q):
        answer='Mình có thể lắng nghe điều bạn đang trải qua, nhưng không thể chẩn đoán hoặc chọn thuốc cho bạn. Để được đánh giá phù hợp, bạn nên gặp bác sĩ hoặc chuyên gia sức khỏe tâm thần. Điều này đang ảnh hưởng đến giấc ngủ, việc học hay sinh hoạt của bạn như thế nào?'
    elif re.search(r'\b(?:chi muon.*lang nghe|dung.*loi khuyen|khong can.*loi khuyen|chi can.*lang nghe)\b',all_text):
        answer='Mình sẽ lắng nghe và chưa đưa lời khuyên. Bạn có thể kể theo nhịp của mình, không cần sắp xếp câu chuyện thật rõ. Phần nào trong chuyện này đang khiến bạn nặng lòng nhất?'
    elif re.search(r'\b(?:bo me|ba me|gia dinh|ky vong|bi so sanh)\b',q):
        answer='Vừa muốn làm tốt vừa lo phụ lòng gia đình có thể khiến bạn rất mệt. Kết quả học tập không nói hết giá trị của bạn. Nếu bạn muốn, ta có thể chuẩn bị một câu để trao đổi: “Dạo này con thấy quá tải vì…, con cần…”. Điều bạn mong gia đình hiểu nhất là gì?'
    elif re.search(r'\b(?:co don|lac long|ban be|mot minh|bat nat)\b',q):
        answer='Cảm giác thiếu người đồng hành có thể rất khó chịu, nhất là khi ở môi trường mới. Bạn không phải ép mình hòa nhập ngay. Nếu phù hợp, có thể bắt đầu bằng một người đáng tin như bạn cùng lớp hoặc cố vấn; nếu bị bắt nạt, hãy tìm người hỗ trợ trực tiếp. Chuyện gì gần đây khiến bạn cảm thấy lạc lõng nhất?'
    elif re.search(r'\b(?:mat ngu|kiet suc|may tuan|vai tuan|nhieu ngay|khong an|khong di hoc)\b',all_text):
        answer='Nghe như điều này đang làm bạn hao sức. Nếu khó ngủ hoặc căng thẳng kéo dài, ảnh hưởng việc học và sinh hoạt, bạn nên tìm bác sĩ hoặc chuyên gia sức khỏe tâm thần để được hỗ trợ. Trước mắt, có thể giảm một việc chưa gấp và nhờ người tin cậy đồng hành. Tình trạng này đã ảnh hưởng sinh hoạt của bạn như thế nào?'
    elif anchored and re.search(r'\b(?:diem|thi cu|ky thi|deadline|bai vo|khong biet bat dau)\b',q):
        answer='Mình hiểu hơn rồi: việc học đang dồn lại và khiến bạn khó bắt đầu. Nếu bạn muốn thử một bước nhỏ, hãy chọn việc gần hạn nhất, chia thành phần làm được trong 10–15 phút rồi nghỉ. Bạn cũng có thể mở “Lịch học bằng ảnh” bên dưới để sắp xếp theo giờ rảnh. Việc nào đang khiến bạn lo nhất hôm nay?'
    else:
        answer='Nghe có vẻ bạn đang mang nhiều áp lực. Bạn không cần giải quyết mọi thứ ngay lúc này. Mình có thể lắng nghe trước, hoặc cùng bạn chia nhỏ điều đang khó. Điều khiến bạn nặng lòng nhất là bài vở, kỳ vọng từ bản thân/gia đình, hay một chuyện khác?'
    return {'kind':'wellbeing','generate':False,'turns':[question],'answer':answer}
