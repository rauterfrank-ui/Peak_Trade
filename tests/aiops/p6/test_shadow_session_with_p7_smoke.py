from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


def _run_with_p7(
    repo: Path, outdir: Path, run_id: str, spec: str, p7_enable: int = 1
) -> list[Path]:
    cli = repo / "scripts" / "aiops" / "run_shadow_session.py"
    spec_path = repo / spec
    assert cli.is_file()
    assert spec_path.is_file()
    cmd = [
        sys.executable,
        str(cli),
        "--spec",
        str(spec_path),
        "--outdir",
        str(outdir),
        "--run-id",
        run_id,
        "--evidence",
        "1",
        "--dry-run",
        "--p7-enable",
        str(p7_enable),
    ]
    p = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        cwd=str(repo),
    )
    return [Path(ln.strip()) for ln in p.stdout.splitlines() if ln.strip()]


def test_shadow_session_with_p7_outputs_exist() -> None:
    repo = Path(__file__).resolve().parents[3]
    spec = "tests/fixtures/p6/shadow_session_min_v1_p7.json"
    with tempfile.TemporaryDirectory() as td:
        outdir = Path(td) / "shadow"
        paths = _run_with_p7(repo, outdir, "fixed", spec, p7_enable=1)
        assert len(paths) >= 5
        for p in paths:
            assert p.is_file()
        summary = json.loads(paths[0].read_text(encoding="utf-8"))
        assert summary["schema_version"].startswith("p6.")
        assert "steps" in summary
        assert "p7_outputs" in summary
        assert "p7_account_summary" in summary
        assert "p7_fills" in summary["p7_outputs"]
        assert "p7_account" in summary["p7_outputs"]
        assert "cash" in summary["p7_account_summary"]
        assert "positions" in summary["p7_account_summary"]


def test_shadow_session_without_p7_skips_p7() -> None:
    repo = Path(__file__).resolve().parents[3]
    spec = "tests/fixtures/p6/shadow_session_min_v0.json"
    with tempfile.TemporaryDirectory() as td:
        outdir = Path(td) / "shadow"
        paths = _run_with_p7(repo, outdir, "fixed", spec, p7_enable=0)
        assert len(paths) == 4
        summary = json.loads(paths[0].read_text(encoding="utf-8"))
        assert summary["p7_outputs"] == {}
        assert summary["p7_account_summary"] == {}
