"""C3 — Directional Assessment Confirmation Integration V1.

Capability: DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_V1

Integrates C1 ObservationAcceptanceResultV1 into C2 confirmation progress and
maps the resulting side-isolated cursor onto DirectionalAssessmentV1.status.

PURE_DOMAIN_COMPONENT=true
DETERMINISTIC=true
NO_IO=true
RUNTIME_WIRING=false
CONFIG_CHANGE=false
PARAMETER_RESEARCH=false
VOLATILITY_SCOPE=false
IMPLICIT_RESUME_ALLOWED=false
PARALLEL_CONFIRMATION_AUTHORITY_FORBIDDEN=true

OBSERVATION_AUTHORITY=C1
CONFIRMATION_PROGRESS_AUTHORITY=C2
INTEGRATION_OWNER=C3
STATE_OWNER=C3_SIDE_STATE_CARRIER_USING_C2_STATE
DOWNSTREAM_STATUS_CONTRACT=DirectionalAssessmentV1.status
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Tuple

from trading.market_state.directional_confirmation_progress_v1 import (
    ConfirmationAssessmentSignalV1,
    ConfirmationAssessmentStateV1,
    ConfirmationProgressInputV1,
    ConfirmationProgressReasonCodeV1,
    ConfirmationProgressResultV1,
    ConfirmationProgressStateV1,
    ConfirmationSideV1,
    evaluate_confirmation_progress_v1,
    initial_confirmation_progress_state_v1,
    reject_decision_epoch_confirmation_advance_v1,
    reject_receive_time_confirmation_advance_v1,
    reject_runtime_cycle_confirmation_advance_v1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceResultV1,
    ObservationAcceptanceStateV1,
    ObservationClassification,
    ObservationReasonCode,
)
from trading.market_state.observation_identity_v1 import (
    InstrumentObservationKeyV1,
    MarketObservationEpoch,
)
from trading.master_v2.directional_assessment_v1 import (
    DirectionalAssessmentHardBlockReason,
    DirectionalAssessmentInputV1,
    DirectionalAssessmentPolicyV1,
    DirectionalAssessmentSide,
    DirectionalAssessmentStatus,
    DirectionalAssessmentV1,
    compute_directional_confidence,
    compute_signal_strength,
    validate_directional_assessment_policy,
    with_computed_directional_assessment_digest,
)
from trading.master_v2.directional_assessment_v1 import (
    _collect_input_gate_blocks,
    _finalize_assessment,
    _sorted_reason_values,
)

DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_CAPABILITY_ID = (
    "DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_V1"
)
DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_COMPONENT = (
    "DirectionalAssessmentConfirmationIntegrationV1"
)
DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_PURITY = "PURE_DETERMINISTIC_NO_IO"
DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_STATE_VERSION = "v1"

PARALLEL_CONFIRMATION_AUTHORITY_FORBIDDEN = True
LEGACY_DIRECTIONAL_CONFIRMATION_STATE_AUTHORITY = False
LEGACY_TRADING_EPOCH_COUNTER_CONFIRMATION_AUTHORITY = False
IMPLICIT_RESUME_ALLOWED = False
RUNTIME_WIRING_INCLUDED = False
PARAMETER_CHANGE_INCLUDED = False
VOLATILITY_CHANGE_INCLUDED = False


class ParallelConfirmationAuthorityErrorV1(ValueError):
    """Raised when C3 and legacy confirmation authorities are combined."""


def assert_c3_confirmation_authority_exclusive_v1(
    *,
    legacy_confirmation_authority_enabled: bool = False,
) -> None:
    """Fail-closed guard: C3 must not share confirmation authority with the legacy path."""
    if not PARALLEL_CONFIRMATION_AUTHORITY_FORBIDDEN:
        raise ParallelConfirmationAuthorityErrorV1("PARALLEL_CONFIRMATION_AUTHORITY_FLAG_DRIFT")
    if legacy_confirmation_authority_enabled:
        raise ParallelConfirmationAuthorityErrorV1(
            "PARALLEL_CONFIRMATION_AUTHORITY_FORBIDDEN:"
            "legacy_trading_epoch_counter_must_not_share_authority_with_c3"
        )
    if LEGACY_DIRECTIONAL_CONFIRMATION_STATE_AUTHORITY:
        raise ParallelConfirmationAuthorityErrorV1(
            "LEGACY_DIRECTIONAL_CONFIRMATION_STATE_AUTHORITY_DRIFT"
        )
    if LEGACY_TRADING_EPOCH_COUNTER_CONFIRMATION_AUTHORITY:
        raise ParallelConfirmationAuthorityErrorV1(
            "LEGACY_TRADING_EPOCH_COUNTER_CONFIRMATION_AUTHORITY_DRIFT"
        )


@dataclass(frozen=True)
class DirectionalConfirmationSideStateCarrierV1:
    """Caller-owned Bull/Bear confirmation progress carrier (C3 state owner)."""

    bull_confirmation_state: ConfirmationProgressStateV1
    bear_confirmation_state: ConfirmationProgressStateV1

    def __post_init__(self) -> None:
        if self.bull_confirmation_state.side is not ConfirmationSideV1.LONG:
            raise ValueError("INVALID_C3_SIDE_CARRIER:bull_side")
        if self.bear_confirmation_state.side is not ConfirmationSideV1.SHORT:
            raise ValueError("INVALID_C3_SIDE_CARRIER:bear_side")
        if self.bull_confirmation_state.session_id != self.bear_confirmation_state.session_id:
            raise ValueError("INVALID_C3_SIDE_CARRIER:session_mismatch")
        if self.bull_confirmation_state.venue != self.bear_confirmation_state.venue:
            raise ValueError("INVALID_C3_SIDE_CARRIER:venue_mismatch")
        if self.bull_confirmation_state.instrument != self.bear_confirmation_state.instrument:
            raise ValueError("INVALID_C3_SIDE_CARRIER:instrument_mismatch")

    def for_side(self, side: ConfirmationSideV1) -> ConfirmationProgressStateV1:
        if side is ConfirmationSideV1.LONG:
            return self.bull_confirmation_state
        if side is ConfirmationSideV1.SHORT:
            return self.bear_confirmation_state
        raise ValueError("INVALID_C3_SIDE_CARRIER:unknown_side")

    def with_side_state(
        self,
        side: ConfirmationSideV1,
        state: ConfirmationProgressStateV1,
    ) -> "DirectionalConfirmationSideStateCarrierV1":
        if side is ConfirmationSideV1.LONG:
            return DirectionalConfirmationSideStateCarrierV1(
                bull_confirmation_state=state,
                bear_confirmation_state=self.bear_confirmation_state,
            )
        if side is ConfirmationSideV1.SHORT:
            return DirectionalConfirmationSideStateCarrierV1(
                bull_confirmation_state=self.bull_confirmation_state,
                bear_confirmation_state=state,
            )
        raise ValueError("INVALID_C3_SIDE_CARRIER:unknown_side")

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_STATE_VERSION,
            "bull_confirmation_state": self.bull_confirmation_state.to_dict(),
            "bear_confirmation_state": self.bear_confirmation_state.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DirectionalConfirmationSideStateCarrierV1":
        version = str(
            payload.get("version", DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_STATE_VERSION)
        )
        if version != DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_STATE_VERSION:
            raise ValueError(f"UNSUPPORTED_C3_SIDE_CARRIER_VERSION:{version}")
        return cls(
            bull_confirmation_state=ConfirmationProgressStateV1.from_dict(
                payload["bull_confirmation_state"]
            ),
            bear_confirmation_state=ConfirmationProgressStateV1.from_dict(
                payload["bear_confirmation_state"]
            ),
        )


@dataclass(frozen=True)
class DirectionalAssessmentConfirmationIntegrationInputV1:
    """Pure C3 evaluator input. No clocks, configs, or runtime wiring."""

    directional_input: DirectionalAssessmentInputV1
    policy: DirectionalAssessmentPolicyV1
    prior_confirmation_progress: ConfirmationProgressStateV1
    observation_acceptance_result: ObservationAcceptanceResultV1
    session_id: str
    venue: str
    instrument: InstrumentObservationKeyV1
    side: ConfirmationSideV1
    acceptor_result_fingerprint: Optional[str] = None


@dataclass(frozen=True)
class DirectionalAssessmentConfirmationIntegrationResultV1:
    assessment: DirectionalAssessmentV1
    confirmation_progress_before: ConfirmationProgressStateV1
    confirmation_progress_after: ConfirmationProgressStateV1
    confirmation_progress_result: ConfirmationProgressResultV1
    assessment_signal: ConfirmationAssessmentSignalV1
    confirmation_advanced: bool
    state_changed: bool
    fail_closed: bool
    reason_code: ConfirmationProgressReasonCodeV1


def initial_directional_confirmation_side_state_carrier_v1(
    *,
    session_id: str,
    venue: str,
    instrument: InstrumentObservationKeyV1,
    initial_market_observation_epoch: Optional[MarketObservationEpoch] = None,
) -> DirectionalConfirmationSideStateCarrierV1:
    """Session-bound empty OBSERVE carrier for Bull and Bear."""
    return DirectionalConfirmationSideStateCarrierV1(
        bull_confirmation_state=initial_confirmation_progress_state_v1(
            session_id=session_id,
            venue=venue,
            instrument=instrument,
            side=ConfirmationSideV1.LONG,
            initial_market_observation_epoch=initial_market_observation_epoch,
        ),
        bear_confirmation_state=initial_confirmation_progress_state_v1(
            session_id=session_id,
            venue=venue,
            instrument=instrument,
            side=ConfirmationSideV1.SHORT,
            initial_market_observation_epoch=initial_market_observation_epoch,
        ),
    )


def non_advancing_observation_acceptance_result_v1(
    *,
    bound_instrument_key: InstrumentObservationKeyV1,
    market_observation_epoch: Optional[MarketObservationEpoch] = None,
) -> ObservationAcceptanceResultV1:
    """Caller helper: explicit NON_DISTINCT placeholder (never invents DISTINCT)."""
    epoch = (
        MarketObservationEpoch(value=0)
        if market_observation_epoch is None
        else market_observation_epoch
    )
    state = ObservationAcceptanceStateV1(
        last_accepted_observation_identity=None,
        market_observation_epoch=epoch,
        bound_instrument_key=bound_instrument_key,
        last_accepted_transport=None,
    )
    return ObservationAcceptanceResultV1(
        classification=ObservationClassification.DUPLICATE,
        strategy_advance_allowed=False,
        state_before=state,
        state_after=state,
        observation_identity=None,
        reason_code=ObservationReasonCode.DUPLICATE.value,
    )


def map_signal_strength_to_confirmation_assessment_signal_v1(
    signal_strength: float,
    policy: DirectionalAssessmentPolicyV1,
) -> ConfirmationAssessmentSignalV1:
    """Deterministic mapping using existing DA thresholds (no redefinition)."""
    if float(signal_strength) < float(policy.candidate_signal_threshold):
        return ConfirmationAssessmentSignalV1.OBSERVE
    if float(signal_strength) < float(policy.confirmation_signal_threshold):
        return ConfirmationAssessmentSignalV1.CANDIDATE
    return ConfirmationAssessmentSignalV1.CONFIRMED


def map_confirmation_assessment_state_to_directional_status_v1(
    state: ConfirmationAssessmentStateV1,
) -> DirectionalAssessmentStatus:
    if state is ConfirmationAssessmentStateV1.OBSERVE:
        return DirectionalAssessmentStatus.OBSERVE
    if state is ConfirmationAssessmentStateV1.CANDIDATE:
        return DirectionalAssessmentStatus.CANDIDATE
    if state is ConfirmationAssessmentStateV1.CONFIRMED:
        return DirectionalAssessmentStatus.CONFIRMED
    # INVALID never silently treated as progress; map to existing INVALID.
    return DirectionalAssessmentStatus.INVALID


def map_directional_side_to_confirmation_side_v1(
    side: DirectionalAssessmentSide,
) -> ConfirmationSideV1:
    if side is DirectionalAssessmentSide.LONG:
        return ConfirmationSideV1.LONG
    if side is DirectionalAssessmentSide.SHORT:
        return ConfirmationSideV1.SHORT
    raise ValueError(f"unsupported_directional_side:{side!r}")


def _fail_closed_status_for_reason(
    reason: ConfirmationProgressReasonCodeV1,
) -> DirectionalAssessmentStatus:
    if reason in {
        ConfirmationProgressReasonCodeV1.STATE_INCONSISTENT,
        ConfirmationProgressReasonCodeV1.INVALID_SIGNAL,
        ConfirmationProgressReasonCodeV1.INVALID_THRESHOLD,
    }:
        return DirectionalAssessmentStatus.INVALID
    return DirectionalAssessmentStatus.BLOCKED


def evaluate_directional_assessment_with_confirmation_progress_v1(
    integration_input: DirectionalAssessmentConfirmationIntegrationInputV1,
) -> DirectionalAssessmentConfirmationIntegrationResultV1:
    """C3 productive confirmation integration. Legacy epoch-counter is not consulted."""
    assert_c3_confirmation_authority_exclusive_v1(
        legacy_confirmation_authority_enabled=False,
    )

    inp = integration_input.directional_input
    policy = integration_input.policy
    prior = integration_input.prior_confirmation_progress

    def _gated_no_progress(
        *,
        status: DirectionalAssessmentStatus,
        hard_block_reasons: Tuple[str, ...],
        reason_codes: Tuple[str, ...],
        progress_reason: ConfirmationProgressReasonCodeV1,
    ) -> DirectionalAssessmentConfirmationIntegrationResultV1:
        assessment = _finalize_assessment(
            inp,
            policy,
            status=status,
            signal_strength=0.0,
            confidence=0.0,
            hard_block_reasons=hard_block_reasons,
            reason_codes=reason_codes,
        )
        # Deterministic fingerprint body via C2 unchanged-result helper family.
        fingerprint_donor = reject_runtime_cycle_confirmation_advance_v1(prior)
        stub = ConfirmationProgressResultV1(
            accepted=False,
            state_before=prior,
            state_after=prior,
            reason_code=progress_reason,
            state_changed=False,
            confirmation_advanced=False,
            fail_closed=True,
            observation_epoch_before=prior.latest_accepted_market_observation_epoch,
            observation_epoch_after=prior.latest_accepted_market_observation_epoch,
            deterministic_fingerprint=fingerprint_donor.deterministic_fingerprint,
        )
        return DirectionalAssessmentConfirmationIntegrationResultV1(
            assessment=assessment,
            confirmation_progress_before=prior,
            confirmation_progress_after=prior,
            confirmation_progress_result=stub,
            assessment_signal=ConfirmationAssessmentSignalV1.OBSERVE,
            confirmation_advanced=False,
            state_changed=False,
            fail_closed=True,
            reason_code=progress_reason,
        )

    policy_blocks = validate_directional_assessment_policy(
        policy, policy_version=inp.policy_version
    )
    if policy_blocks:
        progress_reason = (
            ConfirmationProgressReasonCodeV1.INVALID_THRESHOLD
            if DirectionalAssessmentHardBlockReason.POLICY_CONFIRMATION_EPOCHS_INVALID
            in policy_blocks
            else ConfirmationProgressReasonCodeV1.STATE_INCONSISTENT
        )
        return _gated_no_progress(
            status=DirectionalAssessmentStatus.BLOCKED,
            hard_block_reasons=_sorted_reason_values(policy_blocks),
            reason_codes=("policy_validation_failed",),
            progress_reason=progress_reason,
        )

    gate_blocks = _collect_input_gate_blocks(inp)
    if gate_blocks:
        status = (
            DirectionalAssessmentStatus.INVALID
            if any(
                r
                in {
                    DirectionalAssessmentHardBlockReason.INPUT_INCOMPLETE,
                    DirectionalAssessmentHardBlockReason.PRICE_PATH_TOO_SHORT,
                    DirectionalAssessmentHardBlockReason.REFERENCE_PRICE_NON_POSITIVE,
                    DirectionalAssessmentHardBlockReason.SCOPE_EVENT_REF_INVALID,
                }
                for r in gate_blocks
            )
            else DirectionalAssessmentStatus.BLOCKED
        )
        return _gated_no_progress(
            status=status,
            hard_block_reasons=_sorted_reason_values(gate_blocks),
            reason_codes=("input_gate_failed",),
            progress_reason=ConfirmationProgressReasonCodeV1.STATE_INCONSISTENT,
        )

    signal_strength = compute_signal_strength(
        price_path=inp.price_path,
        side=inp.side,
        reference_price=inp.reference_price,
    )
    confidence = compute_directional_confidence(
        signal_strength, policy.confirmation_signal_threshold
    )
    assessment_signal = map_signal_strength_to_confirmation_assessment_signal_v1(
        signal_strength, policy
    )

    progress_input = ConfirmationProgressInputV1(
        prior_state=prior,
        observation_acceptance_result=integration_input.observation_acceptance_result,
        session_id=integration_input.session_id,
        venue=integration_input.venue,
        instrument=integration_input.instrument,
        side=integration_input.side,
        assessment_signal=assessment_signal,
        confirmation_threshold=int(policy.confirmation_epochs),
        acceptor_result_fingerprint=integration_input.acceptor_result_fingerprint,
    )
    progress_result = evaluate_confirmation_progress_v1(progress_input)

    if progress_result.fail_closed:
        status = _fail_closed_status_for_reason(progress_result.reason_code)
        assessment = _finalize_assessment(
            inp,
            policy,
            status=status,
            signal_strength=signal_strength,
            confidence=confidence,
            hard_block_reasons=(progress_result.reason_code.value.lower(),),
            reason_codes=("confirmation_progress_fail_closed", progress_result.reason_code.value),
        )
        return DirectionalAssessmentConfirmationIntegrationResultV1(
            assessment=assessment,
            confirmation_progress_before=prior,
            confirmation_progress_after=progress_result.state_after,
            confirmation_progress_result=progress_result,
            assessment_signal=assessment_signal,
            confirmation_advanced=False,
            state_changed=False,
            fail_closed=True,
            reason_code=progress_result.reason_code,
        )

    status = map_confirmation_assessment_state_to_directional_status_v1(
        progress_result.state_after.assessment_state
    )
    reason_codes: Tuple[str, ...] = (
        "c3_confirmation_progress",
        progress_result.reason_code.value,
        f"assessment_signal_{assessment_signal.value}",
        f"confirmation_state_{progress_result.state_after.assessment_state.value}",
    )
    assessment = with_computed_directional_assessment_digest(
        _finalize_assessment(
            inp,
            policy,
            status=status,
            signal_strength=signal_strength,
            confidence=confidence,
            hard_block_reasons=(),
            reason_codes=reason_codes,
        )
    )

    return DirectionalAssessmentConfirmationIntegrationResultV1(
        assessment=assessment,
        confirmation_progress_before=prior,
        confirmation_progress_after=progress_result.state_after,
        confirmation_progress_result=progress_result,
        assessment_signal=assessment_signal,
        confirmation_advanced=bool(progress_result.confirmation_advanced),
        state_changed=bool(progress_result.state_changed),
        fail_closed=False,
        reason_code=progress_result.reason_code,
    )


def evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1(
    *,
    bull_input: DirectionalAssessmentInputV1,
    bear_input: DirectionalAssessmentInputV1,
    policy: DirectionalAssessmentPolicyV1,
    prior_carrier: DirectionalConfirmationSideStateCarrierV1,
    observation_acceptance_result: ObservationAcceptanceResultV1,
    session_id: str,
    venue: str,
    instrument: InstrumentObservationKeyV1,
    acceptor_result_fingerprint: Optional[str] = None,
) -> tuple[
    DirectionalAssessmentConfirmationIntegrationResultV1,
    DirectionalAssessmentConfirmationIntegrationResultV1,
    DirectionalConfirmationSideStateCarrierV1,
]:
    """Evaluate Bull then Bear with strict side isolation on the shared C1 result."""
    assert_c3_confirmation_authority_exclusive_v1()

    bull = evaluate_directional_assessment_with_confirmation_progress_v1(
        DirectionalAssessmentConfirmationIntegrationInputV1(
            directional_input=bull_input,
            policy=policy,
            prior_confirmation_progress=prior_carrier.bull_confirmation_state,
            observation_acceptance_result=observation_acceptance_result,
            session_id=session_id,
            venue=venue,
            instrument=instrument,
            side=ConfirmationSideV1.LONG,
            acceptor_result_fingerprint=acceptor_result_fingerprint,
        )
    )
    # Opposite side must remain byte/value-identical after bull evaluation.
    mid_carrier = prior_carrier.with_side_state(
        ConfirmationSideV1.LONG, bull.confirmation_progress_after
    )
    if mid_carrier.bear_confirmation_state != prior_carrier.bear_confirmation_state:
        raise ParallelConfirmationAuthorityErrorV1("BULL_UPDATE_MUTATED_BEAR_STATE")

    bear = evaluate_directional_assessment_with_confirmation_progress_v1(
        DirectionalAssessmentConfirmationIntegrationInputV1(
            directional_input=bear_input,
            policy=policy,
            prior_confirmation_progress=mid_carrier.bear_confirmation_state,
            observation_acceptance_result=observation_acceptance_result,
            session_id=session_id,
            venue=venue,
            instrument=instrument,
            side=ConfirmationSideV1.SHORT,
            acceptor_result_fingerprint=acceptor_result_fingerprint,
        )
    )
    after_carrier = mid_carrier.with_side_state(
        ConfirmationSideV1.SHORT, bear.confirmation_progress_after
    )
    if after_carrier.bull_confirmation_state != mid_carrier.bull_confirmation_state:
        raise ParallelConfirmationAuthorityErrorV1("BEAR_UPDATE_MUTATED_BULL_STATE")

    return bull, bear, after_carrier


# Explicit reject helpers re-exported for C3 tests / integration contracts.
__all__ = [
    "DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_CAPABILITY_ID",
    "DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_COMPONENT",
    "DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_PURITY",
    "PARALLEL_CONFIRMATION_AUTHORITY_FORBIDDEN",
    "ParallelConfirmationAuthorityErrorV1",
    "DirectionalConfirmationSideStateCarrierV1",
    "DirectionalAssessmentConfirmationIntegrationInputV1",
    "DirectionalAssessmentConfirmationIntegrationResultV1",
    "assert_c3_confirmation_authority_exclusive_v1",
    "initial_directional_confirmation_side_state_carrier_v1",
    "non_advancing_observation_acceptance_result_v1",
    "map_signal_strength_to_confirmation_assessment_signal_v1",
    "map_confirmation_assessment_state_to_directional_status_v1",
    "map_directional_side_to_confirmation_side_v1",
    "evaluate_directional_assessment_with_confirmation_progress_v1",
    "evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1",
    "reject_decision_epoch_confirmation_advance_v1",
    "reject_receive_time_confirmation_advance_v1",
    "reject_runtime_cycle_confirmation_advance_v1",
]
