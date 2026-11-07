# Tài liệu chính thức còn thiếu

SDK chính thức đã truy xuất thành công; không cần tải thủ công SDK. developers.binance.com trước đây bị proxy CONNECT403. Không gọi lại khi chính sách mạng chưa đổi, không bypass. Các URL dưới đây **trích nguyên từ SDK đã đọc**, chưa xác minh nội dung HTTP tại host này.

Ưu tiên xuất PDF/HTML/Markdown đầy đủ có URL gốc, thời điểm tải, anchor và các link/changelog liên quan; chỉ tài liệu công khai, không ảnh tài khoản/API key. Codex sẽ hash bản cung cấp và ghi rõ provenance do người dùng chuyển tiếp.

- `futures_account_balance_v3`: <https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/account#futures-account-balance-v3>
- `account_information_v3`: <https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/account#account-information-v3>
- `get_income_history`: <https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/account#get-income-history>
- `position_information_v3`: <https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/trade#position-information-v3>
- `deposit_history`: <https://developers.binance.com/en/docs/catalog/core-trading-wallet/api/rest-api/capital#deposit-history>
- `withdraw_history`: <https://developers.binance.com/en/docs/catalog/core-trading-wallet/api/rest-api/capital#withdraw-history>
- `query_user_universal_transfer_history`: <https://developers.binance.com/en/docs/catalog/core-trading-wallet/api/rest-api/asset#query-user-universal-transfer-history>
- `query_user_wallet_balance`: <https://developers.binance.com/en/docs/catalog/core-trading-wallet/api/rest-api/asset#query-user-wallet-balance>
- `funding_wallet`: <https://developers.binance.com/en/docs/catalog/core-trading-wallet/api/rest-api/asset#funding-wallet>
- `get_account`: <https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/account#get-account>
- `start_user_data_stream`: <https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/user-data-streams#start-user-data-stream>
- `keepalive_user_data_stream`: <https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/user-data-streams#keepalive-user-data-stream>
- `close_user_data_stream`: <https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/user-data-streams#close-user-data-stream>

General information, URL được Futures README trỏ tới: <https://developers.binance.com/docs/derivatives/usds-margined-futures/general-info>. Cần trang security/auth, time-unit/recvWindow, rate headers/quota, error codes và changelog được dẫn từ tài liệu này. URL chính xác từng trang con chưa xác minh; không tự tạo URL.

| Nhóm | Nội dung cần bổ sung trước khi mở chức năng |
| --- | --- |
| Balance trial | Quyền key read-only thực tế cho Futures USER_DATA; timestamp/time unit, signing/canonical query, recvWindow, quota, authenticated error handling; xác minh không cần trading/transfer/withdrawal; các mode tài khoản được hỗ trợ |
| Account/Position | Single vs multi-assets USD valuation, margin và unrealized theo asset/mode; partial/zero-position semantics; timestamp units |
| Income/PnL | Bảng incomeType và dấu tiền; financial finality, tranId namespace (doc SDK typo trandId), response time unit; limit default/max và inclusive boundary/tie truncation; correlation tradeId/rp/n/funding/reversals |
| Capital | Deposit transferType/walletType, trạng thái credited và travel rule, id/txId uniqueness; withdrawal status đầy đủ/gross-net/fee/UTC format; offset/limit/retention/updates của bản ghi cũ |
| Universal transfer | type enum Spot/Futures và hai chiều, current/size base/default/max, tranId namespace và quan hệ Income TRANSFER; trạng thái final/reversal |
| Spot/Wallet | Asset balance composition, quoteAsset/default valuation và đơn vị; free/locked/freeze/withdrawing không cộng trùng; permissions key UI |
| WebSocket | Tài liệu ACCOUNT_UPDATE/ORDER_TRADE_UPDATE/listenKeyExpired và lifecycle hiện hành; authentication, E/T unit, partial updates, ordering/duplicate/gap/retention và REST replay/bootstrap correlation. Tải các trang event được dẫn từ user-data-streams ở trên; URL con chưa xác minh |

Chỉ có thể kiểm tra sau khi có client và được phép trial riêng: key permissions thật (không cần gửi key trong chat), response schema/mode của tài khoản thử, clock skew, header quotas, disconnect/reconnect và lịch sử ở biên pagination, đối soát Binance, latency/soak24h. Tất cả hiện **NOT VERIFIED**; không dùng một fixture mock để đánh dấu PASS.
