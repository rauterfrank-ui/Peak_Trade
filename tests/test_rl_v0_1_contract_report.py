"""
RL v0.1 Contract Test: Report Format Stability
===============================================
Tests that the RL v0.1 validation script produces consistent,
machine-readable reports across all execution scenarios.

This ensures CI artifact uploads and downstream tooling can
reliably parse validation results.
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


def test_json_report_schema_stability(repo_root, validation_script, tmp_path):
    """
    Test that JSON report follows stable schema v0.1:

    Always present:
    - status: "passed" | "skipped" | "failure"
    - ts: ISO 8601 timestamp (YYYY-MM-DDTHH:MM:SSZ)
    - log: relative path to log file

    Conditional fields:
    - reason: present when status != "passed"
    - smoke_rc: present when reason == "pytest_failed"
    - extra_rc: present when reason == "pytest_failed"
    """
    # Skip on Windows
    if os.name == "nt":
        pytest.skip("Bash script not compatible with Windows")

    report_dir = tmp_path / "reports" / "rl_v0_1"
    report_dir.mkdir(parents=True)

    env = os.environ.copy()
    env["REPORT_DIR"] = str(report_dir)

    result = subprocess.run(
        ["bash", str(validation_script)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )

    # Load JSON report
    json_file = report_dir / "validate_rl_v0_1.json"
    assert json_file.exists(), f"JSON report not created at {json_file}"

    with open(json_file) as f:
        report = json.load(f)

    # Schema validation: required fields
    required_fields = {"status", "ts", "log"}
    missing = required_fields - set(report.keys())
    assert not missing, f"Missing required fields: {missing}"

    # Schema validation: field types
    assert isinstance(report["status"], str), "status must be string"
    assert isinstance(report["ts"], str), "ts must be string"
    assert isinstance(report["log"], str), "log must be string"

    # Schema validation: status enum
    valid_statuses = {"passed", "skipped", "failure"}
    assert report["status"] in valid_statuses, (
        f"Invalid status '{report['status']}', expected one of {valid_statuses}"
    )

    # Schema validation: timestamp format (ISO 8601)
    ts = report["ts"]
    assert len(ts) == 20, f"Expected ISO 8601 format (20 chars), got {len(ts)}: {ts}"
    assert ts[10] == "T", f"Expected 'T' separator at position 10, got: {ts}"
    assert ts[19] == "Z", f"Expected 'Z' suffix at position 19, got: {ts}"

    # Schema validation: conditional fields
    if report["status"] in ("skipped", "failure"):
        assert "reason" in report, (
            f"status='{report['status']}' requires 'reason' field"
        )
        assert isinstance(report["reason"], str), "reason must be string"

    if report.get("reason") == "pytest_failed":
        assert "smoke_rc" in report, (
            "reason='pytest_failed' requires 'smoke_rc' field"
        )
        assert "extra_rc" in report, (
            "reason='pytest_failed' requires 'extra_rc' field"
        )
        assert isinstance(report["smoke_rc"], int), "smoke_rc must be integer"
        assert isinstance(report["extra_rc"], int), "extra_rc must be integer"


def test_report_artifacts_match_workflow_paths(repo_root, validation_script, tmp_path):
    """
    Test that report artifacts are created at paths matching CI workflow
    artifact upload configuration.

    Workflow expects:
    - reports/rl_v0_1/**/*
    """
    # Skip on Windows
    if os.name == "nt":
        pytest.skip("Bash script not compatible with Windows")

    # Use default report directory (reports/rl_v0_1)
    result = subprocess.run(
        ["bash", str(validation_script)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=60,
    )

    # Check default paths
    default_report_dir = repo_root / "reports" / "rl_v0_1"
    json_file = default_report_dir / "validate_rl_v0_1.json"
    log_file = default_report_dir / "validate_rl_v0_1.log"

    assert json_file.exists(), (
        f"JSON report not found at workflow artifact path: {json_file}"
    )
    assert log_file.exists(), (
        f"Log file not found at workflow artifact path: {log_file}"
    )

    # Verify JSON contains correct log path (relative)
    with open(json_file) as f:
        report = json.load(f)

    log_path = report.get("log")
    assert log_path == "reports/rl_v0_1/validate_rl_v0_1.log", (
        f"JSON log path should be 'reports/rl_v0_1/validate_rl_v0_1.log', "
        f"got: {log_path}"
    )


def test_json_is_parseable_by_jq(repo_root, validation_script, tmp_path):
    """
    Test that JSON report is valid and can be parsed by jq (if available).
    This ensures machine-readability for CI/CD tooling.
    """
    # Skip on Windows
    if os.name == "nt":
        pytest.skip("Bash script not compatible with Windows")

    report_dir = tmp_path / "reports" / "rl_v0_1"
    report_dir.mkdir(parents=True)

    env = os.environ.copy()
    env["REPORT_DIR"] = str(report_dir)

    result = subprocess.run(
        ["bash", str(validation_script)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )

    json_file = report_dir / "validate_rl_v0_1.json"

    # Basic JSON validation (Python can parse it)
    with open(json_file) as f:
        report = json.load(f)

    # If jq is available, test with it too
    jq_result = subprocess.run(
        ["which", "jq"],
        capture_output=True,
    )

    if jq_result.returncode == 0:
        # jq is available, use it to validate
        jq_parse = subprocess.run(
            ["jq", ".", str(json_file)],
            capture_output=True,
            text=True,
        )
        assert jq_parse.returncode == 0, (
            f"jq failed to parse JSON report:\n{jq_parse.stderr}"
        )
