"""Typed natural VolatilityEstimate lifecycle contract (research evidence only)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Optional

from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.constants_v1 import (
    AGE_DERIVED_FROM_EVENT_TIME_ONLY,
    AGE_FORMULA_VERSION,
    AGE_REFERENCE_CLOCK,
    ESTIMATE_AS_OF_EVENT_TIME_IMMUTABLE_DURING_REUSE,
    ESTIMATE_RECOMPUTE_TRIGGER_EXPLICIT,
    ESTIMATE_REUSE_DOES_NOT_MUTATE_ESTIMATE,
    ESTIMATE_REUSE_EXPLICIT,
    NO_POLICY_ENFORCEMENT,
    NO_SLEEP_BASED_AGE_SYNTHESIS,
    NO_TIMESTAMP_INJECTION,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    CanonicalVolatilityEstimateV1,
    VolatilityEstimateV1,
)


class NaturalAgeLifecycleErrorV1(ValueError):
    """Fail-closed natural age lifecycle error."""


class LifecycleOutcomeV1(str, Enum):
    WARMUP = "WARMUP"
    PRODUCED = "PRODUCED"
    REUSED = "REUSED"
    DUPLICATE_NOOP = "DUPLICATE_NOOP"
    OUT_OF_ORDER_NOT_EVALUABLE = "OUT_OF_ORDER_NOT_EVALUABLE"
    INVALID_SAMPLE_REJECTED = "INVALID_SAMPLE_REJECTED"
    MISSING_ESTIMATE = "MISSING_ESTIMATE"
    RUNTIME_CYCLE_NOOP = "RUNTIME_CYCLE_NOOP"
    RECOMPUTED = "RECOMPUTED"


class RecomputeReasonV1(str, Enum):
    SESSION_START_FIRST_ESTIMATE = "SESSION_START_FIRST_ESTIMATE"
    MISSING_ESTIMATE = "MISSING_ESTIMATE"
    INVALID_PRIOR_ESTIMATE = "INVALID_PRIOR_ESTIMATE"
    MINIMUM_NEW_DISTINCT_OBSERVATIONS_REACHED = "MINIMUM_NEW_DISTINCT_OBSERVATIONS_REACHED"
    MINIMUM_EVENT_TIME_ELAPSED_REACHED = "MINIMUM_EVENT_TIME_ELAPSED_REACHED"
    SOURCE_WINDOW_MATERIAL_CHANGE = "SOURCE_WINDOW_MATERIAL_CHANGE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


def _parse_event_time(value: Any, *, field_name: str) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            raise NaturalAgeLifecycleErrorV1(f"{field_name}_required")
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def compute_natural_age_seconds_v1(
    *,
    market_event_time: Any,
    as_of_event_time: Any,
) -> float:
    """Age from event time only. Negative ages fail closed (not silently corrected)."""
    market = _parse_event_time(market_event_time, field_name="market_event_time")
    as_of = _parse_event_time(as_of_event_time, field_name="as_of_event_time")
    age = (market - as_of).total_seconds()
    if age < 0:
        raise NaturalAgeLifecycleErrorV1("negative_age_seconds")
    return float(age)


@dataclass(frozen=True)
class VolatilityEstimateLifecycleState:
    """Immutable lifecycle carrier for a reused or freshly produced estimate."""

    estimate: VolatilityEstimateV1
    produced_at_market_event_time: str
    last_recompute_reason: str
    reuse_count: int
    distinct_observations_since_recompute: int
    source_window_start_event_time: str
    source_window_end_event_time: str
    source_digest: str

    def __post_init__(self) -> None:
        if self.reuse_count < 0:
            raise NaturalAgeLifecycleErrorV1("reuse_count_negative")
        if self.distinct_observations_since_recompute < 0:
            raise NaturalAgeLifecycleErrorV1("distinct_observations_since_recompute_negative")
        if not isinstance(self.estimate, CanonicalVolatilityEstimateV1):
            raise NaturalAgeLifecycleErrorV1("estimate_must_be_typed_volatility_estimate")
        as_of = self.estimate.as_of_event_time.astimezone(timezone.utc).isoformat()
        if as_of != self.produced_at_market_event_time and self.reuse_count == 0:
            # Fresh produce: as_of must equal produced_at.
            produced = _parse_event_time(
                self.produced_at_market_event_time, field_name="produced_at_market_event_time"
            )
            if self.estimate.as_of_event_time.astimezone(timezone.utc) != produced:
                raise NaturalAgeLifecycleErrorV1("fresh_as_of_must_equal_produced_at")
        if not str(self.source_digest).strip():
            raise NaturalAgeLifecycleErrorV1("source_digest_required")
        if not str(self.last_recompute_reason).strip():
            raise NaturalAgeLifecycleErrorV1("last_recompute_reason_required")

    @property
    def as_of_event_time(self) -> datetime:
        return self.estimate.as_of_event_time

    def to_dict(self) -> dict[str, Any]:
        return {
            "distinct_observations_since_recompute": self.distinct_observations_since_recompute,
            "estimate": self.estimate.to_dict(),
            "last_recompute_reason": self.last_recompute_reason,
            "produced_at_market_event_time": self.produced_at_market_event_time,
            "reuse_count": self.reuse_count,
            "source_digest": self.source_digest,
            "source_window_end_event_time": self.source_window_end_event_time,
            "source_window_start_event_time": self.source_window_start_event_time,
        }


@dataclass(frozen=True)
class NaturalAgeLifecycleObservationV1:
    """One lifecycle observation for evidence / tests (non-enforcing)."""

    outcome: str
    market_event_time: Optional[str]
    as_of_event_time: Optional[str]
    age_seconds: Optional[float]
    estimate_reused: bool
    reuse_count: int
    distinct_observations_since_recompute: int
    source_digest: Optional[str]
    recompute_reason: str
    age_evaluable: bool
    not_evaluable_reason: str
    lifecycle_state: Optional[VolatilityEstimateLifecycleState]

    def to_dict(self) -> dict[str, Any]:
        return {
            "age_evaluable": self.age_evaluable,
            "age_formula_version": AGE_FORMULA_VERSION,
            "age_reference_clock": AGE_REFERENCE_CLOCK,
            "age_seconds": self.age_seconds,
            "as_of_event_time": self.as_of_event_time,
            "distinct_observations_since_recompute": self.distinct_observations_since_recompute,
            "estimate_reused": self.estimate_reused,
            "market_event_time": self.market_event_time,
            "not_evaluable_reason": self.not_evaluable_reason,
            "outcome": self.outcome,
            "recompute_reason": self.recompute_reason,
            "reuse_count": self.reuse_count,
            "source_digest": self.source_digest,
            "invariants": {
                "AGE_DERIVED_FROM_EVENT_TIME_ONLY": AGE_DERIVED_FROM_EVENT_TIME_ONLY,
                "ESTIMATE_AS_OF_EVENT_TIME_IMMUTABLE_DURING_REUSE": (
                    ESTIMATE_AS_OF_EVENT_TIME_IMMUTABLE_DURING_REUSE
                ),
                "ESTIMATE_RECOMPUTE_TRIGGER_EXPLICIT": ESTIMATE_RECOMPUTE_TRIGGER_EXPLICIT,
                "ESTIMATE_REUSE_DOES_NOT_MUTATE_ESTIMATE": ESTIMATE_REUSE_DOES_NOT_MUTATE_ESTIMATE,
                "ESTIMATE_REUSE_EXPLICIT": ESTIMATE_REUSE_EXPLICIT,
                "NO_POLICY_ENFORCEMENT": NO_POLICY_ENFORCEMENT,
                "NO_SLEEP_BASED_AGE_SYNTHESIS": NO_SLEEP_BASED_AGE_SYNTHESIS,
                "NO_TIMESTAMP_INJECTION": NO_TIMESTAMP_INJECTION,
            },
        }


def assert_lifecycle_invariants_v1(
    prior: Optional[VolatilityEstimateLifecycleState],
    current: VolatilityEstimateLifecycleState,
    *,
    reused: bool,
) -> None:
    if not reused:
        return
    if prior is None:
        raise NaturalAgeLifecycleErrorV1("reuse_without_prior_state")
    if prior.estimate.source_digest != current.estimate.source_digest:
        raise NaturalAgeLifecycleErrorV1("reuse_mutated_source_digest")
    if prior.estimate.as_of_event_time != current.estimate.as_of_event_time:
        raise NaturalAgeLifecycleErrorV1("reuse_mutated_as_of_event_time")
    if prior.estimate.value != current.estimate.value:
        raise NaturalAgeLifecycleErrorV1("reuse_mutated_estimate_value")
    if current.produced_at_market_event_time != prior.produced_at_market_event_time:
        raise NaturalAgeLifecycleErrorV1("reuse_mutated_produced_at")


def lifecycle_state_machine_matrix_v1() -> Mapping[str, Any]:
    return {
        "states": [
            "NO_ESTIMATE",
            "WARMUP",
            "FRESHLY_PRODUCED",
            "REUSED",
            "RECOMPUTED",
            "NOT_EVALUABLE_OUT_OF_ORDER",
            "DUPLICATE_NOOP",
            "RUNTIME_CYCLE_NOOP",
        ],
        "transitions": [
            {
                "from": "NO_ESTIMATE",
                "event": "first_valid_materialization",
                "to": "FRESHLY_PRODUCED",
                "reason": RecomputeReasonV1.SESSION_START_FIRST_ESTIMATE.value,
            },
            {
                "from": "FRESHLY_PRODUCED",
                "event": "distinct_observation_without_recompute_trigger",
                "to": "REUSED",
                "age": "advances_by_event_time_only",
            },
            {
                "from": "REUSED",
                "event": "distinct_observation_without_recompute_trigger",
                "to": "REUSED",
                "age": "advances_by_event_time_only",
            },
            {
                "from": "REUSED",
                "event": "recompute_trigger",
                "to": "RECOMPUTED",
                "age": "resets_to_zero",
            },
            {
                "from": "*",
                "event": "duplicate_observation",
                "to": "DUPLICATE_NOOP",
                "age": "unchanged",
            },
            {
                "from": "*",
                "event": "out_of_order_observation",
                "to": "NOT_EVALUABLE_OUT_OF_ORDER",
                "age": "not_negatively_advanced",
            },
            {
                "from": "*",
                "event": "runtime_cycle_without_sample",
                "to": "RUNTIME_CYCLE_NOOP",
                "age": "unchanged",
            },
        ],
        "age_formula": "market_event_time - estimate.as_of_event_time",
        "enforcement": False,
    }
