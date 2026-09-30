# LTX trong Mambot

```text
static/index.html + js/app.view.js
  → features/chat/chat.controller.js       Gate 1: lifecycle, history, abort, stale guard
  → features/chat/chat.api.js
  → shared/http.js                        only fetch location
  → backend/routes/api.py                 strict DTO, HTTP mapping
  → backend/services/chat.py              answer policy + orchestration
  → backend/operations/knowledge.py       named domain operations
  → backend/db/gateway.py                 Gate 2: authority + schema + limits + audit
  → backend/db/store.py                   local JSON OR read-only MongoDB
```

Library và system/health có controller/API riêng. Composition root là `backend/app.py`; việc root nối dependency không phải endpoint truy cập thẳng DB. Middleware xử lý size/origin/rate-limit; routes không đọc raw DB.

Bản 1.4: `backend/domain/conversation.py` là các hàm thuần nhận câu hỏi, lịch sử giới hạn và metadata tri thức đã qua gateway. Nó chỉ nhận diện ngành/chủ đề/năm, không gọi transport hoặc DB. Service áp dụng chính sách hỏi lại/phạm vi/năm, rồi gọi retrieval; điều kiện chọn chủ đề/năm/ngành áp dụng cho cả lexical và dense. Không thay đổi DTO, operation authority hoặc quyền dữ liệu để thêm ngữ cảnh hội thoại.

Bản 1.5: domain giữ riêng loại điểm (điểm chuẩn/điểm sàn) và danh sách chủ đề; service chọn bằng chứng cho mỗi chủ đề, yêu cầu đủ năm/phần và trả `mode: clarification` khi cần làm rõ. Mode mới được feature API kiểm tra khi đọc stream/phiên và view trình bày; mode lạ vẫn bị từ chối. Không chuyển transport, DB hoặc quyền ghi sang domain/controller.

Bản 1.6: `domain/corrections.py` xử lý mệnh đề sửa ý; `domain/majors.py` nhận tên/mã từ metadata đã được gateway kiểm định. `conversation.py` kết hợp chúng vào ngữ cảnh giới hạn. Cache bộ tên là hàm thuần theo tên/mã, không lưu câu hỏi hay trạng thái người dùng. Controller của thư viện xử lý lọc nhiều từ; API/transport và operation giữ nguyên trách nhiệm.

Bản 1.7: domain giải quyết thứ tự/số lượng ngành và câu chọn ngành sau làm rõ từ lịch sử giới hạn. Service hỏi lại khi tham chiếu không xác định được. Chat controller quyết định có nội dung cần xác nhận trước khi reset; view đọc bản nháp và hiển thị hộp thoại. Chat API kiểm định chung nguồn/metadata ở ranh giới stream và sessionStorage, giữ year/data_mode qua khôi phục. Không thêm endpoint, quyền dữ liệu hay thay đổi operation đã phát hành.

Bản 1.8: domain nhận năm là phần bổ sung cho câu chọn/tham chiếu ngành; service kiểm tra đủ ngành sau truy hồi trước khi gọi LLM hoặc trình bày so sánh. Controller gộp thông báo tiến trình bằng microtask, giữ trạng thái đồng bộ cho dừng/reset và chặn thông báo cũ. View chỉ xóa bản nháp tương ứng câu đã gửi. Không thay đổi transport, endpoint, gateway hoặc authority.

Bản 1.9: service chia câu hỏi nhiều năm thành các phần có giới hạn; domain retrieval lọc theo từng bộ năm và ưu tiên loại nguồn điểm chuẩn trước top-k. Adapter LLM nhận thêm năm trong evidence; service vẫn kiểm tra đủ citation. Controller xuất năm/ngày nguồn trong TXT, view trình bày nhãn năm và giữ focus bằng readOnly thay vì disabled. Không mở thêm endpoint/quyền DB hoặc thay đổi hợp đồng operation đã phát hành.

Bản 1.2: API mặc định được giải quyết từ URL của feature module, nên `/mambot/static/...` gọi `/mambot/api/...`, kể cả dưới một mount ngoài. Endpoint cũ là alias tương thích, vẫn dùng cùng quota/boundary. Architecture checker nhận cả endpoint có prefix và đường dẫn tương đối.

Phiên hội thoại tùy chọn là dữ liệu do trình duyệt sở hữu: controller quản lý lựa chọn/lịch sử; adapter trong chat.api.js đọc/ghi sessionStorage có schema, TTL và giới hạn byte. Adapter không truy cập kho tri thức. View chỉ nhận snapshot và dispatch hành động; mọi lần đọc tri thức backend vẫn đi qua gateway như trước.

