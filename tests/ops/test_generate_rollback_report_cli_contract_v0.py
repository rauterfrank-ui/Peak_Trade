"""CLI contract tests for scripts/ops/generate_rollback_report.py (placeholder stub)."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "scripts" / "ops" / "generate_rollback_report.py"

_EXPECTED_LINE_1 = "Placeholder stub: scripts/ops/generate_rollback_report.py is not implemented."
_EXPECTED_LINE_2 = "This file exists only to satisfy documentation reference targets."


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_rollback_report", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_cli_exits_2_with_placeholder_stdout(capsys) -> None:
    mod = _load_module()
    assert mod.main() == 2
    out = capsys.readouterr().out
    assert _EXPECTED_LINE_1 in out
    assert _EXPECTED_LINE_2 in out
    assert capsys.readouterr().err == ""


def test_cli_subprocess_contract() -> None:
    p = subprocess.run(
        [sys.executable, str(_SCRIPT)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert p.returncode == 2
    assert _EXPECTED_LINE_1 in p.stdout
    assert _EXPECTED_LINE_2 in p.stdout
    assert p.stderr == ""
