# Kết quả kiểm tra Mambot

Ngày cập nhật: 22/09/2026. Môi trường đã chạy: Windows, Python 3.12, Node.js; FastAPI TestClient + trình duyệt Codex. Các thư viện runtime kiểm thử được khóa trong requirements.lock.txt.

## Đã kiểm tra

- Architecture gate: frontend dependency direction, vị trí transport/endpoint/DOM, backend imports và Mongo reach-through.
- 178 tests Python: API/health/library/assets, DTO, origin, payload cap, rate limit, không lộ file riêng; cosine, alias tiếng Việt, dữ liệu tuyển sinh nguyên đoạn, câu hỏi ngoài phạm vi/năm không có; provider fallback; operation checksum/status/type/version binding, collection/cost/schema/finite vector/output/audit và fail-closed. Thêm mount `/portal/mambot/`, redirect, cache, quota chung đường dẫn mới/cũ, health kho rỗng, đồng thời, local reload, provider response và các kiểm thử hội thoại/truy hồi ở phần 1.4–1.9 bên dưới.
- 53 tests JavaScript: lifecycle/history, duplicate send, abort/stale response, reset race, lỗi kết nối, history cap, tìm không dấu, UTF-8/NDJSON bị chia byte và stream chưa hoàn tất. Thêm lưu/khôi phục/xóa/hết hạn phiên, hỏng schema/JSON, chặn storage/hết quota, giới hạn UTF-8 theo cặp, xuất văn bản, health contract, endpoint tương đối, null error payload, Retry-After, malformed UTF-8, cleanup bị treo, clarification, chuỗi hủy/thử lại, tìm nhiều từ, bộ lọc trong lúc tải, bản nháp, metadata phiên, gộp cập nhật tiến trình và năm/ngày nguồn khi xuất TXT.
- Trình duyệt thực: gợi ý câu hỏi ngành AI → câu trả lời và link nguồn; tìm “cong nghe thong tin” → 1/45 bản ghi; trang LTX trả trạng thái thực; xác nhận tạo hội thoại mới; kiểm tra responsive desktop và điện thoại.
- Nội dung không được render bằng innerHTML; frontend không chứa credentials hoặc Mongo implementation.

## Bản 1.10 — hỗ trợ sinh viên và hội thoại

- 28 tests Python mới: chào hỏi có tên/punctuation/không dấu, câu chào kèm học phí không mất ý chính, identity, ngữ cảnh học tập, giới hạn thời gian/giá trị âm, kế hoạch một ngày và ngày ôn cuối, chuyển lại về ngành/học phí, chặn kế thừa qua chủ đề khác hoặc từ lời assistant, email theo mục đích, hướng dẫn cơ bản, câu hỏi dữ liệu riêng/quy định, hướng nghiệp, hỗ trợ khi người dùng diễn đạt nguy cơ tự hại.
- Kiểm tra fallback khi provider lỗi hoặc trả citation/URL/quy định ngoài evidence, prompt hỗ trợ và lịch sử/budget có giới hạn bằng MockTransport, stream mode mới. Tên tất cả ngành trong kho được chạy qua các tests hồi quy; sửa nhầm “điện tử học” thành “tự học” và “Du lịch học” thành “lịch học”.
- 3 tests JavaScript mới: hai mode support/conversation đi qua stream, xuất không sinh nguồn giả, giữ mode/ngữ cảnh sau khôi phục phiên, vẫn từ chối mode lạ.
- Browser QA: chào Mambot → gợi ý lịch học → Giải tích 7 ngày/2 giờ → bật giữ phiên → tải lại → còn 3 ngày → học phí HUIT có nguồn đúng năm → email giảng viên → gia hạn nộp bài. Focus giữ ở ô nhập sau Enter; bảng nguồn phân biệt hướng dẫn với trích đoạn; không ghi nhận console error.
- Màn hình điện thoại 390 × 844: thẻ gợi ý, nút gửi, lịch 3 ngày/90 phút, nút đổi chủ đề và ghi chú đọc được; không tràn ngang. Đã kiểm tra ảnh desktop và điện thoại; viewport được trả về mặc định.

