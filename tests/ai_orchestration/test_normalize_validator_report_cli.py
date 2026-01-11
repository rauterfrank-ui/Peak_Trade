"""
CLI Tests for Validator Report Normalizer (Phase 4E)

Test Coverage:
- CLI argument parsing
- File input / stdin input
- Output generation
- Exit codes
- Runtime context handling

Reference:
- docs/governance/ai_autonomy/PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

import pytest


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def legacy_report_json() -> str:
    """Legacy validator report as JSON string."""
    return json.dumps({
        "validator": {
            "name": "l4_critic_determinism_contract_validator",
            "version": "1.0.0",
        },
        "contract_version": "1.0.0",
        "inputs": {
            "baseline": "tests/fixtures/baseline.json",
            "candidate": "tests/fixtures/candidate.json",
        },
        "result": {
            "equal": True,
            "baseline_hash": "abc123",
            "candidate_hash": "abc123",
            "diff_summary": "Reports are identical",
            "first_mismatch_path": None,
        },
    })


@pytest.fixture
def cli_script() -> Path:
    """Path to CLI script."""
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "scripts" / "aiops" / "normalize_validator_report.py"


# =============================================================================
# CLI Invocation Tests
# =============================================================================


def test_cli_help(cli_script):
    """Test CLI --help flag."""
    result = subprocess.run(
        [sys.executable, str(cli_script), "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Normalize validator reports" in result.stdout
    assert "--input" in result.stdout
    assert "--out-dir" in result.stdout


def test_cli_from_file(tmp_path, cli_script, legacy_report_json):
    """Test CLI with file input."""
    # Prepare input file
    input_file = tmp_path / "input_report.json"
    input_file.write_text(legacy_report_json, encoding="utf-8")

    # Prepare output dir
    out_dir = tmp_path / "output"

    # Run CLI
    result = subprocess.run(
        [
            sys.executable,
            str(cli_script),
            "--input", str(input_file),
            "--out-dir", str(out_dir),
        ],
        capture_output=True,
        text=True,
    )

    # Verify success
    assert result.returncode == 0
    assert "✅ Normalization complete" in result.stdout

    # Verify outputs
    json_path = out_dir / "validator_report.normalized.json"
    md_path = out_dir / "validator_report.normalized.md"

    assert json_path.exists()
    assert md_path.exists()

    # Verify JSON content
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0.0"
    assert data["tool"]["name"] == "l4_critic_determinism_contract_validator"


def test_cli_from_stdin(tmp_path, cli_script, legacy_report_json):
    """Test CLI with stdin input."""
    out_dir = tmp_path / "output"

    # Run CLI with stdin
    result = subprocess.run(
        [
            sys.executable,
            str(cli_script),
            "--out-dir", str(out_dir),
        ],
        input=legacy_report_json,
        capture_output=True,
        text=True,
    )

    # Verify success
    assert result.returncode == 0

    # Verify outputs
    json_path = out_dir / "validator_report.normalized.json"
    assert json_path.exists()


def test_cli_with_runtime_context(tmp_path, cli_script, legacy_report_json):
    """Test CLI with runtime context args."""
    input_file = tmp_path / "input_report.json"
    input_file.write_text(legacy_report_json, encoding="utf-8")

    out_dir = tmp_path / "output"

    # Run CLI with runtime context
    result = subprocess.run(
        [
            sys.executable,
            str(cli_script),
            "--input", str(input_file),
            "--out-dir", str(out_dir),
            "--git-sha", "abc123def456",
            "--run-id", "123456",
            "--workflow", "Test Workflow",
            "--job", "test_job",
            "--timestamp",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    # Verify runtime context NOT in canonical JSON (deterministic mode)
    json_path = out_dir / "validator_report.normalized.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "runtime_context" not in data


def test_cli_no_markdown_flag(tmp_path, cli_script, legacy_report_json):
    """Test CLI --no-markdown flag."""
    input_file = tmp_path / "input_report.json"
    input_file.write_text(legacy_report_json, encoding="utf-8")

    out_dir = tmp_path / "output"

    # Run CLI with --no-markdown
    result = subprocess.run(
        [
            sys.executable,
            str(cli_script),
            "--input", str(input_file),
            "--out-dir", str(out_dir),
            "--no-markdown",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    # Verify JSON exists but Markdown doesn't
    json_path = out_dir / "validator_report.normalized.json"
    md_path = out_dir / "validator_report.normalized.md"

    assert json_path.exists()
    assert not md_path.exists()


def test_cli_quiet_flag(tmp_path, cli_script, legacy_report_json):
    """Test CLI --quiet flag."""
    input_file = tmp_path / "input_report.json"
    input_file.write_text(legacy_report_json, encoding="utf-8")

    out_dir = tmp_path / "output"

    # Run CLI with --quiet
    result = subprocess.run(
        [
            sys.executable,
            str(cli_script),
            "--input", str(input_file),
            "--out-dir", str(out_dir),
            "--quiet",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    # Verify no output (quiet mode)
    assert result.stdout.strip() == ""


# =============================================================================
# Error Handling Tests
# =============================================================================


def test_cli_missing_input_file(tmp_path, cli_script):
    """Test CLI with missing input file."""
    out_dir = tmp_path / "output"

    result = subprocess.run(
        [
            sys.executable,
            str(cli_script),
            "--input", str(tmp_path / "nonexistent.json"),
            "--out-dir", str(out_dir),
        ],
        capture_output=True,
        text=True,
    )

    # Should fail
    assert result.returncode == 1
    assert "ERROR" in result.stderr
    assert "not found" in result.stderr


def test_cli_invalid_json(tmp_path, cli_script):
    """Test CLI with invalid JSON input."""
    input_file = tmp_path / "invalid.json"
    input_file.write_text("not valid json", encoding="utf-8")

    out_dir = tmp_path / "output"

    result = subprocess.run(
        [
            sys.executable,
            str(cli_script),
            "--input", str(input_file),
            "--out-dir", str(out_dir),
        ],
        capture_output=True,
        text=True,
    )

    # Should fail
    assert result.returncode == 1
    assert "ERROR" in result.stderr
    assert "Invalid JSON" in result.stderr


# =============================================================================
# Determinism Tests
# =============================================================================


def test_cli_determinism(tmp_path, cli_script, legacy_report_json):
    """Test that CLI produces deterministic outputs."""
    input_file = tmp_path / "input_report.json"
    input_file.write_text(legacy_report_json, encoding="utf-8")

    # Run twice
    out_dir1 = tmp_path / "run1"
    out_dir2 = tmp_path / "run2"

    for out_dir in [out_dir1, out_dir2]:
        result = subprocess.run(
            [
                sys.executable,
                str(cli_script),
                "--input", str(input_file),
                "--out-dir", str(out_dir),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    # Compare outputs (byte-identical)
    json1 = (out_dir1 / "validator_report.normalized.json").read_bytes()
    json2 = (out_dir2 / "validator_report.normalized.json").read_bytes()

    assert json1 == json2


# =============================================================================
# Integration Tests
# =============================================================================


def test_cli_full_pipeline(tmp_path, cli_script, legacy_report_json):
    """Test full CLI pipeline (input -> normalize -> output)."""
    input_file = tmp_path / "input_report.json"
    input_file.write_text(legacy_report_json, encoding="utf-8")

    out_dir = tmp_path / "output"

    # Run normalization
    result = subprocess.run(
        [
            sys.executable,
            str(cli_script),
            "--input", str(input_file),
            "--out-dir", str(out_dir),
            "--git-sha", "test-sha",
            "--run-id", "test-run-123",
        ],
        capture_output=True,
        text=True,
    )

    # Verify success
    assert result.returncode == 0

    # Verify outputs exist
    json_path = out_dir / "validator_report.normalized.json"
    md_path = out_dir / "validator_report.normalized.md"

    assert json_path.exists()
    assert md_path.exists()

    # Verify JSON structure
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "schema_version" in data
    assert "tool" in data
    assert "subject" in data
    assert "result" in data
    assert "checks" in data
    assert "summary" in data

    # Verify Markdown structure
    md_content = md_path.read_text(encoding="utf-8")
    assert "# Validator Report Summary" in md_content
    assert "## Summary" in md_content
    assert "## Checks" in md_content
