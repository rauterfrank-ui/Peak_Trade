from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def test_p90_metrics_emits_json(tmp_path: Path) -> None:
    # create minimal fake OUT_DIR with one tick and p76 result
    run_dir = tmp_path / "run_x"
    tick = run_dir / "tick_20260216T000000Z" / "p76"
    tick.mkdir(parents=True)
    (tick / "P76_RESULT.txt").write_text("P76_READY out_dir=x run_id=y mode=shadow\n")

    env = os.environ.copy()
    env["OUT_DIR"] = str(run_dir)
    env["MIN_TICKS"] = "1"
    env["MAX_AGE_SEC"] = "999999"

    out = subprocess.check_output(
        ["bash", "scripts/ops/p90_supervisor_metrics_v1.sh"],
        env=env,
        text=True,
        cwd=Path(__file__).resolve().parents[2],
    ).strip()

    data = json.loads(out)
    assert data["version"] == "p90_supervisor_metrics_v1"
    assert data["tick_count"] == 1
    assert data["latest_p76_status"] == "ready"
