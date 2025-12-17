"""Smoke tests for operator convenience scripts."""
import os
import subprocess
from pathlib import Path


def test_install_shortcuts_script_exists():
    """Verify install_desktop_shortcuts.sh exists and is executable."""
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "install_desktop_shortcuts.sh"

    assert script.exists(), f"Script not found: {script}"
    assert os.access(script, os.X_OK), f"Script not executable: {script}"


def test_install_shortcuts_dry_run():
    """Test install_desktop_shortcuts.sh --dry-run (graceful on all platforms)."""
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "install_desktop_shortcuts.sh"

    # Dry run should work even if Desktop doesn't exist (it just shows what would happen)
    result = subprocess.run(
        [str(script), "--dry-run"],
        cwd=str(repo_root),
        capture_output=True,
        text=True
    )

    # Exit code 0 (success) or 1 (no Desktop dir on non-macOS) is acceptable for dry-run
    assert result.returncode in [0, 1], f"Unexpected exit code: {result.returncode}\n{result.stderr}"

    if result.returncode == 0:
        assert "Would create:" in result.stdout, "Dry run should show what would be created"


def test_install_shortcuts_help():
    """Test install_desktop_shortcuts.sh --help."""
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "install_desktop_shortcuts.sh"

    result = subprocess.run(
        [str(script), "--help"],
        cwd=str(repo_root),
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Help command failed: {result.stderr}"
    assert "install_desktop_shortcuts.sh" in result.stdout
    assert "Usage:" in result.stdout