Tổng **231 tests (178 Python + 53 JavaScript)** cùng architecture gate. ZIP được kiểm tra lại từ thư mục giải nén. Registry/lock, dữ liệu/provenance, logo, AGENTS.md và architecture checker được đối chiếu nguyên byte với 1.9. Các test provider dùng giả lập, không chứng minh chất lượng model thật. Tham khảo và giới hạn mới ở [STUDENT_SUPPORT.md](STUDENT_SUPPORT.md).

Chạy lại bằng `python scripts/verify.py`. Kết quả xanh là kiểm tra code/hợp đồng, không phải xác minh độ chính xác tuyển sinh trên website HUIT.

## Chưa xác nhận trong môi trường thật

- Atlas kết nối thật, index E5 và chất lượng RRF/dense trên kho sản xuất.
- API/model OpenRouter thật, chi phí và chất lượng câu trả lời sinh.
- Docker build và reverse proxy/TLS trên máy chủ; chưa có URL công khai.
- GitHub Actions/branch protection trên repo thật: chỉ cung cấp cấu hình, chưa tạo repo.
- Khả năng chịu tải nhiều worker, xác thực người dùng, lưu bền hội thoại hoặc đồng bộ dữ liệu mới.

Mambot là web con chat/tri thức mới; chưa thay toàn bộ admin/image/crawler/mutation APIs của chatbot2. Bản local chỉ có quyền đọc dữ liệu. LTX gates và schema giảm lỗi kiến trúc phổ biến; không thay thế review con người hoặc bảo đảm LLM không bịa.

## Bản 1.1 — cải tiến độ ổn định và nhận diện HUIT

- Màu xanh HUIT #0b5598, trắng, điểm nhấn đỏ; logo JPG do người dùng cung cấp đặt phía trên tên Mambot. Không thay đổi nội dung logo.
- ASGI middleware đọc body có giới hạn dung lượng và deadline 10 giây; xử lý body chia chunk, mất kết nối, Content-Length lỗi. Không dùng thuộc tính private Request._body.
- JSON lỗi an toàn, X-Request-ID liên kết phản hồi với audit; lỗi bất ngờ không đưa nội dung exception ra giao diện.
- Frontend timeout 15 giây cho dữ liệu/45 giây cho chat, kiểm tra MIME và thứ tự NDJSON; chặn stream lỗi/trống/quá dài.
- Nút thử lại, giữ ngữ cảnh chỉ từ lượt thành công, giảm history về 32.000 byte, không cắt đôi emoji.
- Không mất đăng ký trạng thái khi trang được khôi phục từ bộ nhớ Back/Forward của trình duyệt.
- Loại URL lỗi trước truy hồi, ưu tiên năm/chủ đề mới của câu hỏi tiếp nối; giữ nhiều đoạn khác nhau cùng một URL khi kết hợp kết quả.
- Mongo client khởi tạo có khóa, đóng cursor/client đúng vòng đời, giới hạn dung lượng khi đọc; hỗ trợ retrieved_at kiểu BSON datetime. Các nhánh này kiểm tra bằng mock, chưa xác nhận Atlas thật.
- Giữ nguyên byte của hai operation authority đã phát hành; không nới schema/checksum để vượt test.

Tối ưu: cache tối đa 4 chỉ mục TF–IDF theo nội dung kho tri thức, tái tính khi nội dung đổi. Không cache câu hỏi hoặc hội thoại. Có test chống dùng chỉ mục cũ sau khi thay dữ liệu.

## Bản 1.2 — web con, phiên chat và trải nghiệm

