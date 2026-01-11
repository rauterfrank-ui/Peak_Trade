"""
Unit tests for L4 Critic Determinism Contract (Phase 4D)

Tests:
- Canonicalization removes volatile keys
- Hash is stable across key order
- Compare reports finds first mismatch path deterministically
- Numeric tolerance (if implemented)

Reference:
    docs/governance/ai_autonomy/PHASE4D_L4_CRITIC_DETERMINISM_CONTRACT.md
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ai_orchestration.l4_critic_determinism_contract import (
    ComparisonResult,
    DeterminismContract,
    canonicalize,
    compare_reports,
    dumps_canonical_json,
    hash_canonical,
    load_json,
    write_json,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def contract_v1() -> DeterminismContract:
    """Default v1.0.0 contract."""
    return DeterminismContract.default_v1_0_0()


@pytest.fixture
def sample_report() -> dict:
    """Minimal L4 Critic report for testing."""
    return {
        "schema_version": "1.0.0",
        "pack_id": "test_pack",
        "mode": "replay",
        "critic": {"name": "L4_Governance_Critic", "version": "1.0.0"},
        "inputs": {"evidence_pack_path": "tests/fixtures/test", "fixture": "test"},
        "summary": {
            "verdict": "PASS",
            "risk_level": "LOW",
            "score": None,
            "finding_counts": {"high": 0, "med": 0, "low": 1, "info": 0},
        },
        "findings": [
            {
                "id": "F001",
                "title": "Test Finding",
                "severity": "LOW",
                "status": "OPEN",
                "rationale": "Test rationale",
                "evidence_refs": [],
                "metrics": {},
            }
        ],
        "meta": {
            "deterministic": True,
            "created_at": None,
            "canonicalization": {"rules": ["sorted_keys"]},
        },
    }


# =============================================================================
# Canonicalization Tests
# =============================================================================


def test_canonicalization_removes_volatile_keys(contract_v1: DeterminismContract):
    """Test that volatile keys are removed during canonicalization."""
    report_with_volatile = {
        "schema_version": "1.0.0",
        "pack_id": "test",
        "timestamp": "2026-01-11T12:00:00Z",  # volatile
        "created_at": "2026-01-11T12:00:00Z",  # volatile
        "duration": 1.23,  # volatile
        "stable_field": "keep_me",
    }

    canonical = canonicalize(report_with_volatile, contract=contract_v1)

    # Volatile keys should be removed
    assert "timestamp" not in canonical
    assert "created_at" not in canonical
    assert "duration" not in canonical

    # Stable keys should remain
    assert "schema_version" in canonical
    assert "pack_id" in canonical
    assert "stable_field" in canonical
    assert canonical["stable_field"] == "keep_me"


def test_canonicalization_preserves_nested_structure(contract_v1: DeterminismContract):
    """Test that canonicalization preserves nested dict/list structure."""
    report = {
        "top": {
            "nested": {
                "timestamp": "2026-01-11T12:00:00Z",  # volatile, should be removed
                "stable": "value",
            }
        },
        "list_field": [
            {"id": "1", "created_at": "2026-01-11T12:00:00Z"},  # volatile
            {"id": "2", "stable": "data"},
        ],
    }

    canonical = canonicalize(report, contract=contract_v1)

    # Nested volatile key removed
    assert "timestamp" not in canonical["top"]["nested"]
    assert canonical["top"]["nested"]["stable"] == "value"

    # List preserved, volatile keys removed from list items
    assert len(canonical["list_field"]) == 2
    assert "created_at" not in canonical["list_field"][0]
    assert canonical["list_field"][0]["id"] == "1"
    assert canonical["list_field"][1]["stable"] == "data"


def test_canonicalization_normalizes_paths(contract_v1: DeterminismContract):
    """Test that file paths are normalized (backslash -> slash)."""
    report = {
        "inputs": {
            "evidence_pack_path": "C:\\Users\\test\\Peak_Trade\\tests\\fixtures",
            "relative_path": "tests/fixtures/test",
        }
    }

    canonical = canonicalize(report, contract=contract_v1)

    # Backslashes converted to forward slashes
    assert "\\" not in canonical["inputs"]["evidence_pack_path"]
    assert "/" in canonical["inputs"]["evidence_pack_path"]

    # Relative paths unchanged
    assert canonical["inputs"]["relative_path"] == "tests/fixtures/test"


# =============================================================================
# Hashing Tests
# =============================================================================


def test_hash_is_stable_across_key_order(
    contract_v1: DeterminismContract, sample_report: dict
):
    """Test that hash is stable regardless of dict key order."""
    # Create two reports with same data but different key order
    report1 = sample_report.copy()
    report2 = {
        "meta": report1["meta"],
        "findings": report1["findings"],
        "summary": report1["summary"],
        "inputs": report1["inputs"],
        "critic": report1["critic"],
        "mode": report1["mode"],
        "pack_id": report1["pack_id"],
        "schema_version": report1["schema_version"],
    }

    hash1 = hash_canonical(report1, contract_v1)
    hash2 = hash_canonical(report2, contract_v1)

    # Hashes should be identical (canonicalization sorts keys)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex length


def test_hash_changes_on_data_change(
    contract_v1: DeterminismContract, sample_report: dict
):
    """Test that hash changes when data changes."""
    report1 = sample_report.copy()
    report2 = sample_report.copy()
    report2["pack_id"] = "different_pack"

    hash1 = hash_canonical(report1, contract_v1)
    hash2 = hash_canonical(report2, contract_v1)

    # Hashes should differ
    assert hash1 != hash2


def test_hash_ignores_volatile_fields(contract_v1: DeterminismContract):
    """Test that hash is stable when only volatile fields differ."""
    report1 = {
        "schema_version": "1.0.0",
        "pack_id": "test",
        "timestamp": "2026-01-11T12:00:00Z",  # volatile
        "stable": "data",
    }
    report2 = {
        "schema_version": "1.0.0",
        "pack_id": "test",
        "timestamp": "2026-01-11T13:00:00Z",  # different timestamp
        "stable": "data",
    }

    hash1 = hash_canonical(report1, contract_v1)
    hash2 = hash_canonical(report2, contract_v1)

    # Hashes should be identical (volatile fields ignored)
    assert hash1 == hash2


# =============================================================================
# Comparison Tests
# =============================================================================


def test_compare_reports_equal(
    contract_v1: DeterminismContract, sample_report: dict
):
    """Test that identical reports are considered equal."""
    baseline = sample_report.copy()
    candidate = sample_report.copy()

    result = compare_reports(baseline, candidate, contract_v1)

    assert result.equal is True
    assert result.baseline_hash == result.candidate_hash
    assert result.first_mismatch_path is None
    assert "identical" in result.diff_summary.lower()


def test_compare_reports_finds_first_mismatch_path(
    contract_v1: DeterminismContract, sample_report: dict
):
    """Test that first mismatch path is identified deterministically."""
    baseline = sample_report.copy()
    candidate = sample_report.copy()
    candidate["pack_id"] = "different_pack"

    result = compare_reports(baseline, candidate, contract_v1)

    assert result.equal is False
    assert result.baseline_hash != result.candidate_hash
    assert result.first_mismatch_path == "$.pack_id"
    assert "pack_id" in result.diff_summary


def test_compare_reports_nested_mismatch(
    contract_v1: DeterminismContract, sample_report: dict
):
    """Test that nested mismatch path is identified."""
    import copy

    baseline = copy.deepcopy(sample_report)
    candidate = copy.deepcopy(sample_report)
    candidate["summary"]["verdict"] = "FAIL"

    result = compare_reports(baseline, candidate, contract_v1)

    assert result.equal is False
    assert result.first_mismatch_path == "$.summary.verdict"


def test_compare_reports_ignores_volatile_fields(contract_v1: DeterminismContract):
    """Test that reports differing only in volatile fields are equal."""
    baseline = {
        "schema_version": "1.0.0",
        "pack_id": "test",
        "timestamp": "2026-01-11T12:00:00Z",
        "stable": "data",
    }
    candidate = {
        "schema_version": "1.0.0",
        "pack_id": "test",
        "timestamp": "2026-01-11T13:00:00Z",  # different
        "stable": "data",
    }

    result = compare_reports(baseline, candidate, contract_v1)

    assert result.equal is True


# =============================================================================
# JSON I/O Tests
# =============================================================================


def test_dumps_canonical_json_stable_formatting(sample_report: dict):
    """Test that canonical JSON has stable formatting."""
    json_str = dumps_canonical_json(sample_report)

    # Should have trailing newline
    assert json_str.endswith("\n")

    # Should be valid JSON
    parsed = json.loads(json_str)
    assert parsed["schema_version"] == "1.0.0"

    # Should be deterministic (re-dump should be identical)
    json_str2 = dumps_canonical_json(sample_report)
    assert json_str == json_str2


def test_load_and_write_json_roundtrip(tmp_path: Path, sample_report: dict):
    """Test that load/write JSON roundtrip preserves data."""
    test_file = tmp_path / "test_report.json"

    # Write
    write_json(test_file, sample_report)
    assert test_file.exists()

    # Load
    loaded = load_json(test_file)
    assert loaded == sample_report


def test_write_json_creates_parent_dirs(tmp_path: Path, sample_report: dict):
    """Test that write_json creates parent directories."""
    nested_file = tmp_path / "nested" / "dir" / "report.json"

    write_json(nested_file, sample_report)

    assert nested_file.exists()
    assert nested_file.parent.exists()


# =============================================================================
# Integration Test with Real Fixture
# =============================================================================


def test_integration_with_real_fixture(contract_v1: DeterminismContract):
    """Integration test with real L4 critic fixture."""
    fixture_path = Path(
        "tests/fixtures/l4_critic_determinism/"
        "l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0/"
        "critic_report.json"
    )

    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")

    # Load real fixture
    report = load_json(fixture_path)

    # Should be valid report structure
    assert "schema_version" in report
    assert "pack_id" in report
    assert "findings" in report

    # Canonicalization should work
    canonical = canonicalize(report, contract=contract_v1)
    assert "schema_version" in canonical

    # Hashing should work
    report_hash = hash_canonical(report, contract_v1)
    assert len(report_hash) == 64

    # Comparing with itself should be equal
    result = compare_reports(report, report, contract_v1)
    assert result.equal is True
