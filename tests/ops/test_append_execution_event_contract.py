import json
import subprocess
import sys
from pathlib import Path


def test_appends_jsonl(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "out").mkdir()
    repo_root = Path(__file__).resolve().parent.parent.parent
    outp = tmp_path / "out/ops/execution_events/execution_events.jsonl"
    r = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts/ops/append_execution_event.py"),
            "--out",
            str(outp),
            "--event-type",
            "rate_limit",
            "--level",
            "warning",
            "--is-anomaly",
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert r.returncode == 0, r.stderr
    lines = outp.read_text(encoding="utf-8").splitlines()
    obj = json.loads(lines[0])
    assert obj["event_type"] == "rate_limit"
    assert obj["is_anomaly"] is True
