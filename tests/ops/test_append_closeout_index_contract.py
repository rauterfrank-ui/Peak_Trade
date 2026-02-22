import json
import os
from pathlib import Path
import subprocess
import sys


def test_append_closeout_index_contract(tmp_path: Path, monkeypatch):
    idx = tmp_path / "index.jsonl"
    env = os.environ.copy()
    env["PT_EVIDENCE_DIR"] = "out/ops/evidence_x"
    env["PT_CLOSEOUT_KIND"] = "UNIT_TEST"
    env["PT_CLOSEOUT_NOTES"] = "note"
    env["PT_CLOSEOUT_INDEX"] = str(idx)
    env["PT_HEAD"] = "deadbeef"

    r = subprocess.run(
        [sys.executable, "scripts/ops/append_closeout_index.py"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr

    lines = idx.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert obj["timestamp"].endswith("Z")
    assert obj["kind"] == "UNIT_TEST"
    assert obj["evidence_dir"] == "out/ops/evidence_x"
    assert obj["head"] == "deadbeef"
    assert obj["notes"] == "note"


def test_requires_evidence_dir(tmp_path: Path):
    idx = tmp_path / "index.jsonl"
    env = os.environ.copy()
    env.pop("PT_EVIDENCE_DIR", None)
    env["PT_CLOSEOUT_INDEX"] = str(idx)
    env["PT_HEAD"] = "deadbeef"

    r = subprocess.run(
        [sys.executable, "scripts/ops/append_closeout_index.py"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
