"""Repo-native Testnet wall-clock duration evidence contract (v0).

Offline fail-closed evaluator for future Testnet execute duration evidence.
Does not authorize Testnet execute, network access, credentials, or runtime start.
Charter: testnet_wallclock_duration_guard_external_charter_no_run_v0_20260603T182859Z
"""

from __future__ import annotations

from typing import Any

from src.ops.wallclock_session_evidence_v0 import evaluate_wallclock_evidence_fields

PACKAGE_MARKER = "TESTNET_WALLCLOCK_DURATION_EVIDENCE_CONTRACT_V0=true"
CLASS4_SCOPED_EXCEPTION_MARKER = "TESTNET_WALLCLOCK_DURATION_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
CHARTER_BUNDLE_SUFFIX = (
    "testnet_wallclock_duration_guard_external_charter_no_run_v0_20260603T182859Z"
)

REQUIRED_WALLCLOCK_FIELD_NAMES: tuple[str, ...] = (
    "planned_duration_seconds",
    "min_required_wall_clock_seconds",
    "start_wall_clock_iso",
    "end_wall_clock_iso",
    "start_monotonic_seconds",
    "end_monotonic_seconds",
    "elapsed_wall_clock_seconds",
    "elapsed_monotonic_seconds",
    "wall_clock_slack_seconds",
    "duration_proven",
    "duration_evidence_valid",
    "early_exit_detected",
    "early_exit_reason",
    "invalid_if_elapsed_below_min",
)


def evaluate_wallclock_duration_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    """Fail-closed evaluator mirroring charter rules R1–R8 (offline, no I/O)."""
    result: dict[str, Any] = {
        "duration_proven": False,
        "duration_evidence_valid": False,
        "invalid_if_elapsed_below_min": True,
        "fail_reasons": [],
    }

    projection_only = evidence.get("projection_ready") is True and "duration_proven" not in evidence
    if projection_only:
        result["fail_reasons"].append("projection_ready alone is not duration proof (R4)")

    simulation_forbidden = evidence.get("simulation_forbidden")
    real_sleep_used = evidence.get("real_sleep_used")
    if simulation_forbidden is True and real_sleep_used is False:
        result["fail_reasons"].append("simulation_forbidden but real_sleep_used=false (R6)")

    field_eval = evaluate_wallclock_evidence_fields(evidence)
    result["fail_reasons"].extend(field_eval["fail_reasons"])

    if not result["fail_reasons"]:
        result["duration_evidence_valid"] = True
        result["duration_proven"] = True

    return result
