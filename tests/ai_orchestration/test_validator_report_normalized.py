"""
Tests for Validator Report Normalization (Phase 4E)

Test Coverage:
- Schema validation
- Legacy report conversion
- Deterministic serialization
- Hash stability
- CLI integration

Reference:
- docs/governance/ai_autonomy/PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, Any

import pytest

from src.ai_orchestration.validator_report_normalized import (
    normalize_validator_report,
    hash_normalized_report,
    validate_determinism,
)
from src.ai_orchestration.validator_report_schema import (
    ValidatorReport,
    ToolInfo,
    ValidationCheck,
    ValidationResult,
    CheckStatus,
    SummaryMetrics,
    Evidence,
    RuntimeContext,
    VALIDATOR_REPORT_SCHEMA_VERSION,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def legacy_validator_report_pass() -> Dict[str, Any]:
    """Legacy Phase 4D validator report (PASS case)."""
    return {
        "validator": {
            "name": "l4_critic_determinism_contract_validator",
            "version": "1.0.0",
        },
        "contract_version": "1.0.0",
        "inputs": {
            "baseline": "tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0/critic_report.json",
            "candidate": ".tmp/l4_critic_out/critic_report.json",
        },
        "result": {
            "equal": True,
            "baseline_hash": "abc123def456",
            "candidate_hash": "abc123def456",
            "diff_summary": "Reports are identical (0 diffs)",
            "first_mismatch_path": None,
        },
    }


@pytest.fixture
def legacy_validator_report_fail() -> Dict[str, Any]:
    """Legacy Phase 4D validator report (FAIL case)."""
    return {
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
            "equal": False,
            "baseline_hash": "abc123",
            "candidate_hash": "def456",
            "diff_summary": "Reports differ (12 diffs)",
            "first_mismatch_path": "$.findings[0].severity",
        },
    }


@pytest.fixture
def runtime_context_ci() -> Dict[str, Any]:
    """CI runtime context."""
    return {
        "git_sha": "abc123def456",
        "run_id": "123456789",
        "workflow": "L4 Critic Replay Determinism",
        "job": "validate_determinism_contract",
        "generated_at_utc": "2026-01-11T12:00:00Z",
    }


# =============================================================================
# Schema Validation Tests
# =============================================================================


def test_validator_report_schema_valid():
    """Test ValidatorReport schema with valid data."""
    report = ValidatorReport(
        schema_version=VALIDATOR_REPORT_SCHEMA_VERSION,
        tool=ToolInfo(name="test_validator", version="1.0.0"),
        subject="test_subject",
        result=ValidationResult.PASS,
        checks=[
            ValidationCheck(
                id="check_1",
                status=CheckStatus.PASS,
                message="Check passed",
                metrics={"count": 42},
            ),
        ],
        summary=SummaryMetrics(passed=1, failed=0, total=1),
        evidence=Evidence(baseline="a.json", candidate="b.json"),
    )

    assert report.schema_version == VALIDATOR_REPORT_SCHEMA_VERSION
    assert report.tool.name == "test_validator"
    assert report.result == ValidationResult.PASS
    assert len(report.checks) == 1
    assert report.summary.passed == 1


def test_validator_report_schema_forbids_extra_fields():
    """Test that schema forbids extra fields (strict validation)."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        ValidatorReport(
            schema_version=VALIDATOR_REPORT_SCHEMA_VERSION,
            tool=ToolInfo(name="test_validator", version="1.0.0"),
            subject="test_subject",
            result=ValidationResult.PASS,
            checks=[],
            summary=SummaryMetrics(passed=0, failed=0, total=0),
            extra_field="should_fail",  # type: ignore
        )


# =============================================================================
# Legacy Report Conversion Tests
# =============================================================================


def test_normalize_legacy_report_pass(legacy_validator_report_pass):
    """Test normalization of legacy report (PASS case)."""
    normalized = normalize_validator_report(legacy_validator_report_pass)

    assert normalized.schema_version == VALIDATOR_REPORT_SCHEMA_VERSION
    assert normalized.tool.name == "l4_critic_determinism_contract_validator"
    assert normalized.tool.version == "1.0.0"
    assert normalized.subject == "l4_critic_determinism_contract_v1.0.0"
    assert normalized.result == ValidationResult.PASS
    assert normalized.summary.passed == 1
    assert normalized.summary.failed == 0
    assert normalized.summary.total == 1

    # Check checks array
    assert len(normalized.checks) == 1
    check = normalized.checks[0]
    assert check.id == "determinism_contract_validation"
    assert check.status == CheckStatus.PASS
    assert "identical" in check.message.lower()
    assert check.metrics["baseline_hash"] == "abc123def456"
    assert check.metrics["candidate_hash"] == "abc123def456"


