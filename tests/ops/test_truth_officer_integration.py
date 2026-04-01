"""Tests for Unified Truth Core integration into officer reports."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from src.ops.truth_officer_integration import (
    UnifiedTruthStatusValidationError,
    build_unified_truth_status,
    validate_unified_truth_status_shape,
)
from src.ops.workflow_officer_schema import WorkflowOfficerSchemaError, validate_report_payload


def test_build_unified_truth_status_real_repo() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    st = build_unified_truth_status(repo_root)
    assert st["unified_truth_status_schema_version"] == "ops.unified_truth_status/v1"
    assert st["docs_drift"]["status"] in {"PASS", "FAIL", "UNKNOWN"}
    assert isinstance(st["docs_drift"]["changed_files_count"], int)
    assert st["repo_claims"]["status"] in {"PASS", "FAIL", "UNKNOWN"}
    assert st["repo_claims"]["checks_run"] >= 1


def test_build_unified_truth_status_docs_drift_unknown_on_git_error() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with mock.patch(
        "src.ops.truth.git_changed_files_three_dot",
        side_effect=RuntimeError("git oops"),
    ):
        st = build_unified_truth_status(repo_root, git_base="origin/main")
    assert st["docs_drift"]["status"] == "UNKNOWN"
    assert "git oops" in (st["docs_drift"].get("detail") or "")


def test_validate_unified_truth_status_shape_accepts_minimal() -> None:
    validate_unified_truth_status_shape(
        {
            "unified_truth_status_schema_version": "ops.unified_truth_status/v1",
            "git_base": "origin/main",
            "docs_drift": {
                "status": "PASS",
                "changed_files_count": 0,
                "violation_rule_ids": [],
                "detail": None,
            },
            "repo_claims": {
                "status": "FAIL",
                "checks_run": 2,
                "failed_claim_ids": ["a"],
                "unknown_claim_ids": [],
                "detail": None,
            },
        }
    )


def test_validate_unified_truth_status_shape_rejects_bad_enum() -> None:
    with pytest.raises(UnifiedTruthStatusValidationError):
        validate_unified_truth_status_shape(
            {
                "unified_truth_status_schema_version": "ops.unified_truth_status/v1",
                "git_base": "origin/main",
                "docs_drift": {
                    "status": "MAYBE",
                    "changed_files_count": 0,
                    "violation_rule_ids": [],
                    "detail": None,
                },
                "repo_claims": {
                    "status": "PASS",
                    "checks_run": 0,
                    "failed_claim_ids": [],
                    "unknown_claim_ids": [],
                    "detail": None,
                },
            }
        )


def test_workflow_officer_report_requires_unified_truth_block() -> None:
    """Schema rejects legacy summaries without ``unified_truth_status``."""
    payload_min = {
        "officer_version": "v1-min",
        "mode": "audit",
        "profile": "docs_only_pr",
        "started_at": "2026-03-23T10:00:00+00:00",
        "finished_at": "2026-03-23T10:00:01+00:00",
        "output_dir": "out/x",
        "repo_root": "/tmp/repo",
        "success": True,
        "checks": [],
        "summary": {
            "total_checks": 0,
            "hard_failures": 0,
            "warnings": 0,
            "infos": 0,
            "severity_counts": {"hard_fail": 0, "warn": 0, "info": 0},
            "status_counts": {},
            "outcome_counts": {"pass": 0, "fail": 0, "missing": 0},
            "effective_level_counts": {"ok": 0, "warning": 0, "error": 0, "info": 0},
            "recommended_priority_counts": {"p0": 0, "p1": 0, "p2": 0, "p3": 0},
            "strict": False,
        },
    }
    with pytest.raises(WorkflowOfficerSchemaError):
        validate_report_payload(payload_min)
