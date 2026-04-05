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
    assert "--prefix" in out


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
    assert "### Top files under `src/`" in tgt_text
    assert "### Top files under `scripts/`" in tgt_text


def test_generate_placeholder_reports_prefix_filters_scan_and_lists_scope(tmp_path):
    """--prefix limits the walk; inventory notes Scan scope; triage headings match prefix."""
    cmd = [
        sys.executable,
        str(_SCRIPT),
        "--output-dir",
        str(tmp_path),
        "--prefix",
        "src/strategies/ideas/",
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
    inv_text = inventory.read_text(encoding="utf-8")
    tgt_text = target_map.read_text(encoding="utf-8")
    assert "- Scan scope:" in inv_text
    assert "`src/strategies/ideas/`" in inv_text
    assert "### Top files under `src/strategies/ideas/`" in tgt_text
    assert "### Top files under `src/`" not in tgt_text


def test_generate_placeholder_reports_rejects_output_dir_that_is_file(tmp_path):
    """--output-dir must not point at an existing file (fail before repo scan)."""
    bad = tmp_path / "not_a_dir.txt"
    bad.write_text("x", encoding="utf-8")
    p = subprocess.run(
        [sys.executable, str(_SCRIPT), "--output-dir", str(bad)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert p.returncode == 1
    combined = (p.stderr or "") + (p.stdout or "")
    assert "directory" in combined.lower()
    assert "file" in combined.lower()
