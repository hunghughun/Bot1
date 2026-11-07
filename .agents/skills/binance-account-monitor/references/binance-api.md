# Bản đồ API và quy trình xác minh

## Nguồn và trạng thái

Nguồn chính thức: <https://developers.binance.com/>. Tra các mục USDⓈ-M Futures → Account/Trade/User Data Streams, và Wallet → Capital/Asset/Transfer. Không sao chép toàn bộ tài liệu vào Skill.

Ngày kiểm tra: **2026-11-06**. Thử đọc trang tài liệu Account Information V3 tại host này qua proxy được cấu hình; nhận `CONNECT tunnel failed, response 403`. Đây là lỗi truy cập tài liệu, không chứng minh API bị ngừng hay tài khoản thiếu quyền. Không gọi API Binance hoặc dùng thông tin tài khoản. Vì không đọc được tài liệu hiện hành, **tất cả các hàng dưới đây CẦN XÁC MINH trước khi triển khai**. Không dùng tên mục để tự đoán đường dẫn, version hoặc HTTP method.

| Nhóm tài liệu/chức năng cần tra | Mục đích và điều phải xác minh |
| --- | --- |
| Futures Account Information | Snapshot wallet/available/margin/initial margin/unrealized PnL; phiên bản còn hỗ trợ, single/multi-assets, cross/isolated và ý nghĩa từng trường |
| Futures Account Balance | Số dư theo tài sản; đơn vị, phạm vi, thời điểm snapshot, quan hệ với snapshot tài khoản |
| Position Information | Vị thế, lượng, giá vốn, chiều LONG/SHORT/BOTH, hedge mode, trạng thái đóng/mở |
| Current Orders, Order/Trade History | Trạng thái lệnh, fills và commission; phân trang và độ dài lịch sử; không dùng thao tác tạo/hủy/sửa lệnh |
| Futures Income History | Realized PnL, commission, funding và các khoản thu/chi khác; ý nghĩa dấu, ID, loại income, thời gian và lưu giữ |
| Futures User Data Streams | Hỗ trợ `ACCOUNT_UPDATE`, `ORDER_TRADE_UPDATE`; trường dữ liệu, phạm vi, thứ tự, heartbeat, lifecycle và quyền đọc tối thiểu |
| Deposit History | Nạp USDT bên ngoài; ID, network, phí nếu có, trạng thái, thời gian và giao dịch thất bại/đảo trạng thái |
| Withdraw History | Yêu cầu và lịch sử rút; ID yêu cầu/ID chuỗi, phí, trạng thái, thời gian yêu cầu/hoàn tất; chỉ đọc lịch sử |
| Universal Transfer History | Các chiều Spot/Funding/USDT-M thực sự được hỗ trợ, mã chiều, phạm vi tài khoản, ID và trạng thái; không gọi chức năng thực hiện transfer |
| Funding Wallet balance/history | Khả năng truy vấn chỉ đọc và phạm vi lịch sử; nếu thiếu nguồn đọc, công bố khoảng trống giám sát |
| API restrictions/permissions | Cách kiểm tra quyền nếu có endpoint đọc phù hợp; nếu không, kiểm tra cấu hình và báo mức xác minh hạn chế |
| Server time, limits và lỗi | Cơ chế đồng bộ clock, trọng số endpoint, hạn mức tài khoản/IP, mã lỗi, backoff và thời gian khóa |

## Cổng xác minh trước khi lập trình adapter

Với từng API cần dùng, lưu bằng chứng trong tài liệu dự án: URL trang chính thức, ngày đọc, phiên bản/changelog, host, HTTP method + path, quyền, tham số bắt buộc/tùy chọn, xác thực, ví dụ dữ liệu không chứa bí mật, lỗi, rate weight, phân trang, khoảng truy vấn tối đa và độ dài lưu giữ. Chỉ ghi các chi tiết này vào Skill sau khi đọc được nguồn hiện hành. Kiểm tra thông báo deprecation và thời điểm hiệu lực; không sử dụng API đã ngừng hỗ trợ.

Đối với xác thực: xác minh cơ chế hiện hành, cách truyền khóa/chữ ký nếu được yêu cầu, đồng bộ thời gian và yêu cầu cửa sổ thời gian. Không hard-code thuật toán, tên tham số hoặc thời hạn stream từ trí nhớ. Duy trì TLS và xác minh chữ ký/checksum của thư viện cài đặt.

Chỉ thêm route vào allowlist adapter sau khi xác minh semantics là đọc. HTTP POST không luôn là giao dịch (có thể quản lý phiên), GET không tự chứng minh an toàn; kiểm tra cả method, route và chức năng. Quản lý phiên chỉ được phép nếu không thay đổi tài chính/cấu hình giao dịch và dùng được quyền đọc. Nếu stream yêu cầu quyền vượt quá giới hạn, dừng tính năng đó, báo lỗi rõ và dùng REST chỉ đọc đã xác minh nếu đáp ứng được; không xin bật trading.

## REST và streaming

- REST: bootstrap snapshot; backfill có cửa sổ chồng lấn; đối soát định kỳ và sau reconnect; lịch sử nạp/rút/chuyển và phần thiếu sự kiện realtime. Chọn chu kỳ từ weight và yêu cầu độ trễ đã xác minh, có jitter; không tự ấn định một chu kỳ cho mọi endpoint.
- Stream: dùng làm nguồn thay đổi nhanh sau khi xác minh hỗ trợ; không thay thế REST history. Tên `ACCOUNT_UPDATE`/`ORDER_TRADE_UPDATE` là mục tiêu cần kiểm chứng, không bảo đảm toàn bộ luồng tiền đều được phát.
- Duyệt hết trang; phát hiện dữ liệu bị cắt/giới hạn lưu giữ. Không đánh dấu checkpoint hoàn thành khi có trang lỗi hoặc khoảng thời gian chưa phủ.
- Không có snapshot nguyên tử giữa Spot, Funding và Futures: gắn thời điểm từng snapshot và uncertainty; không gán chênh lệch tức thời thành thất thoát.

## Danh sách chưa xác minh cần báo cáo khi dùng Skill

Endpoint/version/method/path; tham số/lọc USDT; auth/chữ ký; quyền đọc và khả năng kiểm tra quyền thừa; stream lifecycle (không mặc định listen key hoặc TTL cũ); retention/pagination; rate limit; mã trạng thái nạp/rút/chuyển; ID ổn định và khả năng liên kết qua các ví; commission asset; account mode; khả năng lấy số dư trước/sau; mức hỗ trợ thời gian thực của Spot/Funding; khả năng testnet cung cấp lịch sử Wallet.

Không cần các câu trả lời này để soạn Skill, nhưng thiếu bằng chứng phải chặn phần triển khai tương ứng. Không suy ra permission cần thiết từ mã lỗi chung và không xin API Key ở bước tạo Skill.
