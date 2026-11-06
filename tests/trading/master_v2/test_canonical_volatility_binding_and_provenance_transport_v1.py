"""Tests for C1 canonical volatility binding and provenance transport v1."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from trading.master_v2.canonical_market_context_v1 import (
    FEATURE_CONTRACT_VERSION,
    BarFinalityStatus,
    CanonicalMarketContextBlockReason,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    WarmupStatus,
    compute_canonical_market_context_input_digest,
    evaluate_canonical_market_context_eligibility,
    with_computed_input_digest,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    CanonicalScopeInitializationPolicyV1,
    ScopeInitializationPrerequisitesV1,
    initialize_canonical_scope,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
    finalize_offline_replay_decision_evidence_v1,
    serialize_canonical_trading_decision_evidence_canonical,
)
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    CAPABILITY_ID,
    PACKAGE_MARKER,
    VOLATILITY_MAX_AGE_VALUE_UNRESOLVED,
    CanonicalVolatilityBindingError,
    CanonicalVolatilityBindingErrorCode,
    VolatilityStaleStatusV1,
    VolatilityValidationResultV1,
    adapt_validated_typed_estimate_to_legacy_float_v1,
    assert_architecture_guards_v1,
    assert_capability_non_goals_v1,
    assert_general_input_digest_alone_insufficient_v1,
    attach_volatility_provenance_to_decision_evidence_v1,
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
    build_volatility_decision_evidence_provenance_v1,
    compute_legacy_adaptation_digest_v1,
    compute_typed_estimate_digest_v1,
    compute_volatility_input_binding_digest_v1,
    evaluate_typed_volatility_binding_eligibility_v1,
    reject_untyped_float_at_typed_cmc_boundary_v1,
    resolve_legacy_volatility_float_for_consumer_v1,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    LEGACY_ADAPTER_OWNER,
    TYPED_CARRIER_OWNER,
    build_canonical_volatility_estimate_v1,
    with_mutated_field_for_tests_v1,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType
from trading.master_v2.double_play_state import DynamicScopeRules
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import _DEFAULT_SCOPE_RULES
from trading.master_v2.offline_double_play_scenario_replay_v0 import _DEFAULT_RULES

ROOT = Path(__file__).resolve().parents[3]
AS_OF = datetime(2026, 6, 1, 1, 0, tzinfo=timezone.utc)


def _valid_estimate(**overrides: object):
    base: dict[str, object] = {
        "value": 0.004321,
        "observation_count": 60,
        "as_of_event_time": AS_OF,
        "fallback_used": False,
    }
    base.update(overrides)
    return build_canonical_volatility_estimate_v1(**base)  # type: ignore[arg-type]


def _context(**overrides: object) -> CanonicalMarketContextV1:
    base: dict = {
        "context_id": "ctx-eth-perp-epoch42-ev1",
        "instrument_id": "inst-eth-usdt-perp",
        "market_type": FuturesMarketType.PERPETUAL,
        "trading_epoch": 42,
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


def _minimal_evidence(**overrides: object) -> CanonicalTradingDecisionEvidenceV1:
    base: dict = {
        "decision_id": "decision-1",
        "replay_id": "replay-1",
        "instrument_id": "inst-eth-usdt-perp",
        "trading_epoch": 42,
        "market_context_ref": "ctx-1",
        "scope_initialization_ref": "scope-1",
        "scope_event_ref": "sev-1",
        "bull_assessment_ref": "bull-1",
        "bear_assessment_ref": "bear-1",
        "state_switch_ref": "sw-1",
        "bull_survival_ref": "bs-1",
        "bear_survival_ref": "brs-1",
        "bull_suitability_ref": "bsu-1",
        "bear_suitability_ref": "brsu-1",
        "composition_result_ref": "comp-1",
        "entry_exit_policy_ref": "ee-1",
        "current_scope_ref": "cs-1",
        "next_scope_ref": "ns-1",
        "previous_direction_state": "NEUTRAL",
        "next_direction_state": "NEUTRAL",
        "selected_side": "NONE",
        "selected_strategy_ref": "",
        "decision_outcome": "observe",
        "entry_or_exit_policy_ref": "ee-1",
        "reason_codes": (),
        "decision_precedence_trace": (),
        "component_versions": {},
        "policy_versions": {},
        "config_digest": "a" * 64,
        "implementation_digest": "b" * 64,
        "input_digest": "c" * 64,
        "semantic_digest": "",
    }
    base.update(overrides)
    return CanonicalTradingDecisionEvidenceV1(**base)


def test_package_marker_and_manifest() -> None:
    assert PACKAGE_MARKER.endswith("=true")
    manifest = assert_capability_non_goals_v1()
    assert manifest["capability_id"] == CAPABILITY_ID
    assert manifest["typed_transport_model"] == "A"
    assert manifest["runtime_wiring"] is False
    assert manifest["live_authorization"] is False
    assert manifest["default_mutation"] is False
    assert VOLATILITY_MAX_AGE_VALUE_UNRESOLVED is True
    assert manifest["typed_carrier_owner"] == TYPED_CARRIER_OWNER
    assert manifest["legacy_adapter_owner"] == LEGACY_ADAPTER_OWNER


def test_architecture_guards_pass() -> None:
    result = assert_architecture_guards_v1(repo_root=ROOT)
    assert result["guards_pass"] is True
    assert result["adapter_defs_in_typed"] == 1
    assert result["adapter_defs_in_binding"] == 0


def test_proven_typed_estimate_accepted_into_cmc() -> None:
    estimate = _valid_estimate()
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(_context(), estimate)
    assert ctx.canonical_volatility_estimate is not None
    assert ctx.canonical_volatility_estimate.value == pytest.approx(0.004321)
    assert ctx.volatility_estimate == pytest.approx(0.004321)
    assert ctx.canonical_volatility_estimate.unit == estimate.unit
    assert ctx.canonical_volatility_estimate.source_digest == estimate.source_digest
    assert ctx.canonical_volatility_estimate.as_of_event_time == estimate.as_of_event_time


def test_legacy_float_matches_typed_carrier_for_float_consumer() -> None:
    estimate = _valid_estimate(value=0.012345)
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(_context(), estimate)
    legacy = resolve_legacy_volatility_float_for_consumer_v1(ctx)
    assert legacy == pytest.approx(0.012345)
    assert legacy == pytest.approx(ctx.canonical_volatility_estimate.value)  # type: ignore[union-attr]


def test_digests_deterministic() -> None:
    estimate = _valid_estimate()
    d1 = compute_typed_estimate_digest_v1(estimate)
    d2 = compute_typed_estimate_digest_v1(estimate)
    assert d1 == d2
    legacy = 0.004321
    a1 = compute_legacy_adaptation_digest_v1(estimate=estimate, legacy_float=legacy)
    a2 = compute_legacy_adaptation_digest_v1(estimate=estimate, legacy_float=legacy)
    assert a1 == a2
    b1 = compute_volatility_input_binding_digest_v1(
        estimate=estimate,
        legacy_float=legacy,
        stale_status=VolatilityStaleStatusV1.UNRESOLVED_MAX_AGE,
        validation_result=VolatilityValidationResultV1.ACCEPTED,
    )
    b2 = compute_volatility_input_binding_digest_v1(
        estimate=estimate,
        legacy_float=legacy,
        stale_status=VolatilityStaleStatusV1.UNRESOLVED_MAX_AGE,
        validation_result=VolatilityValidationResultV1.ACCEPTED,
    )
    assert b1 == b2
    assert len(d1) == 64 and len(a1) == 64 and len(b1) == 64


def test_evidence_contains_full_identity_and_roundtrip() -> None:
    estimate = _valid_estimate()
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(_context(), estimate)
    provenance = build_volatility_decision_evidence_provenance_v1(ctx)
    assert provenance.volatility_contract_version
    assert provenance.source_digest == estimate.source_digest
    assert provenance.typed_estimate_digest
    assert provenance.legacy_adaptation_digest
    assert provenance.volatility_input_binding_digest
    assert provenance.stale_status == "UNRESOLVED_MAX_AGE"
    assert provenance.validation_result == "ACCEPTED"
    assert provenance.legacy_float_value == pytest.approx(estimate.value)
    evidence = attach_volatility_provenance_to_decision_evidence_v1(
        _minimal_evidence(),
        provenance,
    )
    finalized = finalize_offline_replay_decision_evidence_v1(evidence)
    assert finalized.volatility_provenance is not None
    assert finalized.volatility_provenance.to_dict() == provenance.to_dict()
    serialized = serialize_canonical_trading_decision_evidence_canonical(finalized)
    assert "volatility_provenance" in serialized
    assert provenance.volatility_input_binding_digest in serialized


def test_legacy_cmc_digest_unchanged_without_typed_field() -> None:
    ctx = with_computed_input_digest(_context(volatility_estimate=0.38))
    assert ctx.canonical_volatility_estimate is None
    # Recompute from float-only context; digest path omits None typed field.
    again = compute_canonical_market_context_input_digest(
        _context(volatility_estimate=0.38, input_digest="")
    )
    assert ctx.input_digest == again


def test_scope_init_uses_adapted_typed_value() -> None:
    estimate = _valid_estimate(value=0.25)
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        _context(mark_price=1000.0),
        estimate,
    )
    result = initialize_canonical_scope(
        ctx,
        CanonicalScopeInitializationPolicyV1(min_scope_band=1.0, max_scope_band=10_000.0),
        ScopeInitializationPrerequisitesV1(
            required_window_complete=True,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
    )
    assert result.scope is not None
    assert result.scope.volatility_estimate == pytest.approx(0.25)
    assert result.scope.initial_volatility_distance == pytest.approx(250.0)


def test_untyped_float_rejected_at_typed_boundary() -> None:
    with pytest.raises(CanonicalVolatilityBindingError) as exc:
        reject_untyped_float_at_typed_cmc_boundary_v1(raw_float=0.2, typed_estimate=None)
    assert exc.value.code is CanonicalVolatilityBindingErrorCode.UNTYPED_FLOAT_REJECTED


def test_fallback_used_rejected() -> None:
    estimate = _valid_estimate()
    bad = with_mutated_field_for_tests_v1(estimate, fallback_used=True)
    with pytest.raises(CanonicalVolatilityBindingError) as exc:
        bind_typed_canonical_volatility_estimate_into_market_context_v1(_context(), bad)
    assert exc.value.code is CanonicalVolatilityBindingErrorCode.INVALID_ESTIMATE


def test_unsupported_version_rejected() -> None:
    estimate = _valid_estimate()
    bad = with_mutated_field_for_tests_v1(estimate, contract_version="not/a/version")
    with pytest.raises(CanonicalVolatilityBindingError):
        bind_typed_canonical_volatility_estimate_into_market_context_v1(_context(), bad)


def test_wrong_unit_horizon_estimator_rejected() -> None:
    estimate = _valid_estimate()
    for kwargs in (
        {"unit": "ANNUALIZED_VOL"},
        {"horizon_seconds": 999},
        {"estimator": "OTHER"},
    ):
        bad = with_mutated_field_for_tests_v1(estimate, **kwargs)
        with pytest.raises(CanonicalVolatilityBindingError):
            bind_typed_canonical_volatility_estimate_into_market_context_v1(_context(), bad)


def test_insufficient_observations_rejected() -> None:
    estimate = _valid_estimate()
    bad = with_mutated_field_for_tests_v1(estimate, observation_count=10)
    with pytest.raises(CanonicalVolatilityBindingError):
        bind_typed_canonical_volatility_estimate_into_market_context_v1(_context(), bad)


def test_naive_event_time_rejected() -> None:
    estimate = _valid_estimate()
    bad = with_mutated_field_for_tests_v1(
        estimate,
        as_of_event_time=datetime(2026, 6, 1, 1, 0),
    )
    with pytest.raises(CanonicalVolatilityBindingError):
        bind_typed_canonical_volatility_estimate_into_market_context_v1(_context(), bad)


def test_missing_source_digest_rejected() -> None:
    estimate = _valid_estimate()
    bad = with_mutated_field_for_tests_v1(estimate, source_digest="")
    with pytest.raises(CanonicalVolatilityBindingError):
        bind_typed_canonical_volatility_estimate_into_market_context_v1(_context(), bad)


def test_adaptation_without_validation_flag_rejected() -> None:
    estimate = _valid_estimate()
    with pytest.raises(CanonicalVolatilityBindingError) as exc:
        adapt_validated_typed_estimate_to_legacy_float_v1(estimate, already_validated=False)
    assert exc.value.code is CanonicalVolatilityBindingErrorCode.ADAPTATION_WITHOUT_VALIDATION


def test_general_input_digest_alone_insufficient() -> None:
    with pytest.raises(CanonicalVolatilityBindingError) as exc:
        assert_general_input_digest_alone_insufficient_v1(
            input_digest="c" * 64,
            provenance=None,
        )
    assert exc.value.code is CanonicalVolatilityBindingErrorCode.MISSING_TYPED_ESTIMATE


def test_typed_path_missing_estimate_blocks_exposure_and_scope() -> None:
    ctx = with_computed_input_digest(_context())
    elig = evaluate_typed_volatility_binding_eligibility_v1(ctx)
    assert elig.new_directional_exposure_allowed is False
    assert elig.scope_confirmation_allowed is False
    assert elig.observation_and_reconciliation_only is True
    assert CanonicalMarketContextBlockReason.TYPED_VOLATILITY_ESTIMATE_MISSING in elig.block_reasons


def test_legacy_eligibility_unchanged_without_typed_requirement() -> None:
    ctx = with_computed_input_digest(_context())
    elig = evaluate_canonical_market_context_eligibility(ctx)
    assert elig.trading_decision_allowed is True
    assert elig.new_directional_exposure_allowed is True


def test_defaults_unchanged_regression() -> None:
    # C2: constructive default 1.0 removed; bare rules leave volatility unmaterialized.
    assert DynamicScopeRules().volatility_estimate is None
    assert _DEFAULT_RULES.volatility_estimate == 0.02
    assert _DEFAULT_SCOPE_RULES.volatility_estimate == 0.02
    wiring = (ROOT / "src/backtest/mv2_research_wiring_v1.py").read_text(encoding="utf-8")
    assert 'bar.get("volatility_estimate", 0.2)' not in wiring
    assert "quarantine_historical_bar_volatility_v1" in wiring
    integrated = (
        ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
    ).read_text(encoding="utf-8")
    assert "max(float(snapshot.volatility_estimate), 1e-9)" not in integrated
    assert "admit_positive_volatility_without_strategy_floor_v1" in integrated


def test_no_runtime_wiring_flags() -> None:
    manifest = assert_capability_non_goals_v1()
    assert manifest["runtime_wiring"] is False
    assert manifest["runtime_producer_cutover"] is False
    binding_src = (
        ROOT / "src/trading/master_v2/canonical_volatility_binding_and_provenance_transport_v1.py"
    ).read_text(encoding="utf-8")
    code_before_guards = binding_src.split("def assert_architecture_guards_v1", 1)[0]
    assert "feature_regime_pipeline" not in code_before_guards
    assert "FuturesVolatilityProfile" not in code_before_guards
    assert "panel_sequential" not in code_before_guards
