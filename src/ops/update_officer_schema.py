from __future__ import annotations

from typing import Any


ALLOWED_CLASSIFICATIONS = {"safe_review", "manual_review", "blocked"}
ALLOWED_PROFILES = {"dev_tooling_review"}
ALLOWED_SURFACES = {"pyproject.toml", "github_actions"}
ALLOWED_PRIORITIES = {"p0", "p1", "p2", "p3"}
PRIORITY_COUNT_KEYS = {"p0", "p1", "p2", "p3"}

ALLOWED_NOTIFIER_SEVERITY = {"info", "low", "medium", "high", "critical"}
ALLOWED_REMINDER_CLASS = {"none", "blocked", "manual_review", "hygiene"}

REQUIRED_NOTIFIER_KEYS = {
    "officer_version",
    "generated_at",
    "next_recommended_topic",
    "top_priority_reason",
    "recommended_update_queue",
    "recommended_next_action",
    "recommended_review_paths",
    "severity",
    "reminder_class",
    "requires_manual_review",
}

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
    "next_recommended_topic",
    "top_priority_reason",
    "recommended_update_queue",
    "notifier_payload_path",
}

REQUIRED_QUEUE_ENTRY_KEYS = {
    "topic_id",
    "rank",
    "worst_priority",
    "finding_count",
    "blocked_count",
    "manual_review_count",
    "safe_review_count",
    "headline",
}

REQUIRED_FINDING_KEYS = {
    "surface",
    "item_name",
    "current_spec",
    "classification",
    "reason",
    "category",
    "description",
    "recommended_action",
    "recommended_priority",
}

REQUIRED_SUMMARY_KEYS = {
    "total_findings",
    "safe_review",
    "manual_review",
    "blocked",
    "priority_counts",
    "category_counts",
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
    _require_type(finding["category"], str, f"{scope}.category")
    _require_type(finding["description"], str, f"{scope}.description")
    _require_type(finding["recommended_action"], str, f"{scope}.recommended_action")
    _require_type(finding["recommended_priority"], str, f"{scope}.recommended_priority")
    _require_enum(finding["classification"], ALLOWED_CLASSIFICATIONS, f"{scope}.classification")
    _require_enum(finding["surface"], ALLOWED_SURFACES, f"{scope}.surface")
    _require_enum(
        finding["recommended_priority"],
        ALLOWED_PRIORITIES,
        f"{scope}.recommended_priority",
    )
    if "notes" in finding:
        _require_type(finding["notes"], list, f"{scope}.notes")
        for j, note in enumerate(finding["notes"]):
            _require_type(note, str, f"{scope}.notes[{j}]")


def validate_notifier_payload(payload: dict[str, Any]) -> None:
    scope = "notifier_payload"
    _require_keys(payload, REQUIRED_NOTIFIER_KEYS, scope)
    _require_type(payload["officer_version"], str, f"{scope}.officer_version")
    _require_type(payload["generated_at"], str, f"{scope}.generated_at")
    _require_type(payload["next_recommended_topic"], str, f"{scope}.next_recommended_topic")
    _require_type(payload["top_priority_reason"], str, f"{scope}.top_priority_reason")
    _require_type(payload["recommended_next_action"], str, f"{scope}.recommended_next_action")
    _require_type(payload["recommended_review_paths"], list, f"{scope}.recommended_review_paths")
    for i, p in enumerate(payload["recommended_review_paths"]):
        _require_type(p, str, f"{scope}.recommended_review_paths[{i}]")
    _require_enum(payload["severity"], ALLOWED_NOTIFIER_SEVERITY, f"{scope}.severity")
    _require_enum(payload["reminder_class"], ALLOWED_REMINDER_CLASS, f"{scope}.reminder_class")
    _require_type(payload["requires_manual_review"], bool, f"{scope}.requires_manual_review")
    _require_type(payload["recommended_update_queue"], list, f"{scope}.recommended_update_queue")
    for qi, qe in enumerate(payload["recommended_update_queue"]):
        _require_type(qe, dict, f"{scope}.recommended_update_queue[{qi}]")
        validate_queue_entry(qe, qi)
    for i, entry in enumerate(payload["recommended_update_queue"]):
        if entry["rank"] != i + 1:
            raise UpdateOfficerSchemaError(
                f"{scope}.recommended_update_queue: expected rank {i + 1}, got {entry['rank']}"
            )


def validate_queue_entry(entry: dict[str, Any], idx: int) -> None:
    scope = f"recommended_update_queue[{idx}]"
    _require_keys(entry, REQUIRED_QUEUE_ENTRY_KEYS, scope)
    _require_type(entry["topic_id"], str, f"{scope}.topic_id")
    _require_type(entry["rank"], int, f"{scope}.rank")
    _require_type(entry["worst_priority"], str, f"{scope}.worst_priority")
    _require_enum(entry["worst_priority"], ALLOWED_PRIORITIES, f"{scope}.worst_priority")
    for k in (
        "finding_count",
        "blocked_count",
        "manual_review_count",
        "safe_review_count",
    ):
        _require_type(entry[k], int, f"{scope}.{k}")
    _require_type(entry["headline"], str, f"{scope}.headline")


def validate_summary_payload(summary: dict[str, Any]) -> None:
    scope = "summary"
    _require_keys(summary, REQUIRED_SUMMARY_KEYS, scope)
    for key in (
        "total_findings",
        "safe_review",
        "manual_review",
        "blocked",
    ):
        _require_type(summary[key], int, f"{scope}.{key}")
    _require_type(summary["priority_counts"], dict, f"{scope}.priority_counts")
    _require_type(summary["category_counts"], dict, f"{scope}.category_counts")

    pc = summary["priority_counts"]
    if set(pc.keys()) != PRIORITY_COUNT_KEYS:
        raise UpdateOfficerSchemaError(
            f"{scope}.priority_counts: expected keys {sorted(PRIORITY_COUNT_KEYS)}, "
            f"got {sorted(pc.keys())}"
        )
    for k in PRIORITY_COUNT_KEYS:
        _require_type(pc[k], int, f"{scope}.priority_counts.{k}")

    for ck, cv in summary["category_counts"].items():
        _require_type(ck, str, f"{scope}.category_counts key")
        _require_type(cv, int, f"{scope}.category_counts[{ck!r}]")


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

    _require_type(report["next_recommended_topic"], str, f"{scope}.next_recommended_topic")
    _require_type(report["top_priority_reason"], str, f"{scope}.top_priority_reason")
    _require_type(report["recommended_update_queue"], list, f"{scope}.recommended_update_queue")
    for qi, qe in enumerate(report["recommended_update_queue"]):
        _require_type(qe, dict, f"{scope}.recommended_update_queue[{qi}]")
        validate_queue_entry(qe, qi)
    for i, entry in enumerate(report["recommended_update_queue"]):
        if entry["rank"] != i + 1:
            raise UpdateOfficerSchemaError(
                f"{scope}.recommended_update_queue: expected rank {i + 1}, got {entry['rank']}"
            )

    _require_type(report["notifier_payload_path"], str, f"{scope}.notifier_payload_path")
