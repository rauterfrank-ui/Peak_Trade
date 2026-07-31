"""Focused tests for numeric max-age policy contract + non-enforcing telemetry v1."""

from __future__ import annotations

import math
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from trading.master_v2.canonical_market_context_v1 import (
    FEATURE_CONTRACT_VERSION,
    BarFinalityStatus,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    WarmupStatus,
    with_computed_input_digest,
)
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    build_canonical_volatility_estimate_v1,
)
from trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    AGE_FORMULA,
    AGE_REFERENCE_CLOCK,
    CAPABILITY_ID,
    CanonicalVolatilityMaxAgePolicyContractError,
    CanonicalVolatilityNumericMaxAgePolicyContractV1,
    ENFORCEMENT_ENABLED,
    NUMERIC_MAX_AGE_DECIDED,
    POLICY_VERSION,
    THRESHOLD_STATUS_UNRESOLVED,
    VolatilityMaxAgeReasonCodeV1,
    VolatilityPresenceStatusV1,
    VolatilityRestartStatusV1,
    VolatilityReuseStatusV1,
    assert_architecture_guards_v1,
    assert_capability_non_goals_v1,
    build_ratified_unresolved_max_age_policy_contract_v1,
    evaluate_canonical_volatility_estimate_age_policy_v1,
    validate_canonical_volatility_numeric_max_age_policy_contract_v1,
)
from trading.master_v2.canonical_volatility_productive_runtime_cmc_typed_binding_v1 import (
    CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1,
    ProductiveTypedBindingFailClosedReasonV1,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionDirectionState,
    PositionManagementContext,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    DoublePlayEntryExitPolicyV0,
    ENTRY_EXIT_POLICY_VERSION,
    ExistingPositionSide,
    PolicySignalV0,
    PositionState,
    ReconciliationState,
    SafetyMode,
    TradingGate,
    EntryExitDirectionState,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType
from trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    evaluate_double_play_runtime_typed_volatility_presence_gate_v1,
    evaluate_protection_authority_when_typed_absent_v1,
    protection_authority_required_v1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationTransportMetadataV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import (
    EventTimeInstantV1,
    MarketSampleIdentityV1,
)

ROOT = Path(__file__).resolve().parents[3]
AS_OF = datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc)
VENUE = "okx_europe"
CANON = "ETH-USD_UM_XPERP-310404"
VENUE_INST = "ETH-USD_UM_XPERP-310404"
T0 = 1_700_000_000.0


def _estimate(*, as_of: datetime = AS_OF, value: float = 0.004321):
    return build_canonical_volatility_estimate_v1(
        value=value,
        observation_count=61,
        as_of_event_time=as_of,
        fallback_used=False,
        source_digest="b" * 64,
    )


