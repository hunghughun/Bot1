# Hoàn thiện Skill và kiểm định lại — v2

Ngày 2026-11-06 (GMT+7). Dùng Skill `binance-account-monitor`; chỉ cập nhật Skill, tài liệu và checker đặc tả độc lập. Không tạo Bot 1, API adapter, DB nghiệp vụ, receiver Bot4 hoặc Telegram client. Không yêu cầu API Key, không kết nối tài khoản, không dùng dữ liệu tài chính thật.

**F01/F02 đã được sửa ở mức đặc tả và có kiểm chứng bằng mô hình số học độc lập. Đủ để bắt đầu lập trình lõi Bot 1 offline với dữ liệu mô phỏng; chưa đủ để triển khai adapter Binance/live hoặc tuyên bố chức năng bot đã PASS.** API/quyền/lifecycle hiện hành và auto-discovery vẫn chưa xác minh. Không tính điểm chất lượng mới từ số test checker.

## Những thay đổi đã lưu

| File | Thay đổi |
| --- | --- |
| `.agents/skills/binance-account-monitor/SKILL.md` | Bắt buộc NUMERIC-1, finite, context128/traps, lỗi không zero-fill và tách ledger khỏi ratio/display |
| `references/financial-arithmetic.md` (trong Skill, mới) | Đặc tả đầy đủ input type/ASCII/grammar/length/digits/scale/exponent/magnitude/domain; precision và chứng minh sum/product/ratio; lỗi/quarantine |
| `references/account-events.md` | Liên kết quy tắc numeric bắt buộc, tách primitive/aggregate, giữ leaf count |
| `references/testing-guidelines.md` | Thêm test numeric biên/traps/ratio; không ghi PASS cho chức năng chỉ diễn tập |
| `docs/skill-audit/REPORT.md` | Banner xác định báo cáo cũ là lịch sử, dẫn kết quả v2 |
| `docs/skill-audit/SCENARIOS.md` | Banner dẫn kết quả rà soát lại, giữ bằng chứng lịch sử |
| `docs/skill-audit/TEST-PLAN.md` | Bổ sung NUMERIC-1 cho các case số học, giữ40 case Bot1 chưa chạy |
| `docs/skill-audit/SCENARIOS-V2.md` (mới) | Kết quả rà soát lại đủ16 tình huống; tất cả runtime NOT TESTED |
| `docs/skill-audit/checks/check_numeric_policy.py` (mới) | Checker offline độc lập cho đặc tả; không import/tạo Bot1, không mạng hoặc secrets |
| `docs/skill-audit/numeric-results-v2.json` (mới) | Kết quả thực chạy từng test numeric với exit status được kiểm tra |
| `docs/skill-audit/verification-v2.json` (mới) | YAML/validator/link/inventory, SHA-256 trước/sau, danh sách thay đổi thực tế và phạm vi kiểm chứng |
| `docs/skill-audit/RETEST-V2.md` (file này, mới) | Báo cáo hiện hành và lệnh chạy lại |

Các file Skill khác, báo cáo evidence gốc và validator chính thức không bị sửa. Thêm đúng một reference cần thiết vào Skill, không thêm Skill thứ hai. Danh sách đầy đủ hash/change thực tế ở `verification-v2.json`.

## Quy tắc mới và cơ sở

- Reject non-finite theo cả grammar và `is_finite()`; gồm NaN/sNaN/±Infinity/Inf và biến thể. Không biến input lỗi, null hoặc unknown thành0.
- Biên primitive: chuỗi ASCII≤96; hệ số≤48 chữ số; phần lẻ literal≤18; explicit và stored exponent∈[−18,18]; effective scale≤18; abs<1e30. Positive/nonnegative/signed theo field schema, không cấm mọi số âm.
- Đây là ngân sách cục bộ NUMERIC-1, không giả là limit của Binance. Chưa xác minh schema nguồn thì chưa bật adapter; vượt bound báo lỗi, không clamp/round hoặc tự nâng bound.
- Context mới/local: precision128, Emin−999/Emax999, HALF_EVEN, clamp0; trap InvalidOperation/DivisionByZero/Overflow/Underflow/Subnormal/Clamped/FloatOperation/Inexact/Rounded.
- Sum≤1 tỷ leaf, abs<1e39/scale≤18, tối đa57 chữ số. Product hai primitive≤96 chữ số. Aggregate có count/provenance/version bền vững; không reset khi batch/restart. Precision128 lớn hơn các bound đã chứng minh; không hứa vô hạn phép toán.
- Ledger/snapshot/PnL/fee reconciliation phải exact. Ratio được round riêng từ quotient/remainder, tránh double rounding; scale0..18 và HALF_EVEN có metadata. Display round không sửa ledger. Phép chia exact1/3, chia0 hay vượt precision phải báo lỗi.

## PASS — chỉ những kiểm tra đã thực chạy

