# Kế hoạch kiểm thử độ tin cậy Bot 1

Phiên bản kế hoạch: 1.0, ngày 2026-11-06 (GMT+7). Chỉ thiết kế; chưa viết Bot 1, adapter hay bộ test của bot. Các case dưới đây đều **NOT TESTED trên Bot 1**. Những oracle đã tính trong đợt audit là bằng chứng riêng, không đổi trạng thái các case.

Cập nhật sau sửa F01/F02: khi triển khai B1-009/B1-010/B1-011, áp dụng [NUMERIC-1](../../.agents/skills/binance-account-monitor/references/financial-arithmetic.md): input chuỗi ASCII≤96, hệ số≤48 chữ số, frac≤18, exponent tường minh/effective∈[−18,18], abs<1e30, finite bắt buộc; context128/traps, aggregate≤1 tỷ leaf với provenance và phép ratio round từ quotient/remainder chính xác. Bằng chứng checker số học nằm ở [numeric-results-v2.json](numeric-results-v2.json); không thay thế test bot. Kết quả hiện hành: [RETEST-V2.md](RETEST-V2.md).

## 1. Phạm vi và các giai đoạn

- **Làm ngay:** kiểm tra Skill/YAML/link/READ-ONLY; diễn tập; định nghĩa fixture và oracle; kiểm tra tài liệu công khai nếu truy cập được. Các hoạt động đã thực hiện ghi ở [REPORT.md](REPORT.md), không lặp dưới nhãn test bot.
- **Chờ sửa đặc tả và xác minh nguồn:** finite/bounds/precision, schema API/permission, status/amount semantics, key namespace và rate/retention. Không đoán method/path từ tên chức năng.
- **Chờ Bot 1 có module:** unit, contract theo schema đã xác minh, integration offline với fake transport + DB tạm, concurrency và fault injection.
- **Chờ runtime/service manager:** soak 24 giờ, restart/backup/restore trên Windows và VPS Linux; không gộp kết quả hai nền tảng.
- **Live read-only sau này:** chỉ khi người dùng yêu cầu riêng và cấu hình quyền phù hợp; không cần và không xin khóa cho kế hoạch này. Chỉ quan sát hoạt động sẵn có, không tạo order/transfer/deposit/withdraw để sinh dữ liệu. API testnet không đủ Wallet coverage không được ngầm chuyển sang mainnet.

## 2. Dữ liệu giả lập cần chuẩn bị

Mọi fixture là tổng hợp, không lấy từ tài khoản thật; số tài chính lưu chuỗi Decimal. Trạng thái dưới đây là mô hình nội bộ, chưa là mã Binance đã xác minh. Khi triển khai contract tests, chuẩn bị bản raw theo tài liệu đã kiểm chứng và mapping riêng; không gắn schema fixture nội bộ là schema chính thức.

| Fixture | Nội dung bắt buộc |
| --- | --- |
| FX01 snapshots | USDT single-asset: wallet `100`, available `80`, initial margin `20`, unrealized `4`, margin `104` theo giả định test được ghi rõ; tách account/mode/timestamp |
| FX02 cashflow | Deposit D1 +100 Spot; transfer X1 −100 Spot/+100 Futures; withdrawal W1 gross20 + fee riêng1; pending/success/failed/canceled; fee null và asset khác |
| FX03 trades | Order chưa fill, partial fills 0.4/0.6, close 0.2/1.0, reversal, hedge sides, cumulative và incremental, symbol/account namespace |
| FX04 incomes | Realized +8, commission −1, funding −0.5/+0.5; fee rebate; cross-source IDs có và không có correlation chắc chắn |
| FX05 replay | Replay nguyên bản, out-of-order, hai record cùng timestamp/amount khác ID, cùng ID khác namespace, status update cũ/mới |
| FX06 faults | REST nhiều trang/trang lỗi, overlap, retention gap; stream drop/expiry/partial update; clock skew, timeout/rate limit/auth/schema lạ |
| FX07 persistence | Lịch crash trước/sau commit, sau enqueue, sau send trước ack, lease hết hạn, hai worker, disk full, DB corrupt/backup restore |
| FX08 notifier | Fake ack, timeout trước nhận và sau nhận, rate limit kèm delay, đích/token sai giả, queue backlog, nội dung cần escape |
| FX09 invalid | Null/thiếu/sai kiểu, bool, float, chuỗi rỗng, `abc`, `NaN`, `sNaN`, ±Infinity, overflow/scale/magnitude cực hạn, dấu không hợp lệ theo trường |
| FX10 time/health | UTC qua ngày GMT+7, event time thiếu, detection trễ; im lặng tài khoản nhưng heartbeat khỏe; snapshot stale/watchdog/process chết |
| FX11 security | Secret giả có marker dễ nhận biết, payload Bot 4 giả/mất TTL/sai account/replay, yêu cầu nâng quyền và yêu cầu gọi route tài chính |

