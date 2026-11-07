# Kiểm thử và điều kiện nghiệm thu

Đây là hướng dẫn cho lần xây dựng/sửa bot sau này; bước tạo Skill không viết chương trình hay test suite của Bot 1. Dùng fixture tổng hợp và fake transport, không gọi tài khoản thật hay Telegram. Unit test không được cần mạng. Contract fixture chỉ gắn nhãn “đã kiểm chứng Binance” khi schema được đối chiếu tài liệu hiện hành.

Áp dụng [NUMERIC-1](financial-arithmetic.md) cho mọi test tài chính: finite bắt buộc, chuỗi đầu vào có bounds, context128 và traps, N/leaf count, lỗi không zero-fill. Test biên phải đối chiếu oracle độc lập; không dùng chính hàm đang thử để tạo expected.

## Ma trận tối thiểu

| Nhóm | Trường hợp và kết quả phải kiểm tra |
| --- | --- |
| Decimal | `NaN`, `sNaN`, ±Infinity/Inf và biến thể đều bị từ chối; type/bool/float/null, quá96 ký tự, hệ số>48 chữ số, fractional>18, exponent ngoài±18, effective scale>18, abs≥1e30; âm/zero theo miền; 1e-18 hợp lệ, 1e-19 lỗi; không zero-fill |
| Precision/rounding | Context128 và traps Inexact/Rounded/overflow; bound sum≤N và max57 chữ số, product≤96; ví dụ F02 phải ra chính xác; division1/3 ở exact mode phải lỗi, ratio HALF_EVEN được metadata; tie/sát tie/zero divisor, display không đổi ledger |
| Balance/margin | Available giảm do margin, wallet không đổi: không WITHDRAWAL; unrealized thay đổi không tạo REALIZED_PNL; chế độ chưa hỗ trợ báo rõ |
| Luồng vốn | Deposit 100 Spot rồi transfer 100 Futures: vốn ngoài chỉ 100; transfer ròng toàn Binance bằng 0; Funding qua trung gian, chân đến chậm và thiếu mapping |
| Rút tiền | Pending → success/failed/canceled và hiệu chỉnh; phí gross/net không trừ hai lần; TX hash không đủ xác nhận thành công |
| Trade/position | Order chưa fill; partial fills với cumulative replay; đóng một phần/toàn bộ; hedge LONG/SHORT; đảo chiều vừa đóng vừa mở; canceled không mặc định là closed position |
| PnL/fees | Commission/income/stream cùng một khoản chỉ một bút toán; funding nhận/trả; fee khác USDT giữ asset, không tự quy đổi |
| Dedup | Replay cùng nguồn, REST + stream, ID trùng khác symbol/account/wallet, cùng amount/time nhưng hai giao dịch thật; trạng thái mới phát thông báo mới đúng một khóa logic |
| Thời gian | UTC và GMT+7 qua ranh giới ngày; event time khác detection; thiếu event time giữ null; event đến muộn không lùi projection sai |
| Đối soát | Khoản nguồn đầy đủ khớp delta; thiếu khoản thành UNKNOWN; tìm được khoản muộn liên kết hiệu chỉnh không ghi đôi; snapshot lệch giờ không kết luận thất thoát |
| History | Nhiều trang, trang lỗi, overlap, retention gap, pending cũ đổi trạng thái; không tăng watermark quá khoảng chưa hoàn thành |
| Stream | Trùng, sai thứ tự, partial update, disconnect giữa snapshot, hết phiên theo schema đã xác minh; reconnect backfill đầy đủ trước nhãn dữ liệu đã đồng bộ |
| Lỗi dịch vụ | Rate limit/ban, timeout, clock skew, auth/permission, schema lạ; đúng backoff, bounded retry, không nâng quyền hoặc gọi route bị cấm |
| Restart/DB | Crash trước/sau commit, trước/sau ack gửi; restart giữ ledger/checkpoint/outbox; unique constraint và lease chống tranh chấp; disk full không làm mất gap |
| Telegram | Retry, giới hạn, token/đích sai, response mất sau gửi, escape nội dung, cooldown, backlog/dead-letter; không tuyên bố exactly-once |
| Health | Tài khoản im lặng nhưng heartbeat khỏe không báo mất mạng; snapshot stale/stream hỏng báo đúng; watchdog phát hiện tiến trình chết |
| Security | Spy thấy 0 trade/cancel/modify/transfer/withdraw/config calls; bí mật giả không xuất hiện log/exception/Telegram; quyền thừa được xác nhận chặn adapter |
| Backup | Restore bản sao nhất quán trong môi trường cô lập; replay không nhân đôi ledger/outbox; công bố RPO/RTO chưa đạt nếu thiếu dữ liệu |
| Bot 4 (tương lai) | Replay/TTL sai/producer giả/sai account bị từ chối; cảnh báo được xác nhận hoặc gắn chưa xác nhận; không gây hành động tài chính |

