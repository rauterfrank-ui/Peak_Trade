"""Non-authorizing durable OUTROOT execution-prep readiness evidence for preflight reporter v0."""

from __future__ import annotations

import stat
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.bounded_daemon_paper_shadow_24h_approval_v0 import parse_machine_lines
from scripts.ops.paper_shadow_247_governance_outroot_clearance_v0 import (
    resolve_durable_run_outroot,
)

EXECUTION_PREP_READINESS_SCHEMA_VERSION = "execution_prep_readiness.v0"

EXECUTION_PREP_PREFLIGHT_REL = Path("preflight/EXECUTION_PREP_OPERATOR_RECORD_V0.md")
EXECUTION_PREP_CLOSEOUT_REL = Path("closeout/EXECUTION_PREP_OPERATOR_RECORD_ARCHIVE_ONLY_V0.md")
NON_EXECUTING_COMMAND_REL = Path("commands/NON_EXECUTING_START_COMMAND_V0.sh")
EXECUTING_COMMAND_REL = Path("commands/EXECUTING_START_COMMAND_V0.sh")

REQUIRED_EXECUTION_PREP_VALUES = {
    "EXECUTION_PREP_OPERATOR_RECORD_CREATED": "true",
    "EXECUTION_PREP_AUTHORIZED": "true_FOR_RUN_ID_ONLY",
    "EXECUTION_PREP_SCOPE": "bounded_24h_daemon_paper_shadow_dry_run_only",
    "EXECUTION_PREP_ALLOWED_NEXT_STEP": "reporter_binding_pr_only",
    "NO_ACTIVE_RUN_SNAPSHOT_VALID": "true",
    "COMMAND_GUARDS_PRESERVED": "true",
    "RUNTIME_STARTED": "false",
    "READY_TO_START_RUN_NOW": "false",
    "TESTNET_STARTED": "false",
    "LIVE_STARTED": "false",
    "ACTIVE_RUNS_DETECTED": "false",
}

REASON_VALID = (
    "Scoped execution-prep readiness validated; "
    "does not authorize runtime or change BLOCKED status."
)
REASON_INVALID = (
    "Execution-prep readiness validation failed; "
    "does not authorize runtime or change BLOCKED status."
)


def _read_execution_prep_file(outroot: Path, rel: Path) -> tuple[str | None, str | None]:
    path = outroot / rel
    if not path.is_file():
        return None, f"missing_allowlisted_file:{rel.as_posix()}"
    return path.read_text(encoding="utf-8"), None


def _validate_execution_prep_record(
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

    for key, expected in REQUIRED_EXECUTION_PREP_VALUES.items():
        actual = fields.get(key, "").strip()
        if actual != expected:
            issues.append(f"{label}:{key}_invalid")

    return issues


def _validate_command_guards(outroot: Path) -> list[str]:
    issues: list[str] = []
    for rel in (NON_EXECUTING_COMMAND_REL, EXECUTING_COMMAND_REL):
        path = outroot / rel
        if not path.is_file():
            issues.append(f"command_guard:missing_{rel.as_posix()}")
            continue
        if path.stat().st_mode & stat.S_IXUSR:
            issues.append(f"command_guard:executable_{rel.as_posix()}")
    return issues


def build_execution_prep_readiness_v0(
    durable_run_outroot: Path,
    *,
    expected_run_id: str,
    governance_outroot_clearance_v0: Mapping[str, Any] | None,
    activation_authorization_v0: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Validate scoped OUTROOT execution-prep readiness; non-authorizing, fail-closed."""

    outroot = resolve_durable_run_outroot(durable_run_outroot)
    validation_issues: list[str] = []

    governance_valid = (
        isinstance(governance_outroot_clearance_v0, Mapping)
        and governance_outroot_clearance_v0.get("valid") is True
    )
    if not governance_valid:
        validation_issues.append("governance_outroot_clearance_not_valid")

    activation_valid = (
        isinstance(activation_authorization_v0, Mapping)
        and activation_authorization_v0.get("valid") is True
    )
    if not activation_valid:
        validation_issues.append("activation_authorization_not_valid")

    preflight_text, preflight_err = _read_execution_prep_file(outroot, EXECUTION_PREP_PREFLIGHT_REL)
    if preflight_err:
        validation_issues.append(preflight_err)
    closeout_text, closeout_err = _read_execution_prep_file(outroot, EXECUTION_PREP_CLOSEOUT_REL)
    if closeout_err:
        validation_issues.append(closeout_err)

    preflight_fields = parse_machine_lines(preflight_text or "")
    closeout_fields = parse_machine_lines(closeout_text or "")

    validation_issues.extend(
        _validate_execution_prep_record(
            preflight_fields, expected_run_id=expected_run_id, label="execution_prep_preflight"
        )
    )
    validation_issues.extend(
        _validate_execution_prep_record(
            closeout_fields, expected_run_id=expected_run_id, label="execution_prep_closeout"
        )
    )

    for key in REQUIRED_EXECUTION_PREP_VALUES:
        if preflight_fields.get(key) != closeout_fields.get(key):
            validation_issues.append(f"execution_prep_records:{key}_preflight_closeout_mismatch")

    validation_issues.extend(_validate_command_guards(outroot))

    valid = len(validation_issues) == 0
    return {
        "schema_version": EXECUTION_PREP_READINESS_SCHEMA_VERSION,
        "non_authorizing": True,
        "durable_run_outroot": str(outroot),
        "expected_run_id": expected_run_id,
        "valid": valid,
        "governance_outroot_clearance_valid": governance_valid,
        "activation_authorization_valid": activation_valid,
        "execution_prep_authorized": preflight_fields.get("EXECUTION_PREP_AUTHORIZED")
        == "true_FOR_RUN_ID_ONLY",
        "execution_prep_scope": preflight_fields.get("EXECUTION_PREP_SCOPE"),
        "execution_prep_allowed_next_step": preflight_fields.get(
            "EXECUTION_PREP_ALLOWED_NEXT_STEP"
        ),
        "command_guards_preserved": preflight_fields.get("COMMAND_GUARDS_PRESERVED") == "true",
        "no_active_run_snapshot_valid": preflight_fields.get("NO_ACTIVE_RUN_SNAPSHOT_VALID")
        == "true",
        "validation_issues": validation_issues,
        "permits_scheduler_runtime_paper_testnet_live": False,
        "reason": REASON_VALID if valid else REASON_INVALID,
    }