Mỗi bộ fixture có version/hash, seed khi random, account alias, scope/asset/mode, raw source giả, source ID/correlation, event/detection time, expected event set, expected ledger/closing snapshots, expected notification keys, gaps và lỗi kỳ vọng. Oracle viết tay/tính độc lập trước khi chạy implementation; không lấy output của bot làm expected.

## 3. Danh sách 40 test case

Mức U = unit, I = integration offline, F = fault injection, S = soak/runtime, L = live read-only sau này. Tất cả cần bot/module tương ứng trước khi thực thi; không có case nào đã PASS chỉ vì có trong bảng.

| ID / mức | Đầu vào | Kết quả kỳ vọng |
| --- | --- | --- |
| B1-001 U | FX01 available 80→60, wallet100 không đổi | Không DEPOSIT/WITHDRAWAL; wallet delta0; margin được giải thích riêng |
| B1-002 U | Wallet100, unrealized+4 theo mode test | Margin104 nếu schema/mode cho phép; wallet100, không REALIZED_PNL+4 |
| B1-003 U/I | FX02 deposit100 rồi transfer100 | Spot0/Futures100; external capital100, không200; internal net0 |
| B1-004 U/I | Futures100→Spot30→Funding10, chân đến trễ | Cuối70/20/10, tổng100; trong gap chưa khẳng định thất thoát |
| B1-005 U | W1 gross20, fee riêng1 từ Spot100, debit fixture−21 | Spot79, withdrawal/fee không ghi đôi |
| B1-006 U/I | W1 pending→failed, không debit nguồn | Không debit tự suy, giữ status và lịch sử cập nhật |
| B1-007 U | Futures100, gross realized+8, fee−1, funding−0.5 | Wallet106.5, net6.5; từng khoản duy nhất |
| B1-008 U | Funding nhận+0.5 hoặc phí bằng asset khác | Dấu đúng, giữ asset; không quy đổi thiếu tỷ giá |
| B1-009 U | FX09 non-finite, bool/float, sai dấu, null/thiếu | Từ chối/quarantine theo schema; không zero-fill hoặc ghi ledger; gap rõ |
| B1-010 U | FX09 số dài và cộng dồn sát bound đã định nghĩa | Chính xác hoặc reject có lỗi; không round im lặng; không chọn context mặc định vô thức |
| B1-011 U | 0.1+0.2 và micro-amount nhiều lần | Tổng chính xác theo oracle; round hiển thị không đổi ledger |
| B1-012 U | Order NEW chưa fill | Chỉ order projection; không TRADE_OPENED |
| B1-013 U/I | Fill0.4, fill0.6 có cumulative1.0, replay | Position1.0, không2.0; partial status đúng, fee mỗi fill một lần |
| B1-014 U | Position1, closing0.2 rồi0.8; reversal1.5 từ long1 | Đóng phần còn0.8 rồi0; reversal tách đóng1 và mở short0.5 theo mode giả |
| B1-015 U | Hedge LONG/SHORT, IDs trùng khác symbol | Projection tách đúng side/symbol; không net sai hoặc dedup nhầm |
| B1-016 I | FX04 cùng commission từ REST+stream, correlation chắc chắn | Một economic posting, giữ hai evidence refs |
| B1-017 I | Amount/time giống nhưng ID khác; ID giống khác account | Giữ sự kiện khác, không merge bằng heuristic đơn thuần |
| B1-018 I | D1 pending→success→replay success→pending cũ | Một success notification key; không lùi trạng thái hoặc ghi hai deposit |
| B1-019 I | REST 3 trang, trang2 lỗi rồi retry | Không đánh dấu cửa sổ hoàn tất trước trang2; sau retry đủ expected IDs |
| B1-020 I | Record pending trước watermark cập nhật hôm sau | Query lại và nhận status mới; không bỏ vì created time cũ |
| B1-021 I | Tập expected10, bỏ một khoản khác0 | Phát hiện missing ID và residual đúng; gap chặn đồng bộ hoàn toàn |
| B1-022 I | Bỏ hai khoản +5/−5, snapshot net không đổi | Set comparison phát hiện cả hai thiếu dù residual0 |
| B1-023 I/F | Disconnect120s, gap3 sự kiện, replay sau reconnect | Backfill đủ3, dedup, chỉ complete khi phủ gap; health/financial sync tách biệt |
| B1-024 I | Bootstrap snapshot trong lúc nhận stream; partial account update | Không áp delta hai lần, không mất event hoặc xóa field vắng; baseline/cutoff được chứng minh |
| B1-025 I | Retention gap không thể backfill | Báo incomplete coverage, không “history đầy đủ” hoặc tự tạo giao dịch |
| B1-026 I | Schema lạ, invalid timestamp, income type chưa biết | Quarantine/alert an toàn; không đoán nguồn PnL/fee hoặc âm thầm bỏ |
| B1-027 I | Rate limit/ban/timestamp/auth/quyền thiếu | Đúng nhóm lỗi và bounded backoff; không nâng quyền, không spam request |
| B1-028 F | Kill trước commit và sau commit trước enqueue hoàn tất | Transaction atomic; không mất ledger/outbox hoặc checkpoint đi trước dữ liệu |
| B1-029 F/I | Hai instance, duplicate ingest, notifier lease race | Unique event/posting/outbox; không hai worker cùng claim; kết quả ổn định |
| B1-030 I | Telegram timeout trước nhận rồi retry thành công | Một outbox logical key, không mất event; retry theo policy, ingest tiếp tục |
| B1-031 I/F | Telegram nhận nhưng ack mất, rồi restart | Ghi ambiguous/dedup-risk; không hứa exactly-once; hành vi theo chính sách đã chốt |
| B1-032 I | Telegram rate limit/delay, token/đích sai giả, backlog | Tôn trọng delay; lỗi cấu hình không retry nóng; alert/dead-letter/queue metrics rõ |
| B1-033 U/I | Chuỗi cần escape, thiếu amount/time, secret giả trong exception | Nội dung hợp lệ; unknown khác0; không secret/raw payload nhạy cảm lọt log/chat |
| B1-034 F | Disk full/DB error, backup và restore vào DB cô lập | Không advance watermark trước commit; restore kiểm tra hash/row/invariants, replay không nhân đôi |
| B1-035 U/I | UTC20:30Z ngày6/11, stale snapshot và account im lặng | Hiển thị03:30 GMT+7 ngày7/11; stale được báo; account im lặng không tự là disconnect |
| B1-036 I | Request bật trading/rút, auto-transfer, change leverage; Bot4 giả/replay | 0 lời gọi tài chính; từ chối quyền thừa; Bot4 không điều khiển route/đích/chat |
| B1-037 S | Replay workload24h + fault schedule, Windows | Đạt SLO và invariant ở mục7; report đúng số giờ thực, không mô phỏng nhanh rồi gọi 24h |
| B1-038 S | Workload24h + restart/kill trên VPS Linux | Đạt SLO/RPO/RTO; independent watchdog phát hiện process chết; không dùng PID làm readiness |
| B1-039 L | History/snapshots live cùng account/asset/window, chỉ đọc | Đối chiếu IDs, statuses, số tiền/fee và residual với raw đã bảo vệ; gap/uncertainty công khai |
| B1-040 I rồi L tùy yêu cầu | Timestamped events → outbox → fake ack; sau này Telegram thật nếu được phép | Histogram p50/p95/p99, failures/backlog theo mục6; phân biệt server ack và người nhận đã đọc |

