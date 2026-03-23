from __future__ import annotations

from typing import Any


ALLOWED_MODES = {"audit", "preflight", "advise"}
ALLOWED_SEVERITIES = {"hard_fail", "warn", "info"}
ALLOWED_OUTCOMES = {"pass", "fail", "missing"}
ALLOWED_EFFECTIVE_LEVELS = {"ok", "warning", "error", "info"}

REQUIRED_TOP_LEVEL_KEYS = {
    "officer_version",
    "mode",
    "profile",
    "started_at",
    "finished_at",
    "output_dir",
    "repo_root",
    "success",
    "checks",
    "summary",
}

REQUIRED_CHECK_KEYS = {
    "check_id",
    "command",
    "returncode",
    "status",
    "severity",
    "outcome",
    "effective_level",
}

REQUIRED_SUMMARY_KEYS = {
    "total_checks",
    "hard_failures",
    "warnings",
    "infos",
    "severity_counts",
    "status_counts",
    "outcome_counts",
    "effective_level_counts",
    "strict",
}


class WorkflowOfficerSchemaError(ValueError):
    pass


def _require_keys(obj: dict[str, Any], required: set[str], scope: str) -> None:
    missing = sorted(required - set(obj.keys()))
    if missing:
        raise WorkflowOfficerSchemaError(f"{scope}: missing keys: {missing}")


def _require_enum(value: Any, allowed: set[str], scope: str) -> None:
    if value not in allowed:
        raise WorkflowOfficerSchemaError(
            f"{scope}: invalid value {value!r}, allowed={sorted(allowed)}"
        )


def _require_type(value: Any, expected_type: type | tuple[type, ...], scope: str) -> None:
    if not isinstance(value, expected_type):
        raise WorkflowOfficerSchemaError(f"{scope}: expected {expected_type}, got {type(value)}")


def validate_check_payload(check: dict[str, Any], idx: int) -> None:
    scope = f"check[{idx}]"
    _require_keys(check, REQUIRED_CHECK_KEYS, scope)
    _require_type(check["check_id"], str, f"{scope}.check_id")
    _require_type(check["command"], list, f"{scope}.command")
    _require_type(check["returncode"], int, f"{scope}.returncode")
    _require_type(check["status"], str, f"{scope}.status")
    _require_type(check["severity"], str, f"{scope}.severity")
    _require_type(check["outcome"], str, f"{scope}.outcome")
    _require_type(check["effective_level"], str, f"{scope}.effective_level")
    _require_enum(check["severity"], ALLOWED_SEVERITIES, f"{scope}.severity")
    _require_enum(check["outcome"], ALLOWED_OUTCOMES, f"{scope}.outcome")
    _require_enum(
        check["effective_level"],
        ALLOWED_EFFECTIVE_LEVELS,
        f"{scope}.effective_level",
    )


def validate_summary_payload(summary: dict[str, Any]) -> None:
    scope = "summary"
    _require_keys(summary, REQUIRED_SUMMARY_KEYS, scope)
    for key in ["total_checks", "hard_failures", "warnings", "infos"]:
        _require_type(summary[key], int, f"{scope}.{key}")
    _require_type(summary["strict"], bool, f"{scope}.strict")
    _require_type(summary["severity_counts"], dict, f"{scope}.severity_counts")
    _require_type(summary["status_counts"], dict, f"{scope}.status_counts")
    _require_type(summary["outcome_counts"], dict, f"{scope}.outcome_counts")
    _require_type(
        summary["effective_level_counts"],
        dict,
        f"{scope}.effective_level_counts",
    )

    severity_keys = set(summary["severity_counts"].keys())
    outcome_keys = set(summary["outcome_counts"].keys())
    effective_level_keys = set(summary["effective_level_counts"].keys())

    if severity_keys != ALLOWED_SEVERITIES:
        raise WorkflowOfficerSchemaError(
            f"{scope}.severity_counts: expected keys {sorted(ALLOWED_SEVERITIES)}, got {sorted(severity_keys)}"
        )
    if outcome_keys != ALLOWED_OUTCOMES:
        raise WorkflowOfficerSchemaError(
            f"{scope}.outcome_counts: expected keys {sorted(ALLOWED_OUTCOMES)}, got {sorted(outcome_keys)}"
        )
    if effective_level_keys != ALLOWED_EFFECTIVE_LEVELS:
        raise WorkflowOfficerSchemaError(
            f"{scope}.effective_level_counts: expected keys {sorted(ALLOWED_EFFECTIVE_LEVELS)}, got {sorted(effective_level_keys)}"
        )


def validate_report_payload(report: dict[str, Any]) -> None:
    scope = "report"
    _require_keys(report, REQUIRED_TOP_LEVEL_KEYS, scope)
    _require_type(report["officer_version"], str, f"{scope}.officer_version")
    _require_type(report["mode"], str, f"{scope}.mode")
    _require_type(report["profile"], str, f"{scope}.profile")
    _require_type(report["started_at"], str, f"{scope}.started_at")
    _require_type(report["finished_at"], str, f"{scope}.finished_at")
    _require_type(report["output_dir"], str, f"{scope}.output_dir")
    _require_type(report["repo_root"], str, f"{scope}.repo_root")
    _require_type(report["success"], bool, f"{scope}.success")
    _require_type(report["checks"], list, f"{scope}.checks")
    _require_type(report["summary"], dict, f"{scope}.summary")
    _require_enum(report["mode"], ALLOWED_MODES, f"{scope}.mode")

    for idx, check in enumerate(report["checks"]):
        _require_type(check, dict, f"{scope}.checks[{idx}]")
        validate_check_payload(check, idx)

    validate_summary_payload(report["summary"])
