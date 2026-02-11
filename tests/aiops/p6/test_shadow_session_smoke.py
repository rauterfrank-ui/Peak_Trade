from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


def _run(repo: Path, outdir: Path, run_id: str) -> list[Path]:
    cli = repo / "scripts" / "aiops" / "run_shadow_session.py"
    spec = repo / "tests" / "fixtures" / "p6" / "shadow_session_min_v0.json"
    assert cli.is_file()
    assert spec.is_file()
    p = subprocess.run(
        [
            sys.executable,
            str(cli),
            "--spec",
            str(spec),
            "--outdir",
            str(outdir),
            "--run-id",
            run_id,
            "--evidence",
            "1",
            "--dry-run",
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(repo),
    )
    return [Path(ln.strip()) for ln in p.stdout.splitlines() if ln.strip()]


def test_shadow_session_outputs_exist() -> None:
    repo = Path(__file__).resolve().parents[3]
    with tempfile.TemporaryDirectory() as td:
        outdir = Path(td) / "shadow"
        paths = _run(repo, outdir, "fixed")
        # summary + p4c + p5a + manifest (4 paths)
        assert len(paths) == 4
        for p in paths:
            assert p.is_file()
        summary = json.loads(paths[0].read_text(encoding="utf-8"))
        assert summary["schema_version"].startswith("p6.")
        assert "steps" in summary
