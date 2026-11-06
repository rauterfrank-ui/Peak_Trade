import json
import subprocess
import sys
from pathlib import Path


def test_ready(tmp_path: Path):
    (tmp_path / "stab.json").write_text(json.dumps({"overall_ok": True}), encoding="utf-8")
    (tmp_path / "live.json").write_text(json.dumps({"decision": "GO"}), encoding="utf-8")
    (tmp_path / "st.json").write_text(
        json.dumps({"decision": "READY_FOR_TESTNET"}), encoding="utf-8"
    )
    (tmp_path / "exe.json").write_text(
        json.dumps(
            {
                "status": "OK",
                "sample_size": 200,
                "anomaly_count": 0,
                "error_count": 0,
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    out.mkdir()
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/live_pilot_scorecard.py",
            "--out-dir",
            str(out),
            "--stability",
            str(tmp_path / "stab.json"),
            "--live-readiness",
            str(tmp_path / "live.json"),
            "--shadow-testnet",
            str(tmp_path / "st.json"),
            "--execution-evidence",
            str(tmp_path / "exe.json"),
            "--min-sample-size",
            "100",
            "--max-anomalies",
            "0",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 0
    obj = json.loads((out / "live_pilot_scorecard.json").read_text(encoding="utf-8"))
    assert obj["decision"] == "READY_FOR_LIVE_PILOT"


def test_no_go_on_errors(tmp_path: Path):
    (tmp_path / "stab.json").write_text(json.dumps({"overall_ok": True}), encoding="utf-8")
    (tmp_path / "live.json").write_text(json.dumps({"decision": "GO"}), encoding="utf-8")
    (tmp_path / "st.json").write_text(
        json.dumps({"decision": "READY_FOR_TESTNET"}), encoding="utf-8"
    )
    (tmp_path / "exe.json").write_text(
        json.dumps(
            {
                "status": "OK",
                "sample_size": 200,
                "anomaly_count": 0,
                "error_count": 1,
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    out.mkdir()
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/live_pilot_scorecard.py",
            "--out-dir",
            str(out),
            "--stability",
            str(tmp_path / "stab.json"),
            "--live-readiness",
            str(tmp_path / "live.json"),
            "--shadow-testnet",
            str(tmp_path / "st.json"),
            "--execution-evidence",
            str(tmp_path / "exe.json"),
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 2
    obj = json.loads((out / "live_pilot_scorecard.json").read_text(encoding="utf-8"))
    assert obj["decision"] == "NO_GO"
