# Kiểm định Skill binance-account-monitor

> Báo cáo lịch sử trước sửa F01/F02. Kết quả hiện hành và cách phân loại nghiêm ngặt nằm tại [RETEST-V2.md](RETEST-V2.md). Nhãn PASS rà soát trong báo cáo cũ không là PASS chức năng; không dùng điểm72 hoặc kết luận FAIL cũ thay cho kết quả v2.

Ngày: 2026-11-06 (GMT+7). Phạm vi: Skill tại `.agents/skills/binance-account-monitor/`, không phải chương trình Bot 1. Skill giữ nguyên trong toàn bộ kiểm định.

**Kết luận: FAIL cho việc dùng làm đặc tả đủ điều kiện triển khai Bot 1. Điểm chất lượng tài liệu: 72/100.** Có thể dùng để thảo luận kiến trúc và chuẩn bị fixture offline; chưa đủ để triển khai adapter hoặc xác nhận tính chính xác tài chính. Hai thiếu sót đặc tả số học F01/F02 kích hoạt điều kiện FAIL tài chính bất kể tổng điểm. Không phát hiện chỉ dẫn giao dịch hoặc tiết lộ bí mật trong Skill; kiểm tra bảo mật lúc chạy chưa thực hiện.

## Phương pháp và giới hạn bằng chứng

- Đã đọc `SKILL.md` và cả 7 file tham khảo; kiểm tra file, YAML, link và các quy tắc bằng chương trình kiểm tra tĩnh và rà soát thủ công.
- Đã tải, đọc mã và chạy `quick_validate.py` chính thức từ kho `openai/skills` qua HTTPS với TLS verification. Validator chỉ kiểm tra cấu trúc tối thiểu; không xác nhận API, tài chính hoặc hành vi mô hình.
- Đã thực hiện 16 tình huống **diễn tập trên tài liệu**: nêu đầu vào, áp dụng hướng dẫn của Skill, ghi cách xử lý và đánh giá độ đủ của chỉ dẫn. Đây là đánh giá của người kiểm định trong phiên này, không phải chạy Bot 1 hay benchmark mô hình độc lập. Xem [SCENARIOS.md](SCENARIOS.md).
- Đã chạy riêng 7 phép kiểm tra oracle số học/thời gian bằng Python và tái hiện 2 rủi ro Decimal. Không chạy DB, WebSocket hay Telegram giả và không tính oracle là test Bot 1. Xem [evidence.json](evidence.json).
- Không có bot, API Key, kết nối tài khoản, cuộc gọi Binance account API hoặc Telegram. Chỉ truy cập tài liệu công khai và thử discovery cục bộ. Không sửa network policy, secret hay cấu hình môi trường đã lưu.
- PASS dưới đây luôn có phạm vi (cấu trúc, rà soát hoặc oracle). NOT TESTED không được quy đổi thành PASS. FAIL về đặc tả không có nghĩa đã quan sát bot làm sai.

## A — Cấu trúc

| ID | Hạng mục | Kết quả | Bằng chứng |
| --- | --- | --- | --- |
| A01 | YAML frontmatter | PASS | Parse bằng PyYAML; đúng `name`, `description` chuỗi 331 ký tự; tên trùng thư mục |
| A02 | Validator chính thức | PASS | `python3 /tmp/binance-skill-audit/quick_validate.py /workspace/Bot1/.agents/skills/binance-account-monitor` → exit 0, `Skill is valid!` |
| A03 | Kiểm tra toàn bộ references | PASS | Đọc đủ 7 file, UTF-8, không rỗng; đúng 8 Markdown file toàn Skill |
| A04 | Đường dẫn tham chiếu | PASS | 9 link tương đối: 9 tồn tại, 0 hỏng, không thoát thư mục Skill; không coi URL ngoài là đã kiểm chứng |
| A05 | Đọc và dùng Skill theo yêu cầu trực tiếp | PASS | Phiên kiểm định đã đọc Skill và áp dụng quy tắc READ-ONLY, xác minh nguồn, phân biệt mô phỏng/live |
| A06 | Codex discovery và kích hoạt tự động | NOT TESTED | Thử `codex app-server` + `skills/list` nhưng server không khởi động được vì filesystem chỉ đọc; chưa nhận phản hồi discovery |
| A07 | File dư / dấu placeholder | PASS | Không file dư, symlink hay script; không marker TODO/FIXME/TBD/HACK |
| A08 | Nội dung đủ để triển khai ngay | FAIL | Bản đồ API tự công bố chưa xác minh; F01/F02 chưa quy định đầy đủ số học an toàn |

