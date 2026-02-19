from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def test_p4c_runner_emits_json(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[3]
    runner = repo / "scripts" / "aiops" / "run_l2_market_outlook_capsule.py"
    assert runner.is_file()

    capsule = repo / "tests" / "fixtures" / "p4c" / "capsule_min_v0.json"
    assert capsule.is_file()

    outdir = tmp_path / "out"
    outdir.mkdir(parents=True, exist_ok=True)

    p = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--capsule",
            str(capsule),
            "--outdir",
            str(outdir),
            "--dry-run",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    lines = [ln.strip() for ln in p.stdout.splitlines() if ln.strip()]
    assert len(lines) in (2, 3), f"expected 2 (no evidence) or 3 (with evidence), got {len(lines)}"
    out_json = Path(lines[0])
    assert out_json.is_file()

    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert "meta" in data
    assert data["meta"].get("schema_version")
    assert "outlook" in data
    if len(lines) == 3:
        mf = Path(lines[2])
        assert mf.is_file()
        m = json.loads(mf.read_text(encoding="utf-8"))
        assert m.get("meta", {}).get("kind") == "p4c_evidence_manifest"
        assert isinstance(m.get("files", []), list)
    assert data["outlook"]["regime"] in (
        None,
        "NEUTRAL",
        "RISK_ON",
        "RISK_OFF",
        "HIGH_VOL",
    )