- Browser QA mới: hỏi ngành AI → câu trả lời + nguồn; bật giữ phiên → reload khôi phục 2 tin nhắn; hỏi năm 2035 → nhãn chưa có dữ liệu phù hợp; tìm không dấu → 1/45 bản ghi; tạo mới từ trang khác → focus đúng; xác nhận xóa hội thoại → số tin nhắn về 0, bản nháp trống. Logo tải ảnh gốc rộng 447 px, hiển thị CSS 42 px trên mobile. DOM ở chiều rộng thực 375 px không tràn ngang.
- Nội dung TXT có nguồn và nhãn lượt chưa hoàn tất được kiểm tra tự động. Trình duyệt nhúng không báo sự kiện download khi bấm nút; chưa xác nhận file tải về qua UI trên Chrome/Edge thật.
- Endpoint mới/cũ vẫn dùng cùng middleware và quota, kể cả khi mount dưới prefix ngoài. Điều này được kiểm tra bằng TestClient; chưa thay thế kiểm tra reverse proxy/TLS thật.
- DOM dùng ID tin nhắn ổn định, không dựng lại lịch sử mỗi chunk. Chưa có benchmark tải lớn hoặc đo cải thiện tốc độ trên máy chủ sản xuất.
- SessionStorage mặc định tắt, tối đa 256 KiB/100 tin nhắn/8 giờ, chỉ nằm trong phiên trình duyệt. Đây không phải lưu bền tài khoản. Các hội thoại lỗi/dừng không được khôi phục thành ngữ cảnh đã hoàn tất.
- Authority và registry lock được so sánh từng byte với ZIP 1.1 trước đóng gói. Giữ nguyên logo gốc. Không có provider/Atlas thật hoặc dữ liệu tuyển sinh mới được kiểm chứng trong bản này.

## Bản 1.3 — lỗi phản hồi, quá tải và dữ liệu local

Đã tái hiện lỗi bằng test trước khi sửa: dữ liệu local thay đổi nhưng vẫn trả bản cache cũ; file đã chuyển đi vẫn được phục vụ từ cache; phản hồi 503 dạng JSON null mất status/request ID; UTF-8 lỗi bị báo thành mất mạng. Kiểm thử sau sửa xác nhận phục hồi sau khi sửa lại file hợp lệ và không đọc dữ liệu quá giới hạn vào JSON decoder.

Kiểm thử ASGI giữ một chat đang chạy, gửi chat khác qua alias còn lại và nhận 503/Retry-After; health vẫn trả 200, chat tiếp theo dùng được sau khi slot giải phóng. Kiểm tra slot cũng được giải phóng sau exception. Đây là kiểm thử concurrency có kiểm soát, không phải benchmark tải lớn.

MockTransport kiểm tra phản hồi provider hoàn tất, cắt ngắn, bị lọc, rỗng, sai schema/MIME/encoding, quá dung lượng, quá ngân sách thời gian, lỗi HTTP và đóng stream. Câu trả lời bị cắt giữa chừng chuyển về trích đoạn đầy đủ có nguồn. Không cần khóa thật và không phát sinh gọi AI từ bộ test.

Frontend xác nhận phản hồi quá lớn vẫn kết thúc khi thao tác hủy underlying stream không bao giờ hoàn tất. Cả **92 tests** và architecture gate đạt. Giữ nguyên từng byte các authority/lock so với ZIP 1.2; dữ liệu tuyển sinh và logo không đổi.

Browser QA 1.3: trang hiển thị V.1.3 và 45 tài liệu; câu hỏi “Mã ngành CNTT là gì?” trả 7480201 cùng link nguồn; bật giữ phiên và reload khôi phục hội thoại. Không ghi nhận console error trong luồng này. Màu sắc/bố cục tiếp tục dùng nhận diện HUIT của bản trước.

## Bản 1.4 — ngữ cảnh hội thoại và chọn bằng chứng

Đã tái hiện và sửa mất ngành ở câu tiếp nối thứ ba, không nhận câu ngắn chuyển sang Marketing, so sánh hai ngành chỉ xuất một trích đoạn và lấy học phí HUIT trả lời câu hỏi về Bách Khoa. Loại alias hướng nữ giới sang ngành thời trang/dệt may; hỏi thêm sở thích khi chỉ có thông tin giới tính. Phân loại intent theo ranh giới từ để “học phim” không bị nhận nhầm thành “học phí”.