Validator: <https://raw.githubusercontent.com/openai/skills/main/skills/.system/skill-creator/scripts/quick_validate.py>. SHA-256 bản thực chạy: `6cc9dc3199c935916cf6f73fcbbbb0e3bb1b58c8f5109fefa499978908164f51`. Tải từ nhánh main tại thời điểm kiểm định, không khẳng định đây là version pin lâu dài; hash nhận diện bản đã chạy.

Codex CLI được kiểm tra: `0.167.0-alpha.4`. Lần đầu app-server không mở được `/home/agent/.codex/state_5.sqlite`; lần sau đặt `sqlite_home` và `log_dir` tạm trong `/tmp` vẫn dừng với `Read-only file system`. Không đổi trust hoặc ghi đè cấu hình người dùng. Log nói “skills still load” không là bằng chứng Skill cụ thể đã được khám phá. Danh sách cloud/executor skills cũng không chứa Skill này, nhưng đó không phải kết luận repo-scope discovery thất bại. Cần kiểm tra lại từ phiên Codex mở trực tiếp `/workspace/Bot1`, xem danh sách Skill và gọi `$binance-account-monitor`; không thể khẳng định tự kích hoạt từ kết quả hiện tại.

## B — Chất lượng nội dung

| ID | Hạng mục | Kết quả | Đánh giá |
| --- | --- | --- | --- |
| B01 | API Binance hiện hành | NOT TESTED | Truy cập trang tài liệu account chính thức qua proxy trả CONNECT 403; không có bằng chứng endpoint/permission/lifecycle hiện hành |
| B02 | Wallet/available/margin/PnL | PASS (khái niệm) | Phân biệt số dư, initial margin và unrealized; không xem dùng margin là withdrawal; không áp dụng công thức single-asset cho mọi mode |
| B03 | An toàn đầu vào và độ chính xác số học | FAIL (đặc tả) | Decimal chưa đủ: F01/F02; ví dụ số học đơn giản đúng nhưng thiếu quy tắc bắt buộc về số hữu hạn, miền giá trị và context |
| B04 | Nạp/rút vs chuyển nội bộ | PASS (rà soát) | Có boundary toàn Binance/riêng Futures; ví dụ nạp 100 rồi chuyển 100 không thành nạp 200; pending, phí gross/net được cảnh báo |
| B05 | WebSocket disconnect | PASS (thiết kế) | Có trạng thái degraded, backoff/jitter, overlap/backfill và kiểm tra gap; tách reconnect với dữ liệu đã đồng bộ |
| B06 | Chống ghi và gửi trùng | PASS (thiết kế) | Namespace ID, DB unique/transaction, cross-source correlation, outbox; không hứa exactly-once Telegram |
| B07 | Restart và khôi phục lịch sử | PASS (thiết kế) | Checkpoint chỉ sau commit, DB bền vững, pending cũ, restore và retention gap; chưa kiểm thử chạy |
| B08 | READ-ONLY | PASS (rà soát) | Cấm order/cancel/modify/transfer/withdraw/config; không nâng quyền; phiên stream chỉ khi đúng phạm vi đọc; Bot 4 không kích hoạt tài chính |
| B09 | API Key/Secret/Telegram Token | PASS (rà soát) | Secret manager/env, không hard-code, lọc log/query/URL token; không xin khóa hoặc thử quyền bằng thao tác tài chính |
| B10 | DB/recovery/notifier/24 giờ thực chạy | NOT TESTED | Chưa có Bot 1; không có bằng chứng độ bền, độ trễ hoặc hành vi runtime |

