# Futures Balance V3 readiness — 07/11/2026 GMT+7

## Kiểm tra lại yêu cầu mới — 07/11/2026 GMT+7

**Chưa có nguồn hoặc môi trường mới để hoàn tất đối chiếu/API fixtures và chạy Windows.** Vendor vẫn chỉ có README intake,0 HTML/PDF chính thức. Đã lưu draft network revision3 thêm duy nhất `developers.binance.com`, giữ preset package_managers và cấu hình hiện có; runtime vẫn chưa áp dụng, không request lại host bị chặn. Cần review/apply trong Environment settings rồi kiểm tra runtime đã enforced cho host này; có thể thay bằng bản HTML/PDF chính thức được cung cấp.

Windows/Python3.14 probe mới exit2/**NOT TESTED**, executed0: máy hiện tại Linux/Python3.12.14, không có Windows interpreter/PowerShell. 221 PASS dưới đây là kết quả Linux trước đó, không phải Windows rerun mới. Không sửa fixture hoặc expected khi chưa có bằng chứng nguồn mới; hash mock SDK vẫn khớp metadata. Smoke-test có confirmation vẫn exit2/BLOCKED tại contract gate, chưa dùng credential hoặc truy vấn Binance, live_readonly khóa.

[Bằng chứng kiểm tra lại](test-reports/balance-readiness-recheck.json) · [Windows target probe mới](test-reports/balance-windows314-recheck.json). Điều kiện live còn thiếu: official docs/fixture tests; loại key/quyền read-only; reviewed live transport/auth/clock/timeout/quota; suite thực chạy trên Windows/Python3.14. Chưa đề xuất mở truy vấn thật.

---

**Chưa đủ điều kiện cho người vận hành chạy truy vấn Binance thật.** Đã chuẩn bị smoke-test riêng ở mức offline và chạy **221/221 runtime tests PASS,0 FAIL**. Tài liệu HTML/PDF chính thức được nêu trong yêu cầu chưa có trong workspace; không thay bằng SDK để tuyên bố đối chiếu API hoàn tất.

## Trả lời5 kết luận bắt buộc

| Câu hỏi | Kết quả và bằng chứng |
| --- | --- |
| 1. Futures Balance V3 đã đối chiếu tài liệu chính thức chưa? | **NOT VERIFIED**. Đầu giai đoạn không tồn tại docs/vendor/binance và không tìm thấy HTML/PDF trong workspace. Hiện chỉ có README intake do dự án tạo. Policy host vẫn bị chặn; không lặp lại CONNECT403. [Review JSON](test-reports/balance-official-doc-review.json) |
| 2. Mapper đã hoàn thành positive contract tests chưa? | **PASS ở mức SDK offline**:39 Balance tests, trong đó11 positive/provenance/numeric tests, dùng1 mock copy từ SDK chính thức. **NOT VERIFIED ở mức official API docs**:0 document-based golden fixtures/tests, không gán mock SDK thành API example |
| 3. Smoke-test chỉ giới hạn một endpoint đọc không? | **PASS cho candidate/offline guard**: GET https://fapi.binance.com/fapi/v3/balance, fixed method/base/path, không arbitrary query/redirect/action; một attempt trong fake harness. **NOT VERIFIED cho live client**, chưa triển khai; active allowlist rỗng, nhánh live luôn bị chặn |
| 4. Đủ điều kiện chạy trên Windows với API Key READ-ONLY chưa? | **CHƯA**. Thiếu docs/official signing/key scopes và live client; Windows/Python3.14 **NOT TESTED** vì môi trường chỉ Linux/Python3.12.14. Không dùng kết quả Linux để suy Windows PASS |
| 5. Còn điểm chặn kết nối thật? | Có: official Balance/base/auth/signing/limits/errors, golden API fixture/tests, actual key type/read-only scope verification, reviewed credential provider/transport/TLS/clock/timeout/quota và Windows execution evidence |

Không có FAIL còn mở trong suite runtime hiện tại. Các mục chưa có bằng chứng là NOT VERIFIED/NOT TESTED và vẫn chặn live. Không đề xuất mở thử số dư thật cho đến khi mọi điều kiện bắt buộc đạt. Các nhóm Income/PnL, Deposit/Withdrawal/Transfer/Spot và WebSocket giữ nguyên trạng thái NOT VERIFIED của giai đoạn trước; không triển khai thêm ở giai đoạn này.

## Kết quả thực chạy

Command `python scripts/run_adapter_tests.py`, Python3.12.14/Linux, socket/DNS guard bật ở parent và Python subprocess. [JSON từng case](test-reports/adapter-offline-tests.json), [log](test-reports/adapter-offline-tests.log).

| Nhóm thực thi | PASS | FAIL | Phạm vi |
| --- | --- | --- | --- |
| Core regression cũ |124|0|Giữ nguyên core và test body/expected |
| Adapter foundation cũ |29|0|Parser/gates/quarantine/generic policies |
| Balance SDK contract/reliability cũ |39|0|SDK provenance, positive/negative mapping, source identity, isolated snapshots, replay,2 process crashes trước/sau commit |
| Smoke preparation mới |29|0|SDK candidate HMAC/route, input/redaction, fake timeout/error-stop/single-attempt, full field inspection và CLI live block |
| **Tổng runtime** |**221**|**0**|skipped0; không gồm kiểm thử live hoặc Windows |

Smoke command --plan và --offline-fixture được chạy thực, exit0 và summary OFFLINE_SDK_PROFILE_ONLY, không in số dư/alias. Tests gọi nhánh --live có/không confirmation đều exit2/BLOCKED, không request/credential load. Windows target probe `python scripts/check_compatibility.py --require-windows --require-python314 --output docs/test-reports/balance-smoke-windows314.json` exit2/NOT TESTED: thiếu Windows và CPython3.14; python3.14/pwsh/powershell không có sẵn. [Target evidence](test-reports/balance-smoke-windows314.json).

221 runtime PASS không chứng minh quyền key thật, signing hiện hành, server quota, đối soát Binance, timeout trên socket thật hoặc Windows hoạt động. Coverage nghiệp vụ core23/40 test cases và11/16 tình huống không được tự nâng vì thêm29 unit tests. Giai đoạn này không có test runtime FAIL rồi sửa expected; tất cả192 test cũ giữ nguyên.

## Nguồn và đối chiếu còn thiếu

SDK chính thức đã pin từ giai đoạn trước: repository https://github.com/binance/binance-connector-python, commit f75b4a52c5aebf52b1c6ad671b0ce53b96f8e179, Futures18.3.0; [manifest69 file/excerpt](api-evidence/f75b4a52c5ae/source-manifest.json). Nguồn SDK giữ nguyên SHA và không chạy/cài SDK. Signing candidate tham chiếu common-utils hmac_hashing/get_signature/encoded_string/send_request và common-configuration cho API-key header.

Nguồn chính thức cần đối chiếu: https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/account#futures-account-balance-v3. [Proxy evidence cũ](test-reports/adapter-doc-access.json) là CONNECT403 trước khi nhận nội dung target; không là auth403 của Binance. Network policy hiện tại restricted/enforced không cho host này, không đổi từ lần trước; không request lặp hoặc bypass.

Không thể kết luận khác biệt mapper/API khi chưa đọc được tài liệu API. Các policy local đã xác định được ghi rõ, không giả làm API contract: mapper yêu cầu5 field dù SDK Optional; smoke inspection yêu cầu đủ9/non-null; reject unknown/duplicate/empty/timestamp0/future; NUMERIC-1 bounds và local recvWindow1..5000ms không phải giới hạn Binance đã xác minh. Mapper cũ không bị sửa/nới miền theo suy đoán.

Cần HTML/PDF đầy đủ kèm URL/ngày từ trình duyệt ở [docs/vendor/binance/README.md](vendor/binance/README.md). README chỉ là hướng dẫn tiếp nhận, không có dữ liệu Binance và không tự mở gate. Cần cả Balance section, base/security/signing/parameters, errors/rate limits, read-only permissions và changelog liên quan; không chỉ endpoint example. Chi tiết từng hạng mục ở [API-CONTRACT-MATRIX.md](API-CONTRACT-MATRIX.md) và [official review JSON](test-reports/balance-official-doc-review.json).

## Smoke-test đã chuẩn bị và giới hạn

Code mới: [smoke.py](../src/bot1/adapters/binance/smoke.py), [balance-smoke-test.py](../scripts/balance-smoke-test.py), [29 tests](../tests/adapter_offline/test_balance_smoke.py). Hướng dẫn chi tiết [BALANCE-SMOKE-TEST.md](BALANCE-SMOKE-TEST.md).

- Candidate route cố định GET /fapi/v3/balance ở base chính thức theo SDK. Không có CLI option chọn method/url/path/db/token; cấm tham số lạ và không echo input bị từ chối.
- Nhánh live kiểm tra confirmation tường minh, key-type và require_verified **trước** credential/signing/network/write. Cờ --confirm-readonly không xác minh quyền và không vượt review gate. Chưa có live transport/credential loader; không đòi hoặc dùng key thật.
- HMAC-SHA256 hex candidate chỉ thuần offline với key tổng hợp, oracle OpenSSL độc lập; không log key/secret/signature/query/body. Key type phải khai báo HMAC, RSA/Ed25519/unknown dừng và không fallback. **Official signing compatibility và loại key thực tế NOT VERIFIED**.
- Fake exchange nhận timeout≤30000ms, response cap1MiB; một attempt kể cả lỗi, không tự polling/retry. Auth/permission401/403 dừng, không nâng quyền.418/429 dừng, không retry; redirect/5xx/transport error dừng. Đây chưa là network timeout hoặc quota/cooldown liên tiến trình live.
- Full smoke inspection validate asset, balance, availableBalance, crossWalletBalance, crossUnPnl, maxWithdrawAmount, marginAvailable, updateTime và accountAlias. Test mọi trường tiền với tiny/negative/zero/max precision/NaN/Inf/overflow/type; missing/null/unknown/duplicate/malformed reject, không zero-fill. Giữ trị string Decimal, không float hoặc round.
- Chỉ wallet/available snapshots; không cashflow/opening/financial ledger. Không coi crossUnPnl là total unrealized/margin. CLI summary chỉ counts/codes; stateless replay không ghi file/DB, không Telegram. SnapshotSandbox riêng và crash/restart tests cũ vẫn PASS, không sửa core để nối live.

Kế hoạch và fixture SDK hiện hành giữ network=false/live_readonly=false/allowlist=[]; không tuyên bố credential thực là read-only chỉ vì operator xác nhận hoặc một GET thành công. Khi thiếu quyền/schema không tương thích phải dừng và báo phần chưa hỗ trợ, không bật trading/transfer/withdrawal.

## File thay đổi và điều kiện chuyển tiếp

[balance-smoke-change-manifest.json](test-reports/balance-smoke-change-manifest.json) ghi từng file thêm/sửa, SHA trước/sau, protected-file checks. Thêm module/lệnh/tests, docs intake/hướng dẫn và kết quả review/compatibility; cập nhật runner, readiness, matrix và README. Không sửa Skill/reference/audit cũ, NUMERIC-1, mapper/store/safety/core hoặc192 test body/expected.

Chỉ khi tài liệu được cung cấp và review, official golden tests đạt, quyền/key type rõ, live client hoàn chỉnh và Windows/Python3.14 đã thực chạy, mới đề xuất operator thử một snapshot bằng key READ-ONLY trực tiếp trên máy. Vẫn cần xác nhận một lần; không ledger chính/Telegram/polling liên tục. Hiện **không có credential được nạp, không query Binance, không Telegram/VPS, không mở live**.