20 tests mới kiểm tra ba lượt tiếp nối, chuyển ngành, mã/tên viết tắt, tên ngành chồng lấn, phân biệt AI với đại từ, đủ nguồn và thứ tự so sánh, hỏi lại khi mơ hồ, năm thiếu, lịch sử assistant không làm thay đổi thực thể, giới tính/sở thích, phạm vi trường, kỳ thi do trường khác tổ chức, điểm chuẩn khác điểm sàn, lọc dense đúng chủ đề, chủ đề không có dữ liệu, nhãn thông tin mới nhất, ranh giới từ và fallback khi câu trả lời sinh thiếu nguồn so sánh.

Tổng **112 tests (79 Python + 33 JavaScript)** và architecture gate đạt. Quy tắc nhận diện tên/ngữ cảnh có phạm vi hữu hạn, chưa được đánh giá trên tập hội thoại người dùng thực tế. Không có benchmark độ chính xác tuyển sinh hoặc cam kết loại bỏ mọi lỗi. Dữ liệu, logo, authority/lock và các gate được giữ nguyên so với bản 1.3.

Browser QA 1.4 sau khi xác nhận health trả version 1.4.0: “CNTT học gì?” → “Ngành này ra trường làm gì?” → “Mã ngành đó?” giữ đúng Công nghệ thông tin/7480201; “Còn Marketing thì sao?” đổi sang Marketing/7340115. So sánh CNTT và Trí tuệ nhân tạo hiển thị cả hai trích đoạn, hai link nguồn; “Ngành đó học bao lâu?” yêu cầu chọn rõ một ngành. Không ghi nhận console error trong luồng sáu câu hỏi này. Giao diện tiếp tục dùng màu xanh HUIT và logo gốc.

## Bản 1.5 — không bỏ sót chủ đề và không thay ngành gần tên

Đã tái hiện trên bản 1.4: câu hỏi chỉ có năm sau khi hỏi điểm chuẩn làm mất cảnh báo hoặc trả mô tả ngành; câu hỏi Y khoa nhận mã Dinh dưỡng; học phí + học bổng chỉ trả học bổng; câu hỏi Bách Khoa có cụm kỳ thi bị trả thông tin HUIT; lời cảm ơn làm mất chủ đề; hỏi số/danh sách ngành trả không tìm thấy.

17 tests mới kiểm tra các trường hợp trên, đổi rõ điểm chuẩn sang điểm sàn, tên/mã ngành lạ trong câu tiếp nối, alias được hỗ trợ, phân biệt trường đích với trường tổ chức thi, thứ tự nguồn theo từng chủ đề, cụm từ chồng lấn, phần/năm thiếu, điểm chuẩn trong câu nhiều chủ đề, LLM thiếu nguồn và số ngành tính từ kho. 3 tests frontend xác nhận clarification qua stream và khôi phục phiên, từ chối mode lạ và hủy → thử lại không bị lượt cũ ghi đè. Tổng **132 tests (96 Python + 36 JavaScript)** và architecture gate đạt.

Các thay đổi áp dụng quy tắc xác định, không bảo đảm hiểu mọi câu phủ định/câu ghép hoặc nhận diện mọi tên trường/ngành. Chọn bằng chứng cho nhiều chủ đề không đồng nghĩa đã tổng hợp mọi bản ghi cùng chủ đề. Không có dữ liệu tuyển sinh mới, provider/Atlas thật hay đo tải sản xuất trong bản này.

Browser QA 1.5: health xác nhận version 1.5.0/45 tài liệu. Câu hỏi Y khoa hiển thị CẦN LÀM RÕ CÂU HỎI, không có nguồn/mã ngành thay thế; bật lưu phiên rồi reload giữ đúng nội dung và nhãn. Học phí + học bổng có hai trích đoạn, hai link nguồn. “Điểm chuẩn CNTT?” → “2026?” giữ cảnh báo điểm sàn ở đầu câu trả lời. Không ghi nhận console error trong luồng kiểm tra này; đã tắt lưu phiên của tab thử nghiệm sau kiểm tra.

## Bản 1.6 — sửa ý, nhận diện đủ ngành và tìm kiếm trong kho

