import json
from pathlib import Path

from scripts.ops.append_done_registry import append_registry


def test_append_registry_parses_and_appends(tmp_path: Path) -> None:
    done = tmp_path / "MORNING_ONE_SHOT_DONE_X.txt"
    done.write_text(
        "\n".join(
            [
                "DONE: morning_one_shot",
                "ts_utc: 20260304T000000Z",
                "ops_status_exit: 0",
                "prbi_decision: READY_FOR_LIVE_PILOT",
                "prbi_score: 100",
                "prbg_status: OK",
                "prbg_sample_size: 152",
                "prbg_anomaly_count: 0",
                "prbg_error_count: 0",
                "evidence_dir: out/ops/morning_one_shot_20260304T000000Z",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    reg = tmp_path / "registry.jsonl"
    rec = append_registry(done, reg, sha256_ok=True)
    assert reg.exists()
    lines = reg.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert obj["kind"] == "morning_one_shot"
    assert obj["ts_utc"] == "20260304T000000Z"
    assert obj["prbg_sample_size"] == 152
    assert obj["sha256_ok"] is True