## Hai operation ban đầu

| Operation | Tham số | Runtime |
|---|---|---|
| knowledge.snapshot@1.0.0 | object rỗng, không cho key lạ | đọc tối đa 100 bản ghi, 8s, 512 KiB |
| knowledge.semantic@1.0.0 | vector 1024 số hữu hạn, TOP_K 1..20 | Atlas vector search, 8s, tối đa 20 bản ghi |

Source collection và allowlist chỉ `huit_kb`. Chỉ đọc, không có registered command/transaction vì web con này không có mutation DB. Mỗi query kiểm tra lock/version/checksum và schema đầu ra trước khi dữ liệu lên service. Checksum được tính từ toàn bộ authority trừ trường checksum, UTF-8 canonical JSON, sort_keys, separators `(',', ':')`, ensure_ascii=False.

Giới hạn thời gian Mongo áp dụng qua maxTimeMS + connection/socket timeout; gateway cũng kiểm tra thời gian đã trôi qua sau khi driver trả về. Provider có timeout kết nối 5s/đọc 10s, ngân sách 20s kiểm tra giữa các chunk và giới hạn raw response 128 KiB; lần đọc đang chờ vẫn chịu timeout riêng. Local mode đọc file trong dự án; post-check thời gian local không phải sandbox ngắt cứng tác vụ Python.

Middleware giới hạn 4 chat đồng thời trong một tiến trình, chung cho endpoint cũ/mới; health/library không chiếm slot chat. Đây là kiểm soát tài nguyên HTTP, không thay thế authority. Cache snapshot trong driver local chỉ tránh giải mã lặp khi file không đổi, không cache kết quả kiểm định gateway. Khi file đổi/lỗi/mất, không bỏ qua schema hay lấy dữ liệu cũ làm fallback.

Audit ghi request ID, public-reader principal, operation/version/hash, trạng thái allowed/denied, số kết quả và thời gian. Không ghi params/tri thức/khóa. Nếu audit ghi không được, cả operation thất bại (fail closed). Web không phục vụ thư mục data, registry, backend hay var.

## Chốt ở thời điểm viết code

Architecture checker chặn transport ngoài shared, endpoint ngoài API, controller truy cập DOM, import đảo chiều và driver/query trong route/service. Python kiểm tra AST; JS kiểm tra import/transport pattern. Đây là static contract cho codebase hiện tại, không phải trình phân tích mọi cú pháp JavaScript hoặc hệ thống chống code đối kháng.

Tests thử checksum sai, operation lạ, schema input/output, vector sai, giới hạn, dữ liệu private, cost, audit lỗi, chế độ Mongo không fallback; frontend thử stale response, reset, abort, duplicate, history và NDJSON bị chia byte/ngắt. CI có thêm đối chiếu operation history với base PR.

`AGENTS.md` giúp AI hiểu hợp đồng. Branch protection/review giúp bảo vệ gate khỏi bị sửa. JSON Schema runtime không ngăn mọi lỗi nghiệp vụ/LLM; cần bộ dữ liệu đánh giá riêng cho tuyển sinh thực tế.

## Lựa chọn khác bản gốc

- Không import nguyên rag_core vì nó trộn DB trực tiếp, cấu hình provider và đọc .env.
- Tái sử dụng có chọn lọc các hàm ngôn ngữ thuần; dữ liệu giữ provenance.
- RAG local thay dense bằng TF–IDF để chạy ngay và gắn với notebook được cung cấp. Đây là thay đổi thuật toán có chủ đích, không tuyên bố tương đương điểm benchmark gốc.
- Dense tùy chọn vẫn E5 1024D, kết hợp lexical qua reciprocal-rank fusion. Không dùng vector local đã loại bỏ.
- Không có raw DB fallback, generic query endpoint, admin mặc định, API chạy script hoặc exec code do chatbot tạo ra.

Bản 1.10: domain/student_support.py nhận diện nhu cầu hỗ trợ và tạo hướng dẫn thuần; service chọn hội thoại/hỗ trợ hoặc luồng evidence. Adapter LLM dùng prompt hỗ trợ riêng và chung giới hạn phản hồi. API frontend nhận hai mode mới, view chỉ trình bày nhãn/gợi ý và phát action; controller giữ lịch sử/khôi phục như trước. Hướng dẫn có sẵn không đọc DB; mọi truy hồi tri thức vẫn qua operations/gateway. Không thay authority, gate hoặc mở endpoint mới.

