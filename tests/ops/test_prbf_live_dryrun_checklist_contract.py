import json
import subprocess
import sys
from pathlib import Path


def test_ok(tmp_path: Path):
    stab = {"overall_ok": True}
    read = {"decision": "GO"}
    (tmp_path / "s.json").write_text(json.dumps(stab), encoding="utf-8")
    (tmp_path / "r.json").write_text(json.dumps(read), encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ops/live_dryrun_checklist.py",
            "--stability",
            str(tmp_path / "s.json"),
            "--readiness",
            str(tmp_path / "r.json"),
            "--out-dir",
            str(out),
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 0
    assert any(p.name.startswith("live_dryrun_checklist_") for p in out.iterdir())


def test_fail(tmp_path: Path):
    stab = {"overall_ok": False}
    read = {"decision": "NO_GO"}
    (tmp_path / "s.json").write_text(json.dumps(stab), encoding="utf-8")
    (tmp_path / "r.json").write_text(json.dumps(read), encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ops/live_dryrun_checklist.py",
            "--stability",
            str(tmp_path / "s.json"),
            "--readiness",
            str(tmp_path / "r.json"),
            "--out-dir",
            str(out),
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 2
