import json
import subprocess
import sys
from pathlib import Path


def test_gate_ok(tmp_path: Path):
    prk = [
        {
            "databaseId": 1,
            "status": "completed",
            "conclusion": "success",
            "createdAt": "2026-02-24T10:00:00Z",
            "event": "schedule",
        }
    ]
    prj = [
        {
            "databaseId": 2,
            "status": "completed",
            "conclusion": "success",
            "createdAt": "2026-02-24T11:00:00Z",
            "event": "schedule",
        }
    ]
    prk_path = tmp_path / "prk.json"
    prj_path = tmp_path / "prj.json"
    outdir = tmp_path / "out"
    outdir.mkdir()
    prk_path.write_text(json.dumps(prk), encoding="utf-8")
    prj_path.write_text(json.dumps(prj), encoding="utf-8")

    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/stability_gate.py",
            "--out-dir",
            str(outdir),
            "--now",
            "2026-02-24T12:00:00Z",
            "--prk-runs-json",
            str(prk_path),
            "--prj-runs-json",
            str(prj_path),
            "--max-age-hours-prk",
            "36",
            "--max-age-hours-prj",
            "36",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 0, r.stderr
    obj = json.loads((outdir / "stability_gate.json").read_text(encoding="utf-8"))
    assert obj["overall_ok"] is True


def test_gate_stale(tmp_path: Path):
    prk = [
        {
            "databaseId": 1,
            "status": "completed",
            "conclusion": "success",
            "createdAt": "2026-02-20T00:00:00Z",
            "event": "schedule",
        }
    ]
    prj = [
        {
            "databaseId": 2,
            "status": "completed",
            "conclusion": "success",
            "createdAt": "2026-02-24T11:00:00Z",
            "event": "schedule",
        }
    ]
    prk_path = tmp_path / "prk.json"
    prj_path = tmp_path / "prj.json"
    outdir = tmp_path / "out"
    outdir.mkdir()
    prk_path.write_text(json.dumps(prk), encoding="utf-8")
    prj_path.write_text(json.dumps(prj), encoding="utf-8")

    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/stability_gate.py",
            "--out-dir",
            str(outdir),
            "--now",
            "2026-02-24T12:00:00Z",
            "--prk-runs-json",
            str(prk_path),
            "--prj-runs-json",
            str(prj_path),
            "--max-age-hours-prk",
            "36",
            "--max-age-hours-prj",
            "36",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 2
    obj = json.loads((outdir / "stability_gate.json").read_text(encoding="utf-8"))
    assert obj["overall_ok"] is False
