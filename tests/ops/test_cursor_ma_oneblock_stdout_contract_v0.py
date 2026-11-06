"""Stdout/scaffold contract for scripts/ops/cursor_ma_oneblock.py (v0).

Does not execute the emitted shell scaffold; asserts stable substrings only.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "scripts" / "ops" / "cursor_ma_oneblock.py"


def test_cursor_ma_oneblock_stdout_contract_v0() -> None:
    payload = "peak-trade-cursor-ma-oneblock-contract-v0"
    proc = subprocess.run(
        [sys.executable, str(_SCRIPT)],
        cwd=str(ROOT),
        input=payload + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stderr == ""
    out = proc.stdout
    assert 'printf "%s\\n" "CONTEXT: REPO ROOT + CURRENT BRANCH"' in out
    assert 'printf "%s\\n" "INPUT (USER STATUS)"' in out
    assert payload in out
    assert (
        'printf "%s\\n" "CURSOR MULTI-AGENT ORCHESTRATOR: NEXT ACTIONS (single consolidated block)"'
        in out
    )
    assert "cat <<'MSG'" in out