def _context(**overrides: object) -> CanonicalMarketContextV1:
    base: dict = {
        "context_id": "ctx-eth-max-age-policy",
        "instrument_id": CANON,
        "market_type": FuturesMarketType.PERPETUAL,
        "trading_epoch": 1,
        "market_event_time": "2026-06-30T12:05:00+00:00",
        "decision_time": "2026-06-30T12:05:01+00:00",
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


def _price_at(i: int) -> float:
    return 100.0 * math.exp(0.001 * i)


def _sample(i: int) -> MarketSampleIdentityV1:
    return MarketSampleIdentityV1(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        event_time=EventTimeInstantV1(unix_seconds=T0 + float(i * 60)),
        mark_price=_price_at(i),
    )


def test_01_valid_estimate_reference_after_as_of_computes_age() -> None:
    estimate = _estimate()
    ref = AS_OF + timedelta(seconds=300)
    evidence = evaluate_canonical_volatility_estimate_age_policy_v1(
        estimate=estimate,
        reference_market_event_time=ref,
        presence_status=VolatilityPresenceStatusV1.PRESENT,
    )
    assert evidence.computed_age_seconds == 300.0
    assert evidence.threshold_status == THRESHOLD_STATUS_UNRESOLVED
    assert evidence.enforcement_applied is False
    assert (
        evidence.reason_code
        == VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_AGE_UNRESOLVED.value
    )
    assert evidence.reason_code not in {
        VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_FRESH.value,
        VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_STALE.value,
    }


def test_02_reference_equals_as_of_age_zero() -> None:
    estimate = _estimate()
    evidence = evaluate_canonical_volatility_estimate_age_policy_v1(
        estimate=estimate,
        reference_market_event_time=AS_OF,
        presence_status=VolatilityPresenceStatusV1.PRESENT,
    )
    assert evidence.computed_age_seconds == 0.0
    assert evidence.threshold_status == THRESHOLD_STATUS_UNRESOLVED
    assert evidence.enforcement_applied is False


def test_03_reference_before_as_of_fail_closed_no_negative_age() -> None:
    estimate = _estimate()
    ref = AS_OF - timedelta(seconds=60)
    evidence = evaluate_canonical_volatility_estimate_age_policy_v1(
        estimate=estimate,
        reference_market_event_time=ref,
        presence_status=VolatilityPresenceStatusV1.PRESENT,
    )
    assert evidence.computed_age_seconds is None
    assert (
        evidence.reason_code == VolatilityMaxAgeReasonCodeV1.VOLATILITY_REFERENCE_BEFORE_AS_OF.value
    )
    assert evidence.enforcement_applied is False


def test_04_missing_reference_time() -> None:
    evidence = evaluate_canonical_volatility_estimate_age_policy_v1(
        estimate=_estimate(),
        reference_market_event_time=None,
        presence_status=VolatilityPresenceStatusV1.PRESENT,
    )
    assert (
        evidence.reason_code == VolatilityMaxAgeReasonCodeV1.VOLATILITY_REFERENCE_TIME_MISSING.value
    )
    assert evidence.computed_age_seconds is None


def test_05_missing_as_of() -> None:
    class _EstimateWithoutAsOf:
        source_digest = "c" * 64
        as_of_event_time = None

    evidence = evaluate_canonical_volatility_estimate_age_policy_v1(
        estimate=_EstimateWithoutAsOf(),  # type: ignore[arg-type]
        reference_market_event_time=AS_OF + timedelta(seconds=10),
        presence_status=VolatilityPresenceStatusV1.PRESENT,
    )
    assert evidence.reason_code == VolatilityMaxAgeReasonCodeV1.VOLATILITY_AS_OF_MISSING.value


def test_06_missing_typed_estimate_presence_authority_no_synthetic_age() -> None:
    evidence = evaluate_canonical_volatility_estimate_age_policy_v1(
        estimate=None,
        reference_market_event_time=AS_OF + timedelta(seconds=10),
        presence_status=VolatilityPresenceStatusV1.MISSING,
    )
    assert evidence.reason_code == VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_MISSING.value
    assert evidence.computed_age_seconds is None
    assert evidence.decision == "NOT_EVALUATED_PRESENCE_AUTHORITY"

    ctx = with_computed_input_digest(_context(volatility_estimate=0.38))
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(ctx)
    assert gate.alpha_scope_entry_authority_allowed is False
    assert gate.max_age_policy_evidence is not None
    assert gate.max_age_policy_evidence.computed_age_seconds is None
    assert (
        gate.max_age_policy_evidence.reason_code
        == VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_MISSING.value
    )


def test_07_restart_without_estimate() -> None:
    evidence = evaluate_canonical_volatility_estimate_age_policy_v1(
        estimate=None,
        reference_market_event_time=AS_OF,
        presence_status=VolatilityPresenceStatusV1.RESTART_UNAVAILABLE,
        restart_status=VolatilityRestartStatusV1.RESTART_WITHOUT_ESTIMATE,
    )
    assert evidence.max_age_status == "UNDEFINED"
    assert (
        evidence.reason_code
        == VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_RESTART_UNAVAILABLE.value
    )
    assert evidence.computed_age_seconds is None


def test_08_history_restore_no_estimate_no_fresh_mark(tmp_path: Path) -> None:
    path = tmp_path / "hist.json"
    host = CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        persistence_path=path,
    )
    ctx = _context()
    for i in range(0, 61):
        host.apply_to_market_context_v1(
            ctx,
            sample=_sample(i),
            transport=ObservationTransportMetadataV1(receive_time=T0 + i * 60 + 0.5),
            ingest_sample=True,
        )
    restored = (
        CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.restore_from_persistence_v1(
            persistence_path=path,
        )
    )
    assert restored.restart_without_estimate is True
    cycle = restored.apply_to_market_context_v1(ctx, ingest_sample=False)
    assert cycle.bound_estimate is None
    assert (
        cycle.telemetry.fail_closed_reason
        == ProductiveTypedBindingFailClosedReasonV1.RESTART_WITHOUT_ESTIMATE.value
    )
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        cycle.context,
        restart_status=VolatilityRestartStatusV1.HISTORY_RESTORE_WITHOUT_ESTIMATE,
    )
    assert gate.alpha_scope_entry_authority_allowed is False
    assert gate.max_age_policy_evidence is not None
    assert (
        gate.max_age_policy_evidence.reason_code
        == VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_RESTART_UNAVAILABLE.value
    )
    assert gate.max_age_policy_evidence.reason_code != (
        VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_FRESH.value
    )


