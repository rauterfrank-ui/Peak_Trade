"""DistinctMarketObservationAcceptorV1 — pure deterministic C1 evaluator.

PURE_DETERMINISTIC_NO_IO=true
EVALUATOR_MUTATES_EXTERNAL_STATE=false
CALLER_COMMIT_REQUIRED=true
NO_SESSION_RUNTIME_HOT_PATH_WIRING=true
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional, Tuple

from trading.market_state.observation_identity_v1 import (
    InstrumentObservationKeyV1,
    MarketObservationEpoch,
    ObservationIdentityV1,
    is_finite_number,
)

OBSERVATION_ACCEPTOR_COMPONENT = "DistinctMarketObservationAcceptorV1"
OBSERVATION_ACCEPTOR_PURITY = "PURE_DETERMINISTIC_NO_IO"

# Classification priority (first match wins after input validation):
# 1 INVALID_EVENT_TIME
# 2 INVALID_MARK
# 3 IDENTITY_CONFLICT
# 4 OUT_OF_ORDER
# 5 TRANSPORT_ONLY_DUPLICATE
# 6 DUPLICATE
# 7 DISTINCT


class ObservationClassification(str, Enum):
    DISTINCT = "distinct"
    DUPLICATE = "duplicate"
    OUT_OF_ORDER = "out_of_order"
    IDENTITY_CONFLICT = "identity_conflict"
    INVALID_EVENT_TIME = "invalid_event_time"
    INVALID_MARK = "invalid_mark"
    TRANSPORT_ONLY_DUPLICATE = "transport_only_duplicate"


class ObservationReasonCode(str, Enum):
    ACCEPTED_DISTINCT = "observation_accepted_distinct"
    ACCEPTED_DISTINCT_INITIAL = "observation_accepted_distinct_initial"
    DUPLICATE = "observation_duplicate"
    TRANSPORT_ONLY_DUPLICATE = "observation_transport_only_duplicate"
    OUT_OF_ORDER = "observation_out_of_order"
    IDENTITY_CONFLICT_VENUE = "observation_identity_conflict_venue"
    IDENTITY_CONFLICT_INSTRUMENT = "observation_identity_conflict_instrument"
    IDENTITY_CONFLICT_CANONICAL_MAPPING = "observation_identity_conflict_canonical_mapping"
    IDENTITY_CONFLICT_MARK = "observation_identity_conflict_mark"
    INVALID_EVENT_TIME_MISSING = "observation_invalid_event_time_missing"
    INVALID_EVENT_TIME_NON_FINITE = "observation_invalid_event_time_non_finite"
    INVALID_EVENT_TIME_NON_POSITIVE = "observation_invalid_event_time_non_positive"
    INVALID_MARK_MISSING = "observation_invalid_mark_missing"
    INVALID_MARK_NON_FINITE = "observation_invalid_mark_non_finite"
    INVALID_MARK_NON_POSITIVE = "observation_invalid_mark_non_positive"
    INVALID_IDENTITY_FIELD = "observation_invalid_identity_field"
    COMMIT_COMPARE_MISMATCH = "observation_accept_commit_compare_mismatch"
    COMMIT_PARTIAL_REJECTED = "observation_accept_commit_partial_rejected"
    COMMIT_NON_DISTINCT_NOOP = "observation_accept_commit_non_distinct_noop"


@dataclass(frozen=True)
class ObservationTransportMetadataV1:
    """Transport/poll metadata. Never distinctness authority."""

    receive_time: Optional[float] = None
    poll_attempt: Optional[int] = None
    runtime_cycle_index: Optional[int] = None
    heartbeat_sequence: Optional[int] = None
    transport_latency: Optional[float] = None
    wallclock_now: Optional[float] = None

    def fingerprint(self) -> Tuple[object, ...]:
        return (
            self.receive_time,
            self.poll_attempt,
            self.runtime_cycle_index,
            self.heartbeat_sequence,
            self.transport_latency,
            self.wallclock_now,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "receive_time": self.receive_time,
            "poll_attempt": self.poll_attempt,
            "runtime_cycle_index": self.runtime_cycle_index,
            "heartbeat_sequence": self.heartbeat_sequence,
            "transport_latency": self.transport_latency,
            "wallclock_now": self.wallclock_now,
        }

    @classmethod
    def from_dict(
        cls, payload: Optional[Mapping[str, Any]]
    ) -> Optional["ObservationTransportMetadataV1"]:
        if payload is None:
            return None
        return cls(
            receive_time=payload.get("receive_time"),
            poll_attempt=payload.get("poll_attempt"),
            runtime_cycle_index=payload.get("runtime_cycle_index"),
            heartbeat_sequence=payload.get("heartbeat_sequence"),
            transport_latency=payload.get("transport_latency"),
            wallclock_now=payload.get("wallclock_now"),
        )


@dataclass(frozen=True)
class ObservationCandidateV1:
    """Evaluator input. Invalid numeric fields are classified, not silently defaulted."""

    venue: Optional[str]
    canonical_instrument_id: Optional[str]
    venue_instrument_id: Optional[str]
    venue_event_time: Optional[float]
    mark_price: Optional[float]
    transport: Optional[ObservationTransportMetadataV1] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "venue": self.venue,
            "canonical_instrument_id": self.canonical_instrument_id,
            "venue_instrument_id": self.venue_instrument_id,
            "venue_event_time": self.venue_event_time,
            "mark_price": self.mark_price,
            "transport": None if self.transport is None else self.transport.to_dict(),
        }


@dataclass(frozen=True)
class ObservationAcceptanceStateV1:
    """Immutable instrument-bound acceptance state.

    Ownership group (atomic commit):
      last_accepted_observation_identity + market_observation_epoch
    """

    last_accepted_observation_identity: Optional[ObservationIdentityV1]
    market_observation_epoch: MarketObservationEpoch
    bound_instrument_key: Optional[InstrumentObservationKeyV1] = None
    last_accepted_transport: Optional[ObservationTransportMetadataV1] = None

    def __post_init__(self) -> None:
        if self.last_accepted_observation_identity is not None:
            identity_key = self.last_accepted_observation_identity.instrument_key()
            if self.bound_instrument_key is None:
                object.__setattr__(self, "bound_instrument_key", identity_key)
            elif self.bound_instrument_key != identity_key:
                raise ValueError("STATE_BOUND_INSTRUMENT_KEY_MISMATCH")

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_accepted_observation_identity": (
                None
                if self.last_accepted_observation_identity is None
                else self.last_accepted_observation_identity.to_dict()
            ),
            "market_observation_epoch": self.market_observation_epoch.to_dict(),
            "bound_instrument_key": (
                None if self.bound_instrument_key is None else self.bound_instrument_key.to_dict()
            ),
            "last_accepted_transport": (
                None
                if self.last_accepted_transport is None
                else self.last_accepted_transport.to_dict()
            ),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ObservationAcceptanceStateV1":
        identity_payload = payload.get("last_accepted_observation_identity")
        key_payload = payload.get("bound_instrument_key")
        return cls(
            last_accepted_observation_identity=(
                None
                if identity_payload is None
                else ObservationIdentityV1.from_dict(identity_payload)
            ),
            market_observation_epoch=MarketObservationEpoch.from_dict(
                payload["market_observation_epoch"]
            ),
            bound_instrument_key=(
                None if key_payload is None else InstrumentObservationKeyV1.from_dict(key_payload)
            ),
            last_accepted_transport=ObservationTransportMetadataV1.from_dict(
                payload.get("last_accepted_transport")
            ),
        )


def initial_observation_acceptance_state_v1(
    *,
    bound_instrument_key: Optional[InstrumentObservationKeyV1] = None,
) -> ObservationAcceptanceStateV1:
    return ObservationAcceptanceStateV1(
        last_accepted_observation_identity=None,
        market_observation_epoch=MarketObservationEpoch(value=0),
        bound_instrument_key=bound_instrument_key,
        last_accepted_transport=None,
    )


@dataclass(frozen=True)
class ObservationAcceptanceResultV1:
    classification: ObservationClassification
    strategy_advance_allowed: bool
    state_before: ObservationAcceptanceStateV1
    state_after: ObservationAcceptanceStateV1
    observation_identity: Optional[ObservationIdentityV1]
    reason_code: str

    @property
    def fail_closed(self) -> bool:
        return self.classification in {
            ObservationClassification.OUT_OF_ORDER,
            ObservationClassification.IDENTITY_CONFLICT,
            ObservationClassification.INVALID_EVENT_TIME,
            ObservationClassification.INVALID_MARK,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification.value,
            "strategy_advance_allowed": self.strategy_advance_allowed,
            "state_before": self.state_before.to_dict(),
            "state_after": self.state_after.to_dict(),
            "observation_identity": (
                None if self.observation_identity is None else self.observation_identity.to_dict()
            ),
            "reason_code": self.reason_code,
            "fail_closed": self.fail_closed,
        }


def _reject(
    *,
    state: ObservationAcceptanceStateV1,
    classification: ObservationClassification,
    reason_code: ObservationReasonCode,
    identity: Optional[ObservationIdentityV1] = None,
) -> ObservationAcceptanceResultV1:
    return ObservationAcceptanceResultV1(
        classification=classification,
        strategy_advance_allowed=False,
        state_before=state,
        state_after=state,
        observation_identity=identity,
        reason_code=reason_code.value,
    )


def _validate_event_time(
    raw: Optional[float],
) -> Optional[ObservationReasonCode]:
    if raw is None:
        return ObservationReasonCode.INVALID_EVENT_TIME_MISSING
    if not is_finite_number(raw):
        return ObservationReasonCode.INVALID_EVENT_TIME_NON_FINITE
    if float(raw) <= 0.0:
        return ObservationReasonCode.INVALID_EVENT_TIME_NON_POSITIVE
    return None


def _validate_mark(raw: Optional[float]) -> Optional[ObservationReasonCode]:
    if raw is None:
        return ObservationReasonCode.INVALID_MARK_MISSING
    if not is_finite_number(raw):
        return ObservationReasonCode.INVALID_MARK_NON_FINITE
    if float(raw) <= 0.0:
        return ObservationReasonCode.INVALID_MARK_NON_POSITIVE
    return None


def _try_build_identity(
    candidate: ObservationCandidateV1,
) -> Tuple[Optional[ObservationIdentityV1], Optional[ObservationReasonCode]]:
    try:
        if (
            candidate.venue is None
            or candidate.canonical_instrument_id is None
            or candidate.venue_instrument_id is None
        ):
            return None, ObservationReasonCode.INVALID_IDENTITY_FIELD
        identity = ObservationIdentityV1(
            venue=candidate.venue,
            canonical_instrument_id=candidate.canonical_instrument_id,
            venue_instrument_id=candidate.venue_instrument_id,
            venue_event_time=float(candidate.venue_event_time),  # type: ignore[arg-type]
            mark_price=float(candidate.mark_price),  # type: ignore[arg-type]
        )
        return identity, None
    except (TypeError, ValueError):
        return None, ObservationReasonCode.INVALID_IDENTITY_FIELD


def _instrument_conflict_reason(
    bound: InstrumentObservationKeyV1,
    incoming: InstrumentObservationKeyV1,
) -> Optional[ObservationReasonCode]:
    if bound.venue != incoming.venue:
        return ObservationReasonCode.IDENTITY_CONFLICT_VENUE
    if bound.venue_instrument_id != incoming.venue_instrument_id:
        return ObservationReasonCode.IDENTITY_CONFLICT_INSTRUMENT
    if bound.canonical_instrument_id != incoming.canonical_instrument_id:
        return ObservationReasonCode.IDENTITY_CONFLICT_CANONICAL_MAPPING
    return None


def evaluate_distinct_market_observation_v1(
    state: ObservationAcceptanceStateV1,
    candidate: ObservationCandidateV1,
) -> ObservationAcceptanceResultV1:
    """Pure evaluator: returns next state; does not persist.

    Receive time / wallclock / runtime cycle never substitute venue event time
    and never create a DISTINCT advance by themselves.
    """
    event_reason = _validate_event_time(candidate.venue_event_time)
    if event_reason is not None:
        return _reject(
            state=state,
            classification=ObservationClassification.INVALID_EVENT_TIME,
            reason_code=event_reason,
        )

    mark_reason = _validate_mark(candidate.mark_price)
    if mark_reason is not None:
        return _reject(
            state=state,
            classification=ObservationClassification.INVALID_MARK,
            reason_code=mark_reason,
        )

    identity, identity_reason = _try_build_identity(candidate)
    if identity is None:
        return _reject(
            state=state,
            classification=ObservationClassification.IDENTITY_CONFLICT,
            reason_code=identity_reason or ObservationReasonCode.INVALID_IDENTITY_FIELD,
        )

    incoming_key = identity.instrument_key()
    bound = state.bound_instrument_key
    if bound is not None:
        conflict = _instrument_conflict_reason(bound, incoming_key)
        if conflict is not None:
            return _reject(
                state=state,
                classification=ObservationClassification.IDENTITY_CONFLICT,
                reason_code=conflict,
                identity=identity,
            )

    last = state.last_accepted_observation_identity
    if last is not None:
        last_key = last.instrument_key()
        conflict = _instrument_conflict_reason(last_key, incoming_key)
        if conflict is not None:
            return _reject(
                state=state,
                classification=ObservationClassification.IDENTITY_CONFLICT,
                reason_code=conflict,
                identity=identity,
            )

        if (
            identity.event_identity_key() == last.event_identity_key()
            and identity.mark_price != last.mark_price
        ):
            return _reject(
                state=state,
                classification=ObservationClassification.IDENTITY_CONFLICT,
                reason_code=ObservationReasonCode.IDENTITY_CONFLICT_MARK,
                identity=identity,
            )

        if identity.venue_event_time < last.venue_event_time:
            return _reject(
                state=state,
                classification=ObservationClassification.OUT_OF_ORDER,
                reason_code=ObservationReasonCode.OUT_OF_ORDER,
                identity=identity,
            )

        if identity.distinctness_key() == last.distinctness_key():
            prev_transport = state.last_accepted_transport
            curr_transport = candidate.transport
            if (
                prev_transport is not None
                and curr_transport is not None
                and prev_transport.fingerprint() != curr_transport.fingerprint()
            ):
                return _reject(
                    state=state,
                    classification=ObservationClassification.TRANSPORT_ONLY_DUPLICATE,
                    reason_code=ObservationReasonCode.TRANSPORT_ONLY_DUPLICATE,
                    identity=identity,
                )
            return _reject(
                state=state,
                classification=ObservationClassification.DUPLICATE,
                reason_code=ObservationReasonCode.DUPLICATE,
                identity=identity,
            )

    reason = (
        ObservationReasonCode.ACCEPTED_DISTINCT_INITIAL
        if last is None
        else ObservationReasonCode.ACCEPTED_DISTINCT
    )
    state_after = ObservationAcceptanceStateV1(
        last_accepted_observation_identity=identity,
        market_observation_epoch=state.market_observation_epoch.advanced_by_one(),
        bound_instrument_key=incoming_key,
        last_accepted_transport=candidate.transport,
    )
    return ObservationAcceptanceResultV1(
        classification=ObservationClassification.DISTINCT,
        strategy_advance_allowed=True,
        state_before=state,
        state_after=state_after,
        observation_identity=identity,
        reason_code=reason.value,
    )


def commit_observation_acceptance_v1(
    *,
    current_state: ObservationAcceptanceStateV1,
    result: ObservationAcceptanceResultV1,
) -> ObservationAcceptanceStateV1:
    """Atomic C1 commit helper (compare-before/after). No runtime integration.

    OBSERVATION_ACCEPT_COMMIT_GROUP =
      last_accepted_observation_identity + market_observation_epoch
    PARTIAL_COMMIT_ALLOWED=false
    """
    if result.state_before != current_state:
        raise ValueError(ObservationReasonCode.COMMIT_COMPARE_MISMATCH.value)

    if result.classification != ObservationClassification.DISTINCT:
        if result.state_after != result.state_before:
            raise ValueError(ObservationReasonCode.COMMIT_PARTIAL_REJECTED.value)
        return current_state

    before = result.state_before
    after = result.state_after
    epoch_delta = after.market_observation_epoch.value - before.market_observation_epoch.value
    if epoch_delta != 1:
        raise ValueError(ObservationReasonCode.COMMIT_PARTIAL_REJECTED.value)
    if after.last_accepted_observation_identity is None:
        raise ValueError(ObservationReasonCode.COMMIT_PARTIAL_REJECTED.value)
    if before.last_accepted_observation_identity is after.last_accepted_observation_identity:
        raise ValueError(ObservationReasonCode.COMMIT_PARTIAL_REJECTED.value)
    return after


class DistinctMarketObservationAcceptorV1:
    """Stateless facade over the pure evaluator + optional commit helper."""

    COMPONENT = OBSERVATION_ACCEPTOR_COMPONENT
    PURITY = OBSERVATION_ACCEPTOR_PURITY

    @staticmethod
    def initial_state(
        *,
        bound_instrument_key: Optional[InstrumentObservationKeyV1] = None,
    ) -> ObservationAcceptanceStateV1:
        return initial_observation_acceptance_state_v1(bound_instrument_key=bound_instrument_key)

    @staticmethod
    def evaluate(
        state: ObservationAcceptanceStateV1,
        candidate: ObservationCandidateV1,
    ) -> ObservationAcceptanceResultV1:
        return evaluate_distinct_market_observation_v1(state, candidate)

    @staticmethod
    def commit(
        *,
        current_state: ObservationAcceptanceStateV1,
        result: ObservationAcceptanceResultV1,
    ) -> ObservationAcceptanceStateV1:
        return commit_observation_acceptance_v1(current_state=current_state, result=result)
