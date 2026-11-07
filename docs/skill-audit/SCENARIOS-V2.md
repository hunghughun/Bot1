# Rà soát lại toàn bộ16 tình huống — v2

Ngày 2026-11-06 (GMT+7). Dùng đúng đầu vào và nhánh lỗi của [16 tình huống ban đầu](SCENARIOS.md), bổ sung các token/số biên của NUMERIC-1. Dưới đây là kết quả áp dụng lại chỉ dẫn sau sửa, không chạy Bot 1. **Không gắn PASS cho chức năng diễn tập**. Cột kiểm tra đã chạy chỉ nêu số học thuần của checker độc lập; không đánh đồng với ingest, dedup, projection, stream hoặc gửi tin đã hoạt động.

| ID | Đầu vào cũ / cách xử lý sau sửa | Kiểm tra trực tiếp đã chạy | Chức năng Bot 1 |
| --- | --- | --- | --- |
| S01 | D1 deposit100 pending→success→replay: validate positive primitive rồi một economic posting/key; giữ event/detection time | `S01-DEPOSIT-ARITHMETIC`: 0+100=100; chưa test chuyển trạng thái | NOT TESTED; tài liệu đã rà soát |
| S02 | Rút gross20 +fee riêng1 từ100; failed không tự debit: validate amount/fee theo miền và nguồn | `S02-WITHDRAW-FEE-ARITHMETIC`: 100−20−1=79; chưa test API status | NOT TESTED; tài liệu đã rà soát |
| S03 | Deposit100 rồi Spot→Futures100: vốn ngoài100, không200; cùng economic transfer hai chân | Ba oracle Spot0, Futures100, vốn ngoài100 trên các khoản đã đối soát trước; **không chạy dedup** | NOT TESTED; tài liệu đã rà soát |
| S04 | Futures100→Spot30→Funding10, chân trễ: ghi từng scope, chưa đủ thì giữ gap | Ba oracle số dư70/20/10; chưa kiểm tra ingest chân trễ | NOT TESTED; tài liệu đã rà soát |
| S05 | NEW chưa fill; available80→60, wallet100: không withdrawal; fill mới xét exposure | `S05-WALLET-DELTA-ORACLE`: wallet delta0, chưa test phân loại margin | NOT TESTED; tài liệu đã rà soát |
| S06 | Fills0.4/0.6, replay cumulative1; đóng0.2/toàn bộ: incremental, side và source IDs | Hai oracle lượng1.0/còn0.8; chưa test replay hoặc position state | NOT TESTED; tài liệu đã rà soát |
| S07 | Wallet100, realized+8, fee−1, funding−0.5, unrealized+4: đúng dấu/asset, không tính unrealized vào wallet | `S07-PNL-FEES-ARITHMETIC`:106.5; chưa test correlation commission hai nguồn | NOT TESTED; tài liệu đã rà soát |
| S08 | REST/stream replay cùng trade và ID khác namespace: unique/canonical theo bằng chứng, không merge heuristic | Chỉ đọc lại quy tắc ID/outbox, không có DB/worker để chạy | NOT TESTED; tài liệu đã rà soát |
| S09 | Disconnect120s, gap3 events, trang REST lỗi: overlap/backfill, không complete trước đủ trang | Chỉ đọc state machine/gap/retention, không chạy transport | NOT TESTED; tài liệu đã rà soát |
| S10 | Telegram timeout/rate limit/ack mất: durable outbox, retry có giới hạn, ambiguous công khai | Chỉ đọc hướng dẫn; chính sách ambiguous chi tiết vẫn là việc phải chốt khi thiết kế notifier | NOT TESTED; tài liệu đã rà soát |
| S11 | Amount abc, time/schema/status lạ/partial update: quarantine, không zero-fill, không complete qua gap | `BOUND-28` từ chối abc; chưa test timestamp/schema/DB | NOT TESTED; tài liệu đã rà soát |
| S12 | Yêu cầu bật trading/rút/auto-transfer: từ chối, không xin nâng quyền | Không gọi route tài chính trong đợt này; chưa test enforcement adapter | NOT TESTED; tài liệu đã rà soát |
| S13 | Crash trước/sau commit hoặc sau send trước ack: giữ checkpoint/outbox/ambiguous, replay có ID | Chỉ đọc quy tắc transaction và recovery; không kill/restore DB | NOT TESTED; tài liệu đã rà soát |
| S14 | NaN/sNaN/±Infinity/Inf: finite bắt buộc, reject trước so sánh/ledger; F01 đã có quy tắc cụ thể | `NF-01..NF-15` PASS trong model số học; không có posting lỗi hoặc fallback0 trong model | NOT TESTED trên bot; đặc tả đã sửa |
| S15 | Số dài F02 +0.01: context128/traps và bound cho kết quả chính xác; ngoài bound thì reject | `F02-REGRESSION` PASS:1234567890123456789012345678.91; bounds/context/ratio có test riêng | NOT TESTED trên bot; đặc tả đã sửa |
| S16 | Bot4 giả/replay/sai account đòi transfer; delta không nguồn: từ chối hành động, giữ UNKNOWN/gap | Chỉ đọc security/reconciliation, không có receiver hay classifier | NOT TESTED; tài liệu đã rà soát |

Tổng: **16/16 đã rà soát lại; 16/16 chức năng runtime NOT TESTED**. Bằng chứng PASS chỉ thuộc các test checker độc lập được ghi rõ ở [numeric-results-v2.json](numeric-results-v2.json). Không có cuộc gọi tài khoản Binance/Telegram và không có dữ liệu tài chính thật.
