# Bot 1 Offline Core — Báo cáo triển khai

Đây là báo cáo **implementation đã chạy**, không dùng PASS của checker tài liệu. Python 3.12.14, Linux; runtime chuẩn Python, SQLite. Không kết nối Binance, không Telegram thật, không API Key/Token, không triển khai VPS. Skill và mọi audit cũ giữ nguyên.

## 1. Kiến trúc đã triển khai

- Financial Numeric Engine: NUMERIC-1 ở `src/bot1/core/numeric.py`, parse/finite/bounds/domain, context128/traps, aggregate có leaf count, ratio và display riêng, serialize/deserialize chính xác.
- Account Event Engine: internal schema v1, source/account/wallet/asset, amount, UTC event/received time, trạng thái/version/evidence; không giả là schema Binance.
- Ledger: opening cutoff, cashflows theo ví/asset, observed snapshots/metrics riêng; không cộng unrealized hoặc snapshot vào dòng tiền. Reversal append-only và kiểm tra target; phí rút có WITHDRAWAL_FEE riêng.
- Deduplication nằm trong transaction Engine và bảng identities/economic_events: same-source/cross-source có attestation, namespace IDs, conflict quarantine; không dùng timestamp/amount để gộp.
- Database: SQLite WAL/FULL/foreign keys, initial migration v1, inbox, events, identities, economic events, ledger, reversals, openings, snapshots, reconciliations, outbox, checkpoints, recovery manifest/window/revisions, quarantine, health. Không amount REAL hoặc SQL SUM tiền.
- Recovery: durable admission, processing/checkpoint atomic, replay pending/history, contiguous processed cursor tách complete certificate, fake manifest phát hiện mất record/net-zero; quarantine replacement có audit và manifest revision có evidence.
- Notification: outbox commit trước send, lease/attempt/retry/dead/ambiguous; FakeTelegram memory/JSONL fsync, không mạng. Payload có signed ledger deltas theo ví, UTC/GMT+7; không gọi đó là số dư Binance đã xác nhận. Historical-only không là vốn mới.
- Health: DB quick_check, counts processed/errors/quarantine, retry/backlog, gaps, heartbeat age và processing lag. CLI có đủ init/load-mock/simulate/balances/history/notifications/gaps/health/recover/test.

Chi tiết hợp đồng và state machine: [OFFLINE-CORE.md](architecture/OFFLINE-CORE.md). Interfaces EventSource/Notifier có thể thay adapter; chuyển PostgreSQL cần Store/repository implementation mới, không thay chuỗi connection đơn thuần.

## 2. File thực tế đã tạo

Không ghi đè hoặc xóa file audit/Skill cũ. File mới được kiểm tra tồn tại trên ổ đĩa và hash trong [build-integrity.json](test-reports/build-integrity.json). `__init__.py` là package initialization, không phải module chức năng giả.

```text
.gitignore
README.md
data/mock/scenario.json
data/runtime/.gitkeep
docs/OFFLINE-CORE-REPORT.md
docs/architecture/OFFLINE-CORE.md
docs/test-reports/build-integrity.json
docs/test-reports/coverage-matrix.json
docs/test-reports/fake-latency.json
docs/test-reports/offline-demo.json
docs/test-reports/runtime-tests.json
docs/test-reports/runtime-tests.txt
pyproject.toml
scripts/bot1.py
scripts/measure_fake_latency.py
scripts/run_tests.py
src/bot1/__init__.py
src/bot1/cli.py
src/bot1/core/__init__.py
src/bot1/core/numeric.py
src/bot1/database/__init__.py
src/bot1/database/store.py
src/bot1/domain/__init__.py
src/bot1/domain/events.py
src/bot1/health/__init__.py
src/bot1/health/monitor.py
src/bot1/ledger/__init__.py
src/bot1/ledger/engine.py
src/bot1/notifications/__init__.py
src/bot1/notifications/fake.py
src/bot1/notifications/outbox.py
src/bot1/recovery/__init__.py
src/bot1/recovery/runner.py
src/bot1/sources/__init__.py
src/bot1/sources/fake.py
tests/__init__.py
tests/fixtures/__init__.py
tests/fixtures/helpers.py
tests/integration/__init__.py
tests/integration/test_core.py
tests/integration/test_recovery_edges.py
tests/integration/test_safety_cli.py
tests/unit/__init__.py
tests/unit/test_numeric.py
```