## 4. Kiểm tra độ chính xác số dư

Định nghĩa số dư mở kỳ và cutoff nguồn cho từng account/wallet/asset/mode; snapshot là baseline, không lại cộng toàn bộ lịch sử trước baseline vào projection. Tất cả expected đều lấy từ fixture/oracle độc lập, không từ bot.

Trong fixture USDT đơn giản: `closing_wallet = opening_wallet + tổng signed cashflows duy nhất` (vốn, chuyển, realized, commission, funding, điều chỉnh đã chứng minh). Ví dụ `100 + 8 − 1 − 0.5 = 106.5`. Internal transfer có −/+ hai ví; khi tổng toàn Binance thì triệt tiêu. Unrealized không tự cộng vào wallet. Giữ asset khác riêng; available/margin kiểm theo semantics mode đã xác minh, không dùng cùng phương trình wallet cho mọi metric.

Kiểm tra cả tổng tiền, số record, source IDs, evidence refs, dấu, asset, status và từng economic posting. Yêu cầu exact equality khi fixture cùng đơn vị/độ chính xác; tolerance live chỉ theo độ chính xác nguồn được chứng minh và ghi lại, không dùng epsilon tùy ý để làm test qua. Finite/bounds/context là precondition, không để input lỗi thành số0. Tính lại từ ledger độc lập sau replay và restart.

