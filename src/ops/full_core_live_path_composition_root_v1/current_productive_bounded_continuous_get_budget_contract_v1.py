"""Bounded continuous S6 poll count and shared productive GET budget contract.

Single source for orchestrator anti-hang poll iterations and Product entry
transport max_request_count derivation. Pure constants; no network I/O.
"""

from __future__ import annotations

from math import isfinite
from typing import Any

# Matches orchestrator anti-hang guard: floor(T/w) + max_cycles + margin.
ANTI_HANG_POLL_ITERATION_MARGIN = 8

# Worst-case charged GETs on the Product shared transport before/during S6.
PRODUCTIVE_SHARED_TRANSPORT_G17_CHARGED_GETS = 1
# Cold bootstrap poll(): one dynamic candle + mark + optional dynamic index.
PRODUCTIVE_COLD_BOOTSTRAP_WORST_CASE_CHARGED_GETS = 3
# Each S6 observation poll() issues dynamic-refresh candle + mark GETs (cache bypass).
PRODUCTIVE_S6_DYNAMIC_CANDLE_GETS_PER_POLL = 1
PRODUCTIVE_S6_DYNAMIC_MARK_GETS_PER_POLL = 1
# A mark response without idxPx requires a fresh index-tickers GET on every poll.
PRODUCTIVE_S6_DYNAMIC_INDEX_GETS_PER_POLL = 1
# Small finite margin for charged wire attempts beyond idealized happy path.
FINITE_GET_BUDGET_SAFETY_MARGIN = 1


def productive_s6_dynamic_wire_gets_per_poll_v1() -> int:
    """Worst-case charged candle, mark and conditional index GETs per S6 poll."""
    return (
        PRODUCTIVE_S6_DYNAMIC_CANDLE_GETS_PER_POLL
        + PRODUCTIVE_S6_DYNAMIC_MARK_GETS_PER_POLL
        + PRODUCTIVE_S6_DYNAMIC_INDEX_GETS_PER_POLL
    )


def productive_pretrade_wire_gets_per_decision_v1() -> int:
    """Count original unique fetch groups; a new decision cannot reuse old GETs.

    Lazy import avoids the observation/orchestrator/fresh-pretrade import cycle.
    This counts required reads, without adding endpoints or acquisition authority.
    """
    from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
        REQUIRED_GET_ITEM_SPECS,
    )

    return len({spec.fetch_group for spec in REQUIRED_GET_ITEM_SPECS})


def compute_max_canonical_continuous_poll_iterations_v1(
    *,
    max_run_duration_seconds: float,
    wait_interval_seconds: float,
    max_cycles_per_run: int,
) -> int:
    """Upper bound on orchestrator loop poll() calls (anti-hang guard)."""
    duration = float(max_run_duration_seconds)
    interval = float(wait_interval_seconds)
    if not isfinite(duration) or duration <= 0:
        raise ValueError("RUN_DURATION_SECONDS_MUST_BE_FINITE_POSITIVE")
    if not isfinite(interval) or interval <= 0:
        raise ValueError("WAIT_INTERVAL_SECONDS_MUST_BE_POSITIVE")
    if (
        isinstance(max_cycles_per_run, bool)
        or not isinstance(max_cycles_per_run, int)
        or max_cycles_per_run <= 0
    ):
        raise ValueError("MAX_CYCLES_PER_RUN_MUST_BE_POSITIVE_INTEGER")
    return int(duration // interval) + int(max_cycles_per_run) + ANTI_HANG_POLL_ITERATION_MARGIN


def compute_worst_case_legitimate_shared_transport_charged_gets_v1(
    *,
    max_run_duration_seconds: float,
    wait_interval_seconds: float,
    max_cycles_per_run: int,
) -> int:
    """Charged attempts for the existing Product launcher, bootstrap and S6.

    Poll retries already consume the same finite poll count. Each S5 attempt
    collects at most the original pretrade GET set. This is not a rate limit,
    an in-flight deadline, or a budget for the full standing supervisor.
    """
    poll_cap = compute_max_canonical_continuous_poll_iterations_v1(
        max_run_duration_seconds=max_run_duration_seconds,
        wait_interval_seconds=wait_interval_seconds,
        max_cycles_per_run=max_cycles_per_run,
    )
    dynamic_per_poll = productive_s6_dynamic_wire_gets_per_poll_v1()
    return (
        PRODUCTIVE_SHARED_TRANSPORT_G17_CHARGED_GETS
        + PRODUCTIVE_COLD_BOOTSTRAP_WORST_CASE_CHARGED_GETS
        + poll_cap * dynamic_per_poll
        + max_cycles_per_run * productive_pretrade_wire_gets_per_decision_v1()
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
    "PRODUCTIVE_S6_DYNAMIC_INDEX_GETS_PER_POLL",
    "PRODUCTIVE_S6_DYNAMIC_MARK_GETS_PER_POLL",
    "PRODUCTIVE_SHARED_TRANSPORT_G17_CHARGED_GETS",
    "compute_max_canonical_continuous_poll_iterations_v1",
    "compute_productive_policy_governed_live_c1_shared_transport_max_request_count_v1",
    "compute_worst_case_legitimate_shared_transport_charged_gets_v1",
    "productive_s6_dynamic_wire_gets_per_poll_v1",
    "productive_pretrade_wire_gets_per_decision_v1",
]
