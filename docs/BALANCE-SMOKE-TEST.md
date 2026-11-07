# Futures Balance V3 smoke-test — chuẩn bị offline, live bị chặn

Ngày **07/11/2026 GMT+7**. Chưa có HTML/PDF chính thức trong `docs/vendor/binance/` tại thời điểm kiểm tra. Chính sách mạng restricted/enforced chưa đổi, không cho developers.binance.com; không lặp lại request CONNECT403 đã ghi ở giai đoạn trước. Không có request Binance thật trong giai đoạn này.

## Trạng thái thực tế

`scripts/balance-smoke-test.py` là lệnh riêng; không thêm chức năng vào CLI/core đã đạt. Mặc định không có live client, credential loader, DB hoặc Telegram. Đây là chức năng **chuẩn bị/offline**, chưa là client được phép truy vấn thật.

- Candidate request chỉ GET `https://fapi.binance.com/fapi/v3/balance`; method/base/path không nhận từ CLI. Không cho endpoint khác, query tùy ý, body/action tài chính hoặc redirect. Route candidate đã đọc từ SDK; active network allowlist vẫn rỗng.
- `--live` bắt buộc `--confirm-readonly` và khai báo loại key; sau đó luôn bị chặn bởi `require_verified(futures_balance_v3)`. Cờ xác nhận không chứng minh quyền key và không vượt được cổng tài liệu. Chưa có đường đọc credential hoặc khởi tạo HTTP client.
- Signing HMAC candidate là hàm thuần offline dựa trên common-utils của SDK đã pin, không dựa vào trí nhớ. Truyền API key qua `X-MBX-APIKEY`, tạo query recvWindow/timestamp, HMAC-SHA256 hex. Đã kiểm tra với oracle OpenSSL độc lập bằng key giả; đây **không phải** xác minh signing theo tài liệu API hiện hành hoặc key thật. RSA/Ed25519/unknown dừng, không fallback HMAC. Không suy đoán loại key thực tế.
- Local candidate recvWindow1..5000ms, timestamp nguyên ms; trần này là policy kỹ thuật nội bộ, không tuyên bố là giới hạn Binance. Không đổi NUMERIC-1, không đưa tiền qua float.
- Offline fake exchange nhận timeout1..30000ms và response cap1MiB; mỗi harness chỉ một attempt, kể cả lỗi. 401/403 dừng, không nâng quyền; 418/429 dừng, không retry; 3xx/5xx/lỗi transport dừng. Không polling, không retry tự động. Đây là test propagation/hard-stop trên fake, **chưa chứng minh timeout/quota/cooldown liên tiến trình trên client mạng thật**.
- Secret/signature/body không có trong repr; CLI chỉ in count/status/code, không alias/amount, không dump exception hoặc tham số bị argparse từ chối. Không nhận secret trên command line. HMAC function chỉ được dùng với dữ liệu tổng hợp trong giai đoạn này; CLI không gọi signer thật.

## Chạy được ngay, không mạng

Tại thư mục dự án:

```sh
python scripts/balance-smoke-test.py --plan
python scripts/balance-smoke-test.py --offline-fixture tests/fixtures/binance_sdk/balance_v3_response.json --account offline-test-account --expected-account-alias SgsR --poll-id smoke-001 --received-time 2026-11-06T18:00:00Z
python scripts/run_adapter_tests.py
```

`--plan` exit0 chỉ xác nhận tạo kế hoạch; fixture command exit0/PASS là **OFFLINE_SDK_PROFILE_ONLY**. Fixture này là mock SDK chính thức được sao chép có hash/commit; không phải official API golden fixture hoặc số dư thật. CLI không in giá trị tài chính và không ghi database nào.

Không chạy với key thật. Các kiểm thử automated đã gọi `--live` với và không có cờ xác nhận: exit2/BLOCKED,0 request và không đọc credential. Chưa có lệnh live có thể thành công; việc thêm file vendor hoặc đổi cờ cấu hình không mở gate.

## Schema và khác biệt với mapper

Mapper cũ giữ nguyên profile SDK: yêu cầu accountAlias/asset/balance/availableBalance/updateTime; bốn field còn lại Optional theo annotation SDK. Smoke inspection yêu cầu đủ cả9 field, không null, để báo kiểm tra hoàn chỉnh: asset, balance, availableBalance, crossWalletBalance, crossUnPnl, maxWithdrawAmount, marginAvailable, updateTime và accountAlias. Đây là policy local chặt hơn SDK, **chưa phải required-fields của API đã được xác minh**. Chưa có tài liệu chính thức để kết luận khác biệt mapper/API.

Năm trường tiền được validate trực tiếp từ string bằng Decimal/NUMERIC-1, giữ trị nguồn. Asset/bool/integer-ms không bị coi là tiền. Cross PnL chỉ cross; không cộng snapshot, không suy margin/total unrealized, không chuyển delta thành deposit/withdrawal. Optional bị thiếu/null không thay0. Unknown field, duplicate key/asset, malformed JSON, numeric ngoài bound hoặc sai account binding dừng an toàn.

29 tests mới thực thi được: signing candidate/route/confirmation, input/redaction, fake timeout/one-attempt/error stop, mọi field tài chính, precision/nonfinite/type/missing/unknown/duplicate và stateless replay. 39 Balance contract/reliability tests trước đó vẫn chạy, gồm local snapshot replay và process crash trước/sau commit. Không gọi các test này là official API contract tests hoặc Windows tests.

## Cổng bắt buộc còn thiếu

1. Tài liệu Balance/base/auth/signing/parameters/quota/errors và permission ở [vendor intake](vendor/binance/README.md); hash/source URL/ngày và đối chiếu từng trường. Chưa có official API golden fixture để tạo.
2. Xác minh loại key dự kiến và cách kiểm chứng quyền read-only phù hợp; không chỉ dùng operator checkbox hoặc một GET thành công để khẳng định key không có quyền thừa. Không đề nghị bật trading/withdrawal/transfer.
3. Review/triển khai live credential provider, signer cho đúng key type, TLS/proxy/no-redirect/timeout/response cap/clock, quota/cooldown liên tiến trình và safe errors sau khi có tài liệu. Không thêm route time/permissions khác vào smoke-test chỉ cho phép một endpoint này; clock phải được chuẩn bị ở OS theo quy trình được review.
4. Chạy regression, official positive/negative fixture tests và Windows/Python3.14 thực; kiểm tra local secret storage/permissions trên Windows. Kết quả Linux không chứng minh Windows PASS.
5. Chỉ sau khi mọi điều kiện bắt buộc đạt mới review cho phép người vận hành chạy một lần bằng key read-only trực tiếp trên máy, có xác nhận tường minh; không ghi ledger nghiệp vụ hoặc Telegram.

**Hiện chưa đề xuất mở thử số dư thật.** Điểm chặn chính là thiếu tài liệu vendor, granular key permissions/signing chính thức, live transport/rate-control và Windows execution. Chi tiết [readiness](BINANCE-ADAPTER-READINESS.md) và [review JSON](test-reports/balance-official-doc-review.json).