### Toàn bộ API/hành vi chưa xác minh

Nguồn bắt buộc: <https://developers.binance.com/>. Lần kiểm định này thử trang `https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api/Account-Information-V3`: proxy trả HTTP 403 trước khi tải nội dung. Đây là truy cập tài liệu, không phải gọi endpoint tài khoản. Không suy ra API tồn tại/ngừng hỗ trợ từ HTTP 403 của proxy.

| Nhóm | Phần còn thiếu bằng chứng chính thức |
| --- | --- |
| Futures Account Information / Balance | Endpoint/version/method, trường và quyền; single/multi-assets, cross/isolated, định nghĩa các số dư |
| Position Information | Trường, mode, mapping hedge/one-way và phiên bản |
| Orders / Trade History | Query chỉ đọc, phân trang, retention, ID order/fill và commission |
| Futures Income History | Income types, dấu, ID và correlation với fill/commission/funding |
| User Data Streams | `ACCOUNT_UPDATE`, `ORDER_TRADE_UPDATE`, schema, thứ tự/partial updates, quyền và lifecycle xác thực hiện hành |
| Deposit History | Trường/ID, trạng thái, network, phí, thời gian và độ trễ xuất hiện |
| Withdraw History | Request/completion/status, amount gross/net, phí và quyền đọc |
| Universal Transfer History | Chiều được hỗ trợ, loại chuyển, ID và liên kết các chân Spot/Funding/Futures |
| Funding Wallet | Phạm vi balance/history có thể đọc, khả năng realtime và giới hạn dữ liệu |
| API restrictions / authentication / time / limits | Kiểm chứng quyền read-only/quyền thừa, ký request, clock/window, weight, lỗi, rate limit và ban |
| Testnet | Mức hỗ trợ Wallet/history và schema/permission tương ứng |

Telegram Bot API tại <https://core.telegram.org/bots/api> cũng chưa được kiểm chứng trực tiếp trong đợt audit này; không có cuộc gọi Telegram. Không nêu endpoint chưa xác minh như một cấu hình có thể sử dụng ngay.

## C — Kết quả tình huống giả lập

Chi tiết đầu vào, kết quả kỳ vọng, hướng xử lý thực hiện trong buổi diễn tập và chứng cứ tại [SCENARIOS.md](SCENARIOS.md).

- **14/16 PASS ở mức rà soát chỉ dẫn**: S01–S13 và S16.
- **2/16 FAIL về độ đầy đủ của đặc tả tài chính**: S14 (non-finite) và S15 (precision/context).
- **0 tình huống được chạy bằng Bot 1**. Không gọi đây là 14 bài integration test thành công.
- 7/7 oracle số học/thời gian độc lập PASS; 2 rủi ro Decimal tái hiện được. Oracle không chứng minh mapping Binance hoặc chống trùng/khôi phục của bot.

## Lỗi, thiếu sót và thay đổi đề xuất — chưa áp dụng