## 5. Phát hiện bỏ sót và thông báo trùng

**Bỏ sót:** fixture có manifest expected IDs theo namespace và expected trạng thái/version. So sánh hiệu tập `expected − observed`, `observed − expected`, cardinality và hash/tổng theo cửa sổ; không chỉ tổng tiền vì hai khoản +5/−5 có thể cùng bị mất mà residual bằng0. Không dùng “khoảng trống ID” làm bằng chứng sequence thiếu nếu API không bảo đảm sequence liên tục. Theo dõi phân trang, retention, pending cũ, gap coverage, stream/REST correlation và tuổi snapshot. Cửa sổ chỉ complete khi đủ dữ liệu hoặc được đánh dấu incomplete rõ.

**Trùng DB/outbox:** nhóm theo event/economic key và notification key `(event_id, status_version, notification_type, destination)`; một posting kinh tế/khoản và một logical enqueue/key. Bản quan sát raw trùng được phép giữ nếu không sinh posting đôi. Kiểm tra replay nhiều lần và race hai worker với DB thật tạm.

**Trùng Telegram:** fake server ghi cả request attempts và deliveries riêng, liên kết event ID/notification key. Nếu timeout trước server nhận, kỳ vọng không quá một delivery sau retry; timeout sau nhận/ack mất phải phân loại ambiguous và kiểm chứng chính sách đã chốt, không áp tiêu chí exactly-once bất khả thi. Với live sau này, không tự đọc lịch sử chat bằng bot như thể API hỗ trợ đầy đủ; dùng receipt/message reference hoặc kiểm tra người nhận được cho phép. Số attempts không bằng số deliveries.

## 6. Đo độ trễ Telegram

Thu `source_occurred_at_utc`, `detected_at`, `persisted_at`, `enqueued_at`, thời điểm từng send attempt và `ack_received_at`. Monotonic clock dùng cho duration nội bộ; source-to-detection chỉ đo khi đồng hồ nguồn/hệ thống và semantics source time được xác minh. Thiếu source time thì báo không đo được phần đó.

Phân tách: source→detect (Binance/polling), detect→enqueue (bot), enqueue→ack (queue/network/Telegram), detect→ack (đầu-cuối phía bot). Telegram HTTP ack không chứng minh người dùng nhận push hoặc đọc tin. Ghi sample count, p50/p95/p99/max, failure/ambiguous/censored events và backlog; không bỏ các mẫu thất bại để làm percentile đẹp.

**Ngưỡng đề xuất để nghiệm thu sau này, chưa phải kết quả đo:** khi mạng khỏe, tải đã định nghĩa và không rate-limit, p95 detect→enqueue ≤1 giây, p95 detect→ack ≤5 giây, p99 ≤15 giây; ít nhất1.000 mẫu cho percentile offline. Live ít mẫu phải công bố, không suy ra p99 đáng tin từ vài giao dịch. REST detection latency budget tính riêng theo polling interval và rate budget đã xác minh. Khi fault, dùng thời gian phục hồi/backlog thay vì ép SLO mạng khỏe.

## 7. Vận hành 24/7, backup và phục hồi

Soak ít nhất24 giờ thời gian thực trên mỗi nền tảng được công bố hỗ trợ; seed/workload/số event/phân bố burst được ghi trước, không “time travel” fixture thay thế24 giờ thực. Lịch fault có kiểm soát gồm stream drop, REST lỗi/trang chậm, Telegram timeout/rate limit, restart lúc commit/send, disk pressure và clock skew; đồng hồ giả cho fault không làm sai số giờ soak. Test ở DB/transport cô lập, không gây lỗi trên tài khoản thật.

