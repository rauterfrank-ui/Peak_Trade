"""Single-lane confirmation presence and activation lifecycle V1.

Presence/lifecycle wrapper only. Not a direction evaluator and not a C3 owner.

ElementaryDirectionV1 remains the sole elementary direction identity.
C3 ``evaluate_directional_assessment_with_confirmation_progress_v1`` remains
confirmation-only. This module selects which C2 cursor may exist.

INACTIVE is absence — not OBSERVE, BLOCKED, or INVALID.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional

from trading.market_state.directional_confirmation_progress_v1 import (
    ConfirmationAssessmentStateV1,
    ConfirmationProgressStateV1,
    ConfirmationSideV1,
    initial_confirmation_progress_state_v1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceResultV1,
    ObservationClassification,
)
from trading.market_state.elementary_direction_v1 import (
    ElementaryDirectionResultV1,
    ElementaryDirectionStatusV1,
    ElementaryDirectionV1,
)
from trading.market_state.observation_identity_v1 import (
    InstrumentObservationKeyV1,
    MarketObservationEpoch,
)
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    DirectionalConfirmationSideStateCarrierV1,
    initial_directional_confirmation_side_state_carrier_v1,
)

SINGLE_LANE_CONFIRMATION_ACTIVATION_COMPONENT = "SingleLaneConfirmationActivationV1"
SINGLE_LANE_CONFIRMATION_ACTIVATION_PURITY = "PURE_DETERMINISTIC_NO_IO"
SINGLE_LANE_CONFIRMATION_ACTIVATION_VERSION = "v1"
AUTHORITY_EFFECT_NONE = "NONE"


class SingleLanePresenceKindV1(str, Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"


class SingleLaneLifecycleReasonV1(str, Enum):
    NEUTRAL_NO_LANE = "neutral_no_lane"
    REJECTED_NO_LANE = "rejected_no_lane"
    CONTINUE_SELECTED_LANE = "continue_selected_lane"
    ACTIVATE_NEW_SEQUENCE = "activate_new_sequence"
    DISCARD_NO_LANE = "discard_no_lane"
    SWITCH_ACTIVATE_NEW_SEQUENCE = "switch_activate_new_sequence"
    IDENTITY_CHANGE_WITHOUT_DISTINCT = "identity_change_without_distinct"
    NON_DISTINCT_NO_ACTIVATION = "non_distinct_no_activation"


class InactiveLaneAuthorityErrorV1(ValueError):
    """Raised when an inactive lane is asked to expose C2/DA authority."""


def selected_lane_from_elementary_direction_v1(
    result: ElementaryDirectionResultV1,
) -> Optional[ConfirmationSideV1]:
    """Map evaluated elementary identity onto a confirmation lane.

    BULL → LONG. BEAR → SHORT. NEUTRAL → no lane.
    Rejected/invalid identities do not normalize to NEUTRAL and select no lane.
    """
    if result.status is not ElementaryDirectionStatusV1.EVALUATED:
        return None
    if result.direction is ElementaryDirectionV1.BULL:
        return ConfirmationSideV1.LONG
    if result.direction is ElementaryDirectionV1.BEAR:
        return ConfirmationSideV1.SHORT
    return None


def is_distinct_admission_v1(result: ObservationAcceptanceResultV1) -> bool:
    return (
        result.classification is ObservationClassification.DISTINCT
        and result.strategy_advance_allowed is True
    )


def _slot_holds_authoritative_progress(state: ConfirmationProgressStateV1) -> bool:
    """Cap-61 dual-carrier decode: empty unfingerprinted OBSERVE is Inactive padding."""
    if state.assessment_state is ConfirmationAssessmentStateV1.INVALID:
        return False
    if state.last_processed_acceptor_result_fingerprint:
        return True
    if state.assessment_state is not ConfirmationAssessmentStateV1.OBSERVE:
        return True
    if state.distinct_confirmation_observation_count != 0:
        return True
    if state.candidate_started_at_epoch is not None:
        return True
    return False


@dataclass(frozen=True)
class SingleLaneConfirmationPresenceV1:
    """Typed lane presence: Inactive (absence) or Active(C2 cursor)."""

    kind: SingleLanePresenceKindV1
    selected_side: Optional[ConfirmationSideV1]
    confirmation_progress: Optional[ConfirmationProgressStateV1]

    def __post_init__(self) -> None:
        if self.kind is SingleLanePresenceKindV1.INACTIVE:
            if self.selected_side is not None or self.confirmation_progress is not None:
                raise ValueError("INACTIVE_MUST_BE_ABSENCE")
            return
        if self.kind is not SingleLanePresenceKindV1.ACTIVE:
            raise ValueError("UNKNOWN_LANE_PRESENCE_KIND")
        if self.selected_side is None or self.confirmation_progress is None:
            raise ValueError("ACTIVE_REQUIRES_SIDE_AND_C2")
        if self.confirmation_progress.side is not self.selected_side:
            raise ValueError("ACTIVE_SIDE_MISMATCH")

    @property
    def is_active(self) -> bool:
        return self.kind is SingleLanePresenceKindV1.ACTIVE

    def authoritative_confirmation_progress(self) -> ConfirmationProgressStateV1:
        if self.confirmation_progress is None:
            raise InactiveLaneAuthorityErrorV1("INACTIVE_HAS_NO_C2_AUTHORITY")
        return self.confirmation_progress

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": SINGLE_LANE_CONFIRMATION_ACTIVATION_VERSION,
            "kind": self.kind.value,
            "selected_side": None if self.selected_side is None else self.selected_side.value,
            "confirmation_progress": (
                None if self.confirmation_progress is None else self.confirmation_progress.to_dict()
            ),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SingleLaneConfirmationPresenceV1":
        kind = SingleLanePresenceKindV1(str(payload["kind"]))
        side_raw = payload.get("selected_side")
        progress_raw = payload.get("confirmation_progress")
        return cls(
            kind=kind,
            selected_side=None if side_raw is None else ConfirmationSideV1(str(side_raw)),
            confirmation_progress=(
                None
                if progress_raw is None
                else ConfirmationProgressStateV1.from_dict(progress_raw)
            ),
        )


def inactive_single_lane_presence_v1() -> SingleLaneConfirmationPresenceV1:
    return SingleLaneConfirmationPresenceV1(
        kind=SingleLanePresenceKindV1.INACTIVE,
        selected_side=None,
        confirmation_progress=None,
    )


def active_single_lane_presence_v1(
    *,
    selected_side: ConfirmationSideV1,
    confirmation_progress: ConfirmationProgressStateV1,
) -> SingleLaneConfirmationPresenceV1:
    return SingleLaneConfirmationPresenceV1(
        kind=SingleLanePresenceKindV1.ACTIVE,
        selected_side=selected_side,
        confirmation_progress=confirmation_progress,
    )


def _new_sequence_state(
    *,
    selected_side: ConfirmationSideV1,
    observation_acceptance_result: ObservationAcceptanceResultV1,
    session_id: str,
    venue: str,
    instrument: InstrumentObservationKeyV1,
) -> ConfirmationProgressStateV1:
    """Activate at C1 state_before epoch so the same DISTINCT advances delta==1."""
    return initial_confirmation_progress_state_v1(
        session_id=session_id,
        venue=venue,
        instrument=instrument,
        side=selected_side,
        initial_market_observation_epoch=(
            observation_acceptance_result.state_before.market_observation_epoch
        ),
    )


def prior_presence_from_dual_carrier_v1(
    prior_carrier: Optional[DirectionalConfirmationSideStateCarrierV1],
) -> SingleLaneConfirmationPresenceV1:
    """Decode Cap-61 dual padding into typed presence. Never treats padding as authority."""
    if prior_carrier is None:
        return inactive_single_lane_presence_v1()
    bull_auth = _slot_holds_authoritative_progress(prior_carrier.bull_confirmation_state)
    bear_auth = _slot_holds_authoritative_progress(prior_carrier.bear_confirmation_state)
    if bull_auth and bear_auth:
        # Dual productive authority is forbidden on this path; fail closed to absence.
        return inactive_single_lane_presence_v1()
    if bull_auth:
        return active_single_lane_presence_v1(
            selected_side=ConfirmationSideV1.LONG,
            confirmation_progress=prior_carrier.bull_confirmation_state,
        )
    if bear_auth:
        return active_single_lane_presence_v1(
            selected_side=ConfirmationSideV1.SHORT,
            confirmation_progress=prior_carrier.bear_confirmation_state,
        )
    return inactive_single_lane_presence_v1()


def persist_single_lane_into_dual_carrier_v1(
    *,
    presence: SingleLaneConfirmationPresenceV1,
    session_id: str,
    venue: str,
    instrument: InstrumentObservationKeyV1,
    padding_epoch: Optional[MarketObservationEpoch] = None,
) -> DirectionalConfirmationSideStateCarrierV1:
    """Cap-61 schema adapter. Opposite/inactive slots are non-authoritative padding."""
    padding = initial_directional_confirmation_side_state_carrier_v1(
        session_id=session_id,
        venue=venue,
        instrument=instrument,
        initial_market_observation_epoch=padding_epoch,
    )
    if not presence.is_active or presence.confirmation_progress is None:
        return padding
    if presence.selected_side is ConfirmationSideV1.LONG:
        return DirectionalConfirmationSideStateCarrierV1(
            bull_confirmation_state=presence.confirmation_progress,
            bear_confirmation_state=padding.bear_confirmation_state,
        )
    if presence.selected_side is ConfirmationSideV1.SHORT:
        return DirectionalConfirmationSideStateCarrierV1(
            bull_confirmation_state=padding.bull_confirmation_state,
            bear_confirmation_state=presence.confirmation_progress,
        )
    return padding


@dataclass(frozen=True)
class SingleLaneLifecycleResultV1:
    presence: SingleLaneConfirmationPresenceV1
    elementary_direction: Optional[ElementaryDirectionV1]
    identity_status: ElementaryDirectionStatusV1
    selected_side: Optional[ConfirmationSideV1]
    activated_new_sequence: bool
    discarded_prior_authority: bool
    distinct_admission: bool
    reason_code: str
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def __post_init__(self) -> None:
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("AUTHORITY_EFFECT_MUST_BE_NONE")


def apply_single_lane_confirmation_lifecycle_v1(
    *,
    prior_presence: SingleLaneConfirmationPresenceV1,
    elementary: ElementaryDirectionResultV1,
    observation_acceptance_result: ObservationAcceptanceResultV1,
    session_id: str,
    venue: str,
    instrument: InstrumentObservationKeyV1,
) -> SingleLaneLifecycleResultV1:
    """Apply the ratified OD1 activation table. Does not evaluate C3."""
    distinct = is_distinct_admission_v1(observation_acceptance_result)
    selected = selected_lane_from_elementary_direction_v1(elementary)
    prior_side = prior_presence.selected_side if prior_presence.is_active else None
    evaluated_direction = (
        elementary.direction if elementary.status is ElementaryDirectionStatusV1.EVALUATED else None
    )

    def _inactive(
        *,
        reason: SingleLaneLifecycleReasonV1,
        discarded: bool,
        activated: bool = False,
    ) -> SingleLaneLifecycleResultV1:
        return SingleLaneLifecycleResultV1(
            presence=inactive_single_lane_presence_v1(),
            elementary_direction=evaluated_direction,
            identity_status=elementary.status,
            selected_side=None,
            activated_new_sequence=activated,
            discarded_prior_authority=discarded,
            distinct_admission=distinct,
            reason_code=reason.value,
        )

    def _active(
        *,
        side: ConfirmationSideV1,
        state: ConfirmationProgressStateV1,
        reason: SingleLaneLifecycleReasonV1,
        discarded: bool,
        activated: bool,
    ) -> SingleLaneLifecycleResultV1:
        return SingleLaneLifecycleResultV1(
            presence=active_single_lane_presence_v1(
                selected_side=side,
                confirmation_progress=state,
            ),
            elementary_direction=evaluated_direction,
            identity_status=elementary.status,
            selected_side=side,
            activated_new_sequence=activated,
            discarded_prior_authority=discarded,
            distinct_admission=distinct,
            reason_code=reason.value,
        )

    if elementary.status is not ElementaryDirectionStatusV1.EVALUATED:
        return _inactive(
            reason=SingleLaneLifecycleReasonV1.REJECTED_NO_LANE,
            discarded=prior_presence.is_active,
        )

    if selected is None:
        return _inactive(
            reason=SingleLaneLifecycleReasonV1.NEUTRAL_NO_LANE,
            discarded=prior_presence.is_active,
        )

    if prior_side is selected and prior_presence.is_active:
        return _active(
            side=selected,
            state=prior_presence.authoritative_confirmation_progress(),
            reason=SingleLaneLifecycleReasonV1.CONTINUE_SELECTED_LANE,
            discarded=False,
            activated=False,
        )

    if not distinct:
        if prior_side is not None and prior_side is not selected:
            return _inactive(
                reason=SingleLaneLifecycleReasonV1.IDENTITY_CHANGE_WITHOUT_DISTINCT,
                discarded=True,
            )
        return _inactive(
            reason=SingleLaneLifecycleReasonV1.NON_DISTINCT_NO_ACTIVATION,
            discarded=prior_presence.is_active,
        )

    discarded = prior_presence.is_active and prior_side is not selected
    reason = (
        SingleLaneLifecycleReasonV1.SWITCH_ACTIVATE_NEW_SEQUENCE
        if discarded
        else SingleLaneLifecycleReasonV1.ACTIVATE_NEW_SEQUENCE
    )
    return _active(
        side=selected,
        state=_new_sequence_state(
            selected_side=selected,
            observation_acceptance_result=observation_acceptance_result,
            session_id=session_id,
            venue=venue,
            instrument=instrument,
        ),
        reason=reason,
        discarded=discarded,
        activated=True,
    )


__all__ = [
    "AUTHORITY_EFFECT_NONE",
    "SINGLE_LANE_CONFIRMATION_ACTIVATION_COMPONENT",
    "SINGLE_LANE_CONFIRMATION_ACTIVATION_PURITY",
    "SINGLE_LANE_CONFIRMATION_ACTIVATION_VERSION",
    "InactiveLaneAuthorityErrorV1",
    "SingleLaneConfirmationPresenceV1",
    "SingleLaneLifecycleReasonV1",
    "SingleLaneLifecycleResultV1",
    "SingleLanePresenceKindV1",
    "active_single_lane_presence_v1",
    "apply_single_lane_confirmation_lifecycle_v1",
    "inactive_single_lane_presence_v1",
    "is_distinct_admission_v1",
    "persist_single_lane_into_dual_carrier_v1",
    "prior_presence_from_dual_carrier_v1",
    "selected_lane_from_elementary_direction_v1",
]
