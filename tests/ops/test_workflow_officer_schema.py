from __future__ import annotations

import pytest

from src.ops.workflow_officer_schema import (
    WorkflowOfficerSchemaError,
    validate_report_payload,
)


def _valid_report() -> dict:
    return {
        "officer_version": "v1-min",
        "mode": "audit",
        "profile": "docs_only_pr",
        "started_at": "2026-03-23T10:00:00+00:00",
        "finished_at": "2026-03-23T10:00:01+00:00",
        "output_dir": "out/ops/workflow_officer/20260323T100000Z",
        "repo_root": "/tmp/repo",
        "success": True,
        "checks": [
            {
                "check_id": "docs_token_policy",
                "command": ["python3", "scripts/ops/validate_docs_token_policy.py"],
                "returncode": 0,
                "status": "OK",
                "severity": "hard_fail",
                "outcome": "pass",
                "effective_level": "ok",
                "surface": "docs",
                "category": "documentation",
                "description": "Docs token policy.",
                "recommended_action": "No operator action required.",
                "recommended_priority": "p3",
            }
        ],
        "summary": {
            "total_checks": 1,
            "hard_failures": 0,
            "warnings": 0,
            "infos": 0,
            "severity_counts": {
                "hard_fail": 1,
                "warn": 0,
                "info": 0,
            },
            "status_counts": {
                "OK": 1,
            },
            "outcome_counts": {
                "pass": 1,
                "fail": 0,
                "missing": 0,
            },
            "effective_level_counts": {
                "ok": 1,
                "warning": 0,
                "error": 0,
                "info": 0,
            },
            "recommended_priority_counts": {
                "p0": 0,
                "p1": 0,
                "p2": 0,
                "p3": 1,
            },
            "strict": False,
        },
    }


def test_validate_report_payload_accepts_valid_payload() -> None:
    payload = _valid_report()
    validate_report_payload(payload)


def test_validate_report_payload_rejects_invalid_mode() -> None:
    payload = _valid_report()
    payload["mode"] = "broken"
    with pytest.raises(WorkflowOfficerSchemaError):
        validate_report_payload(payload)


def test_validate_report_payload_rejects_missing_check_field() -> None:
    payload = _valid_report()
    del payload["checks"][0]["effective_level"]
    with pytest.raises(WorkflowOfficerSchemaError):
        validate_report_payload(payload)


def test_validate_report_payload_rejects_invalid_outcome_counts_keys() -> None:
    payload = _valid_report()
    payload["summary"]["outcome_counts"] = {"pass": 1, "fail": 0}
    with pytest.raises(WorkflowOfficerSchemaError):
        validate_report_payload(payload)


def test_validate_report_payload_rejects_invalid_effective_level_enum() -> None:
    payload = _valid_report()
    payload["checks"][0]["effective_level"] = "bad"
    with pytest.raises(WorkflowOfficerSchemaError):
        validate_report_payload(payload)


def test_validate_report_payload_rejects_invalid_recommended_priority() -> None:
    payload = _valid_report()
    payload["checks"][0]["recommended_priority"] = "p9"
    with pytest.raises(WorkflowOfficerSchemaError):
        validate_report_payload(payload)


def test_validate_report_payload_rejects_bad_priority_count_keys() -> None:
    payload = _valid_report()
    payload["summary"]["recommended_priority_counts"] = {"p0": 1, "p1": 0}
    with pytest.raises(WorkflowOfficerSchemaError):
        validate_report_payload(payload)


def test_validate_report_payload_accepts_optional_primary_sequencing() -> None:
    payload = _valid_report()
    payload["summary"]["primary_sequencing"] = {
        "sequencing_bucket": "build_now",
        "sequencing_rationale": "execution-adjacent bounded-pilot / truth / ops work is a nearer prerequisite than broader AI-layer expansion",
        "prerequisite_signals": ["active_path_hardening"],
        "blocked_by": [],
        "suggested_next_theme_class": "bounded_pilot_truth_ops",
        "sequencing_schema_version": "workflow_officer.sequencing/v0",
    }
    validate_report_payload(payload)
