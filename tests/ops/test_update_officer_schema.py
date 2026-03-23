from __future__ import annotations

import pytest

from src.ops.update_officer_schema import (
    UpdateOfficerSchemaError,
    validate_report_payload,
)


def _valid_report() -> dict:
    return {
        "officer_version": "v0-min",
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
            }
        ],
        "summary": {
            "total_findings": 1,
            "safe_review": 1,
            "manual_review": 0,
            "blocked": 0,
        },
    }


def test_validate_report_payload_accepts_valid() -> None:
    validate_report_payload(_valid_report())


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
