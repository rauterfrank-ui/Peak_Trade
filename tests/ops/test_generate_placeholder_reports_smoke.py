"""Smoke test for placeholder inventory report generator (stdlib, offline)."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "scripts" / "ops" / "placeholders" / "generate_placeholder_reports.py"


def test_generate_placeholder_reports_help_lists_no_live_scope():
    """CLI --help documents NO-LIVE / local triage scope."""
    p = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert p.returncode == 0, p.stderr
    out = p.stdout
    assert "NO-LIVE" in out
    assert "place orders" in out.lower()
    assert "--output-dir" in out


def test_generate_placeholder_reports_exits_zero_and_writes_core_artifacts(tmp_path):
    """Runs the script against the real repo scan; writes reports to a temp dir."""
    cmd = [
        sys.executable,
        str(_SCRIPT),
        "--output-dir",
        str(tmp_path),
    ]
    p = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert p.returncode == 0, p.stderr or p.stdout

    inventory = tmp_path / "TODO_PLACEHOLDER_INVENTORY.md"
    target_map = tmp_path / "TODO_PLACEHOLDER_TARGET_MAP.md"
    assert inventory.is_file()
    assert target_map.is_file()

    inv_text = inventory.read_text(encoding="utf-8")
    tgt_text = target_map.read_text(encoding="utf-8")
    assert inv_text.startswith("# TODO/Placeholder Inventory\n")
    assert "## Pattern Summary" in inv_text
    assert tgt_text.startswith("# TODO/Placeholder Target Map (Inventory Addendum)\n")
    assert "## Pattern:" in tgt_text
