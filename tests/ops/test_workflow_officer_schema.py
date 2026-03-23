from __future__ import annotations

import pytest

from src.ops.workflow_officer_schema import (
    WorkflowOfficerSchemaError,
    validate_report_payload,
)


def _valid_report() -> dict:
    return {
        "officer_version": "v0-min",
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
