import json
import subprocess
import sys
from pathlib import Path


def test_jsonl_input_parsing(tmp_path: Path):
    inp = tmp_path / "events.jsonl"
    inp.write_text(
        "\n".join(
            [
                json.dumps({"event_type": "rate_limit", "level": "warning"}),
                json.dumps({"event_type": "order_error", "level": "error"}),
                json.dumps({"is_anomaly": True}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    outdir = tmp_path / "out"
    outdir.mkdir()
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/execution_evidence_producer.py",
            "--out-dir",
            str(outdir),
            "--input",
            str(inp),
            "--input-format",
            "jsonl",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 0
    obj = json.loads((outdir / "execution_evidence.json").read_text(encoding="utf-8"))
    assert obj["status"] == "OK"
    assert obj["sample_size"] == 3
    assert obj["anomaly_count"] >= 2
    assert obj["error_count"] >= 1


def test_csv_input_parsing(tmp_path: Path):
    inp = tmp_path / "events.csv"
    inp.write_text(
        "event_type,level,is_anomaly,is_error\n"
        "reconnect,warning,false,false\n"
        "fill_error,error,false,true\n",
        encoding="utf-8",
    )
    outdir = tmp_path / "out"
    outdir.mkdir()
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/execution_evidence_producer.py",
            "--out-dir",
            str(outdir),
            "--input",
            str(inp),
            "--input-format",
            "csv",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 0
    obj = json.loads((outdir / "execution_evidence.json").read_text(encoding="utf-8"))
    assert obj["status"] == "OK"
    assert obj["sample_size"] == 2
    assert obj["anomaly_count"] >= 1
    assert obj["error_count"] >= 1