Tiêu chí đề xuất: không crash không được phát hiện; không mất/nhân đôi economic postings; không route tài chính; steady load queue không tăng vô hạn; không leak tài nguyên tăng đơn điệu. Đo CPU/RSS/disk/queue từng phút, warm-up1 giờ, RSS giờ cuối không quá120% baseline đã ổn định với cùng workload (phải giải thích cache hợp lệ); backlog về baseline ≤5 phút sau fault kết thúc trong điều kiện tải thử đã định nghĩa.

Watchdog bên ngoài báo process chết ≤120 giây; freshness cảnh báo theo ngưỡng nguồn đã cấu hình, phân biệt tài khoản yên lặng. Mục tiêu phục hồi offline sau lỗi tạm kết thúc ≤5 phút; RPO0 cho DB transaction đã commit trên ổ khỏe, không hứa RPO0 nếu cả ổ hỏng. Backup fixture thử RPO≤15 phút, restore RTO≤15 phút và replay overlap trong retention; nếu không đáp ứng phải báo gap thực tế, không giấu. Tất cả ngưỡng là đề xuất cần chốt theo workload và rate budget, không là cam kết đã đạt.

## 8. Đối chiếu với Binance thực tế — để sau

Chỉ đọc sau khi có yêu cầu riêng; xác minh read-only, account/mode/phạm vi ví, thời gian, retention và endpoint trước. Không xin quyền trading/withdrawal nếu stream không hoạt động. Không tạo giao dịch để test.

Lấy raw history/snapshot trong cùng cửa sổ và phạm vi, lưu có kiểm soát truy cập và hash, loại credentials khỏi evidence. Dùng export chính thức nếu sẵn có làm nguồn tham chiếu thêm; không mặc định export đầy đủ mọi trạng thái. So từng source ID, order/fill linkage, status, asset, amount, fee, source time và closing balances; REST/stream cùng mô tả một khoản không là hai khoản độc lập.

Snapshot giữa các ví không nguyên tử: lưu timestamp từng ví, xét các transfer đang đi và uncertainty. Nếu thiếu retention/trang/permission hoặc chưa có hoạt động quan sát được, kết quả là NOT TESTED/incomplete phù hợp, không PASS không phát sinh. Không lấy việc HTTP200 hoặc port mở làm chức năng đúng.

## 9. PASS/FAIL và điều kiện dừng

- PASS case cần fixture/version, expected độc lập, command, actual, assertions, exit status và evidence của đúng run. Skip/zero-tests/unrun khác PASS. Contract schema hoặc live chưa kiểm chứng phải giữ NOT TESTED.
- Bất kỳ mất tiền/ghi đôi/sai asset/dấu, non-finite lọt ledger, round không kiểm soát, phân loại margin thành withdrawal, duplicate capital, checkpoint đi trước commit, tự nâng quyền, gọi route tài chính hoặc leak secret: **FAIL và dừng triển khai**, bất kể tổng pass rate.
- Dừng adapter/feature liên quan khi permission/schema/endpoint chưa xác minh, reconciliation gap chưa giải thích, history incomplete nhưng báo complete, hoặc không restore được trạng thái. Tiếp tục phần kiểm thử độc lập nếu an toàn.
- Không hứa zero Telegram duplicates trong ambiguous-ack. FAIL nếu bot giấu ambiguous, mất logical notification hoặc không theo chính sách đã chốt. Health notification được cooldown không làm mất lịch sử tài chính.
- Trước release: toàn bộ U/I/F bắt buộc PASS; case platform S PASS cho nền tảng công bố; live L có thể chưa chạy chỉ khi phạm vi phát hành offline và không tuyên bố đã xác nhận tài khoản thật. Chưa có bot thì không có quyết định release từ kế hoạch này.

## 10. Bằng chứng và mẫu báo cáo tương lai

Mỗi run lưu run ID/UTC, nền tảng/Python/dependency versions, commit, fixture hash/seed, target, command/exit code, test count pass/fail/skip/unrun, observed ledger/notification keys, gap và latency/resource metrics. Raw tài khoản nếu sau này có phải lưu riêng được bảo vệ; báo cáo chỉ số liệu đã lọc và references an toàn.

Trạng thái hiện tại: kiểm định tài liệu và 7 oracle độc lập đã thực hiện; 40 test Bot 1 ở bảng **NOT TESTED**. Không script bot, API adapter, receiver Bot 4, Telegram client, khóa hoặc service nào được tạo trong đợt này.
