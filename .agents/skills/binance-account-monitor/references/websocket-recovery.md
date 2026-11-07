# Realtime, phục hồi và vận hành 24/7

## Khởi động và vòng đời stream

Trước khi triển khai, xác minh cơ chế User Data Stream hiện hành theo [binance-api.md](binance-api.md). Không mặc định cách tạo/gia hạn phiên, thời hạn listen key, URL stream hoặc cơ chế xác thực của phiên bản cũ.

Thiết kế state machine: STARTING → SYNCING → LIVE; mất dữ liệu/stream chuyển DEGRADED hoặc RECONNECTING; chỉ trở lại LIVE khi phạm vi đã đối soát đạt yêu cầu. Lỗi xác thực/quyền chuyển BLOCKED, không retry vô hạn. Đăng ký `ACCOUNT_UPDATE`, `ORDER_TRADE_UPDATE` chỉ khi tài liệu đã xác nhận hỗ trợ và quyền phù hợp.

Khi bootstrap: mở/buffer stream và lấy snapshot/history với cửa sổ chồng lấn theo semantics đã xác minh. Xử lý trùng và sự kiện đến trong lúc snapshot được lấy. Nếu nguồn không có sequence/snapshot nguyên tử thì ghi uncertainty, dùng backfill chồng lấn và đối soát đến khi nhất quán; không tuyên bố không thể có gap. Không tự phát minh sequence ID từ timestamp.

Liveness transport khác freshness dữ liệu tài chính: tài khoản không giao dịch có thể không phát account event. Theo dõi heartbeat/ping theo giao thức được xác minh, REST lần cuối thành công, clock drift, tuổi snapshot và backlog; không kết luận mất kết nối chỉ vì thiếu trade event.

## Mất mạng và khôi phục

1. Ghi thời điểm cuối dữ liệu tin cậy, lỗi đã lọc bí mật và trạng thái degraded; thông báo mất kết nối qua outbox, rate limit/cooldown.
2. Reconnect có exponential backoff + jitter + trần; chỉ quản lý lại phiên khi cần theo tài liệu. Tôn trọng giới hạn kết nối và retry của server.
3. Buffer dữ liệu mới khi có thể; backfill REST từ watermark trước lỗi, trừ cửa sổ overlap, phân trang đầy đủ và tải snapshot account/positions/orders liên quan.
4. Dedup trong DB; đối soát PnL/fees/transfers và các snapshot. Không mặc định `ACCOUNT_UPDATE` chứa tất cả tài sản/vị thế: xác minh semantics partial update trước khi merge, không xóa trường vắng mặt.
5. Commit dữ liệu/outbox/checkpoint nhất quán; lưu các gap không khôi phục được. Chỉ báo “kết nối phục hồi” cho kết nối; ghi riêng “đối soát hoàn tất” nếu dữ liệu đã đủ. Không báo đồng bộ đầy đủ khi còn gap.

Nguồn không có realtime (hoặc stream không khả dụng với quyền đọc) dùng REST polling đã xác minh với giới hạn độ trễ công bố rõ. Telegram mất mạng không được chặn ingest Binance; từng subsystem có retry/health riêng.

## Lưu trạng thái và lỗi API

Dùng DB bền vững có transaction (ví dụ SQLite một writer hoặc PostgreSQL theo tải thực tế), không chỉ cache RAM. Lưu raw đã lọc, sự kiện, projections, watermark/gap, trạng thái giao dịch pending, dedup và outbox. Dùng cơ chế khóa/single writer khi cần; restart hoặc nhiều instance không được gửi/ghi trùng do tranh chấp.

- Rate limit: ngân sách chung mọi worker theo weight và response header đã xác minh; bounded concurrency, jitter, ưu tiên gap quan trọng. Tôn trọng retry delay/ban nếu nguồn cung cấp; không reconnect/fetch dồn dập.
- Timestamp: UTC cho dữ liệu, monotonic clock cho timeout/backoff; theo dõi lệch giờ và đồng bộ OS. Lỗi timestamp cần kiểm tra clock/quy tắc auth, không chỉ tăng cửa sổ thời gian tùy ý.
- Auth/quyền/IP restriction: dừng adapter bị lỗi, cảnh báo an toàn, giữ dữ liệu đã có và tiếp tục phần độc lập; không xin nâng quyền giao dịch/rút.
- Schema lạ/mã trạng thái lạ: giữ raw trong kho hạn chế, quarantine mapping, cảnh báo và đối soát; không crash loop hoặc bỏ im lặng.
- Disk full/DB lỗi: không tiến checkpoint trước khi commit, báo lỗi nghiêm trọng; quản lý dung lượng/retention có chính sách, không tự xóa lịch sử tài chính.

## Windows và VPS Linux

Khi được yêu cầu viết bot: pin Python và dependency phù hợp hệ điều hành; tách cấu hình, DB, log và secret khỏi mã nguồn. Chọn service manager phù hợp (systemd trên Linux hoặc Windows service/Task Scheduler theo yêu cầu), working directory cố định, tài khoản OS tối thiểu quyền, restart policy có giới hạn và graceful shutdown. Không lưu secret vào unit/task command line. Chưa cài service hay triển khai bot trong bước tạo Skill.

Heartbeat lưu bền gồm last successful REST/stream health/ingest/commit, outbox age, queue depth, gap và clock skew. Ngưỡng có cấu hình và cooldown. Process đã chết không thể tự gửi Telegram: thiết kế watchdog độc lập giám sát heartbeat, cùng kênh cảnh báo dự phòng nếu Telegram hỏng.

Log có cấu trúc: UTC, severity, component, error category, correlation/event ID, độ trễ và trạng thái; không ghi credentials/payload ký. Metric quan trọng: stale snapshot, reconnect, rate budget, reconciliation residual, DB health, outbox retry/dead-letter.

Backup nhất quán DB/checkpoint/outbox theo công cụ DB, mã hóa và giới hạn quyền; chính sách retention, RPO/RTO và bản sao ngoài ổ đĩa chính theo yêu cầu. Kiểm tra restore trong môi trường cô lập bằng dữ liệu mô phỏng, sau đó replay overlap/dedup; không replay thông báo cũ không kiểm soát. Graceful shutdown flush transaction hợp lệ, giữ hàng chưa gửi; không đánh dấu sent trước khi có phản hồi.