Trước sửa, 11/15 bài kiểm tra đầu tiên cho các tình huống mới thất bại: giữ ngành/chủ đề bị bác bỏ, giữ năm sai, không thoát phạm vi trường cũ, trả một phần so sánh khi ngành còn lại chưa biết, nhận “Luật quốc tế” thành “Luật”, không nhận Logistics viết ngắn. Các ca này đã đạt sau sửa. Hai kiểm thử cũ phát hiện năm bị nhận nhầm là phần tên ngành; đã sửa bộ nhận diện, giữ nguyên kỳ vọng kiểm thử cũ.

Bổ sung tổng 19 tests Python, gồm các ca sửa ý, không dấu/dấu tách, không nhầm “không chỉ” với bác bỏ, mã lạ, tên chứa “và”, toàn bộ 39 tên ngành và làm mới cache khi đổi metadata. Ba tests JavaScript kiểm tra khoảng trắng/Unicode, nhiều từ kết hợp bộ lọc, và không nhận kết quả cũ khi người dùng đã lọc trong lúc tải. Tổng **154 tests (115 Python + 39 JavaScript)** cùng architecture gate đạt.

Cache chỉ chứa bộ tên/mã đã chuẩn hóa, tối đa 256 khóa. Chưa đo hiệu năng sản xuất. Nhận diện sửa ý/ngành vẫn theo quy tắc hữu hạn; không cam kết hiểu mọi câu ghép, phủ định nhiều lớp hay cách viết tắt. Dữ liệu snapshot và trạng thái chưa kiểm thử provider/Atlas thật không đổi.

Browser QA 1.6: health trả version 1.6.0 và 45 tài liệu. Học phí CNTT năm 2026 → sửa sang Marketing vẫn trả trích đoạn học phí cùng ghi chú đã áp dụng ý sửa; “Mã ngành đó?” trả Marketing/7340115. “So sánh CNTT và Y khoa” hiển thị cần làm rõ, không có nguồn thay thế. Trong Kho tri thức, tìm “  7480201   cong nghe  ” với bộ lọc Ngành học trả 1/45 bản ghi đúng CNTT; không ghi nhận console error trên tab kiểm tra tìm kiếm. Tab thử hội thoại bị công cụ trình duyệt đóng sau khi kiểm tra, phần thư viện được xác nhận ở tab mới.

## Bản 1.7 — câu hỏi tham chiếu và bảo toàn phiên

Đã tái hiện lỗi ở “cả hai ngành đó”, “ngành thứ hai” và câu đáp ngắn sau yêu cầu làm rõ làm mất chủ đề/năm. Bổ sung 15 tests Python: chọn theo thứ tự người hỏi, tham chiếu không có ngữ cảnh/vượt số ngành, giữ chủ đề/năm khi chọn ngành, chuyển chủ đề rõ ràng, lời cảm ơn, ngắt ngữ cảnh cũ, không nhầm hai chủ đề thành hai ngành, số lượng không khớp và giữ phạm vi trường khác. Quy tắc tham chiếu dùng danh sách ngành đang có trong tối đa 10 tin nhắn lịch sử; không phải bộ nhớ hội thoại vô hạn.

Đã tái hiện trên trình duyệt việc tạo mới xóa bản nháp khi chưa gửi câu nào. Hộp thoại xác nhận nay áp dụng cả trường hợp này. API dùng chung quy tắc kiểm định nguồn/metadata cho stream và phiên lưu, giữ trường year/data_mode thay vì bỏ khi khôi phục. Năm thiếu hoặc null vẫn tương thích phiên cũ. Năm phải là số nguyên an toàn; không thêm phạm vi năm tuyển sinh giả định. Năm/source metadata lỗi không được coi là câu trả lời hoàn tất.

5 tests JavaScript mới kiểm tra metadata sai, giới hạn nguồn/năm, khôi phục và xuất JSON, giữ lượt cũ khi lượt mới lỗi và điều kiện bảo vệ bản nháp. Tổng **174 tests (130 Python + 44 JavaScript)** cùng architecture gate đạt. Khi đóng gói, chạy lại toàn bộ từ thư mục giải nén ZIP; đối chiếu dữ liệu, logo, registry/lock và gate với bản 1.6.

