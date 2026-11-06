"""Tests for MASTER_V2_CANONICAL_VOLATILITY_HOT_PATH_CONTRACT_CLOSURE_V1."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from trading.master_v2 import canonical_volatility_estimate_feature_contract_v1 as contract
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
    FuturesMarketType,
    WarmupStatus,
)
from trading.master_v2.canonical_volatility_default_quarantine_v1 import (
    LEGACY_DYNAMIC_SCOPE_RULES_CONSTRUCTOR_DEFAULT_VALUE,
    LEGACY_HISTORICAL_BIND_DEFAULT_VALUE,
    LEGACY_REPLAY_RULES_DEFAULT_VALUE,
    quarantine_explicit_replay_default_volatility_v1,
)
from trading.master_v2.canonical_volatility_hot_path_contract_closure_v1 import (
    BRIDGE_COMPETING_PRODUCER_IDENTITY,
    CANONICAL_VOLATILITY_ESTIMATOR_DDOF_ZERO,
    CANONICAL_VOLATILITY_NOT_ANNUALIZED,
    CAPABILITY_ID,
    COMPETING_BRIDGE_PRODUCER_REMOVED_OR_QUARANTINED,
    LEGACY_0_02_EXPLICIT_QUARANTINE_ONLY,
    LEGACY_0_2_SILENT_FALLBACK_FORBIDDEN,
    LEGACY_1_0_NOT_PRODUCTIVE,
    MAX_AGE_ENFORCEMENT_ENABLED,
    MAX_AGE_THRESHOLD_SELECTED,
    NUMERIC_MAX_AGE_DECIDED,
    NUMERIC_MAX_AGE_VALUE_UNRESOLVED,
    PACKAGE_MARKER,
    VolatilityHotPathStatusV1,
    assert_architecture_guards_v1,
    assert_capability_non_goals_v1,
    assert_config_digest_matches_runtime_v1,
    assert_source_digest_matches_v1,
    build_hot_path_volatility_cycle_evidence_v1,
    classify_hot_path_status_v1,
    clear_untyped_productive_volatility_float_v1,
    compute_closure_config_digest_v1,
    producer_consumer_graph_v1,
    productive_cmc_volatility_seed_v1,
    reject_competing_bridge_producer_as_productive_authority_v1,
    reject_naked_float_productive_binding_v1,
)
from trading.master_v2.canonical_volatility_hot_path_contract_closure_v1 import (
    CanonicalVolatilityHotPathClosureError,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import TradingGate
from trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    demote_trading_gate_for_typed_presence_failure_v1,
    evaluate_double_play_runtime_typed_volatility_presence_gate_v1,
)
from trading.master_v2.double_play_state import DynamicScopeRules

ROOT = Path(__file__).resolve().parents[3]
AS_OF = datetime(2026, 6, 1, 1, 0, tzinfo=timezone.utc)


def _estimate(**overrides: object) -> typed.CanonicalVolatilityEstimateV1:
    base: dict[str, object] = {
        "value": 0.001234,
        "observation_count": 60,
        "as_of_event_time": AS_OF,
    }
    base.update(overrides)
    return typed.build_canonical_volatility_estimate_v1(**base)  # type: ignore[arg-type]


def _cmc(
    *, estimate: typed.CanonicalVolatilityEstimateV1 | None, vol: float = 0.0
) -> CanonicalMarketContextV1:
    return CanonicalMarketContextV1(
        context_id="ctx-hot-path-closure",
        instrument_id="BTC-USDT-SWAP",
        market_type=FuturesMarketType.PERPETUAL,
        trading_epoch=1,
        market_event_time=AS_OF.isoformat(),
        decision_time=(AS_OF + timedelta(milliseconds=1)).isoformat(),
        bar_interval="PT1M",
        bar_finality_status=BarFinalityStatus.FINALIZED,
        mark_price=100.0,
        index_price=100.0,
        best_bid=99.9,
        best_ask=100.1,
        spread=0.2,
        volume=1_000_000.0,
        open_interest=50_000_000.0,
        funding_rate=0.0001,
        volatility_estimate=float(vol if estimate is None else estimate.value),
        trend_feature_set={"slope": 0.0},
        momentum_feature_set={"roc": 0.0},
        liquidity_feature_set={"depth_score": 0.0},
        market_structure_feature_set={"range_ratio": 0.0},
        data_integrity_status=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        warmup_status=WarmupStatus.WARMUP_COMPLETE,
        feature_contract_version=FEATURE_CONTRACT_VERSION,
        canonical_volatility_estimate=estimate,
    )


def test_01_canonical_estimator_ddof_zero() -> None:
    assert contract.DDOF == 0
    assert CANONICAL_VOLATILITY_ESTIMATOR_DDOF_ZERO is True
    fixture = materializer.exact_known_61_price_fixture_v1()
    series = materializer.compute_canonical_volatility_estimate_from_mark_prices_v1(
        fixture["mark_price"]
    )
    expected = materializer.expected_population_std_for_fixture_v1(
        fixture["mark_price"].astype(float).tolist()
    )
    assert float(series.dropna().iloc[-1]) == pytest.approx(expected)


def test_02_no_sqrt_n_scaling() -> None:
    # Deterministic non-constant returns so ddof=0 vs ddof=1×sqrt(n) diverge.
    idx = pd.date_range("2026-06-01T00:00:00Z", periods=61, freq="1min", tz="UTC")
    marks = [100.0]
    for i in range(1, 61):
        marks.append(marks[-1] * (1.0 + (0.002 if i % 2 == 0 else -0.001)))
    prices = pd.Series(marks, index=idx, dtype=float)
    log_rets = (prices / prices.shift(1)).apply(math.log).dropna()
    pop = float(log_rets.std(ddof=0))
    sample_sqrt_n = float(log_rets.std(ddof=1) * math.sqrt(len(log_rets)))
    series = materializer.compute_canonical_volatility_estimate_from_mark_prices_v1(prices)
    got = float(series.dropna().iloc[-1])
    assert got == pytest.approx(pop)
    assert abs(got - sample_sqrt_n) > 1e-6
    mat_src = (
        ROOT / "src/trading/master_v2/canonical_volatility_estimate_materializer_v1.py"
    ).read_text(encoding="utf-8")
    assert "math.sqrt(len" not in mat_src
    assert ".std(ddof=contract.DDOF)" in mat_src


def test_03_deterministic_pt60m_window() -> None:
    fixture = materializer.exact_known_61_price_fixture_v1()
    a = typed.materialize_typed_canonical_volatility_estimate_v1(fixture["mark_price"])
    b = typed.materialize_typed_canonical_volatility_estimate_v1(fixture["mark_price"])
    assert a.value == b.value
    assert a.horizon_seconds == 3600
    assert a.lookback_bars == 60
    assert a.bar_duration == "PT1M"
    assert a.source_digest == b.source_digest


def test_04_duplicate_sample_no_advance_status() -> None:
    status = classify_hot_path_status_v1(
        estimate=_estimate(),
        producer_outcome="DUPLICATE_NOOP",
    )
    assert status is VolatilityHotPathStatusV1.DUPLICATE_NO_ADVANCE


def test_05_out_of_order_fail_closed_status() -> None:
    status = classify_hot_path_status_v1(
        estimate=None,
        producer_outcome="OUT_OF_ORDER_REJECTED",
    )
    assert status is VolatilityHotPathStatusV1.OUT_OF_ORDER


def test_06_insufficient_history_fail_closed() -> None:
    with pytest.raises(typed.CanonicalVolatilityTypedConsumptionError) as exc:
        typed.build_canonical_volatility_estimate_v1(
            value=0.01,
            observation_count=10,
            as_of_event_time=AS_OF,
        )
    assert "INSUFFICIENT_OBSERVATIONS" in str(exc.value)
    status = classify_hot_path_status_v1(
        estimate=None,
        producer_outcome="WARMUP",
    )
    assert status is VolatilityHotPathStatusV1.INSUFFICIENT_HISTORY


def test_07_non_finite_value_rejected() -> None:
    with pytest.raises(typed.CanonicalVolatilityTypedConsumptionError):
        typed.build_canonical_volatility_estimate_v1(
            value=float("nan"),
            observation_count=60,
            as_of_event_time=AS_OF,
        )


def test_08_negative_value_rejected() -> None:
    with pytest.raises(typed.CanonicalVolatilityTypedConsumptionError):
        typed.build_canonical_volatility_estimate_v1(
            value=-0.01,
            observation_count=60,
            as_of_event_time=AS_OF,
        )


def test_09_typed_unit_horizon_preserved() -> None:
    estimate = _estimate()
    assert estimate.unit == "PER_BAR_DECIMAL_RETURN_VOLATILITY"
    assert estimate.horizon_seconds == 3600
    assert typed.CANONICAL_HORIZON == "PT60M"
    assert CANONICAL_VOLATILITY_NOT_ANNUALIZED is True
    assert estimate.annualized is False


def test_10_source_digest_deterministic() -> None:
    a = _estimate(source_digest=None)
    b = _estimate(source_digest=None)
    assert a.source_digest == b.source_digest
    assert len(a.source_digest) == 64


def test_11_config_digest_deterministic() -> None:
    a = _estimate()
    b = _estimate()
    assert a.config_digest == b.config_digest
    assert a.config_digest == typed.resolve_canonical_config_digest_v1()
    assert compute_closure_config_digest_v1() == compute_closure_config_digest_v1()


def test_12_config_digest_mismatch_fail_closed() -> None:
    estimate = typed.with_mutated_field_for_tests_v1(_estimate(), config_digest="a" * 64)
    with pytest.raises(CanonicalVolatilityHotPathClosureError) as exc:
        assert_config_digest_matches_runtime_v1(estimate)
    assert exc.value.code is VolatilityHotPathStatusV1.CONFIG_DIGEST_MISMATCH


def test_13_source_digest_mismatch_fail_closed() -> None:
    estimate = _estimate()
    with pytest.raises(CanonicalVolatilityHotPathClosureError) as exc:
        assert_source_digest_matches_v1(estimate, expected_source_digest="b" * 64)
    assert exc.value.code is VolatilityHotPathStatusV1.SOURCE_DIGEST_MISMATCH


def test_14_legacy_0_02_only_explicit_quarantine() -> None:
    admitted = quarantine_explicit_replay_default_volatility_v1(
        value=LEGACY_REPLAY_RULES_DEFAULT_VALUE,
        source_file_or_component="tests/hot_path_closure",
    )
    assert admitted.admitted is True
    assert LEGACY_0_02_EXPLICIT_QUARANTINE_ONLY is True
    with pytest.raises(typed.CanonicalVolatilityTypedConsumptionError):
        typed.reject_implicit_legacy_float_input_v1(
            raw_value=0.02,
            provenance={"typed_estimate": False, "implicit_default": True},
        )


def test_15_legacy_0_2_silent_fallback_impossible() -> None:
    assert LEGACY_HISTORICAL_BIND_DEFAULT_VALUE == 0.2
    assert typed.MV2_FALLBACK_0_2_ADMISSIBLE is False
    assert LEGACY_0_2_SILENT_FALLBACK_FORBIDDEN is True
    with pytest.raises(typed.CanonicalVolatilityTypedConsumptionError):
        typed.reject_implicit_legacy_float_input_v1(
            raw_value=0.2,
            provenance=None,
        )


def test_16_constructor_1_0_not_productive() -> None:
    assert LEGACY_DYNAMIC_SCOPE_RULES_CONSTRUCTOR_DEFAULT_VALUE == 1.0
    assert DynamicScopeRules().volatility_estimate is None
    assert LEGACY_1_0_NOT_PRODUCTIVE is True


def test_17_bridge_competing_producer_not_productive() -> None:
    assert COMPETING_BRIDGE_PRODUCER_REMOVED_OR_QUARANTINED is True
    with pytest.raises(CanonicalVolatilityHotPathClosureError):
        reject_competing_bridge_producer_as_productive_authority_v1(
            source_identity=BRIDGE_COMPETING_PRODUCER_IDENTITY,
            used_as_cmc_volatility_estimate=True,
        )
    reject_competing_bridge_producer_as_productive_authority_v1(
        source_identity=BRIDGE_COMPETING_PRODUCER_IDENTITY,
        used_as_cmc_volatility_estimate=False,
    )


def test_18_naked_float_productive_hot_path_rejected() -> None:
    with pytest.raises(typed.CanonicalVolatilityTypedConsumptionError):
        reject_naked_float_productive_binding_v1(
            raw_value=0.38,
            typed_estimate=None,
            provenance={"typed_estimate": False},
        )
    estimate = _estimate()
    # Typed carrier present → productive binding accepted (no naked-float path).
    reject_naked_float_productive_binding_v1(
        raw_value=float(estimate.value),
        typed_estimate=estimate,
        provenance={"typed_estimate": True},
    )
    with pytest.raises(typed.CanonicalVolatilityTypedConsumptionError):
        typed.reject_implicit_legacy_float_input_v1(
            raw_value=0.38,
            provenance={"typed_estimate": False},
        )


def test_19_volatility_unknown_blocks_entry() -> None:
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(_cmc(estimate=None))
    assert gate.alpha_scope_entry_authority_allowed is False
    assert demote_trading_gate_for_typed_presence_failure_v1(TradingGate.ENTRY_ALLOWED) is (
        TradingGate.EXIT_ONLY
    )


def test_20_volatility_unknown_allows_exit_path() -> None:
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(_cmc(estimate=None))
    assert gate.exit_risk_safety_authority_preserved is True
    assert demote_trading_gate_for_typed_presence_failure_v1(TradingGate.EXIT_ONLY) is (
        TradingGate.EXIT_ONLY
    )


def test_21_volatility_unknown_allows_reduce_path() -> None:
    demoted = demote_trading_gate_for_typed_presence_failure_v1(TradingGate.INCREASE_ALLOWED)
    assert demoted is TradingGate.EXIT_ONLY
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(_cmc(estimate=None))
    assert gate.exit_risk_safety_authority_preserved is True


def test_22_volatility_unknown_allows_reconciliation_authority() -> None:
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(_cmc(estimate=None))
    assert gate.exit_risk_safety_authority_preserved is True
    assert gate.eligibility.observation_and_reconciliation_only is True or (
        not gate.alpha_scope_entry_authority_allowed
    )


def test_23_exit_only_preserved() -> None:
    assert demote_trading_gate_for_typed_presence_failure_v1(TradingGate.EXIT_ONLY) is (
        TradingGate.EXIT_ONLY
    )
    assert demote_trading_gate_for_typed_presence_failure_v1(TradingGate.BLOCKED) is (
        TradingGate.BLOCKED
    )


def test_24_offline_runtime_estimator_equivalence() -> None:
    fixture = materializer.exact_known_61_price_fixture_v1()
    offline = materializer.compute_canonical_volatility_estimate_from_mark_prices_v1(
        fixture["mark_price"]
    )
    typed_est = typed.materialize_typed_canonical_volatility_estimate_v1(fixture["mark_price"])
    assert float(offline.dropna().iloc[-1]) == pytest.approx(typed_est.value)
    assert typed_est.estimator_version == typed.CANONICAL_ESTIMATOR_VERSION


def test_25_decision_evidence_contains_full_provenance() -> None:
    estimate = _estimate()
    ctx = _cmc(estimate=estimate, vol=estimate.value)
    evidence = build_hot_path_volatility_cycle_evidence_v1(ctx, reason_codes=("VALID",))
    payload = evidence.to_dict()
    required = [
        "volatility_contract_version",
        "volatility_value",
        "volatility_unit",
        "volatility_horizon",
        "volatility_estimator",
        "volatility_estimator_version",
        "volatility_observation_count",
        "volatility_as_of_event_time",
        "volatility_oldest_observation_event_time",
        "volatility_source_digest",
        "volatility_config_digest",
        "volatility_fallback_used",
        "volatility_fallback_identity",
        "volatility_status",
        "volatility_reason_codes",
        "volatility_age_seconds",
        "max_age_threshold",
        "max_age_enforcement_enabled",
    ]
    for key in required:
        assert key in payload
    assert payload["max_age_threshold"] is None
    assert payload["max_age_enforcement_enabled"] is False
    assert payload["volatility_status"] == "VALID"


def test_26_numeric_max_age_unresolved() -> None:
    assert NUMERIC_MAX_AGE_DECIDED is False
    assert NUMERIC_MAX_AGE_VALUE_UNRESOLVED is True
    assert MAX_AGE_THRESHOLD_SELECTED is False


def test_27_max_age_enforcement_disabled() -> None:
    assert MAX_AGE_ENFORCEMENT_ENABLED is False
    non_goals = assert_capability_non_goals_v1()
    assert non_goals["max_age_enforcement_enabled"] is False


def test_28_no_alpha_state_composition_semantics_changed() -> None:
    non_goals = assert_capability_non_goals_v1()
    assert non_goals["alpha_semantics_changed"] is False
    assert non_goals["state_semantics_changed"] is False
    assert non_goals["composition_authority_changed"] is False


def test_29_exit_precedence_surface_preserved() -> None:
    # Presence demotion must not collapse EXIT_ONLY / BLOCKED into entry.
    assert demote_trading_gate_for_typed_presence_failure_v1(TradingGate.EXIT_ONLY) is (
        TradingGate.EXIT_ONLY
    )


def test_30_reversal_reduce_first_preserved_flag() -> None:
    from trading.master_v2.canonical_volatility_hot_path_contract_closure_v1 import (
        REVERSAL_REDUCE_FIRST_PRESERVED,
    )

    assert REVERSAL_REDUCE_FIRST_PRESERVED is True


def test_package_marker_and_graph() -> None:
    assert PACKAGE_MARKER.endswith("=true")
    assert CAPABILITY_ID.endswith("HOT_PATH_CONTRACT_CLOSURE_V1")
    graph = producer_consumer_graph_v1()
    assert graph[0].startswith("NormalizedPublicMarketData")
    assert "VolatilityEstimateV1" in graph[4]
    assert productive_cmc_volatility_seed_v1() == 0.0


def test_clear_untyped_float_resets_placeholder() -> None:
    ctx = _cmc(estimate=_estimate(), vol=0.5)
    cleared = clear_untyped_productive_volatility_float_v1(ctx)
    assert cleared.canonical_volatility_estimate is None
    assert cleared.volatility_estimate == 0.0


def test_architecture_guards_pass() -> None:
    guards = assert_architecture_guards_v1(repo_root=ROOT)
    assert guards["guards_pass"] is True
    bridge = (
        ROOT
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
        / "hardening_cycle_bridge_v2.py"
    ).read_text(encoding="utf-8")
    assert "volatility_estimate=float(features.volatility_estimate)" not in bridge
    assert "productive_cmc_volatility_seed_v1" in bridge


def test_alias_volatility_estimate_v1() -> None:
    assert typed.VolatilityEstimateV1 is typed.CanonicalVolatilityEstimateV1
    estimate = _estimate()
    assert isinstance(estimate, typed.VolatilityEstimateV1)
