"""Smoke tests for scripts/ops/validate_evidence_index.py (NO-LIVE)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "scripts" / "ops" / "validate_evidence_index.py"


def test_validate_evidence_index_help_lists_no_live_scope() -> None:
    p = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, p.stderr
    assert "NO-LIVE" in p.stdout


def test_validate_evidence_index_main_returns_2_when_index_missing() -> None:
    sys.path.insert(0, str(ROOT / "scripts" / "ops"))
    import validate_evidence_index as v  # noqa: E402

    code = v.main(["--index-path", "this/path/does/not/exist/EVIDENCE_INDEX.md"])
    assert code == 2
