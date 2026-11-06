"""Bounded productive continuous observation budget (cycles + duration only).

Authority: Product launcher
``run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py``
and S6 orchestrator validation caps. Does not alter trading thresholds or safety pins.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

REASON_UNBOUNDED_OR_INVALID_BOUND = "UNBOUNDED_OR_INVALID_SAFETY_BOUND"
REASON_EXCEEDS_HARD_CAP = "SAFETY_BOUND_EXCEEDS_VALIDATION_HARD_CAP"

# Product default when launcher flags are omitted (unchanged productive policy).
PRODUCTIVE_DEFAULT_MAX_CYCLES_PER_RUN = 4
PRODUCTIVE_DEFAULT_MAX_RUN_DURATION_SECONDS = 180.0

# Smallest finite absolute ceiling permitting WP extended natural verification (12 / 900s).
ABSOLUTE_MAX_CYCLES_PER_RUN = 12
ABSOLUTE_MAX_RUN_DURATION_SECONDS = 900.0

# Backward-compatible aliases (productive defaults, not validation ceiling).
HARD_CAP_MAX_CYCLES_PER_RUN = PRODUCTIVE_DEFAULT_MAX_CYCLES_PER_RUN
HARD_CAP_MAX_RUN_DURATION_SECONDS = PRODUCTIVE_DEFAULT_MAX_RUN_DURATION_SECONDS

REASON_NONFINITE_BOUND = "NONFINITE_SAFETY_BOUND"


class ContinuousObservationBudgetError(ValueError):
    """Fail-closed observation budget parse/validation."""

    def __init__(self, reason_code: str, detail: str = "") -> None:
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}:{detail}" if detail else reason_code)


@dataclass(frozen=True)
class ResolvedContinuousObservationBudgetV1:
    requested_max_cycles: int
    requested_max_run_duration_seconds: float
    effective_max_cycles: int
    effective_max_run_duration_seconds: float


def _reject_nonfinite(*, name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ContinuousObservationBudgetError(REASON_NONFINITE_BOUND, name)


def resolve_continuous_observation_budget_v1(
    *,
    max_cycles: int,
    max_run_duration_seconds: float,
) -> ResolvedContinuousObservationBudgetV1:
    """Validate and resolve explicit bounded observation budget."""
    if not isinstance(max_cycles, int) or isinstance(max_cycles, bool) or max_cycles <= 0:
        raise ContinuousObservationBudgetError(REASON_UNBOUNDED_OR_INVALID_BOUND, "MAX_CYCLES")
    if max_cycles > ABSOLUTE_MAX_CYCLES_PER_RUN:
        raise ContinuousObservationBudgetError(REASON_EXCEEDS_HARD_CAP, "MAX_CYCLES")

    try:
        duration = float(max_run_duration_seconds)
    except (TypeError, ValueError) as exc:
        raise ContinuousObservationBudgetError(
            REASON_UNBOUNDED_OR_INVALID_BOUND, "MAX_RUN_DURATION_SECONDS"
        ) from exc
    _reject_nonfinite(name="MAX_RUN_DURATION_SECONDS", value=duration)
    if duration <= 0:
        raise ContinuousObservationBudgetError(
            REASON_UNBOUNDED_OR_INVALID_BOUND, "MAX_RUN_DURATION_SECONDS"
        )
    if duration > ABSOLUTE_MAX_RUN_DURATION_SECONDS:
        raise ContinuousObservationBudgetError(REASON_EXCEEDS_HARD_CAP, "MAX_RUN_DURATION_SECONDS")

    return ResolvedContinuousObservationBudgetV1(
        requested_max_cycles=int(max_cycles),
        requested_max_run_duration_seconds=duration,
        effective_max_cycles=int(max_cycles),
        effective_max_run_duration_seconds=duration,
    )


__all__ = [
    "ABSOLUTE_MAX_CYCLES_PER_RUN",
    "ABSOLUTE_MAX_RUN_DURATION_SECONDS",
    "ContinuousObservationBudgetError",
    "HARD_CAP_MAX_CYCLES_PER_RUN",
    "HARD_CAP_MAX_RUN_DURATION_SECONDS",
    "PRODUCTIVE_DEFAULT_MAX_CYCLES_PER_RUN",
    "PRODUCTIVE_DEFAULT_MAX_RUN_DURATION_SECONDS",
    "REASON_EXCEEDS_HARD_CAP",
    "REASON_NONFINITE_BOUND",
    "REASON_UNBOUNDED_OR_INVALID_BOUND",
    "ResolvedContinuousObservationBudgetV1",
    "resolve_continuous_observation_budget_v1",
]
