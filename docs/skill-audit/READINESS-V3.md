# Bot 1 — Readiness v3

Ngày kiểm định: **2026-11-06 (GMT+7)**. Dự án: `/workspace/Bot1`. Skill: `binance-account-monitor`, bản đã kiểm định v2. Không sửa Skill hoặc NUMERIC-1 trong đợt này; các kiểm tra đã đạt v2 được giữ nguyên, không chạy lại suite không liên quan.

**Kết luận: đủ điều kiện bắt đầu lập trình lõi Bot 1 offline bằng dữ liệu mô phỏng. Chưa đủ để viết adapter dựa trên API suy đoán, kết nối tài khoản thật hoặc triển khai VPS.** Discovery có bằng chứng PASS mới; explicit/implicit activation và việc model trong phiên mới đọc nội dung vẫn NOT TESTED do kết nối dịch vụ mô hình không hoàn tất. API/schema/quyền Binance hiện hành vẫn NOT TESTED vì ba nguồn chính thức bị proxy chặn.

## 1. Phạm vi và bằng chứng

- Đã đọc `SKILL.md` và tài liệu cần thiết về API, READ-ONLY, NUMERIC-1, recovery; đối chiếu các báo cáo v2 được người dùng chỉ định. Việc đọc trong phiên kiểm định chính không thay thế bằng chứng activation của hai phiên mới.
- Khởi chạy Codex app-server trong cwd `/workspace/Bot1`, thực hiện JSON-RPC `initialize` và `skills/list` với `forceReload: true`.
- Thử lại discovery bằng quyền filesystem hợp lệ qua cơ chế approval của công cụ; dùng `sqlite_home` và `log_dir` riêng trong `/tmp/binance-v3`. Không đổi `HOME`, `CODEX_HOME`, trust, cấu hình lưu của người dùng hoặc network policy.
- Chuẩn bị và gửi hai yêu cầu riêng cho explicit/implicit, mỗi yêu cầu trong một thread mới, ephemeral, sandbox read-only, approval never. Không thay model hoặc reasoning effort mặc định.
- Thử tải đúng ba URL tài liệu công khai người dùng cung cấp, qua proxy được cấu hình, TLS verification bật. Không gửi request có chữ ký, API Key, header xác thực Binance hoặc yêu cầu đến API tài khoản.
- Chỉ lưu request kiểm thử và phản hồi/tool output hiển thị cần thiết; không lưu reasoning riêng, token, credential file hoặc dump môi trường.

Bằng chứng máy:

- [execution.json](v3-evidence/execution.json): discovery, lỗi sandbox, prompts và phản hồi của hai phiên activation, kết quả curl.
- [api-matrix.json](v3-evidence/api-matrix.json): từng chức năng và tất cả trường API chưa xác minh.
- [integrity.json](v3-evidence/integrity.json): hash của Skill, kiểm tra giữ nguyên file v2 và danh sách file mới.

## 2. Skill discovery và explicit activation

| ID | Kiểm tra | Kết quả | Bằng chứng / giới hạn |
| --- | --- | --- | --- |
| D01 | App-server trong sandbox filesystem ban đầu | FAIL — hạ tầng của lần thử | Exit1 trước response initialize; `Read-only file system (os error 30)`. Không kết luận Skill lỗi |
| D02 | Thử lại app-server với quyền hợp lệ | PASS | `initialize` và `skills/list` trả kết quả; process được probe dừng sau khi thu đủ response |
| D03 | Skill xuất hiện và được bật | PASS | Tên `binance-account-monitor`, scope `repo`, `enabled: true`, path `/workspace/Bot1/.agents/skills/binance-account-monitor/SKILL.md`; `errors: []` |
| E01 | Gửi yêu cầu explicit trong thread mới | PASS — chỉ giao thức submit | `thread/start` và `turn/start` trả response; prompt có `$binance-account-monitor`, kèm item chuẩn `type: skill`, name/path; không coi việc nhận request là activation PASS |
| E02 | Explicit activation hoàn tất, model đọc và áp dụng Skill | NOT TESTED | Không có phản hồi model/lệnh đọc tài liệu hoàn tất để xác nhận; có lỗi kết nối dịch vụ mô hình trong lần thử |
| E03 | Model đọc reference cần thiết | NOT TESTED | Không có tool output đọc nội dung của phiên explicit; không dùng tên file xuất hiện trong catalogue làm bằng chứng đọc |

