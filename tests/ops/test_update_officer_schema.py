from __future__ import annotations

import pytest

from src.ops.update_officer_schema import (
    UpdateOfficerSchemaError,
    validate_notifier_payload,
    validate_report_payload,
)


def _valid_report() -> dict:
    return {
        "officer_version": "v3-min",
        "profile": "dev_tooling_review",
        "started_at": "2026-03-23T10:00:00+00:00",
        "finished_at": "2026-03-23T10:00:01+00:00",
        "output_dir": "out/ops/update_officer/20260323T100000Z",
        "repo_root": "/tmp/repo",
        "success": True,
        "findings": [
            {
                "surface": "pyproject.toml",
                "item_name": "ruff",
                "current_spec": ">=0.1.0",
                "classification": "safe_review",
                "reason": "recognized dev tooling",
                "category": "python_dependencies",
                "description": "Dev dependency ruff in pyproject.toml.",
                "recommended_action": "No immediate action; include in routine dev-tooling hygiene.",
                "recommended_priority": "p3",
                "notes": [],
            }
        ],
        "summary": {
            "total_findings": 1,
            "safe_review": 1,
            "manual_review": 0,
            "blocked": 0,
            "priority_counts": {"p0": 0, "p1": 0, "p2": 0, "p3": 1},
            "category_counts": {"python_dependencies": 1},
            "unified_truth_status": {
                "unified_truth_status_schema_version": "ops.unified_truth_status/v1",
                "git_base": "origin/main",
                "docs_drift": {
                    "status": "PASS",
                    "changed_files_count": 0,
                    "violation_rule_ids": [],
                    "detail": None,
                },
                "repo_claims": {
                    "status": "PASS",
                    "checks_run": 1,
                    "failed_claim_ids": [],
                    "unknown_claim_ids": [],
                    "detail": None,
                },
            },
        },
        "next_recommended_topic": "python_dependencies",
        "top_priority_reason": "Topic `python_dependencies` ranks first.",
        "recommended_update_queue": [
            {
                "topic_id": "python_dependencies",
                "rank": 1,
                "worst_priority": "p3",
                "finding_count": 1,
                "blocked_count": 0,
                "manual_review_count": 0,
                "safe_review_count": 1,
                "headline": "1 finding(s); worst_priority=p3; blocked=0; manual_review=0; safe_review=1",
            }
        ],
        "notifier_payload_path": "notifier_payload.json",
    }


def _valid_notifier_payload() -> dict:
    return {
        "officer_version": "v3-min",
        "generated_at": "2026-03-23T10:00:01+00:00",
        "next_recommended_topic": "python_dependencies",
        "top_priority_reason": "Topic `python_dependencies` ranks first.",
        "recommended_update_queue": [
            {
                "topic_id": "python_dependencies",
                "rank": 1,
                "worst_priority": "p3",
                "finding_count": 1,
                "blocked_count": 0,
                "manual_review_count": 0,
                "safe_review_count": 1,
                "headline": "1 finding(s); worst_priority=p3; blocked=0; manual_review=0; safe_review=1",
            }
        ],
        "recommended_next_action": "Focus manual review on update topic `python_dependencies` first.",
        "recommended_review_paths": ["pyproject.toml"],
        "severity": "low",
        "reminder_class": "hygiene",
        "requires_manual_review": False,
    }


def test_validate_report_payload_accepts_valid() -> None:
    validate_report_payload(_valid_report())


def test_validate_notifier_payload_accepts_valid() -> None:
    validate_notifier_payload(_valid_notifier_payload())


def test_validate_notifier_payload_rejects_bad_severity() -> None:
    payload = _valid_notifier_payload()
    payload["severity"] = "nope"
    with pytest.raises(UpdateOfficerSchemaError):
        validate_notifier_payload(payload)


def test_validate_report_payload_rejects_invalid_profile() -> None:
    payload = _valid_report()
    payload["profile"] = "nonexistent_profile"
    with pytest.raises(UpdateOfficerSchemaError):
        validate_report_payload(payload)


def test_validate_report_payload_rejects_invalid_classification() -> None:
    payload = _valid_report()
    payload["findings"][0]["classification"] = "invalid_class"
    with pytest.raises(UpdateOfficerSchemaError):
        validate_report_payload(payload)


def test_validate_report_payload_rejects_missing_finding_key() -> None:
    payload = _valid_report()
    del payload["findings"][0]["reason"]
    with pytest.raises(UpdateOfficerSchemaError):
        validate_report_payload(payload)


def test_validate_report_payload_rejects_missing_summary_key() -> None:
    payload = _valid_report()
    del payload["summary"]["blocked"]
    with pytest.raises(UpdateOfficerSchemaError):
        validate_report_payload(payload)


def test_validate_report_payload_rejects_missing_top_level_key() -> None:
    payload = _valid_report()
    del payload["success"]
    with pytest.raises(UpdateOfficerSchemaError):
        validate_report_payload(payload)


def test_validate_report_payload_rejects_invalid_surface() -> None:
    payload = _valid_report()
    payload["findings"][0]["surface"] = "unknown_surface"
    with pytest.raises(UpdateOfficerSchemaError):
        validate_report_payload(payload)


def test_validate_report_payload_rejects_invalid_priority() -> None:
    payload = _valid_report()
    payload["findings"][0]["recommended_priority"] = "p9"
    with pytest.raises(UpdateOfficerSchemaError):
        validate_report_payload(payload)


def test_validate_report_payload_rejects_bad_priority_count_keys() -> None:
    payload = _valid_report()
    payload["summary"]["priority_counts"] = {"p0": 0, "p1": 1}
    with pytest.raises(UpdateOfficerSchemaError):
        validate_report_payload(payload)


def test_validate_report_payload_rejects_missing_next_topic() -> None:
    payload = _valid_report()
    del payload["next_recommended_topic"]
    with pytest.raises(UpdateOfficerSchemaError):
        validate_report_payload(payload)


def test_validate_report_payload_rejects_missing_notifier_path() -> None:
    payload = _valid_report()
    del payload["notifier_payload_path"]
    with pytest.raises(UpdateOfficerSchemaError):
        validate_report_payload(payload)


def test_validate_report_payload_rejects_bad_queue_rank_sequence() -> None:
    payload = _valid_report()
    payload["recommended_update_queue"] = [
        {
            "topic_id": "python_dependencies",
            "rank": 2,
            "worst_priority": "p3",
            "finding_count": 1,
            "blocked_count": 0,
            "manual_review_count": 0,
            "safe_review_count": 1,
            "headline": "x",
        }
    ]
    with pytest.raises(UpdateOfficerSchemaError):
        validate_report_payload(payload)
