"""Tests for PR-K health dashboard format generator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_formats_created(tmp_path: Path) -> None:
    inp = tmp_path / "hs.json"
    outdir = tmp_path / "out"
    outdir.mkdir()
    inp.write_text(
        json.dumps(
            {
                "generated_at": "2026-02-22T00:00:00Z",
                "status": "STALE",
                "policy_action": "NO_TRADE",
                "reason_codes": ["PRJ_STATUS_STALE"],
                "last_success_age_hours": 48.0,
                "runs_sampled": 50,
                "output_version": 1,
            }
        ),
        encoding="utf-8",
    )

    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/prk_health_dashboard.py",
            "--input",
            str(inp),
            "--output-dir",
            str(outdir),
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 0, r.stderr or r.stdout

    assert (outdir / "prj_health_dashboard.txt").exists()
    assert (outdir / "prj_health_dashboard.csv").exists()
    assert (outdir / "prj_health_dashboard.md").exists()

    prom = (outdir / "prj_health_dashboard.txt").read_text(encoding="utf-8")
    assert 'prj_health_status{status="STALE"} 1' in prom
    assert "prj_health_last_success_age_hours 48.0" in prom