def test_09_duplicate_reuse_as_of_unchanged_age_grows_with_market_event_time(
    tmp_path: Path,
) -> None:
    host = CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        persistence_path=tmp_path / "h.json",
    )
    ctx = _context()
    produced = None
    for i in range(0, 61):
        produced = host.apply_to_market_context_v1(
            ctx,
            sample=_sample(i),
            transport=ObservationTransportMetadataV1(receive_time=T0 + i * 60 + 0.5),
            ingest_sample=True,
        )
    assert produced is not None and produced.bound_estimate is not None
    as_of = produced.bound_estimate.as_of_event_time
    dup = host.apply_to_market_context_v1(
        ctx,
        sample=_sample(60),
        transport=ObservationTransportMetadataV1(receive_time=T0 + 60 * 60 + 0.5),
        ingest_sample=True,
    )
    assert dup.bound_estimate is not None
    assert dup.bound_estimate.as_of_event_time == as_of
    assert dup.bound_estimate.source_digest == produced.bound_estimate.source_digest

    later_ctx = with_computed_input_digest(
        _context(
            market_event_time=(as_of + timedelta(seconds=600)).isoformat(),
            decision_time=(as_of + timedelta(seconds=601)).isoformat(),
            volatility_estimate=0.0,
        )
    )
    bound = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        later_ctx, dup.bound_estimate
    )
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        bound,
        reuse_status=VolatilityReuseStatusV1.DUPLICATE_REUSE,
    )
    assert gate.max_age_policy_evidence is not None
    assert gate.max_age_policy_evidence.computed_age_seconds == 600.0
    assert gate.max_age_policy_evidence.reuse_status == (
        VolatilityReuseStatusV1.DUPLICATE_REUSE.value
    )
    assert gate.alpha_scope_entry_authority_allowed is True


def test_10_runtime_cycle_without_sample_no_refresh(tmp_path: Path) -> None:
    host = CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        persistence_path=tmp_path / "h2.json",
    )
    ctx = _context()
    produced = None
    for i in range(0, 61):
        produced = host.apply_to_market_context_v1(
            ctx,
            sample=_sample(i),
            transport=ObservationTransportMetadataV1(receive_time=T0 + i * 60 + 0.5),
            ingest_sample=True,
        )
    assert produced is not None and produced.bound_estimate is not None
    as_of = produced.bound_estimate.as_of_event_time
    cycle = host.apply_to_market_context_v1(produced.context, ingest_sample=False)
    assert cycle.bound_estimate is not None
    assert cycle.bound_estimate.as_of_event_time == as_of
    assert cycle.producer_result.estimate is None


def test_11_process_reuse_monotone_age_growth() -> None:
    estimate = _estimate()
    ages: list[float] = []
    for seconds in (0, 60, 120, 300):
        evidence = evaluate_canonical_volatility_estimate_age_policy_v1(
            estimate=estimate,
            reference_market_event_time=AS_OF + timedelta(seconds=seconds),
            presence_status=VolatilityPresenceStatusV1.PRESENT,
            reuse_status=VolatilityReuseStatusV1.PROCESS_REUSE,
        )
        assert evidence.computed_age_seconds is not None
        ages.append(evidence.computed_age_seconds)
        assert evidence.enforcement_applied is False
    assert ages == [0.0, 60.0, 120.0, 300.0]
    assert estimate.as_of_event_time == AS_OF


def test_12_unresolved_policy_contract_values() -> None:
    policy = build_ratified_unresolved_max_age_policy_contract_v1()
    assert policy.numeric_max_age_seconds is None
    assert policy.threshold_status == THRESHOLD_STATUS_UNRESOLVED
    assert policy.enforcement_enabled is False
    assert policy.reference_clock == AGE_REFERENCE_CLOCK
    assert policy.age_formula == AGE_FORMULA
    assert policy.rematerialization_policy == "FORBIDDEN"
    assert NUMERIC_MAX_AGE_DECIDED is False
    assert ENFORCEMENT_ENABLED is False


