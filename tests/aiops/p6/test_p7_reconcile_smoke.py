"""Smoke tests for P7 reconciliation checks (run_p7_reconcile.py)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_reconcile(repo: Path, outdir: Path, spec: str | None = None) -> int:
    recon = repo / "scripts" / "aiops" / "run_p7_reconcile.py"
    assert recon.is_file()
    cmd = [sys.executable, str(recon), str(outdir)]
    if spec:
        cmd.extend(["--spec", str(repo / spec)])
    return subprocess.run(cmd, cwd=str(repo), capture_output=True, text=True).returncode


def test_p7_reconcile_on_shadow_output() -> None:
    """Run shadow session with P7, then reconcile on output."""
    repo = Path(__file__).resolve().parents[3]
    cli = repo / "scripts" / "aiops" / "run_shadow_session.py"
    spec = repo / "tests/fixtures/p6/shadow_session_min_v1_p7.json"
    p7_spec = "tests/fixtures/p7/paper_run_min_v0.json"
    assert cli.is_file()
    assert spec.is_file()

    import tempfile

    with tempfile.TemporaryDirectory() as td:
        outdir = Path(td) / "shadow"
        subprocess.run(
            [
                sys.executable,
                str(cli),
                "--spec",
                str(spec),
                "--outdir",
                str(outdir),
                "--run-id",
                "recon_smoke",
                "--evidence",
                "1",
                "--dry-run",
                "--p7-enable",
                "1",
            ],
            check=True,
            capture_output=True,
            cwd=str(repo),
        )
        assert (outdir / "p7_fills.json").is_file()
        assert (outdir / "p7_account.json").is_file()

        code = _run_reconcile(repo, outdir, spec=p7_spec)
        assert code == 0


def test_p7_reconcile_invariants_only_no_spec() -> None:
    """Reconcile without --spec: only cash/position invariants (no expected vs actual)."""
    repo = Path(__file__).resolve().parents[3]
    spec = repo / "tests/fixtures/p6/shadow_session_min_v1_p7.json"

    import tempfile

    with tempfile.TemporaryDirectory() as td:
        outdir = Path(td) / "shadow"
        subprocess.run(
            [
                sys.executable,
                str(repo / "scripts/aiops/run_shadow_session.py"),
                "--spec",
                str(spec),
                "--outdir",
                str(outdir),
                "--run-id",
                "inv",
                "--p7-enable",
                "1",
            ],
            check=True,
            capture_output=True,
            cwd=str(repo),
        )
        code = _run_reconcile(repo, outdir, spec=None)
        assert code == 0


def test_p7_reconcile_malformed_fails() -> None:
    """Malformed account (negative position) should fail."""
    repo = Path(__file__).resolve().parents[3]

    import tempfile

    with tempfile.TemporaryDirectory() as td:
        outdir = Path(td)
        acct = outdir / "p7_account.json"
        acct.write_text(
            json.dumps({"cash": 100, "positions": {"BTC": -1}, "schema_version": "p7.account.v0"})
        )
        code = _run_reconcile(repo, outdir, spec=None)
        assert code == 1
