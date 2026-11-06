"""Disk-capacity preflight and evidence-growth bound checks (offline-safe)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.constants_v1 import (
    DISK_FREE_MINIMUM_BYTES_BEFORE,
    DISK_RESERVE_BYTES,
    MAX_EVIDENCE_BYTES,
    MAX_EVIDENCE_GROWTH_BYTES_PER_MINUTE,
)


def disk_free_bytes_v1(path: Path) -> int:
    usage = os.statvfs(str(path))
    return int(usage.f_bavail) * int(usage.f_frsize)


def evaluate_disk_capacity_preflight_v1(
    *,
    check_path: Path,
    free_bytes: int | None = None,
    minimum_bytes: int = DISK_FREE_MINIMUM_BYTES_BEFORE,
    reserve_bytes: int = DISK_RESERVE_BYTES,
    free_bytes_provider: Callable[[Path], int] | None = None,
) -> dict[str, Any]:
    path = Path(check_path)
    path.mkdir(parents=True, exist_ok=True)
    provider = free_bytes_provider or disk_free_bytes_v1
    free = int(free_bytes) if free_bytes is not None else int(provider(path))
    blockers: list[str] = []
    if free < int(minimum_bytes):
        blockers.append("DISK_PREFLIGHT_FAIL")
    runtime_pressure = free < int(reserve_bytes)
    return {
        "ok": not blockers,
        "blockers": blockers,
        "disk_free_bytes_before": free,
        "disk_free_minimum_bytes_before": int(minimum_bytes),
        "disk_reserve_bytes": int(reserve_bytes),
        "runtime_disk_pressure": bool(runtime_pressure),
        "check_path": str(path),
        "STEP5_SESSION_STARTED": False if blockers else None,
        "classification": "DISK_PREFLIGHT_FAIL" if blockers else "DISK_PREFLIGHT_PASS",
        "notes": [
            "FAIL_CLOSED_ON_PREFLIGHT_FAIL=true",
            "RUNTIME_DISK_PRESSURE_IF_FREE_LT_RESERVE=true",
        ],
    }


def evaluate_evidence_growth_bound_v1(
    *,
    evidence_bytes: int,
    evidence_growth_bytes_per_minute: float,
    max_evidence_bytes: int = MAX_EVIDENCE_BYTES,
    max_growth_bytes_per_minute: int = MAX_EVIDENCE_GROWTH_BYTES_PER_MINUTE,
) -> dict[str, Any]:
    blockers: list[str] = []
    if int(evidence_bytes) > int(max_evidence_bytes):
        blockers.append("EVIDENCE_GROWTH_BOUND_EXCEEDED_TOTAL")
    if float(evidence_growth_bytes_per_minute) > float(max_growth_bytes_per_minute):
        blockers.append("EVIDENCE_GROWTH_BOUND_EXCEEDED_RATE")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "evidence_bytes": int(evidence_bytes),
        "evidence_growth_rate": float(evidence_growth_bytes_per_minute),
        "max_evidence_bytes": int(max_evidence_bytes),
        "max_evidence_growth_bytes_per_minute": int(max_growth_bytes_per_minute),
        "classification": (
            "EVIDENCE_GROWTH_BOUND_EXCEEDED" if blockers else "EVIDENCE_GROWTH_WITHIN_BOUNDS"
        ),
    }


def prove_disk_and_evidence_bounds_offline_v1(*, check_path: Path) -> dict[str, Any]:
    preflight_ok = evaluate_disk_capacity_preflight_v1(
        check_path=check_path,
        free_bytes=DISK_FREE_MINIMUM_BYTES_BEFORE + 1,
    )
    preflight_fail = evaluate_disk_capacity_preflight_v1(
        check_path=check_path,
        free_bytes=DISK_FREE_MINIMUM_BYTES_BEFORE - 1,
    )
    growth_ok = evaluate_evidence_growth_bound_v1(
        evidence_bytes=1024,
        evidence_growth_bytes_per_minute=1024.0,
    )
    growth_fail = evaluate_evidence_growth_bound_v1(
        evidence_bytes=MAX_EVIDENCE_BYTES + 1,
        evidence_growth_bytes_per_minute=float(MAX_EVIDENCE_GROWTH_BYTES_PER_MINUTE + 1),
    )
    blockers: list[str] = []
    if not preflight_ok["ok"]:
        blockers.append("DISK_PREFLIGHT_OK_CASE_FAILED")
    if preflight_fail["ok"]:
        blockers.append("DISK_PREFLIGHT_FAIL_CASE_DID_NOT_FAIL")
    if not growth_ok["ok"]:
        blockers.append("EVIDENCE_GROWTH_OK_CASE_FAILED")
    if growth_fail["ok"]:
        blockers.append("EVIDENCE_GROWTH_FAIL_CASE_DID_NOT_FAIL")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "preflight_ok": preflight_ok,
        "preflight_fail": preflight_fail,
        "growth_ok": growth_ok,
        "growth_fail": growth_fail,
        "network_session_started": False,
    }
