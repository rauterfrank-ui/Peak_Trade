"""Smoke tests for scripts/ops/verify_registry_pointer_artifacts.py (NO-LIVE)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "scripts" / "ops" / "verify_registry_pointer_artifacts.py"


def test_verify_registry_pointer_artifacts_help_lists_no_live() -> None:
    p = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, p.stderr
    # argparse may wrap the description across lines (e.g. "NO-\nLIVE")
    assert "NO-LIVE" in p.stdout.replace("\n", "")


def test_verify_registry_pointer_artifacts_main_returns_1_missing_pointer(tmp_path: Path) -> None:
    sys.path.insert(0, str(ROOT / "scripts" / "ops"))
    import verify_registry_pointer_artifacts as v  # noqa: E402

    missing = tmp_path / "missing.pointer"
    code = v.main([str(missing)])
    assert code == 1
