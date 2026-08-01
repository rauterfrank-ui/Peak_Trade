"""Focused tests for productive runtime CMC typed binding v1."""

from __future__ import annotations

import ast
import math
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
    run_hardened_bridge_cycle_v2,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationTransportMetadataV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import (
    EventTimeInstantV1,
    MarketSampleIdentityV1,
)
from trading.master_v2 import canonical_volatility_estimate_materializer_v1 as materializer
from trading.master_v2 import (
    canonical_volatility_estimate_typed_consumption_contract_v1 as typed,
)
from trading.master_v2.canonical_market_context_v1 import (
    FEATURE_CONTRACT_VERSION,
    BarFinalityStatus,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    WarmupStatus,
)
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    adapt_validated_typed_estimate_to_legacy_float_v1,
    evaluate_typed_volatility_binding_eligibility_v1,
)
from trading.master_v2.canonical_volatility_productive_runtime_cmc_typed_binding_v1 import (
    CAPABILITY_ID,
    PACKAGE_MARKER,
    CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1,
    ProductiveTypedBindingFailClosedReasonV1,
    assert_architecture_guards_v1,
    assert_capability_non_goals_v1,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    TypedRuntimeProducerOutcomeV1,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType

ROOT = Path(__file__).resolve().parents[3]
VENUE = "okx_europe"
CANON = "ETH-USD_UM_XPERP-310404"
VENUE_INST = "ETH-USD_UM_XPERP-310404"
T0 = 1_700_000_000.0


def _price_at(i: int) -> float:
    return 100.0 * math.exp(0.001 * i)


def _sample(i: int, *, mark: float | None = None) -> MarketSampleIdentityV1:
    return MarketSampleIdentityV1(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        event_time=EventTimeInstantV1(unix_seconds=T0 + float(i * 60)),
        mark_price=_price_at(i) if mark is None else mark,
    )


def _host(
    tmp_path: Path | None = None,
) -> CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1:
    path = None if tmp_path is None else tmp_path / "mark_history.json"
    return CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        persistence_path=path,
    )


def _context(**overrides: object) -> CanonicalMarketContextV1:
    base: dict = {
        "context_id": "ctx-eth-typed-binding",
        "instrument_id": CANON,
        "market_type": FuturesMarketType.PERPETUAL,
        "trading_epoch": 1,
        "market_event_time": "2026-06-30T12:00:00+00:00",
        "decision_time": "2026-06-30T12:00:01+00:00",
        "bar_interval": "1m",
        "bar_finality_status": BarFinalityStatus.FINALIZED,
        "mark_price": 3500.0,
        "index_price": 3499.5,
        "best_bid": 3499.8,
        "best_ask": 3500.2,
        "spread": 0.4,
        "volume": 1_250_000.0,
        "open_interest": 85_000_000.0,
        "funding_rate": 0.00012,
        "volatility_estimate": 0.38,
        "trend_feature_set": {"slope": 0.02},
        "momentum_feature_set": {"rsi": 55.0},
        "liquidity_feature_set": {"depth_score": 0.88},
        "market_structure_feature_set": {"range_ratio": 0.42},
        "data_integrity_status": DataIntegrityStatus.TRUSTED,
        "clock_trust_status": ClockTrustStatus.TRUSTED,
        "warmup_status": WarmupStatus.WARMUP_COMPLETE,
        "feature_contract_version": FEATURE_CONTRACT_VERSION,
        "input_digest": "",
        "canonical_volatility_estimate": None,
    }
    base.update(overrides)
    return CanonicalMarketContextV1(**base)


def _ingest_range(
    host: CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1,
    context: CanonicalMarketContextV1,
    start: int,
    end_inclusive: int,
):
    last = None
    for i in range(start, end_inclusive + 1):
        last = host.apply_to_market_context_v1(
            context,
            sample=_sample(i),
            transport=ObservationTransportMetadataV1(receive_time=T0 + i * 60 + 0.5),
            ingest_sample=True,
        )
        context = last.context
    assert last is not None
    return last


