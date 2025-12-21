"""
Tests für scripts/ops/run_merge_log_workflow_robust.sh Wrapper

Offline, deterministisch, nutzt PEAK_TRADE_TEST_MODE=1
um keine echten Git/GitHub Aktionen zu triggern.
"""

import subprocess
from pathlib import Path


# ============================================================================
# Helpers
# ============================================================================

SCRIPT_PATH = Path(__file__).parent.parent / "scripts/ops/run_merge_log_workflow_robust.sh"


def run_wrapper(*args: str) -> subprocess.CompletedProcess:
    """
    Führt den Wrapper-Script im TEST_MODE aus.

    Args:
        *args: Positional arguments für das Script (z.B. "207", "auto")

    Returns:
        CompletedProcess mit stdout/stderr/returncode
    """
    env = {"PEAK_TRADE_TEST_MODE": "1"}
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
