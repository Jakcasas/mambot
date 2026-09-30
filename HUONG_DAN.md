# Hướng dẫn sử dụng và phát triển Mambot 1.1

## 1. Chạy thử trên Windows

Gói **Mambot 1.1.zip dành cho Windows 64-bit** có sẵn Python 3.12 và thư viện, không cần cài thêm hoặc tải thư viện qua mạng. Node.js chỉ cần khi phát triển/chạy bộ tests JavaScript.

1. Bấm chuột phải `Mambot 1.1.zip` → **Extract All / Giải nén tất cả** vào thư mục mới. Không chạy trực tiếp từ cửa sổ ZIP.
2. Mở thư mục `Mambot 1.1` đã giải nén và chạy `START_MAMBOT.cmd`. Giữ nguyên thư mục `runtime` đi kèm; không dùng `.venv` của bản cũ. Trình duyệt tự mở khi máy chủ đã sẵn sàng.
3. Nếu trình duyệt không tự mở, dùng địa chỉ in trong cửa sổ chạy (mặc định **http://127.0.0.1:8000/mambot/**). Nếu cổng mặc định bận, chương trình thử 8001–8009. Giữ cửa sổ máy chủ mở; Ctrl+C để dừng. Chạy `KIEM_TRA_MAMBOT.cmd` để kiểm tra runtime, dữ liệu và authority.

Nếu dùng **mã nguồn không kèm runtime**, hoặc muốn tạo môi trường phát triển riêng, cần Python 3.11+ và mạng để cài thư viện. Mở PowerShell tại thư mục dự án:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

Không cần kích hoạt Activate.ps1. Nếu máy không có lệnh `py`, dùng `python` thay `py -3`. Nếu cổng 8000 đang bận, đặt `$env:PORT="8010"` rồi chạy lại và mở cổng 8010.

Trên macOS/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py
```

**Không mở trực tiếp static/index.html bằng double-click:** trang cần máy chủ để gọi API và nạp JavaScript module.

## 2. Dùng ba phần của website

**Trò chuyện:** nhập câu hỏi hoặc chọn một ô gợi ý. Bản 1.10 bổ sung chào hỏi, lịch ôn thi, email, thuyết trình, làm việc nhóm và hỗ trợ tân sinh viên; đọc [các ví dụ và giới hạn](docs/STUDENT_SUPPORT.md). Enter gửi; Shift+Enter xuống dòng. Câu hỏi tối đa 800 ký tự. Mambot tìm nội dung liên quan, hiển thị trích đoạn và đường dẫn nguồn. Dùng “Dừng” để hủy việc nhận phản hồi trên trình duyệt. Tác vụ máy chủ đang tính có thể vẫn chạy đến khi hoàn thành; đây chưa phải hủy tác vụ LLM từ xa.

Từ bản 1.8, nếu đang soạn câu hỏi khác rồi bấm ô gợi ý, bản nháp vẫn nằm trong ô nhập sau khi bot trả lời. Chỉ xóa ô nhập khi chính nội dung đó đã được gửi. Bạn có thể gửi tiếp bản nháp hoặc sửa trước khi gửi; bản nháp chưa gửi vẫn không được lưu khi tải lại trang.

Bản 1.9 giữ vị trí bàn phím trong ô nhập khi gửi bằng Enter. Trong lúc chờ, ô nhập chỉ đọc; khi trả lời xong bạn gõ tiếp ngay. Nếu tự chuyển sang vùng khác, web không giành lại vị trí bàn phím khi phản hồi đến. Năm trên thẻ nguồn và trong TXT là năm của dữ liệu; “Bản lưu” là ngày lưu nội dung, hai thông tin có thể khác nhau.

“Xuất .TXT” tải bản văn bản tiếng Việt có nguồn, dễ mở bằng Notepad/Word; “JSON” xuất dữ liệu có cấu trúc. “Cuộc trò chuyện mới”/“Tạo mới” có xác nhận trước khi xóa hội thoại hoặc nội dung đang soạn, kể cả chưa gửi câu nào. Chọn “Giữ lại” để giữ nguyên nội dung; xác nhận tạo mới sẽ xóa và đưa con trỏ về ô nhập. Bản nháp chưa gửi không được tự lưu khi tải lại trang. Chỉ tối đa 10 tin nhắn thuộc các cặp hỏi–đáp hoàn tất gần nhất được gửi lại để hiểu ngữ cảnh. Trả lời lỗi/dừng không được đưa vào lịch sử ngữ cảnh.

**Giữ hội thoại trong tab này** mặc định tắt. Khi bật, Mambot lưu vào sessionStorage của tab để khôi phục sau khi tải lại. Tối đa 100 tin nhắn (50 cặp), 256 KiB UTF-8; khi vượt giới hạn chỉ lưu các cặp gần nhất và thông báo. Phiên quá 8 giờ kể từ lần cập nhật sẽ bị bỏ khi đọc lại. Không đồng bộ với máy chủ, MongoDB, localStorage hay thiết bị khác. Trình duyệt có thể khôi phục sessionStorage khi khôi phục tab; bỏ chọn để chủ động xóa bản lưu. “Tạo mới” xóa nội dung đã lưu nhưng giữ lựa chọn bật lưu phiên. Nếu lưu trữ bị chặn/đầy/hỏng, web báo rõ và vẫn cho chat. Hãy xuất file để giữ hội thoại lâu dài. Bản lưu có thể đánh dấu lượt đang trả lời là chưa hoàn tất khi trang bị đóng bất ngờ.

**Kho tri thức:** tìm có dấu hoặc không dấu, chọn chủ đề, mở từng bản lưu để đọc và bấm mũi tên để đến website nguồn. Đây là 45 bản ghi có sẵn trong ZIP, không phải dữ liệu crawl trực tiếp. Ngày bản lưu là 27/07/2026; không suy ra thông tin còn hiệu lực chỉ từ nhãn năm 2026.

**LTX / Cách hoạt động:** xem chế độ đang chạy, số bản ghi thực tế và hai chốt kiểm soát. “Đã cấu hình AI” chỉ nghĩa là có cấu hình máy chủ, không có nghĩa nhà cung cấp đã được kiểm tra online.

Thử các câu:

- “Ngành Trí tuệ nhân tạo HUIT học những gì?”
- “ma nganh cntt la gi”
- “Học phí HUIT năm 2026 được tính như thế nào?”
- “Các phương thức xét tuyển HUIT năm 2026 là gì?”
- “điểm chuẩn HUIT năm 2035” — cần trả lời chưa đủ dữ liệu thay vì bịa năm tương lai.

Từ bản 1.7, thử “So sánh CNTT và Marketing” → “Cả hai ngành đó học gì?” → “Ngành thứ hai học gì?”. Thứ tự lấy từ các ngành bạn vừa nêu; sau khi chọn một ngành, ngữ cảnh hiện tại là ngành đã chọn. Khi chưa có ngữ cảnh hoặc số ngành không khớp, bot hỏi lại. Sau câu hỏi làm rõ, bạn có thể đáp ngắn “Marketing” để giữ chủ đề/năm vừa hỏi; nêu chủ đề mới như “Marketing học gì?” để chuyển ý. Các quy tắc này có phạm vi hữu hạn, không bảo đảm hiểu mọi cách diễn đạt.

Nguồn trong phiên lưu và file JSON tiếp tục giữ trường năm nếu có. Phản hồi sai cấu trúc được báo lỗi trước khi hoàn tất lượt; các lượt đã lưu trước đó vẫn được giữ nếu bộ nhớ trình duyệt hoạt động bình thường.

Bản 1.8 giữ chủ đề trong câu như “Học phí CNTT và Marketing năm 2026?” → “Ngành thứ hai năm 2025?”. Nếu năm yêu cầu không có dữ liệu, bot báo thiếu học phí đúng năm thay vì chuyển sang mô tả ngành. Sau yêu cầu làm rõ, “Marketing năm 2025” cũng giữ chủ đề cũ. Câu có chủ đề mới rõ ràng như “Ngành thứ hai năm 2026 học gì?” vẫn chuyển sang thông tin ngành. Khi so sánh mô tả các ngành, nếu một ngành không còn bằng chứng phù hợp sau lọc năm, bot báo phần thiếu thay vì chỉ trả ngành còn lại.

Bản 1.9 hỗ trợ đối chiếu theo năm khi kho thực sự có đủ bản ghi: chọn nguồn cho từng năm, trình bày từ năm cũ đến năm mới và yêu cầu AI trích dẫn đủ từng phần. Tối đa 3 phần ngành/chủ đề–năm mỗi lần; ví dụ một chủ đề trong 3 năm được hỗ trợ, còn 2 chủ đề × 2 năm thì cần chia nhỏ. Nếu thiếu một năm, bot báo thiếu thay vì trả năm còn lại. Kho đi kèm vẫn là snapshot cũ, không được bổ sung dữ liệu 2025 qua cải tiến này; câu hỏi học phí 2025 và 2026 hiện vẫn báo thiếu năm 2025.

Điểm “độ khớp” dùng để sắp xếp văn bản, **không phải độ chính xác**. Nó kết hợp cosine với ưu tiên chủ đề; khi bật tìm kiếm dense có thêm RRF. Trích dẫn chỉ chứng minh câu trả lời gắn với bản lưu, không tự chứng minh bản lưu đúng/còn mới.

## 3. Mambot kế thừa và cải tiến những gì?

| Thành phần | Từ tài liệu gốc | Mambot |
|---|---|---|
| Nền web | FastAPI, JS thuần | Giữ nền, viết giao diện Mambot riêng |
| Tri thức | Mongo export trong chatbot2 | 45 bản ghi có provenance, bỏ `_id` và embedding khỏi gói local |
| Tiếng Việt | Chuẩn hóa lỗi gõ, bỏ dấu, alias, intent trong rag_core | Tách thành hàm thuần tái sử dụng |
| Notebook Module 26 | TF–IDF + cosine | Áp dụng cho tiếng Việt, thêm bigram và xử lý từ ngoài từ vựng |
| Giao diện tham khảo | YEAR0001/label | Cảm hứng danh mục, chữ lớn, monospace, đường kẻ, đánh số; không dùng lại logo/ảnh/font độc quyền |
| LTX Rule 1 | View → hook → API → HTTP | Dùng domain controller tương đương hook cho JS thuần |
| LTX Rule 2 | Versioned operation + gateway | Schema, checksum pin, allowlist, limits, output validation, audit |

Một cải tiến quan trọng: phần fallback cũ chứa một số thông tin tuyển sinh viết cứng, có thể khác bản dữ liệu. Mambot lấy mã ngành, mức phí và danh sách từ **nội dung bản ghi**, không viết lại các con số vào code trả lời. Nội dung từ file được xem là dữ liệu; không chạy lệnh hay làm theo chỉ dẫn nhúng trong tài liệu.

## 4. Bật AI diễn đạt tự nhiên — tùy chọn

Mặc định vẫn chat được bằng trích đoạn. Muốn mô hình ngôn ngữ diễn đạt lại, đặt biến môi trường trong PowerShell trước khi chạy:

```powershell
$env:OPENROUTER_API_KEY="<khóa của bạn>"
$env:OPENROUTER_MODEL="<model ID được tài khoản hỗ trợ>"
.\runtime\python\python.exe -B run.py --open-browser
```

Mambot chỉ gọi OpenRouter khi cả khóa và model đều có. Khóa nằm phía server. Không cần cung cấp khóa trong hội thoại với AI lập trình. `.env.example` là **mẫu tham khảo**; ứng dụng không tự đọc `.env`.

Khi bật, câu hỏi, tối đa 6 lượt lịch sử và tối đa 3 đoạn tri thức được gửi tới OpenRouter. Hãy lựa chọn dữ liệu và tài khoản phù hợp. Không có khóa được lấy lại từ ZIP cũ. Khi provider lỗi, phản hồi sai cấu trúc, bị cắt ngắn hoặc trích dẫn có số không hợp lệ, Mambot quay về trích đoạn và thông báo rõ. Việc kiểm tra số trích dẫn không bảo đảm mô hình không diễn giải sai; cần đánh giá RAG trước khi đưa vào tư vấn chính thức.

Luồng NDJSON trả `meta → token → sources → done`; bản hiện tại hoàn tất xử lý câu trả lời rồi chia thành các chunk. Đây **chưa phải** stream token trực tiếp từ nhà cung cấp LLM.

## 5. Kết nối MongoDB — tùy chọn

Dùng một tài khoản **chỉ đọc** kho HUIT của bạn. Không dùng lại thông tin kết nối hard-code hoặc file `.env` trong ZIP.

```powershell
$env:MAMBOT_DATA_MODE="mongo"
$env:MONGODB_URI="<connection string của bạn>"
$env:MONGODB_DATABASE="huit_chatbot"
$env:MAMBOT_VECTOR_ENABLED="0"
.\runtime\python\python.exe -B run.py --open-browser
```

Collection cần là `huit_kb`, có các trường `title`, `text`, `source_url`, `category`, `year`, `major_code`, `retrieved_at`. Dữ liệu mẫu và schema ở `data/knowledge.json`, `registry/knowledge.snapshot@1.0.0.json`. Bản này đọc tối đa 100 bản ghi; vượt giới hạn sẽ từ chối thay vì lặng lẽ bỏ bớt. Với kho lớn hơn, thiết kế operation phân trang/tìm kiếm mới và version hóa.

Không có endpoint nhập, ghi hay xóa DB. Có thể nhập dữ liệu qua công cụ quản trị của bạn bằng tài khoản bootstrap riêng; không cấp quyền ghi cho tiến trình web. Chế độ Mongo lỗi **không** tự chuyển sang file local. `/mambot/api/health` trả 503 và giao diện báo lỗi. Kho rỗng trả `status: empty`, khác với lỗi không truy cập được kho.

Để bật dense vector search:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-vector.txt
$env:MAMBOT_VECTOR_ENABLED="1"
.\runtime\python\python.exe -B run.py --open-browser
```

Atlas cần index `huit_vector_index`, path `embedding`, 1024 chiều, similarity `cosine`. Dữ liệu phải được tạo bằng cùng model `intfloat/multilingual-e5-large`, tiền tố `passage: `; câu hỏi dùng `query: `. Gói local đã bỏ vector để nhẹ và không tự ghi lại embedding. Dùng quy trình ingest đã được kiểm tra của bạn để tạo vector; không tái sử dụng vector khác model/khác tiền tố. Lần đầu E5 tải model, có thể lâu và tốn bộ nhớ. Đây là tùy chọn chưa được kiểm thử với một Atlas thật trong lần bàn giao này.

## 6. Kiểm soát code AI bằng LTX

`AGENTS.md` hướng dẫn AI sửa đúng lớp. Nhưng tài liệu đơn lẻ không đủ: `scripts/check_architecture.py` + tests + GitHub Actions kiểm tra tự động, gateway kiểm tra lúc chạy.

Prompt mẫu khi nhờ AI sửa:

> Đọc AGENTS.md của Mambot. Thêm tính năng [mô tả] theo luồng LTX hiện có. Không gọi fetch trong view/controller, không truy cập DB từ route/service. Giữ operation đã phát hành bất biến, thêm version khi đổi hợp đồng. Thêm test hành vi và chạy python scripts/verify.py. Báo rõ file sửa, lý do và kết quả kiểm tra. Không sửa test/gate chỉ để che lỗi.

Mỗi lần sửa:

1. Xác định feature và lớp chịu trách nhiệm. Ví dụ đổi gợi ý câu hỏi nằm ở HTML; đổi lịch sử/abort ở controller; đổi endpoint ở API; đổi truy hồi ở domain/service.
2. Viết thay đổi và test chứng minh hành vi, kể cả trường hợp lỗi.
3. Chạy `.\.venv\Scripts\python.exe scripts\verify.py`.
4. Review diff, đặc biệt gateway, registry lock, AGENTS.md và CI. Không tự chấp nhận vì AI báo “đã xong”.
5. Nếu đưa lên GitHub, bật branch protection với job `verify` bắt buộc và yêu cầu người review. Workflow đã có trong `.github/workflows/verify.yml`; nó chỉ chạy sau khi bạn tạo repo/push. Chưa có repo hoặc chính sách GitHub nào được tự tạo.

Thay đổi operation: thêm `knowledge.snapshot@1.1.0.json` chẳng hạn, giữ file cũ, tính SHA-256 canonical JSON bằng hàm `checksum()` của gateway, review nội dung/schema/giới hạn rồi chuyển `registry/lock.json` sang version mới. Không sửa file đã phát hành và cập nhật checksum cùng lúc để che thay đổi. Script `check_immutable.py <base-commit>` và CI PR so sánh file cũ với revision gốc.

Không có cơ chế nào bảo đảm tuyệt đối AI luôn viết code đúng. Static checks có thể bỏ sót cấu trúc động; người có quyền sửa gateway/tests/CI vẫn có thể thay đổi rào kiểm soát. Cần quyền repo và review độc lập nếu dùng cho dự án thật.

## 7. Ghép vào website chính / triển khai

Bản đang chạy tại máy không phải URL công khai. Bạn có thể chạy trên máy chủ hỗ trợ Python hoặc dùng Dockerfile kèm theo. Nên dành một hostname riêng như `mambot.<tên-miền-của-bạn>` và liên kết từ website chính.

Từ bản 1.2, trang, API và tài nguyên nằm chung tại `/mambot/`, `/mambot/api/`, `/mambot/static/`. Reverse proxy chỉ cần chuyển nhánh `/mambot/` đến ứng dụng, giữ nguyên đường dẫn. `/` và `/mambot` chuyển tới `/mambot/`. API/assets cũ tại `/api/` và `/static/` vẫn hoạt động khi gọi trực tiếp để tương thích bản cũ; website chính không cần proxy hai nhánh cũ này.

Ví dụ cấu hình Nginx bên trong khối `server` đã có HTTPS (chưa được chạy trên máy chủ thật):

```nginx
location = /mambot { return 308 /mambot/; }
location /mambot/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $http_host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_buffering off;
    proxy_read_timeout 60s;
}
```

Không thêm dấu `/` vào cuối `proxy_pass` ở ví dụ trên: Mambot cần nhận nguyên prefix `/mambot/`. Kiểm tra `/mambot/api/health` và gửi một câu hỏi sau khi ghép vào web chính.

Ví dụ chạy một worker phía sau reverse proxy tại máy chủ:

```sh
MAMBOT_HOST=127.0.0.1 PORT=8000 MAMBOT_TRUSTED_PROXIES=127.0.0.1 python run.py
```

Proxy cần ghi đè `Host`, `X-Forwarded-Proto`, `X-Forwarded-For` đúng giá trị, không chuyển nguyên header giả từ client. Chỉ khai báo IP proxy bạn kiểm soát. Không đặt trusted proxies là `*` nếu chưa cô lập mạng.

Container mặc định chạy 1 worker. Rate limit hiện ở bộ nhớ tiến trình (60 yêu cầu API/phút/IP), cùng tối đa 4 chat đang xử lý trong mỗi tiến trình; nếu dùng nhiều worker/máy cần limiter dùng kho chia sẻ tại proxy. Khi đủ 4 chat, yêu cầu chat mới nhận 503 với Retry-After 2 giây; API health/library vẫn hoạt động. Frontend hiển thị thời gian chờ, không tự gửi lại câu hỏi có thể phát sinh phí AI. Log operation nằm trong `var/operations.jsonl`, không chứa câu hỏi, câu trả lời hay vector; cấu hình lưu trữ/rotation cho vận hành dài hạn. Lịch sử chat chưa có lưu bền hay tài khoản.

Để nhúng iframe, CSP hiện chỉ cho same-origin. Nhúng khác origin cần cấu hình `frame-ancestors` cho đúng website được phép và điều chỉnh X-Frame-Options phù hợp; không mở wildcard.

## 8. Xử lý lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| Python was not found | Cài Python 3.11+ và mở terminal mới; thử `py -3 --version`. |
| Không mở được web | Kiểm tra terminal server còn chạy và đúng PORT; không mở HTML trực tiếp. |
| Thư viện thiếu | Dùng đúng `.venv\Scripts\python.exe`, cài lại requirements trong môi trường đó. |
| “Kho tri thức chưa sẵn sàng” | Kiểm tra file registry/hash/schema và quyền ghi thư mục var; Mongo mode cần URI/allowlist mạng hợp lệ. Không tắt gateway. |
| 429 | Chờ một phút; limiter dành cho API bao gồm health/library/chat. |
| Tìm không đúng chủ đề | Nêu ngành và năm cụ thể, đọc nguồn; cải thiện dữ liệu và test retrieval thay vì hạ gate. |
| Node không tìm thấy khi verify | Cài Node 20+ để chạy tests frontend; ứng dụng Python vẫn chạy độc lập. |

Các chi tiết kỹ thuật và giới hạn đã biết nằm trong `docs/LTX_ARCHITECTURE.md`, `docs/PROVENANCE.md`, `docs/VALIDATION.md`.

## 9. Những thay đổi ở bản 1.1

Giao diện đã dùng xanh–trắng HUIT và logo trường do bạn cung cấp, đặt nhỏ phía trên tên Mambot. Nút “Thử lại câu hỏi” xuất hiện nếu kết nối lỗi hoặc bạn dừng phản hồi; thao tác thử lại thay lượt lỗi, không thêm trùng vào lịch sử.

Chat chờ tối đa 45 giây, tải kho/health tối đa 15 giây. Nếu có lỗi máy chủ, lưu “Mã yêu cầu” trên thông báo để đối chiếu `var/operations.jsonl`. Các lỗi bất ngờ được ghi tên loại lỗi và request ID, không ghi khóa hay nội dung câu hỏi.

Ngữ cảnh vẫn tối đa 10 lượt nhưng thêm giới hạn 32.000 byte để tránh lỗi khi hội thoại dài hoặc chứa nhiều ký tự Unicode. Khi vượt ngưỡng, bỏ cặp hỏi–đáp cũ nhất khỏi phần gửi lên máy chủ; nội dung hiển thị trong trang không bị xóa.

Bản 1.1 có 60 tests tự động. Các giới hạn về dữ liệu bản lưu, AI/Atlas chưa kiểm thử thật và chưa có URL công khai vẫn áp dụng.

## 10. Những thay đổi ở bản 1.2

- Sửa xung đột đường dẫn API/assets khi gắn web con, giữ các kiểm soát request và giới hạn tần suất trên cả đường dẫn mới/cũ.
- Giữ nguyên DOM của các tin nhắn đã có khi nhận phản hồi tiếp theo; chỉ cập nhật nội dung thay đổi. Khung nguồn không bị tạo lại mỗi chunk.
- Thêm lưu phiên có lựa chọn, khôi phục ngữ cảnh từ các cặp hoàn tất; kiểm tra cấu trúc, thời hạn, dung lượng và lỗi bộ nhớ trình duyệt.
- Xuất TXT/JSON; nhãn chính xác cho câu chào và trường hợp chưa có dữ liệu; thông báo kết quả cho trình đọc màn hình.
- Sửa mất bản nháp khi lệnh gửi bị từ chối, xóa bản nháp và đặt focus đúng khi tạo mới từ trang khác. Logo, palette HUIT và các operation đã phát hành được giữ nguyên.
- Kiểm tra cấu trúc health trước khi hiển thị; số tài liệu thống nhất với bộ lọc nguồn tin cậy của kho tri thức.

Bản 1.2 đạt 76 tests: 47 Python và 29 JavaScript, cùng architecture gate. Bản ZIP là mã nguồn chạy local; không bao gồm môi trường .venv, khóa API hoặc dữ liệu phiên người dùng. Xem `docs/VALIDATION.md` cho phạm vi kiểm tra.

## 11. Những thay đổi ở bản 1.3

- Sửa lỗi API trả JSON `null` bị hiểu nhầm là mất mạng. Giữ mã HTTP, mã yêu cầu và thời gian chờ từ Retry-After. Nội dung UTF-8 lỗi được báo riêng.
- Luồng lỗi/quá dung lượng được kết thúc mà không chờ vô hạn thao tác đóng kết nối. Hủy và gửi lại vẫn có chốt chống phản hồi cũ.
- Kho local kiểm tra thay đổi của `data/knowledge.json` khi đọc, dựa trên thời gian sửa, kích thước và định danh file. Giới hạn đọc file trước khi giải mã JSON; cache mới chỉ được gán sau khi đọc trọn file. Nếu file bị hỏng/mất thì báo lỗi, không âm thầm dùng bản cache cũ. Khi sửa file đúng, lần đọc sau tự phục hồi và gateway vẫn kiểm schema/giới hạn. Khi cập nhật dữ liệu nên ghi ra file tạm rồi đổi tên thay thế để tránh người dùng đọc giữa lúc đang ghi; cập nhật provenance kèm nguồn và ngày dữ liệu. Không chỉnh số liệu tuyển sinh khi chưa có nguồn.
- Giới hạn xử lý chat đồng thời như phần triển khai; slot được giải phóng khi hoàn tất hoặc gặp lỗi.
- Provider phải trả JSON UTF-8 không nén, tối đa 128 KiB. Mambot yêu cầu encoding identity và từ chối encoding khác. Kết nối timeout 5 giây, từng lần đọc timeout 10 giây, ngân sách 20 giây được kiểm tra giữa các chunk; một lần đọc đang chờ có thể kéo dài quá mốc 20 giây đến timeout đọc. Đây không phải ngắt tác vụ LLM từ xa. Chỉ nhận câu trả lời hoàn tất (`finish_reason: stop`), không rỗng, tối đa 6.500 ký tự; các trường hợp khác quay về trích đoạn. Không tự cắt câu trả lời dài giữa chừng.

Bản 1.3 đạt **92 tests (59 Python + 33 JavaScript)**. Kiểm thử provider dùng HTTP giả lập, không gọi hoặc xác nhận model OpenRouter thật. Registry/lock giữ nguyên so với bản 1.2; không nới LTX gate để vượt kiểm thử.

## 12. Những thay đổi ở bản 1.4

- Thử lần lượt “CNTT học gì?” → “Ngành này ra trường làm gì?” → “Mã ngành đó?”. Mambot giữ được ngành qua các câu tiếp nối; “Còn Marketing thì sao?” chuyển sang ngành mới. Thông báo bên dưới câu trả lời cho biết ngành được kế thừa.
- Nhận tên ngành trong kho, mã ngành và một số tên viết tắt: CNTT, ATTT, KHDL, QTKD, TMĐT, AI, IT, Fintech. “AI” viết hoa được phân biệt với đại từ “ai”. Đây là bộ quy tắc hữu hạn, chưa phải hiểu mọi cách viết hoặc lỗi chính tả.
- “So sánh Công nghệ thông tin và Trí tuệ nhân tạo” hiển thị trích đoạn có nguồn của cả hai, theo thứ tự bạn hỏi. Tối đa 3 ngành/lần. Nếu hỏi tiếp “ngành đó” sau khi nhắc nhiều ngành, bot yêu cầu chọn rõ ngành. Bản mặc định cung cấp tư liệu để đối chiếu, chưa xếp hạng ngành hoặc đưa ra quyết định thay người học.
- Chủ đề và năm mới được ưu tiên; thiếu năm yêu cầu thì báo rõ các năm có dữ liệu. Câu hỏi về “điểm chuẩn” không được trình bày điểm sàn như điểm trúng tuyển. Câu hỏi “mới nhất” có nhắc rõ nội dung chưa được xác minh hiện hành.
- Khi nhận ra câu hỏi về trường khác, bot nói rõ phạm vi HUIT; câu hỏi tiếp nối giữ phạm vi này đến khi bạn chuyển chủ đề/trường. Nhận diện dùng tên/nhóm từ thông dụng, không bảo đảm nhận mọi trường hoặc câu phủ định phức tạp.
- Không gợi ý nghề chỉ vì người hỏi là nam/nữ. Bot hỏi thêm sở thích, thế mạnh và mục tiêu; các sở thích/ngành được nêu rõ vẫn được tra cứu.
- Ngữ cảnh truy hồi chỉ lấy thực thể/chủ đề/năm nhận diện được từ câu hỏi của người dùng trong tối đa 10 tin nhắn lịch sử, không lấy lời của assistant làm chỉ dẫn. Không lưu trạng thái chat ở máy chủ. Lịch sử gửi cho provider tùy chọn vẫn chịu giới hạn riêng ở phần 4.
- Lọc chủ đề/năm/ngành áp dụng cho cả cosine và dense. Khi dùng LLM để đối chiếu ngành, thiếu trích dẫn cho bất kỳ tài liệu được chọn nào sẽ quay về trích đoạn. Có đủ số trích dẫn vẫn không bảo đảm mọi câu mô hình viết là đúng.

Bản 1.4 đạt **112 tests (79 Python + 33 JavaScript)**, bổ sung 20 kiểm thử hội thoại/truy hồi. Dữ liệu vẫn là bản lưu 27/07/2026; không có dữ liệu mới, kết nối Atlas thật hoặc model OpenRouter thật được xác nhận trong lần cập nhật này.

## 13. Những thay đổi ở bản 1.5

- “Học phí và học bổng HUIT?” có trích đoạn riêng và nguồn cho cả hai phần. Tối đa 3 chủ đề trong nhóm học phí, học bổng, điểm tuyển sinh, xét tuyển, liên hệ. Mỗi chủ đề lấy một bản ghi phù hợp nhất; chưa tổng hợp tất cả các chương trình/chính sách cùng chủ đề. Nếu một phần thiếu dữ liệu hoặc thiếu năm yêu cầu, bot nói rõ thay vì chỉ trả lời phần còn lại. LLM tùy chọn phải trích dẫn đủ nguồn được chọn, nếu không sẽ dùng trích đoạn.
- “Điểm chuẩn CNTT?” → “Còn 2025?” → “2026?” vẫn giữ chủ đề điểm chuẩn và cảnh báo rõ khi kho chỉ có điểm sàn. Đổi sang “điểm sàn” thì bot nhận ý mới. Sửa lỗi nhận diện trường khác trong câu hỏi xét tuyển có nhắc kỳ thi; câu hỏi HUIT nêu trường tổ chức kỳ thi vẫn được tra cứu.
- Khi không nhận diện được tên/mã ngành nêu trực tiếp, bot yêu cầu làm rõ thay vì chọn mã ngành gần tên. Ví dụ “Ngành Y khoa mã ngành là gì?” không còn nhận mã Khoa học dinh dưỡng và ẩm thực. Đây là quy tắc thận trọng: tên rút gọn chưa hỗ trợ cũng có thể cần nhập lại. Tên/mã trong Kho tri thức là cách hỏi ổn định nhất; thêm “Data Science” và “tiếp thị”.
- Nhãn **CẦN LÀM RÕ CÂU HỎI** tách biệt **CHƯA CÓ DỮ LIỆU PHÙ HỢP**, áp dụng cả thanh trạng thái và khung nguồn. Phiên được lưu/khôi phục vẫn giữ đúng nhãn. Câu “Cảm ơn” có phản hồi phù hợp và không làm mất ngữ cảnh câu trước trong giới hạn lịch sử.
- Hỏi “Trường có những ngành nào?” sẽ nhận số ngành thực có trong kho cùng hướng dẫn xem danh sách ở Kho tri thức. Số đếm tính từ mã/định danh ngành, không viết cứng và không được coi là số ngành tuyển sinh hiện hành.

API bổ sung giá trị `mode: clarification`; JSON/NDJSON và bộ đọc phiên đều hỗ trợ. Khi nâng cấp, khởi động lại server rồi tải lại trang để JavaScript và backend cùng phiên bản. Các chế độ cũ tiếp tục hoạt động. Không đổi operation/schema dữ liệu hay nới gate LTX.

Bản 1.5 đạt **132 tests (96 Python + 36 JavaScript)**, thêm 17 bài kiểm tra truy hồi/hội thoại và 3 bài kiểm tra frontend (hợp đồng làm rõ, khôi phục phiên, hủy/thử lại khi phản hồi cũ đến trễ). Quy tắc ngôn ngữ còn hữu hạn, chưa xử lý đầy đủ câu phủ định, tên ngành không đầy đủ, câu ghép phức tạp hoặc mọi tên trường. Dữ liệu tuyển sinh và tình trạng chưa xác nhận provider/Atlas thật vẫn như bản 1.4.

## 14. Những thay đổi ở bản 1.6

- Sửa ý bằng “Không phải CNTT, tôi hỏi Marketing” hoặc “Không phải CNTT mà là Marketing”. Bot bỏ ngành bị bác bỏ, giữ chủ đề/năm đang hỏi nếu bạn chỉ đổi ngành. Ví dụ hỏi học phí CNTT năm 2026 rồi sửa sang Marketing vẫn tra học phí. Dòng ghi chú cho biết bot đã áp dụng ý sửa. Câu chỉ nói “Không phải CNTT” sẽ được hỏi lại nội dung đúng.
- Tương tự, “Tôi hỏi học phí, không phải học bổng”, sửa năm 2025 thành 2026 hoặc sửa Bách Khoa thành HUIT không còn giữ phần bị bác bỏ. Hỗ trợ có dấu, không dấu và Unicode dấu tách. Bộ quy tắc nhận các mệnh đề “không phải”, “không hỏi”, “không muốn hỏi”, phân tách bằng dấu câu hoặc “mà [là/về]”; không phải bộ hiểu mọi cách phủ định. “Không chỉ CNTT mà còn AI” vẫn là hỏi cả hai ngành.
- “So sánh CNTT với Y khoa” yêu cầu làm rõ phần chưa nhận ra, không chỉ trả CNTT rồi coi như đã so sánh đủ. Tên “Luật quốc tế” không bị coi là “Luật”; mã lạ trong câu có mã hợp lệ cũng cần làm rõ. Kiểm tra này tập trung câu nêu ngành/mã ngành hoặc so sánh, chưa bao phủ mọi câu tự do hay lỗi gõ.
- Thêm tên ngắn Logistics và TMĐT/tmdt, chỉ ánh xạ khi ngành tương ứng có trong kho. Tên ngành chính thức chứa “và” được nhận nguyên cụm trước khi kiểm tra các phần còn thiếu. Bộ tên đã chuẩn hóa được cache tối đa 256 mục theo tên/mã; metadata thay đổi tự dùng khóa mới. Không cache hội thoại/câu hỏi hoặc bỏ qua gateway.
- Kho tri thức nhận nhiều từ theo mọi thứ tự, yêu cầu tất cả các từ cùng có trong bản ghi; bỏ dấu và khoảng trắng thừa. Ví dụ nhập “lap trinh cong nghe” hoặc “7480201 cong nghe”. Bộ lọc chủ đề vẫn áp dụng. Đây là tìm chuỗi trong bản ghi, chưa phải tìm đồng nghĩa tự do.
- Tách logic sửa ý và nhận diện ngành thành hai module domain thuần để dễ bảo trì/kiểm thử. Câu hỏi chuyển tới provider tùy chọn có ngữ cảnh đã giải quyết; dữ liệu lịch sử vẫn được coi là nội dung tham khảo, không phải chỉ dẫn hệ thống.

Bản 1.6 đạt **154 tests (115 Python + 39 JavaScript)**. Có kiểm thử tên đầy đủ của cả 39 ngành trong snapshot, cùng ca tên/mã thay đổi để tránh cache cũ. Không đổi operation/lock, dữ liệu tuyển sinh, logo hoặc quyền dữ liệu. Khởi động lại server và mở lại trang khi nâng cấp; xuất hội thoại trước nếu muốn giữ bản lâu dài.