Browser QA 1.7: health trả version 1.7.0/45 tài liệu. “Giữ lại” giữ nguyên bản nháp; xác nhận “Bắt đầu mới” xóa bản nháp. So sánh CNTT và Marketing → “Cả hai ngành đó học gì?” có đủ hai mã/ngành và hai link nguồn; “Ngành thứ hai học gì?” chỉ trả Marketing/7340115. “Học phí ngành Y khoa năm 2025?” → “Marketing” giữ học phí/năm 2025 và báo thiếu dữ liệu. Bật lưu phiên rồi tải lại giữ đúng câu trả lời và nhãn thiếu dữ liệu; không ghi nhận console error trong luồng này. Bản nháp chưa gửi vẫn không được lưu khi tải lại trang. Không thay đổi snapshot, chưa kiểm thử provider/Atlas thật.

## Bản 1.8 — giữ chủ đề khi đổi năm và giảm cập nhật giao diện

6/8 tests Python đầu tiên của đợt này tái hiện lỗi trên 1.7: tham chiếu ngành kèm năm làm mất chủ đề, chọn ngành kèm năm sau làm rõ bị xem là câu mới, mất cảnh báo điểm chuẩn và so sánh chỉ trả ngành còn dữ liệu sau lọc năm. Bổ sung một test cho “cả hai ngành đó/ấy/này” không kèm năm sau khi phát hiện lỗi khoảng trắng trong mẫu nhận diện. Tổng 9 tests mới đều đạt; hai ca so sánh thiếu dữ liệu dùng bản ghi giả lập nhiều năm, không sửa snapshot bàn giao.

Controller cập nhật trạng thái ngay nhưng gộp thông báo tiến trình trong cùng một lượt xử lý; các hành động dừng/reset/kết thúc vẫn thông báo ngay và vô hiệu hóa thông báo cũ đang chờ. Với bài kiểm tra 256 token liên tiếp, số snapshot gửi giao diện giảm từ 260 xuống 4, giữ đủ 3.218 ký tự. Đây là phép đo số lần cập nhật với dữ liệu giả lập, không phải benchmark tốc độ mạng/LLM hay bảo đảm nhanh hơn trên mọi thiết bị. 4 tests mới kiểm tra gộp tiến trình, dừng giữ đủ đoạn cuối, reset không nhận cập nhật cũ, lỗi giữ văn bản dở dang nhưng không đưa vào lịch sử thành công.

Tổng **187 tests (139 Python + 48 JavaScript)** và architecture gate đạt. Gói ZIP được kiểm thử lại sau giải nén; dữ liệu, logo, registry/lock, AGENTS.md và architecture checker được đối chiếu nguyên byte với 1.7.

Browser QA 1.8, trên tab riêng:

1. Trên 1.7, nhập bản nháp “Học phí ngành Marketing năm 2025?” rồi bấm gợi ý AI: bản nháp bị xóa. Sau sửa, bản nháp và bộ đếm 33/800 giữ nguyên trong khi câu trả lời AI hiển thị đầy đủ.
2. Gửi bản nháp được giữ: có đúng một lượt hỏi mới, bot báo thiếu học phí 2025, ô nhập trống và bộ đếm về 0/800.
3. Học phí CNTT và Marketing năm 2026 → “Ngành thứ hai năm 2025?”: giữ chủ đề học phí, báo thiếu năm 2025.
4. Điểm chuẩn CNTT và Marketing năm 2025 → “Ngành thứ hai năm 2026?”: cảnh báo chỉ có điểm sàn vẫn nằm đầu câu trả lời. Không ghi nhận console error trong luồng này.

Các quy tắc ngôn ngữ vẫn hữu hạn; dữ liệu tuyển sinh chưa cập nhật/đối chiếu trực tuyến. Không có kiểm thử provider, Atlas hay tải sản xuất thật trong bản này.

## Bản 1.9 — đủ nguồn theo năm và thao tác bàn phím