File runtime phát sinh và được gitignore: `data/runtime/offline-final.sqlite` (có WAL/SHM trong lúc mở), `data/runtime/final-fake-telegram.jsonl`; thư mục bytecode Python. Không cần commit database để chạy lại; fixture nguồn và scripts đi kèm.

## 3. Kết quả mô phỏng thực chạy

Kịch bản13 record: baseline0 Spot/Futures; nạp100 Spot; chuyển100 Futures; realized+8, commission−1, funding−0.5; unrealized+4 chỉ là snapshot; chuyển30 về Spot; rút20 và phí rút riêng1; snapshot kết kỳ9/76.5. Expected values độc lập có trong fixture và assertions runtime.

| Kết quả | Actual | Expected | Trạng thái |
| --- | --- | --- | --- |
| Spot USDT | 9 | 9 | PASS |
| Futures USDT | 76.5 | 76.5 | PASS |
| Ledger postings | 10 | 10 | PASS |
| Vốn nạp ngoài | 100 | 100, không200 | PASS |
| Reconciliation kết kỳ | MATCH | MATCH cả hai ví | PASS |
| Replay đã gửi fake notifications | 0 lần gửi thêm | 0 | PASS |

[offline-demo.json](test-reports/offline-demo.json) lưu các command/exit code/output thực tế: init → disconnect sau5 record → gaps → recover → balances/history → fake drain → replay → drain lại → health. Test `test_cli_end_to_end_and_recovery` chạy lại các CLI trên DB tạm khác và kiểm expected.

## 4. Automated tests

Command thực chạy: `python3 scripts/run_tests.py`. Kết quả: **124 PASS / 0 FAIL / 0 skipped trong suite**; 56 unit và 68 integration tests. Dữ liệu tổng hợp, không import checker tài liệu. Mỗi generated numeric boundary là unittest riêng; vòng250 oracle ratio/sum và10.000 tiny amounts không được đếm thành hàng nghìn test mới.

Bằng chứng: [runtime-tests.json](test-reports/runtime-tests.json) và [runtime-tests.txt](test-reports/runtime-tests.txt). FAIL0 chỉ áp dụng suite thực chạy, không biến các hạng mục NOT TESTED dưới đây thành PASS.

Ma trận toàn bộ kế hoạch:16 tình huống = {'PASS': 11, 'NOT TESTED': 5};40 case = {'PASS': 23, 'NOT TESTED': 17}. Đây là các nhóm tiêu chí v2, **không cộng vào124 test runtime**. Case chỉ có một phần được chạy vẫn NOT TESTED ở mức đầy đủ; test subset cụ thể được liệt kê.

### Ánh xạ16 tình huống

