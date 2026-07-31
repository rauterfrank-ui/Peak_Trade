"""Contract and integration tests for C3 Directional Assessment Confirmation Integration."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Optional

import pytest

from trading.market_state.directional_confirmation_progress_v1 import (
    ConfirmationAssessmentSignalV1,
    ConfirmationAssessmentStateV1,
    ConfirmationProgressReasonCodeV1,
    ConfirmationSideV1,
    reject_decision_epoch_confirmation_advance_v1,
    reject_receive_time_confirmation_advance_v1,
    reject_runtime_cycle_confirmation_advance_v1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceResultV1,
    ObservationCandidateV1,
    ObservationClassification,
    ObservationTransportMetadataV1,
    commit_observation_acceptance_v1,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)
from trading.market_state.observation_identity_v1 import (
    InstrumentObservationKeyV1,
    MarketObservationEpoch,
)
from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    ClockTrustStatus,
    DataIntegrityStatus,
)
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_CAPABILITY_ID,
    PARALLEL_CONFIRMATION_AUTHORITY_FORBIDDEN,
    DirectionalAssessmentConfirmationIntegrationInputV1,
    DirectionalConfirmationSideStateCarrierV1,
    ParallelConfirmationAuthorityErrorV1,
    assert_c3_confirmation_authority_exclusive_v1,
    evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1,
    evaluate_directional_assessment_with_confirmation_progress_v1,
    initial_directional_confirmation_side_state_carrier_v1,
    map_confirmation_assessment_state_to_directional_status_v1,
    map_signal_strength_to_confirmation_assessment_signal_v1,
    non_advancing_observation_acceptance_result_v1,
)
from trading.master_v2.directional_assessment_v1 import (
    DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    DirectionalAssessmentInputV1,
    DirectionalAssessmentPolicyV1,
    DirectionalAssessmentSide,
    DirectionalAssessmentStatus,
    DirectionalConfirmationStateV1,
    ScopeEventRefV1,
    compute_signal_strength,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
REPLAY_MODULE = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
C3_MODULE = (
    REPO_ROOT / "src/trading/master_v2/directional_assessment_confirmation_integration_v1.py"
)
WIRING_MODULE = REPO_ROOT / "src/backtest/mv2_research_wiring_v1.py"


def _key(
    *,
    venue: str = "okx_eea",
    canonical: str = "ETH-USD-SWAP-CANON",
    venue_inst: str = "ETH-USD-SWAP",
) -> InstrumentObservationKeyV1:
    return InstrumentObservationKeyV1(
        venue=venue,
        canonical_instrument_id=canonical,
        venue_instrument_id=venue_inst,
    )


def _policy(**overrides: object) -> DirectionalAssessmentPolicyV1:
    base = {
        "observe_signal_threshold": 0.001,
        "candidate_signal_threshold": 0.005,
        "confirmation_signal_threshold": 0.01,
        "confirmation_epochs": 2,
        "validity_epochs": 3,
        "policy_version": DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    }
    base.update(overrides)
    return DirectionalAssessmentPolicyV1(**base)  # type: ignore[arg-type]


def _scope_ref(trading_epoch: int = 10) -> ScopeEventRefV1:
    return ScopeEventRefV1(
        scope_event_id="scope-evt-1",
        semantic_digest="a" * 64,
        event_type="UPSCOPE_CONFIRMED",
        trading_epoch=trading_epoch,
    )


def _da_input(
    *,
    side: DirectionalAssessmentSide = DirectionalAssessmentSide.LONG,
    price_path: tuple[float, ...] = (3500.0, 3550.0),
    trading_epoch: int = 10,
) -> DirectionalAssessmentInputV1:
    return DirectionalAssessmentInputV1(
        instrument_id="ETH-USD-SWAP-CANON",
        trading_epoch=trading_epoch,
        side=side,
        price_path=price_path,
        reference_price=3500.0,
        feature_refs=("feat-momentum-v1",),
        scope_event_ref=_scope_ref(trading_epoch),
        survival_preconditions=("survival_precondition_ref_only",),
        confirmation_state=DirectionalConfirmationStateV1(
            candidate_count=99,
            last_evaluated_trading_epoch=0,
            last_signal_strength=9.0,
        ),
        data_integrity_status=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        bar_finality_status=BarFinalityStatus.FINALIZED,
        trusted_data=True,
        input_complete=True,
        explicit_hard_block_reasons=(),
        policy_version=DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    )


def _candidate(
    *,
    event_time: float,
    mark: float,
    receive_time: Optional[float] = None,
    poll_attempt: Optional[int] = None,
    runtime_cycle_index: Optional[int] = None,
    key: Optional[InstrumentObservationKeyV1] = None,
) -> ObservationCandidateV1:
    instrument = key or _key()
    transport = None
    if receive_time is not None or poll_attempt is not None or runtime_cycle_index is not None:
        transport = ObservationTransportMetadataV1(
            receive_time=receive_time,
            poll_attempt=poll_attempt,
            runtime_cycle_index=runtime_cycle_index,
        )
    return ObservationCandidateV1(
        venue=instrument.venue,
        canonical_instrument_id=instrument.canonical_instrument_id,
        venue_instrument_id=instrument.venue_instrument_id,
        venue_event_time=event_time,
        mark_price=mark,
        transport=transport,
    )


def _eval_c1(state, candidate):
    result = evaluate_distinct_market_observation_v1(state, candidate)
    if result.classification == ObservationClassification.DISTINCT:
        state = commit_observation_acceptance_v1(current_state=state, result=result)
    return result, state


def _carrier(session_id: str = "sess-c3") -> DirectionalConfirmationSideStateCarrierV1:
    return initial_directional_confirmation_side_state_carrier_v1(
        session_id=session_id,
        venue="okx_eea",
        instrument=_key(),
    )


def _progress_side(
    *,
    side: ConfirmationSideV1,
    prior_carrier: DirectionalConfirmationSideStateCarrierV1,
    acceptor: ObservationAcceptanceResultV1,
    price_path: tuple[float, ...],
    session_id: str = "sess-c3",
    venue: str = "okx_eea",
    instrument: Optional[InstrumentObservationKeyV1] = None,
    policy: Optional[DirectionalAssessmentPolicyV1] = None,
):
    instrument = instrument or _key()
    policy = policy or _policy()
    da_side = (
        DirectionalAssessmentSide.LONG
        if side is ConfirmationSideV1.LONG
        else DirectionalAssessmentSide.SHORT
    )
    return evaluate_directional_assessment_with_confirmation_progress_v1(
        DirectionalAssessmentConfirmationIntegrationInputV1(
            directional_input=_da_input(side=da_side, price_path=price_path),
            policy=policy,
            prior_confirmation_progress=prior_carrier.for_side(side),
            observation_acceptance_result=acceptor,
            session_id=session_id,
            venue=venue,
            instrument=instrument,
            side=side,
        )
    )


def test_01_bull_observe_candidate_confirmed() -> None:
    policy = _policy(confirmation_epochs=2)
    carrier = _carrier()
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    # strong bull path
    path = (3500.0, 3550.0)
    assert (
        map_signal_strength_to_confirmation_assessment_signal_v1(
            compute_signal_strength(
                price_path=path, side=DirectionalAssessmentSide.LONG, reference_price=3500.0
            ),
            policy,
        )
        is ConfirmationAssessmentSignalV1.CONFIRMED
    )
    a1, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    r1 = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a1,
        price_path=path,
        policy=policy,
    )
    assert r1.assessment.status is DirectionalAssessmentStatus.CANDIDATE
    carrier = carrier.with_side_state(ConfirmationSideV1.LONG, r1.confirmation_progress_after)

    a2, c1 = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    r2 = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a2,
        price_path=path,
        policy=policy,
    )
    assert r2.assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert (
        r2.confirmation_progress_after.assessment_state is ConfirmationAssessmentStateV1.CONFIRMED
    )


def test_02_bear_observe_candidate_confirmed() -> None:
    policy = _policy(confirmation_epochs=2)
    carrier = _carrier()
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    path = (3500.0, 3450.0)  # down move → SHORT strength positive
    a1, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    r1 = _progress_side(
        side=ConfirmationSideV1.SHORT,
        prior_carrier=carrier,
        acceptor=a1,
        price_path=path,
        policy=policy,
    )
    assert r1.assessment.status is DirectionalAssessmentStatus.CANDIDATE
    carrier = carrier.with_side_state(ConfirmationSideV1.SHORT, r1.confirmation_progress_after)
    a2, _ = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    r2 = _progress_side(
        side=ConfirmationSideV1.SHORT,
        prior_carrier=carrier,
        acceptor=a2,
        price_path=path,
        policy=policy,
    )
    assert r2.assessment.status is DirectionalAssessmentStatus.CONFIRMED


def test_03_bull_bear_state_isolation() -> None:
    policy = _policy(confirmation_epochs=2)
    carrier = _carrier()
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    a1, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    bull_before = carrier.bull_confirmation_state
    bear_before = carrier.bear_confirmation_state
    bull, bear, after = evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1(
        bull_input=_da_input(side=DirectionalAssessmentSide.LONG, price_path=(3500.0, 3550.0)),
        bear_input=_da_input(side=DirectionalAssessmentSide.SHORT, price_path=(3500.0, 3550.0)),
        policy=policy,
        prior_carrier=carrier,
        observation_acceptance_result=a1,
        session_id="sess-c3",
        venue="okx_eea",
        instrument=_key(),
    )
    assert after.bull_confirmation_state != bull_before
    assert after.bear_confirmation_state != bear_before or bear.assessment.status in {
        DirectionalAssessmentStatus.OBSERVE,
        DirectionalAssessmentStatus.CANDIDATE,
        DirectionalAssessmentStatus.CONFIRMED,
        DirectionalAssessmentStatus.BLOCKED,
        DirectionalAssessmentStatus.INVALID,
    }
    # Bull-only update must not touch bear prior when evaluated alone.
    alone = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a1,
        price_path=(3500.0, 3550.0),
        policy=policy,
    )
    mid = carrier.with_side_state(ConfirmationSideV1.LONG, alone.confirmation_progress_after)
    assert mid.bear_confirmation_state == bear_before
    assert alone.assessment.status is DirectionalAssessmentStatus.CANDIDATE


def test_04_non_distinct_noop() -> None:
    carrier = _carrier()
    acceptor = non_advancing_observation_acceptance_result_v1(bound_instrument_key=_key())
    out = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=acceptor,
        price_path=(3500.0, 3550.0),
    )
    assert out.reason_code is ConfirmationProgressReasonCodeV1.NON_DISTINCT_NOOP
    assert out.confirmation_advanced is False
    assert out.confirmation_progress_after == carrier.bull_confirmation_state
    assert out.assessment.status is DirectionalAssessmentStatus.OBSERVE


def test_05_idempotent_replay() -> None:
    carrier = _carrier()
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    a1, _ = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    first = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a1,
        price_path=(3500.0, 3550.0),
    )
    carrier2 = carrier.with_side_state(ConfirmationSideV1.LONG, first.confirmation_progress_after)
    replay = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier2,
        acceptor=a1,
        price_path=(3500.0, 3550.0),
    )
    assert replay.reason_code is ConfirmationProgressReasonCodeV1.IDEMPOTENT_REPLAY
    assert replay.confirmation_advanced is False
    assert replay.confirmation_progress_after == first.confirmation_progress_after


def test_06_epoch_gap_fail_closed() -> None:
    carrier = _carrier()
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    a1, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    progressed = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a1,
        price_path=(3500.0, 3550.0),
    )
    carrier = carrier.with_side_state(
        ConfirmationSideV1.LONG, progressed.confirmation_progress_after
    )
    # Force gap: advance C1 twice without feeding C2 the intermediate result.
    a2, c1 = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    a3, _ = _eval_c1(c1, _candidate(event_time=1002.0, mark=12.0))
    assert a3.state_after.market_observation_epoch.value == (
        progressed.confirmation_progress_after.latest_accepted_market_observation_epoch.value + 2
    )
    gap = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a3,
        price_path=(3500.0, 3550.0),
    )
    assert gap.fail_closed is True
    assert gap.reason_code is ConfirmationProgressReasonCodeV1.EPOCH_GAP
    assert gap.assessment.status is DirectionalAssessmentStatus.BLOCKED


def test_07_epoch_regression_fail_closed() -> None:
    carrier = _carrier()
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    a1, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    first = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a1,
        price_path=(3500.0, 3550.0),
    )
    carrier = carrier.with_side_state(ConfirmationSideV1.LONG, first.confirmation_progress_after)
    a2, _ = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    # Replay older acceptor epoch by manufacturing stale result via non-advancing at epoch 0.
    stale = non_advancing_observation_acceptance_result_v1(
        bound_instrument_key=_key(),
        market_observation_epoch=MarketObservationEpoch(value=0),
    )
    # Make it look DISTINCT with strategy_advance to trigger epoch check.
    from trading.market_state.distinct_market_observation_acceptor_v1 import (
        ObservationAcceptanceStateV1,
    )

    stale_distinct = ObservationAcceptanceResultV1(
        classification=ObservationClassification.DISTINCT,
        strategy_advance_allowed=True,
        state_before=ObservationAcceptanceStateV1(
            last_accepted_observation_identity=None,
            market_observation_epoch=MarketObservationEpoch(value=0),
            bound_instrument_key=_key(),
            last_accepted_transport=None,
        ),
        state_after=ObservationAcceptanceStateV1(
            last_accepted_observation_identity=a1.observation_identity,
            market_observation_epoch=MarketObservationEpoch(value=0),
            bound_instrument_key=_key(),
            last_accepted_transport=None,
        ),
        observation_identity=a1.observation_identity,
        reason_code="forced_regression",
    )
    out = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=stale_distinct,
        price_path=(3500.0, 3550.0),
    )
    assert out.fail_closed is True
    assert out.reason_code is ConfirmationProgressReasonCodeV1.EPOCH_REGRESSION
    _ = a2
    _ = stale


def test_08_session_mismatch() -> None:
    carrier = _carrier(session_id="sess-a")
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    a1, _ = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    out = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a1,
        price_path=(3500.0, 3550.0),
        session_id="other-session",
    )
    assert out.fail_closed is True
    assert out.reason_code is ConfirmationProgressReasonCodeV1.SESSION_MISMATCH


def test_09_venue_mismatch() -> None:
    carrier = _carrier()
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    a1, _ = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    out = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a1,
        price_path=(3500.0, 3550.0),
        venue="other-venue",
    )
    assert out.fail_closed is True
    assert out.reason_code is ConfirmationProgressReasonCodeV1.VENUE_MISMATCH


def test_10_instrument_mismatch() -> None:
    carrier = _carrier()
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    a1, _ = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    other = _key(canonical="OTHER-CANON", venue_inst="OTHER")
    out = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a1,
        price_path=(3500.0, 3550.0),
        instrument=other,
    )
    assert out.fail_closed is True
    assert out.reason_code is ConfirmationProgressReasonCodeV1.INSTRUMENT_MISMATCH


def test_11_side_mismatch() -> None:
    carrier = _carrier()
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    a1, _ = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    # Feed LONG input but claim SHORT side against LONG prior state.
    out = evaluate_directional_assessment_with_confirmation_progress_v1(
        DirectionalAssessmentConfirmationIntegrationInputV1(
            directional_input=_da_input(side=DirectionalAssessmentSide.SHORT),
            policy=_policy(),
            prior_confirmation_progress=carrier.bull_confirmation_state,
            observation_acceptance_result=a1,
            session_id="sess-c3",
            venue="okx_eea",
            instrument=_key(),
            side=ConfirmationSideV1.SHORT,
        )
    )
    assert out.fail_closed is True
    assert out.reason_code is ConfirmationProgressReasonCodeV1.SIDE_MISMATCH


def test_12_runtime_cycle_rejected() -> None:
    carrier = _carrier()
    reject = reject_runtime_cycle_confirmation_advance_v1(carrier.bull_confirmation_state)
    assert reject.reason_code is ConfirmationProgressReasonCodeV1.RUNTIME_CYCLE_NOT_OBSERVATION
    assert reject.fail_closed is True


def test_13_receive_time_rejected() -> None:
    carrier = _carrier()
    reject = reject_receive_time_confirmation_advance_v1(carrier.bull_confirmation_state)
    assert reject.reason_code is ConfirmationProgressReasonCodeV1.RECEIVE_TIME_NOT_EPOCH


def test_14_decision_epoch_rejected() -> None:
    carrier = _carrier()
    reject = reject_decision_epoch_confirmation_advance_v1(carrier.bull_confirmation_state)
    assert reject.reason_code is ConfirmationProgressReasonCodeV1.DECISION_EPOCH_FORBIDDEN


def test_15_observe_signal_resets() -> None:
    policy = _policy(confirmation_epochs=2)
    carrier = _carrier()
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    a1, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    cand = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a1,
        price_path=(3500.0, 3550.0),
        policy=policy,
    )
    carrier = carrier.with_side_state(ConfirmationSideV1.LONG, cand.confirmation_progress_after)
    a2, _ = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    reset = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a2,
        price_path=(3500.0, 3500.5),  # below candidate threshold → OBSERVE signal
        policy=policy,
    )
    assert reset.assessment_signal is ConfirmationAssessmentSignalV1.OBSERVE
    assert (
        reset.confirmation_progress_after.assessment_state is ConfirmationAssessmentStateV1.OBSERVE
    )
    assert reset.confirmation_progress_after.distinct_confirmation_observation_count == 0
    assert reset.confirmation_progress_after.candidate_started_at_epoch is None


def test_16_confirmed_hold_stable() -> None:
    policy = _policy(confirmation_epochs=2)
    carrier = _carrier()
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    path = (3500.0, 3550.0)
    a1, c1 = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    r1 = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a1,
        price_path=path,
        policy=policy,
    )
    carrier = carrier.with_side_state(ConfirmationSideV1.LONG, r1.confirmation_progress_after)
    a2, c1 = _eval_c1(c1, _candidate(event_time=1001.0, mark=11.0))
    r2 = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a2,
        price_path=path,
        policy=policy,
    )
    assert r2.assessment.status is DirectionalAssessmentStatus.CONFIRMED
    count = r2.confirmation_progress_after.distinct_confirmation_observation_count
    carrier = carrier.with_side_state(ConfirmationSideV1.LONG, r2.confirmation_progress_after)
    a3, _ = _eval_c1(c1, _candidate(event_time=1002.0, mark=12.0))
    hold = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a3,
        price_path=path,
        policy=policy,
    )
    assert hold.assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert hold.confirmation_progress_after.distinct_confirmation_observation_count == count
    assert hold.reason_code is ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_HOLD_CONFIRMED


def test_17_deterministic_serialization_and_fingerprints() -> None:
    carrier = _carrier()
    restored = DirectionalConfirmationSideStateCarrierV1.from_dict(carrier.to_dict())
    assert restored == carrier
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    a1, _ = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    r1 = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a1,
        price_path=(3500.0, 3550.0),
    )
    r2 = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a1,
        price_path=(3500.0, 3550.0),
    )
    assert r1.confirmation_progress_result.deterministic_fingerprint == (
        r2.confirmation_progress_result.deterministic_fingerprint
    )
    assert r1.assessment.semantic_digest == r2.assessment.semantic_digest


def test_18_downstream_status_mapping_stable() -> None:
    assert (
        map_confirmation_assessment_state_to_directional_status_v1(
            ConfirmationAssessmentStateV1.OBSERVE
        )
        is DirectionalAssessmentStatus.OBSERVE
    )
    assert (
        map_confirmation_assessment_state_to_directional_status_v1(
            ConfirmationAssessmentStateV1.CANDIDATE
        )
        is DirectionalAssessmentStatus.CANDIDATE
    )
    assert (
        map_confirmation_assessment_state_to_directional_status_v1(
            ConfirmationAssessmentStateV1.CONFIRMED
        )
        is DirectionalAssessmentStatus.CONFIRMED
    )


def test_19_no_config_or_threshold_mutation() -> None:
    policy = _policy()
    assert policy.confirmation_epochs == 2
    assert policy.observe_signal_threshold == 0.001
    assert policy.candidate_signal_threshold == 0.005
    assert policy.confirmation_signal_threshold == 0.01
    source = C3_MODULE.read_text(encoding="utf-8")
    assert "confirmation_epochs" in source
    assert "PARAMETER_CHANGE_INCLUDED = False" in source
    assert "VOLATILITY_CHANGE_INCLUDED = False" in source


def test_20_old_confirmation_counter_not_productive_authority() -> None:
    replay_src = REPLAY_MODULE.read_text(encoding="utf-8")
    assert "evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1" in replay_src
    assert "evaluate_directional_assessment_v1(" not in replay_src
    tree = ast.parse(replay_src)
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                call_names.add(func.id)
            elif isinstance(func, ast.Attribute):
                call_names.add(func.attr)
    assert "evaluate_directional_assessment_v1" not in call_names
    assert "evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1" in call_names
    wiring_src = WIRING_MODULE.read_text(encoding="utf-8")
    assert "LEGACY_LOSSY_CROSS_SIDE_PROJECTOR_AUTHORITY_FORBIDDEN" in wiring_src
    wiring_tree = ast.parse(wiring_src)
    proj_fn = None
    for node in wiring_tree.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "project_mv2_integrated_replay_bar_sequence_state_from_intermediate_v1"
        ):
            proj_fn = node
            break
    assert proj_fn is not None
    proj_src = ast.get_source_segment(wiring_src, proj_fn) or ""
    assert "directional_confirmation_progress_after" in proj_src
    assert "project_directional_confirmation_state_from_assessments_v1" not in proj_src


def test_21_parallel_authority_guard() -> None:
    assert PARALLEL_CONFIRMATION_AUTHORITY_FORBIDDEN is True
    assert_c3_confirmation_authority_exclusive_v1()
    with pytest.raises(ParallelConfirmationAuthorityErrorV1):
        assert_c3_confirmation_authority_exclusive_v1(legacy_confirmation_authority_enabled=True)
    assert DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_CAPABILITY_ID == (
        "DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_V1"
    )


def test_22_legacy_candidate_count_ignored_by_c3() -> None:
    """Poisoned legacy DirectionalConfirmationStateV1 must not drive C3 status."""
    carrier = _carrier()
    c1 = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    a1, _ = _eval_c1(c1, _candidate(event_time=1000.0, mark=10.0))
    out = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=carrier,
        acceptor=a1,
        price_path=(3500.0, 3550.0),
    )
    # Legacy input had candidate_count=99; first DISTINCT CONFIRMED-signal → CANDIDATE at threshold 2.
    assert out.assessment.status is DirectionalAssessmentStatus.CANDIDATE
    assert out.confirmation_progress_after.distinct_confirmation_observation_count == 1


def test_23_run_integrated_imports_c3_not_legacy_da_evaluator() -> None:
    source = inspect.getsource(run_integrated_offline_trading_logic_replay_v1)
    assert "evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1" in source
    assert "evaluate_directional_assessment_v1" not in source
