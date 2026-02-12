from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


def _run(repo: Path) -> tuple[dict, dict]:
    runner = repo / "scripts" / "aiops" / "run_l3_trade_plan_advisory_p5a.py"
    inp = repo / "tests" / "fixtures" / "p5a" / "input_min_v0.json"
    assert runner.is_file()
    assert inp.is_file()

    with tempfile.TemporaryDirectory() as td:
        outdir = Path(td)
        p = subprocess.run(
            [
                sys.executable,
                str(runner),
                "--input",
                str(inp),
                "--outdir",
                str(outdir),
                "--run-id",
                "fixed",
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
        j = json.loads(Path(lines[0]).read_text(encoding="utf-8"))
        m = json.loads(Path(lines[1]).read_text(encoding="utf-8"))
        return j, m


def test_outputs_deterministic() -> None:
    repo = Path(__file__).resolve().parents[3]
    j1, m1 = _run(repo)
    j2, m2 = _run(repo)
    assert j1 == j2
    assert m1["files"] == m2["files"]
