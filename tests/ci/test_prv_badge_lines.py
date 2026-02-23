"""Tests for PR-V: machine-parseable badge lines in status/health markdown."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_status(tmp_path: Path, runs_json: list, now: str = "2026-02-22T16:00:00Z") -> list[str]:
    inpath = tmp_path / "runs.json"
    outdir = tmp_path / "out"
    outdir.mkdir(parents=True)
    inpath.write_text(json.dumps(runs_json), encoding="utf-8")
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
            "24",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 0, r.stderr or r.stdout
    return (outdir / "prj_status_latest.md").read_text(encoding="utf-8").splitlines()


def test_badge_first_line_ok(tmp_path: Path) -> None:
    runs = [
        {
            "id": 1,
            "run_number": 1,
            "event": "schedule",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2026-02-22T15:00:00Z",
            "updated_at": "2026-02-22T15:01:00Z",
            "html_url": "https://example.invalid/1",
        }
    ]
    md = _run_status(tmp_path, runs)
    assert md[0].startswith("PRJ_BADGE:")
    assert "OK" in md[0]
    assert "policy=none" in md[0] or "policy=" in md[0]


def test_badge_first_line_stale(tmp_path: Path) -> None:
    runs = [
        {
            "id": 1,
            "run_number": 1,
            "event": "schedule",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2026-02-20T00:00:00Z",
            "updated_at": "2026-02-20T00:01:00Z",
            "html_url": "https://example.invalid/1",
        }
    ]
    md = _run_status(tmp_path, runs)
    assert md[0].startswith("PRJ_BADGE:")
    assert "STALE" in md[0]


def test_health_badge_first_line(tmp_path: Path) -> None:
    """PRJ_HEALTH_BADGE is first line of prj_health_summary.md."""
    obj = {
        "runs_count": 50,
        "counts": {},
        "runs": [],
        "last_successful_schedule_age_hours": 1.2,
    }
    inpath = tmp_path / "prj_status_latest.json"
    outdir = tmp_path / "reports"
    outdir.mkdir(parents=True)
    inpath.write_text(json.dumps(obj), encoding="utf-8")

    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/prk_health_summary.py",
            "--input",
            str(inpath),
            "--output-dir",
            str(outdir),
            "--now",
            "2026-02-22T00:00:00Z",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 0, r.stderr or r.stdout
    md = (outdir / "prj_health_summary.md").read_text(encoding="utf-8").splitlines()
    assert md[0].startswith("PRJ_HEALTH_BADGE:")
    assert "OK" in md[0]
    assert "runs=50" in md[0]
