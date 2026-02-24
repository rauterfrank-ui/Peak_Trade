import json
import subprocess
import sys
from pathlib import Path


def test_ready_for_testnet_without_exec_evidence_is_not_ready(tmp_path: Path):
    stab = {"overall_ok": True}
    live = {"decision": "GO"}
    (tmp_path / "stab.json").write_text(json.dumps(stab), encoding="utf-8")
    (tmp_path / "live.json").write_text(json.dumps(live), encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/shadow_testnet_readiness_scorecard.py",
            "--out-dir",
            str(out),
            "--stability",
            str(tmp_path / "stab.json"),
            "--live-readiness",
            str(tmp_path / "live.json"),
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 2
    obj = json.loads((out / "shadow_testnet_scorecard.json").read_text(encoding="utf-8"))
    assert obj["decision"] == "CONTINUE_SHADOW"


def test_no_go_if_stability_fail(tmp_path: Path):
    stab = {"overall_ok": False}
    live = {"decision": "GO"}
    (tmp_path / "stab.json").write_text(json.dumps(stab), encoding="utf-8")
    (tmp_path / "live.json").write_text(json.dumps(live), encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/shadow_testnet_readiness_scorecard.py",
            "--out-dir",
            str(out),
            "--stability",
            str(tmp_path / "stab.json"),
            "--live-readiness",
            str(tmp_path / "live.json"),
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 2
    obj = json.loads((out / "shadow_testnet_scorecard.json").read_text(encoding="utf-8"))
    assert obj["decision"] == "NO_GO"
