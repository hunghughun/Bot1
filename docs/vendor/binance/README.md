# Chờ bản tài liệu Binance chính thức

Ngày kiểm tra: **07/11/2026 GMT+7**. Khi bắt đầu giai đoạn này, thư mục này chưa tồn tại và không tìm thấy HTML/PDF Binance trong workspace. README này là hướng dẫn tiếp nhận do dự án tạo, **không phải tài liệu Binance và không mở cổng live**.

Cần cung cấp bản HTML có nội dung đầy đủ hoặc PDF xuất từ trình duyệt:

1. `futures-balance-v3.html` hoặc `.pdf`: mục **Futures Account Balance V3**, bao gồm method/path, request weight, parameters, toàn bộ response example và chú thích từng trường. URL nguồn: <https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/account#futures-account-balance-v3>.
2. `futures-general-info.html` hoặc `.pdf`: base URL, time unit, request/error/timeout/rate-limit rules. Entry URL được SDK chính thức trỏ tới: <https://developers.binance.com/docs/derivatives/usds-margined-futures/general-info>.
3. `futures-security-signing.html` hoặc `.pdf`: security USER_DATA, API-key header, signing và canonical encoding, timestamp/recvWindow; phần cho từng loại key HMAC/RSA/Ed25519 thực sự được hỗ trợ. Tải các trang được dẫn từ general-info; URL trang con chưa xác minh, không tự tạo URL.
4. `futures-errors-rate-limits.html` hoặc `.pdf`: HTTP/error-code handling, response quota headers, 429/418 và retry/cooldown. Nếu đã đầy đủ trong general-info, không cần bản trùng.
5. `readonly-key-permissions.html` hoặc `.pdf`: tài liệu quyền đọc cho Futures Balance với loại tài khoản/key tương ứng, không yêu cầu bật trading/withdrawal/transfer. Chưa có URL trang con được xác minh; giữ URL gốc của trang thực sự tải được.
6. Changelog/deprecation liên quan Balance V3 và signing, nếu các trang trên có dẫn tới thông báo thay đổi.

Kèm `sources.json` ghi cho mỗi tài liệu: file, source_url đầy đủ, thời điểm tải có timezone, title và cách xuất HTML/PDF. Đây là metadata do người cung cấp khai báo; Codex vẫn phải đọc/review và hash nội dung. File HTML chỉ có app shell hoặc PDF thiếu response/signing không đủ chứng cứ. Không chỉ đổi tên fixture SDK thành official API fixture.

Chỉ tài liệu công khai; không gửi API Key, Secret, private key, token, signed request, ảnh tài khoản hoặc số dư thật. Credential tương lai chỉ được cung cấp trực tiếp trên máy người vận hành sau khi các cổng review đạt. Việc xuất hiện file/metadata không tự bật live hoặc xác nhận provenance.

Hiện trạng và các mục bị chặn: [BALANCE-SMOKE-TEST.md](../../BALANCE-SMOKE-TEST.md), [official review](../../test-reports/balance-official-doc-review.json).
