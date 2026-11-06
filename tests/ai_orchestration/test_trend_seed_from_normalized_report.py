"""
Tests for Trend Seed Consumer (Phase 5A)

Test Coverage:
- Determinism: byte-identical JSON output on repeated generation
- Fail-closed: missing schema_version, unsupported schema_version, missing required fields
- Schema validation: only accept schema_version starting with "1."
- Conclusion normalization: PASS/FAIL/ERROR -> pass/fail/error
- Counts extraction: checks_total, checks_passed, checks_failed
- Determinism info extraction: hash, is_deterministic
- Markdown summary rendering

Reference:
    docs/ops/runbooks/RUNBOOK_PHASE5A_NORMALIZED_REPORT_CONSUMER_TREND_SEED_CURSOR_MULTI_AGENT.md
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.ai_orchestration.trends.trend_seed_consumer import (
    SchemaVersionError,
    TrendSeedError,
    ValidationError,
    generate_trend_seed,
    load_normalized_report,
    render_markdown_summary,
    write_deterministic_json,
)


@pytest.fixture
def sample_normalized_report() -> dict:
    """Load sample normalized report fixture."""
    fixture_path = Path("tests/fixtures/validator_report.normalized.sample.json")
    with open(fixture_path, "r") as f:
        return json.load(f)


@pytest.fixture
def sample_meta() -> dict:
    """Sample workflow run metadata."""
    return {
        "repo": "owner/repo",
        "workflow_name": "L4 Critic Replay Determinism",
        "run_id": "12345",
        "run_attempt": 1,
        "head_sha": "abc123",
        "ref": "refs/heads/main",
        "run_created_at": "2026-01-11T12:00:00Z",
        "consumer_name": "trend_seed_consumer",
        "consumer_version": "0.1.0",
        "consumer_commit_sha": "def456",
    }


def test_load_normalized_report(sample_normalized_report):
    """Test loading normalized report from JSON file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_normalized_report, f)
        temp_path = f.name

    try:
        report = load_normalized_report(temp_path)
        assert report["schema_version"] == "1.0.0"
        assert report["result"] == "PASS"
    finally:
        Path(temp_path).unlink()


