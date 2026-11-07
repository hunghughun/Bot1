# Bàn giao Bot 1 từ cloud sang PC — 07/11/2026 GMT+7

## Phạm vi gói

Mã nguồn hiện có, toàn bộ tests/fixtures, repo Skill, mock data,69 nguồn/excerpt
SDK có provenance, tài liệu thiết kế/audit/readiness và test reports lịch sử.
Không phải executable/installer; chương trình hiện là Python offline. Gói không
chứa `.git`, lịch sử chat đầy đủ, credential, cloud environment bindings, cache,
venv hoặc database/log nghiệp vụ trong `data/runtime/`. Phần mềm Windows/Python
và app Codex phải có sẵn trên PC theo chính sách máy.

Trong checkout cloud các file dự án đang là untracked; chưa có bằng chứng commit
hoặc push toàn bộ thay đổi lên `hunghughun/Bot1`. ZIP chứa file trên ổ đĩa, kể cả
file chưa commit. Không chỉ clone repository rồi giả định sẽ có đủ mã này.
Nếu đã có checkout local, giải nén vào thư mục mới và đối chiếu trước khi ghép;
không chép đè source/database/credential local hiện hữu một cách tự động.

## Trạng thái và bằng chứng

| Nhóm | Đã biết khi bàn giao |
| --- | --- |
| Core offline | Decimal/NUMERIC-1, Internal Schema v1, SQLite ledger, quarantine, replay/recovery, fake notifier |
| Suite nguồn |221 PASS:124 core +29 foundation +39 SDK Balance/reliability +29 smoke prep, trên Linux/Python3.12.14 |
| Windows/Python3.14 | NOT TESTED; cloud probe executed0 do thiếu Windows/interpreter |
| Balance | Wallet/available snapshots offline theo SDK18.3.0; giữ cross fields riêng, không ledger posting hoặc automatic opening |
| Fixture |1 response mock copy từ unit test SDK chính thức có metadata/hash; không phải official API response example |
| Official API docs | NOT VERIFIED; cloud proxy CONNECT403; vendor hiện chỉ README,0 HTML/PDF |
| Smoke | Command riêng, HMAC candidate test offline bằng key giả, route fixed GET Balance; live branch BLOCKED trước credential/network |
| Live/key permissions | NOT VERIFIED; chưa có live client/credential loader, chưa xác minh actual key type/read-only grants |
| Income/capital/transfer/Spot/WS | Financial mapping/correlation còn NOT VERIFIED; fail-closed |
| Telegram/VPS/soak24h | Chưa triển khai hoặc kiểm thử thực |

SDK pin: `f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179`, repository chính thức
<https://github.com/binance/binance-connector-python>. Retained evidence không cần
tải lại để chạy tests. Coverage nghiệp vụ core23/40 test cases và11/16 tình huống
không được đồng nhất với221 runtime tests hoặc tự nâng vì test môi trường PASS.

Các file nên đọc:

- [Readiness](BINANCE-ADAPTER-READINESS.md), [API matrix](API-CONTRACT-MATRIX.md).
- [Smoke preparation](BALANCE-SMOKE-TEST.md), [tài liệu cần bổ sung](vendor/binance/README.md).
- [Review mới nhất trên cloud](test-reports/balance-readiness-recheck.json).
- [221-case evidence](test-reports/adapter-offline-tests.json), [SDK provenance](api-evidence/f75b4a52c5ae/source-manifest.json).
- [Kiến trúc core](architecture/OFFLINE-CORE.md), [Skill v2 audit](skill-audit/RETEST-V2.md).

Báo cáo cloud có timestamp/đường dẫn/platform lịch sử. Không thay `/workspace/Bot1`
bằng đường dẫn PC trong các audit cũ để làm bằng chứng trông như đã chạy local.
Các script/test dùng root từ vị trí file nên có thể mở dự án ở đường dẫn PC mới.

## Điều kiện tiếp tục local

1. Mở đúng project root trong Codex PC, chạy verify trước mọi thay đổi và kiểm
   tra Skill discovery/đọc reference. Có prompt bàn giao ở CODEX-PC-PROMPT.md.
2. Chạy suite trên Windows/Python3.14 thật, giữ JSON/log mới. Có thể dùng Python
   trực tiếp như START-HERE-PC.md; không cần bypass PowerShell execution policy.
3. Đọc official docs trên mạng PC được phép. Policy cloud không mang sang PC;
   kiểm tra lỗi thật trên PC trước khi kết luận bị chặn. Draft cloud thêm host
   developers.binance.com đã lưu nhưng chưa apply, không phải cấu hình local.
4. Nếu cần xuất tài liệu bằng trình duyệt, giữ URL/ngày/HTML/PDF đầy đủ; không
   cần gửi số dư, ảnh tài khoản hoặc bí mật. Snapshot schema cần cả signing,
   limits/errors và permission, không chỉ sample response.
5. Khi có nguồn mới, cập nhật mapper/fixture/tests đúng khác biệt có chứng cứ;
   phân biệt chính thức/API docs với SDK-only, synthetic và real execution.

## Điều kiện còn thiếu trước đọc số dư thật

Official Balance/base/auth/signing/parameters/weight/quota/errors; official API
golden fixture và tests; actual key type và verified minimum read-only grants;
reviewed credential provider/live transport/TLS/clock/timeout/rate controls;
bằng chứng Windows/Python3.14. Xác nhận của operator hoặc một GET thành công
không chứng minh key không có quyền thừa. Chưa đề xuất mở live khi còn thiếu.

Tiếp tục giữ `live_readonly` khóa; không tự bật khi rời cloud. Không gửi Telegram
thật hoặc ghi ledger nghiệp vụ chính trong bước smoke snapshot sau này. Không
trade/transfer/withdraw/sửa account; không dùng float hoặc zero-fill lỗi số học.

## Kiểm tra gói

`HANDOFF-MANIFEST.json` ghi SHA256 từng file (ngoại trừ chính manifest để tránh
tự tham chiếu). `scripts/verify_handoff.py` kiểm tra các file đó trước khi sửa.
File SHA256 cạnh ZIP kiểm tra tải xuống, không phải chữ ký số chứng minh nguồn.
Kết quả giải nén/chạy Linux nằm ở PC-HANDOFF-VALIDATION.json cạnh ZIP; Windows vẫn
phải thực chạy. Đừng dùng các checksum này như manifest runtime vĩnh viễn sau
khi đã sửa source hoặc sinh lại báo cáo local.
