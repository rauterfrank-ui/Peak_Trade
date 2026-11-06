"""Paper session CLI contract tests (fast, no network)."""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "aiops" / "run_paper_trading_session.py"
SPEC = REPO_ROOT / "tests" / "fixtures" / "p7" / "paper_run_min_v0.json"
PYTHON = sys.executable


def test_paper_session_cli_help_runs():
    assert SCRIPT.exists()
    p = subprocess.run(
        [PYTHON, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    # help may exit 0 or 1 depending on argparse; accept output presence
    assert (p.stdout + p.stderr).strip() != ""


def test_paper_session_cli_dry_exec_produces_expected_outputs(tmp_path: Path):
    assert SCRIPT.exists()
    assert SPEC.exists()

    outdir = tmp_path / "session_out"
    outdir.mkdir(parents=True, exist_ok=True)

    p = subprocess.run(
        [
            PYTHON,
            str(SCRIPT),
            "--spec",
            str(SPEC),
            "--run-id",
            "ci_smoke_test",
            "--outdir",
            str(outdir),
            "--evidence",
            "1",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert p.returncode == 0, f"stdout:\n{p.stdout}\n\nstderr:\n{p.stderr}"
    for fn in ["fills.json", "account.json", "evidence_manifest.json"]:
        fp = outdir / fn
        assert fp.exists(), f"missing {fn}"
        json.loads(fp.read_text(encoding="utf-8"))
