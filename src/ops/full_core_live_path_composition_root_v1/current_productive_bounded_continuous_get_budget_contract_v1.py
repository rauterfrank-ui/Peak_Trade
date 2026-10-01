"""Bounded continuous S6 poll count and shared productive GET budget contract.

Single source for orchestrator anti-hang poll iterations and Product entry
transport max_request_count derivation. Pure constants; no network I/O.
"""

from __future__ import annotations

from typing import Any

# Matches orchestrator anti-hang guard: floor(T/w) + max_cycles + margin.
ANTI_HANG_POLL_ITERATION_MARGIN = 8

# Worst-case charged GETs on the Product shared transport before/during S6.
PRODUCTIVE_SHARED_TRANSPORT_G17_CHARGED_GETS = 1
# Cold bootstrap poll(): one dynamic candle + mark + optional index (cache miss each).
PRODUCTIVE_COLD_BOOTSTRAP_WORST_CASE_CHARGED_GETS = 3
# Each S6 observation poll() issues one dynamic-refresh candle GET (cache bypass).
PRODUCTIVE_S6_DYNAMIC_CANDLE_GETS_PER_POLL = 1
# Small finite margin for charged wire attempts beyond idealized happy path.
FINITE_GET_BUDGET_SAFETY_MARGIN = 1


def compute_max_canonical_continuous_poll_iterations_v1(
    *,
    max_run_duration_seconds: float,
    wait_interval_seconds: float,
    max_cycles_per_run: int,
) -> int:
    """Upper bound on orchestrator loop poll() calls (anti-hang guard)."""
    duration = float(max_run_duration_seconds)
    interval = float(wait_interval_seconds)
    if interval <= 0:
        raise ValueError("WAIT_INTERVAL_SECONDS_MUST_BE_POSITIVE")
    return int(duration // interval) + int(max_cycles_per_run) + ANTI_HANG_POLL_ITERATION_MARGIN


def compute_worst_case_legitimate_shared_transport_charged_gets_v1(
    *,
    max_run_duration_seconds: float,
    wait_interval_seconds: float,
    max_cycles_per_run: int,
) -> int:
    """Deterministic worst-case request_count for legitimate bounded Product run."""
    poll_cap = compute_max_canonical_continuous_poll_iterations_v1(
        max_run_duration_seconds=max_run_duration_seconds,
        wait_interval_seconds=wait_interval_seconds,
        max_cycles_per_run=max_cycles_per_run,
    )
    return (
        PRODUCTIVE_SHARED_TRANSPORT_G17_CHARGED_GETS
        + PRODUCTIVE_COLD_BOOTSTRAP_WORST_CASE_CHARGED_GETS
        + poll_cap * PRODUCTIVE_S6_DYNAMIC_CANDLE_GETS_PER_POLL
        + FINITE_GET_BUDGET_SAFETY_MARGIN
    )


def compute_productive_policy_governed_live_c1_shared_transport_max_request_count_v1(
    authorization: Any,
) -> int:
    """Finite transport fuse aligned with the same poll bound as S6 orchestrator."""
    return compute_worst_case_legitimate_shared_transport_charged_gets_v1(
        max_run_duration_seconds=authorization.max_run_duration_seconds,
        wait_interval_seconds=authorization.wait_interval_seconds,
        max_cycles_per_run=authorization.max_cycles_per_run,
    )


__all__ = [
    "ANTI_HANG_POLL_ITERATION_MARGIN",
    "FINITE_GET_BUDGET_SAFETY_MARGIN",
    "PRODUCTIVE_COLD_BOOTSTRAP_WORST_CASE_CHARGED_GETS",
    "PRODUCTIVE_S6_DYNAMIC_CANDLE_GETS_PER_POLL",
    "PRODUCTIVE_SHARED_TRANSPORT_G17_CHARGED_GETS",
    "compute_max_canonical_continuous_poll_iterations_v1",
    "compute_productive_policy_governed_live_c1_shared_transport_max_request_count_v1",
    "compute_worst_case_legitimate_shared_transport_charged_gets_v1",
]
