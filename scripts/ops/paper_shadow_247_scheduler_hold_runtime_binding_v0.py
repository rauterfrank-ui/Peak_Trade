"""Non-authorizing RUN_ID-scoped scheduler HOLD runtime binding for bounded 24h dry-run v0."""

from __future__ import annotations

import stat
from pathlib import Path
from typing import Any, Mapping

from scripts.ops import bounded_daemon_paper_shadow_24h_approval_v0 as contract_24h
from scripts.ops.bounded_daemon_paper_shadow_24h_approval_v0 import parse_machine_lines
from scripts.ops.paper_shadow_247_activation_authorization_v0 import (
    build_activation_authorization_v0,
)
from scripts.ops.paper_shadow_247_execution_prep_readiness_v0 import (
    build_execution_prep_readiness_v0,
)
from scripts.ops.paper_shadow_247_governance_outroot_clearance_v0 import (
    build_governance_outroot_clearance_v0,
    resolve_durable_run_outroot,
)

SCHEDULER_HOLD_RUNTIME_BINDING_SCHEMA_VERSION = "scheduler_hold_runtime_binding.v0"
BOUNDED_SCOPE = "bounded_24h_daemon_paper_shadow_dry_run_only"

ADAPTER_APPROVAL_PREFLIGHT_REL = Path("preflight/BOUNDED_ADAPTER_24H_EXECUTE_APPROVAL_RECORD_V0.md")
ADAPTER_APPROVAL_CLOSEOUT_REL = Path(
    "closeout/BOUNDED_ADAPTER_24H_EXECUTE_APPROVAL_RECORD_ARCHIVE_ONLY_V0.md"
)
CANONICAL_COMBINED_COMMAND_REL = Path(
    "commands/CANONICAL_COMBINED_PAPER_SHADOW_START_COMMAND_V0.sh"
)

CANONICAL_GUARD_EXIT = 76
FORBIDDEN_CANONICAL_TOKENS = (
    "start_testnet_now=true",
    "start_live_now=true",
    "broker_exchange_allowed=true",
)

REASON_VALID = (
    "RUN_ID-scoped scheduler HOLD runtime binding validated for bounded 24h "
    "Daemon Paper/Shadow dry-run only; does not clear global HOLD or authorize "
    "Testnet/Live/broker/exchange."
)
REASON_INVALID = (
    "Scheduler HOLD runtime binding validation failed; default HOLD_NO_PAPER_RUN remains in force."
)


def _read_allowlisted_file(outroot: Path, rel: Path) -> tuple[str | None, str | None]:
    path = outroot / rel
    if not path.is_file():
        return None, f"missing_allowlisted_file:{rel.as_posix()}"
    return path.read_text(encoding="utf-8"), None


def _validate_adapter_approval_records(
    outroot: Path,
    *,
    expected_run_id: str,
) -> list[str]:
    issues: list[str] = []
    for label, rel in (
        ("adapter_approval_preflight", ADAPTER_APPROVAL_PREFLIGHT_REL),
        ("adapter_approval_closeout", ADAPTER_APPROVAL_CLOSEOUT_REL),
    ):
        text, err = _read_allowlisted_file(outroot, rel)
        if err:
            issues.append(err)
            continue
        fields = parse_machine_lines(text or "")
        issues.extend(
            contract_24h.validate_approval_record(fields, approved_run_id=expected_run_id)
        )
        scope = fields.get("ADAPTER_APPROVAL_SCOPE", "").strip()
        if scope and scope != BOUNDED_SCOPE:
            issues.append(f"{label}:ADAPTER_APPROVAL_SCOPE_invalid")
        lowered = (text or "").lower()
        for key in contract_24h.FORBIDDEN_APPROVAL_TRUE:
            if fields.get(key, "false").lower() == "true":
                issues.append(f"{label}:forbidden_{key}=true")
        if "start_testnet_now=true" in lowered or "start_live_now=true" in lowered:
            issues.append(f"{label}:forbidden_testnet_or_live_token")
    return issues


def _validate_canonical_combined_command(outroot: Path, *, expected_run_id: str) -> list[str]:
    issues: list[str] = []
    path = outroot / CANONICAL_COMBINED_COMMAND_REL
    if not path.is_file():
        return [f"missing_allowlisted_file:{CANONICAL_COMBINED_COMMAND_REL.as_posix()}"]

    mode = path.stat().st_mode
    if mode & stat.S_IXUSR:
        issues.append("canonical_combined_command:executable_bit_set")
    if oct(mode & 0o777) != oct(stat.S_IRUSR | stat.S_IWUSR):
        issues.append("canonical_combined_command:chmod_not_600")

    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    if f"run_id={expected_run_id}".lower() not in lowered.replace('"', "").replace("'", ""):
        issues.append("canonical_combined_command:RUN_ID_binding_missing")
    if f"exit {CANONICAL_GUARD_EXIT}" not in text and f"exit {CANONICAL_GUARD_EXIT}\n" not in text:
        issues.append("canonical_combined_command:guard_exit_76_missing")
    for token in FORBIDDEN_CANONICAL_TOKENS:
        if token in lowered:
            issues.append(f"canonical_combined_command:forbidden_{token}")

    return issues


def build_scheduler_hold_runtime_binding_v0(
    durable_run_outroot: Path,
    *,
    expected_run_id: str,
) -> dict[str, Any]:
    """Validate scoped OUTROOT chain for scheduler runtime HOLD binding; non-authorizing."""

    outroot = resolve_durable_run_outroot(durable_run_outroot)
    validation_issues: list[str] = []

    governance = build_governance_outroot_clearance_v0(outroot, expected_run_id=expected_run_id)
    activation = build_activation_authorization_v0(
        outroot,
        expected_run_id=expected_run_id,
        governance_outroot_clearance_v0=governance,
    )
    execution_prep = build_execution_prep_readiness_v0(
        outroot,
        expected_run_id=expected_run_id,
        governance_outroot_clearance_v0=governance,
        activation_authorization_v0=activation,
    )

    if governance.get("valid") is not True:
        validation_issues.append("governance_outroot_clearance_not_valid")
    if activation.get("valid") is not True:
        validation_issues.append("activation_authorization_not_valid")
    if execution_prep.get("valid") is not True:
        validation_issues.append("execution_prep_readiness_not_valid")

    adapter_issues = _validate_adapter_approval_records(outroot, expected_run_id=expected_run_id)
    canonical_issues = _validate_canonical_combined_command(
        outroot, expected_run_id=expected_run_id
    )
    validation_issues.extend(adapter_issues)
    validation_issues.extend(canonical_issues)

    valid = len(validation_issues) == 0
    return {
        "schema_version": SCHEDULER_HOLD_RUNTIME_BINDING_SCHEMA_VERSION,
        "non_authorizing": True,
        "durable_run_outroot": str(outroot),
        "expected_run_id": expected_run_id,
        "binding_scope": BOUNDED_SCOPE,
        "valid": valid,
        "clearance_granted": valid,
        "governance_outroot_clearance_valid": governance.get("valid") is True,
        "activation_authorization_valid": activation.get("valid") is True,
        "execution_prep_readiness_valid": execution_prep.get("valid") is True,
        "adapter_execute_approval_valid": len(adapter_issues) == 0,
        "canonical_combined_command_valid": len(canonical_issues) == 0,
        "validation_issues": validation_issues,
        "permits_scheduler_runtime_paper_testnet_live": False,
        "permits_testnet_live_broker_exchange": False,
        "clears_global_hold_no_paper_run": False,
        "reason": REASON_VALID if valid else REASON_INVALID,
    }
