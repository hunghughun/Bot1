# Futures Balance V3 — official-document review, 07/11/2026 GMT+7

## Kiểm tra lại yêu cầu mới — 07/11/2026 GMT+7

**Chưa có nguồn hoặc môi trường mới để hoàn tất đối chiếu/API fixtures và chạy Windows.** Vendor vẫn chỉ có README intake,0 HTML/PDF chính thức. Đã lưu draft network revision3 thêm duy nhất `developers.binance.com`, giữ preset package_managers và cấu hình hiện có; runtime vẫn chưa áp dụng, không request lại host bị chặn. Cần review/apply trong Environment settings rồi kiểm tra runtime đã enforced cho host này; có thể thay bằng bản HTML/PDF chính thức được cung cấp.

Windows/Python3.14 probe mới exit2/**NOT TESTED**, executed0: máy hiện tại Linux/Python3.12.14, không có Windows interpreter/PowerShell. 221 PASS dưới đây là kết quả Linux trước đó, không phải Windows rerun mới. Không sửa fixture hoặc expected khi chưa có bằng chứng nguồn mới; hash mock SDK vẫn khớp metadata. Smoke-test có confirmation vẫn exit2/BLOCKED tại contract gate, chưa dùng credential hoặc truy vấn Binance, live_readonly khóa.

[Bằng chứng kiểm tra lại](test-reports/balance-readiness-recheck.json) · [Windows target probe mới](test-reports/balance-windows314-recheck.json). Điều kiện live còn thiếu: official docs/fixture tests; loại key/quyền read-only; reviewed live transport/auth/clock/timeout/quota; suite thực chạy trên Windows/Python3.14. Chưa đề xuất mở truy vấn thật.

---

**NOT VERIFIED** đối với tài liệu API chính thức. Khi bắt đầu giai đoạn này không có `docs/vendor/binance/`, cũng không tìm thấy HTML/PDF trong workspace. Hiện thư mục chỉ có README intake của dự án, không phải nguồn Binance. Host developers.binance.com vẫn không được policy cho phép; không gọi lại CONNECT403 hoặc đổi đường truy cập để bypass. Nguồn SDK pin ở phần dưới vẫn giữ giá trị SDK_ONLY.

[Review JSON](test-reports/balance-official-doc-review.json) ghi từng mục, nguồn/hash và blocker; [vendor intake](vendor/binance/README.md) ghi bản tài liệu cần cung cấp; [smoke-test](BALANCE-SMOKE-TEST.md) mô tả code và giới hạn.

| Mục Balance V3 | Có bằng chứng SDK đã pin | Đối chiếu HTML/PDF chính thức lần này |
| --- | --- | --- |
| GET /fapi/v3/balance | PASS SDK_ONLY, account_api method | NOT VERIFIED |
| Base https://fapi.binance.com | PASS SDK_ONLY, common constants | NOT VERIFIED |
| USER_DATA, key header, signed request | PASS SDK_ONLY; quyền key UI cụ thể chưa biết | NOT VERIFIED |
| recvWindow/timestamp/signature, key types | PASS SDK_ONLY; HMAC offline candidate đã test với OpenSSL/key giả | NOT VERIFIED cho official signing, encoding/bounds và loại key thật |
| Request weight5 | PASS SDK_ONLY; quota/reset/header không suy từ weight | NOT VERIFIED |
| Array/schema và 9 fields | PASS SDK_ONLY, annotations/mock | NOT VERIFIED requiredness/current server support |
| Tiền string, flag bool, last-update ms | PASS SDK_ONLY; NUMERIC-1 không sửa | NOT VERIFIED với toàn miền tài khoản/mode thực tế |
| Error codes, timeout/rate/retry rules | Common SDK đã đọc; smoke fake dừng trên auth/rate/server errors | NOT VERIFIED cho live behavior và giới hạn server |
| Khác biệt mapper/API docs | Không có tài liệu để so sánh; không tự suy ra khác biệt | NOT VERIFIED |
| Official API golden fixtures/tests | Không tạo fixture giả official; tiếp tục dùng mock SDK có provenance | NOT VERIFIED,0 official API fixtures/tests |

Mapper giữ nguyên local profile5 required fields; smoke yêu cầu đủ9/non-null để kiểm tra hoàn chỉnh. Unknown field/duplicate/nonfinite/missing không zero-fill. UpdateTime0/tương lai và ngoài numeric bounds bị từ chối theo policy local; không tuyên bố đó là quy tắc chính thức Binance. Không thay optionalness hoặc nới precision dựa trên tài liệu chưa có. Không cộng wallet+available/cross state, không post snapshot.

**Live vẫn khóa.** Smoke-test chỉ có command/gate, pure signing candidate và fake exchange; chưa có live transport/credential loader. Cờ xác nhận của operator không thay thế review. Active allowlist rỗng. Kết quả runtime offline mới nhất221/221 PASS; official-document/signing/permission và Windows còn NOT VERIFIED/NOT TESTED.

---

Phần dưới là inventory bằng chứng SDK của giai đoạn trước, giữ nguyên nguồn/commit/hash và phạm vi SDK_ONLY. Không phải kết quả đối chiếu mới của các API khác.

# Binance API Contract Matrix — SDK evidence / offline Balance

Xác minh nguồn ngày **2026-11-06T18:31:09.887090+00:00**. Repository chính thức: <https://github.com/binance/binance-connector-python>; commit **`f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179`**. Futures SDK **18.3.0**, Wallet **13.10.0**, Spot **13.5.0**. Chỉ đọc mã/tài liệu, không cài hoặc chạy SDK.

Nguồn SDK: **PASS** về truy xuất, commit, method/model/example/mock. Đối chiếu developers.binance.com: **NOT VERIFIED**; proxy CONNECT403 đã có bằng chứng ở giai đoạn trước, chính sách mạng không đổi, không truy cập lặp lại. SDK_ONLY không có nghĩa API đã ngừng hỗ trợ hay được kiểm chứng trên tài khoản thật.

Bằng chứng giữ tại [source-manifest.json](api-evidence/f75b4a52c5ae/source-manifest.json): mỗi file/excerpt có URL theo commit, dòng, SHA256 toàn file gốc và SHA256 bản giữ lại. [methods.json](api-evidence/f75b4a52c5ae/methods.json) lưu chữ ký/docstring/request call; [model-fields.json](api-evidence/f75b4a52c5ae/model-fields.json) lưu field/type/alias/description. [Ma trận JSON](test-reports/api-contract-matrix.json) là bản hiện hành; [proxy evidence](test-reports/adapter-doc-access.json) giữ nguyên lịch sử.

## Endpoint, bảo mật và quota theo SDK

Base F = `https://fapi.binance.com`; W/S = `https://api.binance.com`, lấy từ common-constants. Dưới đây là bằng chứng SDK_ONLY cho tất cả dòng, không phải kết quả request thật.

| Ưu tiên / chức năng | Method / path | Security / signing | Weight theo docstring | Kết quả mapping |
| --- | --- | --- | --- | --- |
| 1 Balance V3 | GET `/fapi/v3/balance` (F) | USER_DATA, signed | IP5 | PASS offline wallet/available snapshots |
| 2 Account V3 | GET `/fapi/v3/account` (F) | USER_DATA, signed | IP5 | NOT VERIFIED |
| 3 Income | GET `/fapi/v1/income` (F) | USER_DATA, signed | IP30 | NOT VERIFIED |
| 4 Position V3 | GET `/fapi/v3/positionRisk` (F) | USER_DATA, signed | IP5 | NOT VERIFIED |
| 5 Deposit | GET `/sapi/v1/capital/deposit/hisrec` (W) | USER_DATA, signed | IP1 | NOT VERIFIED |
| 6 Withdrawal | GET `/sapi/v1/capital/withdraw/history` (W) | USER_DATA, signed | UID18000; doc ghi 10 req/s | NOT VERIFIED |
| 7 Universal history | GET `/sapi/v1/asset/transfer` (W) | USER_DATA, signed | IP1 | NOT VERIFIED |
| 8 Spot account | GET `/api/v3/account` (S) | USER_DATA, signed | IP20 | NOT VERIFIED |
| 8 Wallet valuation | GET `/sapi/v1/asset/wallet/balance` (W) | USER_DATA, signed | IP60 | NOT VERIFIED |
| 8 Funding wallet query | POST `/sapi/v1/asset/get-funding-asset` (W) | USER_DATA, signed | IP1 | NOT VERIFIED; không allowlist |
| 9 Stream start / keepalive / close | POST / PUT / DELETE `/fapi/v1/listenKey` (F) | USER_STREAM; SDK không truyền is_signed=True | IP1 mỗi method | NOT VERIFIED; không allowlist |

USER_DATA/USER_STREAM là security type trong SDK, **không chứng minh quyền checkbox API Key cụ thể**. Common configuration đặt `X-MBX-APIKEY`; signed request thêm timestamp và signature, query keys snake_case→camelCase. SDK hỗ trợ time-unit header tùy chọn; thử nghiệm Balance sau này phải cố định ms hoặc fail-closed. Không suy ra phải bật Futures trading từ security type USER_DATA. Chưa có bằng chứng một key chỉ đọc theo UI đọc được từng nhóm tài khoản; dùng ma trận permission tách Futures snapshot / income / capital / transfer-history / Spot / stream, mặc định tất cả disabled.

Endpoint đang có trong SDK tại commit này; **trạng thái hỗ trợ/deprecation hiện hành trên máy chủ chưa xác minh**. Weight là chi phí request được ghi trong SDK, không chứng minh toàn bộ quota IP/UID/account, reset interval hoặc tier. Không tự điền rate-per-minute/limit defaults không có trong nguồn.

## Lỗi, retry và giới hạn chung

common-utils/errors mô tả HTTP400 BadRequest,401 Unauthorized,403 Forbidden,404 NotFound,418 RateLimitBan,429 TooManyRequests (retry_after),5xx ServerError; JSON `code`/`msg` giữ ý nghĩa lỗi server nhưng bảng numeric error code theo endpoint chưa xác minh. Proxy CONNECT403 là lỗi truy xuất tài liệu, không phải403 từ Binance authenticated API.

SDK should_retry_request cho GET/DELETE khi lỗi mạng và retry còn, hoặc500/502/503/504; DELETE không được phép trong trial này. Đây là hành vi SDK, không phải chính sách live đã triển khai. Đề xuất trial GET-only: retry hữu hạn, backoff+jitter, tôn trọng Retry-After, dừng khi418;401/403/schema/numeric không retry vô hạn và không tự tăng quyền; kiểm soát429 theo bằng chứng header còn thiếu. Phải budget từng nhóm và quarantine schema lỗi. Signer/clock, giới hạn recvWindow, time-unit/header/reset interval, endpoint-specific codes còn NOT VERIFIED.

## Request, response, identity, nghiệp vụ và mapping theo nguồn

### `futures_account_balance_v3` — futures_balance_v3

Nguồn đã đọc: [SDK method](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/api/account_api.py#L182), [bản lưu](api-evidence/f75b4a52c5ae/method-futures_account_balance_v3.txt). Truy xuất 2026-11-06T18:31:09.887090+00:00; mức OFFICIAL_SDK_ONLY. URL API do SDK trỏ tới, **chưa tải/đối chiếu**: <https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/account#futures-account-balance-v3>.

Request signature: `self, recv_window: Optional[int]=None`. Query wire camelCase theo common-utils; signing/header xem phần chung. Response model: `FuturesAccountBalanceV3Response`. Mọi field/alias/type/description được trích ở model-fields và appendix dưới; Optional/default None trong SDK không cho phép tự điền0.

Trường tài chính cần đọc: `balance`, `crossWalletBalance`, `crossUnPnl`, `availableBalance`, `maxWithdrawAmount`.

**Identity/correlation:** No native transaction ID. Local observation ID binds accountAlias/account/asset/poll_id/metric; body SHA retained separately. updateTime is last update, not acquisition time.

**Pagination/history:** Snapshot array; no pagination params in SDK. No history coverage.

**Nghiệp vụ / Internal Schema v1:** PASS: offline wallet/available BALANCE_SNAPSHOT only; cross values retained, not posted. Full API/permissions NOT VERIFIED.

### `account_information_v3` — futures_account

Nguồn đã đọc: [SDK method](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/api/account_api.py#L98), [bản lưu](api-evidence/f75b4a52c5ae/method-account_information_v3.txt). Truy xuất 2026-11-06T18:31:09.887090+00:00; mức OFFICIAL_SDK_ONLY. URL API do SDK trỏ tới, **chưa tải/đối chiếu**: <https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/account#account-information-v3>.

Request signature: `self, recv_window: Optional[int]=None`. Query wire camelCase theo common-utils; signing/header xem phần chung. Response model: `AccountInformationV3Response`. Mọi field/alias/type/description được trích ở model-fields và appendix dưới; Optional/default None trong SDK không cho phép tự điền0.

Trường tài chính cần đọc: `total*`, `availableBalance`, `maxWithdrawAmount`, `assets.*`, `positions.*`.

**Identity/correlation:** State snapshot only. Must not sum aggregate USD valuations with asset rows, or post balance deltas.

**Pagination/history:** Snapshot object; no paging in SDK.

**Nghiệp vụ / Internal Schema v1:** NOT VERIFIED: no mapper. Single-asset USDT versus multi-assets USD semantics require explicit unit/mode binding.

### `get_income_history` — futures_income

Nguồn đã đọc: [SDK method](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/api/account_api.py#L788), [bản lưu](api-evidence/f75b4a52c5ae/method-get_income_history.txt). Truy xuất 2026-11-06T18:31:09.887090+00:00; mức OFFICIAL_SDK_ONLY. URL API do SDK trỏ tới, **chưa tải/đối chiếu**: <https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/account#get-income-history>.

Request signature: `self, symbol: Optional[str]=None, income_type: Optional[GetIncomeHistoryIncomeTypeEnum]=None, start_time: Optional[int]=None, end_time: Optional[int]=None, limit: Optional[int]=None, recv_window: Optional[int]=None`. Query wire camelCase theo common-utils; signing/header xem phần chung. Response model: `GetIncomeHistoryResponse`. Mọi field/alias/type/description được trích ở model-fields và appendix dưới; Optional/default None trong SDK không cho phép tự điền0.

Trường tài chính cần đọc: `income`.

**Identity/correlation:** SDK doc says trandId unique within incomeType/user; model spelling tranId. Preserve exact integer tranId and tradeId string. Cross-source identity/sign/time-unit/reversal rules not verified.

**Pagination/history:** SDK: default last 7 days; retained last 3 months; inclusive startTime/endTime (ms); limit optional, no page param. Limit default/max and equal-timestamp truncation not verified.

**Nghiệp vụ / Internal Schema v1:** NOT VERIFIED: incomeType enum is not proof of cashflow sign, settlement/finality or cross-source correlation.

### `position_information_v3` — futures_positions

Nguồn đã đọc: [SDK method](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/api/trade_api.py#L1757), [bản lưu](api-evidence/f75b4a52c5ae/method-position_information_v3.txt). Truy xuất 2026-11-06T18:31:09.887090+00:00; mức OFFICIAL_SDK_ONLY. URL API do SDK trỏ tới, **chưa tải/đối chiếu**: <https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/trade#position-information-v3>.

Request signature: `self, symbol: Optional[str]=None, recv_window: Optional[int]=None`. Query wire camelCase theo common-utils; signing/header xem phần chung. Response model: `PositionInformationV3Response`. Mọi field/alias/type/description được trích ở model-fields và appendix dưới; Optional/default None trong SDK không cho phép tự điền0.

Trường tài chính cần đọc: `positionAmt`, `entryPrice`, `breakEvenPrice`, `markPrice`, `unRealizedProfit`, `liquidationPrice`, `isolatedMargin`, `notional`, `isolatedWallet`, `initialMargin`, `maintMargin`, `positionInitialMargin`, `openOrderInitialMargin`.

**Identity/correlation:** State by symbol/positionSide, not economic event ID. Positive long/negative short per model; bidNotional/askNotional marked ignore.

**Pagination/history:** SDK: only symbols with position/open orders; no paging params. Missing symbol not proof of closed event/history coverage.

**Nghiệp vụ / Internal Schema v1:** NOT VERIFIED: no PnL posting. Must not sum snapshot unrealizedProfit with realized income.

### `deposit_history` — deposit_history

Nguồn đã đọc: [SDK method](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/wallet/src/binance_sdk_wallet/rest_api/api/capital_api.py#L149), [bản lưu](api-evidence/f75b4a52c5ae/method-deposit_history.txt). Truy xuất 2026-11-06T18:31:09.887090+00:00; mức OFFICIAL_SDK_ONLY. URL API do SDK trỏ tới, **chưa tải/đối chiếu**: <https://developers.binance.com/en/docs/catalog/core-trading-wallet/api/rest-api/capital#deposit-history>.

Request signature: `self, include_source: Optional[bool]=None, coin: Optional[str]=None, status: Optional[DepositHistoryStatusEnum]=None, start_time: Optional[int]=None, end_time: Optional[int]=None, offset: Optional[int]=None, limit: Optional[int]=None, recv_window: Optional[int]=None, tx_id: Optional[str]=None`. Query wire camelCase theo common-utils; signing/header xem phần chung. Response model: `DepositHistoryResponse`. Mọi field/alias/type/description được trích ở model-fields và appendix dưới; Optional/default None trong SDK không cho phép tự điền0.

Trường tài chính cần đọc: `amount`.

**Identity/correlation:** Preserve id, txId, network, transferType, walletType. Model lacks explanatory transferType/walletType descriptions; do not borrow withdrawal meanings.

**Pagination/history:** SDK: default start 90 days ago/end now; explicit interval less than 90 days. offset/limit; default/max limit, total retention and same-timestamp boundary completeness not verified.

**Nghiệp vụ / Internal Schema v1:** NOT VERIFIED: status 0 pending/1 success/2 rejected/6 credited cannot withdraw/7 wrong/8 waiting confirmation per SDK doc. These do not alone prove external deposit or economic finality.

### `withdraw_history` — withdraw_history

Nguồn đã đọc: [SDK method](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/wallet/src/binance_sdk_wallet/rest_api/api/capital_api.py#L496), [bản lưu](api-evidence/f75b4a52c5ae/method-withdraw_history.txt). Truy xuất 2026-11-06T18:31:09.887090+00:00; mức OFFICIAL_SDK_ONLY. URL API do SDK trỏ tới, **chưa tải/đối chiếu**: <https://developers.binance.com/en/docs/catalog/core-trading-wallet/api/rest-api/capital#withdraw-history>.

Request signature: `self, coin: Optional[str]=None, withdraw_order_id: Optional[str]=None, status: Optional[int]=None, offset: Optional[int]=None, limit: Optional[int]=None, id_list: Optional[str]=None, start_time: Optional[int]=None, end_time: Optional[int]=None, recv_window: Optional[int]=None`. Query wire camelCase theo common-utils; signing/header xem phần chung. Response model: `WithdrawHistoryResponse`. Mọi field/alias/type/description được trích ở model-fields và appendix dưới; Optional/default None trong SDK không cho phép tự điền0.

Trường tài chính cần đọc: `amount`, `transactionFee`.

**Identity/correlation:** id is Binance withdrawal ID; txId distinct chain ID; withdrawOrderId optional. transferType 1 internal/0 external; walletType 1 Funding/0 Spot per model. Gross/net and fee-leg accounting not verified.

**Pagination/history:** SDK: default 90 days; interval less than 90 days; withdrawOrderId interval less than 7 days/default 7 days; offset default0, limit bound unknown; idList max45. network may be absent for old records.

**Nghiệp vụ / Internal Schema v1:** NOT VERIFIED: doc has incomplete/malformed status list; 6 completed per model. applyTime/completeTime are UTC strings, exact accepted format still needs official evidence.

### `query_user_universal_transfer_history` — universal_transfer_history

Nguồn đã đọc: [SDK method](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/wallet/src/binance_sdk_wallet/rest_api/api/asset_api.py#L735), [bản lưu](api-evidence/f75b4a52c5ae/method-query_user_universal_transfer_history.txt). Truy xuất 2026-11-06T18:31:09.887090+00:00; mức OFFICIAL_SDK_ONLY. URL API do SDK trỏ tới, **chưa tải/đối chiếu**: <https://developers.binance.com/en/docs/catalog/core-trading-wallet/api/rest-api/asset#query-user-universal-transfer-history>.

Request signature: `self, type: Union[str, None], start_time: Optional[int]=None, end_time: Optional[int]=None, current: Optional[int]=None, size: Optional[int]=None, from_symbol: Optional[QueryUserUniversalTransferHistoryFromSymbolEnum]=None, to_symbol: Optional[QueryUserUniversalTransferHistoryToSymbolEnum]=None, recv_window: Optional[int]=None`. Query wire camelCase theo common-utils; signing/header xem phần chung. Response model: `QueryUserUniversalTransferHistoryResponse`. Mọi field/alias/type/description được trích ở model-fields và appendix dưới; Optional/default None trong SDK không cho phép tự điền0.

Trường tài chính cần đọc: `rows.amount`.

**Identity/correlation:** Preserve rows.tranId as integer lexeme; no proven equality to income tranId. rows.type binds wallets only after enum/document review; not external cashflow.

**Pagination/history:** SDK: last 6 months, default last7 days; current/size params, base/default/max not described. Conditional isolated-margin fromSymbol/toSymbol.

**Nghiệp vụ / Internal Schema v1:** NOT VERIFIED: response total integer, rows status CONFIRMED/FAILED/PENDING. No posting until type direction and correlation proven. Same path POST must remain forbidden.

### `query_user_wallet_balance` — spot_funding_balances

Nguồn đã đọc: [SDK method](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/wallet/src/binance_sdk_wallet/rest_api/api/asset_api.py#L811), [bản lưu](api-evidence/f75b4a52c5ae/method-query_user_wallet_balance.txt). Truy xuất 2026-11-06T18:31:09.887090+00:00; mức OFFICIAL_SDK_ONLY. URL API do SDK trỏ tới, **chưa tải/đối chiếu**: <https://developers.binance.com/en/docs/catalog/core-trading-wallet/api/rest-api/asset#query-user-wallet-balance>.

Request signature: `self, quote_asset: Optional[str]=None, need_balance_detail: Optional[bool]=None, recv_window: Optional[int]=None`. Query wire camelCase theo common-utils; signing/header xem phần chung. Response model: `QueryUserWalletBalanceResponse`. Mọi field/alias/type/description được trích ở model-fields và appendix dưới; Optional/default None trong SDK không cho phép tự điền0.

Trường tài chính cần đọc: `balance`, `assetBalances.free`, `assetBalances.locked`, `assetBalances.freeze`, `assetBalances.withdrawing`, `assetBalances.btcValuation`.

**Identity/correlation:** Wallet valuation/state; walletName not ledger event ID. needBalanceDetail changes nested response. Quote valuation must not be relabelled USDT or added to per-asset balances.

**Pagination/history:** Snapshot array; quoteAsset/needBalanceDetail/recvWindow; no paging params.

**Nghiệp vụ / Internal Schema v1:** NOT VERIFIED: no mapper; currency/valuation and field composition need API-doc confirmation.

### `funding_wallet` — spot_funding_balances

Nguồn đã đọc: [SDK method](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/wallet/src/binance_sdk_wallet/rest_api/api/asset_api.py#L402), [bản lưu](api-evidence/f75b4a52c5ae/method-funding_wallet.txt). Truy xuất 2026-11-06T18:31:09.887090+00:00; mức OFFICIAL_SDK_ONLY. URL API do SDK trỏ tới, **chưa tải/đối chiếu**: <https://developers.binance.com/en/docs/catalog/core-trading-wallet/api/rest-api/asset#funding-wallet>.

Request signature: `self, asset: Optional[str]=None, need_btc_valuation: Optional[bool]=None, recv_window: Optional[int]=None`. Query wire camelCase theo common-utils; signing/header xem phần chung. Response model: `FundingWalletResponse`. Mọi field/alias/type/description được trích ở model-fields và appendix dưới; Optional/default None trong SDK không cho phép tự điền0.

Trường tài chính cần đọc: `free`, `locked`, `freeze`, `withdrawing`, `btcValuation`.

**Identity/correlation:** Funding state, NOT Spot free balance. No event ID.

**Pagination/history:** Snapshot array; asset/needBtcValuation/recvWindow; no paging params.

**Nghiệp vụ / Internal Schema v1:** NOT VERIFIED: SDK POST query, not allowlisted. Preserve field distinctions; do not infer free+locked equals all wallet balance.

### `get_account` — spot_funding_balances

Nguồn đã đọc: [SDK method](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/spot/src/binance_sdk_spot/rest_api/api/account_api.py#L235), [bản lưu](api-evidence/f75b4a52c5ae/method-get_account.txt). Truy xuất 2026-11-06T18:31:09.887090+00:00; mức OFFICIAL_SDK_ONLY. URL API do SDK trỏ tới, **chưa tải/đối chiếu**: <https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/account#get-account>.

Request signature: `self, omit_zero_balances: Optional[bool]=None, recv_window: Optional[float]=None`. Query wire camelCase theo common-utils; signing/header xem phần chung. Response model: `GetAccountResponse`. Mọi field/alias/type/description được trích ở model-fields và appendix dưới; Optional/default None trong SDK không cho phép tự điền0.

Trường tài chính cần đọc: `balances.free`, `balances.locked`, `commissionRates.*`.

**Identity/correlation:** Spot snapshot only; permissions/canTrade response does NOT certify the key UI grants. Account UID integer is not event ID.

**Pagination/history:** SDK: omitZeroBalances optional; Memory=>Database source. No pagination params.

**Nghiệp vụ / Internal Schema v1:** NOT VERIFIED: no Spot mapper. Do not combine raw Spot balances with aggregate quote valuations or Funding wallet.

### `start_user_data_stream` — futures_user_stream

Nguồn đã đọc: [SDK method](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/api/user_data_streams_api.py#L110), [bản lưu](api-evidence/f75b4a52c5ae/method-start_user_data_stream.txt). Truy xuất 2026-11-06T18:31:09.887090+00:00; mức OFFICIAL_SDK_ONLY. URL API do SDK trỏ tới, **chưa tải/đối chiếu**: <https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/user-data-streams#start-user-data-stream>.

Request signature: `self`. Query wire camelCase theo common-utils; signing/header xem phần chung. Response model: `StartUserDataStreamResponse`. Mọi field/alias/type/description được trích ở model-fields và appendix dưới; Optional/default None trong SDK không cho phép tự điền0.

Trường tài chính cần đọc: `ACCOUNT_UPDATE.a.B:wb,cw,bc`, `a.P:pa,ep,bep,cr,up,iw`, `ORDER_TRADE_UPDATE.o:n,rp,p,q,L,l,z,ap`.

**Identity/correlation:** ACCOUNT_UPDATE lacks a proven unique economic transaction ID. bc excludes PnL/commission; cr accumulated and pre-fee, not a new realized posting. ORDER_TRADE_UPDATE has i/t but link to REST income tradeId needs verified namespace/settlement rules.

**Pagination/history:** SDK lifecycle60min; snapshot+income+capital recovery needs overlap/retention/gap proofs. Event E/T timestamp units, ordering/duplicates and account binding not fully verified.

**Nghiệp vụ / Internal Schema v1:** NOT VERIFIED: lifecycle/events/correlation disabled. Create/renew/delete stream session is not a query and not included in snapshot-only allowlist.

### `keepalive_user_data_stream` — futures_user_stream

Nguồn đã đọc: [SDK method](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/api/user_data_streams_api.py#L70), [bản lưu](api-evidence/f75b4a52c5ae/method-keepalive_user_data_stream.txt). Truy xuất 2026-11-06T18:31:09.887090+00:00; mức OFFICIAL_SDK_ONLY. URL API do SDK trỏ tới, **chưa tải/đối chiếu**: <https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/user-data-streams#keepalive-user-data-stream>.

Request signature: `self`. Query wire camelCase theo common-utils; signing/header xem phần chung. Response model: `KeepaliveUserDataStreamResponse`. Mọi field/alias/type/description được trích ở model-fields và appendix dưới; Optional/default None trong SDK không cho phép tự điền0.

Trường tài chính cần đọc: `ACCOUNT_UPDATE.a.B:wb,cw,bc`, `a.P:pa,ep,bep,cr,up,iw`, `ORDER_TRADE_UPDATE.o:n,rp,p,q,L,l,z,ap`.

**Identity/correlation:** ACCOUNT_UPDATE lacks a proven unique economic transaction ID. bc excludes PnL/commission; cr accumulated and pre-fee, not a new realized posting. ORDER_TRADE_UPDATE has i/t but link to REST income tradeId needs verified namespace/settlement rules.

**Pagination/history:** SDK lifecycle60min; snapshot+income+capital recovery needs overlap/retention/gap proofs. Event E/T timestamp units, ordering/duplicates and account binding not fully verified.

**Nghiệp vụ / Internal Schema v1:** NOT VERIFIED: lifecycle/events/correlation disabled. Create/renew/delete stream session is not a query and not included in snapshot-only allowlist.

### `close_user_data_stream` — futures_user_stream

Nguồn đã đọc: [SDK method](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/api/user_data_streams_api.py#L33), [bản lưu](api-evidence/f75b4a52c5ae/method-close_user_data_stream.txt). Truy xuất 2026-11-06T18:31:09.887090+00:00; mức OFFICIAL_SDK_ONLY. URL API do SDK trỏ tới, **chưa tải/đối chiếu**: <https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/user-data-streams#close-user-data-stream>.

Request signature: `self`. Query wire camelCase theo common-utils; signing/header xem phần chung. Response model: `None`. Mọi field/alias/type/description được trích ở model-fields và appendix dưới; Optional/default None trong SDK không cho phép tự điền0.

Trường tài chính cần đọc: `ACCOUNT_UPDATE.a.B:wb,cw,bc`, `a.P:pa,ep,bep,cr,up,iw`, `ORDER_TRADE_UPDATE.o:n,rp,p,q,L,l,z,ap`.

**Identity/correlation:** ACCOUNT_UPDATE lacks a proven unique economic transaction ID. bc excludes PnL/commission; cr accumulated and pre-fee, not a new realized posting. ORDER_TRADE_UPDATE has i/t but link to REST income tradeId needs verified namespace/settlement rules.

**Pagination/history:** SDK lifecycle60min; snapshot+income+capital recovery needs overlap/retention/gap proofs. Event E/T timestamp units, ordering/duplicates and account binding not fully verified.

**Nghiệp vụ / Internal Schema v1:** NOT VERIFIED: lifecycle/events/correlation disabled. Create/renew/delete stream session is not a query and not included in snapshot-only allowlist.

## NUMERIC-1 và profile Balance

Tất cả trường tiền Balance là Optional StrictStr trong model, updateTime StrictInt (ms), marginAvailable StrictBool. V3 response kế thừa V2 inner và is_array()=True; không đọc nhầm response thành object. Profile local yêu cầu accountAlias/asset/balance/availableBalance/updateTime, array không rỗng, asset không trùng, account binding tường minh và không có unknown field. Đây là ràng buộc an toàn **chặt hơn SDK**, không tuyên bố Binance luôn trả đủ/không có field mới. Thiếu dữ liệu, timestamp0, timestamp tương lai, schema mới → quarantine cả batch, không zero-fill.

Balance/crossWalletBalance/crossUnPnl/availableBalance/maxWithdrawAmount đều qua NUMERIC-1 dưới dạng string; không float. Bound hiện giữ nguyên: ASCII≤96, coefficient≤48, fraction≤18, exponent±18, abs<1e30; precision128 và traps cũ giữ nguyên. SDK không công bố max magnitude/scale trong các model này: khả năng chấp nhận **mọi** tài khoản ngoài đời còn NOT VERIFIED. Dữ liệu vượt bound bị từ chối, không clamp/round. balance/available cho phép signed vì SDK không nêu nonnegative; không áp đặt miền dấu đoán trước.

Chỉ balance→wallet và availableBalance→available BALANCE_SNAPSHOT. Không lấy crossUnPnl làm tổng unrealized, không cộng wallet+available, không suy ra margin=wallet+crossUnPnl, không lấy maxWithdrawAmount làm tiền có thể tự rút. updateTime là last-update, received_time do acquisition context cung cấp; hai mốc không thay thế nhau và không chứng minh snapshot mới/fresh. Không chọn baseline opening tự động.

Các field string tài chính của income/position/capital/wallet có thể đi qua NUMERIC-1 nhưng **semantic compatibility chưa hoàn tất**: sign/unit/finality và max scale chưa đủ. Spot recv_window Optional[float] trong SDK là request time window, không phải tiền; chưa tích hợp SDK và không đưa giá trị tài chính qua float. Commission int trong Spot account là cấu hình commission, không tự coi là fee amount.

## Chống cộng trùng và ranh giới triển khai

- Balance/Account/Position/Spot/WS wallet fields là state observations, không cashflow. Snapshot cùng một số tiền tại nhiều endpoint không tạo ledger posting.
- Balance không có native transaction ID; giữ accountAlias, updateTime nguyên lexeme, raw SHA và local observation ID (account+alias+asset+durable poll_id+metric). Same poll/same bytes replay idempotent; changed bytes cùng poll quarantine, không overwrite. Poll mới là observation mới, không chứng minh sự kiện tài chính mới.
- Income realized/commission/funding có thể trùng thông tin ORDER_TRADE_UPDATE rp/n; transfer có thể xuất hiện Income TRANSFER, Universal Transfer và ACCOUNT_UPDATE. Không dùng amount/time gần nhau hoặc ID cùng số để hợp nhất. Chưa có namespace/correlation evidence nên các cashflow mapper và REST/WS link đều fail-closed.
- Withdrawal transferType=1 là internal theo model; không mặc định tất cả withdrawal là vốn rút ngoài. Deposit transferType thiếu mô tả tương ứng; không copy enum từ endpoint khác. Fee transactionFee cần bằng chứng gross/net trước khi hạch toán hai leg.
- ACCOUNT_UPDATE bc loại trừ PnL/commission; cr là accumulated realized pre-fee. Không post bc hoặc cr làm delta tiền tùy ý. Funding có thể nằm nhiều nguồn; unknown incomeType bị chặn cùng toàn bộ income mapper hiện tại.
- Pagination boundaries, retention recovery và lịch sử nguồn thật cho income/capital/stream còn NOT VERIFIED. Balance không có history API qua endpoint này; replay local snapshot không được gọi là Binance historical recovery.

## Appendix: response fields từ mã nguồn SDK

Đây là trích tĩnh annotation/Field alias, không chạy pydantic/SDK. Wrapper array dùng inheritance/is_array trong file nguồn; các field oneOf nội bộ router không phải wire fields. Description không có nghĩa là NOT DOCUMENTED trong SDK, không được tự bổ sung.

### `futures_account_balance_v3_response`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/models/futures_account_balance_v3_response.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-futures_account_balance_v3_response.txt)

Không có field khai báo trực tiếp; xem base class/is_array trong bản lưu.

### `futures_account_balance_v2_response_inner`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/models/futures_account_balance_v2_response_inner.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-futures_account_balance_v2_response_inner.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `accountAlias` | `Optional[StrictStr]` | Unique account alias. |
| `asset` | `Optional[StrictStr]` | Asset name. |
| `balance` | `Optional[StrictStr]` | Wallet balance. |
| `crossWalletBalance` | `Optional[StrictStr]` | Cross wallet balance. |
| `crossUnPnl` | `Optional[StrictStr]` | Unrealized PnL of cross positions. |
| `availableBalance` | `Optional[StrictStr]` | Available balance. |
| `maxWithdrawAmount` | `Optional[StrictStr]` | Maximum transferable/withdrawable amount. |
| `marginAvailable` | `Optional[StrictBool]` | Whether the asset can be used as margin in multi-assets mode. |
| `updateTime` | `Optional[StrictInt]` | Last update time in milliseconds. |

### `account_information_v3_response`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/models/account_information_v3_response.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-account_information_v3_response.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `totalInitialMargin` | `Optional[StrictStr]` | Total initial margin requirement. USDT only in single-asset mode; the sum of USD value of all cross positions/open order initial margin in multi-assets mode. |
| `totalMaintMargin` | `Optional[StrictStr]` | Total maintenance margin requirement. USDT only in single-asset mode; the sum of USD value of all cross positions maintenance margin in multi-assets mode. |
| `totalWalletBalance` | `Optional[StrictStr]` | Total wallet balance. USDT only in single-asset mode; USD-denominated in multi-assets mode. |
| `totalUnrealizedProfit` | `Optional[StrictStr]` | Total unrealized profit. USDT only in single-asset mode; USD-denominated in multi-assets mode. |
| `totalMarginBalance` | `Optional[StrictStr]` | Total margin balance. USDT only in single-asset mode; USD-denominated in multi-assets mode. |
| `totalPositionInitialMargin` | `Optional[StrictStr]` | Initial margin required for positions. USDT only in single-asset mode; the sum of USD value of all cross positions initial margin in multi-assets mode. |
| `totalOpenOrderInitialMargin` | `Optional[StrictStr]` | Initial margin required for open orders. USDT only in single-asset mode; USD-denominated in multi-assets mode. |
| `totalCrossWalletBalance` | `Optional[StrictStr]` | Cross wallet balance. USDT only in single-asset mode; USD-denominated in multi-assets mode. |
| `totalCrossUnPnl` | `Optional[StrictStr]` | Unrealized PnL for cross positions. USDT only in single-asset mode; USD-denominated in multi-assets mode. |
| `availableBalance` | `Optional[StrictStr]` | Available balance. USDT only in single-asset mode; USD-denominated in multi-assets mode. |
| `maxWithdrawAmount` | `Optional[StrictStr]` | Maximum transferable/withdrawable amount. USDT only in single-asset mode; a maximum virtual USD amount in multi-assets mode. |
| `assets` | `Optional[List[AccountInformationV3ResponseAssetsInner]]` | Asset-level account details. |
| `positions` | `Optional[List[AccountInformationV3ResponsePositionsInner]]` | Position details for symbols. |

### `account_information_v3_response_assets_inner`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/models/account_information_v3_response_assets_inner.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-account_information_v3_response_assets_inner.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `asset` | `Optional[StrictStr]` | Asset name. |
| `walletBalance` | `Optional[StrictStr]` | Wallet balance. |
| `unrealizedProfit` | `Optional[StrictStr]` | Unrealized profit. |
| `marginBalance` | `Optional[StrictStr]` | Margin balance. |
| `maintMargin` | `Optional[StrictStr]` | Maintenance margin requirement. |
| `initialMargin` | `Optional[StrictStr]` | Total initial margin requirement. |
| `positionInitialMargin` | `Optional[StrictStr]` | Initial margin required for positions. |
| `openOrderInitialMargin` | `Optional[StrictStr]` | Initial margin required for open orders. |
| `crossWalletBalance` | `Optional[StrictStr]` | Cross wallet balance. |
| `crossUnPnl` | `Optional[StrictStr]` | Unrealized PnL for cross positions. |
| `availableBalance` | `Optional[StrictStr]` | Available balance. |
| `maxWithdrawAmount` | `Optional[StrictStr]` | Maximum transferable/withdrawable amount. |
| `updateTime` | `Optional[StrictInt]` | Last update time in milliseconds. |

### `account_information_v3_response_positions_inner`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/models/account_information_v3_response_positions_inner.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-account_information_v3_response_positions_inner.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `symbol` | `Optional[StrictStr]` | Symbol. |
| `positionSide` | `Optional[StrictStr]` | Position side. |
| `positionAmt` | `Optional[StrictStr]` | Position quantity. |
| `unrealizedProfit` | `Optional[StrictStr]` | Unrealized profit. |
| `isolatedMargin` | `Optional[StrictStr]` | Isolated margin. |
| `notional` | `Optional[StrictStr]` | Position notional value. |
| `isolatedWallet` | `Optional[StrictStr]` | Isolated wallet balance. |
| `initialMargin` | `Optional[StrictStr]` | Initial margin requirement. |
| `maintMargin` | `Optional[StrictStr]` | Maintenance margin requirement. |
| `updateTime` | `Optional[StrictInt]` | Last update time in milliseconds. |

### `get_income_history_response`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/models/get_income_history_response.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-get_income_history_response.txt)

Không có field khai báo trực tiếp; xem base class/is_array trong bản lưu.

### `get_income_history_response_inner`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/models/get_income_history_response_inner.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-get_income_history_response_inner.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `symbol` | `Optional[StrictStr]` | trade symbol, if existing |
| `incomeType` | `Optional[StrictStr]` | income type |
| `income` | `Optional[StrictStr]` | income amount |
| `asset` | `Optional[StrictStr]` | income asset |
| `info` | `Optional[StrictStr]` | extra information |
| `time` | `Optional[StrictInt]` | Time. |
| `tranId` | `Optional[StrictInt]` | transaction id |
| `tradeId` | `Optional[StrictStr]` | trade id, if existing |

### `position_information_v3_response_inner`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/models/position_information_v3_response_inner.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-position_information_v3_response_inner.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `symbol` | `Optional[StrictStr]` | symbol |
| `positionSide` | `Optional[StrictStr]` | position side |
| `positionAmt` | `Optional[StrictStr]` | position amount, positive for long, negative for short |
| `entryPrice` | `Optional[StrictStr]` | entry price |
| `breakEvenPrice` | `Optional[StrictStr]` | break-even price |
| `markPrice` | `Optional[StrictStr]` | current mark price |
| `unRealizedProfit` | `Optional[StrictStr]` | unrealized profit |
| `liquidationPrice` | `Optional[StrictStr]` | liquidation price |
| `isolatedMargin` | `Optional[StrictStr]` | isolated margin |
| `notional` | `Optional[StrictStr]` | notional value of position |
| `marginAsset` | `Optional[StrictStr]` | margin asset |
| `isolatedWallet` | `Optional[StrictStr]` | isolated wallet (if isolated position) |
| `initialMargin` | `Optional[StrictStr]` | initial margin required with current mark price |
| `maintMargin` | `Optional[StrictStr]` | maintenance margin required |
| `positionInitialMargin` | `Optional[StrictStr]` | initial margin required for positions with current mark price |
| `openOrderInitialMargin` | `Optional[StrictStr]` | initial margin required for open orders with current mark price |
| `adl` | `Optional[StrictInt]` | auto-deleverage ranking |
| `bidNotional` | `Optional[StrictStr]` | ignore |
| `askNotional` | `Optional[StrictStr]` | ignore |
| `updateTime` | `Optional[StrictInt]` | update time |

### `deposit_history_response_inner`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/wallet/src/binance_sdk_wallet/rest_api/models/deposit_history_response_inner.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-deposit_history_response_inner.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `id` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `amount` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `coin` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `network` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `status` | `Optional[StrictInt]` | NOT DOCUMENTED |
| `address` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `addressTag` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `txId` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `insertTime` | `Optional[StrictInt]` | NOT DOCUMENTED |
| `completeTime` | `Optional[StrictInt]` | represents deposit completion datetime, available for deposits after 6-Mar-2025. |
| `transferType` | `Optional[StrictInt]` | NOT DOCUMENTED |
| `confirmTimes` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `unlockConfirm` | `Optional[StrictInt]` | NOT DOCUMENTED |
| `walletType` | `Optional[StrictInt]` | NOT DOCUMENTED |
| `travelRuleStatus` | `Optional[StrictInt]` | 0: travel rule not required OR info already provided and funds ready to use, 1: travel rule required to provide deposit info |

### `withdraw_history_response_inner`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/wallet/src/binance_sdk_wallet/rest_api/models/withdraw_history_response_inner.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-withdraw_history_response_inner.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `id` | `Optional[StrictStr]` | Withdrawal id in Binance |
| `amount` | `Optional[StrictStr]` | withdrawal amount |
| `transactionFee` | `Optional[StrictStr]` | transaction fee |
| `coin` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `status` | `Optional[StrictInt]` | NOT DOCUMENTED |
| `address` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `txId` | `Optional[StrictStr]` | withdrawal transaction id |
| `applyTime` | `Optional[StrictStr]` | UTC time |
| `network` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `transferType` | `Optional[StrictInt]` | 1 for internal transfer, 0 for external transfer |
| `withdrawOrderId` | `Optional[StrictStr]` | will not be returned if there's no withdrawOrderId for this withdraw. |
| `info` | `Optional[StrictStr]` | reason for withdrawal failure |
| `confirmNo` | `Optional[StrictInt]` | confirm times for withdraw |
| `walletType` | `Optional[StrictInt]` | 1: Funding Wallet 0:Spot Wallet |
| `txKey` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `completeTime` | `Optional[StrictStr]` | complete UTC time when user's asset is deduct from withdrawing, only if status =  6(success) |

### `query_user_universal_transfer_history_response`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/wallet/src/binance_sdk_wallet/rest_api/models/query_user_universal_transfer_history_response.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-query_user_universal_transfer_history_response.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `total` | `Optional[StrictInt]` | NOT DOCUMENTED |
| `rows` | `Optional[List[QueryUserUniversalTransferHistoryResponseRowsInner]]` | NOT DOCUMENTED |

### `query_user_universal_transfer_history_response_rows_inner`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/wallet/src/binance_sdk_wallet/rest_api/models/query_user_universal_transfer_history_response_rows_inner.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-query_user_universal_transfer_history_response_rows_inner.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `asset` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `amount` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `type` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `status` | `Optional[StrictStr]` | status: CONFIRMED / FAILED / PENDING |
| `tranId` | `Optional[StrictInt]` | NOT DOCUMENTED |
| `timestamp` | `Optional[StrictInt]` | NOT DOCUMENTED |

### `funding_wallet_response_inner`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/wallet/src/binance_sdk_wallet/rest_api/models/funding_wallet_response_inner.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-funding_wallet_response_inner.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `asset` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `free` | `Optional[StrictStr]` | avalible balance |
| `locked` | `Optional[StrictStr]` | locked asset |
| `freeze` | `Optional[StrictStr]` | freeze asset |
| `withdrawing` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `btcValuation` | `Optional[StrictStr]` | NOT DOCUMENTED |

### `query_user_wallet_balance_response_inner`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/wallet/src/binance_sdk_wallet/rest_api/models/query_user_wallet_balance_response_inner.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-query_user_wallet_balance_response_inner.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `activate` | `Optional[StrictBool]` | NOT DOCUMENTED |
| `balance` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `walletName` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `assetBalances` | `Optional[List[QueryUserWalletBalanceResponseInnerAssetBalancesInner]]` | Per-asset balance detail for this wallet. Only present when `needBalanceDetail=true` is passed; omitted entirely otherwise. |

### `get_account_response`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/spot/src/binance_sdk_spot/rest_api/models/get_account_response.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-get_account_response.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `makerCommission` | `Optional[StrictInt]` | NOT DOCUMENTED |
| `takerCommission` | `Optional[StrictInt]` | NOT DOCUMENTED |
| `buyerCommission` | `Optional[StrictInt]` | NOT DOCUMENTED |
| `sellerCommission` | `Optional[StrictInt]` | NOT DOCUMENTED |
| `commissionRates` | `Optional[GetAccountResponseCommissionRates]` | NOT DOCUMENTED |
| `canTrade` | `Optional[StrictBool]` | NOT DOCUMENTED |
| `canWithdraw` | `Optional[StrictBool]` | NOT DOCUMENTED |
| `canDeposit` | `Optional[StrictBool]` | NOT DOCUMENTED |
| `brokered` | `Optional[StrictBool]` | NOT DOCUMENTED |
| `requireSelfTradePrevention` | `Optional[StrictBool]` | NOT DOCUMENTED |
| `preventSor` | `Optional[StrictBool]` | NOT DOCUMENTED |
| `updateTime` | `Optional[StrictInt]` | NOT DOCUMENTED |
| `accountType` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `balances` | `Optional[List[GetAccountResponseBalancesInner]]` | NOT DOCUMENTED |
| `permissions` | `Optional[List[StrictStr]]` | NOT DOCUMENTED |
| `uid` | `Optional[StrictInt]` | NOT DOCUMENTED |

### `get_account_response_balances_inner`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/spot/src/binance_sdk_spot/rest_api/models/get_account_response_balances_inner.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-get_account_response_balances_inner.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `asset` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `free` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `locked` | `Optional[StrictStr]` | NOT DOCUMENTED |

### `user_data_stream_events_response`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/websocket_streams/models/user_data_stream_events_response.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-user_data_stream_events_response.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `oneof_schema_1_validator` | `Optional[AccountConfigUpdate]` | NOT DOCUMENTED |
| `oneof_schema_2_validator` | `Optional[AccountUpdate]` | NOT DOCUMENTED |
| `oneof_schema_3_validator` | `Optional[AlgoUpdate]` | NOT DOCUMENTED |
| `oneof_schema_4_validator` | `Optional[ConditionalOrderTriggerReject]` | NOT DOCUMENTED |
| `oneof_schema_5_validator` | `Optional[GridUpdate]` | NOT DOCUMENTED |
| `oneof_schema_6_validator` | `Optional[ListenKeyExpired]` | NOT DOCUMENTED |
| `oneof_schema_7_validator` | `Optional[MarginCall]` | NOT DOCUMENTED |
| `oneof_schema_8_validator` | `Optional[OrderTradeUpdate]` | NOT DOCUMENTED |
| `oneof_schema_9_validator` | `Optional[StrategyUpdate]` | NOT DOCUMENTED |
| `oneof_schema_10_validator` | `Optional[TradeLite]` | NOT DOCUMENTED |
| `actual_instance` | `Optional[Union[AccountConfigUpdate, AccountUpdate, AlgoUpdate, ConditionalOrderTriggerReject, GridUpdate, ListenKeyExpired, MarginCall, OrderTradeUpdate, StrategyUpdate, TradeLite]]` | NOT DOCUMENTED |
| `one_of_schemas` | `Set[str]` | NOT DOCUMENTED |
| `discriminator_value_class_map` | `Dict[str, str]` | NOT DOCUMENTED |

### `account_update`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/websocket_streams/models/account_update.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-account_update.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `E` | `Optional[StrictInt]` | Event Time |
| `T` | `Optional[StrictInt]` | Transaction |
| `a` | `Optional[AccountUpdateA]` | NOT DOCUMENTED |

### `account_update_a`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/websocket_streams/models/account_update_a.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-account_update_a.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `m` | `Optional[StrictStr]` | Event reason type |
| `B` | `Optional[List[AccountUpdateABInner]]` | Balances |
| `P` | `Optional[List[AccountUpdateAPInner]]` | NOT DOCUMENTED |
| `S` | `Optional[StrictStr]` | Symbol associated with FUNDING_FEE event |

### `account_update_ab_inner`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/websocket_streams/models/account_update_ab_inner.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-account_update_ab_inner.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `a` | `Optional[StrictStr]` | Asset |
| `wb` | `Optional[StrictStr]` | Wallet Balance |
| `cw` | `Optional[StrictStr]` | Cross Wallet Balance |
| `bc` | `Optional[StrictStr]` | Balance Change except PnL and Commission |

### `account_update_ap_inner`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/websocket_streams/models/account_update_ap_inner.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-account_update_ap_inner.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `s` | `Optional[StrictStr]` | Symbol |
| `pa` | `Optional[StrictStr]` | Position Amount |
| `ep` | `Optional[StrictStr]` | Entry Price |
| `bep` | `Optional[StrictStr]` | Breakeven Price |
| `cr` | `Optional[StrictStr]` | (Pre-fee) Accumulated Realized |
| `up` | `Optional[StrictStr]` | Unrealized PnL |
| `mt` | `Optional[StrictStr]` | Margin Type |
| `iw` | `Optional[StrictStr]` | Isolated Wallet (if isolated position) |
| `ps` | `Optional[StrictStr]` | Position Side |

### `order_trade_update`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/websocket_streams/models/order_trade_update.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-order_trade_update.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `E` | `Optional[StrictInt]` | Event Time |
| `T` | `Optional[StrictInt]` | Transaction Time |
| `o` | `Optional[OrderTradeUpdateO]` | NOT DOCUMENTED |

### `order_trade_update_o`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/websocket_streams/models/order_trade_update_o.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-order_trade_update_o.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `s` | `Optional[StrictStr]` | Symbol |
| `c` | `Optional[StrictStr]` | Client Order Id |
| `S` | `Optional[StrictStr]` | Side |
| `o` | `Optional[StrictStr]` | Order Type |
| `f` | `Optional[StrictStr]` | Time in Force |
| `q` | `Optional[StrictStr]` | Original Quantity |
| `p` | `Optional[StrictStr]` | Original Price |
| `ap` | `Optional[StrictStr]` | Average Price |
| `sp` | `Optional[StrictStr]` | Stop Price. Please ignore with TRAILING_STOP_MARKET order |
| `x` | `Optional[StrictStr]` | Execution Type |
| `X` | `Optional[StrictStr]` | Order Status |
| `i` | `Optional[StrictInt]` | Order Id |
| `M` | `Optional[StrictStr]` | modifyId, only pushed for AMENDMENT (order modification) events when a modifyId was provided in the request |
| `l` | `Optional[StrictStr]` | Order Last Filled Quantity |
| `z` | `Optional[StrictStr]` | Order Filled Accumulated Quantity |
| `L` | `Optional[StrictStr]` | Last Filled Price |
| `N` | `Optional[StrictStr]` | Commission Asset |
| `n` | `Optional[StrictStr]` | Commission |
| `T` | `Optional[StrictInt]` | Order Trade Time |
| `t` | `Optional[StrictInt]` | Trade Id |
| `b` | `Optional[StrictStr]` | Bids Notional |
| `a` | `Optional[StrictStr]` | Ask Notional |
| `m` | `Optional[StrictBool]` | Is this trade the maker side? |
| `R` | `Optional[StrictBool]` | Is this reduce only |
| `wt` | `Optional[StrictStr]` | Stop Price Working Type |
| `ot` | `Optional[StrictStr]` | Original Order Type |
| `ps` | `Optional[StrictStr]` | Position Side |
| `cp` | `Optional[StrictBool]` | If Close-All, pushed with conditional order |
| `AP` | `Optional[StrictStr]` | Activation Price, only pushed with TRAILING_STOP_MARKET order |
| `cr` | `Optional[StrictStr]` | Callback Rate, only pushed with TRAILING_STOP_MARKET order |
| `pP` | `Optional[StrictBool]` | If price protection is turned on |
| `si` | `Optional[StrictInt]` | ignore |
| `ss` | `Optional[StrictInt]` | ignore |
| `rp` | `Optional[StrictStr]` | Realized Profit of the trade |
| `V` | `Optional[StrictStr]` | STP mode |
| `pm` | `Optional[StrictStr]` | Price match mode |
| `gtd` | `Optional[StrictInt]` | TIF GTD order auto cancel time |
| `er` | `Optional[StrictStr]` | Expiry Reason |

### `position_information_v3_response`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/models/position_information_v3_response.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-position_information_v3_response.txt)

Không có field khai báo trực tiếp; xem base class/is_array trong bản lưu.

### `start_user_data_stream_response`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/models/start_user_data_stream_response.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-start_user_data_stream_response.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `listenKey` | `Optional[StrictStr]` | NOT DOCUMENTED |

### `keepalive_user_data_stream_response`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/derivatives_trading_usds_futures/src/binance_sdk_derivatives_trading_usds_futures/rest_api/models/keepalive_user_data_stream_response.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-keepalive_user_data_stream_response.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `listenKey` | `Optional[StrictStr]` | NOT DOCUMENTED |

### `deposit_history_response`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/wallet/src/binance_sdk_wallet/rest_api/models/deposit_history_response.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-deposit_history_response.txt)

Không có field khai báo trực tiếp; xem base class/is_array trong bản lưu.

### `withdraw_history_response`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/wallet/src/binance_sdk_wallet/rest_api/models/withdraw_history_response.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-withdraw_history_response.txt)

Không có field khai báo trực tiếp; xem base class/is_array trong bản lưu.

### `funding_wallet_response`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/wallet/src/binance_sdk_wallet/rest_api/models/funding_wallet_response.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-funding_wallet_response.txt)

Không có field khai báo trực tiếp; xem base class/is_array trong bản lưu.

### `query_user_wallet_balance_response`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/wallet/src/binance_sdk_wallet/rest_api/models/query_user_wallet_balance_response.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-query_user_wallet_balance_response.txt)

Không có field khai báo trực tiếp; xem base class/is_array trong bản lưu.

### `query_user_wallet_balance_response_inner_asset_balances_inner`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/wallet/src/binance_sdk_wallet/rest_api/models/query_user_wallet_balance_response_inner_asset_balances_inner.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-query_user_wallet_balance_response_inner_asset_balances_inner.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `asset` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `assetName` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `free` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `locked` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `freeze` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `withdrawing` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `btcValuation` | `Optional[StrictStr]` | NOT DOCUMENTED |

### `get_account_response_commission_rates`

[Nguồn](https://github.com/binance/binance-connector-python/blob/f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179/clients/spot/src/binance_sdk_spot/rest_api/models/get_account_response_commission_rates.py#L1) · [bản lưu](api-evidence/f75b4a52c5ae/model-get_account_response_commission_rates.txt)

| Wire alias / tên field | Annotation SDK | Description SDK |
| --- | --- | --- |
| `maker` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `taker` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `buyer` | `Optional[StrictStr]` | NOT DOCUMENTED |
| `seller` | `Optional[StrictStr]` | NOT DOCUMENTED |

## Những nguồn còn thiếu

Xem [MISSING-API-SOURCES.md](MISSING-API-SOURCES.md) cho URL và nội dung cần xuất thủ công. Không cần tải lại GitHub SDK: đã có bản commit/hash. Không yêu cầu API Key/Secret/Token hoặc sao kê thật.

**Allowlist hoạt động vẫn rỗng.** GET Balance là candidate query đã đọc từ SDK, chưa cấp quyền gọi mạng; trial chỉ có kế hoạch inert ở balance-trial-plan.json.
