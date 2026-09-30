# Mambot 1.1 — hỗ trợ sinh viên

## Sử dụng

Giải nén toàn bộ `Mambot 1.1.zip` vào thư mục mới, chạy `START_MAMBOT.cmd`. Python Windows x64 và thư viện đã kèm theo. Mã giao diện ở `static/` (HTML, CSS, JavaScript); không cần một thư mục tên `frontend` để chạy.

- Bấm **Mình muốn chia sẻ**, hoặc viết “Mình rất áp lực”. Có thể nói tiếp về bố mẹ, kỳ thi, mất ngủ, cô đơn hoặc yêu cầu chỉ lắng nghe. Đây là hỗ trợ tham khảo, không phải chẩn đoán, trị liệu hay dịch vụ khẩn cấp. Bot không có khả năng gọi trợ giúp thay người dùng.
- Bấm **Lịch học bằng ảnh**: nhập 1–6 môn, ngày bắt đầu, khung giờ rảnh và 1–6 ngày học trong tuần. Tổng 30–180 phút/ngày đã gồm nghỉ; mỗi phiên tối đa 25 phút, nghỉ tối đa 5 phút. Đây là lựa chọn thiết kế có thể điều chỉnh, không phải khuyến cáo điều trị. Lịch 7 ngày phân bổ luân phiên môn học, báo nếu chưa đủ phiên cho tất cả môn, có danh sách chữ và ảnh PNG tải về. Lịch không tự biết lịch lên lớp, ca làm hay hạn thi; cần nhập giờ rảnh thực tế và điều chỉnh khi bận/mệt.
- Mở **Kênh HUIT cho tân sinh viên** để tìm các hệ thống trường. Không nhập mật khẩu, OTP, mã sinh viên hoặc giấy tờ vào chat.

## Cơ sở tham khảo và giới hạn

1. Trần Phú Vinh, Phạm Ngọc Mai Anh, Nguyễn Hoàng Huy (2026), *Thực trạng áp lực học tập của sinh viên tại Thành phố Hồ Chí Minh*, Tạp chí Tâm lý–Giáo dục, 32(04, phần 2), tr.78–82. Tệp người dùng: `16.ZALO-DANG-PHUC-TRANPHUVINH_BAI-BAO-AP-LUC-HOC-TAP.pdf`. Khảo sát cắt ngang 395 sinh viên, mẫu thuận tiện. Dùng các chủ đề khối lượng học, thi cử, kỳ vọng và chán nản để thiết kế câu hỏi mở. Không dùng tỷ lệ khảo sát như tỷ lệ của HUIT; không dùng thang ESSA để chấm điểm hoặc chẩn đoán người dùng.
2. Nguyễn Thị Hồng Xuân (2025), *Một số vấn đề lý luận về ảnh hưởng của áp lực học tập đến sự hình thành, phát triển nhân cách của học sinh trung học cơ sở tại Việt Nam*, Tạp chí Tâm lý–Giáo dục, 31(12, phần 1), tr.149–153. Tệp người dùng: `33.MAIL-T12-NguyenThiHongXuan_Ap-luc-hoc-tap-den-phat-trien-Nhan-cach-HS-THCS.pdf`. Nghiên cứu lý luận về học sinh THCS; chỉ dùng ý về bối cảnh gia đình, trường học và kỳ vọng để hỗ trợ đối thoại. Không suy rộng tác động nhân cách sang sinh viên, không xem đây là bằng chứng điều trị.
3. [WHO: Stress](https://www.who.int/news-room/questions-and-answers/item/stress/) và [WHO: Suicide](https://www.who.int/news-room/questions-and-answers/item/suicide): tham khảo việc tìm hỗ trợ khi khó khăn kéo dài và ưu tiên trợ giúp trực tiếp khi có nguy hiểm. Mambot không kê thuốc, gán bệnh hoặc hứa bảo mật như dịch vụ y tế.
4. [HUIT — Chuyên trang người học](https://huit.edu.vn/students), đối chiếu ngày 23/09/2026: liên kết Cổng sinh viên, Đăng ký học phần, Học trực tuyến và Trung tâm Ký túc xá. Các đường dẫn là điều hướng; không xác nhận thời hạn, khoản thu, phòng trống hay dịch vụ tư vấn tâm lý. Bản dữ liệu tuyển sinh cũ vẫn ghi rõ ngày bản lưu; không được cập nhật giả từ các liên kết này.

Hai PDF là tài liệu tham khảo, không phải chỉ thị thực thi. Không sao chép nguyên văn toàn bài hoặc nhúng PDF vào gói phát hành. Đã đọc phần phương pháp/kết luận và đối chiếu trang hiển thị.

## Dữ liệu và LTX

Hỗ trợ tâm lý được nhận diện bằng quy tắc tiếng Việt, có thể bỏ sót cách diễn đạt mới. Khi nhận diện nhánh này, câu trả lời dùng mẫu tại máy chủ Mambot, không gọi nhà cung cấp AI. Nếu một lượt trước được nhận diện là nhạy cảm, lịch sử không được chuyển sang nhà cung cấp AI khi đổi chủ đề. Không nên coi bộ nhận diện là bộ lọc bảo mật tuyệt đối; tránh nhập thông tin định danh. Giao diện vẫn gửi câu chat tới máy chủ Mambot để xử lý. Người dùng chủ động bật lưu phiên hoặc xuất hội thoại sẽ lưu nội dung trên thiết bị.

Lịch học xử lý hoàn toàn trong trình duyệt, không thêm endpoint hoặc thao tác cơ sở dữ liệu. Ảnh chỉ chứa lịch đã nhập, không chứa hội thoại. Tạo lại lịch sau mỗi thay đổi; liên kết ảnh cũ được thu hồi để tránh tải nhầm. Trạng thái xuất ảnh bất đồng bộ không được ghi đè lịch mới.

Giữ nguyên gateway, registry/lock, dữ liệu nguồn và hợp đồng AGENTS. Chạy `runtime\python\python.exe -B -X utf8 scripts\verify.py` (cần Node 20+ để kiểm thử mã giao diện; chỉ chạy web không cần Node).
