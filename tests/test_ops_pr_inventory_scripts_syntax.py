"""
Test syntax and basic structure of ops PR inventory/labeling scripts.
"""

import subprocess
from pathlib import Path

import pytest


def test_pr_inventory_script_exists():
    """PR inventory script exists and is executable."""
    script = Path("scripts/ops/pr_inventory_full.sh")
    assert script.exists(), f"Script not found: {script}"
    assert script.stat().st_mode & 0o111, f"Script not executable: {script}"


def test_label_merge_log_script_exists():
    """Label merge-log script exists and is executable."""
    script = Path("scripts/ops/label_merge_log_prs.sh")
    assert script.exists(), f"Script not found: {script}"
    assert script.stat().st_mode & 0o111, f"Script not executable: {script}"


def test_pr_inventory_help():
    """PR inventory script shows help without errors."""
    result = subprocess.run(
        ["scripts/ops/pr_inventory_full.sh", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, f"Help failed: {result.stderr}"
    assert "Usage:" in result.stdout
    assert "pr_inventory_full.sh" in result.stdout
    assert "OUT_ROOT" in result.stdout


def test_label_merge_log_help():
    """Label merge-log script shows help without errors."""
    result = subprocess.run(
        ["scripts/ops/label_merge_log_prs.sh", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, f"Help failed: {result.stderr}"
    assert "Usage:" in result.stdout
    assert "label_merge_log_prs.sh" in result.stdout
    assert "DRY_RUN" in result.stdout


def test_pr_inventory_shebang():
    """PR inventory script has correct shebang."""
    script = Path("scripts/ops/pr_inventory_full.sh")
    first_line = script.read_text().splitlines()[0]
    assert first_line == "#!/usr/bin/env bash", f"Invalid shebang: {first_line}"


def test_label_merge_log_shebang():
    """Label merge-log script has correct shebang."""
    script = Path("scripts/ops/label_merge_log_prs.sh")
    first_line = script.read_text().splitlines()[0]
    assert first_line == "#!/usr/bin/env bash", f"Invalid shebang: {first_line}"


def test_pr_inventory_has_set_flags():
    """PR inventory script has safety flags (set -euo pipefail)."""
    script = Path("scripts/ops/pr_inventory_full.sh")
    content = script.read_text()
    assert "set -euo pipefail" in content, "Missing safety flags"


def test_label_merge_log_has_set_flags():
    """Label merge-log script has safety flags (set -euo pipefail)."""
    script = Path("scripts/ops/label_merge_log_prs.sh")
    content = script.read_text()
    assert "set -euo pipefail" in content, "Missing safety flags"


def test_pr_inventory_has_repo_default():
    """PR inventory script has REPO default."""
    script = Path("scripts/ops/pr_inventory_full.sh")
    content = script.read_text()
    assert 'REPO="${REPO:-' in content, "Missing REPO default"


def test_label_merge_log_has_dry_run_default():
    """Label merge-log script has DRY_RUN=1 default (safe)."""
    script = Path("scripts/ops/label_merge_log_prs.sh")
    content = script.read_text()
    assert 'DRY_RUN="${DRY_RUN:-1}"' in content, "Missing or wrong DRY_RUN default"


def test_pr_inventory_checks_gh_cli():
    """PR inventory script checks for gh CLI."""
    script = Path("scripts/ops/pr_inventory_full.sh")
    content = script.read_text()
    assert "command -v gh" in content, "Missing gh CLI check"


def test_label_merge_log_checks_gh_cli():
    """Label merge-log script checks for gh CLI."""
    script = Path("scripts/ops/label_merge_log_prs.sh")
    content = script.read_text()
    assert "command -v gh" in content, "Missing gh CLI check"


def test_pr_inventory_checks_gh_auth():
    """PR inventory script checks gh auth status."""
    script = Path("scripts/ops/pr_inventory_full.sh")
    content = script.read_text()
    assert "gh auth status" in content, "Missing gh auth check"


def test_label_merge_log_checks_gh_auth():
    """Label merge-log script checks gh auth status."""
    script = Path("scripts/ops/label_merge_log_prs.sh")
    content = script.read_text()
    assert "gh auth status" in content, "Missing gh auth check"


def test_pr_inventory_python_usage():
    """PR inventory script uses python for data processing."""
    script = Path("scripts/ops/pr_inventory_full.sh")
    content = script.read_text()
    assert "python" in content.lower(), "Script should use Python for processing"
    assert "json" in content or "JSON" in content, "Should process JSON"


def test_label_merge_log_merge_log_pattern():
    """Label merge-log script has correct merge-log pattern."""
    script = Path("scripts/ops/label_merge_log_prs.sh")
    content = script.read_text()
    # Should search for "docs(ops): add PR #... merge log" pattern
    assert "docs" in content.lower() and "merge log" in content.lower()
    assert "re.compile" in content or "regex" in content or r"\d+" in content


def test_ops_readme_exists():
    """Ops README documentation exists."""
    readme = Path("docs/ops/README.md")
    assert readme.exists(), f"Ops README not found: {readme}"
    content = readme.read_text()
    assert "PR Inventory" in content or "pr_inventory" in content
    assert "label" in content.lower()