def test_normalize_legacy_report_fail(legacy_validator_report_fail):
    """Test normalization of legacy report (FAIL case)."""
    normalized = normalize_validator_report(legacy_validator_report_fail)

    assert normalized.result == ValidationResult.FAIL
    assert normalized.summary.passed == 0
    assert normalized.summary.failed == 1
    assert normalized.summary.total == 1

    # Check checks array
    check = normalized.checks[0]
    assert check.status == CheckStatus.FAIL
    assert "differ" in check.message.lower()
    assert check.metrics["baseline_hash"] == "abc123"
    assert check.metrics["candidate_hash"] == "def456"
    assert check.metrics["first_mismatch_path"] == "$.findings[0].severity"


def test_normalize_with_runtime_context(legacy_validator_report_pass, runtime_context_ci):
    """Test normalization with runtime context."""
    normalized = normalize_validator_report(
        legacy_validator_report_pass,
        runtime_context=runtime_context_ci,
    )

    assert normalized.runtime_context is not None
    assert normalized.runtime_context.git_sha == "abc123def456"
    assert normalized.runtime_context.run_id == "123456789"
    assert normalized.runtime_context.workflow == "L4 Critic Replay Determinism"
    assert normalized.runtime_context.job == "validate_determinism_contract"


# =============================================================================
# Deterministic Serialization Tests
# =============================================================================


def test_to_canonical_dict_excludes_runtime_context(legacy_validator_report_pass, runtime_context_ci):
    """Test that canonical dict excludes runtime_context."""
    normalized = normalize_validator_report(
        legacy_validator_report_pass,
        runtime_context=runtime_context_ci,
    )

    canonical = normalized.to_canonical_dict()

    assert "runtime_context" not in canonical
    assert "schema_version" in canonical
    assert "checks" in canonical


def test_to_canonical_dict_sorts_checks(legacy_validator_report_pass):
    """Test that canonical dict sorts checks by id."""
    # Create report with multiple checks
    normalized = normalize_validator_report(legacy_validator_report_pass)

    # Add more checks (out of order)
    normalized.checks.append(
        ValidationCheck(
            id="zzz_last_check",
            status=CheckStatus.PASS,
            message="Last",
        )
    )
    normalized.checks.insert(
        0,
        ValidationCheck(
            id="aaa_first_check",
            status=CheckStatus.PASS,
            message="First",
        ),
    )

    canonical = normalized.to_canonical_dict()
    check_ids = [c["id"] for c in canonical["checks"]]

    # Should be sorted alphabetically
    assert check_ids == sorted(check_ids)
    assert check_ids[0] == "aaa_first_check"
    assert check_ids[-1] == "zzz_last_check"


def test_deterministic_json_serialization(tmp_path, legacy_validator_report_pass):
    """Test that JSON serialization is deterministic (byte-identical)."""
    normalized = normalize_validator_report(legacy_validator_report_pass)

    # Write twice
    path1 = tmp_path / "report1.json"
    path2 = tmp_path / "report2.json"

    normalized.write_json(path1, deterministic=True)
    normalized.write_json(path2, deterministic=True)

    # Compare byte-for-byte
    content1 = path1.read_bytes()
    content2 = path2.read_bytes()

    assert content1 == content2


def test_hash_stability(legacy_validator_report_pass):
    """Test that hash is stable across multiple normalizations."""
    normalized1 = normalize_validator_report(legacy_validator_report_pass)
    normalized2 = normalize_validator_report(legacy_validator_report_pass)

    hash1 = hash_normalized_report(normalized1)
    hash2 = hash_normalized_report(normalized2)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex digest


def test_hash_ignores_runtime_context(legacy_validator_report_pass):
    """Test that hash ignores runtime_context (volatile)."""
    # Normalize with different runtime contexts
    normalized1 = normalize_validator_report(
        legacy_validator_report_pass,
        runtime_context={"git_sha": "abc123", "run_id": "123"},
    )
    normalized2 = normalize_validator_report(
        legacy_validator_report_pass,
        runtime_context={"git_sha": "def456", "run_id": "456"},
    )

    hash1 = hash_normalized_report(normalized1)
    hash2 = hash_normalized_report(normalized2)

    # Hashes should be identical (runtime context excluded)
    assert hash1 == hash2


def test_validate_determinism_pass(legacy_validator_report_pass):
    """Test determinism validation (PASS case)."""
    normalized1 = normalize_validator_report(legacy_validator_report_pass)
    normalized2 = normalize_validator_report(legacy_validator_report_pass)

    assert validate_determinism(normalized1, normalized2) is True


def test_validate_determinism_fail(legacy_validator_report_pass, legacy_validator_report_fail):
    """Test determinism validation (FAIL case)."""
    normalized1 = normalize_validator_report(legacy_validator_report_pass)
    normalized2 = normalize_validator_report(legacy_validator_report_fail)

    assert validate_determinism(normalized1, normalized2) is False


# =============================================================================
# I/O Tests
# =============================================================================


