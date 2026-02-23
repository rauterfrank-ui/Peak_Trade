"""Tests for PR-K health dashboard JSON v1 output."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_dashboard_json_v1(tmp_path: Path) -> None:
    inp = tmp_path / "hs.json"
    outdir = tmp_path / "out"
    outdir.mkdir()
    inp.write_text(
        json.dumps(
            {
                "generated_at": "2026-02-22T00:00:00Z",
                "status": "OK",
                "policy_action": "none",
                "reason_codes": [],
                "last_success_age_hours": 1.0,
                "runs_sampled": 10,
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

    obj = json.loads((outdir / "prj_health_dashboard_v1.json").read_text(encoding="utf-8"))
    assert obj["dashboard_version"] == 1
    assert obj["status"] == "OK"
    assert obj["runs_sampled"] == 10
