# Số dư, ledger và phân loại sự kiện

Áp dụng bắt buộc [financial-arithmetic.md](financial-arithmetic.md): validate số hữu hạn/miền/độ dài trước phép tính; context cục bộ precision 128 với traps; ledger không round và không zero-fill lỗi. Giới hạn primitive và aggregate là hai loại khác nhau; không parse aggregate bằng bộ giới hạn primitive hoặc bỏ bộ đếm leaf khi cộng theo batch.

## Ý nghĩa số liệu

| Số liệu | Cách sử dụng |
| --- | --- |
| Wallet Balance | Số dư ví Futures theo tài sản; quan sát các khoản vốn, PnL đã ghi nhận, phí và điều chỉnh có bằng chứng |
| Available Balance | Phần khả dụng theo Binance; chịu ảnh hưởng vị thế, lệnh mở, margin và account mode; giảm không đồng nghĩa tiền rút |
| Margin Balance | Equity/margin theo định nghĩa và mode của API hiện hành; không mặc định tương đương tiền mặt |
| Initial Margin | Margin ban đầu cho vị thế/lệnh theo định nghĩa nguồn; khoản bị ràng buộc, không phải chi phí hay khoản rút |
| Unrealized PnL | Lãi/lỗ chưa thực hiện, biến động theo định giá; không ghi thành dòng vốn đã nạp hoặc lợi nhuận đã chốt |
| Realized PnL | Kết quả giao dịch đã thực hiện; lưu gross/net và phạm vi theo định nghĩa nguồn, không tự trừ phí lần hai |
| Open Positions / Order Status | Trạng thái quan sát từ Binance; lệnh, fill và vị thế là các thực thể khác nhau |
| Trading Commission / Funding Fee | Khoản phí/thu có ID nguồn và tài sản riêng; funding có thể nhận hoặc trả |

Trong trường hợp USDT single-asset đơn giản, margin balance thường liên hệ wallet + unrealized PnL. Chỉ dùng phương trình này sau khi xác minh mode/trường dữ liệu; không áp dụng mù quáng cho multi-assets, cross/isolated hoặc collateral khác. Không tự tính available balance chỉ từ initial margin. Dù mục tiêu là USDT, phải giữ nguyên tài sản của phí/PnL nguồn; không ép mọi khoản thành USDT hoặc tự tạo tỷ giá.

## Hợp đồng dữ liệu đề xuất (chưa phải mã chương trình)

- `event_id`, `schema_version`, `event_type`, `account_ref` nội bộ không chứa khóa, `wallet_scope`, `asset`, `source`, `source_record_id`, `source_event_type`.
- `occurred_at_utc` có thể null, `source_time_precision`, `detected_at_utc`, `ingested_at_utc`; thêm `requested_at_utc`, `completed_at_utc`, `source_updated_at_utc` nếu có. Không dùng thời gian phát hiện để điền thời gian phát sinh còn thiếu.
- `amount`/`signed_amount`, `fee_amount`, `fee_asset` dạng chuỗi Decimal; quy ước dấu và đơn vị ghi rõ. Unknown khác 0. Giữ cả trị nguồn và bản chuẩn hóa.
- `status`, `source_status`, `status_version`, `symbol`, `side`, `position_side`, order/trade/transaction ID khi có; `network` khi có.
- `balance_before`, `balance_after`, `balance_kind`, thời điểm và tham chiếu snapshot. Chỉ ghi khi có bằng chứng đúng phạm vi; nếu không để null, không tái dựng từ snapshot cách xa rồi gắn nhãn là số dư thật.
- `correlation_id`, `economic_event_id`, `evidence_refs`, `raw_payload_ref`/hash, `confidence`, `reconciliation_status`, `reason`, `supersedes_event_id` nếu hiệu chỉnh.
- Lưu raw payload đã lọc khóa/chữ ký/PII không cần thiết, vẫn giữ dữ liệu tài chính cần đối soát trong kho kiểm soát truy cập. Dữ liệu gốc và mapping version cho phép tái lập kết quả.

## Bảng phân loại

