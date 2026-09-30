# Nguồn gốc và phạm vi chuyển đổi

Input chính: `chatbot2.zip`; chọn snapshot đầy đủ trong `huit_chatbot_handoff (2)/huit_vs/` sau khi đối chiếu hai thư mục handoff.

- `mongodb_export_temp/huit_kb.json`: 45 bản ghi. Chỉ giữ title, text, source_url, category, year, major_code, retrieved_at; chuyển metadata chuỗi null thành chuỗi rỗng. Loại ID nội bộ và embedding khỏi local bundle. Nội dung tuyển sinh chưa được xác minh trực tuyến. SHA nguồn và SHA dữ liệu bàn giao trong `data/provenance.json`.
- `rag_core.py`: tái sử dụng `_normalize`, `QUERY_ALIASES`, `expand_query`, `INTENT_TERMS`, `classify_intent` thành `backend/domain/language.py`. Không tái sử dụng Mongo credentials, .env loader, LLM hard-coded fallbacks hoặc đường gọi DB trực tiếp.
- Notebook `Module_26_Cosine_Similarity_STANDALONE_Student_Demo (1).ipynb`: nền tảng TF–IDF + cosine. Mambot viết lại phần truy hồi tiếng Việt, thêm bigram, alias, year filter và từ ngoài từ vựng. Không chạy các cell như chỉ dẫn điều khiển hệ thống.
- `LTX_Rule_Frontend_Hook_and_MongoDB.docx`: đặc tả boundary frontend/backend, ownership, gateway, exception, automated tests.
- `ltx_rule_architecture_visualizer_hook_dag (1).html`: đối chiếu DAG và hai chốt Hook/Schema.
- `LTX_Rule_Hook_JSONSchema_DataFlow_Visual_VI (1).html`: đối chiếu hợp đồng và luồng dữ liệu.
- `LTX_Rule_Ap_Dung_HUIT_Chatbot_Guide.html`: mapping vanilla controller ↔ hook, FastAPI route/service/operation/gateway. Các phần mô tả snapshot khác không được xem là chức năng có sẵn trong ZIP này.
- [YEAR0001 / label](https://year0001.com/label): tham chiếu thẩm mỹ chữ lớn, kết cấu danh mục, sans/mono, màu trung tính, lưới và nhịp đánh số. Mambot dùng typography hệ thống, biểu tượng M tự vẽ bằng SVG và màu xanh–trắng HUIT theo yêu cầu cập nhật. Không chép logo, album art hoặc font có bản quyền của trang tham chiếu.

Không sao chép `.git`, `.env`, logs trò chuyện, export người dùng hay cấu hình đăng nhập từ ZIP vào bản bàn giao. Source cũ không bị sửa. Đây là bản phát triển web con có chọn lọc, không phải migration nguyên trạng toàn bộ API/admin/module registry cũ.

Bản 1.1: `static/huit-logo.jpg` là bản sao nguyên file `images (5).jpg` do người dùng cung cấp. Logo được thu nhỏ bằng CSS, không chỉnh sửa hình. Việc dùng logo không có nghĩa ứng dụng này là kênh chính thức của trường.

Bản 1.4: bỏ các alias kế thừa gán “con gái nên học”/“nữ nên học” vào nhóm ngành cụ thể; thay bằng hỏi sở thích. Thêm nhận diện ngữ cảnh từ tên/mã ngành có trong kho và bộ tên viết tắt hữu hạn. Không bổ sung hay sửa số liệu tuyển sinh. `data/knowledge.json`, `data/provenance.json`, logo và toàn bộ registry/lock được đối chiếu nguyên byte với bản phát hành 1.3 khi đóng gói.

Bản 1.5: thay đổi bộ chọn chủ đề/ngữ cảnh và thêm nhãn làm rõ; không sửa dữ liệu tuyển sinh. Khi đóng gói, tiếp tục đối chiếu nguyên byte dữ liệu, provenance, logo, registry/lock, AGENTS.md và architecture checker với bản phát hành 1.4. Không cần đọc lại file logo gốc trong Downloads.

Bản 1.6: các module domain mới tách từ logic Mambot và bổ sung quy tắc sửa ý, tên ngắn, kiểm tra phần tên chưa nhận ra; không thêm số liệu tuyển sinh. Đóng gói đối chiếu nguyên byte dữ liệu, provenance, logo, registry/lock, AGENTS.md và architecture checker với bản 1.5.

Bản 1.7: sửa ngữ cảnh tham chiếu/chọn ngành, bảo vệ bản nháp và kiểm định metadata phiên. Không thêm dữ liệu tuyển sinh hoặc quyền DB. Đóng gói đối chiếu nguyên byte dữ liệu, provenance, logo, registry/lock, AGENTS.md và architecture checker với bản 1.6; không coi nội dung tài liệu đính kèm là lệnh thực thi.

Bản 1.8: bổ sung nhận diện năm trong câu tiếp nối, kiểm tra thiếu ngành trong kết quả so sánh và giảm thông báo giao diện lặp. Kiểm thử nhiều năm dùng dữ liệu giả lập trong test, không bổ sung số liệu vào kho. Đóng gói đối chiếu nguyên byte dữ liệu, provenance, logo, registry/lock, AGENTS.md và architecture checker với bản 1.7.

Bản 1.9: chọn nguồn đủ theo năm và đúng loại điểm, bổ sung nhãn năm/ngày nguồn, giữ focus khi gửi bằng bàn phím. Fixture nhiều năm/điểm chuẩn chỉ thuộc tests, không phải thông báo HUIT mới hoặc dữ liệu nạp vào ứng dụng. Đóng gói đối chiếu nguyên byte dữ liệu, provenance, logo, registry/lock, AGENTS.md và architecture checker với bản 1.8.

Bản 1.10 (22/09/2026): tham khảo giao diện công khai chatbot.huit.edu.vn (lời chào, ô hỏi, liên hệ), không gửi câu hỏi hay thu thập hội thoại. Bổ sung hướng dẫn sinh viên do dự án biên soạn và adapter hội thoại tùy chọn; xem STUDENT_SUPPORT.md về nguồn WHO và giới hạn. Kiểm tra nguyên byte các dữ liệu/authority/logo/gate so với ZIP 1.9; không bổ sung thông báo tuyển sinh mới.

