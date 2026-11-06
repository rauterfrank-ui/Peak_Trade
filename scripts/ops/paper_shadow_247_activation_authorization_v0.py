"""Non-authorizing durable OUTROOT activation authorization evidence for preflight reporter v0."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from scripts.ops.bounded_daemon_paper_shadow_24h_approval_v0 import parse_machine_lines
from scripts.ops.paper_shadow_247_governance_outroot_clearance_v0 import (
    resolve_durable_run_outroot,
)

ACTIVATION_AUTHORIZATION_SCHEMA_VERSION = "activation_authorization.v0"

ACTIVATION_PREFLIGHT_REL = Path("preflight/ACTIVATION_AUTHORIZATION_OPERATOR_RECORD_V0.md")
ACTIVATION_CLOSEOUT_REL = Path(
    "closeout/ACTIVATION_AUTHORIZATION_OPERATOR_RECORD_ARCHIVE_ONLY_V0.md"
)

REQUIRED_ACTIVATION_VALUES = {
    "ACTIVATION_AUTHORIZATION_OPERATOR_RECORD_CREATED": "true",
    "ACTIVATION_AUTHORIZATION_DONE": "true_FOR_RUN_ID_ONLY",
    "PAPER_LANE_ACTIVATION_AUTHORIZED": "true_FOR_RUN_ID_ONLY",
    "SHADOW_LANE_ACTIVATION_AUTHORIZED": "true_FOR_RUN_ID_ONLY",
    "SCHEDULER_ACTIVATION_AUTHORIZED": "true_FOR_RUN_ID_ONLY",
    "AUTHORIZATION_SCOPE": "bounded_24h_daemon_paper_shadow_dry_run_only",
    "RUNTIME_STARTED": "false",
    "READY_TO_START_RUN_NOW": "false",
    "TESTNET_STARTED": "false",
    "LIVE_STARTED": "false",
}

REASON_VALID = (
    "Scoped activation authorization record validated; "
    "does not authorize runtime or change BLOCKED status."
)
REASON_INVALID = (
    "Activation authorization validation failed; "
    "does not authorize runtime or change BLOCKED status."
)


def _read_activation_file(outroot: Path, rel: Path) -> tuple[str | None, str | None]:
    path = outroot / rel
    if not path.is_file():
        return None, f"missing_allowlisted_file:{rel.as_posix()}"
    return path.read_text(encoding="utf-8"), None


def _validate_activation_record(
    fields: dict[str, str],
    *,
    expected_run_id: str,
    label: str,
) -> list[str]:
    issues: list[str] = []
    run_id = fields.get("RUN_ID", "").strip()
    if not run_id:
        issues.append(f"{label}:missing_RUN_ID")
    elif run_id != expected_run_id:
        issues.append(f"{label}:RUN_ID_mismatch")

    for key, expected in REQUIRED_ACTIVATION_VALUES.items():
        actual = fields.get(key, "").strip()
        if actual != expected:
            issues.append(f"{label}:{key}_invalid")

    return issues


def build_activation_authorization_v0(
    durable_run_outroot: Path,
    *,
    expected_run_id: str,
    governance_outroot_clearance_v0: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Validate scoped OUTROOT activation authorization; non-authorizing, fail-closed."""

    outroot = resolve_durable_run_outroot(durable_run_outroot)
    validation_issues: list[str] = []

    governance_valid = (
        isinstance(governance_outroot_clearance_v0, Mapping)
        and governance_outroot_clearance_v0.get("valid") is True
    )
    if not governance_valid:
        validation_issues.append("governance_outroot_clearance_not_valid")

    preflight_text, preflight_err = _read_activation_file(outroot, ACTIVATION_PREFLIGHT_REL)
    if preflight_err:
        validation_issues.append(preflight_err)
    closeout_text, closeout_err = _read_activation_file(outroot, ACTIVATION_CLOSEOUT_REL)
    if closeout_err:
        validation_issues.append(closeout_err)

    preflight_fields = parse_machine_lines(preflight_text or "")
    closeout_fields = parse_machine_lines(closeout_text or "")

    validation_issues.extend(
        _validate_activation_record(
            preflight_fields, expected_run_id=expected_run_id, label="activation_preflight"
        )
    )
    validation_issues.extend(
        _validate_activation_record(
            closeout_fields, expected_run_id=expected_run_id, label="activation_closeout"
        )
    )

    for key in REQUIRED_ACTIVATION_VALUES:
        if preflight_fields.get(key) != closeout_fields.get(key):
            validation_issues.append(f"activation_records:{key}_preflight_closeout_mismatch")

    valid = len(validation_issues) == 0
    return {
        "schema_version": ACTIVATION_AUTHORIZATION_SCHEMA_VERSION,
        "non_authorizing": True,
        "durable_run_outroot": str(outroot),
        "expected_run_id": expected_run_id,
        "valid": valid,
        "governance_outroot_clearance_valid": governance_valid,
        "activation_authorization_done": preflight_fields.get("ACTIVATION_AUTHORIZATION_DONE"),
        "authorization_scope": preflight_fields.get("AUTHORIZATION_SCOPE"),
        "paper_lane_activation_authorized": preflight_fields.get("PAPER_LANE_ACTIVATION_AUTHORIZED")
        == "true_FOR_RUN_ID_ONLY",
        "shadow_lane_activation_authorized": preflight_fields.get(
            "SHADOW_LANE_ACTIVATION_AUTHORIZED"
        )
        == "true_FOR_RUN_ID_ONLY",
        "scheduler_activation_authorized": preflight_fields.get("SCHEDULER_ACTIVATION_AUTHORIZED")
        == "true_FOR_RUN_ID_ONLY",
        "validation_issues": validation_issues,
        "permits_scheduler_runtime_paper_testnet_live": False,
        "reason": REASON_VALID if valid else REASON_INVALID,
    }
