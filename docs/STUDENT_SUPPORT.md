# Hội thoại hỗ trợ sinh viên — Mambot 1

## Trải nghiệm mới

Tham khảo giao diện công khai của [chatbot HUIT](https://chatbot.huit.edu.vn/) ngày 22/09/2026: lời chào ngắn, ô hỏi đáp và kênh liên hệ chính thức. Không gửi câu hỏi thử, thu thập hội thoại hoặc suy đoán cách triển khai phía máy chủ của website đó. Mambot là dự án học tập độc lập, không phải chatbot chính thức của trường.

Màn hình chào giữ màu xanh–trắng và logo HUIT, đổi gợi ý sang học tập, định hướng, email và tra cứu. Trong hội thoại có nút đổi chủ đề nhanh. Câu trả lời hỗ trợ không gắn nguồn giả; phần ghi chú giải thích đó là gợi ý tham khảo. Đường dẫn đến chatbot HUIT chính thức luôn nằm ở vùng nguồn.

## Các câu có thể thử ngay

| Nhu cầu | Câu hỏi | Câu trả lời tiếp theo |
| --- | --- | --- |
| Chào hỏi | Chào Mambot nhé! | Bạn có thể làm gì? |
| Lịch ôn thi | Giúp mình lập kế hoạch ôn thi | Giải tích, 7 ngày, 2 giờ mỗi ngày |
| Điều chỉnh thời gian | Lập kế hoạch ôn thi Python 7 ngày, 1,5 giờ mỗi ngày | Còn 3 ngày thôi |
| Email | Soạn email cho giảng viên | Xin gia hạn nộp bài |
| Kiến thức cơ bản | Giải thích vòng lặp Python | Khái niệm nào mình cần biết trước? |
| Thuyết trình | Giúp mình chuẩn bị thuyết trình | Chủ đề môi trường, 10 phút |
| Làm việc nhóm | Nhóm mình cần chia việc | Nhóm có 4 người |
| Đồng hành | Mình đang áp lực vì việc học | Mình lo về kỳ thi |
| Định hướng | Mình chưa biết chọn ngành nào | Mình thích lập trình game |
| Thông tin có nguồn | Chào bạn, học phí HUIT năm 2026 thế nào? | Còn năm 2025? |

Kế hoạch học nhận 1–90 ngày và 10–480 phút/ngày, hỗ trợ giờ thập phân và tuần; tổng thời gian đã tính cả nghỉ. Hỏi lại khi thiếu hoặc vượt giới hạn. Một số môn phổ biến được nhận tên; môn khác vẫn dùng khung ôn tập chung, không bịa chương trình. Không đọc lịch cá nhân hoặc tự tạo sự kiện.

Email luôn là bản nháp có chỗ trống, chưa gửi đi. Nhận ý xin nghỉ/gia hạn qua câu tiếp theo. Không yêu cầu người dùng cung cấp mã số sinh viên, mật khẩu hoặc OTP.

## Khi nào có AI hội thoại?

Không cấu hình khóa: lời chào, kế hoạch, hướng dẫn kỹ năng và một vài ví dụ học tập chạy tại máy. Các chủ đề mới hoặc bài tập tùy ý có thể chỉ nhận được khung hướng dẫn và câu hỏi làm rõ. Đây chưa phải trợ lý đa năng có năng lực ngang ChatGPT/Gemini.

Cấu hình `OPENROUTER_API_KEY` và `OPENROUTER_MODEL` trong môi trường của tiến trình máy chủ rồi khởi động lại (xem HUONG_DAN.md). File `.env.example` chỉ là mẫu, không tự nạp. Khóa không được đưa vào frontend hoặc ZIP. Mô hình/giá do nhà cung cấp quản lý; chọn model còn khả dụng trong tài khoản của bạn.

Khi đã cấu hình, luồng giải thích bài học, email, thuyết trình và làm việc nhóm dùng prompt riêng, chỉ gửi câu hỏi và tối đa 4 lượt người dùng thuộc mạch hỗ trợ đã nhận diện. Prompt yêu cầu phản hồi tiếng Việt, giải thích từng bước, hỏi thêm khi thiếu thông tin, không tự tạo thông tin trường hoặc nguồn. Yêu cầu tra cứu HUIT tiếp tục dùng evidence + citation. Gửi câu hỏi qua nhà cung cấp ngoài xảy ra khi bật AI; thông tin cấu hình và xử lý dữ liệu của nhà cung cấp cần được xem xét trước khi dùng dữ liệu thật.

Phản hồi hỗ trợ có citation/URL hoặc dấu hiệu thông tin trường bị chặn, sau đó dùng hướng dẫn có sẵn. Bộ lọc này là kiểm tra bổ sung theo mẫu, **không xác minh mọi phát biểu của mô hình**. Lỗi mạng, phản hồi bị cắt, sai MIME hoặc quá ngân sách đều dùng fallback; không hiện lỗi nội bộ hay khóa. Chưa kiểm thử model thật trong bản phát hành này.

## Ranh giới và ngữ cảnh

- Hai mode mới: `support` (hướng dẫn có sẵn) và `conversation` (AI hỗ trợ). Không có citation tuyển sinh cho các mode này.
- Tối đa 10 tin nhắn gần nhất được xét. Lời cảm ơn/chào hỏi không xóa ngành và năm đang tra cứu. Câu hỏi học phí/tuyển sinh chuyển về luồng có nguồn; chủ đề khác chặn kế thừa lịch ôn thi.
- Nhận diện theo quy tắc, không phải hiểu ngôn ngữ không giới hạn. Lịch sử do phía khách gửi không được dùng làm system prompt. Nội dung trả về luôn render như văn bản.
- Các câu hỏi lịch thi, bảng điểm, tài khoản, đăng ký học phần hoặc quy định chưa có nguồn nhận hướng dẫn xác minh, không gọi AI để đoán. Không có chức năng đăng nhập, xem hồ sơ, đổi mật khẩu, đăng ký môn hoặc gửi email.
- Hỗ trợ áp lực ở mức lắng nghe và sắp xếp công việc, không chẩn đoán. Một số cách diễn đạt nguy cơ tự hại nhận lời nhắc tìm người tin cậy/cấp cứu; luồng này không dùng model. Tham khảo [hướng dẫn WHO](https://www.who.int/news-room/questions-and-answers/item/suicide). Bộ nhận diện theo mẫu có thể bỏ sót; ứng dụng không phải dịch vụ khẩn cấp.
- Dữ liệu tuyển sinh, logo, registry/lock, AGENTS.md, gateway và architecture checker giữ nguyên. Không mở quyền ghi hay endpoint mới.

## Kiểm thử

`python scripts/verify.py` chạy architecture gate, 178 tests Python và 53 tests JavaScript. Tests mới kiểm tra routing, ngữ cảnh, lịch học, email, dữ liệu cá nhân/quy định, fallback AI, giả nguồn, prompt/budget, stream và khôi phục phiên. Chất lượng model thật và thông tin tuyển sinh hiện hành vẫn cần đánh giá riêng.
