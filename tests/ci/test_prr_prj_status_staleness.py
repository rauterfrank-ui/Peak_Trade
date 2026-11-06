"""Tests for PR-J status report staleness policy (NO_TRADE when last success too old)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def run_report(tmp_path: Path, runs_json: str, now: str, stale_hours: str) -> dict:
    inpath = tmp_path / "runs.json"
    outdir = tmp_path / "out"
    outdir.mkdir()
    inpath.write_text(runs_json, encoding="utf-8")
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/prj_status_report.py",
            "--input",
            str(inpath),
            "--output-dir",
            str(outdir),
            "--limit",
            "10",
            "--now",
            now,
            "--stale-hours",
            stale_hours,
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
        env={"PRJ_REPORTS_DIR": str(outdir), **os.environ},
    )
    assert r.returncode == 0, r.stderr or r.stdout
    obj = json.loads((outdir / "prj_status_latest.json").read_text(encoding="utf-8"))
    return obj


def test_not_stale(tmp_path: Path) -> None:
    """When last success is within threshold, no NO_TRADE policy."""
    runs = (
        '[{"id":1,"run_number":1,"event":"schedule","status":"completed",'
        '"conclusion":"success","created_at":"2026-02-22T15:00:00Z",'
        '"updated_at":"2026-02-22T15:01:00Z","html_url":"https://example.invalid/1"}]'
    )
    obj = run_report(tmp_path, runs, now="2026-02-22T16:00:00Z", stale_hours="36")
    assert "policy" not in obj or obj.get("policy", {}).get("action") != "NO_TRADE"


def test_stale_sets_no_trade(tmp_path: Path) -> None:
    """When last success exceeds threshold, policy.action=NO_TRADE, PRJ_STATUS_STALE."""
    runs = (
        '[{"id":1,"run_number":1,"event":"schedule","status":"completed",'
        '"conclusion":"success","created_at":"2026-02-20T00:00:00Z",'
        '"updated_at":"2026-02-20T00:01:00Z","html_url":"https://example.invalid/1"}]'
    )
    obj = run_report(tmp_path, runs, now="2026-02-22T16:00:00Z", stale_hours="24")
    assert obj["policy"]["action"] == "NO_TRADE"
    assert "PRJ_STATUS_STALE" in obj["policy"]["reason_codes"]


def test_no_success_sets_no_trade(tmp_path: Path) -> None:
    """When no successful schedule run exists, policy.action=NO_TRADE, PRJ_STATUS_NO_SUCCESS."""
    runs = (
        '[{"id":1,"run_number":1,"event":"workflow_dispatch","status":"completed",'
        '"conclusion":"failure","created_at":"2026-02-22T12:00:00Z",'
        '"updated_at":"2026-02-22T12:01:00Z","html_url":"https://example.invalid/1"}]'
    )
    obj = run_report(tmp_path, runs, now="2026-02-22T16:00:00Z", stale_hours="36")
    assert obj["policy"]["action"] == "NO_TRADE"
    assert "PRJ_STATUS_NO_SUCCESS" in obj["policy"]["reason_codes"]
