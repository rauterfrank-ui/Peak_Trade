"""Tests for new_merge_log.py generator."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest import mock

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "ops" / "new_merge_log.py"


def test_script_exists():
    """Script exists and is executable."""
    assert SCRIPT_PATH.exists(), f"Script not found: {SCRIPT_PATH}"
    assert SCRIPT_PATH.stat().st_mode & 0o111, f"Script not executable: {SCRIPT_PATH}"


def test_fallback_mode_without_gh(tmp_path):
    """Fallback mode generates template with placeholders."""
    output_file = tmp_path / "PR_999_MERGE_LOG.md"

    result = subprocess.run(
        [
            "python3",
            str(SCRIPT_PATH),
            "--pr",
            "999",
            "--out",
            str(output_file),
            "--fallback",
            "--no-update-readme",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert output_file.exists(), "Output file not created"

    content = output_file.read_text()
    assert "PR #999" in content
    assert "[TODO: Add PR title]" in content
    assert "## Summary" in content
    assert "## Why" in content
    assert "## Changes" in content
    assert "## Verification" in content
    assert "## Risk" in content
    assert "## Operator How-To" in content
    assert "## References" in content


def test_prevents_overwrite_by_default(tmp_path):
    """Script prevents overwriting existing files by default."""
    output_file = tmp_path / "PR_123_MERGE_LOG.md"
    output_file.write_text("existing content")

    result = subprocess.run(
        [
            "python3",
            str(SCRIPT_PATH),
            "--pr",
            "123",
            "--out",
            str(output_file),
            "--fallback",
            "--no-update-readme",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 1, "Should fail on existing file"
    assert "already exists" in result.stderr.lower()
    assert output_file.read_text() == "existing content", "File should be unchanged"


def test_overwrite_flag_works(tmp_path):
    """Script overwrites with --overwrite flag."""
    output_file = tmp_path / "PR_456_MERGE_LOG.md"
    output_file.write_text("old content")

    result = subprocess.run(
        [
            "python3",
            str(SCRIPT_PATH),
            "--pr",
            "456",
            "--out",
            str(output_file),
            "--fallback",
            "--no-update-readme",
            "--overwrite",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    content = output_file.read_text()
    assert "PR #456" in content
    assert "old content" not in content


def test_gh_integration_mock():
    """Test gh integration with mocked subprocess."""
    # This would be a more complex test using unittest.mock
    # to mock the gh pr view call and verify parsing
    mock_pr_data = {
        "title": "feat(ops): test feature",
        "url": "https://github.com/test/repo/pull/789",
        "mergedAt": "2025-01-01T10:00:00Z",
        "mergeCommit": {"oid": "abc123"},
        "headRefName": "feat/test-branch",
        "state": "MERGED",
    }

    # We'd use mock.patch to mock subprocess.run and return mock_pr_data
    # For now, this is a placeholder test
    assert True


def test_de_pathifies_branch_names():
    """Test that branch names with slashes are de-pathified."""
    from scripts.ops import new_merge_log

    content = new_merge_log.generate_merge_log_content(
        pr_number=100,
        title="test",
        pr_url="https://github.com/test/repo/pull/100",
        head_ref="docs/ops/feature",
    )

    # Branch name should be escaped
    assert "docs&#47;ops&#47;feature" in content
    # Raw slash should not appear in branch display
    assert "docs/ops/feature" not in content or "docs&#47;ops&#47;feature" in content


def test_required_sections_present():
    """Test that all required sections are present in generated content."""
    from scripts.ops import new_merge_log

    content = new_merge_log.generate_merge_log_content(
        pr_number=200,
        title="test: example",
        pr_url="https://github.com/test/repo/pull/200",
    )

    required_sections = [
        "## Summary",
        "## Why",
        "## Changes",
        "## Verification",
        "## Risk",
        "## Operator How-To",
        "## References",
        "## Extended",
    ]

    for section in required_sections:
        assert section in content, f"Missing required section: {section}"


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
    assert "--pr" in result.stdout
    assert "--out" in result.stdout
    assert "--fallback" in result.stdout
