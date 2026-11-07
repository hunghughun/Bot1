# Bot 1 Offline Core

Lõi Python giám sát tài khoản bằng **dữ liệu tổng hợp**, có SQLite, ledger theo ví/asset, quarantine, recovery và fake notifier. Binance adapter có **Futures Balance V3 snapshot mapper offline**, đối chiếu SDK chính thức commit `f75b4a52c5ae`; chưa có client mạng, Telegram thật, khóa hoặc chức năng giao dịch. Xác minh SDK không thay thế kiểm tra API/quyền trên tài khoản thật.

Runtime chỉ dùng thư viện chuẩn, không cần cài gói hoặc mạng. Yêu cầu Python≥3.11; đã chạy test trên **Python3.12.14/Linux**. Python3.14, Windows và vận hành24 giờ chưa kiểm chứng. `setuptools==84.2.1` trong pyproject chỉ là build dependency tùy chọn; các lệnh dưới đây không dùng pip hoặc download.

Tại `/workspace/Bot1`:

```sh
python3 scripts/bot1.py --db data/runtime/bot1.sqlite init
python3 scripts/bot1.py --db data/runtime/bot1.sqlite simulate
python3 scripts/bot1.py --db data/runtime/bot1.sqlite balances
python3 scripts/bot1.py --db data/runtime/bot1.sqlite history
python3 scripts/bot1.py --db data/runtime/bot1.sqlite notifications --drain
python3 scripts/bot1.py --db data/runtime/bot1.sqlite gaps
python3 scripts/bot1.py --db data/runtime/bot1.sqlite health
python3 scripts/bot1.py --db data/runtime/bot1.sqlite recover
python3 scripts/run_tests.py
```

Fixture `data/mock/scenario.json` đã đi kèm. Nếu muốn tạo file mới:

```sh
python3 scripts/bot1.py load-mock --output data/mock/new-scenario.json
python3 scripts/bot1.py --db data/runtime/new.sqlite simulate --input data/mock/new-scenario.json --disconnect-after 5
python3 scripts/bot1.py --db data/runtime/new.sqlite gaps
python3 scripts/bot1.py --db data/runtime/new.sqlite recover --input data/mock/new-scenario.json
```

`load-mock` từ chối ghi đè file có sẵn. `simulate --pace-ms 10` phát theo nhịp10ms cục bộ; mặc định replay nhanh. `recover` đọc lại toàn lịch sử fixture và inbox chưa xử lý, không tạo dòng tiền mới từ replay. Snapshot kết kỳ khớp và manifest đủ mới báo complete. CLI `test` cũng chạy cùng suite: `python3 scripts/bot1.py test`.

Kịch bản đi kèm: nạp100 USDT Spot → chuyển100 Futures → realized+8, commission−1, funding−0.5 → unrealized snapshot+4 (không hạch toán) → chuyển30 về Spot → rút20 +phí rút riêng1. Kết quả **Spot9, Futures76.5**,10 ledger postings; vốn nạp ngoài vẫn100. Expected values viết độc lập trong fixture và được assert bằng test implementation.

`notifications --drain` chỉ ghi fake receipt vào `data/runtime/fake-telegram.jsonl`; không gửi mạng. Timeout/retry/ack mất có test riêng. Lease gửi hết hạn hoặc ack không chắc chắn chuyển ambiguous, **không tự gửi lại**; không tuyên bố exactly-once.

Đo ingest→fake ack1000 mẫu cục bộ, không phải latency Telegram:

```sh
python3 scripts/measure_fake_latency.py
```

Xem [kiến trúc và hợp đồng dữ liệu](docs/architecture/OFFLINE-CORE.md), [báo cáo triển khai và ma trận kiểm thử](docs/OFFLINE-CORE-REPORT.md), [kết quả test runtime](docs/test-reports/runtime-tests.json) và [Readiness v3](docs/skill-audit/READINESS-V3.md). Skill và audit v2/v3 được giữ nguyên. Không kết nối tài khoản thật cho đến khi xác minh endpoint/schema/quyền chính thức và hoàn thiện các kiểm tra còn thiếu.

Giai đoạn adapter: [readiness và các giới hạn](docs/BINANCE-ADAPTER-READINESS.md), [ma trận hợp đồng API](docs/API-CONTRACT-MATRIX.md). Balance mapper cần `BalanceContext` tường minh, chỉ tạo wallet/available snapshots. `SnapshotSandbox` dùng DB riêng, không ledger/outbox. Source tổng quát và cashflow/REST–WS correlation vẫn từ chối; xác minh đầy đủ API/permission còn NOT VERIFIED. `live_readonly`, signing và endpoint allowlist đều khóa.

Chuẩn bị Balance smoke-test: [hướng dẫn](docs/BALANCE-SMOKE-TEST.md). `python scripts/balance-smoke-test.py --plan` chỉ in kế hoạch; `--offline-fixture` kiểm tra mock SDK và không in số dư. Nhánh `--live` luôn bị chặn trước credential/network, kể cả có `--confirm-readonly`; chưa có live client/credential loader. HMAC candidate chỉ test offline theo SDK, chưa xác minh official API signing/key type. HTML/PDF chính thức chưa có; xem [tài liệu cần cung cấp](docs/vendor/binance/README.md). Runtime hiện221 PASS trên Linux, Windows/Python3.14 chưa kiểm thử.

Chạy regression + adapter foundations, mặc định chặn Python sockets/DNS cả process con:

```sh
python3 scripts/run_adapter_tests.py
python3 scripts/check_compatibility.py --output docs/test-reports/compat-local.json
```

Đây là interlock cho test, không thay firewall chống mã độc/native process. Adapter không chứa client mạng. `tests/fixtures/adapter-foundations.json` là JSON tổng hợp. `tests/fixtures/binance_sdk/balance_v3_response.json` sao chép response mock từ unit test SDK chính thức, có metadata/hash/commit; **không phải official API fixture hoặc dữ liệu tài khoản thật**. Các biến thể kiểm thử là dữ liệu tổng hợp.

Trên Windows, dùng Python3.14 đã cài sẵn (thay đường dẫn theo máy):

```powershell
powershell -NoProfile -File .\scripts\test-windows-python314.ps1 -PythonExecutable 'C:\Python314\python.exe'
```

Nếu PowerShell policy không cho chạy script, dùng trực tiếp wrapper Python, không cần thay execution policy:

```powershell
& 'C:\Python314\python.exe' scripts/check_compatibility.py --require-windows --require-python314 --output docs/test-reports/windows-python314.json
```

Exit0 và status PASS chỉ khi đúng target và suite thực chạy thành công; exit1 là FAIL; exit2 là NOT TESTED vì thiếu target. Script không tải/cài Python hoặc dependency. Windows/Python3.14 và soak24h vẫn NOT TESTED cho tới khi có kết quả thực từ môi trường đó.
