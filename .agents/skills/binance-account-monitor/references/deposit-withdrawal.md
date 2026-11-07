# Nạp, rút và chuyển USDT

## Phạm vi tiền

Theo dõi hai góc nhìn tách biệt: (1) dòng vốn bên ngoài vào/ra toàn bộ Binance; (2) vốn vào/ra ví Futures. Spot và Funding là các ví nội bộ trong phạm vi này. Chuyển ví thay đổi vốn Futures nhưng không tạo khoản nạp/rút bên ngoài.

| Luồng cần theo dõi | Phân loại | Nguồn bằng chứng cần xác minh |
| --- | --- | --- |
| Ví ngoài → Binance | DEPOSIT | Deposit History; không chỉ dựa vào biến động Futures |
| Binance → ví ngoài | WITHDRAWAL | Withdraw History và trạng thái/fee nguồn |
| Spot → Futures | INTERNAL_TRANSFER | Lịch sử transfer đúng chiều và hai ví |
| Futures → Spot | INTERNAL_TRANSFER | Lịch sử transfer đúng chiều và hai ví |
| Spot ↔ Funding, Funding ↔ Futures | INTERNAL_TRANSFER nếu được hỗ trợ | Loại transfer/mapping thực tế trong tài liệu; không giả định mọi cặp ví có chuyển trực tiếp |

Nếu luồng phải qua ví trung gian, giữ từng chặng và quan hệ, không tạo một transfer trực tiếp giả. Ngoài phạm vi tài khoản đã cấu hình (ví dụ subaccount) phải phân loại rõ boundary; không tự gắn là nạp ngoài hoặc chuyển nội bộ.

## Vòng đời và trường dữ liệu

Lưu mã giao dịch nội bộ Binance, ID transfer, ID yêu cầu rút và TX hash theo đúng loại; TX hash không nhất thiết duy nhất cho một khoản nhận. Duy trì source ID chính xác và khóa ghép đã kiểm chứng, không thay thế bằng một chuỗi chung mơ hồ.

Mỗi thực thể giữ loại, amount, asset, fee/fee asset nếu có, network nếu có, ví nguồn/đích, trạng thái gốc + chuẩn hóa, event/detection time, thời gian request/completion khi có, bằng chứng và số dư trước/sau nếu xác thực được. Network/fee không có phải null, không giả định 0 hay suy ra mạng từ địa chỉ. Địa chỉ ví và TX hash là dữ liệu nhạy cảm về riêng tư: hạn chế log/Telegram.

Xác minh bảng mã trạng thái hiện hành: pending/processing/success/failed/canceled là nhãn nội bộ dự kiến, không là mapping số Binance đã kiểm chứng. Lần đầu thấy giao dịch đang pending và lần hoàn tất là hai cập nhật của một thực thể. Không hạch toán cùng amount ở mỗi bước. Khoản trừ/hoàn/fee phải dựa vào semantics nguồn, không tự gắn thời điểm trừ tiền với status change.

Giữ nguyên amount và phí tách biệt. Xác minh amount là gross hay net trước khi tính tổng. Withdrawal fee có thể được thể hiện khác nhau giữa bản ghi và delta ví; không trừ phí lần hai. Không ghi nhận thành công từ việc có TX hash đơn thuần nếu trạng thái chưa xác nhận.

## Ví dụ đối soát (dữ liệu mô phỏng)

Nạp ngoài 100 USDT vào Spot, sau đó chuyển 100 USDT Spot → Futures:

- Toàn Binance: vốn nạp ngoài +100; chuyển nội bộ ròng 0.
- Ví Spot: +100 rồi −100. Ví Futures: dòng vốn nội bộ +100.
- Không báo “nạp ngoài +200”; hai sự kiện có liên hệ nhưng không tự coi deposit ID và transfer ID là cùng một ID.

Nếu sau đó Futures realized PnL +8, commission −1, funding −0.5, wallet Futures tăng ròng 106.5 từ mốc trước transfer (giả định không có khoản khác). Lợi nhuận ròng của ví dụ là +6.5, vốn ngoài vẫn +100. Đây là mô hình minh họa, không khẳng định amount/status API.

Nếu một chân transfer đến chậm, tạm giữ pending reconciliation và thời điểm từng ví; không tạo “thất thoát” hoặc deposit mới. Chỉ liên kết chắc chắn khi có ID/correlation đã xác minh; nếu không ghi mức tin cậy và phần chưa chứng minh.

## Polling và lịch sử

Lập lịch đọc REST theo weight từng endpoint đã xác minh; phân trang hết cửa sổ, có overlap và dedup. Truy vấn lại giao dịch chưa kết thúc kể cả thời điểm tạo nằm trước watermark. Không dùng chỉ ngày tạo để bỏ qua cập nhật trạng thái đến muộn. Lưu watermark theo nguồn/ví/tài sản và các gap còn tồn tại.

Backfill trong giới hạn lưu giữ nguồn; lịch sử quá hạn phải báo không thể khôi phục đầy đủ. Không coi history rỗng là bằng chứng không phát sinh nếu query lỗi, sai quyền, thiếu trang hoặc vượt retention. Cảnh báo “yêu cầu rút” chỉ được phát khi API thực sự cung cấp; nếu chỉ thấy bản ghi sau đó, thông báo thời điểm phát hiện và giới hạn độ trễ.
