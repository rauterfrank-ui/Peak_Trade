from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.ops.update_officer import (
    build_recommended_update_queue,
    build_summary,
    enrich_findings,
    next_recommended_topic_and_reason,
    recommend_priority_action,
    run,
    scan_github_actions,
    scan_pyproject,
)
from src.ops.update_officer_profiles import PROFILES


def test_update_officer_dev_tooling_review_emits_report(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    output_root = tmp_path / "update_officer"
    output_root.mkdir(parents=True, exist_ok=True)

    rc = run(
        profile="dev_tooling_review",
        output_root=str(output_root),
        repo_root=repo_root,
    )
    assert rc == 0

    run_dirs = sorted([p for p in output_root.iterdir() if p.is_dir()])
    assert run_dirs, f"expected at least one run dir under {output_root}"
    run_dir = run_dirs[-1]

    report_path = run_dir / "report.json"
    summary_path = run_dir / "summary.md"
    events_path = run_dir / "events.jsonl"
    manifest_path = run_dir / "manifest.json"

    assert report_path.exists()
    assert summary_path.exists()
    assert events_path.exists()
    assert manifest_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["officer_version"] == "v2-min"
    assert report["profile"] == "dev_tooling_review"
    assert "findings" in report
    assert "summary" in report
    assert report["summary"]["total_findings"] > 0
    assert "priority_counts" in report["summary"]
    assert "category_counts" in report["summary"]

    for finding in report["findings"]:
        assert "surface" in finding
        assert "item_name" in finding
        assert "classification" in finding
        assert finding["classification"] in {"safe_review", "manual_review", "blocked"}
        assert "recommended_priority" in finding
        assert "recommended_action" in finding
        assert "category" in finding
        assert "description" in finding

    assert "next_recommended_topic" in report
    assert "top_priority_reason" in report
    assert "recommended_update_queue" in report
    assert isinstance(report["recommended_update_queue"], list)
    for i, q in enumerate(report["recommended_update_queue"], start=1):
        assert q["rank"] == i
        assert "topic_id" in q
        assert "headline" in q


def test_update_officer_cli_exits_zero() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    proc = subprocess.run(
        [
            sys.executable,
            "src/ops/update_officer.py",
            "--profile",
            "dev_tooling_review",
            "--output-root",
            "out/ops/update_officer",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"stderr: {proc.stderr}"


def test_scan_pyproject_finds_dev_deps() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    profile_cfg = PROFILES["dev_tooling_review"]
    findings = scan_pyproject(repo_root, profile_cfg)
    enrich_findings("dev_tooling_review", findings)
    names = {f["item_name"] for f in findings}
    assert "pytest" in names or "ruff" in names, f"expected dev deps, got {names}"


def test_scan_github_actions_finds_refs() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    findings = scan_github_actions(repo_root)
    enrich_findings("dev_tooling_review", findings)
    assert len(findings) > 0, "expected at least one GitHub Action reference"
    for f in findings:
        assert f["surface"] == "github_actions"


def test_build_summary_counts() -> None:
    findings = [
        {
            "surface": "pyproject.toml",
            "item_name": "ruff",
            "current_spec": ">=0.1.0",
            "classification": "safe_review",
            "reason": "recognized dev tooling",
            "category": "python_dependencies",
            "description": "desc",
            "recommended_priority": "p3",
            "recommended_action": "act",
        },
        {
            "surface": "pyproject.toml",
            "item_name": "mystery-pkg",
            "current_spec": "",
            "classification": "manual_review",
            "reason": "unknown",
            "category": "python_dependencies",
            "description": "desc",
            "recommended_priority": "p2",
            "recommended_action": "act",
        },
        {
            "surface": "pyproject.toml",
            "item_name": "fastapi",
            "current_spec": ">=0.104.0",
            "classification": "blocked",
            "reason": "runtime-adjacent",
            "category": "python_dependencies",
            "description": "desc",
            "recommended_priority": "p0",
            "recommended_action": "act",
        },
    ]
    summary = build_summary(findings)
    assert summary["total_findings"] == 3
    assert summary["safe_review"] == 1
    assert summary["manual_review"] == 1
    assert summary["blocked"] == 1
    assert summary["priority_counts"] == {"p0": 1, "p1": 0, "p2": 1, "p3": 1}
    assert summary["category_counts"] == {"python_dependencies": 3}


def test_recommend_priority_action_matrix() -> None:
    assert recommend_priority_action("blocked", "pyproject.toml")[0] == "p0"
    assert recommend_priority_action("blocked", "github_actions")[0] == "p1"
    assert recommend_priority_action("manual_review", "github_actions")[0] == "p1"
    assert recommend_priority_action("manual_review", "pyproject.toml")[0] == "p2"
    assert recommend_priority_action("safe_review", "pyproject.toml")[0] == "p3"


def test_profiles_exports_dev_tooling_review() -> None:
    assert "dev_tooling_review" in PROFILES
    cfg = PROFILES["dev_tooling_review"]
    assert "surfaces" in cfg
    assert "safe_packages" in cfg
    assert "surface_metadata" in cfg


def test_build_recommended_update_queue_tiebreak_lex_topic() -> None:
    """Same worst priority and bucket size → lexicographic topic_id wins."""
    findings = [
        {
            "surface": "pyproject.toml",
            "item_name": "z-pkg",
            "current_spec": "x",
            "classification": "manual_review",
            "reason": "r",
            "category": "python_dependencies",
            "description": "d",
            "recommended_priority": "p2",
            "recommended_action": "a",
        },
        {
            "surface": "pyproject.toml",
            "item_name": "a-pkg",
            "current_spec": "x",
            "classification": "manual_review",
            "reason": "r",
            "category": "python_dependencies",
            "description": "d",
            "recommended_priority": "p2",
            "recommended_action": "a",
        },
        {
            "surface": "github_actions",
            "item_name": "org/act@1",
            "current_spec": "1",
            "classification": "manual_review",
            "reason": "r",
            "category": "ci_integrations",
            "description": "d",
            "recommended_priority": "p2",
            "recommended_action": "a",
        },
        {
            "surface": "github_actions",
            "item_name": "org/other@1",
            "current_spec": "1",
            "classification": "manual_review",
            "reason": "r",
            "category": "ci_integrations",
            "description": "d",
            "recommended_priority": "p2",
            "recommended_action": "a",
        },
    ]
    q = build_recommended_update_queue(findings)
    assert [e["topic_id"] for e in q] == ["ci_integrations", "python_dependencies"]
    nt, reason = next_recommended_topic_and_reason(q)
    assert nt == "ci_integrations"
    assert "ci_integrations" in reason


def test_next_topic_none_when_empty() -> None:
    q = build_recommended_update_queue([])
    nt, reason = next_recommended_topic_and_reason(q)
    assert nt == "none"
    assert "No findings" in reason
