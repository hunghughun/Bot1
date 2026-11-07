# Bot 1 — hướng dẫn tiếp nhận trên PC

Đây là dự án Bot 1 offline được bàn giao từ Codex Cloud. Bắt đầu bằng
[START-HERE-PC.md](START-HERE-PC.md) và [docs/PC-HANDOFF.md](docs/PC-HANDOFF.md).
Dùng thư mục dự án hiện tại làm root; `/workspace/Bot1` trong báo cáo cũ là
đường dẫn cloud lịch sử, không phải đường dẫn bắt buộc trên PC.

## Skill và trạng thái

- Skill repo-scope: `.agents/skills/binance-account-monitor/SKILL.md`. Đọc Skill
  và các reference liên quan trước khi sửa logic tài chính/API. Nếu app chưa
  liệt kê Skill, đọc file trực tiếp và ghi rõ; không khẳng định đã tự kích hoạt.
- Baseline có221 runtime tests PASS trên Linux/Python3.12.14. Windows/Python3.14
  chưa có bằng chứng thực chạy; phải kiểm tra đúng OS/interpreter trước khi PASS.
- Core offline, NUMERIC-1 và mapper Futures Balance V3 theo SDK đã có test.
  Chưa đối chiếu đầy đủ official API docs. Golden fixture hiện là official SDK
  unit-test mock copy, không phải official API example hoặc dữ liệu thật.
- SDK evidence pin: `f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179`.

## Ranh giới phải giữ

- Giữ `live_readonly` khóa, active network allowlist rỗng. Smoke-test live vẫn
  phải BLOCKED trước credential/network. Không tự mở gate sau unit tests.
- Chỉ giám sát READ-ONLY. Không trade/cancel/modify order, transfer/withdraw hoặc
  thay account settings. Không xin nâng quyền giao dịch để đọc số dư.
- Không yêu cầu API Key/Secret/private key/Telegram Token trong chat. Giai đoạn
  tiếp nhận không dùng key thật, Binance authenticated API, Telegram thật/VPS.
- Giữ Decimal/NUMERIC-1; không float/round/zero-fill dữ liệu tài chính lỗi.
  Snapshot không cashflow/ledger posting; cross PnL không total unrealized.
- Không sửa Skill, core hoặc expected results đã đạt để làm test PASS. Chỉ sửa
  khi có lỗi/khác biệt nguồn được chứng minh và báo cáo thay đổi rõ.
- Dùng checkout hiện tại, không tạo worktree trừ khi người dùng yêu cầu. Gói
  không chứa `.git`; không giả định code đã được commit/push lên repository.

## Công việc tiếp theo

1. Kiểm tra OS/Python hiện có; chạy `scripts/verify_handoff.py` trước khi sửa file.
2. Trên Windows/Python3.14 thật, chạy `scripts/check_compatibility.py` với cả
   `--require-windows --require-python314`; lưu JSON/log mới, không ghi đè
   bằng chứng cloud cũ. Target thiếu là NOT TESTED, không PASS.
3. Đọc nguồn Binance chính thức công khai bằng mạng local được cho phép hoặc
   HTML/PDF trong `docs/vendor/binance/`; lưu URL/ngày/hash. Restriction proxy
   trong báo cáo cloud không chứng minh PC cũng bị chặn; kiểm tra theo policy PC.
4. Chỉ sau khi đọc đủ Balance/base/auth/signing/limits/errors/permissions mới
   cập nhật official fixture/mapping/contract tests. Giữ phần thiếu NOT VERIFIED.
5. Báo PASS/FAIL/NOT TESTED/NOT VERIFIED theo phạm vi thực chạy. Không đề xuất
   truy vấn số dư thật khi còn điều kiện bắt buộc chưa đạt.