| ID | Mức | Phát hiện | Đề xuất cụ thể |
| --- | --- | --- | --- |
| F01 | P1 — tài chính | `Decimal('NaN')`, `Decimal('Infinity')`, `Decimal('-Infinity')` đều khởi tạo được; Skill chưa bắt buộc kiểm tra finite trước ghi ledger/so sánh/cảnh báo. Có hướng dẫn “input sai” chung nhưng chưa đủ đặc tả cho các chuỗi hợp lệ với Decimal này | Bắt buộc finite, từ chối bool/float và input không đúng schema; quy định nullable, miền dấu từng trường, min/max/scale; quarantine và không tiến checkpoint hoàn tất qua bản ghi lỗi |
| F02 | P1 — tài chính | “Không làm tròn khi lưu” không ngăn làm tròn trong phép tính Decimal context mặc định. Chưa có miền giá trị, precision/trap và quy tắc cộng dồn an toàn | Chọn precision từ giới hạn đầu vào + số khoản cộng; dùng context cục bộ/traps hoặc phép biểu diễn chính xác có kiểm soát; báo lỗi khi không thể bảo toàn. Chỉ round hiển thị theo quy định; không chọn precision 50 như giải pháp phổ quát |
| V01 | Chặn xác minh — không phải lỗi endpoint | Toàn bộ bảng API/permission/lifecycle hiện hành chưa được kiểm chứng | Khi đọc được nguồn chính thức, lập ma trận URL/ngày/version/method/path/quyền/schema/limits và changelog, rồi mới đề xuất cập nhật Skill |
| V02 | Chặn bằng chứng runtime | Không xác nhận được discovery/kích hoạt tự động trong môi trường hiện tại | Thử trong phiên Codex repo-scope hoạt động, lưu discovery và lời gọi trực tiếp; không suy ra từ file hợp lệ |
| I01 | P2 — vận hành | Có chỉ dẫn retry/heartbeat/độ trễ nhưng chưa có bộ ngưỡng nghiệm thu đo được | Dùng các ngưỡng đề xuất trong [TEST-PLAN.md](TEST-PLAN.md), điều chỉnh sau khi xác minh rate budget; công bố điều kiện và cỡ mẫu |
| I02 | P2 — notifier | Đã thừa nhận duplicate khi mất ack, nhưng để chính sách retry/edit/dedup cho triển khai chọn | Chốt trạng thái giao hàng ambiguous, cách báo duplicate-risk và quy trình xử lý; không đặt mục tiêu exactly-once không khả thi |

F01/F02 là thiếu sót hướng dẫn có thể dẫn đến triển khai sai; không khẳng định agent chắc chắn sẽ xử lý sai mọi lần, hay các số cực lớn trong H02 là số dư Binance thực tế. Chính vì chưa có giới hạn đầu vào được xác minh, không thể miễn trừ trường hợp này. Giữ nguyên 8 file Skill; chỉ liệt kê đề xuất, chưa sửa theo đề xuất.

## D — Kế hoạch kiểm thử

[TEST-PLAN.md](TEST-PLAN.md) có 40 test case với ID, đầu vào, kết quả kỳ vọng, bộ fixture cần chuẩn bị, phương pháp đối soát, phát hiện thiếu/trùng, đo Telegram, soak test, tiêu chuẩn dừng và phân tách việc làm ngay/chờ bot. Các test Bot 1 trong kế hoạch **chưa chạy**.

## E — Điểm và quyết định

Điểm là thang đánh giá tài liệu do đợt audit này định nghĩa, không phải điểm chính thức từ OpenAI hoặc xác suất bot đúng.

| Nhóm | Điểm tối đa | Điểm đạt | Lý do trừ |
| --- | --- | --- | --- |
| Cấu trúc/khả dụng | 20 | 17 | Chưa có bằng chứng auto-discovery/activation |
| API và nguồn hiện hành | 20 | 4 | Có quy trình xác minh trung thực; chưa xác minh các API cần dùng |
| Tài chính và dữ liệu | 25 | 18 | F01/F02 thiếu ràng buộc numeric |
| Recovery và 24/7 | 15 | 14 | Chưa có ngưỡng nghiệm thu vận hành cụ thể trong Skill |
| Telegram | 10 | 9 | Chưa chốt chính sách gửi ambiguous |
| Bảo mật tài liệu | 10 | 10 | Không phát hiện chỉ dẫn vượt quyền hoặc bí mật; không tính là chứng nhận runtime |
| **Tổng** | **100** | **72** | **Gate tài chính FAIL nên kết luận FAIL** |

Điều kiện đánh giá lại: hoàn thiện đề xuất F01/F02 sau khi có yêu cầu sửa; đọc và kiểm chứng tài liệu chính thức; xác nhận discovery; chạy lại validator, link/hashes và diễn tập. Việc vượt qua audit Skill vẫn không thay thế test Bot 1. Không cần API Key để hoàn thiện kiểm định tài liệu.
