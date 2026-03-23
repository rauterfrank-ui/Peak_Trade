from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.ops.workflow_officer import (
    PROFILE_POLICY,
    _resolve_effective_level,
    _resolve_outcome,
    _resolve_severity,
    _resolve_status,
)


def _run(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "src/ops/workflow_officer.py", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )


def test_workflow_officer_docs_only_pr_emits_report() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    proc = _run(repo_root, "--mode", "audit", "--profile", "docs_only_pr")
    assert proc.returncode in (0, 1)

    out_root = repo_root / "out" / "ops" / "workflow_officer"
    assert out_root.exists()

    latest = sorted([p for p in out_root.iterdir() if p.is_dir()])[-1]
    report_path = latest / "report.json"
    manifest_path = latest / "manifest.json"
    events_path = latest / "events.jsonl"
    summary_path = latest / "summary.md"

    assert report_path.exists()
    assert manifest_path.exists()
    assert events_path.exists()
    assert summary_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["officer_version"] == "v0-min"
    assert report["profile"] == "docs_only_pr"
    assert "checks" in report
    assert "summary" in report
    assert "severity_counts" in report["summary"]
    assert "outcome_counts" in report["summary"]
    assert "effective_level_counts" in report["summary"]

    for check in report["checks"]:
        assert "severity" in check
        assert "outcome" in check
        assert "effective_level" in check


def test_workflow_officer_profiles_alias_exports_profiles() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    from src.ops.workflow_officer_profiles import PROFILES

    assert "docs_only_pr" in PROFILES
    assert "ops_local_env" in PROFILES
    assert "live_pilot_preflight" in PROFILES


def test_profile_policy_contains_expected_severities() -> None:
    assert PROFILE_POLICY["docs_only_pr"]["docs_token_policy"] == "hard_fail"
    assert PROFILE_POLICY["ops_local_env"]["ops_doctor_shell"] == "warn"
    assert (
        PROFILE_POLICY["live_pilot_preflight"]["docker_desktop_preflight_readonly"] == "hard_fail"
    )


def test_resolve_severity_and_status() -> None:
    assert _resolve_severity("docs_only_pr", "docs_token_policy") == "hard_fail"
    assert _resolve_severity("ops_local_env", "failure_analysis") == "info"

    assert _resolve_status(0, "hard_fail") == "OK"
    assert _resolve_status(1, "hard_fail") == "FAILED"
    assert _resolve_status(1, "warn") == "WARN"
    assert _resolve_status(1, "info") == "INFO"
    assert _resolve_status(2, "hard_fail", missing=True) == "FAILED_MISSING"
    assert _resolve_status(2, "warn", missing=True) == "WARN_MISSING"
    assert _resolve_status(2, "info", missing=True) == "INFO_MISSING"


def test_resolve_outcome_and_effective_level() -> None:
    assert _resolve_outcome(0) == "pass"
    assert _resolve_outcome(1) == "fail"
    assert _resolve_outcome(2, missing=True) == "missing"

    assert _resolve_effective_level("pass", "hard_fail") == "ok"
    assert _resolve_effective_level("fail", "hard_fail") == "error"
    assert _resolve_effective_level("fail", "warn") == "warning"
    assert _resolve_effective_level("fail", "info") == "info"
    assert _resolve_effective_level("missing", "hard_fail") == "error"
    assert _resolve_effective_level("missing", "warn") == "warning"
    assert _resolve_effective_level("missing", "info") == "info"
