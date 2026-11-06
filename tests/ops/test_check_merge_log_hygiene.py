"""Tests for check_merge_log_hygiene.py."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "ops" / "check_merge_log_hygiene.py"


def test_script_exists():
    """Script exists and is executable."""
    assert SCRIPT_PATH.exists(), f"Script not found: {SCRIPT_PATH}"
    assert SCRIPT_PATH.stat().st_mode & 0o111, f"Script not executable: {SCRIPT_PATH}"


def test_clean_file_passes(tmp_path):
    """Clean markdown file passes all checks."""
    test_file = tmp_path / "clean.md"
    test_file.write_text(
        """# Test Merge Log

## Summary
This is a clean file with no issues.

## Changes
- Updated documentation
- Fixed typos

## References
- PR: https://github.com/test/repo/pull/123
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT_PATH), str(test_file)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0, f"Clean file should pass: {result.stdout}"
    assert "All checks passed" in result.stdout


def test_detects_forbidden_local_paths(tmp_path):
    """Detects forbidden local path patterns."""
    test_cases = [
        ("/Users/frank/code", "forbidden-path"),
        ("/home/user/projects", "forbidden-path"),
        ("C:\\Users\\frank", "forbidden-path"),
        ("~/Documents/file.txt", "forbidden-path"),
    ]

    for pattern, expected_category in test_cases:
        test_file = tmp_path / f"test_{expected_category}.md"
        test_file.write_text(
            f"""# Test

Path reference: {pattern}
""",
            encoding="utf-8",
        )

        result = subprocess.run(
            ["python3", str(SCRIPT_PATH), str(test_file)],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
        )

        assert result.returncode == 1, f"Should detect {pattern}"
        assert expected_category.upper() in result.stdout
        # Check that the pattern or at least the detected forbidden prefix is mentioned
        assert (
            "/Users/" in result.stdout
            or "/home/" in result.stdout
            or "C:\\" in result.stdout
            or "~/" in result.stdout
        )


def test_detects_bidi_control_chars(tmp_path):
    """Detects bidirectional control characters."""
    # U+202E: RIGHT-TO-LEFT OVERRIDE
    test_file = tmp_path / "bidi.md"
    test_file.write_text(
        "# Test\n\nThis has a bidi char: \u202e hidden text",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT_PATH), str(test_file)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 1, "Should detect bidi control char"
    assert "FORMAT-CHAR" in result.stdout or "format-char" in result.stdout.lower()


def test_detects_zero_width_chars(tmp_path):
    """Detects zero-width characters."""
    # U+200B: ZERO WIDTH SPACE
    test_file = tmp_path / "zwsp.md"
    test_file.write_text(
        "# Test\n\nThis has\u200ba zero width space",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT_PATH), str(test_file)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 1, "Should detect zero width space"
    assert "FORMAT-CHAR" in result.stdout or "format-char" in result.stdout.lower()


def test_detects_bom(tmp_path):
    """Detects BOM (Byte Order Mark)."""
    test_file = tmp_path / "bom.md"
    # Write BOM at start of file
    test_file.write_text(
        "\ufeff# Test\n\nContent with BOM",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT_PATH), str(test_file)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 1, "Should detect BOM"
    assert "BOM" in result.stdout or "bom" in result.stdout.lower()


def test_allows_normal_control_chars(tmp_path):
    """Allows normal control characters (newline, tab, carriage return)."""
    test_file = tmp_path / "normal_controls.md"
    test_file.write_text(
        "# Test\n\nTabs:\tare\tok\nNewlines are ok\r\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT_PATH), str(test_file)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0, "Should allow normal control chars"


def test_handles_multiple_files(tmp_path):
    """Handles multiple files at once."""
    clean_file = tmp_path / "clean.md"
    clean_file.write_text("# Clean\n\nNo issues here.")

    dirty_file = tmp_path / "dirty.md"
    dirty_file.write_text("# Dirty\n\nPath: /Users/test")

    result = subprocess.run(
        ["python3", str(SCRIPT_PATH), str(clean_file), str(dirty_file)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 1, "Should fail due to dirty file"
    assert "forbidden-path" in result.stdout.lower()
    assert str(dirty_file) in result.stdout


def test_handles_glob_patterns(tmp_path):
    """Handles glob patterns."""
    for i in range(3):
        test_file = tmp_path / f"PR_{i}_MERGE_LOG.md"
        test_file.write_text(f"# PR {i}\n\nClean content")

    # Note: This test might need adjustment based on how glob expansion works
    # in the script vs shell
    result = subprocess.run(
        ["python3", str(SCRIPT_PATH), str(tmp_path / "PR_*_MERGE_LOG.md")],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
        shell=False,
    )

    # The script should handle the pattern
    assert "3 files" in result.stdout or result.returncode == 0


def test_verbose_mode(tmp_path):
    """Verbose mode shows file being checked."""
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test\n\nClean")

    result = subprocess.run(
        ["python3", str(SCRIPT_PATH), "-v", str(test_file)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    assert "[check]" in result.stdout or str(test_file) in result.stdout


def test_cli_help():
    """Test that --help works."""
    result = subprocess.run(
        ["python3", str(SCRIPT_PATH), "--help"],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0
    assert "hygiene" in result.stdout.lower()
    assert "files" in result.stdout.lower()


def test_reports_line_and_column(tmp_path):
    """Reports line and column numbers for findings."""
    test_file = tmp_path / "test.md"
    test_file.write_text(
        """# Line 1
Normal line 2
Line 3 with /Users/bad/path here
Another line 4
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT_PATH), str(test_file)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 1
    # Should report line 3
    assert ":3:" in result.stdout or "line 3" in result.stdout.lower()
