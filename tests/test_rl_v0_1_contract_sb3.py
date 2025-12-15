"""
RL v0.1 Contract Test: SB3 Presence Matrix
===========================================
Tests that the RL v0.1 validation script correctly handles both
stable-baselines3 presence and absence scenarios per v0.1 spec.

v0.1 Spec:
- SB3 missing → exit 0 with status "skipped"
- SB3 present → run smoke tests, exit 0 on pass or exit 1 on fail
"""

import json
import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def repo_root():
    """Get repository root directory."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def validation_script(repo_root):
    """Get path to validation script."""
    script_path = repo_root / "scripts" / "validate_rl_v0_1.sh"
    if not script_path.exists():
        pytest.skip(f"Validation script not found at {script_path}")
    return script_path


@pytest.fixture
def report_dir(repo_root, tmp_path):
    """Create temporary report directory."""
    return tmp_path / "reports" / "rl_v0_1"


def test_sb3_missing_produces_skipped_status(repo_root, validation_script, report_dir):
    """
    Test that when stable-baselines3 is not installed, the validation
    script exits 0 with status "skipped" per v0.1 spec.

    This test runs the validation script in a subprocess and checks:
    1. Exit code is 0 (success)
    2. JSON report has status="skipped"
    3. JSON report has reason="stable_baselines3_not_installed"
    """
    # Skip on Windows
    if os.name == "nt":
        pytest.skip("Bash script not compatible with Windows")

    # Run validation with custom report directory
    env = os.environ.copy()
    env["REPORT_DIR"] = str(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        ["bash", str(validation_script)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )

    # Check exit code
    assert result.returncode == 0, (
        f"Expected exit 0 when SB3 missing, got {result.returncode}\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )

    # Check JSON report
    json_file = report_dir / "validate_rl_v0_1.json"
    assert json_file.exists(), f"JSON report not found at {json_file}"

    with open(json_file) as f:
        report = json.load(f)

    # Validate report structure for skipped scenario
    assert report.get("status") == "skipped", (
        f"Expected status='skipped', got {report.get('status')}"
    )
    assert "stable_baselines3_not_installed" in report.get("reason", ""), (
        f"Expected reason containing 'stable_baselines3_not_installed', "
        f"got {report.get('reason')}"
    )
    assert "ts" in report, "JSON report missing 'ts' field"
    assert "log" in report, "JSON report missing 'log' field"


def test_validation_produces_valid_json_report(repo_root, validation_script, report_dir):
    """
    Test that the validation script always produces a valid JSON report
    with required fields regardless of outcome.

    Required fields:
    - status: "passed" | "skipped" | "failure"
    - ts: ISO 8601 timestamp
    - log: path to log file

    Optional fields (context-dependent):
    - reason: string explaining status
    - smoke_rc: exit code from smoke tests
    - extra_rc: exit code from extra contract tests
    """
    # Skip on Windows
    if os.name == "nt":
        pytest.skip("Bash script not compatible with Windows")

    # Run validation with custom report directory
    env = os.environ.copy()
    env["REPORT_DIR"] = str(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        ["bash", str(validation_script)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )

    # Validation should complete (exit 0 or 1, not crash)
    assert result.returncode in (0, 1), (
        f"Unexpected exit code {result.returncode} (expected 0 or 1)\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )

    # Check JSON report exists and is valid JSON
    json_file = report_dir / "validate_rl_v0_1.json"
    assert json_file.exists(), f"JSON report not found at {json_file}"

    with open(json_file) as f:
        report = json.load(f)

    # Validate required fields
    assert "status" in report, "JSON report missing required 'status' field"
    assert report["status"] in ("passed", "skipped", "failure"), (
        f"Invalid status value: {report['status']}"
    )

    assert "ts" in report, "JSON report missing required 'ts' field"
    assert isinstance(report["ts"], str), "'ts' field must be string"
    # Basic ISO 8601 format check
    assert "T" in report["ts"] and "Z" in report["ts"], (
        f"'ts' field should be ISO 8601 format, got: {report['ts']}"
    )

    assert "log" in report, "JSON report missing required 'log' field"
    assert isinstance(report["log"], str), "'log' field must be string"

    # Context-dependent optional fields
    if report["status"] == "failure":
        assert "reason" in report, (
            "JSON report with status='failure' should include 'reason' field"
        )

    if report.get("reason") == "pytest_failed":
        assert "smoke_rc" in report, (
            "JSON report with reason='pytest_failed' should include 'smoke_rc'"
        )
        assert "extra_rc" in report, (
            "JSON report with reason='pytest_failed' should include 'extra_rc'"
        )


def test_log_file_created_alongside_json(repo_root, validation_script, report_dir):
    """
    Test that the validation script creates both JSON and log files
    in the report directory.
    """
    # Skip on Windows
    if os.name == "nt":
        pytest.skip("Bash script not compatible with Windows")

    # Run validation with custom report directory
    env = os.environ.copy()
    env["REPORT_DIR"] = str(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        ["bash", str(validation_script)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )

    # Check both files exist
    json_file = report_dir / "validate_rl_v0_1.json"
    log_file = report_dir / "validate_rl_v0_1.log"

    assert json_file.exists(), f"JSON report not found at {json_file}"
    assert log_file.exists(), f"Log file not found at {log_file}"

    # Verify log file has content
    log_content = log_file.read_text()
    assert len(log_content) > 0, "Log file is empty"
    assert "[INFO]" in log_content, "Log file should contain [INFO] entries"
