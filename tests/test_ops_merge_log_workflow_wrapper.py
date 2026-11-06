"""
Tests für scripts/ops/run_merge_log_workflow_robust.sh Wrapper

Offline, deterministisch, nutzt PEAK_TRADE_TEST_MODE=1
um keine echten Git/GitHub Aktionen zu triggern.
"""

import subprocess
from pathlib import Path
from typing import Optional


# ============================================================================
# Helpers
# ============================================================================

SCRIPT_PATH = Path(__file__).parent.parent / "scripts/ops/run_merge_log_workflow_robust.sh"


def run_wrapper(*args: str, extra_env: Optional[dict] = None) -> subprocess.CompletedProcess:
    """
    Führt den Wrapper-Script im TEST_MODE aus.

    Args:
        *args: Positional arguments für das Script (z.B. "207", "auto")
        extra_env: Optionale zusätzliche Environment-Variablen

    Returns:
        CompletedProcess mit stdout/stderr/returncode
    """
    env = {"PEAK_TRADE_TEST_MODE": "1"}
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        env=env,
    )
    return result


# ============================================================================
# Tests
# ============================================================================


def test_missing_pr_arg():
    """Test: Fehlende PR-Nummer -> exit 2 + Usage"""
    result = run_wrapper()

    assert result.returncode == 2, f"Expected exit 2, got {result.returncode}"
    assert "Missing required argument" in result.stdout
    assert "Usage:" in result.stdout
    assert "Modes:" in result.stdout


def test_invalid_mode():
    """Test: Ungültiger MODE -> exit 2 + Valid modes"""
    result = run_wrapper("207", "invalid_mode")

    assert result.returncode == 2, f"Expected exit 2, got {result.returncode}"
    assert "Invalid mode" in result.stdout
    assert "Valid modes:" in result.stdout


def test_auto_mode():
    """Test: auto mode -> exit 0, keine --no-merge/--no-web flags"""
    result = run_wrapper("207", "auto")

    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}"
    assert "TEST_MODE: Resolved configuration" in result.stdout
    assert "PR: 207" in result.stdout
    assert "MODE: auto" in result.stdout

    # Args sollte leer sein (keine flags)
    assert "ARGS:" in result.stdout
    # Keine --no-merge oder --no-web flags
    assert "--no-merge" not in result.stdout
    assert "--no-web" not in result.stdout


def test_review_mode():
    """Test: review mode -> exit 0, --no-merge flag gesetzt"""
    result = run_wrapper("207", "review")

    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}"
    assert "TEST_MODE: Resolved configuration" in result.stdout
    assert "PR: 207" in result.stdout
    assert "MODE: review" in result.stdout
    assert "--no-merge" in result.stdout
    # Kein --no-web
    output_after_args = result.stdout.split("ARGS:")[-1]
    assert "--no-web" not in output_after_args or output_after_args.index(
        "--no-merge"
    ) < output_after_args.index("--no-web")


def test_no_web_mode():
    """Test: no-web mode -> exit 0, --no-web flag gesetzt"""
    result = run_wrapper("207", "no-web")

    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}"
    assert "TEST_MODE: Resolved configuration" in result.stdout
    assert "PR: 207" in result.stdout
    assert "MODE: no-web" in result.stdout
    assert "--no-web" in result.stdout
    # Kein --no-merge in der ARGS Zeile
    output_after_args = result.stdout.split("ARGS:")[-1]
    assert "--no-merge" not in output_after_args or output_after_args.index(
        "--no-web"
    ) < output_after_args.index("--no-merge")


def test_manual_mode():
    """Test: manual mode -> exit 0, BOTH --no-web AND --no-merge"""
    result = run_wrapper("207", "manual")

    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}"
    assert "TEST_MODE: Resolved configuration" in result.stdout
    assert "PR: 207" in result.stdout
    assert "MODE: manual" in result.stdout
    assert "--no-web" in result.stdout
    assert "--no-merge" in result.stdout


def test_default_mode_is_auto():
    """Test: Kein MODE angegeben -> default ist auto"""
    result = run_wrapper("207")

    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}"
    assert "MODE: auto" in result.stdout
    # Keine flags
    assert "--no-merge" not in result.stdout
    assert "--no-web" not in result.stdout


# ============================================================================
# Depth=1 Policy Tests
# ============================================================================


def test_depth1_policy_blocks_merge_log_pr():
    """Test: Depth=1 policy blocks merge-log PRs (exit 2)"""
    # Simulate a merge-log PR title
    result = run_wrapper(
        "207",
        "auto",
        extra_env={"PEAK_TEST_PR_TITLE": "docs(ops): add PR #123 merge log"},
    )

    assert result.returncode == 2, f"Expected exit 2, got {result.returncode}"
    assert "⛔ Depth=1 Policy Violation" in result.stdout
    assert "Refusing to generate a merge log for a merge-log PR" in result.stdout
    assert "ALLOW_RECURSIVE=1" in result.stdout


def test_depth1_policy_allows_with_override():
    """Test: ALLOW_RECURSIVE=1 bypasses depth-1 guard"""
    result = run_wrapper(
        "207",
        "auto",
        extra_env={
            "PEAK_TEST_PR_TITLE": "docs(ops): add PR #123 merge log",
            "ALLOW_RECURSIVE": "1",
        },
    )

    # Should NOT exit 2, but proceed to TEST_MODE success
    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}"
    assert "⛔ Depth=1 Policy Violation" not in result.stdout
    assert "TEST_MODE: Resolved configuration" in result.stdout


def test_depth1_policy_allows_normal_pr():
    """Test: Normal PR (not merge-log) passes depth-1 check"""
    result = run_wrapper(
        "207",
        "auto",
        extra_env={"PEAK_TEST_PR_TITLE": "feat(core): add new feature"},
    )

    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}"
    assert "✅ Depth=1 check passed" in result.stdout
    assert "TEST_MODE: Resolved configuration" in result.stdout


def test_depth1_policy_pattern_variations():
    """Test: Different merge-log title patterns are all blocked"""
    test_cases = [
        "docs(ops): add PR #123 merge log",
        "docs(ops): add PR #1 merge log",
        "docs(ops): add PR #99999 merge log",
    ]

    for title in test_cases:
        result = run_wrapper("207", "auto", extra_env={"PEAK_TEST_PR_TITLE": title})
        assert result.returncode == 2, f"Expected exit 2 for title: {title}"
        assert "⛔ Depth=1 Policy Violation" in result.stdout


def test_depth1_policy_non_matching_patterns():
    """Test: Similar but non-matching titles are allowed"""
    test_cases = [
        "docs(ops): add merge log for PR #123",  # Different word order
        "docs: add PR #123 merge log",  # Missing (ops)
        "chore(ops): add PR #123 merge log",  # Different scope
        "docs(ops): add PR #123 final report",  # Not "merge log"
        "docs(ops): update PR #123 merge log",  # "update" not "add"
    ]

    for title in test_cases:
        result = run_wrapper("207", "auto", extra_env={"PEAK_TEST_PR_TITLE": title})
        # Should pass depth-1 check and reach TEST_MODE
        assert result.returncode == 0, f"Expected exit 0 for title: {title}"
        assert "⛔ Depth=1 Policy Violation" not in result.stdout
