"""Shared assertions for retained-risk table rows in histogram crosslink contracts."""

from __future__ import annotations

DEFINITIVE_MAPPED_RETAINED_RISKS: dict[str, tuple[str, str]] = {
    "R-001": (
        "tests/ci/test_workflow_write_permissions_visibility_contract_v0.py",
        "DERIVED-CYBER-R-001-001",
    ),
    "R-002": (
        "tests/ci/test_cybersecurity_visibility_r_pending_mapping_guard_v0.py",
        "DERIVED-CYBER-R-002-001",
    ),
    "R-007": (
        "tests/ci/test_workflow_secrets_reference_visibility_contract_v0.py",
        "DERIVED-CYBER-R-007-001",
    ),
}

DERIVED_EVIDENCE_RETAINED_RISKS = DEFINITIVE_MAPPED_RETAINED_RISKS


def assert_retained_r001_r002_r007_definitive_mapped(
    rows: dict[str, tuple[str, str]],
) -> None:
    """Require definitive mapped status for R-001/R-002/R-007 after validated INPUT_JSONL."""
    for risk_id, (expected_owner, derived_id) in DEFINITIVE_MAPPED_RETAINED_RISKS.items():
        assert risk_id in rows
        owner_cell, status_cell = rows[risk_id]
        lowered = status_cell.lower()
        assert expected_owner in owner_cell
        assert lowered == "mapped" or (
            "mapped" in lowered and "mapped-by-derived-evidence" not in lowered
        )
        assert derived_id in status_cell or "wave-1 lineage" in lowered


def assert_retained_r001_r002_r007_pending_or_derived_evidence(
    rows: dict[str, tuple[str, str]],
) -> None:
    """Backward-compatible alias — definitive mapped supersedes pending/derived-evidence."""
    assert_retained_r001_r002_r007_definitive_mapped(rows)
