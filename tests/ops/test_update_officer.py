from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.ops.update_officer import (
    build_summary,
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
    assert report["officer_version"] == "v0-min"
    assert report["profile"] == "dev_tooling_review"
    assert "findings" in report
    assert "summary" in report
    assert report["summary"]["total_findings"] > 0

    for finding in report["findings"]:
        assert "surface" in finding
        assert "item_name" in finding
        assert "classification" in finding
        assert finding["classification"] in {"safe_review", "manual_review", "blocked"}


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
    names = {f["item_name"] for f in findings}
    assert "pytest" in names or "ruff" in names, f"expected dev deps, got {names}"


def test_scan_github_actions_finds_refs() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    findings = scan_github_actions(repo_root)
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
        },
        {
            "surface": "pyproject.toml",
            "item_name": "mystery-pkg",
            "current_spec": "",
            "classification": "manual_review",
            "reason": "unknown",
        },
        {
            "surface": "pyproject.toml",
            "item_name": "fastapi",
            "current_spec": ">=0.104.0",
            "classification": "blocked",
            "reason": "runtime-adjacent",
        },
    ]
    summary = build_summary(findings)
    assert summary["total_findings"] == 3
    assert summary["safe_review"] == 1
    assert summary["manual_review"] == 1
    assert summary["blocked"] == 1


def test_profiles_exports_dev_tooling_review() -> None:
    assert "dev_tooling_review" in PROFILES
    cfg = PROFILES["dev_tooling_review"]
    assert "surfaces" in cfg
    assert "safe_packages" in cfg
