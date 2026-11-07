# Hồ sơ số học tài chính bắt buộc — NUMERIC-1

Đặc tả cục bộ cho Bot 1, không phải giới hạn hay schema chính thức của Binance. Cần đối chiếu từng trường với tài liệu hiện hành trước khi viết adapter. Nếu nguồn vượt hồ sơ, dừng xử lý bản ghi liên quan và báo không tương thích; không cắt chuỗi, clamp, round hoặc tự nâng giới hạn. Dùng hồ sơ/version mới có chứng minh và test khi cần mở rộng.

## 1. Tiếp nhận và từ chối dữ liệu

Tiền, phí, giá, lượng và tỷ lệ dùng chuỗi số → `Decimal` trực tiếp, không qua `float` ở bất kỳ bước nào. JSON adapter phải giữ chuỗi tài chính hoặc dùng parser số thập phân chính xác đã xác minh; nếu SDK đã biến thành float, từ chối hoặc lấy lại nguồn chính xác, không dùng `str(float)` để phục hồi giả.

Đầu vào tài chính từ bên ngoài chỉ nhận kiểu `str`; từ chối bool, float, int, Decimal object và kiểu khác tại biên này để không bỏ qua kiểm tra cú pháp/độ dài. Giá trị Decimal nội bộ chỉ được tạo từ đầu vào đã kiểm chứng hoặc phép toán hợp lệ, không đưa trở lại biên ngoài để lách validation.

Thứ tự bắt buộc: kiểm tra kiểu → độ dài/ASCII → từ chối special tokens → cú pháp/bounds dạng chữ → tạo Decimal không làm tròn → `is_finite()` → bounds exponent/scale/magnitude và miền dấu từng trường. Không so sánh `sNaN` trước bước finite. Từ chối mọi giá trị không hữu hạn, không phân biệt hoa thường hoặc dấu: `NaN`, `sNaN`, `Infinity`, `-Infinity`, `Inf`, `-Inf`, kể cả payload NaN có chữ số hoặc biến thể có dấu. Grammar bên dưới cũng loại chúng; finite check là lớp phòng thủ bắt buộc thứ hai.

Không trim khoảng trắng rồi nhận; từ chối khoảng trắng, Unicode digits, dấu phân cách nghìn, underscore, dấu `+` ở đầu, chuỗi rỗng, `.1`, `1.`. Giữ raw đã lọc trong kho bằng chứng có quyền hạn phù hợp; không đổ payload/secret vào log.

## 2. Bounds đầu vào primitive

| Thuộc tính | Quy định |
| --- | --- |
| Độ dài | 1–96 ký tự ASCII cho toàn chuỗi, kiểm tra trước tạo Decimal |
| Grammar | `-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?(?:0|[1-9][0-9]?))?` với full match ASCII |
| Chữ số hệ số thô | Tối đa 48 chữ số, đếm cả zero trong phần nguyên và phần lẻ, không tính dấu/chấm/exponent; không bỏ zero để lách giới hạn |
| Phần lẻ trong literal | Tối đa 18 chữ số trước khi áp dụng exponent |
| Exponent ghi tường minh | Mặc định 0; trị tuyệt đối ≤18; không exponent có leading zeros như `e01` |
| Exponent Decimal lưu | `e = exponent_tường_minh − số_chữ_số_phần_lẻ`, bắt buộc −18 ≤ e ≤18; không normalize rồi mới kiểm tra |
| Scale hiệu lực | `max(0, -e)` ≤18, kể cả zero; quantum nhỏ nhất cho input là `1e-18` |
| Độ lớn | `abs(value) < 1e30`; mọi số khác0 có ít nhất `abs(value) >= 1e-18` do scale; không clamp |

Số0 hợp lệ cho snapshot/balance và signed delta/metric khi schema cho phép. Miền `nonnegative` loại mọi dấu âm, kể cả `-0`; miền `positive` yêu cầu >0 (amount deposit/withdraw/transfer đã phát sinh trong mô hình nội bộ); miền `signed` cho PnL/delta/funding đã chuẩn hóa. Available balance/position quantity có thể có semantics âm: chỉ chọn miền theo schema/account mode đã xác minh, không áp nonnegative cho mọi trường. Phí/rebate giữ dấu và ý nghĩa nguồn trước khi chuẩn hóa; không tự lấy abs. Null chỉ cho trường tùy chọn được khai báo, khác0 và không đưa vào phép toán như0. Signed zero có thể giữ raw nhưng chuẩn hóa giá trị nội bộ về0 sau kiểm tra.

