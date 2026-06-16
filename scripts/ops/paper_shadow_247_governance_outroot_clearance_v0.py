"""Non-authorizing durable OUTROOT governance clearance evidence for preflight reporter v0."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.ops.bounded_daemon_paper_shadow_24h_approval_v0 import parse_machine_lines

GOVERNANCE_OUTROOT_CLEARANCE_SCHEMA_VERSION = "governance_outroot_clearance.v0"

GOVERNANCE_PREFLIGHT_REL = Path("preflight/GOVERNANCE_HOLD_CLEARANCE_OPERATOR_RECORD_V0.md")
GOVERNANCE_CLOSEOUT_REL = Path(
    "closeout/GOVERNANCE_HOLD_CLEARANCE_OPERATOR_RECORD_ARCHIVE_ONLY_V0.md"
)
PAPER_STAGING_BINDING_REL = Path("staging/PAPER_STAGING_BINDING_V0.md")
SHADOW_STAGING_BINDING_REL = Path("staging/SHADOW_STAGING_BINDING_V0.md")
STAGING_BRIDGE_CLOSEOUT_REL = Path(
    "closeout/TMP_STAGING_DURABLE_OUTROOT_BRIDGE_MATERIALIZATION_ARCHIVE_ONLY_V0.md"
)

ALLOWLIST_REL_PATHS = (
    GOVERNANCE_PREFLIGHT_REL,
    GOVERNANCE_CLOSEOUT_REL,
    PAPER_STAGING_BINDING_REL,
    SHADOW_STAGING_BINDING_REL,
    STAGING_BRIDGE_CLOSEOUT_REL,
)

REQUIRED_GOVERNANCE_VALUES = {
    "HOLD_CLEARANCE_DONE": "true_FOR_RUN_ID_ONLY",
    "HOLD_CLEARANCE_SCOPE": "bounded_24h_daemon_paper_shadow_dry_run_only",
    "GOVERNANCE_HOLD_CLEARANCE_OPERATOR_RECORD_CREATED": "true",
    "RUNTIME_STARTED": "false",
    "READY_TO_START_RUN_NOW": "false",
    "STAGING_BRIDGE_MATERIALIZED": "true",
}

REASON_VALID = (
    "OUTROOT governance clearance validated for scoped RUN_ID only; "
    "does not authorize runtime or clear global HOLD."
)
REASON_INVALID = (
    "OUTROOT governance clearance validation failed; "
    "does not authorize runtime or clear global HOLD."
)


def resolve_durable_run_outroot(durable_run_outroot: Path) -> Path:
    """Resolve OUTROOT directory; raise if not a readable directory."""

    root = durable_run_outroot.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"durable run outroot is not a directory: {durable_run_outroot}")
    return root


def _read_allowlisted_file(outroot: Path, rel: Path) -> tuple[str | None, str | None]:
    path = outroot / rel
    if not path.is_file():
        return None, f"missing_allowlisted_file:{rel.as_posix()}"
    return path.read_text(encoding="utf-8"), None


def _validate_governance_record(
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

    for key, expected in REQUIRED_GOVERNANCE_VALUES.items():
        actual = fields.get(key, "").strip()
        if actual != expected:
            issues.append(f"{label}:{key}_invalid")

    return issues


def _validate_staging_binding(
    text: str | None,
    *,
    expected_run_id: str,
    lane: str,
    label: str,
) -> tuple[str | None, list[str]]:
    issues: list[str] = []
    if text is None:
        return None, [f"{label}:missing"]

    fields = parse_machine_lines(text)
    if fields.get("LANE") != lane:
        issues.append(f"{label}:LANE_mismatch")
    if fields.get("RUN_ID") != expected_run_id:
        issues.append(f"{label}:RUN_ID_mismatch")
    if fields.get("EMPTY_LAYOUT_ONLY") != "true":
        issues.append(f"{label}:EMPTY_LAYOUT_ONLY_not_true")
    if fields.get("RUNTIME_STARTED") != "false":
        issues.append(f"{label}:RUNTIME_STARTED_not_false")

    staging_root = fields.get("STAGING_ROOT", "").strip()
    if not staging_root:
        issues.append(f"{label}:missing_STAGING_ROOT")
    elif not staging_root.startswith("/tmp/peak_trade_"):
        issues.append(f"{label}:STAGING_ROOT_not_under_tmp_peak_trade")
    elif not Path(staging_root).is_dir():
        issues.append(f"{label}:STAGING_ROOT_not_on_disk")

    return staging_root or None, issues


def _validate_bridge_closeout(text: str | None) -> list[str]:
    if text is None:
        return ["bridge_closeout:missing"]
    issues: list[str] = []
    for marker in ("STAGING_BRIDGE_MATERIALIZED=true", "EMPTY_LAYOUT_ONLY=true"):
        if marker not in text:
            issues.append(f"bridge_closeout:missing_{marker}")
    return issues


def build_governance_outroot_clearance_v0(
    durable_run_outroot: Path,
    *,
    expected_run_id: str,
) -> dict[str, Any]:
    """Validate scoped OUTROOT governance evidence; non-authorizing, fail-closed."""

    outroot = resolve_durable_run_outroot(durable_run_outroot)
    validation_issues: list[str] = []

    preflight_text, preflight_err = _read_allowlisted_file(outroot, GOVERNANCE_PREFLIGHT_REL)
    if preflight_err:
        validation_issues.append(preflight_err)
    closeout_text, closeout_err = _read_allowlisted_file(outroot, GOVERNANCE_CLOSEOUT_REL)
    if closeout_err:
        validation_issues.append(closeout_err)
    paper_text, paper_err = _read_allowlisted_file(outroot, PAPER_STAGING_BINDING_REL)
    if paper_err:
        validation_issues.append(paper_err)
    shadow_text, shadow_err = _read_allowlisted_file(outroot, SHADOW_STAGING_BINDING_REL)
    if shadow_err:
        validation_issues.append(shadow_err)
    bridge_text, bridge_err = _read_allowlisted_file(outroot, STAGING_BRIDGE_CLOSEOUT_REL)
    if bridge_err:
        validation_issues.append(bridge_err)

    preflight_fields = parse_machine_lines(preflight_text or "")
    closeout_fields = parse_machine_lines(closeout_text or "")

    validation_issues.extend(
        _validate_governance_record(
            preflight_fields, expected_run_id=expected_run_id, label="governance_preflight"
        )
    )
    validation_issues.extend(
        _validate_governance_record(
            closeout_fields, expected_run_id=expected_run_id, label="governance_closeout"
        )
    )

    for key in REQUIRED_GOVERNANCE_VALUES:
        if preflight_fields.get(key) != closeout_fields.get(key):
            validation_issues.append(f"governance_records:{key}_preflight_closeout_mismatch")

    paper_root, paper_issues = _validate_staging_binding(
        paper_text, expected_run_id=expected_run_id, lane="paper", label="paper_staging_binding"
    )
    shadow_root, shadow_issues = _validate_staging_binding(
        shadow_text, expected_run_id=expected_run_id, lane="shadow", label="shadow_staging_binding"
    )
    validation_issues.extend(paper_issues)
    validation_issues.extend(shadow_issues)
    validation_issues.extend(_validate_bridge_closeout(bridge_text))

    valid = len(validation_issues) == 0
    return {
        "schema_version": GOVERNANCE_OUTROOT_CLEARANCE_SCHEMA_VERSION,
        "non_authorizing": True,
        "durable_run_outroot": str(outroot),
        "expected_run_id": expected_run_id,
        "valid": valid,
        "hold_clearance_done": preflight_fields.get("HOLD_CLEARANCE_DONE"),
        "hold_clearance_scope": preflight_fields.get("HOLD_CLEARANCE_SCOPE"),
        "staging_bridge_materialized": preflight_fields.get("STAGING_BRIDGE_MATERIALIZED")
        == "true",
        "paper_staging_root": paper_root,
        "shadow_staging_root": shadow_root,
        "validation_issues": validation_issues,
        "permits_scheduler_runtime_paper_testnet_live": False,
        "reason": REASON_VALID if valid else REASON_INVALID,
    }
