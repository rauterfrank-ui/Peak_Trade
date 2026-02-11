from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def test_runner_accepts_from_p4c(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[3]
    runner = repo / "scripts" / "aiops" / "run_l3_trade_plan_advisory_p5a.py"
    inp = repo / "tests" / "fixtures" / "p5a" / "input_min_v0.json"
    p4c = repo / "tests" / "fixtures" / "p4c" / "capsule_min_v0.json"

    # generate a p4c outlook json in tmp
    p4c_runner = repo / "scripts" / "aiops" / "run_l2_market_outlook_capsule.py"
    outdir = tmp_path / "p4c"
    outdir.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(
        [
            sys.executable,
            str(p4c_runner),
            "--capsule",
            str(p4c),
            "--outdir",
            str(outdir),
            "--evidence",
            "0",
            "--dry-run",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    p4c_out = Path([ln.strip() for ln in p.stdout.splitlines() if ln.strip()][0])
    assert p4c_out.is_file()

    # run p5a with from-p4c
    outdir2 = tmp_path / "p5a"
    outdir2.mkdir(parents=True, exist_ok=True)
    q = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--input",
            str(inp),
            "--from-p4c",
            str(p4c_out),
            "--outdir",
            str(outdir2),
            "--evidence",
            "0",
            "--dry-run",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [ln.strip() for ln in q.stdout.splitlines() if ln.strip()]
    assert len(lines) >= 1
    out_json = Path(lines[0])
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert "stance" in data