Discovery thành công chứng minh Codex loader nhận metadata Skill trong repo, không chứng minh đã nạp body vào một lượt model thành công. Kết quả này giải quyết blocker filesystem của discovery v2; không giải quyết blocker dịch vụ mô hình.

## 3. Skill implicit activation

Yêu cầu implicit được gửi trong thread riêng, không chứa tên Skill, `$binance-account-monitor`, đường dẫn Skill hoặc item `type: skill`:

> Tôi cần thiết kế lõi Python chỉ đọc để giám sát tài khoản Binance Futures USDT-M, phân biệt margin với tiền rút, vốn nạp ngoài với chuyển Spot/Futures, PnL/commission/funding; từ chối NaN và giữ phép cộng tiền chính xác; khôi phục lịch sử sau khi mất WebSocket. Dùng hướng dẫn dự án phù hợp và đọc tài liệu cần thiết trước khi trả lời. Hãy nêu quy tắc số học có giới hạn cụ thể, khôi phục và bảo mật bắt buộc, cùng API nào chưa xác minh. Chỉ lập kế hoạch từ tài liệu hiện có, không viết chương trình hoặc gọi mạng.

Developer instructions của cả hai phiên chỉ giới hạn kiểm thử đọc tài liệu, không chỉ định Skill cho implicit. Hai thread không dùng resume/fork và không được cấp lịch sử hội thoại chính. Prompt explicit dùng cùng nội dung, thêm lời gọi Skill; đây là kiểm tra có đối chứng về cách chọn Skill, không phải benchmark nhiều model/run.

| ID | Kiểm tra | Kết quả |
| --- | --- | --- |
| I01 | Thiết kế prompt implicit phù hợp description và không nhắc Skill | PASS — kiểm tra request đã lưu, không phải activation |
| I02 | Model tự chọn Skill trong phiên mới | NOT TESTED — kết nối model không hoàn tất |
| I03 | Model đọc body và reference đúng rồi trả lời theo nội dung | NOT TESTED — không có output/tool-read của model để đánh giá |

Tiêu chí PASS activation khi thử lại: phiên explicit nhận đúng yêu cầu, phiên implicit tự chọn từ request nghiệp vụ; có bằng chứng `item/completed` command/tool đọc `SKILL.md` (hoặc bằng chứng runtime nạp body tương đương) và các reference cần cho task: `security-rules.md`, `financial-arithmetic.md`, `account-events.md`, `deposit-withdrawal.md`, `websocket-recovery.md`, `binance-api.md`. Output cần thể hiện quy tắc đặc thù (bounds/context128, không margin→withdrawal, vốn nạp không ghi đôi, overlap/backfill, API chưa xác minh). Chỉ câu “đã dùng Skill” hay tìm được path không đủ. Không ép implicit bằng cách thêm tên/path hoặc đọc hộ file vào prompt.

## 4. Chẩn đoán lỗi activation và cách thử lại hợp lệ

Lần discovery trong sandbox không khởi động vì filesystem chỉ đọc. Đã thử lại qua công cụ với quyền được duyệt và thành công; không cần sửa Skill để xử lý lỗi này.