def test_load_normalized_report_missing_file():
    """Test loading missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_normalized_report("/nonexistent/file.json")


def test_generate_trend_seed_success(sample_normalized_report, sample_meta):
    """Test successful Trend Seed generation."""
    seed = generate_trend_seed(sample_normalized_report, meta=sample_meta)

    # Validate schema
    assert seed["schema_version"] == "0.1.0"
    assert seed["generated_at"] == "2026-01-11T12:00:00Z"

    # Validate source
    assert seed["source"]["repo"] == "owner/repo"
    assert seed["source"]["workflow_name"] == "L4 Critic Replay Determinism"
    assert seed["source"]["run_id"] == "12345"
    assert seed["source"]["head_sha"] == "abc123"

    # Validate normalized_report section
    assert seed["normalized_report"]["schema_version"] == "1.0.0"
    assert seed["normalized_report"]["conclusion"] == "pass"
    assert seed["normalized_report"]["counts"]["checks_total"] == 2
    assert seed["normalized_report"]["counts"]["checks_passed"] == 2
    assert seed["normalized_report"]["counts"]["checks_failed"] == 0
    assert seed["normalized_report"]["determinism"]["hash"] == "abc123def456789"
    assert seed["normalized_report"]["determinism"]["is_deterministic"] is True

    # Validate consumer
    assert seed["consumer"]["name"] == "trend_seed_consumer"
    assert seed["consumer"]["version"] == "0.1.0"
    assert seed["consumer"]["commit_sha"] == "def456"


def test_generate_trend_seed_determinism(sample_normalized_report, sample_meta):
    """Test deterministic output: two runs with same inputs produce byte-identical JSON."""
    seed1 = generate_trend_seed(sample_normalized_report, meta=sample_meta)
    seed2 = generate_trend_seed(sample_normalized_report, meta=sample_meta)

    # Serialize to JSON with deterministic formatting
    json1 = json.dumps(seed1, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    json2 = json.dumps(seed2, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    assert json1 == json2, "Trend Seed outputs are not deterministic"


def test_generate_trend_seed_missing_schema_version(sample_meta):
    """Test fail-closed: missing schema_version raises ValidationError."""
    report = {"result": "PASS", "summary": {"total": 1, "passed": 1, "failed": 0}}

    with pytest.raises(ValidationError, match="Missing required field: schema_version"):
        generate_trend_seed(report, meta=sample_meta)


def test_generate_trend_seed_unsupported_schema_version(sample_meta):
    """Test fail-closed: unsupported schema_version raises SchemaVersionError."""
    report = {
        "schema_version": "2.0.0",  # Unsupported
        "result": "PASS",
        "summary": {"total": 1, "passed": 1, "failed": 0},
    }

    with pytest.raises(SchemaVersionError, match="Unsupported normalized report schema version"):
        generate_trend_seed(report, meta=sample_meta)


def test_generate_trend_seed_missing_result(sample_meta):
    """Test fail-closed: missing result field raises ValidationError."""
    report = {"schema_version": "1.0.0", "summary": {"total": 1, "passed": 1, "failed": 0}}

    with pytest.raises(ValidationError, match="Missing required field: result"):
        generate_trend_seed(report, meta=sample_meta)


def test_generate_trend_seed_missing_summary(sample_meta):
    """Test fail-closed: missing summary field raises ValidationError."""
    report = {"schema_version": "1.0.0", "result": "PASS"}

    with pytest.raises(ValidationError, match="Missing required field: summary"):
        generate_trend_seed(report, meta=sample_meta)


def test_generate_trend_seed_missing_summary_counts(sample_meta):
    """Test fail-closed: missing summary counts raise ValidationError."""
    report = {"schema_version": "1.0.0", "result": "PASS", "summary": {}}

    with pytest.raises(ValidationError, match="Missing required field: summary.total"):
        generate_trend_seed(report, meta=sample_meta)


def test_generate_trend_seed_missing_meta_keys(sample_normalized_report):
    """Test fail-closed: missing meta keys raise ValidationError."""
    incomplete_meta = {"repo": "owner/repo"}

    with pytest.raises(ValidationError, match="Missing required meta key"):
        generate_trend_seed(sample_normalized_report, meta=incomplete_meta)


def test_conclusion_normalization(sample_meta):
    """Test conclusion normalization: PASS/FAIL/ERROR -> pass/fail/error."""
    # Test PASS
    report_pass = {
        "schema_version": "1.0.0",
        "result": "PASS",
        "summary": {"total": 1, "passed": 1, "failed": 0},
    }
    seed_pass = generate_trend_seed(report_pass, meta=sample_meta)
    assert seed_pass["normalized_report"]["conclusion"] == "pass"

    # Test FAIL
    report_fail = {
        "schema_version": "1.0.0",
        "result": "FAIL",
        "summary": {"total": 1, "passed": 0, "failed": 1},
    }
    seed_fail = generate_trend_seed(report_fail, meta=sample_meta)
    assert seed_fail["normalized_report"]["conclusion"] == "fail"

    # Test ERROR
    report_error = {
        "schema_version": "1.0.0",
        "result": "ERROR",
        "summary": {"total": 1, "passed": 0, "failed": 1},
    }
    seed_error = generate_trend_seed(report_error, meta=sample_meta)
    assert seed_error["normalized_report"]["conclusion"] == "error"


def test_write_deterministic_json():
    """Test deterministic JSON writing."""
    payload = {"z": 3, "a": 1, "m": 2}  # Unsorted keys

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "test.json"
        write_deterministic_json(str(out_path), payload)

        # Read back and verify
        with open(out_path, "r") as f:
            content = f.read()

        # Keys should be sorted
        assert content.startswith('{\n  "a":1,\n  "m":2,\n  "z":3\n}\n')

        # Should be valid JSON
        parsed = json.loads(content)
        assert parsed == payload


def test_render_markdown_summary(sample_normalized_report, sample_meta):
    """Test Markdown summary rendering."""
    seed = generate_trend_seed(sample_normalized_report, meta=sample_meta)
    summary = render_markdown_summary(seed)

    # Check key sections are present
    assert "# Trend Seed Summary" in summary
    assert "## Source" in summary
    assert "## Normalized Report" in summary
    assert "### Counts" in summary
    assert "### Determinism" in summary
    assert "## Consumer" in summary

    # Check key values are present
    assert "owner/repo" in summary
    assert "L4 Critic Replay Determinism" in summary
    assert "12345" in summary
    assert "abc123" in summary
    assert "PASS" in summary
    assert "Total Checks:** 2" in summary


def test_determinism_info_extraction_no_checks(sample_meta):
    """Test determinism info extraction when checks are missing."""
    report = {
        "schema_version": "1.0.0",
        "result": "PASS",
        "summary": {"total": 1, "passed": 1, "failed": 0},
        "determinism_hash": "test_hash",
    }

    seed = generate_trend_seed(report, meta=sample_meta)
    assert seed["normalized_report"]["determinism"]["hash"] == "test_hash"
    assert seed["normalized_report"]["determinism"]["is_deterministic"] is None


def test_policy_findings_extraction(sample_meta):
    """Test policy findings count extraction."""
    report = {
        "schema_version": "1.0.0",
        "result": "PASS",
        "summary": {"total": 1, "passed": 1, "failed": 0},
        "evidence": {
            "policy_findings": [
                {"severity": "low", "message": "test finding 1"},
                {"severity": "medium", "message": "test finding 2"},
            ]
        },
    }

    seed = generate_trend_seed(report, meta=sample_meta)
    assert seed["normalized_report"]["counts"]["policy_findings_total"] == 2


def test_policy_findings_missing(sample_meta):
    """Test policy findings count when missing (should be None)."""
    report = {
        "schema_version": "1.0.0",
        "result": "PASS",
        "summary": {"total": 1, "passed": 1, "failed": 0},
    }

    seed = generate_trend_seed(report, meta=sample_meta)
    assert seed["normalized_report"]["counts"]["policy_findings_total"] is None


def test_notes_truncation(sample_normalized_report, sample_meta):
    """Test notes are truncated to 280 characters."""
    long_notes = "x" * 500
    meta_with_notes = {**sample_meta, "notes": long_notes}

    seed = generate_trend_seed(sample_normalized_report, meta=meta_with_notes)
    assert len(seed["notes"]) == 280
    assert seed["notes"] == "x" * 280
