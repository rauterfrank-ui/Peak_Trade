import json
from pathlib import Path

from scripts.ops.registry_alerts_gate import main as gate_main


def test_alerts_gate_exit_2_when_alerts(tmp_path: Path, monkeypatch):
    reg = tmp_path / "r.jsonl"
    reg.write_text(
        json.dumps(
            {
                "ts_utc": "20260304T000000Z",
                "ops_status_exit": 2,
                "prbi_decision": "CONTINUE_TESTNET",
                "prbg_status": "OK",
                "prbg_error_count": 1,
                "prbg_sample_size": 10,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "alerts.txt"
    monkeypatch.setenv("PYTHONUTF8", "1")
    import sys

    argv = ["x", "--registry", str(reg), "--out", str(out)]
    monkeypatch.setattr(sys, "argv", argv)
    rc = gate_main()
    assert rc == 2
    assert out.exists()
    assert "OPS_STATUS_FAIL" in out.read_text(encoding="utf-8")


def test_alerts_gate_exit_0_when_clean(tmp_path: Path, monkeypatch):
    reg = tmp_path / "r.jsonl"
    reg.write_text(
        json.dumps(
            {
                "ts_utc": "20260304T000000Z",
                "ops_status_exit": 0,
                "prbi_decision": "READY_FOR_LIVE_PILOT",
                "prbg_status": "OK",
                "prbg_error_count": 0,
                "prbg_sample_size": 150,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "alerts.txt"
    import sys

    argv = ["x", "--registry", str(reg), "--out", str(out)]
    monkeypatch.setattr(sys, "argv", argv)
    rc = gate_main()
    assert rc == 0
    assert out.exists()
    assert out.read_text(encoding="utf-8").strip() == ""
