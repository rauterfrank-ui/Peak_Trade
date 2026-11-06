"""Tests for PR-K health summary generator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run(tmp_path: Path, src_obj: dict) -> dict:
    inpath = tmp_path / "prj_status_latest.json"
    outdir = tmp_path / "reports"
    outdir.mkdir(parents=True)
    inpath.write_text(json.dumps(src_obj), encoding="utf-8")

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
    out = json.loads((outdir / "prj_health_summary.json").read_text(encoding="utf-8"))
    return out


def test_ok(tmp_path: Path) -> None:
    obj = {
        "runs_count": 1,
        "counts": {},
        "runs": [],
        "last_successful_schedule_age_hours": 1.0,
    }
    out = run(tmp_path, obj)
    assert out["status"] == "OK"


def test_stale(tmp_path: Path) -> None:
    obj = {
        "runs_count": 1,
        "counts": {},
        "runs": [],
        "policy": {"action": "NO_TRADE", "reason_codes": ["PRJ_STATUS_STALE"]},
        "last_successful_schedule_age_hours": 99.0,
    }
    out = run(tmp_path, obj)
    assert out["status"] == "STALE"


def test_no_success(tmp_path: Path) -> None:
    obj = {
        "runs_count": 0,
        "counts": {},
        "runs": [],
        "policy": {"action": "NO_TRADE", "reason_codes": ["PRJ_STATUS_NO_SUCCESS"]},
    }
    out = run(tmp_path, obj)
    assert out["status"] == "NO_SUCCESS"