1. **Checker NUMERIC-1 độc lập:101 PASS,0 FAIL**, gồm15 token non-finite, type/bounds/domain, tiny/zero/negative, trap cấu hình, precision F02, product96 digits, giới hạn sumN và vượtN, ratio/tie/sát tie, display không đổi input và12 oracle fixture số học. Một test gồm250 cặp ratio/sum tổng hợp với seed20261106, so với oracle Fraction độc lập. Không cộng các vòng lặp thành250 test case mới.
2. Overflow/underflow/rounding cố ý trong checker đều bị trap theo kỳ vọng. Input quá bounds bị reject; không fallback0. Ví dụ F02 trả `1234567890123456789012345678.91` chính xác. Chứng minh/tính giá trị biên N không có nghĩa đã ingest1 tỷ sự kiện.
3. **YAML, cấu trúc, liên kết nội bộ và validator chính thức:** kết quả máy trong `verification-v2.json`; kiểm tra sau khi lưu tệp. Lệnh `quick_validate.py` phải exit0 và `Skill is valid!`; bản validator cùng SHA-256 như audit trước, không sửa checker chính thức.
4. Kiểm tra toàn vẹn trước/sau: chỉ thay các file cần thiết và tạo các file được liệt kê; Skill có9 Markdown file, gồm8 references; tên/description hợp lệ, không placeholder TODO/FIXME/TBD/HACK. Kiểm tra trực tiếp trạng thái file trên ổ đĩa, không chỉ đưa nội dung đề xuất trong chat.

PASS ở đây kiểm chứng **checker/đặc tả và tài liệu**, không chứng minh module tài chính hoặc hàng đợi của Bot1 đã chạy đúng. Các oracle nhận các khoản đã được lựa chọn theo fixture; chúng không chạy thuật toán dedup hoặc tự xác nhận commission correlation.

## FAIL

Không có FAIL trong các kiểm tra trực tiếp v2 được ghi kết quả. Hai lỗi F01/F02 cũ đã có quy tắc và regression trong checker. Không dùng điều này để biến phần NOT TESTED thành PASS hoặc xóa kết quả lịch sử.

## NOT TESTED và cách kiểm tra thay thế hợp lệ

| Hạng mục | Trạng thái / cách tiếp tục |
| --- | --- |
| 16 tình huống runtime Bot1 | Đã đọc lại toàn bộ và ghi cách xử lý trong `SCENARIOS-V2.md`; chức năng đều NOT TESTED. Sau khi có bot, chạy fake REST/stream/Telegram + DB cô lập theo40 case của test-plan |
| Margin/PnL/deposit/withdraw/internal transfer classification và chống ghi trùng | Oracle số học có chạy; classifier/state/dedup chưa có. Không tính oracle thành test chống cộng trùng. Sau này replay event sets có expected IDs/keys và kiểm DB/outbox |
| Khôi phục, persistence và Telegram latency/24h | Chưa có bot/service nên chưa đo. Dùng fault injection/soak và ngưỡng công khai trong test-plan khi module tồn tại |
| Binance API/schema/quyền và lifecycle hiện hành | Không gọi API tài khoản hoặc truy cập lại mạng trong đợt v2. Lần audit trước proxy chặn tài liệu chính thức HTTP403; chưa có thay đổi mạng để có lý do thử lại. Kiểm chứng sau trong môi trường cho phép đọc `developers.binance.com` hoặc bằng bản tài liệu chính thức có nguồn/ngày/version rõ, rồi lập ma trận nguồn; không bypass policy |
| Telegram API hiện hành/live delivery | Chưa đọc lại docs/gọi API; fake transport khi có notifier không cần token. Kiểm tra live chỉ khi có yêu cầu riêng sau này |
| Codex tự discovery/kích hoạt Skill | Lần trước app-server không khởi động do filesystem chỉ đọc; không thử lại khi chưa có thay đổi. Kiểm tra ở phiên Codex mở root Bot1 với runtime ghi được state, xem Skill list và gọi `$binance-account-monitor`; không suy ra từ YAML hợp lệ |
| Enforce quyền READ-ONLY/log redaction thực chạy | Đã giữ quy tắc và không tạo lời gọi tài chính; enforcement vẫn NOT TESTED khi chưa có adapter. Dùng spies/secret giả trong môi trường offline, không xin cấp trading/withdrawal |

Không có công cụ cần thiết cho numeric/YAML/link/quick_validate bị chặn trong v2; tất cả chạy local bằng dữ liệu tổng hợp và validator có sẵn. Không đổi secret, trust, network policy hoặc global Decimal context để làm test qua.

## Chạy lại

Tại `/workspace/Bot1`:

```sh
python3 docs/skill-audit/checks/check_numeric_policy.py --output /tmp/numeric-recheck.json
python3 /tmp/binance-skill-audit/quick_validate.py .agents/skills/binance-account-monitor
```

Validator ở `/tmp` là artifact từ audit trước; không được giả định tồn tại trong máy mới. Nếu thiếu, lấy nguyên bản từ URL OpenAI ghi trong [REPORT.md](REPORT.md) qua HTTPS cho phép, kiểm hash/version rồi chạy. Không cần cài bot hay kết nối Binance. JSON kết quả giữ scope “independent specification model only; not Bot1”.

## Quyết định bắt đầu lập trình

**Có thể bắt đầu lõi offline**: schema nội bộ, validation NUMERIC-1, ledger/dedup/outbox abstractions và unit tests với fixture tổng hợp. Phải triển khai rồi test chính module đó, không import checker tài liệu làm production code để giả lập hoàn thành.

**Chưa được bắt đầu adapter Binance dựa trên endpoint/quyền suy đoán, kết nối thật hoặc triển khai24/7.** Trước phần này cần hoàn tất xác minh tài liệu/API, chứng minh READ-ONLY và các test runtime tương ứng. Đây là điều kiện phạm vi lập trình, không phải xác nhận Bot1 đã sẵn sàng vận hành.