| Loại | Bằng chứng và lưu ý |
| --- | --- |
| `DEPOSIT` | Lịch sử nạp bên ngoài, trạng thái nguồn xác nhận; theo dõi pending và hoàn tất cùng một giao dịch |
| `WITHDRAWAL` | Yêu cầu rút và chuyển trạng thái; không coi pending là khoản đã hoàn tất hoặc tự suy ra thời điểm trừ ví |
| `INTERNAL_TRANSFER` | Cặp ví trong cùng phạm vi Binance; hạch toán từng chân và liên kết chung, không là vốn bên ngoài |
| `TRADE_OPENED` | Fill làm tăng vị thế từ 0 hoặc tăng exposure theo quy tắc sản phẩm; mở lệnh chưa fill chưa chứng minh đã mở vị thế |
| `TRADE_PARTIALLY_FILLED` | Fill một phần của lệnh; giữ cumulative và incremental riêng, không cộng cumulative nhiều lần |
| `TRADE_CLOSED` | Fill giảm exposure; phân biệt đóng một phần/toàn bộ và hedge side. Một fill đảo chiều có thể vừa đóng vừa mở |
| `REALIZED_PNL` | Khoản PnL đã thực hiện được xác minh từ trade/income; không ghi đôi hai nguồn |
| `TRADING_FEE` | Commission gắn trade/source ID, tài sản và dấu; rebate hoặc hiệu chỉnh không mặc định là phí dương |
| `FUNDING_FEE` | Income nguồn phân loại funding đã xác minh; dấu cho biết trả hay nhận, không tính lại từ funding rate dự kiến |
| `BALANCE_CHANGE` | Quan sát delta đã đối soát/giải thích; sự kiện tổng hợp không là khoản ledger mới cộng thêm |
| `LOW_BALANCE` | Available balance hoặc metric được cấu hình dưới ngưỡng; ghi metric, tuổi snapshot, hysteresis/cooldown; không dùng dữ liệu stale làm kết luận mới |
| `UNKNOWN_BALANCE_CHANGE` | Phần dư chưa có bằng chứng; giữ trạng thái chờ đối soát, không gán là rút tiền/lỗ hoặc gian lận |

Một fill có thể phát sinh nhiều nhãn nghiệp vụ nhưng chỉ một nhóm bút toán kinh tế. Trạng thái order là projection riêng kể cả NEW/CANCELED/EXPIRED/REJECTED nếu nguồn hỗ trợ; thay đổi order không nhất thiết là trade hay dòng tiền.

## Định danh và chống trùng

Ưu tiên ID nguồn có namespace: nguồn + tài khoản + phạm vi ví + tài sản + loại bản ghi + ID; thêm symbol/position side khi ID chỉ duy nhất trong phạm vi đó. Không dùng timestamp đơn lẻ hoặc số tiền để làm ID.

Phân biệt ID thực thể, ID lần cập nhật trạng thái và ID thông báo. Cùng giao dịch đổi pending → thành công phải cập nhật đúng thực thể, có sự kiện chuyển trạng thái; replay cùng cập nhật không sinh bút toán mới. Nếu thiếu ID, fingerprint các trường ổn định đã xác minh, ghi rủi ro collision, giữ raw và đưa trường hợp mơ hồ vào đối soát thay vì gộp tùy tiện.

REST và WebSocket có thể mô tả cùng commission/PnL. Liên kết qua ID đã xác minh, chọn nguồn canonical; nếu chưa chứng minh quan hệ thì giữ bản quan sát riêng, chưa cộng cả hai vào ledger. Không ghép bằng số tiền và thời gian gần nhau làm bằng chứng duy nhất.

Ràng buộc unique trong DB và transaction chung cho sự kiện, ledger, checkpoint cùng phạm vi và outbox; checkpoint chỉ tiến sau khi dữ liệu tương ứng được commit. Sự kiện đến muộn cập nhật projection theo semantics/thời gian nguồn; không ghi đè trạng thái mới bằng trạng thái cũ. Không sửa xóa lịch sử gốc: hiệu chỉnh bằng bản ghi có liên kết.

## Đối soát và bất thường

So sánh wallet delta theo **cùng tài sản, cùng ví, cùng kỳ** với transfer/deposit/withdrawal, realized PnL, commission, funding và điều chỉnh khác đã chứng minh. Phương trình dùng signed cashflow, mỗi khoản đúng một lần. Dùng biên độ chính xác theo nguồn; không tạo tolerance lớn để che sai lệch.

PnL chưa thực hiện và biến động margin có giải thích riêng, không trộn vào dòng tiền ví. Toàn Binance triệt tiêu chuyển nội bộ; riêng Futures vẫn có dòng vốn nội bộ vào/ra. Khoảng thiếu dữ liệu, snapshot không đồng thời, asset conversion, trạng thái pending, lịch sử quá hạn hoặc điều chỉnh ngoài taxonomy phải được ghi rõ.

Ngưỡng tuyệt đối/tỷ lệ, cửa sổ thời gian, dữ liệu stale và chất lượng bằng chứng quyết định cảnh báo. Trước khi kết luận bất thường, backfill và đối soát; nếu vẫn còn dư thì ghi `UNKNOWN_BALANCE_CHANGE`, số dư liên quan, số tiền chưa giải thích và dữ liệu còn thiếu. Khi tìm được nguyên nhân, liên kết hiệu chỉnh và cập nhật thông báo, không cộng delta lần nữa.
