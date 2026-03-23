from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.ops.workflow_officer_markdown import render_workflow_officer_summary


def _sample_report() -> dict:
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
                "notes": [],
            },
            {
                "check_id": "docs_graph_triage",
                "command": ["python3", "scripts/ops/docs_graph_triage.py"],
                "returncode": 1,
                "status": "WARN",
                "severity": "warn",
                "outcome": "fail",
                "effective_level": "warning",
                "notes": ["triage warning"],
            },
        ],
        "summary": {
            "total_checks": 2,
            "hard_failures": 0,
            "warnings": 1,
            "infos": 0,
            "severity_counts": {"hard_fail": 1, "warn": 1, "info": 0},
            "status_counts": {"OK": 1, "WARN": 1},
            "outcome_counts": {"pass": 1, "fail": 1, "missing": 0},
            "effective_level_counts": {"ok": 1, "warning": 1, "error": 0, "info": 0},
            "strict": False,
        },
    }


def test_render_workflow_officer_summary_contains_core_sections() -> None:
    md = render_workflow_officer_summary(_sample_report())
    assert "# Workflow Officer Summary" in md
    assert "## Run" in md
    assert "## Summary Counts" in md
    assert "## Checks" in md
    assert "| check_id | severity | outcome | effective_level | status | returncode |" in md
    assert "docs_token_policy" in md
    assert "docs_graph_triage" in md
    assert "## Notes" in md
    assert "triage warning" in md


def test_workflow_officer_run_writes_summary_md() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    proc = subprocess.run(
        [
            sys.executable,
            "src/ops/workflow_officer.py",
            "--mode",
            "audit",
            "--profile",
            "docs_only_pr",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode in (0, 1)

    out_root = repo_root / "out" / "ops" / "workflow_officer"
    latest = sorted([p for p in out_root.iterdir() if p.is_dir()])[-1]

    summary_path = latest / "summary.md"
    report_path = latest / "report.json"

    assert summary_path.exists()
    assert report_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    summary_md = summary_path.read_text(encoding="utf-8")

    assert report["profile"] in summary_md
    assert report["mode"] in summary_md
    assert "## Checks" in summary_md