Cơ sở: 30 chữ số phần nguyên và 18 chữ số phần lẻ là ngân sách kỹ thuật rộng cho quan sát, không là khẳng định Binance cung cấp đến mức đó. 48 chữ số hệ số khớp 30+18; exponent và scale chặn chuỗi khoa học ngắn nhưng phình lớn/nhỏ; 96 ký tự là trần chi phí parse dự phòng (grammar hợp lệ thực tế ngắn hơn). Bounds hữu hạn giúp chứng minh precision, chống input gây tài nguyên và giữ so sánh nhất quán. Giới hạn thực của từng trường từ tài liệu API có thể hẹp hơn và phải kiểm tra thêm. Không giới hạn hiển thị USDT xuống 2 hay 8 chữ số rồi làm mất dữ liệu nguồn.

## 3. Context chính xác, cộng dồn và nhân

Dùng `localcontext` với **Context mới** đặt rõ `prec=128`, `Emin=-999`, `Emax=999`, `rounding=ROUND_HALF_EVEN`, `clamp=0`; bật traps cho `InvalidOperation`, `DivisionByZero`, `Overflow`, `Underflow`, `Subnormal`, `Clamped`, `FloatOperation`, **`Inexact` và `Rounded`**. Xóa flags khi vào operation group và kiểm tra lỗi; không kế thừa context mặc định hoặc sửa global context cho cả process/worker. `Rounded` bị trap kể cả chỉ bỏ zero, nhằm tránh mất quantum âm thầm. Constructor Decimal không tự áp context precision, vì vậy validation độc lập ở mục2 vẫn bắt buộc.

| Phép toán | Miền được chứng minh và giới hạn |
| --- | --- |
| Cộng/trừ ledger/snapshot/delta | Primitive scale≤18, abs<1e30; một aggregate có tối đa **N=1.000.000.000 leaf terms**, kể cả baseline. Tổng tuyệt đối <1e39, scale≤18, cần tối đa **57 chữ số**; 128 đủ |
| Cộng aggregate theo batch | Mang theo leaf count và policy version bền vững; tổng count hai toán hạng ≤N, không reset count theo batch hoặc restart. Kiểm tra trước phép tính; cancellation không cho bỏ count |
| Lưu/đọc aggregate | Validate finite, abs<1e39, effective scale≤18, đúng count và version; serial hóa fixed-point tối đa57 chữ số hệ số, không dùng validator primitive abs<1e30. Lưu leaf provenance để đối soát, không nhận aggregate giả từ mạng |
| Nhân chính xác | Chỉ hai primitive: tối đa96 chữ số hệ số, scale≤36, abs<1e60; precision128 đủ. Sản phẩm là derived value, không tự là amount ledger hợp lệ |
| Chuỗi toán khác | Không tự nhân aggregate/products lặp hoặc cộng vô hạn. Phải chứng minh bounds mới và test trước. Nếu output muốn thành amount ledger thì phải có bằng chứng nguồn và thỏa miền/scale thích hợp; không quantize để ép vừa |

N là giới hạn vận hành cho một kỳ/aggregate được cấu hình, không phải số sự kiện thử nghiệm đã chạy hoặc hạn mức Binance. Khi đạt N, báo `ACCUMULATION_LIMIT`; mở kỳ mới chỉ từ baseline đã đối soát và ranh giới rõ, không reset count để tiếp tục cùng aggregate ngầm. Lưu count cùng transaction dữ liệu. Trước khi vượt bounds, fail rõ; không sửa context để cố làm phép tính qua. Hạn mức nguồn/API chưa xác minh vẫn chặn adapter live.

Mọi phép cộng/trừ, hạch toán, commission/funding đã ghi nguồn và đối soát số dư phải chính xác tuyệt đối. Không tái dựng phí/PnL ghi nhận từ rate ước tính để thay khoản nguồn. Sai lệch đối soát không được làm tròn hoặc che bằng tolerance không có bằng chứng.

## 4. Chia, tỷ lệ và làm tròn có kiểm soát