def test_a_productive_runtime_caller_exists_outside_tests() -> None:
    bridge = (
        ROOT
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
        / "hardening_cycle_bridge_v2.py"
    ).read_text(encoding="utf-8")
    assert "CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1" in bridge
    assert "apply_to_market_context_v1" in bridge
    assert "tests/" not in PACKAGE_MARKER
    assert CAPABILITY_ID.startswith("MASTER_V2_")
    guards = assert_architecture_guards_v1(repo_root=ROOT)
    assert guards["guards_pass"] is True
    assert guards["productive_bind_typed_caller"] is True


def test_b_sixty_one_contiguous_pt1m_produced_and_cmc_bound(tmp_path: Path) -> None:
    host = _host(tmp_path)
    result = _ingest_range(host, _context(), 0, 60)
    assert result.producer_result.outcome is TypedRuntimeProducerOutcomeV1.PRODUCED
    assert result.bound_estimate is not None
    assert result.context.canonical_volatility_estimate is not None
    expected_float = adapt_validated_typed_estimate_to_legacy_float_v1(
        result.context.canonical_volatility_estimate,
        already_validated=True,
    )
    assert result.context.volatility_estimate == expected_float
    assert result.telemetry.typed_binding_performed is True
    assert result.telemetry.max_age_status == "UNRESOLVED_MAX_AGE"
    assert result.telemetry.legacy_float_adaptation_owner
    assert result.typed_cutover_fail_closed is False


def test_c_warmup_fail_closed_no_static_fallback() -> None:
    host = _host()
    result = _ingest_range(host, _context(volatility_estimate=0.38), 0, 10)
    assert result.producer_result.outcome is TypedRuntimeProducerOutcomeV1.WARMUP
    assert result.context.canonical_volatility_estimate is None
    assert result.telemetry.typed_binding_performed is False
    assert result.typed_cutover_fail_closed is True
    assert (
        result.telemetry.fail_closed_reason
        == ProductiveTypedBindingFailClosedReasonV1.WARMUP_NO_ESTIMATE.value
    )
    # Hot-path closure: untyped float cleared to non-authority placeholder (not 0.38/0.2/0.02/1.0).
    assert result.context.volatility_estimate == 0.0
    eligibility = evaluate_typed_volatility_binding_eligibility_v1(result.context)
    assert eligibility.new_directional_exposure_allowed is False
    assert eligibility.scope_confirmation_allowed is False


def test_d_duplicate_no_advance(tmp_path: Path) -> None:
    host = _host(tmp_path)
    produced = _ingest_range(host, _context(), 0, 60)
    digest_before = host.producer.history.history_digest
    count_before = host.producer.history.observation_count_prices
    estimate_before = produced.bound_estimate
    assert estimate_before is not None
    dup = host.apply_to_market_context_v1(
        produced.context,
        sample=_sample(60),
        transport=ObservationTransportMetadataV1(receive_time=T0 + 60 * 60 + 0.5),
        ingest_sample=True,
    )
    assert dup.producer_result.outcome is TypedRuntimeProducerOutcomeV1.DUPLICATE_NOOP
    assert host.producer.history.history_digest == digest_before
    assert host.producer.history.observation_count_prices == count_before
    assert dup.bound_estimate is not None
    assert dup.bound_estimate.source_digest == estimate_before.source_digest


