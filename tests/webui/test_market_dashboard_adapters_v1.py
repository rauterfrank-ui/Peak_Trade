"""Focused PR-C adapter projection tests."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.webui.market_dashboard_readmodels_v1 import (
    AuthorityClassificationV1,
    CanonicalDecisionStatusV1,
    DashboardAvailabilityStateV1,
    DashboardFreshnessStateV1,
    DecisionDirectionV1,
    EconomicGateStatusV1,
    OperatingModeV1,
    TriStateV1,
    dumps_json,
    to_json_dict,
)
from src.webui.market_dashboard_readmodels_v1.adapters import (
    adapt_canonical_decision_summary_v1,
    adapt_dashboard_freshness_snapshot_v1,
    adapt_diagnostics_summary_snapshot_v1,
    adapt_double_play_decision_snapshot_v1,
    adapt_economic_summary_snapshot_v1,
    adapt_execution_state_snapshot_v1,
    adapt_market_instrument_snapshot_v1,
    adapt_market_ranking_snapshot_v1,
    adapt_safety_authority_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.contracts import UnavailableSnapshotV1
from src.webui.market_futures_ohlcv_readmodel_v0.builder import (
    build_market_futures_ohlcv_readmodel,
)
from src.webui.market_ranking_funnel_readmodel_v0.builder import (
    build_market_ranking_funnel_readmodel,
)

DIGEST = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
DIGEST_B = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
TS = datetime(2026, 7, 17, 9, 0, tzinfo=timezone.utc)
TS2 = datetime(2026, 7, 17, 9, 5, tzinfo=timezone.utc)
REPO = Path(__file__).resolve().parents[2]
OHLCV_FIXTURE = REPO / "tests/fixtures/market_futures_ohlcv_readmodel_v0/complete_minimal"
RANKING_FIXTURE = REPO / "tests/fixtures/market_ranking_funnel_readmodel_v0/complete_minimal"


def _metric(value: float | None, *, semantic: str = "COMPUTED"):
    return SimpleNamespace(semantic=semantic, value=value)


def test_market_lossless_projection_from_fixture() -> None:
    readmodel = build_market_futures_ohlcv_readmodel(OHLCV_FIXTURE)
    snap = adapt_market_instrument_snapshot_v1(
        readmodel,
        instrument_id="ETHUSDT",
        venue="binance_usdm_futures",
        generated_at=TS2,
        source_reference="fixture:ohlcv",
    )
    assert not isinstance(snap, UnavailableSnapshotV1)
    assert snap.instrument_id == "ETHUSDT"
    assert snap.venue == "binance_usdm_futures"
    assert snap.last_price == pytest.approx(4524.4122)
    assert snap.mark_price is None
    assert snap.ohlcv is not None
    assert snap.freshness_state == DashboardFreshnessStateV1.FRESH


def test_market_absent_and_dummy_and_btc_forbidden() -> None:
    absent = adapt_market_instrument_snapshot_v1(
        None, instrument_id="ETHUSDT", venue="binance_usdm_futures", generated_at=TS2
    )
    assert isinstance(absent, UnavailableSnapshotV1)
    assert absent.availability_state == DashboardAvailabilityStateV1.MISSING_SOURCE

    readmodel = build_market_futures_ohlcv_readmodel(OHLCV_FIXTURE)
    dummy = dict(readmodel)
    dummy["source"] = "dummy"
    banned = adapt_market_instrument_snapshot_v1(
        dummy, instrument_id="ETHUSDT", venue="binance_usdm_futures", generated_at=TS2
    )
    assert isinstance(banned, UnavailableSnapshotV1)
    assert banned.reason_code == "MARKET_OHLCV_DUMMY_FORBIDDEN"

    btc = adapt_market_instrument_snapshot_v1(
        readmodel, instrument_id="BTCUSDT", venue="binance_usdm_futures", generated_at=TS2
    )
    assert isinstance(btc, UnavailableSnapshotV1)
    assert btc.reason_code == "MARKET_INSTRUMENT_FORBIDDEN"


def test_market_nan_bar_rejected() -> None:
    readmodel = build_market_futures_ohlcv_readmodel(OHLCV_FIXTURE)
    payload = {
        **readmodel,
        "series": {
            "ETHUSDT": {
                "timeframe": "1d",
                "bars": [
                    {
                        "ts": "2026-05-27T00:00:00+00:00",
                        "open": 1.0,
                        "high": math.nan,
                        "low": 0.5,
                        "close": 0.9,
                        "volume": 1.0,
                    }
                ],
            }
        },
    }
    snap = adapt_market_instrument_snapshot_v1(
        payload, instrument_id="ETHUSDT", venue="binance_usdm_futures", generated_at=TS2
    )
    assert isinstance(snap, UnavailableSnapshotV1)


def test_ranking_projection_and_eligibility_not_inferred() -> None:
    readmodel = build_market_ranking_funnel_readmodel(RANKING_FIXTURE)
    snap = adapt_market_ranking_snapshot_v1(readmodel, generated_at=TS2)
    assert not isinstance(snap, UnavailableSnapshotV1)
    assert snap.selected_instrument_id == "ETHUSDT"
    assert snap.ranked_items[0].eligibility_status.value == "NOT_PROVIDED"
    assert snap.ranked_items[0].score == pytest.approx(0.91)
    absent = adapt_market_ranking_snapshot_v1(None, generated_at=TS2)
    assert isinstance(absent, UnavailableSnapshotV1)


def test_canonical_decision_projection_no_confidence_fabrication() -> None:
    evidence = SimpleNamespace(
        evidence_schema_version="canonical_trading_decision_evidence_v1",
        decision_outcome="enter_long",
        selected_side="long",
        reason_codes=("rc_b", "rc_a"),
        semantic_digest=DIGEST,
        decision_id="dec-1",
    )
    snap = adapt_canonical_decision_summary_v1(
        evidence, generated_at=TS2, effective_at=TS, evidence_status="replay_pass"
    )
    assert not isinstance(snap, UnavailableSnapshotV1)
    assert snap.decision_status == CanonicalDecisionStatusV1.ALLOW
    assert snap.direction == DecisionDirectionV1.LONG
    assert snap.confidence is None
    assert snap.reason_codes == ("rc_a", "rc_b")  # deterministic sort via contract
    assert (
        adapt_canonical_decision_summary_v1(
            None, generated_at=TS2, effective_at=TS
        ).availability_state
        == DashboardAvailabilityStateV1.MISSING_SOURCE
    )


def test_canonical_decision_invalid_digest() -> None:
    evidence = SimpleNamespace(
        evidence_schema_version="canonical_trading_decision_evidence_v1",
        decision_outcome="hold",
        selected_side="none",
        reason_codes=(),
        semantic_digest="not-a-digest",
        decision_id="dec-2",
    )
    snap = adapt_canonical_decision_summary_v1(evidence, generated_at=TS2, effective_at=TS)
    assert isinstance(snap, UnavailableSnapshotV1)
    assert snap.reason_code == "CANONICAL_DECISION_DIGEST_INVALID"


def test_double_play_projection_and_absent() -> None:
    composition = SimpleNamespace(
        composition_status="long_selected",
        conflict_status="none",
        reason_codes=("dp_b", "dp_a"),
        semantic_digest=DIGEST,
        composition_id="comp-1",
        chop_guard_status="none",
    )
    bull = SimpleNamespace(status="CONFIRMED", confidence=0.8, reason_codes=("b1",))
    bear = SimpleNamespace(status="OBSERVE", confidence=0.2, reason_codes=("e1",))
    snap = adapt_double_play_decision_snapshot_v1(
        composition,
        generated_at=TS2,
        effective_at=TS,
        bull_assessment=bull,
        bear_assessment=bear,
    )
    assert not isinstance(snap, UnavailableSnapshotV1)
    assert snap.composition_result == "long_selected"
    assert snap.arbitration_status == "none"
    assert snap.blockers == ("dp_a", "dp_b")
    assert snap.bull_assessment.score == pytest.approx(0.8)
    absent = adapt_double_play_decision_snapshot_v1(
        None, generated_at=TS2, effective_at=TS, bull_assessment=bull, bear_assessment=bear
    )
    assert isinstance(absent, UnavailableSnapshotV1)


def test_safety_authority_not_bound_is_unavailable_not_false() -> None:
    snap = adapt_safety_authority_snapshot_v1(None, generated_at=TS2)
    assert isinstance(snap, UnavailableSnapshotV1)
    assert snap.availability_state == DashboardAvailabilityStateV1.NOT_BOUND
    bound = adapt_safety_authority_snapshot_v1(
        {
            "authority_classification": AuthorityClassificationV1.UNKNOWN,
            "kill_switch_state": TriStateV1.UNKNOWN,
            "risk_gate_state": TriStateV1.UNKNOWN,
            "execution_permission_state": TriStateV1.UNKNOWN,
            "fail_closed_reason_codes": ("missing_runtime_binding",),
            "producer_module": "tests.fixture.safety",
            "source_reference": "tests/safety",
        },
        generated_at=TS2,
        effective_at=TS,
    )
    assert not isinstance(bound, UnavailableSnapshotV1)
    assert bound.kill_switch_state == TriStateV1.UNKNOWN
    assert bound.execution_permission_state == TriStateV1.UNKNOWN


def test_execution_unknown_not_converted_to_no_order() -> None:
    absent = adapt_execution_state_snapshot_v1(None, generated_at=TS2, effective_at=TS)
    assert isinstance(absent, UnavailableSnapshotV1)
    assert absent.reason_code == "EXECUTION_SOURCE_ABSENT"
    assert "UNAVAILABLE" in absent.detail or "Missing execution" in absent.detail

    source = SimpleNamespace(
        decision_outcome="reconcile_only",
        reconciliation_state="unknown",
        position_state="submission_unknown",
        semantic_digest=DIGEST,
        policy_decision_id="pol-1",
    )
    snap = adapt_execution_state_snapshot_v1(
        source,
        generated_at=TS2,
        effective_at=TS,
        operating_mode=OperatingModeV1.OFFLINE,
    )
    assert not isinstance(snap, UnavailableSnapshotV1)
    assert snap.intent_state == "reconcile_only"
    assert snap.fill_state == "NOT_PROVIDED"
    assert snap.unknown_outcome_state == "submission_unknown"


def test_execution_fill_not_provided() -> None:
    source = SimpleNamespace(
        decision_outcome="hold",
        reconciliation_state="reconciled",
        position_state="flat_reconciled",
        semantic_digest=DIGEST,
        policy_decision_id="pol-2",
    )
    snap = adapt_execution_state_snapshot_v1(source, generated_at=TS2, effective_at=TS)
    assert not isinstance(snap, UnavailableSnapshotV1)
    assert snap.fill_state == "NOT_PROVIDED"
    assert snap.unknown_outcome_state == "flat_reconciled"


def test_economic_no_recalculation_and_absent() -> None:
    evidence = SimpleNamespace(
        status="ECONOMICALLY_VIABLE_OFFLINE",
        manifest_digest=DIGEST,
        owner="economic_viability_evidence_v1",
        gross_return=_metric(0.12),
        net_return=_metric(0.10),
        profit_factor=_metric(1.4),
        max_drawdown=_metric(0.2),
        fee_drag=_metric(0.01),
        net_expectancy=_metric(0.05),
        trade_count=_metric(42.0),
    )
    snap = adapt_economic_summary_snapshot_v1(evidence, generated_at=TS2, effective_at=TS)
    assert not isinstance(snap, UnavailableSnapshotV1)
    assert snap.economic_gate_status == EconomicGateStatusV1.PASS
    assert snap.authoritative_gate is True
    assert snap.profit_factor == pytest.approx(1.4)
    assert snap.sample_size == 42
    # Non-computed stays None (no zero fallback).
    evidence2 = SimpleNamespace(
        status="RESEARCH_ONLY",
        manifest_digest=DIGEST_B,
        owner="economic_viability_evidence_v1",
        gross_return=_metric(None, semantic="NOT_COMPUTED"),
        net_return=_metric(None, semantic="NOT_COMPUTED"),
        profit_factor=_metric(None, semantic="NOT_COMPUTED"),
        max_drawdown=_metric(None, semantic="NOT_COMPUTED"),
        fee_drag=_metric(None, semantic="NOT_COMPUTED"),
        net_expectancy=_metric(None, semantic="NOT_COMPUTED"),
        trade_count=_metric(None, semantic="NOT_COMPUTED"),
    )
    snap2 = adapt_economic_summary_snapshot_v1(evidence2, generated_at=TS2, effective_at=TS)
    assert not isinstance(snap2, UnavailableSnapshotV1)
    assert snap2.profit_factor is None
    assert snap2.authoritative_gate is False
    assert isinstance(
        adapt_economic_summary_snapshot_v1(None, generated_at=TS2, effective_at=TS),
        UnavailableSnapshotV1,
    )


def test_diagnostics_non_authority_marker() -> None:
    artifacts = {
        "schema_version": "offline_productive_linear_diagnostics_support_bundle.v0",
        "aggregate_status": "DIAGNOSTIC_SUPPORT_COMPLETE",
        "source_statuses": {"cost_diagnostics": "OK", "factor_exposure": "INDICATIVE"},
        "output_digest": DIGEST,
        "diagnostic_evidence_id": "diag-1",
        "authority_effect": "NONE",
    }
    snap = adapt_diagnostics_summary_snapshot_v1(
        artifacts, generated_at=TS2, effective_at=TS, bundle_reference="evidence/diag"
    )
    assert not isinstance(snap, UnavailableSnapshotV1)
    assert snap.non_authoritative is True
    assert snap.diagnostic_only is True
    assert "aggregate:DIAGNOSTIC_SUPPORT_COMPLETE" in snap.diagnostic_statuses


def test_freshness_explicit_evaluation_time_and_missing_not_fresh() -> None:
    market = adapt_market_instrument_snapshot_v1(
        build_market_futures_ohlcv_readmodel(OHLCV_FIXTURE),
        instrument_id="ETHUSDT",
        venue="binance_usdm_futures",
        generated_at=TS2,
    )
    page_time = datetime(2026, 5, 27, 0, 10, tzinfo=timezone.utc)
    freshness = adapt_dashboard_freshness_snapshot_v1(
        page_generated_at=page_time,
        sources={"market": market, "decision": None},
    )
    by_key = {e.source_key: e for e in freshness.source_entries}
    assert by_key["decision"].missing is True
    assert by_key["decision"].freshness_state == DashboardFreshnessStateV1.MISSING
    assert by_key["market"].missing is False
    # 10 minutes after bar → STALE under default policy (fresh<=5m).
    assert by_key["market"].freshness_state == DashboardFreshnessStateV1.STALE


def test_deterministic_serialization_roundtrip_shape() -> None:
    evidence = SimpleNamespace(
        evidence_schema_version="canonical_trading_decision_evidence_v1",
        decision_outcome="blocked",
        selected_side="none",
        reason_codes=("z", "a"),
        semantic_digest=DIGEST,
        decision_id="dec-ser",
    )
    snap = adapt_canonical_decision_summary_v1(evidence, generated_at=TS2, effective_at=TS)
    assert not isinstance(snap, UnavailableSnapshotV1)
    payload = to_json_dict(snap)
    encoded = dumps_json(snap)
    assert '"decision_status":"BLOCK"' in encoded or '"decision_status": "BLOCK"' in encoded
    assert payload["reason_codes"] == ["a", "z"]
    assert payload["decision_status"] == "BLOCK"


def test_immutable_adapter_results() -> None:
    snap = adapt_safety_authority_snapshot_v1(
        {
            "authority_classification": "UNKNOWN",
            "kill_switch_state": "UNKNOWN",
            "risk_gate_state": "UNKNOWN",
            "execution_permission_state": "UNKNOWN",
            "source_reference": "x",
            "producer_module": "tests.x",
        },
        generated_at=TS2,
    )
    assert not isinstance(snap, UnavailableSnapshotV1)
    with pytest.raises(Exception):
        snap.kill_switch_state = TriStateV1.FALSE  # type: ignore[misc]
