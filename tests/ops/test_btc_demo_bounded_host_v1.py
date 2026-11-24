"""Bounded original Demo runtime with a signed HTTP venue fixture only."""

from base64 import b64encode
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hmac
import json
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest

from src.ops import btc_demo_lane3_v2 as demo
from src.ops.btc_demo_bounded_host_v1 import BtcDemoHostStartV1, run_btc_demo_bounded_host_v1
from src.ops.btc_demo_runtime_v1 import BtcDemoRuntimeV1
from src.ops.full_core_live_path_composition_root_v1 import (
    productive_read_only_get_transport_v1 as wire,
    pretrade_acquisition_v1 as clock_owner,
    external_effect_permit_durable_consume_v1 as durable,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    bind_already_held_k1_venue_auth_session_v1,
    release_k1_venue_auth_session_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest
from tests.ops.test_btc_demo_entry_reservation_v1 import demo_entry as demo_entry
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network
from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
)
from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
)


class DemoVenue:
    def __init__(self, case, direction):
        host, _, _, _, instant, payloads = case
        self.payloads = payloads
        self.clock = instant.timestamp()
        self.start = self.clock
        self.direction = direction
        self.mark = Decimal("64000")
        self.position = None
        self.orders = []
        self.fills = []
        self.histories = []
        self.calls = []
        self.post_count = 0
        self.net_count = 0
        self.timeout_posts = set()

    def now(self):
        return datetime.fromtimestamp(self.clock, timezone.utc)

    def candles(self, mark=False):
        end = int(self.clock) // 60 * 60000 - 60000
        original_end = int(self.start) // 60 * 60000 - 60000
        closes = [
            Decimal("64000")
            * (
                1
                + Decimal(self.direction)
                * Decimal((end - (99 - i) * 60000 - original_end) // 60000)
                * Decimal("0.002")
            )
            for i in range(100)
        ]
        rows = [
            [str(end - (99 - i) * 60000), *(str(p),) * 4, "5", "5", "5", "1"]
            for i, p in enumerate(closes)
        ]
        return [row[:5] + [row[8]] for row in reversed(rows)] if mark else list(reversed(rows))

    def response(self, path, query):
        if path.endswith("/config"):
            return deepcopy(self.payloads["account"]["data"])
        if path.endswith("/balance"):
            return deepcopy(self.payloads["balance"]["data"])
        if path.endswith("/account/instruments"):
            return deepcopy(self.payloads["instruments"]["data"])
        if path.endswith("/public/instruments"):
            return [
                dict(
                    self.payloads["instruments"]["data"][0],
                    settleCcy="USD",
                    quoteCcy="USD",
                    upcChg=[],
                    maxMktSz="1000",
                    maxLmtSz="1000",
                )
            ]
        if path.endswith("/leverage-info"):
            return deepcopy(self.payloads["leverage"]["data"])
        if path.endswith("/max-size"):
            return [dict(instId=demo._NATIVE, maxBuy="1000", maxSell="1000")]
        if path.endswith("/trade-fee"):
            rows = deepcopy(self.payloads["fees"]["data"])
            rows[0]["ts"] = str(int(self.clock * 1000))
            return rows
        if path.endswith("/books"):
            return [
                dict(
                    ts=str(int(self.clock * 1000)),
                    asks=[
                        [str(self.mark + Decimal("0.1")), "0.0002"],
                        [str(self.mark + Decimal("0.2")), "1000"],
                    ],
                    bids=[
                        [str(self.mark - Decimal("0.1")), "0.0002"],
                        [str(self.mark - Decimal("0.2")), "1000"],
                    ],
                )
            ]
        if path.endswith("/history-mark-price-candles"):
            return self.candles(mark=True)
        if path.endswith("/candles"):
            return self.candles()
        if path.endswith("/mark-price"):
            return [
                dict(
                    instId=demo._NATIVE,
                    markPx=str(self.mark),
                    idxPx=str(self.mark),
                    ts=str(int(self.clock * 1000)),
                )
            ]
        if path.endswith("/index-tickers"):
            native = query["instId"][0]
            return [
                dict(
                    instId=native,
                    idxPx="1" if native == "USDC-USD" else str(self.mark),
                    ts=str(int(self.clock * 1000)),
                )
            ]
        if path.endswith("/ticker"):
            return [
                dict(
                    instId=demo._NATIVE,
                    bidPx=str(self.mark - Decimal("0.1")),
                    askPx=str(self.mark + Decimal("0.1")),
                    vol24h="100",
                    volCcy24h="100",
                    ts=str(int(self.clock * 1000)),
                )
            ]
        if path.endswith("/open-interest"):
            return [
                dict(instId=demo._NATIVE, oi="200", oiCcy="200", ts=str(int(self.clock * 1000)))
            ]
        if path.endswith("/funding-rate"):
            rows = deepcopy(self.payloads["funding"]["data"])
            rows[0].update(
                ts=str(int(self.clock * 1000)),
                fundingTime=str((int(self.clock) // 3600 + 1) * 3600000),
                nextFundingTime=str((int(self.clock) // 3600 + 2) * 3600000),
            )
            return rows
        if path.endswith("/positions"):
            return [] if self.position is None else [dict(self.position)]
        if path.endswith("/positions-history"):
            return [deepcopy(row) for row in self.histories if row["posId"] == query["posId"][0]]
        if (
            path.endswith("/orders-pending")
            or path.endswith("/orders-algo-pending")
            or "/tradingBot/" in path
        ):
            return []
        if "after" in query:
            return []
        if path.endswith("/order"):
            return [deepcopy(row) for row in self.orders if row["clOrdId"] == query["clOrdId"][0]]
        if path.endswith("/orders-history"):
            return list(reversed(deepcopy(self.orders)))
        if path.endswith("/fills"):
            return list(reversed(deepcopy(self.fills)))
        raise AssertionError((path, query))

    def submit(self, body):
        self.post_count += 1
        socket = int(self.clock * 1000)
        old = self.position
        quantity = Decimal(body["sz"])
        signed = quantity * (1 if body["side"] == "buy" else -1)
        order = dict(
            instId=body["instId"],
            instType="FUTURES",
            clOrdId=body["clOrdId"],
            ordId=str(91000 + self.post_count),
            sz=body["sz"],
            accFillSz=body["sz"],
            state="filled",
            side=body["side"],
            posSide="net",
            tdMode="cross",
            ordType="market",
            reduceOnly=body.get("reduceOnly", False),
            uTime=str(socket + 300),
        )
        self.orders.append(order)

        def fill(size, offset, fee, pnl):
            row = {
                k: order[k] for k in ("instId", "instType", "clOrdId", "ordId", "side", "posSide")
            }
            row.update(
                tradeId=str(10000 + len(self.fills)),
                billId=str(20000 + len(self.fills)),
                fillSz=str(size),
                fillPx=str(self.mark),
                fillTime=str(socket + offset),
                fee=fee,
                feeCcy="USDC",
                fillPnl=pnl,
            )
            self.fills.append(row)
            return row

        if old is not None:
            closing = abs(Decimal(old["pos"]))
            fill(closing, 100, "-0.02", "0.20")
            fee = Decimal(old["fee"]) - Decimal("0.02")
            self.histories.append(
                dict(
                    instId=demo._NATIVE,
                    instType="FUTURES",
                    posId=old["posId"],
                    cTime=old["cTime"],
                    uTime=str(socket + 300),
                    direction="long" if Decimal(old["pos"]) > 0 else "short",
                    posSide="net",
                    mgnMode="cross",
                    ccy="USDC",
                    type="2",
                    openMaxPos=str(closing),
                    closeTotalPos=str(closing),
                    pnl="0.20",
                    fee=str(fee),
                    fundingFee="-0.01",
                    settledPnl="0",
                    liqPenalty="0",
                    realizedPnl=str(Decimal("0.19") + fee),
                )
            )
            if body.get("reduceOnly"):
                assert quantity == closing
                self.position = None
                self.clock += 0.5
                return order
            assert Decimal(old["pos"]) * signed < 0 and quantity > closing
            opening = quantity - closing
            self.net_count += 1
            open_fill = fill(opening, 200, "-0.02", "0")
            position_fee = "-0.02"
        else:
            opening = quantity
            open_fill = fill(opening, 200, "-0.01", "0")
            position_fee = "-0.01"
        self.position = dict(
            instId=demo._NATIVE,
            instType="FUTURES",
            posSide="net",
            mgnMode="cross",
            ccy="USDC",
            pos=str(opening * (1 if signed > 0 else -1)),
            avgPx=str(self.mark),
            tradeId=open_fill["tradeId"],
            posId=str(8000 + self.post_count),
            cTime=str(socket + 200),
            uTime=str(socket + 400),
            fee=position_fee,
        )
        self.clock += 0.5
        return order

    @contextmanager
    def open(self, request, timeout):
        url = urlsplit(request.full_url)
        assert url.hostname == "eea.okx.com" and request.get_header("X-simulated-trading") == "1"
        method = request.get_method()
        endpoint = url.path + ("?" + url.query if url.query else "")
        if request.get_header("Ok-access-key"):
            timestamp = request.get_header("Ok-access-timestamp")
            text = timestamp + method + endpoint + (request.data.decode() if request.data else "")
            assert request.get_header("Ok-access-sign").encode() == b64encode(
                hmac.digest(b"fixture-secret", text.encode(), "sha256")
            )
        self.calls.append((method, endpoint))
        if method == "POST":
            row = self.submit(json.loads(request.data))
            if self.post_count in self.timeout_posts:
                raise TimeoutError("Offline timeout after the original socket boundary")
            rows = [dict(sCode="0", clOrdId=row["clOrdId"], ordId=row["ordId"])]
        else:
            assert method == "GET" and request.data is None
            rows = self.response(url.path, parse_qs(url.query))
            self.clock = round(self.clock + 0.001, 6)
        raw = json.dumps(dict(code="0", data=rows)).encode()
        yield SimpleNamespace(status=200, url=request.full_url, read=lambda: raw)


@pytest.fixture
def runtime_case(demo_entry, tmp_path, monkeypatch):
    host, entry, _, _, instant, _ = demo_entry
    direction = 1 if entry.cycle.decision_outcome == "enter_long" else -1
    venue = DemoVenue(demo_entry, direction)
    identity = tmp_path / "fixed-instrument.json"
    identity.write_text(
        json.dumps(
            dict(
                environment="TESTNET",
                purpose="INSTRUMENT_IDENTITY",
                instrument=dict(
                    canonical_instrument_id=host.budget.bound.instrument_id,
                    venue_native_inst_id=demo._NATIVE,
                ),
            )
        )
    )
    from hashlib import sha256
    from pathlib import Path

    config = dict(
        schema="btc_demo_bounded_host_preparation.v1",
        session_id="offline-full-bounded-demo",
        testnet_root=str(tmp_path / "bounded-demo"),
        repository_sha=host.repository_sha,
        account_identity=host.budget.account,
        fixed_pin=dict(
            kind="USER_FIXED_TESTNET_INSTRUMENT",
            instrument_source=str(identity),
            instrument_source_sha256=sha256(identity.read_bytes()).hexdigest(),
            canonical_instrument_id=host.budget.bound.instrument_id,
            native_instrument_id=demo._NATIVE,
        ),
        entry_budget_policy_path=str(
            Path(__file__).resolve().parents[2]
            / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V11.json"
        ),
        signer_service="PeakTrade-Slot3-Demo-BTC",
        signer_fields=dict(api_key="api-key", api_secret="secret", passphrase="passphrase"),
        processing_poll_seconds=2,
        close_confirmation_timeout_seconds=120,
    )
    handle = bind_already_held_k1_venue_auth_session_v1(
        api_key="fixture-key",
        api_secret="fixture-secret",
        passphrase="fixture-phrase",
        execution_environment="TESTNET",
    )
    config["entry_budget_policy_sha256"] = sha256(
        Path(config["entry_budget_policy_path"]).read_bytes()
    ).hexdigest()
    monkeypatch.setattr(wire, "build_opener", lambda *_: venue)
    monkeypatch.setattr(demo, "build_opener", lambda *_: venue)
    for owner in (wire, clock_owner, durable):
        monkeypatch.setattr(
            owner,
            "_utc_now_iso_v1" if owner is durable else "utc_now_iso_v1",
            lambda: venue.now().isoformat(),
        )

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return venue.now() if tz is None else venue.now().astimezone(tz)

    monkeypatch.setattr(demo, "datetime", Clock)
    from src.ops import btc_demo_session_close_v1, btc_demo_session_close_reconciliation_v1
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_n1_venue_quantity_limit_admission_v1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
        invoke_join_v1,
    )

    for owner in (
        btc_demo_session_close_v1,
        btc_demo_session_close_reconciliation_v1,
        current_productive_n1_venue_quantity_limit_admission_v1,
        entry_execution_cost_v1,
    ):
        monkeypatch.setattr(owner, "utc_now_iso_v1", lambda: venue.now().isoformat())
    monkeypatch.setattr(invoke_join_v1, "datetime", Clock)
    from src.ops.peak_trade_public_market_data_runtime_v1 import rest_recovery_v1

    monkeypatch.setattr(rest_recovery_v1, "time", SimpleNamespace(time=lambda: venue.clock))
    runtime = BtcDemoRuntimeV1(
        config=config,
        signing_handle=handle,
        clock=lambda: venue.clock,
        execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
            origin_main=host.repository_sha, head=host.repository_sha, drift=""
        ),
        opener_factory=lambda: venue,
    )
    start = BtcDemoHostStartV1(
        config["session_id"],
        digest(config),
        venue.now().isoformat(),
        (venue.now() + timedelta(seconds=60)).isoformat(),
    )
    try:
        yield runtime, start, venue
    finally:
        runtime.close()
        release_k1_venue_auth_session_v1(handle)


@pytest.mark.parametrize("uncertain", [False, True])
@pytest.mark.parametrize("minute_boundary", [False, True])
def test_full_host_first_entry_two_net_switches_and_confirmed_session_end(
    runtime_case, uncertain, minute_boundary
):
    runtime, start, venue = runtime_case
    if uncertain:
        venue.timeout_posts = {1, 2, 3, 4}
    pulses = 0
    crossed = False

    def sleep(seconds):
        nonlocal pulses, crossed
        pulses += 1
        if minute_boundary and venue.position is not None and not crossed:
            venue.clock += 60
            crossed = True
        if venue.net_count >= 2 or pulses > 12:
            venue.clock = max(venue.start + 3600, venue.clock + seconds)
            return
        venue.clock += seconds
        if venue.position is None:
            venue.mark += venue.direction * Decimal(600)
        else:
            from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
                restore_layered_core_episode_v1,
            )

            core = restore_layered_core_episode_v1(
                runtime.cursor, expected_instrument_id=runtime.bound.instrument_id
            )
            signed = Decimal(venue.position["pos"])
            venue.mark = Decimal(str(core.running_reference.reference_price_r_t)) - (
                1 if signed > 0 else -1
            ) * Decimal(str(core.scope.d_t)) * Decimal("1.5")

    result = run_btc_demo_bounded_host_v1(
        runtime=runtime, operator_start=start, clock=lambda: venue.clock, sleep=sleep
    )
    events = [
        json.loads(p.read_bytes()) for p in runtime.root.joinpath("host-events").glob("*.json")
    ]
    assert result["status"] == "CONFIRMED_CLOSED", events
    assert venue.post_count == 4 and venue.net_count == 2
    summary = result["result"]["session_result"]
    assert Decimal(summary["initial_usdc"]) == 25 and Decimal(
        summary["final_session_basis_usdc"]
    ) == Decimal("25.46")


def test_construction_and_expired_start_do_not_open_the_runtime(runtime_case):
    runtime, start, venue = runtime_case
    assert not runtime.root.exists() and not venue.calls
    venue.clock += 61
    with pytest.raises(ValueError, match="START_NOT_CURRENT"):
        run_btc_demo_bounded_host_v1(
            runtime=runtime, operator_start=start, clock=lambda: venue.clock, sleep=lambda _: None
        )
    assert not runtime.root.exists() and not venue.calls and venue.post_count == 0


def test_session_without_entry_is_confirmed_flat_and_cold_readable(runtime_case):
    runtime, start, venue = runtime_case

    def sleep(_):
        venue.clock = venue.start + 3600

    result = run_btc_demo_bounded_host_v1(
        runtime=runtime, operator_start=start, clock=lambda: venue.clock, sleep=sleep
    )
    assert result["status"] == "CONFIRMED_NO_ENTRY", result
    assert venue.post_count == 0 and runtime.owner.active_sum_v1() == 0
    registration = runtime.registration
    assert runtime.owner.risk_snapshot_v1()["state"]["slot_capital_allocation"]["funding"] is None
    runtime.close()
    cold = BtcDemoRuntimeV1(
        config=runtime.config,
        signing_handle=runtime.handle,
        clock=lambda: venue.clock,
        execution_integrity_backend=runtime.integrity,
        opener_factory=lambda: venue,
    )
    try:
        before = list(venue.calls)
        again = run_btc_demo_bounded_host_v1(
            runtime=cold, operator_start=start, clock=lambda: venue.clock, sleep=sleep
        )
        assert cold.registration == registration and again["status"] == "CONFIRMED_NO_ENTRY"
        assert venue.calls == before
    finally:
        cold.close()


def test_restart_after_unknown_entry_reconciles_then_continues_same_budget(runtime_case):
    runtime, start, venue = runtime_case
    venue.timeout_posts = {1}
    registration = runtime.start_or_recover_v1(operator_start=start)
    for _ in range(8):
        runtime.step_v1()
        if venue.post_count:
            break
        venue.clock += 2
        venue.mark += venue.direction * Decimal(600)
    assert venue.post_count == 1
    held = runtime.owner.local_commitment_readback_v1().active_commitment_sum
    runtime.close()
    cold = BtcDemoRuntimeV1(
        config=runtime.config,
        signing_handle=runtime.handle,
        clock=lambda: venue.clock,
        execution_integrity_backend=runtime.integrity,
        opener_factory=lambda: venue,
    )
    try:
        assert cold.start_or_recover_v1(operator_start=start) == registration
        assert cold.owner.local_commitment_readback_v1().active_commitment_sum == held
        with pytest.raises(ValueError, match="G17_UNAVAILABLE"):
            cold.step_v1()
        assert venue.post_count == 1
        assert all(
            row["reconciliation"]["matched"] for row in cold.owner.execution_links_v1().values()
        )
        venue.clock += 60
        from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
            restore_layered_core_episode_v1,
        )

        core = restore_layered_core_episode_v1(
            cold.cursor, expected_instrument_id=cold.bound.instrument_id
        )
        venue.mark = Decimal(str(core.running_reference.reference_price_r_t)) - (
            1 if Decimal(venue.position["pos"]) > 0 else -1
        ) * Decimal(str(core.scope.d_t)) * Decimal("1.5")

        def sleep(seconds):
            venue.clock = max(venue.start + 3600, venue.clock + seconds)

        result = run_btc_demo_bounded_host_v1(
            runtime=cold, operator_start=start, clock=lambda: venue.clock, sleep=sleep
        )
        assert result["status"] == "CONFIRMED_CLOSED", result
        summary = result["result"]["session_result"]
        assert Decimal(summary["initial_usdc"]) == 25 and summary["reversal_count"] == 1
        assert Decimal(summary["final_session_basis_usdc"]) == Decimal("25.31")
        assert venue.post_count == 3
    finally:
        cold.close()