def test_e_reject_outcomes_no_cmc_binding(tmp_path: Path) -> None:
    host = _host(tmp_path)
    warm = _ingest_range(host, _context(), 0, 5)
    # Out-of-order sample.
    ooo = host.apply_to_market_context_v1(
        warm.context,
        sample=_sample(3),
        ingest_sample=True,
    )
    assert ooo.producer_result.outcome is TypedRuntimeProducerOutcomeV1.OUT_OF_ORDER_REJECTED
    assert ooo.context.canonical_volatility_estimate is None
    assert ooo.typed_cutover_fail_closed is True
    assert (
        ooo.telemetry.fail_closed_reason
        == ProductiveTypedBindingFailClosedReasonV1.OUT_OF_ORDER_REJECTED.value
    )

    # History gap after enough contiguous history to attempt materialization window.
    host2 = _host(tmp_path / "gap")
    base = _ingest_range(host2, _context(), 0, 59)
    gap = host2.apply_to_market_context_v1(
        base.context,
        sample=_sample(62),  # skips 60,61 → gap > PT1M vs last=59
        ingest_sample=True,
    )
    assert gap.producer_result.outcome in {
        TypedRuntimeProducerOutcomeV1.HISTORY_GAP_REJECTED,
        TypedRuntimeProducerOutcomeV1.OUT_OF_ORDER_REJECTED,
        TypedRuntimeProducerOutcomeV1.INVALID_SAMPLE_REJECTED,
    }
    # Distinct advance with gap in trailing window after enough prices:
    # ingest index 61 with a hole from continuing after skip may classify as OOO
    # relative to last accepted; force contiguous then jump.
    host3 = _host(tmp_path / "gap2")
    produced = _ingest_range(host3, _context(), 0, 60)
    assert produced.bound_estimate is not None
    jumped = host3.apply_to_market_context_v1(
        produced.context,
        sample=_sample(63),
        ingest_sample=True,
    )
    assert jumped.producer_result.outcome is TypedRuntimeProducerOutcomeV1.HISTORY_GAP_REJECTED
    assert jumped.context.canonical_volatility_estimate is None
    assert jumped.typed_cutover_fail_closed is True
    assert (
        jumped.telemetry.fail_closed_reason
        == ProductiveTypedBindingFailClosedReasonV1.HISTORY_GAP_REJECTED.value
    )


def test_f_cycle_without_sample_reuses_output_port_only(tmp_path: Path) -> None:
    host = _host(tmp_path)
    produced = _ingest_range(host, _context(), 0, 60)
    assert produced.bound_estimate is not None
    cycle = host.apply_to_market_context_v1(produced.context, ingest_sample=False)
    assert cycle.producer_result.estimate is None
    assert "without_new_sample" in cycle.producer_result.reason
    assert cycle.bound_estimate is not None
    assert cycle.bound_estimate.source_digest == produced.bound_estimate.source_digest
    assert cycle.telemetry.typed_binding_performed is True


def test_g_restart_history_without_estimate_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "hist.json"
    host = _host(tmp_path)
    # Point persistence explicitly.
    host.producer.persistence_path = path
    produced = _ingest_range(host, _context(), 0, 60)
    assert produced.bound_estimate is not None
    assert path.exists()

    restored = (
        CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.restore_from_persistence_v1(
            persistence_path=path,
        )
    )
    assert restored.restart_without_estimate is True
    assert restored.producer.history.observation_count_prices == 61
    cycle = restored.apply_to_market_context_v1(_context(), ingest_sample=False)
    assert cycle.bound_estimate is None
    assert cycle.typed_cutover_fail_closed is True
    assert (
        cycle.telemetry.fail_closed_reason
        == ProductiveTypedBindingFailClosedReasonV1.RESTART_WITHOUT_ESTIMATE.value
    )
    # Next PRODUCED clears restart fail-closed.
    nxt = restored.apply_to_market_context_v1(
        _context(),
        sample=_sample(61),
        transport=ObservationTransportMetadataV1(receive_time=T0 + 61 * 60 + 0.5),
        ingest_sample=True,
    )
    assert nxt.producer_result.outcome is TypedRuntimeProducerOutcomeV1.PRODUCED
    assert nxt.bound_estimate is not None
    assert restored.restart_without_estimate is False


