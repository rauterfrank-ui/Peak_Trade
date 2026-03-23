from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


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

    assert report_path.exists()
    assert manifest_path.exists()
    assert events_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["officer_version"] == "v0-min"
    assert report["profile"] == "docs_only_pr"
    assert "checks" in report
    assert "summary" in report


def test_workflow_officer_profiles_alias_exports_profiles() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    from src.ops.workflow_officer_profiles import PROFILES

    assert "docs_only_pr" in PROFILES
    assert "ops_local_env" in PROFILES
    assert "live_pilot_preflight" in PROFILES
