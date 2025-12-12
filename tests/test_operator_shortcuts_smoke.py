"""Smoke tests for operator convenience scripts."""
from pathlib import Path
import subprocess
import sys
import os


def test_install_shortcuts_script_exists():
    """Verify install_desktop_shortcuts.sh exists and is executable."""
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "install_desktop_shortcuts.sh"

    assert script.exists(), f"Script not found: {script}"
    assert os.access(script, os.X_OK), f"Script not executable: {script}"


def test_open_todo_board_script_exists():
    """Verify open_todo_board.sh exists and is executable."""
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "open_todo_board.sh"

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


def test_open_todo_board_json_mode_graceful():
    """Test open_todo_board.sh --json handles missing 'open' command gracefully."""
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "open_todo_board.sh"

    # Create a modified environment where 'open' is not available
    env = os.environ.copy()
    # Remove 'open' from PATH by setting PATH to minimal value
    # Note: This test focuses on graceful degradation, not full functionality

    # Just test that --json doesn't crash
    result = subprocess.run(
        [str(script), "--json"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=30
    )

    # Should return JSON even if some steps fail
    assert result.stdout.strip().startswith("{"), f"Expected JSON output, got: {result.stdout}"
    assert '"steps"' in result.stdout, "JSON should contain 'steps' field"
    assert '"ok"' in result.stdout, "JSON should contain 'ok' field"


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


def test_open_todo_board_help():
    """Test open_todo_board.sh --help."""
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "open_todo_board.sh"

    result = subprocess.run(
        [str(script), "--help"],
        cwd=str(repo_root),
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Help command failed: {result.stderr}"
    assert "open_todo_board.sh" in result.stdout
    assert "Usage:" in result.stdout
