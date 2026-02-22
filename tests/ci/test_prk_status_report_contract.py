from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_prk_status_report_assets_exist():
    assert Path(".github/workflows/prk-prj-status-report.yml").exists()
    assert Path("scripts/ci/prj_status_report.py").exists()
    assert Path("scripts/ci/prj_status_report_schema.json").exists()
    assert Path(".github/workflows/prj-scheduled-shadow-paper-features-smoke.yml").exists()


def test_prk_status_report_output_version_and_schema(tmp_path: Path) -> None:
    """Contract: report JSON includes output_version and basic schema compliance."""
    runs_json = [
        {
            "id": 1,
            "run_number": 1,
            "event": "schedule",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2026-02-22T12:00:00Z",
            "updated_at": "2026-02-22T12:01:00Z",
            "html_url": "https://example.invalid/1",
        }
    ]
    in_path = tmp_path / "runs.json"
    out_dir = tmp_path / "out"
    in_path.write_text(json.dumps(runs_json), encoding="utf-8")

    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/prj_status_report.py",
            "--input",
            str(in_path),
            "--output-dir",
            str(out_dir),
            "--limit",
            "10",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
        env={"PRJ_REPORTS_DIR": str(out_dir), **os.environ},
    )
    assert r.returncode == 0, r.stderr or r.stdout

    out_json = out_dir / "prj_status_latest.json"
    assert out_json.exists()
    obj = json.loads(out_json.read_text(encoding="utf-8"))

    assert "output_version" in obj
    assert isinstance(obj["output_version"], int)
    assert obj["output_version"] >= 1
    assert "generated_utc" in obj
    assert "runs_count" in obj
    assert "counts" in obj
    assert "runs" in obj
