"""Smoke tests for p7_ctl CLI (help output + dry-run style)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "ops" / "p7_ctl.py"), *args],
        text=True,
        capture_output=True,
        cwd=str(cwd or ROOT),
    )


def test_p7_ctl_help() -> None:
    p = _run(["-h"])
    assert p.returncode == 0
    assert "p7_ctl" in p.stdout.lower() or "p7" in p.stdout.lower()


def test_p7_ctl_reconcile_missing_arg_fails() -> None:
    p = _run(["reconcile"])
    assert p.returncode != 0


def test_p7_ctl_reconcile_tmpdir_runs(tmp_path: Path) -> None:
    # Minimal fake p7 dir to exercise runner arg plumbing (runner will decide pass/fail)
    p7 = tmp_path / "p7"
    p7.mkdir()
    (p7 / "p7_fills.json").write_text("[]", encoding="utf-8")
    (p7 / "p7_account.json").write_text('{"equity": 1.0}', encoding="utf-8")
    (p7 / "p7_evidence_manifest.json").write_text(
        '{"artifacts":["p7_fills.json","p7_account.json"]}', encoding="utf-8"
    )

    p = _run(["reconcile", str(p7)])
    # accept either success(0) or failure(1); must not crash
    assert p.returncode in (0, 1)
    assert p.stdout.strip() != "" or p.stderr.strip() != ""