def test_13_invalid_contract_states_rejected() -> None:
    base = build_ratified_unresolved_max_age_policy_contract_v1()

    with pytest.raises(CanonicalVolatilityMaxAgePolicyContractError):
        validate_canonical_volatility_numeric_max_age_policy_contract_v1(
            CanonicalVolatilityNumericMaxAgePolicyContractV1(
                **{**base.to_dict(), "numeric_max_age_seconds": 120.0}
            )
        )

    with pytest.raises(CanonicalVolatilityMaxAgePolicyContractError):
        validate_canonical_volatility_numeric_max_age_policy_contract_v1(
            CanonicalVolatilityNumericMaxAgePolicyContractV1(
                **{**base.to_dict(), "enforcement_enabled": True}
            )
        )

    with pytest.raises(CanonicalVolatilityMaxAgePolicyContractError):
        validate_canonical_volatility_numeric_max_age_policy_contract_v1(
            CanonicalVolatilityNumericMaxAgePolicyContractV1(
                **{**base.to_dict(), "reference_clock": "WALLCLOCK"}
            )
        )

    with pytest.raises(CanonicalVolatilityMaxAgePolicyContractError):
        validate_canonical_volatility_numeric_max_age_policy_contract_v1(
            CanonicalVolatilityNumericMaxAgePolicyContractV1(
                **{**base.to_dict(), "rematerialization_policy": "ALLOWED_WITH_NEW_AS_OF"}
            )
        )


def test_14_clock_trust_untrusted_primary_authority_preserved() -> None:
    evidence = evaluate_canonical_volatility_estimate_age_policy_v1(
        estimate=_estimate(),
        reference_market_event_time=AS_OF + timedelta(seconds=10),
        presence_status=VolatilityPresenceStatusV1.PRESENT,
        clock_trust_status=ClockTrustStatus.UNTRUSTED,
    )
    assert (
        evidence.reason_code
        == VolatilityMaxAgeReasonCodeV1.VOLATILITY_FRESHNESS_CLOCK_UNTRUSTED.value
    )
    assert evidence.computed_age_seconds is None
    assert evidence.decision == "COMPOSED_TRUST_SECONDARY"
    assert evidence.enforcement_applied is False

    estimate = _estimate()
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        with_computed_input_digest(
            _context(clock_trust_status=ClockTrustStatus.UNTRUSTED, volatility_estimate=0.0)
        ),
        estimate,
    )
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(ctx)
    # CMC clock trust blocks alpha via eligibility; age evidence does not replace it.
    assert gate.alpha_scope_entry_authority_allowed is False
    assert gate.max_age_policy_evidence is not None
    assert gate.max_age_policy_evidence.clock_trust_status == "untrusted"


def test_15_data_integrity_untrusted_primary_authority_preserved() -> None:
    evidence = evaluate_canonical_volatility_estimate_age_policy_v1(
        estimate=_estimate(),
        reference_market_event_time=AS_OF + timedelta(seconds=10),
        presence_status=VolatilityPresenceStatusV1.PRESENT,
        data_integrity_status=DataIntegrityStatus.UNTRUSTED,
    )
    assert (
        evidence.reason_code
        == VolatilityMaxAgeReasonCodeV1.VOLATILITY_FRESHNESS_DATA_UNTRUSTED.value
    )
    assert evidence.enforcement_applied is False

    estimate = _estimate()
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        with_computed_input_digest(
            _context(
                data_integrity_status=DataIntegrityStatus.UNTRUSTED,
                volatility_estimate=0.0,
            )
        ),
        estimate,
    )
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(ctx)
    assert gate.alpha_scope_entry_authority_allowed is False
    assert gate.max_age_policy_evidence is not None
    assert gate.max_age_policy_evidence.data_integrity_status == "untrusted"


