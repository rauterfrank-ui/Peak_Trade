from __future__ import annotations

from typing import Any


ALLOWED_CLASSIFICATIONS = {"safe_review", "manual_review", "blocked"}
ALLOWED_PROFILES = {"dev_tooling_review"}
ALLOWED_SURFACES = {"pyproject.toml", "github_actions"}

REQUIRED_TOP_LEVEL_KEYS = {
    "officer_version",
    "profile",
    "started_at",
    "finished_at",
    "output_dir",
    "repo_root",
    "success",
    "findings",
    "summary",
}

REQUIRED_FINDING_KEYS = {
    "surface",
    "item_name",
    "current_spec",
    "classification",
    "reason",
}

REQUIRED_SUMMARY_KEYS = {
    "total_findings",
    "safe_review",
    "manual_review",
    "blocked",
}


class UpdateOfficerSchemaError(ValueError):
    pass


def _require_keys(obj: dict[str, Any], required: set[str], scope: str) -> None:
    missing = sorted(required - set(obj.keys()))
    if missing:
        raise UpdateOfficerSchemaError(f"{scope}: missing keys: {missing}")


def _require_enum(value: Any, allowed: set[str], scope: str) -> None:
    if value not in allowed:
        raise UpdateOfficerSchemaError(
            f"{scope}: invalid value {value!r}, allowed={sorted(allowed)}"
        )


def _require_type(value: Any, expected_type: type | tuple[type, ...], scope: str) -> None:
    if not isinstance(value, expected_type):
        raise UpdateOfficerSchemaError(f"{scope}: expected {expected_type}, got {type(value)}")


def validate_finding_payload(finding: dict[str, Any], idx: int) -> None:
    scope = f"finding[{idx}]"
    _require_keys(finding, REQUIRED_FINDING_KEYS, scope)
    _require_type(finding["surface"], str, f"{scope}.surface")
    _require_type(finding["item_name"], str, f"{scope}.item_name")
    _require_type(finding["current_spec"], str, f"{scope}.current_spec")
    _require_type(finding["classification"], str, f"{scope}.classification")
    _require_type(finding["reason"], str, f"{scope}.reason")
    _require_enum(finding["classification"], ALLOWED_CLASSIFICATIONS, f"{scope}.classification")
    _require_enum(finding["surface"], ALLOWED_SURFACES, f"{scope}.surface")


def validate_summary_payload(summary: dict[str, Any]) -> None:
    scope = "summary"
    _require_keys(summary, REQUIRED_SUMMARY_KEYS, scope)
    for key in REQUIRED_SUMMARY_KEYS:
        _require_type(summary[key], int, f"{scope}.{key}")


def validate_report_payload(report: dict[str, Any]) -> None:
    scope = "report"
    _require_keys(report, REQUIRED_TOP_LEVEL_KEYS, scope)
    _require_type(report["officer_version"], str, f"{scope}.officer_version")
    _require_type(report["profile"], str, f"{scope}.profile")
    _require_type(report["started_at"], str, f"{scope}.started_at")
    _require_type(report["finished_at"], str, f"{scope}.finished_at")
    _require_type(report["output_dir"], str, f"{scope}.output_dir")
    _require_type(report["repo_root"], str, f"{scope}.repo_root")
    _require_type(report["success"], bool, f"{scope}.success")
    _require_type(report["findings"], list, f"{scope}.findings")
    _require_type(report["summary"], dict, f"{scope}.summary")
    _require_enum(report["profile"], ALLOWED_PROFILES, f"{scope}.profile")

    for idx, finding in enumerate(report["findings"]):
        _require_type(finding, dict, f"{scope}.findings[{idx}]")
        validate_finding_payload(finding, idx)

    validate_summary_payload(report["summary"])
