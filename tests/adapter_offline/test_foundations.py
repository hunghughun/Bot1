from __future__ import annotations

from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest

from bot1.adapters.binance.parsing import RestResponseParser, JsonNumber, ParseError, decode
from bot1.adapters.binance.websocket import WebSocketEventParser
from bot1.adapters.binance.schema import SchemaCompatibilityValidator as Validator
from bot1.adapters.binance.mapper import AccountEventMapper
from bot1.adapters.binance.correlation import BinanceEventCorrelation
from bot1.adapters.binance.contracts import REVIEWS, UnsupportedContract
from bot1.adapters.binance.safety import AdapterConfig, EndpointAllowlist, OfflineTransport, LiveModeDisabled, DisabledSigner
from bot1.adapters.binance.source import AdapterQuarantine, OfflineEnvelope, OfflineBinanceSource
from bot1.adapters.binance.pagination import PageWindow, SyntheticPage, PageGap
from bot1.adapters.binance.policies import classify_http, RetryPolicy, RateBudget, clock_observation, freshness
from bot1.core.numeric import NumericError
from bot1.database.store import Store

ROOT = Path(__file__).resolve().parents[2]


class ParserTests(unittest.TestCase):
    def test_synthetic_fixture_provenance_and_independent_values(self):
        fixtures = json.loads((ROOT/'tests/fixtures/adapter-foundations.json').read_text(encoding='utf-8'))
        self.assertIs(fixtures['binance_schema_verified'],False)
        for sample in fixtures['samples']:
            decoded, _ = decode(sample['wire'])
            self.assertEqual(decoded['sample_decimal'].lexeme,sample['expected_lexeme'])

    def test_json_number_lexeme_exact_from_initial_decode(self):
        frame = RestResponseParser().parse(b'{"number":1234567890123456789012345678.901234567890123456,"id":9007199254740993}', 'synthetic-not-binance')
        self.assertEqual(frame.data['number'], JsonNumber('1234567890123456789012345678.901234567890123456'))
        self.assertEqual(frame.data['id'].lexeme, '9007199254740993')
        self.assertEqual(Validator.money(frame.data['number']), Decimal('1234567890123456789012345678.901234567890123456'))

    def test_number_zero_and_scientific_representation(self):
        data, _ = decode('[0,-0,1.000,1e-18]')
        self.assertEqual([x.lexeme for x in data], ['0', '-0', '1.000', '1e-18'])
        with self.assertRaises(NumericError): Validator.money(data[1], 'nonnegative')
        self.assertEqual(Validator.money(data[3]), Decimal('1e-18'))

    def test_string_money_and_json_numbers_are_distinct(self):
        data, _ = decode('{"string":"1.234567890123456789","number":1.234567890123456789}')
        self.assertIsInstance(data['string'], str)
        self.assertIsInstance(data['number'], JsonNumber)
        self.assertEqual(Validator.money(data['string']), Validator.money(data['number']))

    def test_nonfinite_and_duplicate_key_rejected(self):
        for raw in ['{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '{"x":1,"x":2}']:
            with self.assertRaises(ParseError): decode(raw)
        for raw in ['NaN', 'sNaN', 'Infinity', '-Inf']:
            with self.assertRaises(NumericError): Validator.money(raw)

    def test_malformed_missing_container_and_utf8(self):
        for raw in ['{"x":', b'\xff', 'null', 'false', '1']:
            with self.assertRaises(ParseError): RestResponseParser().parse(raw, 'unknown')
        with self.assertRaises(ParseError): WebSocketEventParser().parse('[]', 'unknown')

    def test_complexity_limits(self):
        for raw in [' ' * 1048577, '[' * 34 + '0' + ']' * 34, '[' + ','.join(['0'] * 10001) + ']', '1' * 97]:
            with self.assertRaises(ParseError): decode(raw)

    def test_financial_bounds_after_decode(self):
        for token in ['1e19', '1e-19', '0.0000000000000000001', '1000000000000000000000000000000']:
            value, _ = decode(token)
            with self.assertRaises(NumericError): Validator.money(value)

    def test_bool_float_python_int_not_promoted_to_money(self):
        for value in [True, 0.1, 1, None]:
            with self.assertRaises(NumericError): Validator.money(value)

    def test_rest_and_ws_syntax_decoders_keep_same_number(self):
        raw = b'{"sample_amount":0.000000000000000001}'
        rest = RestResponseParser().parse(raw, 'synthetic')
        ws = WebSocketEventParser().parse(raw, 'synthetic')
        self.assertEqual(rest.data, ws.data)
        self.assertEqual(rest.sha256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(ws.channel, 'websocket')


class VerificationGateTests(unittest.TestCase):
    def test_test_runner_cannot_reuse_stale_passing_output(self):
        import importlib.util
        from unittest.mock import patch
        spec=importlib.util.spec_from_file_location('adapter_runner_for_test',ROOT/'scripts/run_adapter_tests.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'results.json';target.write_text('{"status":"PASS","executed":999}')
            failure=subprocess.CompletedProcess([],1,stdout='',stderr='bootstrap failure')
            with patch.object(sys,'argv',['run_adapter_tests.py','--output',str(target)]), patch.object(module.subprocess,'run',return_value=failure):
                self.assertEqual(module.main(),1)
            result=json.loads(target.read_text())
            self.assertEqual(result['status'],'FAIL');self.assertEqual(result['executed'],0)
            self.assertTrue(result['bootstrap_failed'])

    def test_all_reviewed_inventory_entries_remain_unsupported(self):
        for contract in REVIEWS:
            with self.assertRaises(UnsupportedContract):
                AccountEventMapper().map(RestResponseParser().parse('{}', contract))
            self.assertEqual(REVIEWS[contract].status, 'NOT VERIFIED')

    def test_fake_verified_flag_cannot_enable_mapping(self):
        frame = RestResponseParser().parse('{"verified":true,"amount":"100","status":"completed"}', 'futures_income')
        with self.assertRaises(UnsupportedContract): AccountEventMapper().map(frame)

    def test_unknown_missing_pending_failed_payloads_do_not_create_events(self):
        for status in ['pending', 'failed', 'completed']:
            frame = RestResponseParser().parse(json.dumps({'example':status}), 'deposit_history')
            with self.assertRaises(UnsupportedContract): Validator.validate(frame)

    def test_rest_ws_link_requires_verified_rules(self):
        raw = b'{"sample_id":"same","sample_amount":"100"}'
        rest = RestResponseParser().parse(raw, 'futures_income')
        ws = WebSocketEventParser().parse(raw, 'futures_user_stream')
        with self.assertRaises(UnsupportedContract): BinanceEventCorrelation().link(rest, ws)

    def test_quarantine_persists_on_replay_without_financial_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'adapter.sqlite'
            frames = [OfflineEnvelope('deposit_history','rest',b'{}'),
                      OfflineEnvelope('futures_user_stream','websocket',b'{"sample":1.00}'),
                      OfflineEnvelope('deposit_history','rest',b'{bad json'),
                      OfflineEnvelope('withdraw_history','rest',b'{"amount":NaN}')]
            journal = AdapterQuarantine(path)
            source = OfflineBinanceSource(frames, journal)
            self.assertEqual(list(source.events()), [])
            self.assertFalse(source.complete)
            self.assertEqual(len(journal.rows()), 4)
            journal.close()
            journal = AdapterQuarantine(path)
            try:
                self.assertEqual(list(OfflineBinanceSource(frames, journal).events()), [])
                self.assertEqual(len(journal.rows()), 4)
            finally: journal.close()

    def test_quarantine_never_stores_secret_payload_or_unknown_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'adapter.sqlite'; journal = AdapterQuarantine(path)
            try:
                e = OfflineEnvelope('SECRET_SENTINEL', 'SECRET_SENTINEL', b'{"token":"SECRET_SENTINEL"}')
                self.assertEqual(list(OfflineBinanceSource([e], journal).events()), [])
                self.assertNotIn('SECRET_SENTINEL', repr(journal.rows()))
            finally: journal.close()

    def test_quarantine_refuses_core_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'core.sqlite'; store = Store(path)
            try:
                before = store.rows('SELECT name FROM sqlite_master WHERE type=\'table\'')
                with self.assertRaises(ValueError): AdapterQuarantine(path)
                self.assertEqual(before, store.rows('SELECT name FROM sqlite_master WHERE type=\'table\''))
                self.assertEqual(store.rows('PRAGMA user_version')[0]['user_version'], 1)
            finally: store.close()

    def test_core_recovery_rejects_unverified_source_without_mutation(self):
        from bot1.ledger.engine import Engine
        from bot1.recovery.runner import Recovery
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(Path(tmp)/'core.sqlite');journal=AdapterQuarantine(Path(tmp)/'adapter.sqlite')
            try:
                source=OfflineBinanceSource([OfflineEnvelope('deposit_history','rest',b'{}')],journal)
                with self.assertRaises(UnsupportedContract):Recovery(Engine(store)).run(source)
                self.assertFalse(store.rows('SELECT * FROM ledger'))
                self.assertFalse(store.rows('SELECT * FROM inbox'))
                self.assertFalse(store.rows('SELECT * FROM recovery_windows'))
            finally:journal.close();store.close()

    def test_modes_allowlist_transport_and_signer_default_deny(self):
        self.assertEqual(AdapterConfig().mode, 'offline')
        for mode in ['live_readonly', 'live', '', True]:
            with self.assertRaises(LiveModeDisabled): AdapterConfig(mode=mode)
        self.assertEqual(EndpointAllowlist().entries, frozenset())
        for method in ['GET', 'POST', 'DELETE']:
            with self.assertRaises(LiveModeDisabled): EndpointAllowlist().authorize(method, 'https://not-configured.invalid', '/unverified')
            with self.assertRaises(LiveModeDisabled): OfflineTransport().request(method, 'https://not-configured.invalid', '/unverified')
        with self.assertRaises(LiveModeDisabled): DisabledSigner().sign(b'no credentials')

    def test_network_guard_parent_and_children(self):
        import _socket
        for action in [lambda:socket.socket(), lambda:socket.SocketType(), lambda:_socket.socket(), lambda:socket.create_connection(('example.invalid',443)), lambda:socket.getaddrinfo('example.invalid',443)]:
            with self.assertRaisesRegex(RuntimeError,'BOT1_OFFLINE_NETWORK_DISABLED'): action()
        env = dict(os.environ, PYTHONPATH=str(ROOT/'src'))
        code = 'import socket; socket.create_connection(("example.invalid",443))'
        run = subprocess.run([sys.executable,'-c',code],env=env,capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0)
        self.assertIn('BOT1_OFFLINE_NETWORK_DISABLED',run.stderr)


class PolicyTests(unittest.TestCase):
    def test_http_rate_retry_auth_and_unknown(self):
        self.assertEqual(classify_http(429, '30').wait_ms, 30000)
        self.assertTrue(classify_http(503).retryable)
        for status in [401,403,404,418]: self.assertFalse(classify_http(status).retryable)
        self.assertFalse(classify_http(429).retryable)
        self.assertFalse(classify_http(429,'not-a-delay').retryable)
        self.assertEqual(classify_http(200).category, 'HTTP_SUCCESS_SCHEMA_STILL_REQUIRED')

    def test_retry_backoff_jitter_and_server_wait(self):
        p = RetryPolicy()
        self.assertTrue(1000 <= p.delay(1,'fixed') <= 1250)
        self.assertTrue(2000 <= p.delay(2,'fixed') <= 2250)
        self.assertEqual(p.delay(1,'fixed',300000),300000)
        self.assertIsNone(p.delay(5,'fixed'))
        for x in [0,-1,True]:
            with self.assertRaises(ValueError):p.delay(x,'key')

    def test_weight_budget_and_clock_regression(self):
        budget=RateBudget(10,1000)
        self.assertTrue(budget.reserve(8,0)); self.assertFalse(budget.reserve(3,1))
        self.assertTrue(budget.reserve(2,2)); self.assertTrue(budget.reserve(10,1000))
        with self.assertRaises(ValueError):budget.reserve(1,999)

    def test_clock_offset_and_uncertainty(self):
        self.assertEqual(clock_observation(1000,1100,1075),(25,100))
        with self.assertRaises(ValueError):clock_observation(1000,3000,1075)
        with self.assertRaises(ValueError):clock_observation(1000,999,1075)

    def test_stale_snapshot_is_not_dead_transport(self):
        self.assertEqual(freshness(200000,199999,0,5000,100000), {'transport_stale':False,'snapshot_stale':True})
        self.assertTrue(freshness(200000,0,199999,5000,100000)['transport_stale'])


class PaginationTests(unittest.TestCase):
    def test_missing_page_cannot_complete_then_recover(self):
        pages=PageWindow(3)
        pages.add(SyntheticPage(1,3,b'{"sample":1}'));pages.add(SyntheticPage(3,3,b'{"sample":3}'))
        self.assertEqual(pages.missing,[2]);self.assertFalse(pages.complete)
        with self.assertRaises(PageGap):pages.ordered()
        pages.add(SyntheticPage(2,3,b'{"sample":2}'))
        self.assertEqual(pages.ordered(),(b'{"sample":1}',b'{"sample":2}',b'{"sample":3}'))

    def test_duplicate_conflicting_pages_and_replay(self):
        pages=PageWindow(1);pages.add(SyntheticPage(1,1,b'one'));pages.add(SyntheticPage(1,1,b'one'))
        self.assertEqual(pages.ordered(),(b'one',))
        with self.assertRaises(PageGap):pages.add(SyntheticPage(1,1,b'two'))

    def test_retention_gap_stays_incomplete(self):
        pages=PageWindow(1);pages.add(SyntheticPage(1,1,b'one'));pages.retention_gap=True
        self.assertFalse(pages.complete)
        with self.assertRaises(PageGap):pages.ordered()
