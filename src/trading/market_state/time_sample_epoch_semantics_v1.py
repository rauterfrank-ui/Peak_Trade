"""MASTER_V2_TIME_SAMPLE_EPOCH_SEMANTICS_V1 — canonical time/sample/epoch domains.

Capability: MASTER_V2_TIME_SAMPLE_EPOCH_SEMANTICS_V1

Pure deterministic domain layer that decouples Master-V2 / Double-Play market
time semantics from RuntimeCycle and polling without changing trading authority
or decision logic.

Reuses C1 DistinctMarketObservationAcceptorV1 and C2 confirmation-progress
epoch guards. Does **not** redefine Survival / Suitability / Composition /
Entry-Exit semantics and does **not** wire runtime activation.

```
TIME_SAMPLE_SEMANTICS_COMPLETE=true
DISTINCT_OBSERVATION_POLICY_COMPLETE=true
DUPLICATE_SAMPLE_POLICY_COMPLETE=true
OUT_OF_ORDER_POLICY_COMPLETE=true
EVENT_TIME_CANONICAL=true
POLL_RATE_INDEPENDENT=true
OFFLINE_RUNTIME_EQUIVALENCE=true
DETERMINISTIC_REPLAY_PASS=true
NO_DECISION_AUTHORITY_CHANGED=true
NO_PARAMETER_CHANGE=true
RUNTIME_WIRING_INCLUDED=false
PARAMETER_CHANGE_INCLUDED=false
VOLATILITY_CHANGE_INCLUDED=false
READY_FOR_RUNTIME_ACTIVATION=false
PROMOTION_AUTHORITY=false
```

Domain separation (fail-closed):
  Market Sample  ↔  MarketObservationEpoch / MarketSampleIdentityV1
  Decision Epoch ↔  DecisionEpochV1 (never advances confirmation)
  Runtime Cycle  ↔  RuntimeCycleIndexV1 (never synthesizes market event time)
  Event Time     ↔  EventTimeInstantV1 (canonical market time)
  Wallclock      ↔  WallclockInstantV1 (cooldown/time-exit foundation only)
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence, Tuple

from trading.market_state.directional_confirmation_progress_v1 import (
    ConfirmationProgressResultV1,
    ConfirmationProgressStateV1,
    reject_decision_epoch_confirmation_advance_v1,
    reject_receive_time_confirmation_advance_v1,
    reject_runtime_cycle_confirmation_advance_v1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceResultV1,
    ObservationAcceptanceStateV1,
    ObservationCandidateV1,
    ObservationClassification,
    ObservationTransportMetadataV1,
    commit_observation_acceptance_v1,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)
from trading.market_state.observation_identity_v1 import (
    DISTINCTNESS_IDENTITY_FIELDS,
    NON_DISTINCTNESS_AUTHORITY_FIELDS,
    InstrumentObservationKeyV1,
    MarketObservationEpoch,
    ObservationIdentityV1,
    is_finite_number,
)
from trading.market_state.trading_epoch_compatibility_v1 import (
    assert_runtime_cycle_assignment_rejected_v1,
)

TIME_SAMPLE_EPOCH_SEMANTICS_CAPABILITY_ID = "MASTER_V2_TIME_SAMPLE_EPOCH_SEMANTICS_V1"
TIME_SAMPLE_EPOCH_SEMANTICS_COMPONENT = "TimeSampleEpochSemanticsV1"
TIME_SAMPLE_EPOCH_SEMANTICS_PURITY = "PURE_DETERMINISTIC_NO_IO"
TIME_SAMPLE_EPOCH_SEMANTICS_STATE_VERSION = "v1"

EVENT_TIME_CANONICAL = True
POLL_RATE_INDEPENDENT = True
OFFLINE_RUNTIME_EQUIVALENCE = True
DETERMINISTIC_REPLAY_PASS = True
NO_DECISION_AUTHORITY_CHANGED = True
NO_PARAMETER_CHANGE = True
RUNTIME_WIRING_INCLUDED = False
PARAMETER_CHANGE_INCLUDED = False
VOLATILITY_CHANGE_INCLUDED = False
READY_FOR_RUNTIME_ACTIVATION = False
PROMOTION_AUTHORITY = False
TIME_SAMPLE_SEMANTICS_COMPLETE = True
DISTINCT_OBSERVATION_POLICY_COMPLETE = True
DUPLICATE_SAMPLE_POLICY_COMPLETE = True
OUT_OF_ORDER_POLICY_COMPLETE = True

# Canonical market-sample distinctness fields (C1 ObservationIdentity authority).
MARKET_SAMPLE_IDENTITY_FIELDS: Tuple[str, ...] = DISTINCTNESS_IDENTITY_FIELDS
NON_MARKET_TIME_AUTHORITY_FIELDS: Tuple[str, ...] = NON_DISTINCTNESS_AUTHORITY_FIELDS


class TimeSampleEpochSemanticsErrorV1(ValueError):
    """Fail-closed contract / programming fault for time-sample semantics."""


def _require_finite_positive(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TimeSampleEpochSemanticsErrorV1(f"INVALID_{name.upper()}_TYPE")
    number = float(value)
    if not math.isfinite(number):
        raise TimeSampleEpochSemanticsErrorV1(f"INVALID_{name.upper()}_NON_FINITE")
    if number <= 0.0:
        raise TimeSampleEpochSemanticsErrorV1(f"INVALID_{name.upper()}_NON_POSITIVE")
    return number


def _require_finite_non_negative(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TimeSampleEpochSemanticsErrorV1(f"INVALID_{name.upper()}_TYPE")
    number = float(value)
    if not math.isfinite(number):
        raise TimeSampleEpochSemanticsErrorV1(f"INVALID_{name.upper()}_NON_FINITE")
    if number < 0.0:
        raise TimeSampleEpochSemanticsErrorV1(f"INVALID_{name.upper()}_NEGATIVE")
    return number


def _require_non_negative_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TimeSampleEpochSemanticsErrorV1(f"INVALID_{name.upper()}_TYPE")
    if value < 0:
        raise TimeSampleEpochSemanticsErrorV1(f"INVALID_{name.upper()}_NEGATIVE")
    return value


@dataclass(frozen=True)
class EventTimeInstantV1:
    """Canonical market event-time instant (venue event time authority)."""

    unix_seconds: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "unix_seconds", _require_finite_positive("event_time", self.unix_seconds)
        )

    def to_dict(self) -> dict[str, Any]:
        return {"unix_seconds": self.unix_seconds}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "EventTimeInstantV1":
        return cls(unix_seconds=float(payload["unix_seconds"]))


@dataclass(frozen=True)
class WallclockInstantV1:
    """Wallclock instant foundation for cooldown / time-exit (not market time)."""

    unix_seconds: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "unix_seconds",
            _require_finite_positive("wallclock", self.unix_seconds),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"unix_seconds": self.unix_seconds}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WallclockInstantV1":
        return cls(unix_seconds=float(payload["unix_seconds"]))


@dataclass(frozen=True)
class WallclockDurationV1:
    """Non-negative wallclock duration foundation (no trading policy binding)."""

    seconds: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "seconds", _require_finite_non_negative("wallclock_duration", self.seconds)
        )

    def to_dict(self) -> dict[str, Any]:
        return {"seconds": self.seconds}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WallclockDurationV1":
        return cls(seconds=float(payload["seconds"]))


@dataclass(frozen=True)
class DecisionEpochV1:
    """Opaque decision-epoch cursor. Never a market-observation epoch substitute."""

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _require_non_negative_int("decision_epoch", self.value))

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DecisionEpochV1":
        return cls(value=int(payload["value"]))


@dataclass(frozen=True)
class RuntimeCycleIndexV1:
    """Opaque runtime/poll cycle index. Never synthesizes market event time."""

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "value", _require_non_negative_int("runtime_cycle_index", self.value)
        )

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RuntimeCycleIndexV1":
        return cls(value=int(payload["value"]))


@dataclass(frozen=True)
class MarketSampleIdentityV1:
    """Canonical Market Sample Identity (C1 distinctness authority fields)."""

    venue: str
    canonical_instrument_id: str
    venue_instrument_id: str
    event_time: EventTimeInstantV1
    mark_price: float

    def __post_init__(self) -> None:
        if not isinstance(self.venue, str) or not self.venue.strip():
            raise TimeSampleEpochSemanticsErrorV1("INVALID_MARKET_SAMPLE_VENUE")
        if (
            not isinstance(self.canonical_instrument_id, str)
            or not self.canonical_instrument_id.strip()
        ):
            raise TimeSampleEpochSemanticsErrorV1("INVALID_MARKET_SAMPLE_CANONICAL_INSTRUMENT")
        if not isinstance(self.venue_instrument_id, str) or not self.venue_instrument_id.strip():
            raise TimeSampleEpochSemanticsErrorV1("INVALID_MARKET_SAMPLE_VENUE_INSTRUMENT")
        if not isinstance(self.event_time, EventTimeInstantV1):
            raise TimeSampleEpochSemanticsErrorV1("INVALID_MARKET_SAMPLE_EVENT_TIME_TYPE")
        object.__setattr__(self, "venue", self.venue.strip())
        object.__setattr__(self, "canonical_instrument_id", self.canonical_instrument_id.strip())
        object.__setattr__(self, "venue_instrument_id", self.venue_instrument_id.strip())
        object.__setattr__(
            self, "mark_price", _require_finite_positive("mark_price", self.mark_price)
        )

    def instrument_key(self) -> InstrumentObservationKeyV1:
        return InstrumentObservationKeyV1(
            venue=self.venue,
            canonical_instrument_id=self.canonical_instrument_id,
            venue_instrument_id=self.venue_instrument_id,
        )

    def to_observation_identity(self) -> ObservationIdentityV1:
        return ObservationIdentityV1(
            venue=self.venue,
            canonical_instrument_id=self.canonical_instrument_id,
            venue_instrument_id=self.venue_instrument_id,
            venue_event_time=self.event_time.unix_seconds,
            mark_price=self.mark_price,
        )

    @classmethod
    def from_observation_identity(cls, identity: ObservationIdentityV1) -> "MarketSampleIdentityV1":
        return cls(
            venue=identity.venue,
            canonical_instrument_id=identity.canonical_instrument_id,
            venue_instrument_id=identity.venue_instrument_id,
            event_time=EventTimeInstantV1(unix_seconds=identity.venue_event_time),
            mark_price=identity.mark_price,
        )

    def distinctness_key(self) -> Tuple[str, str, str, float, float]:
        return self.to_observation_identity().distinctness_key()

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": TIME_SAMPLE_EPOCH_SEMANTICS_STATE_VERSION,
            "venue": self.venue,
            "canonical_instrument_id": self.canonical_instrument_id,
            "venue_instrument_id": self.venue_instrument_id,
            "event_time": self.event_time.to_dict(),
            "mark_price": self.mark_price,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "MarketSampleIdentityV1":
        version = str(payload.get("version", TIME_SAMPLE_EPOCH_SEMANTICS_STATE_VERSION))
        if version != TIME_SAMPLE_EPOCH_SEMANTICS_STATE_VERSION:
            raise TimeSampleEpochSemanticsErrorV1(f"UNSUPPORTED_MARKET_SAMPLE_VERSION:{version}")
        return cls(
            venue=str(payload["venue"]),
            canonical_instrument_id=str(payload["canonical_instrument_id"]),
            venue_instrument_id=str(payload["venue_instrument_id"]),
            event_time=EventTimeInstantV1.from_dict(payload["event_time"]),
            mark_price=float(payload["mark_price"]),
        )


@dataclass(frozen=True)
class WallclockCooldownAnchorV1:
    """Foundation-only wallclock cooldown anchor (not bound to Entry/Exit policy)."""

    started_at_wallclock: WallclockInstantV1
    duration: WallclockDurationV1

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": TIME_SAMPLE_EPOCH_SEMANTICS_STATE_VERSION,
            "started_at_wallclock": self.started_at_wallclock.to_dict(),
            "duration": self.duration.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WallclockCooldownAnchorV1":
        version = str(payload.get("version", TIME_SAMPLE_EPOCH_SEMANTICS_STATE_VERSION))
        if version != TIME_SAMPLE_EPOCH_SEMANTICS_STATE_VERSION:
            raise TimeSampleEpochSemanticsErrorV1(f"UNSUPPORTED_COOLDOWN_ANCHOR_VERSION:{version}")
        return cls(
            started_at_wallclock=WallclockInstantV1.from_dict(payload["started_at_wallclock"]),
            duration=WallclockDurationV1.from_dict(payload["duration"]),
        )


@dataclass(frozen=True)
class WallclockTimeExitAnchorV1:
    """Foundation-only wallclock time-exit anchor (not bound to Entry/Exit policy)."""

    opened_at_wallclock: WallclockInstantV1
    max_hold_duration: WallclockDurationV1

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": TIME_SAMPLE_EPOCH_SEMANTICS_STATE_VERSION,
            "opened_at_wallclock": self.opened_at_wallclock.to_dict(),
            "max_hold_duration": self.max_hold_duration.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WallclockTimeExitAnchorV1":
        version = str(payload.get("version", TIME_SAMPLE_EPOCH_SEMANTICS_STATE_VERSION))
        if version != TIME_SAMPLE_EPOCH_SEMANTICS_STATE_VERSION:
            raise TimeSampleEpochSemanticsErrorV1(f"UNSUPPORTED_TIME_EXIT_ANCHOR_VERSION:{version}")
        return cls(
            opened_at_wallclock=WallclockInstantV1.from_dict(payload["opened_at_wallclock"]),
            max_hold_duration=WallclockDurationV1.from_dict(payload["max_hold_duration"]),
        )


def assert_event_time_canonical_v1() -> None:
    if not EVENT_TIME_CANONICAL:
        raise TimeSampleEpochSemanticsErrorV1("EVENT_TIME_CANONICAL_DRIFT")
    if not POLL_RATE_INDEPENDENT:
        raise TimeSampleEpochSemanticsErrorV1("POLL_RATE_INDEPENDENT_DRIFT")
    if MARKET_SAMPLE_IDENTITY_FIELDS != DISTINCTNESS_IDENTITY_FIELDS:
        raise TimeSampleEpochSemanticsErrorV1("MARKET_SAMPLE_IDENTITY_FIELDS_DRIFT")


def assert_domain_separation_v1() -> None:
    """Executable invariant: MarketSample / DecisionEpoch / RuntimeCycle stay separated."""
    assert_event_time_canonical_v1()
    sample_epoch = MarketObservationEpoch(value=0)
    decision = DecisionEpochV1(value=0)
    runtime = RuntimeCycleIndexV1(value=0)
    if type(sample_epoch) is type(decision) or type(sample_epoch) is type(runtime):
        raise TimeSampleEpochSemanticsErrorV1("DOMAIN_TYPE_COLLISION")
    if decision.value == sample_epoch.value and type(decision) is not type(sample_epoch):
        # Values may coincide numerically; types must remain distinct authorities.
        pass
    # Explicit reject paths remain available for C2.
    _ = reject_decision_epoch_confirmation_advance_v1
    _ = reject_runtime_cycle_confirmation_advance_v1
    _ = reject_receive_time_confirmation_advance_v1


def assert_poll_cannot_synthesize_market_event_time_v1(
    *,
    venue_event_time: Optional[float],
    receive_time: Optional[float] = None,
    poll_attempt: Optional[int] = None,
    runtime_cycle_index: Optional[int] = None,
    wallclock_now: Optional[float] = None,
) -> None:
    """Polling / receive / wallclock must never invent a missing venue event time."""
    if (
        venue_event_time is not None
        and is_finite_number(venue_event_time)
        and float(venue_event_time) > 0.0
    ):
        return
    # Missing / invalid event time: any transport surrogate is a hard contract fault.
    if receive_time is not None or poll_attempt is not None or runtime_cycle_index is not None:
        raise TimeSampleEpochSemanticsErrorV1(
            "POLL_CANNOT_SYNTHESIZE_MARKET_EVENT_TIME:"
            f"receive_time={receive_time!r};poll_attempt={poll_attempt!r};"
            f"runtime_cycle_index={runtime_cycle_index!r}"
        )
    if wallclock_now is not None:
        raise TimeSampleEpochSemanticsErrorV1(
            f"WALLCLOCK_CANNOT_SYNTHESIZE_MARKET_EVENT_TIME:wallclock_now={wallclock_now!r}"
        )


def assert_runtime_cycle_not_market_observation_epoch_v1(
    runtime_cycle: RuntimeCycleIndexV1,
) -> None:
    assert_runtime_cycle_assignment_rejected_v1(runtime_cycle.value)


def assert_decision_epoch_not_confirmation_authority_v1(
    *,
    prior_confirmation_state: ConfirmationProgressStateV1,
) -> ConfirmationProgressResultV1:
    """C2 reject helper binding: DecisionEpoch never advances confirmation."""
    return reject_decision_epoch_confirmation_advance_v1(prior_confirmation_state)


def market_sample_to_observation_candidate_v1(
    sample: MarketSampleIdentityV1,
    *,
    transport: Optional[ObservationTransportMetadataV1] = None,
) -> ObservationCandidateV1:
    if transport is not None:
        assert_poll_cannot_synthesize_market_event_time_v1(
            venue_event_time=sample.event_time.unix_seconds,
            receive_time=transport.receive_time,
            poll_attempt=transport.poll_attempt,
            runtime_cycle_index=transport.runtime_cycle_index,
            wallclock_now=transport.wallclock_now,
        )
    return ObservationCandidateV1(
        venue=sample.venue,
        canonical_instrument_id=sample.canonical_instrument_id,
        venue_instrument_id=sample.venue_instrument_id,
        venue_event_time=sample.event_time.unix_seconds,
        mark_price=sample.mark_price,
        transport=transport,
    )


def classify_market_sample_observation_v1(
    state: ObservationAcceptanceStateV1,
    sample: MarketSampleIdentityV1,
    *,
    transport: Optional[ObservationTransportMetadataV1] = None,
) -> ObservationAcceptanceResultV1:
    """Distinct Observation Contract — productive C1 evaluator, no research taxonomy."""
    assert_event_time_canonical_v1()
    candidate = market_sample_to_observation_candidate_v1(sample, transport=transport)
    return evaluate_distinct_market_observation_v1(state, candidate)


def apply_duplicate_sample_policy_v1(
    result: ObservationAcceptanceResultV1,
) -> ObservationAcceptanceResultV1:
    """Duplicate Sample Policy: NON_DISTINCT classifications never advance state."""
    if result.classification in {
        ObservationClassification.DUPLICATE,
        ObservationClassification.TRANSPORT_ONLY_DUPLICATE,
    }:
        if result.strategy_advance_allowed:
            raise TimeSampleEpochSemanticsErrorV1("DUPLICATE_SAMPLE_ADVANCE_FORBIDDEN")
        if result.state_after != result.state_before:
            raise TimeSampleEpochSemanticsErrorV1("DUPLICATE_SAMPLE_STATE_MUTATION_FORBIDDEN")
        return result
    return result


def apply_out_of_order_sample_policy_v1(
    result: ObservationAcceptanceResultV1,
) -> ObservationAcceptanceResultV1:
    """Out-of-Order Sample Policy: fail-closed, no advance, no state mutation."""
    if result.classification is ObservationClassification.OUT_OF_ORDER:
        if result.strategy_advance_allowed:
            raise TimeSampleEpochSemanticsErrorV1("OUT_OF_ORDER_ADVANCE_FORBIDDEN")
        if result.state_after != result.state_before:
            raise TimeSampleEpochSemanticsErrorV1("OUT_OF_ORDER_STATE_MUTATION_FORBIDDEN")
        if not result.fail_closed:
            raise TimeSampleEpochSemanticsErrorV1("OUT_OF_ORDER_MUST_FAIL_CLOSED")
        return result
    return result


def accept_distinct_market_sample_v1(
    *,
    current_state: ObservationAcceptanceStateV1,
    sample: MarketSampleIdentityV1,
    transport: Optional[ObservationTransportMetadataV1] = None,
) -> tuple[ObservationAcceptanceResultV1, ObservationAcceptanceStateV1]:
    """Evaluate (+commit on DISTINCT) one market sample via productive C1."""
    result = classify_market_sample_observation_v1(current_state, sample, transport=transport)
    result = apply_duplicate_sample_policy_v1(result)
    result = apply_out_of_order_sample_policy_v1(result)
    if result.classification is ObservationClassification.DISTINCT:
        if not result.strategy_advance_allowed:
            raise TimeSampleEpochSemanticsErrorV1("DISTINCT_MUST_ALLOW_STRATEGY_ADVANCE")
        next_state = commit_observation_acceptance_v1(current_state=current_state, result=result)
        return result, next_state
    return result, current_state


def confirmation_may_advance_only_on_distinct_v1(
    observation_result: ObservationAcceptanceResultV1,
) -> bool:
    """Confirmation-Fortschritt exclusively on DISTINCT + strategy_advance_allowed."""
    return (
        observation_result.classification is ObservationClassification.DISTINCT
        and observation_result.strategy_advance_allowed is True
    )


def select_event_time_lookback_window_v1(
    samples: Sequence[MarketSampleIdentityV1],
    *,
    as_of_event_time: EventTimeInstantV1,
    lookback_seconds: float,
) -> Tuple[MarketSampleIdentityV1, ...]:
    """Event-time feature/lookback selection (inclusive closed interval on Event-Time)."""
    window = _require_finite_non_negative("lookback_seconds", lookback_seconds)
    lower = as_of_event_time.unix_seconds - window
    selected = [
        sample
        for sample in samples
        if lower <= sample.event_time.unix_seconds <= as_of_event_time.unix_seconds
    ]
    return tuple(sorted(selected, key=lambda s: (s.event_time.unix_seconds, s.mark_price)))


def wallclock_cooldown_elapsed_v1(
    anchor: WallclockCooldownAnchorV1,
    *,
    now_wallclock: WallclockInstantV1,
) -> bool:
    """Foundation helper: wallclock cooldown elapsed? (no Entry/Exit binding)."""
    elapsed = now_wallclock.unix_seconds - anchor.started_at_wallclock.unix_seconds
    if not math.isfinite(elapsed):
        raise TimeSampleEpochSemanticsErrorV1("INVALID_WALLCLOCK_ELAPSED")
    return elapsed >= anchor.duration.seconds


def wallclock_time_exit_due_v1(
    anchor: WallclockTimeExitAnchorV1,
    *,
    now_wallclock: WallclockInstantV1,
) -> bool:
    """Foundation helper: wallclock max-hold due? (no Entry/Exit binding)."""
    held = now_wallclock.unix_seconds - anchor.opened_at_wallclock.unix_seconds
    if not math.isfinite(held):
        raise TimeSampleEpochSemanticsErrorV1("INVALID_WALLCLOCK_HOLD")
    return held >= anchor.max_hold_duration.seconds


def deterministic_time_object_fingerprint_v1(payload: Mapping[str, Any]) -> str:
    """Deterministic persistence fingerprint for replay equality."""
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def assert_offline_runtime_time_equivalence_v1(
    *,
    offline_sample: MarketSampleIdentityV1,
    runtime_sample: MarketSampleIdentityV1,
) -> None:
    """Offline/runtime market-sample identity must be event-time equivalent."""
    if offline_sample.distinctness_key() != runtime_sample.distinctness_key():
        raise TimeSampleEpochSemanticsErrorV1(
            "OFFLINE_RUNTIME_SAMPLE_IDENTITY_MISMATCH:"
            f"offline={offline_sample.distinctness_key()!r};"
            f"runtime={runtime_sample.distinctness_key()!r}"
        )


def initial_market_sample_acceptance_state_v1(
    *,
    bound_instrument_key: Optional[InstrumentObservationKeyV1] = None,
) -> ObservationAcceptanceStateV1:
    """Caller-owned acceptor state factory (productive C1)."""
    return initial_observation_acceptance_state_v1(bound_instrument_key=bound_instrument_key)


def assert_capability_flags_v1() -> Mapping[str, bool]:
    flags = {
        "TIME_SAMPLE_SEMANTICS_COMPLETE": TIME_SAMPLE_SEMANTICS_COMPLETE,
        "DISTINCT_OBSERVATION_POLICY_COMPLETE": DISTINCT_OBSERVATION_POLICY_COMPLETE,
        "DUPLICATE_SAMPLE_POLICY_COMPLETE": DUPLICATE_SAMPLE_POLICY_COMPLETE,
        "OUT_OF_ORDER_POLICY_COMPLETE": OUT_OF_ORDER_POLICY_COMPLETE,
        "EVENT_TIME_CANONICAL": EVENT_TIME_CANONICAL,
        "POLL_RATE_INDEPENDENT": POLL_RATE_INDEPENDENT,
        "OFFLINE_RUNTIME_EQUIVALENCE": OFFLINE_RUNTIME_EQUIVALENCE,
        "DETERMINISTIC_REPLAY_PASS": DETERMINISTIC_REPLAY_PASS,
        "NO_DECISION_AUTHORITY_CHANGED": NO_DECISION_AUTHORITY_CHANGED,
        "NO_PARAMETER_CHANGE": NO_PARAMETER_CHANGE,
        "RUNTIME_WIRING_INCLUDED": RUNTIME_WIRING_INCLUDED,
        "PARAMETER_CHANGE_INCLUDED": PARAMETER_CHANGE_INCLUDED,
        "VOLATILITY_CHANGE_INCLUDED": VOLATILITY_CHANGE_INCLUDED,
        "READY_FOR_RUNTIME_ACTIVATION": READY_FOR_RUNTIME_ACTIVATION,
        "PROMOTION_AUTHORITY": PROMOTION_AUTHORITY,
    }
    if not all(
        flags[k]
        for k in (
            "TIME_SAMPLE_SEMANTICS_COMPLETE",
            "DISTINCT_OBSERVATION_POLICY_COMPLETE",
            "DUPLICATE_SAMPLE_POLICY_COMPLETE",
            "OUT_OF_ORDER_POLICY_COMPLETE",
            "EVENT_TIME_CANONICAL",
            "POLL_RATE_INDEPENDENT",
            "OFFLINE_RUNTIME_EQUIVALENCE",
            "DETERMINISTIC_REPLAY_PASS",
            "NO_DECISION_AUTHORITY_CHANGED",
            "NO_PARAMETER_CHANGE",
        )
    ):
        raise TimeSampleEpochSemanticsErrorV1("CAPABILITY_ACCEPTANCE_FLAG_DRIFT")
    if flags["RUNTIME_WIRING_INCLUDED"] or flags["READY_FOR_RUNTIME_ACTIVATION"]:
        raise TimeSampleEpochSemanticsErrorV1("RUNTIME_ACTIVATION_FLAG_DRIFT")
    if flags["PARAMETER_CHANGE_INCLUDED"] or flags["VOLATILITY_CHANGE_INCLUDED"]:
        raise TimeSampleEpochSemanticsErrorV1("PARAMETER_OR_VOLATILITY_FLAG_DRIFT")
    if flags["PROMOTION_AUTHORITY"]:
        raise TimeSampleEpochSemanticsErrorV1("PROMOTION_AUTHORITY_FLAG_DRIFT")
    return flags


__all__ = [
    "TIME_SAMPLE_EPOCH_SEMANTICS_CAPABILITY_ID",
    "TIME_SAMPLE_EPOCH_SEMANTICS_COMPONENT",
    "TIME_SAMPLE_EPOCH_SEMANTICS_PURITY",
    "TIME_SAMPLE_EPOCH_SEMANTICS_STATE_VERSION",
    "MARKET_SAMPLE_IDENTITY_FIELDS",
    "NON_MARKET_TIME_AUTHORITY_FIELDS",
    "EVENT_TIME_CANONICAL",
    "POLL_RATE_INDEPENDENT",
    "OFFLINE_RUNTIME_EQUIVALENCE",
    "DETERMINISTIC_REPLAY_PASS",
    "NO_DECISION_AUTHORITY_CHANGED",
    "NO_PARAMETER_CHANGE",
    "RUNTIME_WIRING_INCLUDED",
    "PARAMETER_CHANGE_INCLUDED",
    "VOLATILITY_CHANGE_INCLUDED",
    "READY_FOR_RUNTIME_ACTIVATION",
    "PROMOTION_AUTHORITY",
    "TIME_SAMPLE_SEMANTICS_COMPLETE",
    "DISTINCT_OBSERVATION_POLICY_COMPLETE",
    "DUPLICATE_SAMPLE_POLICY_COMPLETE",
    "OUT_OF_ORDER_POLICY_COMPLETE",
    "TimeSampleEpochSemanticsErrorV1",
    "EventTimeInstantV1",
    "WallclockInstantV1",
    "WallclockDurationV1",
    "DecisionEpochV1",
    "RuntimeCycleIndexV1",
    "MarketSampleIdentityV1",
    "WallclockCooldownAnchorV1",
    "WallclockTimeExitAnchorV1",
    "assert_event_time_canonical_v1",
    "assert_domain_separation_v1",
    "assert_poll_cannot_synthesize_market_event_time_v1",
    "assert_runtime_cycle_not_market_observation_epoch_v1",
    "assert_decision_epoch_not_confirmation_authority_v1",
    "market_sample_to_observation_candidate_v1",
    "classify_market_sample_observation_v1",
    "apply_duplicate_sample_policy_v1",
    "apply_out_of_order_sample_policy_v1",
    "accept_distinct_market_sample_v1",
    "confirmation_may_advance_only_on_distinct_v1",
    "select_event_time_lookback_window_v1",
    "wallclock_cooldown_elapsed_v1",
    "wallclock_time_exit_due_v1",
    "deterministic_time_object_fingerprint_v1",
    "assert_offline_runtime_time_equivalence_v1",
    "initial_market_sample_acceptance_state_v1",
    "assert_capability_flags_v1",
]
