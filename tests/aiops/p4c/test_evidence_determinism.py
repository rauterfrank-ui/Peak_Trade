from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


def _run(repo: Path, run_id: str) -> tuple[dict, dict]:
    runner = repo / "scripts" / "aiops" / "run_l2_market_outlook_capsule.py"
    capsule = repo / "tests" / "fixtures" / "p4c" / "capsule_min_v0.json"
    assert runner.is_file()
    assert capsule.is_file()

    with tempfile.TemporaryDirectory() as td:
        outdir = Path(td)
        p = subprocess.run(
            [
                sys.executable,
                str(runner),
                "--capsule",
                str(capsule),
                "--outdir",
                str(outdir),
                "--run-id",
                run_id,
                "--evidence",
                "1",
                "--deterministic",
                "--dry-run",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        lines = [ln.strip() for ln in p.stdout.splitlines() if ln.strip()]
        assert len(lines) == 3, f"expected 3 outputs (l2, alias, manifest), got {len(lines)}"
        out_json = Path(lines[0])
        out_mf = Path(lines[2])
        data = json.loads(out_json.read_text(encoding="utf-8"))
        mf = json.loads(out_mf.read_text(encoding="utf-8"))
        return data, mf


def test_deterministic_outputs() -> None:
    repo = Path(__file__).resolve().parents[3]
    d1, m1 = _run(repo, "fixed")
    d2, m2 = _run(repo, "fixed")

    assert d1 == d2
    assert m1["meta"] == m2["meta"]
    assert m1["files"] == m2["files"]
    for e in m1["files"]:
        assert isinstance(e.get("sha256"), str) and len(e["sha256"]) == 64