| ID | Trạng thái đầy đủ | Test runtime đã chạy / giới hạn |
| --- | --- | --- |
| S01 | PASS | `test_pending_completed_duplicate_stale`. Internal deposit lifecycle, no repeated posting/outbox |
| S02 | PASS | `test_withdrawal_and_separate_fee`, `test_failed_cancelled_are_not_cashflow`. Gross20 + separate fee1 gives79; failed/cancelled have no debit |
| S03 | PASS | `test_full_scenario_and_no_network`, `test_baseline_already_contains_old_history`. Deposit100 not200; snapshots/baseline do not add money twice |
| S04 | NOT TESTED | `test_transfer_two_legs_rollback_and_funding`. Known whole transfers pass; assembling raw delayed legs not implemented |
| S05 | NOT TESTED | `test_margin_unrealized_snapshot_do_not_post`. Margin observations pass; order NEW/fill/position mapping absent |
| S06 | NOT TESTED | Chưa có test runtime cho chức năng này. No order/fill/position projection; not represented as passing Decimal arithmetic |
| S07 | PASS | `test_realized_pnl_commission_funding_exact_balance`, `test_cross_source_verified_correlation`. 100+8-1-0.5=106.5; canonical fee posted once, normalized fixtures only |
| S08 | PASS | `test_cross_source_verified_correlation`, `test_wallet_asset_account_namespaces`, `test_normalized_symbol_qualified_source_ids`, `test_same_time_amount_different_ids_are_distinct`. Trusted internal IDs/correlation only, not proof of live API key scope |
| S09 | NOT TESTED | `test_disconnect_resume_and_gap_completion`, `test_missing_offset_even_net_zero_is_gap`. Fake disconnect/replay works; no WebSocket lifecycle, REST pages or120s transport test |
| S10 | PASS | `test_notifier_retry_and_rate_limit`, `test_ambiguous_delivery_not_automatically_resent`. Fake transport failure/retry/ambiguous only, no Telegram network |
| S11 | PASS | `test_invalid_types_quarantine_without_zero`, `test_late_snapshot_does_not_replace_latest_metric`. Invalid internal schema/time/amount quarantine; independent metrics preserved |
| S12 | PASS | `test_financial_action_cli_commands_are_rejected`, `test_no_network_or_credentials_dependencies_in_source`. Offline capability/CLI guard; not model activation or Binance permission test |
| S13 | PASS | `test_real_process_exit_before_commit_and_recovery`, `test_fault_after_commit`, `test_notification_crash_after_send_is_ambiguous`. Real child process exit plus transaction and fake delivery faults |
| S14 | PASS | `test_reject_01`, `test_reject_02`, `test_reject_03`, `test_reject_04`, `test_reject_05`, `test_reject_06`, `test_reject_07`, `test_reject_08`, `test_reject_09`. Product parse() rejects nonfinite tokens, no doc checker imported |
| S15 | PASS | `test_precision_regression`, `test_context_config`, `test_difference_retains_leaf_count_and_budget`. Exact128 context and actual aggregate limits |
| S16 | NOT TESTED | `test_snapshot_asof_late_event_reconciles_without_adjustment`. UNKNOWN/reconciliation works; Bot4 receiver/auth/TTL absent |

### Ánh xạ40 test case