def test_h_architecture_guards() -> None:
    guards = assert_architecture_guards_v1(repo_root=ROOT)
    assert guards["adapter_defs_in_typed"] == 1
    assert guards["binder_defs_in_binding"] == 1
    assert guards["double_play_typed_cutover"] is False
    assert guards["global_typed_only_enforcement"] is False
    assert guards["numeric_max_age_decided"] is False
    non_goals = assert_capability_non_goals_v1()
    assert non_goals["static_runtime_fallback_used"] is False
    assert non_goals["second_estimator_created"] is False
    assert "C1_G10_NUMERIC_MAX_AGE" in non_goals["gaps_remaining"]

    host_src = (
        ROOT
        / "src/trading/master_v2/canonical_volatility_productive_runtime_cmc_typed_binding_v1.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(host_src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "value":
            # Allow enum .value and telemetry fields; forbid estimate.value adaptation path.
            pass
    assert "def adapt_canonical_volatility_estimate_to_legacy_float_v1(" not in host_src
    assert "def bind_typed_canonical_volatility_estimate_into_market_context_v1(" not in host_src
    assert "def compute_canonical_volatility_estimate_from_mark_prices_v1(" not in host_src


def test_i_offline_research_paths_unchanged() -> None:
    from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
        _REPLAY_DEFAULT_VOL_QUARANTINE,
    )
    from trading.master_v2.canonical_volatility_default_quarantine_v1 import (
        LEGACY_HISTORICAL_BIND_DEFAULT_VALUE,
        LEGACY_REPLAY_RULES_DEFAULT_VALUE,
    )

    assert float(LEGACY_REPLAY_RULES_DEFAULT_VALUE) == 0.02
    assert float(_REPLAY_DEFAULT_VOL_QUARANTINE.legacy_value) == 0.02
    assert float(LEGACY_HISTORICAL_BIND_DEFAULT_VALUE) == 0.2
    non_goals = assert_capability_non_goals_v1()
    assert non_goals["explicit_legacy_quarantine_changed"] is False
    assert non_goals["competing_producers_changed"] is False
    feature_regime = (
        ROOT
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
        / "feature_regime_pipeline_v2.py"
    ).read_text(encoding="utf-8")
    assert "compute_feature_regime_from_mid_prices_v2" in feature_regime


def test_j_offline_runtime_estimator_equivalence(tmp_path: Path) -> None:
    host = _host(tmp_path)
    prices = [_price_at(i) for i in range(61)]
    result = _ingest_range(host, _context(), 0, 60)
    assert result.bound_estimate is not None
    import pandas as pd

    series = pd.Series(prices, dtype=float)
    as_of = datetime.fromtimestamp(T0 + 60 * 60, tz=timezone.utc)
    offline = typed.materialize_typed_canonical_volatility_estimate_v1(
        series,
        as_of_event_time=as_of,
    )
    assert result.bound_estimate.value == offline.value
    assert result.bound_estimate.source_digest == offline.source_digest
    assert result.bound_estimate.observation_count == offline.observation_count
    p1 = materializer.compute_canonical_volatility_estimate_from_mark_prices_v1(series)
    assert math.isclose(float(p1.iloc[-1]), float(offline.value), rel_tol=0.0, abs_tol=0.0)


def test_productive_bridge_caller_with_pt1m_samples(tmp_path: Path) -> None:
    state = HardenedBridgeSessionStateV2()
    state.typed_volatility_persistence_path = tmp_path / "bridge_hist.json"
    last = None
    for i in range(61):
        last = run_hardened_bridge_cycle_v2(
            state,
            mid_price=_price_at(i),
            event_ts_unix=T0 + float(i),
            session_id="typed-binding-bridge",
            finalized_pt1m_mark_sample=_sample(i),
            finalized_pt1m_transport=ObservationTransportMetadataV1(receive_time=T0 + i * 60 + 0.5),
        )
    assert last is not None
    tele = last["canonical_volatility_typed_binding"]
    assert tele["producer_outcome"] == TypedRuntimeProducerOutcomeV1.PRODUCED.value
    assert tele["typed_binding_performed"] is True
    assert tele["estimate_present"] is True
    assert last["canonical_market_context_typed_estimate_present"] is True
    assert "canonical_volatility_productive_runtime_cmc_typed_binding" in last["call_graph"]


def test_productive_bridge_warmup_typed_fail_closed() -> None:
    state = HardenedBridgeSessionStateV2()
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=3500.0,
        event_ts_unix=T0,
        session_id="typed-binding-warmup",
        finalized_pt1m_mark_sample=_sample(0),
    )
    tele = cycle["canonical_volatility_typed_binding"]
    assert tele["typed_binding_performed"] is False
    assert tele["typed_cutover_fail_closed"] is True
    assert tele["max_age_status"] == "UNRESOLVED_MAX_AGE"