Hai phép thử activation sử dụng runtime đã có quyền khởi động app-server. Stderr cục bộ ghi lỗi gửi request và lỗi transport Responses WebSocket; phần URL được chẩn đoán chỉ lấy hostname `chatgpt.com`, không đọc/in giá trị credential. Probe có giới hạn150 giây và kết thúc process do chính probe khởi chạy nếu lượt chưa hoàn tất. Thời hạn này là giới hạn phép kiểm thử, không chứng minh Skill không kích hoạt. Chi tiết request/response, thread ID và việc turn có được submit hay không nằm trong execution.json.

Hai thread thực tế và lỗi trả về qua giao thức:

- Explicit: `01a1b1b3-d409-7611-b219-1a1f28e6022f`, turn `01a1b1b3-ebbd-71c3-978d-dcbacbebb87e`.
- Implicit: `01a1b1b4-0e10-72d3-88c3-b0456e41d9e9`, turn `01a1b1b4-2707-7b42-a989-765e464dad7b`.
- Cả hai có response initialize/thread/start/turn/start nhưng sau đó nhận `responseStreamDisconnected`, `Proxy connection failed: HTTP CONNECT failed with status 403`, rồi `Reconnecting... waiting for network` với `willRetry: true`. Không có `turn/completed`, agent message hoặc command-read hoàn tất; probe dừng sau150 giây. Exit0 của process khi shutdown không là một turn thành công.

Không đổi provider/model, trích xuất credential, interactive login hoặc bypass proxy để làm phép thử qua. Cách tiếp tục: dùng cùng prompts trong runtime Codex đã có kết nối mô hình hoạt động và quyền ghi state hợp lệ, mở root Bot1; lưu danh sách Skill, event đọc tài liệu và output của từng thread mới. Không cần API Key Binance. Nếu chỉ chạy được discovery thì chỉ đánh dấu discovery PASS.

## 5. Xác minh API và schema Binance

### Nguồn chính thức và kết quả truy cập thực tế

| Mã nguồn | URL được thử | Ngày thử (GMT+7) | Kết quả |
| --- | --- | --- | --- |
| S-A | <https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/account> | 2026-11-06 | curl exit56; proxy CONNECT403; không tải được nội dung |
| S-C | <https://developers.binance.com/en/docs/catalog/core-trading-wallet/api/rest-api/capital> | 2026-11-06 | curl exit56; proxy CONNECT403; không tải được nội dung |
| S-T | <https://developers.binance.com/en/docs/catalog/core-trading-wallet/api/rest-api/asset> | 2026-11-06 | curl exit56; proxy CONNECT403; không tải được nội dung |

Policy snapshot: restricted, đang enforced; không có custom allowed host, `developers.binance.com` không nằm trong danh sách host của executor. Phản hồi403 ở CONNECT là của proxy trước TLS tới trang tài liệu, không phải lỗi quyền tài khoản Binance. Curl `%{http_code}` là `000` vì chưa có HTTP response từ website đích; header proxy là `403 Forbidden`. Không dùng các kết quả này để khẳng định tài liệu/path đúng, API ngừng hỗ trợ, schema thay đổi hoặc API Key thiếu quyền.

Không có **ngày xác minh nội dung thành công** cho bất kỳ API nào. Ngày trong bảng là ngày thử truy cập, không gắn nhãn “đã xác minh tài liệu”. Không dùng trí nhớ, SDK cũ, nguồn cộng đồng hay bản sao chưa kiểm chứng để điền thông số.

### Ma trận chức năng bắt buộc

`CXM` = chưa xác minh từ nội dung chính thức. Mỗi hàng dưới đây đều **NOT TESTED**, không phải endpoint đề xuất sử dụng. S-A/S-C/S-T là nguồn bắt đầu tra cứu, chưa chứng minh trang đó chứa đủ mọi chức năng; đối với stream/recovery cần tiếp tục tìm tài liệu chính thức liên quan khi truy cập được.

