import json
import subprocess
import sys
from pathlib import Path


def test_mock_ok(tmp_path: Path):
    outdir = tmp_path / "out"
    outdir.mkdir()
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/execution_evidence_producer.py",
            "--out-dir",
            str(outdir),
            "--mock-profile",
            "ok",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 0
    obj = json.loads((outdir / "execution_evidence.json").read_text(encoding="utf-8"))
    assert obj["status"] == "OK"
    assert obj["sample_size"] == 100


def test_missing(tmp_path: Path):
    outdir = tmp_path / "out"
    outdir.mkdir()
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/execution_evidence_producer.py",
            "--out-dir",
            str(outdir),
            "--mock-profile",
            "missing",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 0
    obj = json.loads((outdir / "execution_evidence.json").read_text(encoding="utf-8"))
    assert obj["status"] == "MISSING_INPUT"
