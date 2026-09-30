# Mambot 1.1 — Hỏi. Hiểu. Chọn.

Giao diện xanh–trắng HUIT, logo trường phía trên tên Mambot. Web con hỗ trợ sinh viên và tra cứu tuyển sinh HUIT được phát triển từ `chatbot2.zip`, có giao diện riêng và các chốt kiểm soát code theo tài liệu LTX. Python/FastAPI + HTML/CSS/JavaScript thuần. Không cần React, npm install, MongoDB hoặc khóa AI để chạy chế độ mặc định.

**Bắt đầu trên Windows 64-bit:** tải **[Mambot 1.1 ZIP đầy đủ](https://github.com/Jakcasas/mambot/releases/download/v1.1.0/Mambot.1.1.zip)** ở phần **Releases → Assets**. Chọn **Extract All / Giải nén tất cả**, mở thư mục `Mambot 1.1` rồi bấm `START_MAMBOT.cmd`. ZIP của nút **Code → Download ZIP** tên `mambot-main.zip` chỉ chứa mã nguồn. Nếu đã tải gói đó, `START_MAMBOT.cmd` sẽ tự lấy bản Windows từ Releases, kiểm tra SHA-256 và giải nén trước khi chạy. Máy cần kết nối mạng cho lần đầu này. Đọc [BAT_DAU.txt](BAT_DAU.txt) và [HUONG_DAN.md](HUONG_DAN.md). Các lệnh bên dưới chỉ dành cho môi trường phát triển từ mã nguồn.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

Mở **http://127.0.0.1:8000/mambot/**. Dừng bằng Ctrl+C trong cửa sổ máy chủ.

## Mới trong 1.1

- Bộ khởi chạy báo chính xác file thiếu và thư mục đang chạy; hỗ trợ thư mục cha chứa Mambot 1.1.
- Kiểm tra các tệp giao diện trước khi chạy để tránh trang thiếu CSS hoặc JavaScript sau giải nén.
- Giữ hỗ trợ chia sẻ áp lực, lịch học xuất PNG và các kênh HUIT: xem [STUDENT_CARE.md](STUDENT_CARE.md).
- Mã nguồn GitHub không chứa Python portable: dùng lệnh tạo môi trường bên trên. ZIP Windows có runtime đi kèm.

## Có gì trong bản này?

- Chức năng hội thoại: chào hỏi tự nhiên, lập kế hoạch ôn thi theo số ngày/thời gian rảnh, bản nháp email, thuyết trình, làm việc nhóm, định hướng và tân sinh viên.
- Hội thoại hỗ trợ tách khỏi thông tin của trường; câu hỏi cá nhân/quy định chưa có nguồn được hướng dẫn xác minh. Có đường dẫn đến chatbot HUIT chính thức.
- Khi cấu hình OpenRouter, các luồng giải thích bài học, email, thuyết trình và làm việc nhóm có thể dùng AI; nếu lỗi sẽ trở về hướng dẫn có sẵn. Xem [phạm vi hội thoại](docs/STUDENT_SUPPORT.md).
- Chat tiếng Việt, gợi ý câu hỏi, nguồn trích dẫn, hủy/thử lại, tạo hội thoại mới, sao chép và xuất TXT/JSON.
- Tùy chọn giữ phiên trong tab khi tải lại; mặc định tắt, giới hạn 256 KiB và 8 giờ, xử lý phiên hỏng/đầy bộ nhớ.
- Trang, API và tài nguyên cùng dưới `/mambot/`; cập nhật từng tin nhắn khi nhận phản hồi để tránh dựng lại cả hội thoại.
- 45 bản ghi từ kho tri thức trong ZIP, tìm kiếm không dấu, lọc chủ đề, đọc bản lưu và mở nguồn HUIT.
- TF–IDF/cosine từ ý tưởng Module 26, chuẩn hóa tiếng Việt và mở rộng từ khóa kế thừa `rag_core.py`.
- Hai chốt LTX: controller phía giao diện; gateway kiểm tra operation phía dữ liệu.
- Hai operation có phiên bản, checksum SHA-256, parameter/output schema, giới hạn và audit.
- Chế độ MongoDB tùy chọn; E5 1024 chiều và OpenRouter tùy chọn.
- Giới hạn 4 chat đồng thời/tiến trình, báo thời gian chờ khi quá tải; phản hồi AI lỗi/cắt ngắn chuyển về trích đoạn có nguồn.
- Kho local tự nạp lại khi file thay đổi; lỗi dữ liệu vẫn bị gateway từ chối.
- Giữ ngữ cảnh ngành qua câu hỏi tiếp nối; nhận tên viết tắt/mã ngành, đổi ngành và đối chiếu tối đa 3 ngành có nguồn.
- Hỏi lại khi ngữ cảnh mơ hồ; phân biệt điểm sàn với điểm chuẩn, từ chối dùng số liệu khác năm hoặc của HUIT để trả lời cho trường khác được nhận diện.
- Bỏ gợi ý ngành dựa riêng vào giới tính; hỏi thêm sở thích và mục tiêu nghề nghiệp.
- Câu hỏi có tối đa 3 chủ đề chọn bằng chứng cho từng phần; giữ ý điểm chuẩn qua câu tiếp nối chỉ có năm.
- Phân biệt cần làm rõ với thiếu dữ liệu; chặn thay ngành chưa nhận diện bằng ngành gần tên; nhận lời cảm ơn mà vẫn giữ ngữ cảnh.
- Nhận câu sửa ý dạng “không phải X mà là Y”; kiểm tra đủ các ngành trong câu so sánh, hỗ trợ Logistics/TMĐT và tìm kiếm nhiều từ trong kho.
- Hiểu “cả hai ngành đó”, “ngành thứ hai” theo ngữ cảnh gần nhất; câu trả lời ngắn sau khi bot hỏi làm rõ giữ chủ đề và năm đang hỏi.
- Bảo vệ bản nháp khi tạo hội thoại mới; giữ năm của nguồn khi khôi phục phiên và kiểm tra phản hồi lỗi trước khi lưu.
- Giữ chủ đề khi câu tham chiếu/chọn ngành kèm năm mới; không trả so sánh thiếu ngành sau khi lọc dữ liệu theo năm.
- Gợi ý câu hỏi giữ bản nháp khác đang soạn; gộp thông báo tiến trình cho các đoạn phản hồi nhận cùng lúc để giảm dựng lại giao diện.
- Khi kho có nhiều năm, chọn nguồn cho từng năm và giữ đủ trích dẫn; giới hạn tối đa 3 phần ngành/chủ đề–năm mỗi lần.
- Chọn nguồn điểm chuẩn trước giới hạn xếp hạng; cảnh báo riêng phần năm chỉ có điểm sàn. Thẻ nguồn và TXT ghi rõ năm dữ liệu/ngày bản lưu.
- Gửi bằng Enter giữ vị trí trong ô nhập để gõ câu tiếp theo sau khi bot trả lời.
- `AGENTS.md`, architecture checks, 241 tests, GitHub Actions và kiểm tra lịch sử operation bất biến.

## Phạm vi

Đây là **web con mới tập trung chat và tri thức**, không phải bản thay thế tương thích toàn bộ chatbot2. Các màn hình admin, đăng nhập, crawl/sync, cache Mongo và sinh ảnh của bản cũ không được đưa vào ứng dụng này. Không có endpoint ghi/xóa MongoDB. Chỉ các operation đọc đang dùng được chuyển sang LTX; không tuyên bố đã migrate cả 52 module cũ.

Mặc định dùng **hướng dẫn có sẵn và trích đoạn tìm được**, không có mô hình ngôn ngữ chạy tại máy. Khả năng hiểu hội thoại tự do còn giới hạn. Kho dữ liệu là bản lưu ngày **27/07/2026** trong ZIP, chưa được xác minh lại với thông báo hiện hành. Xem [nguồn gốc và thay đổi](docs/PROVENANCE.md).

## Kiểm tra code

Cần Node.js 20+ để chạy kiểm thử JavaScript; không cần Node để phục vụ web.

```powershell
.\.venv\Scripts\python.exe scripts\verify.py
```

Luồng kiến trúc: [docs/LTX_ARCHITECTURE.md](docs/LTX_ARCHITECTURE.md). Kết quả kiểm tra và giới hạn: [docs/VALIDATION.md](docs/VALIDATION.md).

## Chạy trên máy chủ

```sh
docker build -t mambot .
docker run --rm -p 8000:8000 -e MAMBOT_DATA_MODE=local mambot
```

Đây là hướng dẫn triển khai, không phải thông báo đã đăng web lên Internet. Gắn reverse proxy HTTPS và thiết lập môi trường phù hợp trước khi mở cho người dùng ngoài máy. Xem phần triển khai trong HUONG_DAN.md.