- Phép chia yêu cầu chính xác dùng exact context trên; `1/3` sẽ báo `Inexact`, không tự trở thành khoản tiền xấp xỉ. Mẫu số0 báo lỗi, không trả0.
- Tỷ lệ phân tích/hiển thị được phép có rounding **khi khai báo output scale s trong 0..18, mode ROUND_HALF_EVEN, policy version và mục đích**. Đầu vào tỷ lệ là hai primitive hữu hạn đã validate. Không đưa kết quả rounded vào ledger hoặc so ngưỡng nếu có thể đảo quyết định; so ngưỡng bằng dữ liệu chính xác/cross-product trong miền đã chứng minh.
- Để không double-round tỷ lệ sát tie, quyết định lượng tử cuối từ **thương và dư chính xác**, không từ một phép chia xấp xỉ có vài guard digits: biểu diễn abs(n)=Cn×10^en, abs(d)=Cd×10^ed; đặt `k=en-ed+s`, `A=Cn×10^max(k,0)`, `B=Cd×10^max(-k,0)`. Dùng Decimal `divmod(A,B)` chính xác trong context128 để có q,r; so `2r` với B. Tăng q khi `2r>B`, hoặc `2r==B` và q lẻ. Áp dấu và scale−s cho kết quả. `was_rounded=(r!=0)`; lưu numerator/denominator, s/mode và nguồn riêng với output. Zero giữ đúng scale đầu ra.
- Chứng minh: Cn/Cd≤48 chữ số, en/ed∈[−18,18], s≤18; A≤102 chữ số, B≤84, phép so 2r≤85, tất cả dưới128. Đây là trường hợp được phép; không tổng quát hóa cho aggregate làm numerator/denominator mà không có chứng minh mới.
- Hiển thị số tiền có thể `quantize` trong context trình bày riêng precision128, scale0..18, HALF_EVEN; chỉ ở đây được tắt traps Inexact/Rounded, vẫn giữ mọi trap lỗi khác và ghi flags/metadata đã round. Không ghi đè raw/ledger. Số hiển thị không làm input tính tiền hay khóa chống trùng.

Ví dụ tỷ lệ: 1/3 tại scale8 → `0.33333333`, `was_rounded=true`; 1/8 tại scale3 → `0.125`, false; tie scale2: 1/8 →`0.12`, 3/8 →`0.38`, −1/8 →`-0.12`. Chỉ là dữ liệu tổng hợp minh họa, không là tỷ lệ Binance thực.

## 5. Lỗi và tính toàn vẹn

Phân loại lỗi an toàn: `NUMERIC_TYPE`, `NUMERIC_LENGTH`, `NUMERIC_NONFINITE`, `NUMERIC_SYNTAX`, `NUMERIC_DIGITS`, `NUMERIC_SCALE`, `NUMERIC_EXPONENT`, `NUMERIC_MAGNITUDE`, `NUMERIC_DOMAIN`, `ACCUMULATION_LIMIT`, `NUMERIC_INEXACT`, `NUMERIC_OVERFLOW`, `NUMERIC_DIV_ZERO`. Giữ event/source reference, tên trường, policy version và loại lỗi; không log secret hoặc toàn payload. NaN có payload không cần lộ literal để báo rõ lỗi.

Quarantine bản ghi và tạo gap/health alert; không thay giá trị lỗi bằng0 hoặc bỏ im lặng. Không commit financial posting/projection/outbox số dư dựa trên input lỗi. Có thể commit bằng chứng quarantine riêng nhưng không đánh dấu cửa sổ reconciliation hoàn tất qua gap. Các nguồn độc lập có thể tiếp tục theo chính sách đã công bố. Khi sửa/đọc lại nguồn, replay theo ID cũ, đối soát và đóng gap; không cộng đôi sự kiện.

## 6. Bằng chứng kiểm thử

Bắt buộc kiểm tra tất cả special tokens, schema/length/digit/scale/exponent/magnitude/domain boundaries, zero/negative/tiny, context/traps, exact sum/product, max-N bằng chứng biên (không giả chạy1 tỷ event), chia không kết thúc, tie và tỷ lệ rất sát tie, overflow/underflow có chủ ý, và bảo toàn input sau display rounding.

Xem [testing-guidelines.md](testing-guidelines.md). Bộ kiểm tra độc lập của tài liệu tại `docs/skill-audit/checks/check_numeric_policy.py` (tính từ root dự án) chỉ kiểm chứng mô hình NUMERIC-1 bằng dữ liệu tổng hợp. PASS của bộ đó không chứng minh Bot 1/adapter/DB/notifier đã triển khai đúng.
