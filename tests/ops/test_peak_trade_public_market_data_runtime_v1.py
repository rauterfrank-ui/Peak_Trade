"""Deterministic tests for PEAK_TRADE_PUBLIC_MARKET_DATA_RUNTIME_V1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.economic_md_input_producer_v1.constants_v1 import (
    MINIMUM_FINALIZED_PT1M_MARKS,
    PT1M_STEP_MS,
)
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import RawMarkCandleV1
from src.ops.economic_md_input_producer_v1.validation_v1 import (
    select_finalized_contiguous_pt1m_marks_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import (
    O4_AUTHORITATIVE_INTERVAL,
    PUBLIC_V1_TRADE_GLOBAL_MAX_AGE_SECONDS,
)
from src.ops.peak_trade_public_market_data_runtime_v1.consumer_adapters_v1 import (
    landscape_readmodel_from_live_facts_v1,
    o4_n_bars_envelope_from_historical_facts_v1,
    ranking_b05_adapter_from_finalized_pt1m_marks_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
    append_fact_v1,
    default_store_paths_v1,
    load_all_facts_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.event_pipeline_v1 import (
    EventSequenceStateV1,
    process_public_events_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.freshness_v1 import (
    PublicFreshnessError,
    assert_no_global_trade_max_age_v1,
    classify_live_best_bid_ask_freshness_v1,
    classify_live_mark_price_freshness_v1,
    consumer_trade_freshness_required_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.historical_query_v1 import (
    query_historical_facts_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.rest_recovery_v1 import (
    PublicRestRecoveryError,
    bootstrap_rest_snapshot_v1,
    parse_finalized_pt1m_mark_rows_v1,
    recover_pt1m_gaps_via_rest_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.runtime_orchestrator_v1 import (
    PublicMarketDataRuntimeV1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.safety_boundary_v1 import (
    public_runtime_safety_attestation_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.ws_binding_v1 import (
    PublicWsBindingError,
    forbid_wseeapap_as_authority_v1,
    load_ratified_eea_public_ws_binding_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.ws_transport_v1 import PublicWsTransportV1

REPO = Path(__file__).resolve().parents[2]
BASE_TS = 1_757_631_540_000


def _mark_rows(n: int, *, start: int = BASE_TS) -> tuple[RawMarkCandleV1, ...]:
    out: list[RawMarkCandleV1] = []
    for i in range(n):
        out.append(
            RawMarkCandleV1(
                venue_native_id="ETH-USDT-SWAP",
                ts_ms=str(start + i * PT1M_STEP_MS),
                mark_px=str(100 + i),
                confirm="1",
                receive_or_capture_timestamp="1757635260000",
            )
        )
    return tuple(out)


class _FakeConnector:
    def __init__(self) -> None:
        self.subscribed = False

    def connect(self, ws_base_url: str) -> None:
        assert ws_base_url.startswith("wss://")

    def subscribe(self, args: list) -> None:
        self.subscribed = True

    def disconnect(self) -> None:
        self.subscribed = False


def test_rest_bootstrap_fixture() -> None:
    def fetch(path: str, params: dict) -> dict:
        return {"code": "0", "data": [{"instId": params.get("instId", ""), "markPx": "1"}]}

    snap = bootstrap_rest_snapshot_v1(fetch, "ETH-USDT-SWAP")
    assert snap["host"] == "eea.okx.com"


def test_ws_connect_subscribe_state() -> None:
    msgs = [{"tradeId": "1", "ts": "1000"}]

    def source():
        return iter(msgs)

    transport = PublicWsTransportV1.from_ratified_binding(
        connector=_FakeConnector(),
        message_source=source,
        venue_native_id="ETH-USDT-SWAP",
    )
    transport.connect_and_subscribe()
    assert transport.state.subscribed is True
    out = transport.poll_messages()
    assert len(out) == 1


def test_ws_reconnect_resubscribe() -> None:
    transport = PublicWsTransportV1.from_ratified_binding(
        connector=_FakeConnector(),
        message_source=lambda: iter(()),
        venue_native_id="ETH-USDT-SWAP",
    )
    transport.connect_and_subscribe()
    transport.reconnect_resubscribe()
    assert transport.state.reconnect_count == 1


def test_duplicate_and_out_of_order_events() -> None:
    events = [
        {"msg_id": "a", "ts": "2000"},
        {"msg_id": "a", "ts": "2000", "_duplicate": True},
        {"msg_id": "b", "ts": "1000"},
    ]
    envs, _, _ = process_public_events_v1(events=events, state=EventSequenceStateV1())
    assert envs[0].duplicate is False
    assert envs[1].duplicate is True
    assert envs[2].out_of_order is True


def test_gap_detection_triggers_rest_recovery() -> None:
    inst = {
        "canonical_instrument_id": "inst-eth",
        "venue_native_id": "ETH-USDT-SWAP",
        "venue": "okx_eea",
        "instrument_type": "SWAP",
        "settlement_asset": "USDT",
        "mapping_provenance_digest": "x",
    }
    gap_ts = BASE_TS + PT1M_STEP_MS

    def fetch(path: str, params: dict) -> dict:
        row = [str(gap_ts), "0", "0", "0", "101", "0", "1"]
        return {"code": "0", "data": [row]}

    result = recover_pt1m_gaps_via_rest_v1(
        fetch_json=fetch,
        venue_native_id="ETH-USDT-SWAP",
        instrument_ref_dict=inst,
        missing_interval_starts_ms=[gap_ts],
        captured_at="2026-09-26T00:00:00Z",
    )
    assert result.gaps_detected == 1
    assert len(result.recovered_bars) == 1


def test_mark_freshness_over_5s_stale() -> None:
    v = classify_live_mark_price_freshness_v1(age_seconds=5.1)
    assert v.publishable is False
    assert v.stale is True


def test_bba_freshness_over_5s_stale() -> None:
    v = classify_live_best_bid_ask_freshness_v1(age_seconds=6.0)
    assert v.publishable is False


def test_no_global_trade_ttl() -> None:
    assert PUBLIC_V1_TRADE_GLOBAL_MAX_AGE_SECONDS is None
    assert_no_global_trade_max_age_v1()
    with pytest.raises(PublicFreshnessError):
        consumer_trade_freshness_required_v1(consumer_id="x", max_age_seconds=None)


def test_finalized_vs_open_interval() -> None:
    rows = parse_finalized_pt1m_mark_rows_v1(
        {"data": [[str(BASE_TS), "0", "0", "0", "1", "0"]]},
        instrument_ref_dict={
            "canonical_instrument_id": "i",
            "venue_native_id": "ETH-USDT-SWAP",
            "venue": "okx_eea",
            "instrument_type": "SWAP",
            "settlement_asset": "USDT",
            "mapping_provenance_digest": "d",
        },
        captured_at="2026-09-26T00:00:00Z",
        transport="rest",
    )
    assert rows == []


def test_exactly_61_contiguous_marks_pass() -> None:
    selected, codes = select_finalized_contiguous_pt1m_marks_v1(_mark_rows(61))
    assert not codes
    assert len(selected) == MINIMUM_FINALIZED_PT1M_MARKS


def test_60_marks_fail_closed() -> None:
    _, codes = select_finalized_contiguous_pt1m_marks_v1(_mark_rows(60))
    assert codes


def test_continuity_gap_fail_closed() -> None:
    marks = list(_mark_rows(61))
    broken = marks[:30] + marks[31:]
    _, codes = select_finalized_contiguous_pt1m_marks_v1(tuple(broken))
    assert codes


def test_ranking_adapter_no_ohlcv_substitution_flag() -> None:
    adapter = ranking_b05_adapter_from_finalized_pt1m_marks_v1(_mark_rows(61))
    assert adapter["ohlcv_substitution"] is False
    assert adapter["ranking_safe"] is True


def test_o4_pt1h_semantics_preserved() -> None:
    env = o4_n_bars_envelope_from_historical_facts_v1([])
    assert env["authoritative_interval"] == O4_AUTHORITATIVE_INTERVAL
    assert env["pt1m_semantic_migration"] is False


def test_durable_restart_replay_without_ws(tmp_path: Path) -> None:
    paths = default_store_paths_v1(tmp_path)
    append_fact_v1(
        paths,
        {
            "fact_kind": "FinalizedPt1mMarkFactV1",
            "interval_start_ms": BASE_TS,
            "mark_px": "100",
            "confirm": "1",
            "instrument": {"venue_native_id": "ETH-USDT-SWAP"},
        },
    )
    hist = query_historical_facts_v1(tmp_path)
    assert hist.live_ws_required is False
    assert len(hist.facts) == 1
    loaded = load_all_facts_v1(paths)
    assert loaded[0]["fact_kind"] == "FinalizedPt1mMarkFactV1"
    assert loaded[0]["instrument"]["venue_native_id"] == "ETH-USDT-SWAP"


def test_landscape_non_authorizing() -> None:
    lm = landscape_readmodel_from_live_facts_v1(
        mark_px="1", live_mark_captured_at="t", ohlcv_freshness_state="fresh"
    )
    assert lm["dashboard_authority_effect"] == "NONE"


def test_multi_future_observation_not_trading_auth() -> None:
    att = public_runtime_safety_attestation_v1()
    assert att["MULTI_FUTURE_RUNTIME_AUTHORIZED"] is False
    assert att["MAX_POSITIONS_EFFECTIVE"] == 1


def test_public_runtime_cannot_post() -> None:
    att = public_runtime_safety_attestation_v1()
    assert att["POST_ALLOWED"] is False
    assert att["EXTERNAL_EFFECT_AUTHORIZED"] is False
    assert att["public_runtime_may_post"] is False


def test_ws_binding_rejects_wseeapap_authority() -> None:
    with pytest.raises(PublicWsBindingError):
        forbid_wseeapap_as_authority_v1("wseeapap.okx.com")
    binding = load_ratified_eea_public_ws_binding_v1()
    assert "wseea" in binding.ws_base_url


def test_runtime_orchestrator_bootstrap_and_publish(tmp_path: Path) -> None:
    runtime = PublicMarketDataRuntimeV1(
        store_root=tmp_path,
        venue_native_id="ETH-USDT-SWAP",
        canonical_instrument_id="inst-eth",
        rest_fetch_json=lambda p, q: {"code": "0", "data": []},
    )
    runtime.bootstrap(captured_at="2026-09-26T00:00:00Z")
    for i in range(61):
        runtime.persist_finalized_mark_fact(
            {
                "fact_kind": "FinalizedPt1mMarkFactV1",
                "interval_start_ms": BASE_TS + i * PT1M_STEP_MS,
                "mark_px": str(100 + i),
                "confirm": "1",
                "instrument": {"venue_native_id": "ETH-USDT-SWAP"},
            }
        )
    surfaces = runtime.publish_consumer_surfaces(
        mark_age_seconds=1.0, bba_age_seconds=1.0, captured_at="2026-09-26T00:00:00Z"
    )
    assert surfaces["ranking_b05"]["ranking_safe"] is True


def test_gap_not_recovered_fail_closed() -> None:
    inst = {
        "canonical_instrument_id": "i",
        "venue_native_id": "ETH-USDT-SWAP",
        "venue": "okx_eea",
        "instrument_type": "SWAP",
        "settlement_asset": "USDT",
        "mapping_provenance_digest": "d",
    }

    def fetch(path: str, params: dict) -> dict:
        return {"code": "0", "data": []}

    with pytest.raises(PublicRestRecoveryError):
        recover_pt1m_gaps_via_rest_v1(
            fetch_json=fetch,
            venue_native_id="ETH-USDT-SWAP",
            instrument_ref_dict=inst,
            missing_interval_starts_ms=[BASE_TS],
            captured_at="2026-09-26T00:00:00Z",
        )


def test_policy_config_present() -> None:
    cfg = json.loads(
        (
            REPO / "config/governance/peak_trade_public_market_data_runtime_v1_policy_v1.json"
        ).read_text()
    )
    assert cfg["PUBLIC_V1_MARK_PRICE_MAX_AGE_SECONDS"] == 5
    assert cfg["PUBLIC_V1_TRADE_GLOBAL_MAX_AGE_SECONDS"] is None