## Cấp độ kiểm chứng

1. Unit tests tài chính, định danh, mapping, timestamp và quyền — bắt buộc cho logic liên quan số dư.
2. Integration offline: fake REST/stream/Telegram + DB thực tạm thời; chạy bootstrap → fill/transfer → disconnect → backfill → restart → drain outbox; đối chiếu số tiền, số event và checkpoint kỳ vọng, không chỉ exit code.
3. Fault injection offline: kill tại ranh giới transaction/send, mất trang history, rate limit, disk failure, restore backup; kiểm tra không ghi trùng hoặc mất lịch sử im lặng.
4. Contract tests theo schema tài liệu chính thức đã xác minh, không nhầm fixture tự tạo là bằng chứng live API. Testnet nếu sau này được cho phép: chỉ đọc, không tạo lệnh/transfer để sinh dữ liệu; xác minh phạm vi Wallet thực sự hỗ trợ. Không có dữ liệu testnet phải ghi “chưa kiểm chứng”, không thay bằng mainnet tự động.
5. Tài khoản thật chỉ khi có yêu cầu riêng và quyền đọc phù hợp được xác minh; không là bước tự động sau khi unit test qua. Không yêu cầu API Key trong quá trình tạo Skill.

## Báo cáo và điểm chặn

Báo command, môi trường, số test thực chạy, passed/failed/skipped/unrun và giả lập hay live. Zero tests không là xác nhận hoạt động. API/schema/quyền chưa xác minh, financial invariant sai, gap chưa giải thích hoặc rò rỉ secret phải chặn tuyên bố tính năng tương ứng đã sẵn sàng. Lỗi repository khác với lỗi setup cần phân biệt rõ.

Diễn tập tài liệu chỉ ghi “đã rà soát / NOT TESTED runtime”, không gắn PASS cho chức năng chưa thực thi. PASS kiểm tra tĩnh hoặc checker số học độc lập phải ghi đúng đối tượng được kiểm tra; không cộng thành số test Bot 1.

## Kiểm tra bản thân Skill

Kiểm tra YAML frontmatter có `name: binance-account-monitor` và description không rỗng, tên trùng thư mục, Markdown link tương đối trỏ file tồn tại; đọc hết tài liệu để kiểm tra READ-ONLY và dấu “cần xác minh”. Không có bot, adapter, khóa, fixture tài khoản thật hoặc script gọi mạng trong thư mục Skill.

Cài đặt repo-scope: thư mục `.agents/skills/binance-account-monitor/`. Trong Codex mở dự án Bot1 và gọi `$binance-account-monitor`, ví dụ: “Dùng $binance-account-monitor để thiết kế unit test đối soát số dư Bot 1 bằng dữ liệu mô phỏng.” Codex cũng có thể chọn theo description khi người dùng yêu cầu xây dựng/sửa Bot 1. Nếu phiên hiện tại chưa nhận Skill mới, mở lại phiên dự án để khám phá lại; chỉ dẫn rõ đọc file `SKILL.md` khi cần, không khẳng định Skill đã được nạp chỉ vì file tồn tại.
