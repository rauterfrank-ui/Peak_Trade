"""Repo-native wall-clock session evidence for Testnet sessions (v0).

Emits charter-aligned WALLCLOCK_EVIDENCE.json for bounded session closeout.
Does not authorize Testnet execute; RUN_TESTNET_SESSION_ALLOWED_NOW remains false.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

PACKAGE_MARKER = "RUNTIME_WALLCLOCK_SESSION_EVIDENCE_V0=true"
WALLCLOCK_EVIDENCE_FILENAME = "WALLCLOCK_EVIDENCE.json"
EVIDENCE_SOURCE_REPO_NATIVE = "repo_native_session"
EVIDENCE_SOURCE_SHADOW_BOUNDED = "shadow_bounded_dry_run"
DEFAULT_WALL_CLOCK_SLACK_SECONDS = 60
INVALID_IF_ELAPSED_BELOW_MIN = True


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _parse_utc_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def _monotonic_tolerance(planned_duration_seconds: float) -> float:
    return 5.0 if planned_duration_seconds > 60 else 2.0


def evaluate_wallclock_evidence_fields(evidence: dict[str, Any]) -> dict[str, Any]:
    """Fail-closed wall-clock evaluation (mirrors tests/ops wall-clock contract R1–R8)."""
    result: dict[str, Any] = {
        "duration_proven": False,
        "duration_evidence_valid": False,
        "fail_reasons": [],
    }

    if evidence.get("invalid_if_elapsed_below_min") is not True:
        result["fail_reasons"].append("invalid_if_elapsed_below_min must be true")

    planned = evidence.get("planned_duration_seconds")
    elapsed_wall = evidence.get("elapsed_wall_clock_seconds")
    elapsed_mono = evidence.get("elapsed_monotonic_seconds")
    min_required = evidence.get("min_required_wall_clock_seconds")
    max_acceptable = evidence.get("max_acceptable_wall_clock_seconds")
    start_iso = evidence.get("start_wall_clock_iso")
    end_iso = evidence.get("end_wall_clock_iso")
    early_exit = evidence.get("early_exit_detected")
    early_reason = evidence.get("early_exit_reason")

    if not start_iso or not end_iso:
        result["fail_reasons"].append("missing start/end wall-clock timestamps (R2)")

    if planned is None or elapsed_wall is None:
        result["fail_reasons"].append(
            "planned_duration_seconds and elapsed_wall_clock_seconds required (R7)"
        )
    elif planned > 0 and min_required is not None and elapsed_wall < min_required:
        result["fail_reasons"].append("elapsed below min_required_wall_clock_seconds (R1)")

    if (
        elapsed_wall is not None
        and elapsed_mono is not None
        and planned is not None
        and abs(elapsed_wall - elapsed_mono) > _monotonic_tolerance(float(planned))
    ):
        result["fail_reasons"].append("wall-clock vs monotonic drift exceeds tolerance (R3)")

    if early_exit is True and not early_reason:
        result["fail_reasons"].append("early_exit_detected without early_exit_reason (R5)")

    if (
        early_exit is True
        and elapsed_wall is not None
        and min_required is not None
        and elapsed_wall < min_required
    ):
        result["fail_reasons"].append("early exit before min_required elapsed (R5)")

    if max_acceptable is not None and elapsed_wall is not None and elapsed_wall > max_acceptable:
        result["fail_reasons"].append("elapsed exceeds max_acceptable_wall_clock_seconds (R8)")

    if not result["fail_reasons"]:
        result["duration_evidence_valid"] = True
        result["duration_proven"] = True

    return result


def bounds_from_planned_duration(
    planned_duration_seconds: int,
    wall_clock_slack_seconds: int = DEFAULT_WALL_CLOCK_SLACK_SECONDS,
) -> dict[str, int]:
    return {
        "planned_duration_seconds": planned_duration_seconds,
        "min_required_wall_clock_seconds": max(
            0, planned_duration_seconds - wall_clock_slack_seconds
        ),
        "max_acceptable_wall_clock_seconds": planned_duration_seconds + wall_clock_slack_seconds,
        "wall_clock_slack_seconds": wall_clock_slack_seconds,
    }


@dataclass
class WallClockSessionTracker:
    """Tracks bounded session wall-clock for repo-native evidence emission."""

    planned_duration_seconds: int
    wall_clock_slack_seconds: int
    start_wall_clock_iso: str
    start_monotonic_seconds: float

    @classmethod
    def begin(
        cls,
        planned_duration_seconds: int,
        *,
        wall_clock_slack_seconds: int = DEFAULT_WALL_CLOCK_SLACK_SECONDS,
        start_wall_clock_iso: Optional[str] = None,
        start_monotonic_seconds: Optional[float] = None,
    ) -> WallClockSessionTracker:
        import time

        return cls(
            planned_duration_seconds=planned_duration_seconds,
            wall_clock_slack_seconds=wall_clock_slack_seconds,
            start_wall_clock_iso=start_wall_clock_iso or _utc_iso_now(),
            start_monotonic_seconds=(
                start_monotonic_seconds if start_monotonic_seconds is not None else time.monotonic()
            ),
        )

    def finalize(
        self,
        *,
        early_exit_detected: bool = False,
        early_exit_reason: str = "",
        end_wall_clock_iso: Optional[str] = None,
        end_monotonic_seconds: Optional[float] = None,
    ) -> dict[str, Any]:
        import time

        end_iso = end_wall_clock_iso or _utc_iso_now()
        end_mono = end_monotonic_seconds if end_monotonic_seconds is not None else time.monotonic()
        elapsed_mono = round(end_mono - self.start_monotonic_seconds, 6)
        elapsed_wall = round(
            (_parse_utc_iso(end_iso) - _parse_utc_iso(self.start_wall_clock_iso)).total_seconds(),
            6,
        )

        evidence: dict[str, Any] = {
            **bounds_from_planned_duration(
                self.planned_duration_seconds, self.wall_clock_slack_seconds
            ),
            "start_wall_clock_iso": self.start_wall_clock_iso,
            "end_wall_clock_iso": end_iso,
            "start_monotonic_seconds": self.start_monotonic_seconds,
            "end_monotonic_seconds": end_mono,
            "elapsed_wall_clock_seconds": elapsed_wall,
            "elapsed_monotonic_seconds": elapsed_mono,
            "early_exit_detected": early_exit_detected,
            "early_exit_reason": early_exit_reason,
            "invalid_if_elapsed_below_min": INVALID_IF_ELAPSED_BELOW_MIN,
            "evidence_source": EVIDENCE_SOURCE_REPO_NATIVE,
            "emitter_artifact_filename": WALLCLOCK_EVIDENCE_FILENAME,
            "real_sleep_used": True,
            "simulation_forbidden": True,
        }

        evaluation = evaluate_wallclock_evidence_fields(evidence)
        evidence["duration_proven"] = evaluation["duration_proven"]
        evidence["duration_evidence_valid"] = evaluation["duration_evidence_valid"]
        if evaluation["fail_reasons"]:
            evidence["wallclock_fail_reasons"] = evaluation["fail_reasons"]
        return evidence


def build_wallclock_evidence_from_manifest_fields(
    *,
    utc_started: str,
    utc_completed: str,
    duration_minutes: int,
    start_monotonic_seconds: float,
    end_monotonic_seconds: float,
    early_exit_detected: bool = False,
    early_exit_reason: str = "",
    evidence_source: str = EVIDENCE_SOURCE_SHADOW_BOUNDED,
    real_sleep_used: bool = False,
) -> dict[str, Any]:
    """Derive charter-aligned wall-clock evidence from bounded session manifest time fields."""
    planned = int(duration_minutes) * 60
    bounds = bounds_from_planned_duration(planned)
    elapsed_wall = round(
        (_parse_utc_iso(utc_completed) - _parse_utc_iso(utc_started)).total_seconds(),
        6,
    )
    elapsed_mono = round(end_monotonic_seconds - start_monotonic_seconds, 6)
    evidence: dict[str, Any] = {
        **bounds,
        "start_wall_clock_iso": utc_started,
        "end_wall_clock_iso": utc_completed,
        "start_monotonic_seconds": start_monotonic_seconds,
        "end_monotonic_seconds": end_monotonic_seconds,
        "elapsed_wall_clock_seconds": elapsed_wall,
        "elapsed_monotonic_seconds": elapsed_mono,
        "early_exit_detected": early_exit_detected,
        "early_exit_reason": early_exit_reason,
        "invalid_if_elapsed_below_min": INVALID_IF_ELAPSED_BELOW_MIN,
        "evidence_source": evidence_source,
        "emitter_artifact_filename": WALLCLOCK_EVIDENCE_FILENAME,
        "real_sleep_used": real_sleep_used,
        "simulation_forbidden": False,
    }
    evaluation = evaluate_wallclock_evidence_fields(evidence)
    evidence["duration_proven"] = evaluation["duration_proven"]
    evidence["duration_evidence_valid"] = evaluation["duration_evidence_valid"]
    if evaluation["fail_reasons"]:
        evidence["wallclock_fail_reasons"] = evaluation["fail_reasons"]
    return evidence


def write_wallclock_evidence(path: Path, evidence: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
