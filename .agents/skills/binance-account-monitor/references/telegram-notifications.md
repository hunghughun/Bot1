# Thông báo Telegram

## Nội dung

Mọi thông báo có loại sự kiện, event ID ngắn/correlation, tài khoản bí danh, phạm vi ví, tài sản, số tiền và dấu, trạng thái, thời gian phát sinh UTC + GMT+7 và thời gian phát hiện nếu cần. Nếu thời gian phát sinh/số tiền chưa biết, hiển thị “chưa xác định”, không tạo giá trị 0. Ghi nguồn, độ mới và độ tin cậy; số dư trước/sau chỉ khi có bằng chứng cùng metric/phạm vi. Không bao giờ đưa khóa, token, địa chỉ ví đầy đủ hoặc raw payload lên Telegram.

| Loại thông báo | Thông tin cần thêm |
| --- | --- |
| Biến động số dư Futures | Wallet/available/margin cụ thể, delta, nguyên nhân đã đối soát hoặc chưa xác định |
| Mở/đóng vị thế | Symbol, position side, lượng fill, đóng một phần/toàn bộ; order chưa fill không báo đã mở vị thế |
| Lãi/lỗ sau giao dịch | Realized PnL gross/net theo bằng chứng, phí riêng, tài sản; không trộn unrealized PnL |
| Commission/funding | Phí trả hay khoản nhận, amount/asset, source time; tránh gửi lại cùng khoản từ hai nguồn |
| Nạp thành công | Amount/asset, network nếu có, trạng thái nguồn; không tính transfer tiếp theo là deposit mới |
| Yêu cầu/trạng thái rút | Request/transaction ID đã che bớt, fee nếu có, trạng thái; không hứa quan sát ngay khi người dùng yêu cầu rút |
| Chuyển nội bộ | Ví nguồn/đích, số tiền, trạng thái và thời gian; phân biệt vốn Futures với dòng vốn ngoài |
| Số dư không đủ | Metric/threshold/observed value, snapshot age, nguồn Binance hay Bot 4, trạng thái đã/chưa xác nhận |
| Mất kết nối Binance | Component, lúc dữ liệu tin cậy cuối, mức ảnh hưởng, đang retry; không chẩn đoán nguyên nhân chưa biết |
| Kết nối phục hồi | Lúc reconnect, khoảng gián đoạn, đối soát còn gap hay đã hoàn tất |
| Biến động chưa xác định | Residual, phạm vi/kỳ, bằng chứng thiếu và trạng thái điều tra; không tự khẳng định có rút trái phép |

Mẫu minh họa (dữ liệu giả, không gửi thực tế):

> INTERNAL_TRANSFER · Thành công · evt-demo-01  
> Spot → USDT-M Futures · +100 USDT vào Futures  
> Phát sinh: 2026-11-06T08:00:00Z · 15:00:00 GMT+7  
> Phát hiện: 2026-11-06T08:00:03Z  
> Nguồn: bản ghi transfer mô phỏng · Số dư trước/sau: chưa có dữ liệu xác thực

## Outbox, giới hạn và gửi lại

Lưu outbox cùng transaction nghiệp vụ. Khóa logic gồm event ID + phiên bản trạng thái + loại thông báo + đích; unique constraint tránh enqueue trùng. Trạng thái pending/inflight/sent/retry/dead-letter, số lần thử, lần thử kế tiếp, lỗi an toàn và message reference nếu có phải bền vững; worker có lease khi chạy nhiều instance.

Timeout, mất mạng và lỗi server tạm thời: backoff + jitter, retry có trần và cảnh báo hàng tồn. Rate limit: tôn trọng thời gian chờ server trả về theo tài liệu đã xác minh, ngân sách theo chat và toàn bot; không hard-code hạn mức từ trí nhớ. Lỗi đích/quyền/token: phân loại cấu hình, không retry dồn dập; giữ hàng và báo qua health/log hoặc kênh dự phòng.

Không có giao dịch nguyên tử giữa DB và Telegram. Nếu Telegram nhận nhưng response mất, retry có thể tạo thông báo trùng; outbox giảm trùng nhưng không bảo đảm exactly-once. Giữ event ID hiển thị và trạng thái giao hàng “không chắc chắn”; định nghĩa chính sách retry/edit/dedup phù hợp, không giả định API Telegram hỗ trợ idempotency key. Không đánh dấu sent trước khi có bằng chứng phản hồi.

Gộp/cooldown các cảnh báo health/low balance lặp lại; giữ các sự kiện tài chính riêng biệt và mọi khoản trong DB. Thứ tự cập nhật trạng thái không đảo ngược khi retry; phát thông báo hiệu chỉnh khi cần. Queue đầy/DB lỗi không được mất sự kiện im lặng; ưu tiên durability và báo backlog.

Nguồn chính thức cần đọc trước khi viết notifier: <https://core.telegram.org/bots/api>. Chưa xác minh trực tiếp API, method, tham số, parse mode, error schema hay hạn mức hiện hành trong lần tạo Skill này; không gọi Telegram ở bước này.
