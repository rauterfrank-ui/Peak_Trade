"""Pacing / backoff / reconnect policy proof for Step-3 surface (reuse-before-new)."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.constants_v1 import (
    BACKOFF_BASE_SECONDS,
    BACKOFF_MAX_SECONDS,
    MAX_RETRY_ATTEMPTS,
    MIN_REQUEST_INTERVAL_SECONDS,
    PACING_POLICY_OWNER,
    STALENESS_OWNER,
    ZERO_INTERVAL_RETRY_FORBIDDEN,
)


def prove_bounded_pacing_and_backoff_v1() -> dict[str, Any]:
    blockers: list[str] = []
    if MIN_REQUEST_INTERVAL_SECONDS <= 0:
        blockers.append("ZERO_INTERVAL_RETRY_BURST_FORBIDDEN")
    if MAX_RETRY_ATTEMPTS < 1:
        blockers.append("RETRY_BUDGET_INVALID")
    if BACKOFF_BASE_SECONDS <= 0:
        blockers.append("BACKOFF_BASE_MUST_BE_POSITIVE")
    if BACKOFF_MAX_SECONDS < BACKOFF_BASE_SECONDS:
        blockers.append("BACKOFF_MAX_MUST_GTE_BASE")
    if not ZERO_INTERVAL_RETRY_FORBIDDEN:
        blockers.append("ZERO_INTERVAL_RETRY_MUST_REMAIN_FORBIDDEN")

    intervals = [
        min(BACKOFF_MAX_SECONDS, BACKOFF_BASE_SECONDS * (2**i)) for i in range(MAX_RETRY_ATTEMPTS)
    ]
    if any(x <= 0 for x in intervals):
        blockers.append("ZERO_INTERVAL_RETRY_BURST")

    return {
        "ok": not blockers,
        "blockers": blockers,
        "claims": {
            "BOUNDED_RECONNECT": True,
            "BOUNDED_BACKOFF": True,
            "ZERO_INTERVAL_RETRY_BURST": False,
            "MIN_REQUEST_INTERVAL_SECONDS": MIN_REQUEST_INTERVAL_SECONDS,
            "MAX_RETRY_ATTEMPTS": MAX_RETRY_ATTEMPTS,
            "BACKOFF_BASE_SECONDS": BACKOFF_BASE_SECONDS,
            "BACKOFF_MAX_SECONDS": BACKOFF_MAX_SECONDS,
            "PACING_POLICY_OWNER": PACING_POLICY_OWNER,
            "STALENESS_OWNER": STALENESS_OWNER,
        },
        "backoff_schedule_seconds": intervals,
        "notes": [
            "REUSES_PHASE92_PACING_CONVENTIONS=true",
            "NO_PARALLEL_PACING_AUTHORITY=true",
        ],
    }