| ID | Trạng thái đầy đủ | Test runtime đã chạy / giới hạn |
| --- | --- | --- |
| B1-001 | PASS | `test_margin_unrealized_snapshot_do_not_post`. Available changes do not post withdrawal |
| B1-002 | PASS | `test_margin_unrealized_snapshot_do_not_post`. Internal reported wallet100/margin104/unrealized4 preserved; no claim of deriving Binance account modes |
| B1-003 | PASS | `test_full_scenario_and_no_network`. Deposit100 and transfers do not duplicate capital |
| B1-004 | NOT TESTED | `test_transfer_two_legs_rollback_and_funding`. Whole normalized transfers tested; delayed raw leg correlation absent |
| B1-005 | PASS | `test_withdrawal_and_separate_fee`. Withdrawal fee distinct from trading commission |
| B1-006 | PASS | `test_failed_cancelled_are_not_cashflow`. No debit on failed/cancelled internal observations |
| B1-007 | PASS | `test_realized_pnl_commission_funding_exact_balance`. Independent expected106.5 |
| B1-008 | PASS | `test_signed_funding_and_non_usdt_fee`. Funding credit/debit and separate BNB fee |
| B1-009 | PASS | `NumericTests.test_reject_01..34` và `test_invalid_types_quarantine_without_zero`. Validation directly on product code |
| B1-010 | PASS | `test_aggregate_limit_and_round_trip`, `test_product_96_digits`, `test_precision_regression`, `test_difference_retains_leaf_count_and_budget`. Mathematical N boundary, not one billion events replayed |
| B1-011 | PASS | `test_tiny_sum`, `test_display_does_not_mutate_ledger`. Exact tiny amounts and display isolation |
| B1-012 | NOT TESTED | Chưa có test runtime cho chức năng này. Order projection absent |
| B1-013 | NOT TESTED | Chưa có test runtime cho chức năng này. Fill/cumulative projection absent |
| B1-014 | NOT TESTED | Chưa có test runtime cho chức năng này. Position close/reversal projection absent; ledger reversal is a different feature |
| B1-015 | NOT TESTED | Chưa có test runtime cho chức năng này. Hedge position projection absent |
| B1-016 | PASS | `test_cross_source_verified_correlation`. Fake two-source correlation with attestation and matching fingerprint |
| B1-017 | PASS | `test_wallet_asset_account_namespaces`, `test_same_time_amount_different_ids_are_distinct`, `test_normalized_symbol_qualified_source_ids`. No amount/time-only merge |
| B1-018 | PASS | `test_pending_completed_duplicate_stale`. Versioned lifecycle and replay |
| B1-019 | NOT TESTED | `test_missing_offset_even_net_zero_is_gap`. No paginated REST adapter; fake offset coverage only |
| B1-020 | PASS | `test_pending_before_watermark_completed_after_restart`. Old pending record receives later completion at new journal cursor |
| B1-021 | PASS | `test_missing_offset_even_net_zero_is_gap`, `test_manifest_detects_substituted_id`. Missing offsets and IDs detected by fake manifest |
| B1-022 | PASS | `test_equal_opposite_missing_events_still_detected`. Missing+5/-5 despite zero residual |
| B1-023 | NOT TESTED | `test_disconnect_resume_and_gap_completion`. Fake reconnect path tested, real stream/lifecycle and120s outage not executed |
| B1-024 | NOT TESTED | `test_baseline_already_contains_old_history`, `test_out_of_order_history`, `test_late_snapshot_does_not_replace_latest_metric`. Baseline and late events tested; no concurrent live stream bootstrap protocol |
| B1-025 | NOT TESTED | `test_missing_offset_even_net_zero_is_gap`. Cannot certify retention behavior without an API source |
| B1-026 | PASS | `test_invalid_types_quarantine_without_zero`. Bad internal timestamp/schema/type quarantined |
| B1-027 | NOT TESTED | `test_db_lock_is_retryable_not_quarantine`. No Binance auth/clock/rate-limit protocol implemented |
| B1-028 | PASS | `test_real_process_exit_before_commit_and_recovery`, `test_fault_after_event_insert`, `test_fault_after_ledger`, `test_fault_after_outbox`, `test_fault_before_commit`, `test_fault_after_commit`. Crash injection and actual os._exit child |
| B1-029 | PASS | `test_two_actual_writers`, `test_two_workers_cannot_claim_same_lease`. Concurrent SQLite writers and interleaved send lease |
| B1-030 | PASS | `test_notifier_transient_retry_then_success`. Fake send retry |
| B1-031 | PASS | `test_notification_crash_after_send_is_ambiguous`, `test_ambiguous_delivery_not_automatically_resent`. Ambiguous held, no exactly-once promise |
| B1-032 | PASS | `test_notifier_retry_and_rate_limit`, `test_permanent_notification_error_dead_letter`, `test_notification_retry_cap`. Fake retry_after, dead letter and bounded attempts |
| B1-033 | NOT TESTED | `test_json_logger_redacts_unknown_message_and_exception`, `test_sensitive_unknown_fields_redacted`. Redaction works; no Telegram markup/message parser to test |
| B1-034 | PASS | `test_sqlite_error_rolls_back_and_can_replay`, `test_backup_restore_replay`. Injected SQLite OperationalError and backup/restore variant; physical disk-full not tested |
| B1-035 | NOT TESTED | `test_utc_gmt7_day_boundary`, `test_health_and_processing_lag`. GMT+7/lag tested; stale-source policy and independent watchdog absent |
| B1-036 | NOT TESTED | `test_financial_action_cli_commands_are_rejected`, `test_no_network_or_credentials_dependencies_in_source`. Offline action guard tested; Bot4 authentication/replay TTL absent |
| B1-037 | NOT TESTED | Chưa có test runtime cho chức năng này. No Windows24h soak |
| B1-038 | NOT TESTED | Chưa có test runtime cho chức năng này. No VPS24h soak/watchdog/RPO-RTO measurement |
| B1-039 | NOT TESTED | Chưa có test runtime cho chức năng này. No live Binance requests permitted |
| B1-040 | NOT TESTED | Chưa có test runtime cho chức năng này. 1000 local ingest-to-fake-ack samples executed in fake-latency.json; live Telegram/source latency and SLO not tested |