| Chức năng | Endpoint + HTTP method | Loại bảo mật + quyền key | Request/response schema + kiểu tiền | Time window / pagination / rate limit | Trạng thái hỗ trợ hiện hành | Nguồn cần đọc |
| --- | --- | --- | --- | --- | --- | --- |
| Số dư Futures USDT-M | CXM | CXM | CXM | CXM | CXM | S-A |
| Realized/unrealized PnL | CXM | CXM | CXM | CXM | CXM | S-A và tài liệu chính thức được liên kết |
| Commission | CXM | CXM | CXM | CXM | CXM | S-A và lịch sử trade/income nếu được tài liệu xác nhận |
| Funding fee | CXM | CXM | CXM | CXM | CXM | S-A và lịch sử income nếu được tài liệu xác nhận |
| Lịch sử nạp USDT | CXM | CXM | CXM | CXM | CXM | S-C |
| Lịch sử rút USDT | CXM | CXM | CXM | CXM | CXM | S-C |
| Lịch sử chuyển Spot/Futures/Funding | CXM | CXM | CXM | CXM | CXM | S-T |
| Thay đổi tài khoản qua stream/phương thức hiện hành | CXM | CXM | CXM | CXM | CXM | Tài liệu stream chính thức; chưa xác minh URL mục con |
| Phục hồi gap sau mất stream | CXM | CXM | CXM | CXM | CXM | Tài liệu lịch sử/snapshot/stream chính thức liên quan |

Không tự điền GET, USER_DATA/SIGNED, tên quyền hoặc path từ mục đích “đọc”; HTTP method không tự chứng minh hành vi an toàn. Không tự khẳng định `ACCOUNT_UPDATE`, `ORDER_TRADE_UPDATE` hoặc cơ chế phiên cũ vẫn hỗ trợ: đó là mục tiêu cần xác minh trong Skill, chưa là kết quả v3.

### Đối chiếu NUMERIC-1

**NOT TESTED với schema Binance:** chưa có schema/ví dụ nguồn đã đọc nên chưa tìm được trường tương thích hoặc không tương thích có bằng chứng. Không có cơ sở sửa NUMERIC-1 hoặc thay kết luận F01/F02 v2.

Khi lấy được tài liệu, kiểm tra từng trường tiền/giá/lượng/fee/PnL: JSON string hay number, khả năng âm/zero/null, scale/exponent, digits/magnitude và đơn vị/asset. NUMERIC-1 nhận chuỗi ở biên: nếu nguồn dùng JSON number thì cần adapter giữ nguyên lexeme số chính xác hoặc cơ chế parse chính xác đã kiểm chứng; không qua float rồi `str()`. Timestamp/ID/status không được đưa vào validator tiền chỉ vì có dạng số.

Nếu nguồn thực có scale>18, exponent ngoài±18, magnitude ngoài bound hoặc representation không hợp grammar, ghi field/schema/URL/ngày và mẫu công khai đã lọc; dừng adapter liên quan, đề xuất thay đổi hồ sơ có chứng minh precision và regression. Không clamp/round/zero-fill hoặc tự nới bound. Ví dụ response công khai riêng lẻ không chứng minh bound tối đa của toàn API; nếu tài liệu không nêu bounds thì phải công bố chưa xác minh.

## 6. READ-ONLY và phương án API Key

| Kiểm tra | Kết quả | Phạm vi |
| --- | --- | --- |
| Skill hiện có cấm order/cancel/modify/transfer/withdraw/leverage/config | PASS — nội dung đã đọc, không sửa | Không phải kiểm thử enforcement của adapter |
| Hoạt động trong đợt kiểm định không gọi Binance account API | PASS — giới hạn và request thực thi | Chỉ thử tài liệu công khai, không key/chữ ký |
| Phương án quyền đọc đáp ứng mọi API cần dùng | NOT TESTED | Chưa có tài liệu quyền hiện hành hoặc key được cấp; không suy ra từ tên endpoint |
| Cơ chế chặn route/quyền vượt mức ở Bot1 thực chạy | NOT TESTED | Chưa có Bot1/adapter |