8/9 ca Python đầu tiên của đợt này thất bại trên 1.8: thứ tự nguồn nhiều năm không ổn định, bỏ năm thứ ba, chọn một bản ghi ngành cho hai năm, chấp nhận AI chỉ trích một năm, không yêu cầu chia câu hỏi quá nhiều phần, mất nguồn điểm sàn của năm khác và bỏ nguồn điểm chuẩn nằm ngoài top 3. Tất cả dùng dữ liệu thử nghiệm riêng; snapshot bàn giao không được sửa.

Truy hồi nhận bộ năm đã xác định từ service; mỗi phần năm có nguồn riêng. Khi hỏi điểm chuẩn, nguồn điểm chuẩn/điểm trúng tuyển được ưu tiên theo từng năm trước giới hạn xếp hạng; các năm chỉ có điểm sàn vẫn được giữ và cảnh báo rõ. Câu nhiều năm phải có đủ trích dẫn hoặc fallback về trích đoạn. Tối đa 3 phần ngành/chủ đề–năm, không tăng giới hạn authority hoặc số nguồn của truy hồi. Không khẳng định một trích đoạn đã bao quát mọi bản ghi cùng chủ đề/năm.

Tổng 11 tests Python mới gồm 9 ca ban đầu, nguồn điểm sàn chưa rõ năm và kiểm tra payload provider có năm riêng cho từng nguồn. Provider được kiểm tra bằng MockTransport, không gọi dịch vụ thật. Hai tests JavaScript mới xác nhận TXT giữ năm/ngày sau khôi phục phiên và không tự gán năm cho nguồn cũ/null. Tổng **200 tests (150 Python + 50 JavaScript)** cùng architecture gate đạt; chạy lại từ ZIP giải nén trước bàn giao.

Browser QA 1.9: trên 1.8, gửi Enter làm focus chuyển về BODY. Sau sửa, focus ở TEXTAREA/question và readOnly=false khi trả lời xong; gõ “Còn năm 2025?” và Enter trực tiếp, không chọn lại ô nhập, gửi thành công. Thẻ học phí ghi “NĂM 2026 · BẢN LƯU 2026-07-27”. Câu hỏi học phí 2025 và 2026 vẫn báo thiếu dữ liệu 2025 trên snapshot thật; không dùng dữ liệu giả lập lên giao diện. Không ghi nhận console error trong luồng này.

Dữ liệu, logo, registry/lock, AGENTS.md và architecture checker được đối chiếu nguyên byte với 1.8. Chưa xác minh dữ liệu tuyển sinh hiện hành, Atlas, provider thật hoặc triển khai công khai.

## Tái bản Mambot 1 — bộ khởi chạy Windows

Tên phát hành theo yêu cầu: Mambot 1.zip, thư mục Mambot 1, phiên bản ứng dụng 1.0.0; không phải 1.11. Kế thừa chức năng bản 1.10. Môi trường Python 3.12 Windows x64 và các thư viện đã khóa được đóng gói sẵn, giữ license. Không kèm site-packages của người dùng, .venv, khóa, log hoặc lịch sử chat.

10 tests khởi chạy mới kiểm tra giải nén thiếu file, Python cũ, lỗi dependency, PORT sai/bận, tự chọn cổng khi mặc định bận, giữ socket tránh tranh cổng, check authority và chỉ mở trình duyệt sau khi health sẵn sàng. Kiểm thử frontend đường dẫn được sửa để so sánh toàn bộ đường dẫn gốc của ứng dụng thay vì giả định tên thư mục luôn là mambot.

Gói ZIP được kiểm tra CRC và giải nén vào đường dẫn có dấu/khoảng trắng. START_MAMBOT.cmd --check được chạy từ thư mục làm việc khác, với PYTHONHOME và PYTHONPATH giả lập sai để xác nhận runtime độc lập. Chạy toàn bộ 241 tests (188 Python + 53 JavaScript) từ bản đã giải nén và giữ nguyên architecture gate/authority. Đây là bản Windows x64; macOS/Linux dùng mã nguồn, không dùng runtime Windows.

