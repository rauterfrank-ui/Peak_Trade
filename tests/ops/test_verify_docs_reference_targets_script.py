"""
Test suite for verify_docs_reference_targets.sh script.

Tests validate that the script correctly:
- Accepts valid references and ignores patterns (wildcards, commands, directories, code blocks)
- Detects missing target references
"""

import subprocess
from pathlib import Path

import pytest


def get_repo_root() -> Path:
    """Get the repository root directory."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())


def run_verify_script(docs_root: Path, repo_root: Path) -> subprocess.CompletedProcess:
    """Run the verify_docs_reference_targets.sh script with given arguments."""
    script_path = repo_root / "scripts" / "ops" / "verify_docs_reference_targets.sh"

    result = subprocess.run(
        [
            str(script_path),
            "--docs-root",
            str(docs_root),
            "--repo-root",
            str(repo_root),
        ],
        capture_output=True,
        text=True,
        cwd=str(repo_root),
    )
    return result


def test_fixtures_pass():
    """
    Test that the 'pass' fixtures succeed.

    The pass fixtures contain:
    - Valid references to existing files
    - Patterns that should be ignored (wildcards, commands, directories)
    - Missing targets inside code blocks (should be ignored)
    """
    repo_root = get_repo_root()
    docs_root = repo_root / "tests" / "fixtures" / "docs_reference_targets" / "pass"

    result = run_verify_script(docs_root, repo_root)

    # Print output for debugging if test fails
    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

    assert result.returncode == 0, (
        f"Expected exit code 0 for pass fixtures, got {result.returncode}. Output: {result.stdout}"
    )


def test_fixtures_fail_detects_missing_target():
    """
    Test that the 'fail' fixtures correctly detect missing targets.

    The fail fixtures contain a reference to a non-existent file that should be detected.
    """
    repo_root = get_repo_root()
    docs_root = repo_root / "tests" / "fixtures" / "docs_reference_targets" / "fail"

    result = run_verify_script(docs_root, repo_root)

    # Print output for debugging
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    # Should fail (non-zero exit code)
    assert result.returncode != 0, (
        f"Expected non-zero exit code for fail fixtures, got {result.returncode}"
    )

    # Check that the missing target is mentioned in output
    output = result.stdout + result.stderr
    assert "__fixture_missing_target__347__nope.md" in output, (
        "Expected missing target '__fixture_missing_target__347__nope.md' "
        f"to be mentioned in output. Output: {output}"
    )
