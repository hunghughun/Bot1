# Mở Bot 1 trong Codex trên PC

Gói này bàn giao **mã nguồn và ngữ cảnh dự án**. Nó không đổi nơi thực thi của
phiên chat cloud hiện tại và không tự chuyển toàn bộ lịch sử chat vào phiên mới.

1. Giải nén ZIP vào thư mục mới, ví dụ `C:\Projects\Bot1`. Mở đúng thư mục có
   file này, `AGENTS.md`, `src`, `tests` và `.agents` trong Codex trên PC, rồi
   dùng phiên làm việc local để Codex đọc/ghi file và chạy lệnh trên PC.
2. Mở [CODEX-PC-PROMPT.md](CODEX-PC-PROMPT.md), sao chép nội dung khối prompt và
   gửi trong phiên Codex local. Codex sẽ có `AGENTS.md`, Skill và tài liệu bàn giao
   để tiếp tục. Không cần dán lại toàn bộ lịch sử chat cloud.
3. Dùng CPython3.14 đã cài nếu mục tiêu là nghiệm thu Windows. Runtime dự án chỉ
   dùng thư viện chuẩn; không cần pip/install SDK, Telegram hoặc Docker.

Trong PowerShell tại root dự án, sửa đường dẫn interpreter theo máy của bạn:

```powershell
$Bot1Python = 'C:\Python314\python.exe'
& $Bot1Python --version
& $Bot1Python scripts/verify_handoff.py
& $Bot1Python scripts/check_compatibility.py --require-windows --require-python314 --output docs/test-reports/pc-windows314.json
```

Chạy verify trước khi sửa file. Exit0/PASS của compatibility chỉ hợp lệ khi
đúng Windows/Python3.14 và suite thực chạy; exit1 là FAIL, exit2 là NOT TESTED
do thiếu target. JSON/log local mới là bằng chứng Windows, không phải log Linux
được đưa sẵn trong ZIP. Nếu chưa có CPython3.14, cần cài từ nguồn chính thức theo
chính sách máy; gói không tự cài hoặc tự tải interpreter.

Trên máy khác Windows có thể kiểm tra offline bằng:

```sh
python scripts/verify_handoff.py
python scripts/run_adapter_tests.py --output docs/test-reports/pc-offline-tests.json
```

Kết quả này chỉ xác nhận đúng nền tảng đang chạy. Các unit/integration tests có
network guard; không dùng credential, gọi Binance hoặc Telegram thật.

Đọc [bàn giao chi tiết](docs/PC-HANDOFF.md) để biết phần đã đạt, phần còn thiếu
và điều kiện giữ khóa live. Code, test và Skill gốc giữ nguyên. Gói bỏ `.git`,
cache/venv, credential/config máy và database/log trong `data/runtime/`; giữ
`.agents/skills/`, mock data, SDK evidence và báo cáo kiểm thử.