def test_write_json_deterministic(tmp_path, legacy_validator_report_pass):
    """Test JSON writing in deterministic mode."""
    normalized = normalize_validator_report(
        legacy_validator_report_pass,
        runtime_context={"git_sha": "abc123"},
    )

    json_path = tmp_path / "report.json"
    normalized.write_json(json_path, deterministic=True)

    assert json_path.exists()

    # Load and verify
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "runtime_context" not in data  # Excluded in deterministic mode
    assert data["schema_version"] == VALIDATOR_REPORT_SCHEMA_VERSION


def test_write_json_non_deterministic(tmp_path, legacy_validator_report_pass):
    """Test JSON writing in non-deterministic mode."""
    normalized = normalize_validator_report(
        legacy_validator_report_pass,
        runtime_context={"git_sha": "abc123"},
    )

    json_path = tmp_path / "report.json"
    normalized.write_json(json_path, deterministic=False)

    assert json_path.exists()

    # Load and verify
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "runtime_context" in data  # Included in non-deterministic mode
    assert data["runtime_context"]["git_sha"] == "abc123"


def test_write_summary_md(tmp_path, legacy_validator_report_pass):
    """Test Markdown summary writing."""
    normalized = normalize_validator_report(legacy_validator_report_pass)

    md_path = tmp_path / "report.md"
    normalized.write_summary_md(md_path)

    assert md_path.exists()

    # Verify content
    content = md_path.read_text(encoding="utf-8")
    assert "# Validator Report Summary" in content
    assert normalized.tool.name in content
    assert normalized.subject in content
    assert "✅" in content  # PASS emoji


def test_write_summary_md_fail_case(tmp_path, legacy_validator_report_fail):
    """Test Markdown summary writing (FAIL case)."""
    normalized = normalize_validator_report(legacy_validator_report_fail)

    md_path = tmp_path / "report.md"
    normalized.write_summary_md(md_path)

    content = md_path.read_text(encoding="utf-8")
    assert "❌" in content  # FAIL emoji
    assert "differ" in content.lower()


# =============================================================================
# Edge Cases & Error Handling
# =============================================================================


def test_empty_checks_array():
    """Test report with empty checks array."""
    report = ValidatorReport(
        schema_version=VALIDATOR_REPORT_SCHEMA_VERSION,
        tool=ToolInfo(name="test_validator", version="1.0.0"),
        subject="test_subject",
        result=ValidationResult.PASS,
        checks=[],
        summary=SummaryMetrics(passed=0, failed=0, total=0),
    )

    canonical = report.to_canonical_dict()
    assert "checks" in canonical
    assert canonical["checks"] == []


def test_evidence_optional_fields():
    """Test Evidence model with optional fields."""
    # All fields
    evidence1 = Evidence(baseline="a.json", candidate="b.json", diff="c.diff")
    assert evidence1.baseline == "a.json"
    assert evidence1.candidate == "b.json"
    assert evidence1.diff == "c.diff"

    # Minimal (all optional)
    evidence2 = Evidence()
    assert evidence2.baseline is None
    assert evidence2.candidate is None
    assert evidence2.diff is None


def test_runtime_context_allows_extra_fields():
    """Test that RuntimeContext allows extra fields (extensible)."""
    context = RuntimeContext(
        git_sha="abc123",
        extra_field="allowed",  # Should not raise
    )
    assert context.git_sha == "abc123"


# =============================================================================
# Integration Tests
# =============================================================================


def test_full_normalization_pipeline(tmp_path, legacy_validator_report_pass):
    """Test full normalization pipeline (legacy -> normalized -> JSON + MD)."""
    # 1. Normalize
    normalized = normalize_validator_report(
        legacy_validator_report_pass,
        runtime_context={"git_sha": "abc123"},
    )

    # 2. Write JSON
    json_path = tmp_path / "validator_report.normalized.json"
    normalized.write_json(json_path, deterministic=True)

    # 3. Write Markdown
    md_path = tmp_path / "validator_report.normalized.md"
    normalized.write_summary_md(md_path)

    # 4. Verify outputs
    assert json_path.exists()
    assert md_path.exists()

    # 5. Verify JSON is valid and canonical
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == VALIDATOR_REPORT_SCHEMA_VERSION
    assert "runtime_context" not in data

    # 6. Verify Markdown is human-readable
    md_content = md_path.read_text(encoding="utf-8")
    assert "# Validator Report Summary" in md_content
    assert "PASS" in md_content


def test_determinism_golden_fixture(tmp_path, legacy_validator_report_pass):
    """Test determinism with golden fixture approach."""
    # Generate normalized report twice
    normalized1 = normalize_validator_report(legacy_validator_report_pass)
    normalized2 = normalize_validator_report(legacy_validator_report_pass)

    # Write to separate files
    path1 = tmp_path / "run1.json"
    path2 = tmp_path / "run2.json"

    normalized1.write_json(path1, deterministic=True)
    normalized2.write_json(path2, deterministic=True)

    # Byte-identical check
    assert path1.read_bytes() == path2.read_bytes()

    # Hash check
    assert hash_normalized_report(normalized1) == hash_normalized_report(normalized2)
