from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.ops.workflow_officer import (
    build_executive_summary_view,
    build_followup_topic_ranking,
    build_handoff_context,
    build_next_chat_preview,
    build_operator_report_view,
    build_workflow_officer_provenance,
)
from src.ops.workflow_officer_markdown import render_workflow_officer_summary


def _sample_report() -> dict:
    checks = [
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
            "description": "Token policy",
            "recommended_action": "No operator action required.",
            "recommended_priority": "p3",
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
            "surface": "docs",
            "category": "documentation",
            "description": "Graph triage",
            "recommended_action": "Review logs.",
            "recommended_priority": "p1",
            "notes": ["triage warning"],
        },
    ]
    summary: dict = {
        "total_checks": 2,
        "hard_failures": 0,
        "warnings": 1,
        "infos": 0,
        "severity_counts": {"hard_fail": 1, "warn": 1, "info": 0},
        "status_counts": {"OK": 1, "WARN": 1},
        "outcome_counts": {"pass": 1, "fail": 1, "missing": 0},
        "effective_level_counts": {"ok": 1, "warning": 1, "error": 0, "info": 0},
        "recommended_priority_counts": {"p0": 0, "p1": 1, "p2": 0, "p3": 1},
        "strict": False,
        "registry_inputs": {
            "registry_dir_present": True,
            "pointer_count": 3,
            "pointers": [
                {
                    "name": "a.pointer",
                    "rel_path": "docs/ops/registry/a.pointer",
                    "fields": {"run_id": "run-1"},
                }
            ],
        },
        "merge_log_inputs": {
            "merge_logs_dir_present": True,
            "canonical_merge_log_count": 2,
            "recent_merge_logs": [
                {
                    "pr_number": 100,
                    "rel_path": "docs/ops/merge_logs/PR_100_MERGE_LOG.md",
                    "merge_commit_sha": "abcdef0",
                    "merged_at": "2026-01-01",
                },
                {
                    "pr_number": 99,
                    "rel_path": "docs/ops/merge_logs/PR_99_MERGE_LOG.md",
                    "merge_commit_sha": None,
                    "merged_at": None,
                },
            ],
        },
        "followup_topic_ranking": build_followup_topic_ranking(checks),
    }
    summary["workflow_officer_provenance"] = build_workflow_officer_provenance()
    summary["handoff_context"] = build_handoff_context(summary)
    summary["next_chat_preview"] = build_next_chat_preview(summary)
    summary["operator_report"] = build_operator_report_view(summary)
    summary["executive_summary"] = build_executive_summary_view(summary)
    return {
        "officer_version": "v1-min",
        "mode": "audit",
        "profile": "docs_only_pr",
        "started_at": "2026-03-23T10:00:00+00:00",
        "finished_at": "2026-03-23T10:00:01+00:00",
        "output_dir": "out/ops/workflow_officer/20260323T100000Z",
        "repo_root": "/tmp/repo",
        "success": True,
        "checks": checks,
        "summary": summary,
    }


def test_render_workflow_officer_summary_contains_core_sections() -> None:
    md = render_workflow_officer_summary(_sample_report())
    assert "# Workflow Officer Summary" in md
    assert "## Run" in md
    assert "## Executive decision package" in md
    assert "workflow_officer.executive_summary/v0" in md
    assert "## Summary Counts" in md
    assert "### Recommended priority counts" in md
    assert "## By priority" in md
    assert "## By category" in md
    assert "## Recommended next actions" in md
    assert "## Checks" in md
    assert "| check_id | surface | category | priority |" in md
    assert "docs_token_policy" in md
    assert "docs_graph_triage" in md
    assert "## Notes" in md
    assert "triage warning" in md
    assert "## Operator consolidated view" in md
    assert "workflow_officer.operator_report/v0" in md
    assert "## Next chat preview" in md
    assert "docs_graph_triage" in md
    assert "queued_followup_check_ids (order preserved):" in md
    assert "sequencing_bucket" in md


def test_workflow_officer_run_writes_summary_md(tmp_path: Path) -> None:
    """Run workflow_officer into isolated tmp output root; assert report.json and summary.md."""
    repo_root = Path(__file__).resolve().parents[2]
    output_root = tmp_path / "workflow_officer"
    output_root.mkdir(parents=True, exist_ok=True)

    proc = subprocess.run(
        [
            sys.executable,
            "src/ops/workflow_officer.py",
            "--mode",
            "audit",
            "--profile",
            "docs_only_pr",
            "--output-root",
            str(output_root),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode in (0, 1)

    run_dirs = sorted([p for p in output_root.iterdir() if p.is_dir()])
    assert run_dirs, f"expected at least one run dir under {output_root}"
    run_dir = run_dirs[-1]

    summary_path = run_dir / "summary.md"
    report_path = run_dir / "report.json"

    assert summary_path.exists(), f"summary.md missing in {run_dir}"
    assert report_path.exists(), f"report.json missing in {run_dir}"

    report = json.loads(report_path.read_text(encoding="utf-8"))
    summary_md = summary_path.read_text(encoding="utf-8")

    assert report["profile"] in summary_md
    assert report["mode"] in summary_md
    assert report["officer_version"] == "v1-min"
    assert "## By priority" in summary_md
    assert "## Recommended next actions" in summary_md
    assert "## Next chat preview" in summary_md
