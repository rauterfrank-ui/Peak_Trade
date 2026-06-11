"""Paper-L2 120min hold-binding approval contract v0.

Non-authorizing: validates machine-line approval records and hold-binding outroot only.
Does not clear global HOLD, start runtime, or grant Testnet/Live/broker authority.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from scripts.ops.primary_evidence_retention_v0 import is_under_tmp

CONTRACT_PROFILE = "paper_l2_120min_hold_binding_v0"
BINDING_SCOPE = "paper_l2_120min_bounded_evidence_only"

L2_DURATION_SECONDS = 7200

REQUIRED_APPROVAL = {
    "APPROVE_EXECUTE_PAPER_ONLY_120MIN_NOW": "true",
    "START_PAPER_NOW": "true",
}

FORBIDDEN_APPROVAL_TRUE = frozenset(
    {
        "START_SHADOW_NOW",
        "START_TESTNET_NOW",
        "START_SUPERVISOR_NOW",
        "START_LIVE_NOW",
        "LIVE_ALLOWED",
        "BROKER_EXCHANGE_ALLOWED",
    }
)


def validate_paper_duration_seconds(duration_seconds: int) -> list[str]:
    if duration_seconds != L2_DURATION_SECONDS:
        return [f"duration-seconds must be {L2_DURATION_SECONDS} for {CONTRACT_PROFILE}"]
    return []


def resolve_hold_binding_outroot(fields: Mapping[str, str]) -> tuple[Path | None, list[str]]:
    raw = fields.get("HOLD_BINDING_OUTROOT", "").strip()
    if not raw:
        return None, ["approval record missing: HOLD_BINDING_OUTROOT"]
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        return None, [f"HOLD_BINDING_OUTROOT must exist as directory: {path}"]
    if is_under_tmp(path):
        return None, ["HOLD_BINDING_OUTROOT must be outside /tmp"]
    return path, []


def validate_approval_record(
    fields: Mapping[str, str],
    *,
    approved_run_id: str,
) -> list[str]:
    issues: list[str] = []
    profile = fields.get("CONTRACT_PROFILE", "").strip()
    if profile and profile != CONTRACT_PROFILE:
        issues.append(f"CONTRACT_PROFILE must be {CONTRACT_PROFILE!r}")
    for key, expected in REQUIRED_APPROVAL.items():
        if fields.get(key, "").lower() != expected:
            issues.append(f"approval record missing or invalid: {key}={expected}")
    record_run_id = fields.get("APPROVED_RUN_ID", "").strip()
    if not record_run_id:
        issues.append("approval record missing: APPROVED_RUN_ID")
    elif record_run_id != approved_run_id:
        issues.append(
            f"APPROVED_RUN_ID mismatch: expected {approved_run_id!r}, got {record_run_id!r}"
        )
    for key in FORBIDDEN_APPROVAL_TRUE:
        if fields.get(key, "false").lower() == "true":
            issues.append(f"approval record forbids {key}=true")
    _, outroot_issues = resolve_hold_binding_outroot(fields)
    issues.extend(outroot_issues)
    return issues


def validate_scheduler_hold_runtime_binding_outroot(
    outroot: Path,
    *,
    expected_run_id: str,
) -> list[str]:
    from scripts.ops.paper_shadow_247_scheduler_hold_runtime_binding_v0 import (
        build_scheduler_hold_runtime_binding_v0,
    )

    binding = build_scheduler_hold_runtime_binding_v0(
        outroot,
        expected_run_id=expected_run_id,
    )
    if binding.get("valid") is True:
        return []
    raw_issues = binding.get("validation_issues")
    if isinstance(raw_issues, list) and raw_issues:
        return [f"scheduler_hold_runtime_binding:{issue}" for issue in raw_issues]
    return ["scheduler_hold_runtime_binding:invalid"]
