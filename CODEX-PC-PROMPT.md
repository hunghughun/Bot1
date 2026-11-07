# Prompt tiếp nhận — dán vào Codex local sau khi mở thư mục Bot1

```text
Tiếp tục dự án Bot 1 từ gói bàn giao Codex Cloud trong thư mục hiện tại trên PC.
Đây là phiên làm việc local; hãy xác minh working directory/OS/Python trước khi chạy.

Đọc AGENTS.md, START-HERE-PC.md, docs/PC-HANDOFF.md và Skill
.agents/skills/binance-account-monitor/SKILL.md cùng các reference liên quan.
Không cần giữ đường dẫn cloud /workspace/Bot1; dùng root dự án local.

Trạng thái bàn giao:221 runtime tests PASS trên Linux/Python3.12.14;
Windows/Python3.14 chưa kiểm chứng. Futures Balance V3 mapper đã test offline
theo SDK chính thức pin commit f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179.
Chưa đối chiếu đầy đủ official API docs,0 document-based official API fixtures.
Smoke-test mới là khung offline/SDK candidate, chưa có live client/credential loader.
live_readonly khóa và active network allowlist rỗng.

Công việc tiếp theo:
1. Kiểm tra tính toàn vẹn bằng scripts/verify_handoff.py trước khi sửa file.
2. Kiểm tra interpreter hiện có; trên Windows/Python3.14 thật chạy toàn bộ suite
   bằng scripts/check_compatibility.py với --require-windows --require-python314,
   xuất docs/test-reports/pc-windows314.json và log. Không thay bằng Linux PASS.
3. Truy cập tài liệu Binance chính thức công khai theo policy mạng local hoặc
   đọc HTML/PDF tôi đặt trong docs/vendor/binance. Tập trung Futures Balance V3,
   base URL, USER_DATA, key headers/signing/parameters/weight/schema/timestamps,
   permission và error/rate rules. Lưu URL/ngày/hash và khác biệt với SDK/mapper.
4. Chỉ với bằng chứng đã đọc mới cập nhật golden fixtures/contract tests.
   Mock SDK không được gọi là official API fixture. Không suy đoán trường thiếu.
5. Cập nhật readiness/matrix và báo PASS/FAIL/NOT TESTED/NOT VERIFIED rõ ràng.

Giữ live_readonly khóa. Chưa dùng key thật, chưa gọi Binance authenticated API,
chưa Telegram/VPS. Không yêu cầu key/token trong chat hoặc tự mở live sau test.
Không trade/transfer/withdraw/account settings. Giữ NUMERIC-1/Decimal và core đã đạt;
không cộng snapshot vào cashflow hoặc đổi expected chỉ để PASS.
```