Machine-readable mapping dùng test ID đầy đủ, đã kiểm tra tồn tại/PASS trong run thực: [coverage-matrix.json](test-reports/coverage-matrix.json).

## 5. Restart, crash, rollback và dedup

- Admission commit trước process;6 fault hooks: after_inbox_commit, after_event_insert, after_ledger, after_outbox, before_commit, after_commit. Restart connection rồi replay: đúng một posting/outbox logic, tiền không tăng lần hai.
- Child process thực `os._exit(23)` tại before_commit: inbox đã lưu, ledger/outbox/checkpoint transaction chưa commit bị rollback; restart replay cho10 đúng expected. Đây là kill process, không phải mất điện/ổ đĩa hỏng thật.
- SQLite lock có writer giữ BEGIN IMMEDIATE: DatabaseBusy rõ, không quarantine dữ liệu; unlock rồi replay thành công. Inject OperationalError sau ledger: rollback rồi replay; backup API/restore vào DB riêng và replay không nhân đôi.
- Hai writer thực chạy đồng thời và hai notifier workers được interleave tại lease: một financial effect/delivery logic. Same ID khác payload hoặc economic ID mâu thuẫn được quarantine, không bỏ im lặng.
- Quarantine xen giữa valid records giữ processed cursor trước gap; replacement append revision, chỉ đóng sau thành công. Recovery vẫn chặn nếu manifest chưa được operator xác nhận revision bằng evidence. Không tự sửa manifest/expected để che mismatch.

## 6. Tính chính xác tài chính và notification

F01/F02 được kiểm thử **trên implementation**: nonfinite/type/bounds đều reject, precision regression ra1234567890123456789012345678.91, max product96 chữ số khớp oracle Fraction, aggregate N và N+1 có kiểm tra, residual difference giữ leaf count. Không thực chạy1 tỷ event; đó là chứng minh và test giá trị biên. Fixed-point TEXT round-trip giữ giá trị; unknown khác0. Rounding display/ratio không sửa ledger. Correction/reversal không sửa lịch sử và summary net giữ category gốc.

Phí rút được tách khỏi trading commission khi hoàn thiện trước run cuối; summary reversal được hiệu chỉnh về category gốc; snapshot trùng thời điểm nhưng số tiền mâu thuẫn bị quarantine; gap mới hủy chứng nhận complete, thiếu opening được báo rõ và resolved alert có version bền vững. Đây là các vấn đề implementation đã xử lý, không thay Skill hoặc expected amount để làm test qua.

Fake notifier test transient, rate_limit/retry_after, permanent, cap5, ack mất và crash sau fake send. Ack mất/expired lease giữ ambiguous, không tự resend. Không tuyên bố Telegram exactly-once; chưa có operator UI giải quyết ambiguous/dead.

Đo riêng1000 mẫu `scripts/measure_fake_latency.py`, scope **local ingest→SQLite→fake ack**, không Telegram/network/source latency: p50=3426513ns, p95=6177591ns, p99=7791607ns, max=113249376ns;1000 fake deliveries, balance100 đúng expected. [fake-latency.json](test-reports/fake-latency.json) giữ từng mẫu. Chưa chứng minh SLO Telegram, clock drift hoặc percentile live.

## 7. Chưa triển khai / NOT TESTED / giới hạn còn lại

Không có FAIL còn tồn tại trong suite đã chạy. Chưa chứng nhận không còn lỗi ngoài phạm vi test. Các phần sau vẫn thiếu:

- Binance API adapter, quyền/auth/schema, User Data Stream lifecycle, REST pagination/retention/clock/rate-limit; tất cả chưa xác minh theo Readiness v3, không dùng endpoint suy đoán.
- Order status/fill/position/hedge projections, ghép raw transfer legs đến chậm, Bot4 receiver/auth/TTL/replay.
- Low-balance threshold/hysteresis, stale-source policy, heartbeat loop độc lập với traffic, watchdog, supervisor, scheduler backup, production backoff jitter/cooldown và periodic VPS exporter.
- Telegram thật, markup renderer/chat routing, latency mạng, policy/operator UI requeue ambiguous/dead. Fake outcomes không chứng minh error schema Telegram.
- Windows, Python3.14 (không có interpreter trong máy), PostgreSQL, packaging install/wheel, physical disk-full/mất điện thật,24h soak, RPO/RTO live; chưa có service triển khai.
- Source secondary chưa có canonical primary/correlation an toàn sẽ quarantine. Source ID scope/correlation là hợp đồng nội bộ của fixture, chưa là chứng nhận Binance ID. Không có ID tin cậy thì giữ gap.
- Source offsets/manifest chỉ của journal fake. Recovery replay toàn history nhỏ, reconciliation scan snapshots và projection có thể tốn O(n²); chưa benchmark quy mô lớn. N là bound số học, không throughput cam kết.
- Ban đầu chỉ migration schema v1; version khác fail-closed, chưa có upgrade path tương lai. Giữ backup trước thay đổi schema.
- Baseline correction và giao dịch trước baseline không có posting chưa được hỗ trợ; SOURCE_OFFSET_CONFLICT đã commit cần điều tra thủ công, không overwrite. Health là snapshot theo yêu cầu, không process monitor24/7.

## 8. Chạy chương trình

Từ `/workspace/Bot1`, không cần pip/mạng/khóa:

```sh
python3 scripts/bot1.py --db data/runtime/bot1.sqlite init
python3 scripts/bot1.py --db data/runtime/bot1.sqlite simulate
python3 scripts/bot1.py --db data/runtime/bot1.sqlite balances
python3 scripts/bot1.py --db data/runtime/bot1.sqlite history
python3 scripts/bot1.py --db data/runtime/bot1.sqlite notifications --drain
python3 scripts/bot1.py --db data/runtime/bot1.sqlite gaps
python3 scripts/bot1.py --db data/runtime/bot1.sqlite recover
python3 scripts/bot1.py --db data/runtime/bot1.sqlite health
python3 scripts/bot1.py test
python3 scripts/measure_fake_latency.py
```

Fixture đã có. Để tạo file khác không ghi đè: `python3 scripts/bot1.py load-mock --output data/mock/new-scenario.json`. Dùng `simulate --input <file> --disconnect-after 5` rồi `recover --input <file>` để thử ngắt/replay. `--pace-ms 10` là pacing local tùy chọn.

Runtime không external dependencies. Pyproject khai báo Python≥3.11; build backend tùy chọn setuptools84.2.1 có sẵn nhưng không dùng để chạy/test; chưa cài/build package trong phiên này. Không tự download dependency.

## 9. Điều kiện trước khi kết nối Binance thật

Đọc được tài liệu chính thức, hoàn thành từng hàng API/schema/quyền tại Readiness v3; chứng minh endpoint chỉ đọc và permission tối thiểu, mapping số tiền/ID/time/status tương thích NUMERIC-1. Viết adapter riêng, contract tests theo nguồn hiện hành, rate/clock/retention/reconnect và đối soát đầy đủ. Không bật trading/transfer/withdrawal để làm giám sát hoạt động. Sau đó cần yêu cầu riêng trước khi dùng tài khoản thật; không xin secret trong chat. Telegram/VPS là các giai đoạn riêng, không được suy ra từ fake transport.

**Kết quả hiện tại: lõi offline chạy được từ đầu đến cuối, có SQLite/ledger/dedup/recovery/fake outbox và test runtime thật; chưa phải bot live hoặc hệ thống được chứng nhận24/7.**
