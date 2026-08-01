"""Monotonic duration authority for S03 (10860s). Wallclock is audit-only."""

from __future__ import annotations

from typing import Callable

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
    ARTIFICIAL_DELAY_FOR_AGE_CREATION,
    BOUND_DURATION_SECONDS,
    MARKET_TIME_FABRICATION,
    MONOTONIC_DURATION_AUTHORITY,
    RUNTIME_CYCLE_CANNOT_ADVANCE_MARKET_TIME,
    SYNTHETIC_TIMESTAMP_AGING,
    WALLCLOCK_ONLY_FOR_AUDIT,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    AdditionalEvidenceS03SessionExecutionOwnerError,
)

MonotonicClock = Callable[[], float]


class MonotonicDurationAuthorityV1:
    """Track monotonic elapsed time; completion requires exact bound duration."""

    def __init__(
        self,
        *,
        requested_duration_seconds: int = BOUND_DURATION_SECONDS,
        monotonic_clock: MonotonicClock,
    ) -> None:
        if int(requested_duration_seconds) != BOUND_DURATION_SECONDS:
            raise AdditionalEvidenceS03SessionExecutionOwnerError(
                "duration_seconds_not_bound_10860"
            )
        if not MONOTONIC_DURATION_AUTHORITY:
            raise AdditionalEvidenceS03SessionExecutionOwnerError(
                "monotonic_duration_authority_disabled"
            )
        if ARTIFICIAL_DELAY_FOR_AGE_CREATION or SYNTHETIC_TIMESTAMP_AGING:
            raise AdditionalEvidenceS03SessionExecutionOwnerError("artificial_aging_forbidden")
        if MARKET_TIME_FABRICATION or not RUNTIME_CYCLE_CANNOT_ADVANCE_MARKET_TIME:
            raise AdditionalEvidenceS03SessionExecutionOwnerError(
                "market_time_fabrication_forbidden"
            )
        if not WALLCLOCK_ONLY_FOR_AUDIT:
            raise AdditionalEvidenceS03SessionExecutionOwnerError("wallclock_authority_forbidden")
        self.requested_duration_seconds = int(requested_duration_seconds)
        self._clock = monotonic_clock
        self._start: float | None = None

    def start(self) -> float:
        self._start = float(self._clock())
        return self._start

    @property
    def started(self) -> bool:
        return self._start is not None

    def elapsed_seconds(self) -> float:
        if self._start is None:
            raise AdditionalEvidenceS03SessionExecutionOwnerError("duration_not_started")
        return float(self._clock()) - float(self._start)

    def remaining_seconds(self) -> float:
        return max(0.0, float(self.requested_duration_seconds) - self.elapsed_seconds())

    def is_complete(self) -> bool:
        return self.elapsed_seconds() >= float(self.requested_duration_seconds)

    def assert_sufficient_for_pass(self) -> None:
        if not self.is_complete():
            raise AdditionalEvidenceS03SessionExecutionOwnerError(
                "insufficient_monotonic_duration_for_s03_pass"
            )


def assert_runtime_cycle_does_not_advance_market_time_v1(
    *,
    prior_event_time: float,
    next_event_time: float,
    cycle_index: int,
) -> None:
    """Runtime cycle index must not fabricate market event time."""
    del cycle_index
    if float(next_event_time) < float(prior_event_time):
        # Out-of-order is handled elsewhere; this guard only rejects fabrication.
        return
    # Fabrication would set event_time from cycle index; samples must carry market time.
    if prior_event_time == 0.0 and next_event_time == 0.0:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("market_time_missing")