def test_16_exit_risk_safety_independence() -> None:
    ctx = with_computed_input_digest(_context())
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(ctx)
    assert gate.exit_risk_safety_authority_preserved is True
    assert gate.alpha_scope_entry_authority_allowed is False
    assert gate.max_age_policy_evidence is not None

    assert (
        protection_authority_required_v1(
            position_state=PositionState.OPEN_FULL,
            existing_position_side=ExistingPositionSide.LONG,
            reconciliation_state=ReconciliationState.RECONCILED,
            safety_exit_signal=PolicySignalV0(triggered=True, reason_code="safety"),
            hard_risk_reduction_signal=PolicySignalV0(triggered=False),
            scope_adverse_exit_signal=PolicySignalV0(triggered=False),
            profit_protection_signal=PolicySignalV0(triggered=False),
            time_exit_signal=PolicySignalV0(triggered=False),
            strategy_invalidation_signal=PolicySignalV0(triggered=False),
            safety_mode=SafetyMode.EXIT_ONLY,
        )
        is True
    )
    decision = evaluate_protection_authority_when_typed_absent_v1(
        instrument_id=CANON,
        trading_epoch=1,
        context_reference="ctx-max-age",
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
        position_state=PositionState.OPEN_FULL,
        reconciliation_state=ReconciliationState.RECONCILED,
        trading_gate=TradingGate.ENTRY_ALLOWED,
        safety_mode=SafetyMode.EXIT_ONLY,
        data_integrity_state=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        cooldown_pass=True,
        existing_position_side=ExistingPositionSide.LONG,
        venue_flat=False,
        scope_adverse_exit_signal=PolicySignalV0(triggered=False),
        profit_protection_signal=PolicySignalV0(triggered=False),
        time_exit_signal=PolicySignalV0(triggered=False),
        strategy_invalidation_signal=PolicySignalV0(triggered=False),
        hard_risk_reduction_signal=PolicySignalV0(triggered=False),
        safety_exit_signal=PolicySignalV0(triggered=True, reason_code="safety"),
        previous_direction_state=CompositionDirectionState.LONG,
        position_management_context=PositionManagementContext.LONG_POSITION,
        entry_exit_policy=DoublePlayEntryExitPolicyV0(policy_version=ENTRY_EXIT_POLICY_VERSION),
        gate=gate,
    )
    assert decision.decision_outcome is DecisionOutcome.EXIT
    assert gate.max_age_policy_evidence.enforcement_applied is False


def test_17_offline_runtime_equivalence_independent_of_wallclock() -> None:
    estimate = _estimate()
    ref = "2026-06-30T12:10:00+00:00"
    t0 = time.perf_counter()
    e1 = evaluate_canonical_volatility_estimate_age_policy_v1(
        estimate=estimate,
        reference_market_event_time=ref,
        presence_status=VolatilityPresenceStatusV1.PRESENT,
    )
    time.sleep(0.01)
    e2 = evaluate_canonical_volatility_estimate_age_policy_v1(
        estimate=estimate,
        reference_market_event_time=datetime(2026, 6, 30, 12, 10, tzinfo=timezone.utc),
        presence_status=VolatilityPresenceStatusV1.PRESENT,
    )
    _ = time.perf_counter() - t0
    assert e1.computed_age_seconds == e2.computed_age_seconds == 600.0
    assert e1.to_dict() == e2.to_dict()


def test_18_backward_compatibility_presence_alpha_unchanged() -> None:
    estimate = _estimate()
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        with_computed_input_digest(_context(volatility_estimate=0.0)),
        estimate,
    )
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(ctx)
    assert gate.alpha_scope_entry_authority_allowed is True
    assert gate.typed_estimate_present is True
    assert gate.max_age_policy_evidence is not None
    assert gate.max_age_policy_evidence.enforcement_applied is False
    assert (
        gate.max_age_policy_evidence.reason_code
        == VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_AGE_UNRESOLVED.value
    )
    # Age evidence must not appear as presence block reason.
    assert all(not r.startswith("VOLATILITY_ESTIMATE_AGE") for r in gate.reason_codes)


def test_architecture_guards_and_non_goals() -> None:
    guards = assert_architecture_guards_v1(repo_root=ROOT)
    assert guards["guards_pass"] is True
    assert guards["numeric_max_age_decided"] is False
    assert guards["enforcement_enabled"] is False
    assert guards["separate_freshness_gate_created"] is False
    non_goals = assert_capability_non_goals_v1()
    assert non_goals["no_alpha_enforcement_enabled"] is True
    assert CAPABILITY_ID.startswith("MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE")
    assert POLICY_VERSION == "canonical_volatility_numeric_max_age_policy/v1"
