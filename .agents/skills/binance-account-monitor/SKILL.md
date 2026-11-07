---
name: binance-account-monitor
description: Hướng dẫn xây dựng, kiểm thử, sửa lỗi và bảo trì Bot 1 Python giám sát tài khoản Binance Futures USDT-M, nạp/rút/chuyển USDT, PnL, phí và thông báo Telegram. Dùng khi làm việc với số dư, sự kiện tài khoản, đối soát REST/WebSocket, chống trùng, khôi phục hoặc vận hành Bot 1; chỉ giám sát, tuyệt đối không giao dịch hay chuyển tiền.
---

# Binance Account Monitor — Bot 1

## Phạm vi và ranh giới

Bot 1 là bộ giám sát độc lập 24/7 cho Binance USDⓈ-M Futures (USDT-M), dự kiến chạy trên VPS Linux hoặc Windows. Quan sát Spot và Funding khi cần truy vết luồng USDT; không biến Bot 1 thành bot giao dịch. Tích hợp cảnh báo thiếu số dư từ Bot 4 chỉ thực hiện khi được yêu cầu ở giai đoạn sau.

Nếu yêu cầu chỉ là tạo/cập nhật Skill, chỉ sửa Skill và tài liệu hỗ trợ. Không tự viết chương trình, gọi API tài khoản, yêu cầu khóa hay gửi Telegram. Việc cài Skill không cấp phép chạy trên tài khoản thật.

**Bắt buộc READ-ONLY:** chỉ dùng quyền đọc. Không đặt/hủy/sửa lệnh Futures hoặc Spot, chuyển/rút tiền, sửa đòn bẩy, margin mode, position mode hoặc cấu hình giao dịch. Không yêu cầu quyền giao dịch/rút tiền để làm cho chức năng giám sát hoạt động. Thiếu quyền đọc phù hợp phải báo lỗi và chỉ rõ phần không thể giám sát.

## Trình tự khi xây dựng hoặc sửa Bot 1

1. Đọc Skill này và [quy tắc bảo mật](references/security-rules.md) trước khi triển khai. Kiểm tra chỉ dẫn dự án và thay đổi hiện có. Dùng checkout hiện tại; môi trường cloud đã cô lập, không tạo Git worktree trừ khi người dùng yêu cầu.
2. Xác định chức năng cần sửa, API và nguồn bằng chứng tương ứng trong [bản đồ API](references/binance-api.md). Đọc tài liệu Binance chính thức hiện hành trước khi chọn endpoint, tham số, quyền hoặc cách xác thực. Không suy ra từ SDK cũ. Mục chưa xác minh là chặn triển khai adapter tương ứng.
3. Kiểm tra quyền và cấu hình bằng tên/trạng thái biến, không in giá trị. Dùng dữ liệu mô phỏng trước, không kết nối tài khoản thật ngầm định.
4. Đọc và áp dụng bắt buộc [hồ sơ số học tài chính](references/financial-arithmetic.md) trước khi thiết kế snapshot, ledger và đối soát theo [sự kiện tài khoản](references/account-events.md) và [nạp/rút/chuyển](references/deposit-withdrawal.md). Ghi rõ phạm vi tài khoản, chế độ margin và dữ liệu còn thiếu.
5. Thiết kế lỗi, mất kết nối, lưu trạng thái và phục hồi theo [WebSocket và vận hành](references/websocket-recovery.md). REST là nguồn đối soát; không coi WebSocket là lịch sử hoàn chỉnh.
6. Viết unit test cho mọi thay đổi liên quan số dư; kiểm thử luồng mô phỏng và lỗi theo [hướng dẫn kiểm thử](references/testing-guidelines.md). Không tạo giao dịch thật để sinh dữ liệu kiểm thử.
7. Nếu được yêu cầu triển khai thông báo, tuân theo [Telegram](references/telegram-notifications.md): outbox bền vững, retry hữu hạn, chống trùng và bảo vệ bí mật.
8. Báo cáo kiểm thử đã chạy, lỗi, phần bỏ qua, API chưa xác minh và giới hạn còn lại. Chỉ tuyên bố tính năng hoạt động khi có bằng chứng. Không tự thực hiện hành động tài chính trong bất kỳ bước nào.

## Quy tắc tài chính không được vi phạm

- Dùng `Decimal` từ chuỗi cho mọi phép tính tiền, giá, khối lượng, tỷ lệ và phí; không qua `float`. Bắt buộc từ chối mọi giá trị không hữu hạn, gồm `NaN`, `sNaN`, `Infinity`, `-Infinity`, `Inf`, `-Inf`. Áp dụng giới hạn đầu vào, context precision 128, traps và giới hạn cộng dồn của [hồ sơ số học](references/financial-arithmetic.md); không dùng context mặc định hoặc âm thầm làm tròn ledger. Dữ liệu lỗi phải có lỗi rõ ràng, không thay bằng 0. Tỷ lệ/hiển thị có chính sách làm tròn riêng, không ghi ngược vào ledger.
- Phân biệt wallet balance, available balance, margin balance, initial margin, realized và unrealized PnL. Dùng margin khi mở lệnh không phải rút tiền.
- Lưu UTC và thời gian phát hiện riêng; hiển thị GMT+7 bằng `Asia/Bangkok`. Không gán thời gian nhận thành thời gian phát sinh khi nguồn không cung cấp.
- Phân biệt dòng vốn bên ngoài, chuyển nội bộ và kết quả giao dịch. Không cộng tiền nạp lần nữa khi USDT chuyển tiếp Spot → Futures.
- Mỗi khoản biến động phải truy về dữ liệu gốc; không đủ bằng chứng thì `UNKNOWN_BALANCE_CHANGE`, không đoán nguyên nhân.
- Lưu sự kiện, khóa chống trùng, checkpoint và outbox bền vững. Không mất lịch sử khi restart; không hứa Telegram có bảo đảm gửi đúng một lần.

## Tình trạng tài liệu

Ngày 2026-11-06: proxy trả HTTP 403 khi đọc tài liệu Binance chính thức; chưa kiểm chứng endpoint, tham số, xác thực, quyền và vòng đời stream hiện hành. Skill này không chứa URL API thực thi hoặc cách ký request chưa xác minh. Xem danh sách bắt buộc xác minh trong [binance-api.md](references/binance-api.md). Các tên sự kiện bên dưới là yêu cầu/thuật ngữ thiết kế, chưa phải chứng nhận API còn hỗ trợ.
