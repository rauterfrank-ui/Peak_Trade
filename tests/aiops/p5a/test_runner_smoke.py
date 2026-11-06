from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def test_p5a_runner_emits_json(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[3]
    runner = repo / "scripts" / "aiops" / "run_l3_trade_plan_advisory_p5a.py"
    inp = repo / "tests" / "fixtures" / "p5a" / "input_min_v0.json"
    assert runner.is_file()
    assert inp.is_file()

    outdir = tmp_path / "out"
    outdir.mkdir(parents=True, exist_ok=True)

    p = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--input",
            str(inp),
            "--outdir",
            str(outdir),
            "--evidence",
            "1",
            "--dry-run",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [ln.strip() for ln in p.stdout.splitlines() if ln.strip()]
    assert len(lines) == 2
    out_json = Path(lines[0])
    out_mf = Path(lines[1])
    assert out_json.is_file()
    assert out_mf.is_file()

    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["schema_version"].startswith("p5a.")
    assert "stance" in data
    assert "no_trade" in data
