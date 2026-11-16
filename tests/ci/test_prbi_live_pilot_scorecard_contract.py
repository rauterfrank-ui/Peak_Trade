import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


def _write_stability(tmp_path: Path, age: int) -> None:
    generated = datetime.now(timezone.utc)
    stab = {
        "overall_ok": True,
        "generated_at": generated.isoformat(),
        "results": [
            {"name": name, "created_at": (generated - timedelta(hours=age)).isoformat()}
            for name in ("PR-J", "PR-K")
        ],
    }
    (tmp_path / "stab.json").write_text(json.dumps(stab), encoding="utf-8")


@pytest.mark.parametrize("age", [1, 37])
def test_ready_requires_fresh_stability(tmp_path: Path, age):
    _write_stability(tmp_path, age)
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
    assert r.returncode == (2 if age == 37 else 0)
    obj = json.loads((out / "live_pilot_scorecard.json").read_text(encoding="utf-8"))
    assert obj["decision"] == ("NO_GO" if age == 37 else "READY_FOR_LIVE_PILOT")
    assert obj["hard_blocks"] == (["STABILITY_GATE_STALE"] if age == 37 else [])


def test_no_go_on_errors(tmp_path: Path):
    _write_stability(tmp_path, 1)
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