Phương án thiết kế cho giai đoạn sau: key chuyên dụng chỉ được cấu hình các capability đọc đã xác minh; không trading, withdrawal, transfer hoặc sửa tài khoản. Nếu có hỗ trợ IP allowlist phù hợp sau khi xác minh, dùng làm lớp bổ sung, không thay thế quyền đọc. Secret phải qua cơ chế an toàn, không source/log/tài liệu; không cần cung cấp key để hoàn thiện xác minh tài liệu.

Không khẳng định một key read-only có thể dùng mọi API Futures/Wallet/stream trước khi tài liệu quyền chứng minh. Nếu chức năng chỉ hoạt động khi bật quyền vượt ranh giới Bot1, không yêu cầu bật: đánh dấu chức năng không khả dụng trong thiết kế này hoặc dùng nguồn chỉ đọc khác đã xác minh. Cấm kiểm tra quyền bằng một lệnh, chuyển tiền, rút hoặc sửa leverage “thử nghiệm”.

**Danh sách endpoint được đề xuất thực thi trong v3: rỗng.** Chưa endpoint nào vượt qua kiểm chứng nội dung/hành vi/quyền. Khi xác minh được mới thêm allowlist method+path+semantics; quản lý phiên chỉ khi đúng ranh giới đọc và không đổi tài sản/cấu hình giao dịch. Không giả định method POST là bị cấm tuyệt đối hoặc GET là an toàn tuyệt đối.

## 7. Các hạng mục phải chờ Bot1

- Unit tests trên module numeric thực tế, không nhập checker tài liệu làm production code để giả test đã hoàn thành.
- Mapping schema → ledger/projection, transaction/checkpoint, canonical correlation REST/stream và chống ghi trùng vốn/PnL/commission.
- Fake transport + DB thật tạm để test pagination/gap/partial update/reconnect/restart/crash/concurrency và giữ UNKNOWN đúng lúc.
- Enforce deny-by-default route/method/capability bằng spies; redaction bằng secret giả; Bot4 không kích hoạt hành động tài chính.
- Outbox retry/rate limit/ambiguous ack, kiểm tra thông báo trùng thực tế và latency; watchdog/backup/restore/soak24h trên nền tảng được công bố.
- Đối chiếu read-only với dữ liệu tài khoản chỉ khi có yêu cầu riêng và quyền/API đã xác minh; không dùng thao tác tài chính để tạo dữ liệu test.

Tất cả hạng mục trên **NOT TESTED trong v3**. Discovery PASS không thay thế bất kỳ test bot nào. Test-plan v2 vẫn là kế hoạch, không đổi trạng thái40 case thành PASS.

## 8. Quyết định và bước tiếp theo

**PASS:** Codex discovery thực thi với quyền hợp lệ; Skill repo enabled và không có lỗi loader; tính toàn vẹn các file v2/Skill được kiểm tra bằng hash. **FAIL:** lần khởi động app-server trong sandbox hạn chế (lỗi hạ tầng), đã có retry discovery thành công. **NOT TESTED:** explicit/implicit activation và đọc tài liệu trong hai phiên model; toàn bộ hợp đồng API/quyền/schema Binance và các chức năng Bot1 chưa tồn tại.

Có thể chuyển sang **lập trình lõi offline** theo đặc tả v2: validation NUMERIC-1, schema nội bộ, ledger/idempotency/outbox abstractions và unit/integration tests với dữ liệu tổng hợp. Việc này không phụ thuộc key thật hoặc endpoint được suy đoán.

Chưa chuyển sang Binance adapter/live hoặc VPS. Để mở các bước đó: khôi phục phép thử activation trên runtime có kết nối model; cho phép đọc host tài liệu chính thức qua quy trình cấu hình mạng hợp lệ (không bypass), xác minh từng hàng API/permission/schema và hoàn thành test runtime. Không sửa Skill hay NUMERIC-1 chỉ để che những mục chưa kiểm chứng.
