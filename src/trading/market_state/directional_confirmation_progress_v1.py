"""Directional Confirmation Progress V1 — pure deterministic C2 mechanism.

Capability: MASTER_V2_DOUBLE_PLAY_C2_DIRECTIONAL_CONFIRMATION_PROGRESS_V1

PURE_DOMAIN_COMPONENT=true
DETERMINISTIC=true
NO_IO=true
NO_GLOBAL_STATE=true
NO_GLOBAL_CLOCK_READ=true
RUNTIME_WIRING=false
CONFIG_CHANGE=false
DECISION_EPOCH_AUTHORITY=false
VOLATILITY_SCOPE=false
PARAMETER_RESEARCH=false
IMPLICIT_RESUME_ALLOWED=false

C1 remains the sole authority for distinct market observation acceptance.
C2 advances confirmation progress only on accepted DISTINCT MarketObservationEpoch
steps (prior + 1). RuntimeCycle, receive time, and DecisionEpoch never advance
confirmation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceResultV1,
    ObservationClassification,
)
from trading.market_state.observation_identity_v1 import (
    InstrumentObservationKeyV1,
    MarketObservationEpoch,
)

CONFIRMATION_PROGRESS_COMPONENT = "DirectionalConfirmationProgressV1"
CONFIRMATION_PROGRESS_PURITY = "PURE_DETERMINISTIC_NO_IO"
CONFIRMATION_PROGRESS_STATE_VERSION = "v1"
CONFIRMATION_PROGRESS_CAPABILITY_ID = (
    "MASTER_V2_DOUBLE_PLAY_C2_DIRECTIONAL_CONFIRMATION_PROGRESS_V1"
)

# CONFIRMED count policy (single documented rule):
# Once CONFIRMED, distinct_confirmation_observation_count remains stable.
# Further accepted-distinct CONFIRMED/CANDIDATE signals hold CONFIRMED without
# unbounded count growth.
CONFIRMED_COUNT_POLICY = "HOLD_STABLE"


class ConfirmationSideV1(str, Enum):
    LONG = "long"
    SHORT = "short"


class ConfirmationAssessmentStateV1(str, Enum):
    OBSERVE = "observe"
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    INVALID = "invalid"


class ConfirmationAssessmentSignalV1(str, Enum):
    """Assessment signal input; INVALID is never a valid progress signal."""

    OBSERVE = "observe"
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"


class ConfirmationProgressReasonCodeV1(str, Enum):
    INITIALIZED = "INITIALIZED"
    ACCEPTED_DISTINCT_PROGRESS = "ACCEPTED_DISTINCT_PROGRESS"
    ACCEPTED_DISTINCT_RESET = "ACCEPTED_DISTINCT_RESET"
    ACCEPTED_DISTINCT_CONFIRMED = "ACCEPTED_DISTINCT_CONFIRMED"
    ACCEPTED_DISTINCT_HOLD_CONFIRMED = "ACCEPTED_DISTINCT_HOLD_CONFIRMED"
    NON_DISTINCT_NOOP = "NON_DISTINCT_NOOP"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"
    EPOCH_GAP = "EPOCH_GAP"
    EPOCH_REGRESSION = "EPOCH_REGRESSION"
    SESSION_MISMATCH = "SESSION_MISMATCH"
    INSTRUMENT_MISMATCH = "INSTRUMENT_MISMATCH"
    VENUE_MISMATCH = "VENUE_MISMATCH"
    SIDE_MISMATCH = "SIDE_MISMATCH"
    STATE_INCONSISTENT = "STATE_INCONSISTENT"
    RUNTIME_CYCLE_NOT_OBSERVATION = "RUNTIME_CYCLE_NOT_OBSERVATION"
    RECEIVE_TIME_NOT_EPOCH = "RECEIVE_TIME_NOT_EPOCH"
    DECISION_EPOCH_FORBIDDEN = "DECISION_EPOCH_FORBIDDEN"
    INVALID_THRESHOLD = "INVALID_THRESHOLD"
    INVALID_SIGNAL = "INVALID_SIGNAL"


def _require_non_empty_str(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"INVALID_CONFIRMATION_PROGRESS_FIELD:{name}")
    return value.strip()


def _require_non_negative_epoch(epoch: MarketObservationEpoch) -> MarketObservationEpoch:
    # MarketObservationEpoch already enforces value >= 0.
    if not isinstance(epoch, MarketObservationEpoch):
        raise ValueError("INVALID_CONFIRMATION_PROGRESS_FIELD:market_observation_epoch")
    return epoch


def _validate_confirmation_progress_state_invariants_v1(
    state: "ConfirmationProgressStateV1",
) -> Optional[str]:
    """Return a machine reason if invariants fail; None if valid."""
    if state.assessment_state == ConfirmationAssessmentStateV1.INVALID:
        return "assessment_state_invalid"
    if state.distinct_confirmation_observation_count < 0:
        return "count_negative"
    if state.assessment_state == ConfirmationAssessmentStateV1.OBSERVE:
        if state.distinct_confirmation_observation_count != 0:
            return "observe_count_nonzero"
        if state.candidate_started_at_epoch is not None:
            return "observe_candidate_started_set"
    if state.assessment_state == ConfirmationAssessmentStateV1.CANDIDATE:
        if state.distinct_confirmation_observation_count < 1:
            return "candidate_count_lt_1"
        if state.candidate_started_at_epoch is None:
            return "candidate_started_missing"
    if state.assessment_state == ConfirmationAssessmentStateV1.CONFIRMED:
        if state.distinct_confirmation_observation_count < 1:
            return "confirmed_count_lt_1"
        if state.candidate_started_at_epoch is None:
            return "confirmed_candidate_started_missing"
    return None


@dataclass(frozen=True)
class ConfirmationProgressStateV1:
    """Session-bound confirmation progress cursor (mechanism-only)."""

    session_id: str
    venue: str
    instrument: InstrumentObservationKeyV1
    side: ConfirmationSideV1
    assessment_state: ConfirmationAssessmentStateV1
    latest_accepted_market_observation_epoch: MarketObservationEpoch
    candidate_started_at_epoch: Optional[MarketObservationEpoch]
    distinct_confirmation_observation_count: int
    last_processed_acceptor_result_fingerprint: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "session_id", _require_non_empty_str("session_id", self.session_id)
        )
        object.__setattr__(self, "venue", _require_non_empty_str("venue", self.venue))
        if not isinstance(self.instrument, InstrumentObservationKeyV1):
            raise ValueError("INVALID_CONFIRMATION_PROGRESS_FIELD:instrument")
        if self.venue != self.instrument.venue:
            raise ValueError("INVALID_CONFIRMATION_PROGRESS_FIELD:venue_instrument_mismatch")
        if not isinstance(self.side, ConfirmationSideV1):
            raise ValueError("INVALID_CONFIRMATION_PROGRESS_FIELD:side")
        if not isinstance(self.assessment_state, ConfirmationAssessmentStateV1):
            raise ValueError("INVALID_CONFIRMATION_PROGRESS_FIELD:assessment_state")
        _require_non_negative_epoch(self.latest_accepted_market_observation_epoch)
        if self.candidate_started_at_epoch is not None:
            _require_non_negative_epoch(self.candidate_started_at_epoch)
        if isinstance(self.distinct_confirmation_observation_count, bool) or not isinstance(
            self.distinct_confirmation_observation_count, int
        ):
            raise ValueError("INVALID_CONFIRMATION_PROGRESS_FIELD:count")
        if self.distinct_confirmation_observation_count < 0:
            raise ValueError("INVALID_CONFIRMATION_PROGRESS_FIELD:count_negative")
        if self.last_processed_acceptor_result_fingerprint is not None and (
            not isinstance(self.last_processed_acceptor_result_fingerprint, str)
            or not self.last_processed_acceptor_result_fingerprint.strip()
        ):
            raise ValueError("INVALID_CONFIRMATION_PROGRESS_FIELD:fingerprint")

        # INVALID is constructible only for explicit fail-closed paths; invariants
        # for OBSERVE/CANDIDATE/CONFIRMED are enforced here. INVALID skips them
        # so callers can never treat it as a silent valid progress state.
        if self.assessment_state != ConfirmationAssessmentStateV1.INVALID:
            fault = _validate_confirmation_progress_state_invariants_v1(self)
            if fault is not None:
                raise ValueError(f"INVALID_CONFIRMATION_PROGRESS_STATE:{fault}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": CONFIRMATION_PROGRESS_STATE_VERSION,
            "session_id": self.session_id,
            "venue": self.venue,
            "instrument": self.instrument.to_dict(),
            "side": self.side.value,
            "assessment_state": self.assessment_state.value,
            "latest_accepted_market_observation_epoch": (
                self.latest_accepted_market_observation_epoch.to_dict()
            ),
            "candidate_started_at_epoch": (
                None
                if self.candidate_started_at_epoch is None
                else self.candidate_started_at_epoch.to_dict()
            ),
            "distinct_confirmation_observation_count": (
                self.distinct_confirmation_observation_count
            ),
            "last_processed_acceptor_result_fingerprint": (
                self.last_processed_acceptor_result_fingerprint
            ),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ConfirmationProgressStateV1":
        version = str(payload.get("version", CONFIRMATION_PROGRESS_STATE_VERSION))
        if version != CONFIRMATION_PROGRESS_STATE_VERSION:
            raise ValueError(f"UNSUPPORTED_CONFIRMATION_PROGRESS_STATE_VERSION:{version}")
        candidate_payload = payload.get("candidate_started_at_epoch")
        return cls(
            session_id=str(payload["session_id"]),
            venue=str(payload["venue"]),
            instrument=InstrumentObservationKeyV1.from_dict(payload["instrument"]),
            side=ConfirmationSideV1(str(payload["side"])),
            assessment_state=ConfirmationAssessmentStateV1(str(payload["assessment_state"])),
            latest_accepted_market_observation_epoch=MarketObservationEpoch.from_dict(
                payload["latest_accepted_market_observation_epoch"]
            ),
            candidate_started_at_epoch=(
                None
                if candidate_payload is None
                else MarketObservationEpoch.from_dict(candidate_payload)
            ),
            distinct_confirmation_observation_count=int(
                payload["distinct_confirmation_observation_count"]
            ),
            last_processed_acceptor_result_fingerprint=payload.get(
                "last_processed_acceptor_result_fingerprint"
            ),
        )


@dataclass(frozen=True)
class ConfirmationProgressInputV1:
    """Pure evaluator input. No clocks, configs, or runtime wiring."""

    prior_state: ConfirmationProgressStateV1
    observation_acceptance_result: ObservationAcceptanceResultV1
    session_id: str
    venue: str
    instrument: InstrumentObservationKeyV1
    side: ConfirmationSideV1
    assessment_signal: ConfirmationAssessmentSignalV1
    confirmation_threshold: int
    acceptor_result_fingerprint: Optional[str] = None


@dataclass(frozen=True)
class ConfirmationProgressResultV1:
    accepted: bool
    state_before: ConfirmationProgressStateV1
    state_after: ConfirmationProgressStateV1
    reason_code: ConfirmationProgressReasonCodeV1
    state_changed: bool
    confirmation_advanced: bool
    fail_closed: bool
    observation_epoch_before: MarketObservationEpoch
    observation_epoch_after: MarketObservationEpoch
    deterministic_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "state_before": self.state_before.to_dict(),
            "state_after": self.state_after.to_dict(),
            "reason_code": self.reason_code.value,
            "state_changed": self.state_changed,
            "confirmation_advanced": self.confirmation_advanced,
            "fail_closed": self.fail_closed,
            "observation_epoch_before": self.observation_epoch_before.to_dict(),
            "observation_epoch_after": self.observation_epoch_after.to_dict(),
            "deterministic_fingerprint": self.deterministic_fingerprint,
        }


def confirmation_progress_fingerprint_v1(
    observation_acceptance_result: ObservationAcceptanceResultV1,
    *,
    explicit_fingerprint: Optional[str] = None,
) -> str:
    """Stable fingerprint of a C1 acceptor result for idempotent replay detection."""
    if explicit_fingerprint is not None:
        if not isinstance(explicit_fingerprint, str) or not explicit_fingerprint.strip():
            raise ValueError("INVALID_CONFIRMATION_PROGRESS_FIELD:explicit_fingerprint")
        return explicit_fingerprint.strip()
    payload = json.dumps(
        observation_acceptance_result.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _result_fingerprint(payload: Mapping[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def initial_confirmation_progress_state_v1(
    *,
    session_id: str,
    venue: str,
    instrument: InstrumentObservationKeyV1,
    side: ConfirmationSideV1,
    initial_market_observation_epoch: Optional[MarketObservationEpoch] = None,
) -> ConfirmationProgressStateV1:
    """Create a session-bound empty OBSERVE state.

    Epoch start defaults to MarketObservationEpoch(0), matching the C1 initial
    acceptance cursor. Callers may pass an explicit C1-aligned epoch; C2 never
    invents a DecisionEpoch or RuntimeCycle cursor.
    """
    epoch = (
        MarketObservationEpoch(value=0)
        if initial_market_observation_epoch is None
        else initial_market_observation_epoch
    )
    if venue != instrument.venue:
        raise ValueError("INVALID_CONFIRMATION_PROGRESS_FIELD:venue_instrument_mismatch")
    return ConfirmationProgressStateV1(
        session_id=session_id,
        venue=venue,
        instrument=instrument,
        side=side,
        assessment_state=ConfirmationAssessmentStateV1.OBSERVE,
        latest_accepted_market_observation_epoch=epoch,
        candidate_started_at_epoch=None,
        distinct_confirmation_observation_count=0,
        last_processed_acceptor_result_fingerprint=None,
    )


def _unchanged_result(
    *,
    prior: ConfirmationProgressStateV1,
    reason: ConfirmationProgressReasonCodeV1,
    accepted: bool,
    fail_closed: bool,
) -> ConfirmationProgressResultV1:
    epoch = prior.latest_accepted_market_observation_epoch
    provisional = {
        "accepted": accepted,
        "state_before": prior.to_dict(),
        "state_after": prior.to_dict(),
        "reason_code": reason.value,
        "state_changed": False,
        "confirmation_advanced": False,
        "fail_closed": fail_closed,
        "observation_epoch_before": epoch.to_dict(),
        "observation_epoch_after": epoch.to_dict(),
    }
    fingerprint = _result_fingerprint(provisional)
    return ConfirmationProgressResultV1(
        accepted=accepted,
        state_before=prior,
        state_after=prior,
        reason_code=reason,
        state_changed=False,
        confirmation_advanced=False,
        fail_closed=fail_closed,
        observation_epoch_before=epoch,
        observation_epoch_after=epoch,
        deterministic_fingerprint=fingerprint,
    )


def _success_result(
    *,
    prior: ConfirmationProgressStateV1,
    after: ConfirmationProgressStateV1,
    reason: ConfirmationProgressReasonCodeV1,
    confirmation_advanced: bool,
) -> ConfirmationProgressResultV1:
    provisional = {
        "accepted": True,
        "state_before": prior.to_dict(),
        "state_after": after.to_dict(),
        "reason_code": reason.value,
        "state_changed": after != prior,
        "confirmation_advanced": confirmation_advanced,
        "fail_closed": False,
        "observation_epoch_before": prior.latest_accepted_market_observation_epoch.to_dict(),
        "observation_epoch_after": after.latest_accepted_market_observation_epoch.to_dict(),
    }
    fingerprint = _result_fingerprint(provisional)
    return ConfirmationProgressResultV1(
        accepted=True,
        state_before=prior,
        state_after=after,
        reason_code=reason,
        state_changed=after != prior,
        confirmation_advanced=confirmation_advanced,
        fail_closed=False,
        observation_epoch_before=prior.latest_accepted_market_observation_epoch,
        observation_epoch_after=after.latest_accepted_market_observation_epoch,
        deterministic_fingerprint=fingerprint,
    )


def reject_runtime_cycle_confirmation_advance_v1(
    prior_state: ConfirmationProgressStateV1,
) -> ConfirmationProgressResultV1:
    """Fail-closed: RuntimeCycleIndex is not a confirmation-advance epoch."""
    return _unchanged_result(
        prior=prior_state,
        reason=ConfirmationProgressReasonCodeV1.RUNTIME_CYCLE_NOT_OBSERVATION,
        accepted=False,
        fail_closed=True,
    )


def reject_receive_time_confirmation_advance_v1(
    prior_state: ConfirmationProgressStateV1,
) -> ConfirmationProgressResultV1:
    """Fail-closed: receive time is not a confirmation-advance epoch."""
    return _unchanged_result(
        prior=prior_state,
        reason=ConfirmationProgressReasonCodeV1.RECEIVE_TIME_NOT_EPOCH,
        accepted=False,
        fail_closed=True,
    )


def reject_decision_epoch_confirmation_advance_v1(
    prior_state: ConfirmationProgressStateV1,
) -> ConfirmationProgressResultV1:
    """Fail-closed: DecisionEpoch has no C2 confirmation-advance authority."""
    return _unchanged_result(
        prior=prior_state,
        reason=ConfirmationProgressReasonCodeV1.DECISION_EPOCH_FORBIDDEN,
        accepted=False,
        fail_closed=True,
    )


def _apply_transition(
    *,
    prior: ConfirmationProgressStateV1,
    current_epoch: MarketObservationEpoch,
    signal: ConfirmationAssessmentSignalV1,
    threshold: int,
    fingerprint: str,
) -> tuple[ConfirmationProgressStateV1, ConfirmationProgressReasonCodeV1, bool]:
    """Return (state_after, reason, confirmation_advanced)."""
    base_kwargs = {
        "session_id": prior.session_id,
        "venue": prior.venue,
        "instrument": prior.instrument,
        "side": prior.side,
        "latest_accepted_market_observation_epoch": current_epoch,
        "last_processed_acceptor_result_fingerprint": fingerprint,
    }

    state = prior.assessment_state

    if state == ConfirmationAssessmentStateV1.OBSERVE:
        if signal == ConfirmationAssessmentSignalV1.OBSERVE:
            after = ConfirmationProgressStateV1(
                **base_kwargs,
                assessment_state=ConfirmationAssessmentStateV1.OBSERVE,
                candidate_started_at_epoch=None,
                distinct_confirmation_observation_count=0,
            )
            return after, ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_PROGRESS, False

        if signal == ConfirmationAssessmentSignalV1.CANDIDATE:
            after = ConfirmationProgressStateV1(
                **base_kwargs,
                assessment_state=ConfirmationAssessmentStateV1.CANDIDATE,
                candidate_started_at_epoch=current_epoch,
                distinct_confirmation_observation_count=1,
            )
            return after, ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_PROGRESS, True

        # OBSERVE + CONFIRMED
        if threshold <= 1:
            after = ConfirmationProgressStateV1(
                **base_kwargs,
                assessment_state=ConfirmationAssessmentStateV1.CONFIRMED,
                candidate_started_at_epoch=current_epoch,
                distinct_confirmation_observation_count=1,
            )
            return after, ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_CONFIRMED, True
        after = ConfirmationProgressStateV1(
            **base_kwargs,
            assessment_state=ConfirmationAssessmentStateV1.CANDIDATE,
            candidate_started_at_epoch=current_epoch,
            distinct_confirmation_observation_count=1,
        )
        return after, ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_PROGRESS, True

    if state == ConfirmationAssessmentStateV1.CANDIDATE:
        if signal == ConfirmationAssessmentSignalV1.OBSERVE:
            after = ConfirmationProgressStateV1(
                **base_kwargs,
                assessment_state=ConfirmationAssessmentStateV1.OBSERVE,
                candidate_started_at_epoch=None,
                distinct_confirmation_observation_count=0,
            )
            return after, ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_RESET, False

        # CANDIDATE + CANDIDATE/CONFIRMED share one rule: count+1, confirm at threshold.
        count_after = prior.distinct_confirmation_observation_count + 1
        if count_after >= threshold:
            after = ConfirmationProgressStateV1(
                **base_kwargs,
                assessment_state=ConfirmationAssessmentStateV1.CONFIRMED,
                candidate_started_at_epoch=prior.candidate_started_at_epoch,
                distinct_confirmation_observation_count=count_after,
            )
            return after, ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_CONFIRMED, True
        after = ConfirmationProgressStateV1(
            **base_kwargs,
            assessment_state=ConfirmationAssessmentStateV1.CANDIDATE,
            candidate_started_at_epoch=prior.candidate_started_at_epoch,
            distinct_confirmation_observation_count=count_after,
        )
        return after, ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_PROGRESS, True

    if state == ConfirmationAssessmentStateV1.CONFIRMED:
        if signal == ConfirmationAssessmentSignalV1.OBSERVE:
            after = ConfirmationProgressStateV1(
                **base_kwargs,
                assessment_state=ConfirmationAssessmentStateV1.OBSERVE,
                candidate_started_at_epoch=None,
                distinct_confirmation_observation_count=0,
            )
            return after, ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_RESET, False

        # CONFIRMED + CONFIRMED/CANDIDATE: hold CONFIRMED, count stays stable.
        after = ConfirmationProgressStateV1(
            **base_kwargs,
            assessment_state=ConfirmationAssessmentStateV1.CONFIRMED,
            candidate_started_at_epoch=prior.candidate_started_at_epoch,
            distinct_confirmation_observation_count=prior.distinct_confirmation_observation_count,
        )
        return after, ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_HOLD_CONFIRMED, False

    # INVALID or unknown — should be caught earlier.
    raise ValueError("INVALID_CONFIRMATION_PROGRESS_STATE:unhandled_assessment_state")


def evaluate_confirmation_progress_v1(
    progress_input: ConfirmationProgressInputV1,
) -> ConfirmationProgressResultV1:
    """Pure confirmation-progress evaluator. No mutation, I/O, or clocks."""
    prior = progress_input.prior_state

    invariant_fault = _validate_confirmation_progress_state_invariants_v1(prior)
    if invariant_fault is not None:
        return _unchanged_result(
            prior=prior,
            reason=ConfirmationProgressReasonCodeV1.STATE_INCONSISTENT,
            accepted=False,
            fail_closed=True,
        )

    if progress_input.session_id != prior.session_id:
        return _unchanged_result(
            prior=prior,
            reason=ConfirmationProgressReasonCodeV1.SESSION_MISMATCH,
            accepted=False,
            fail_closed=True,
        )
    if progress_input.venue != prior.venue:
        return _unchanged_result(
            prior=prior,
            reason=ConfirmationProgressReasonCodeV1.VENUE_MISMATCH,
            accepted=False,
            fail_closed=True,
        )
    if progress_input.instrument != prior.instrument:
        return _unchanged_result(
            prior=prior,
            reason=ConfirmationProgressReasonCodeV1.INSTRUMENT_MISMATCH,
            accepted=False,
            fail_closed=True,
        )
    if progress_input.side != prior.side:
        return _unchanged_result(
            prior=prior,
            reason=ConfirmationProgressReasonCodeV1.SIDE_MISMATCH,
            accepted=False,
            fail_closed=True,
        )

    threshold = progress_input.confirmation_threshold
    if isinstance(threshold, bool) or not isinstance(threshold, int) or threshold < 1:
        return _unchanged_result(
            prior=prior,
            reason=ConfirmationProgressReasonCodeV1.INVALID_THRESHOLD,
            accepted=False,
            fail_closed=True,
        )

    if not isinstance(progress_input.assessment_signal, ConfirmationAssessmentSignalV1):
        return _unchanged_result(
            prior=prior,
            reason=ConfirmationProgressReasonCodeV1.INVALID_SIGNAL,
            accepted=False,
            fail_closed=True,
        )

    acceptor = progress_input.observation_acceptance_result
    fingerprint = confirmation_progress_fingerprint_v1(
        acceptor,
        explicit_fingerprint=progress_input.acceptor_result_fingerprint,
    )

    if (
        prior.last_processed_acceptor_result_fingerprint is not None
        and fingerprint == prior.last_processed_acceptor_result_fingerprint
    ):
        return _unchanged_result(
            prior=prior,
            reason=ConfirmationProgressReasonCodeV1.IDEMPOTENT_REPLAY,
            accepted=True,
            fail_closed=False,
        )

    is_distinct_advance = (
        acceptor.classification == ObservationClassification.DISTINCT
        and acceptor.strategy_advance_allowed is True
    )
    if not is_distinct_advance:
        return _unchanged_result(
            prior=prior,
            reason=ConfirmationProgressReasonCodeV1.NON_DISTINCT_NOOP,
            accepted=False,
            fail_closed=False,
        )

    current_epoch = acceptor.state_after.market_observation_epoch
    prior_epoch = prior.latest_accepted_market_observation_epoch
    delta = current_epoch.value - prior_epoch.value

    if delta == 0:
        # Same epoch without matching fingerprint already handled above when
        # fingerprints match. A same-epoch distinct claim without fingerprint
        # match is treated as regression/conflict.
        return _unchanged_result(
            prior=prior,
            reason=ConfirmationProgressReasonCodeV1.EPOCH_REGRESSION,
            accepted=False,
            fail_closed=True,
        )
    if delta < 0:
        return _unchanged_result(
            prior=prior,
            reason=ConfirmationProgressReasonCodeV1.EPOCH_REGRESSION,
            accepted=False,
            fail_closed=True,
        )
    if delta > 1:
        return _unchanged_result(
            prior=prior,
            reason=ConfirmationProgressReasonCodeV1.EPOCH_GAP,
            accepted=False,
            fail_closed=True,
        )

    # delta == 1 — contiguous accepted-distinct MarketObservationEpoch step
    after, reason, confirmation_advanced = _apply_transition(
        prior=prior,
        current_epoch=current_epoch,
        signal=progress_input.assessment_signal,
        threshold=threshold,
        fingerprint=fingerprint,
    )
    return _success_result(
        prior=prior,
        after=after,
        reason=reason,
        confirmation_advanced=confirmation_advanced,
    )
