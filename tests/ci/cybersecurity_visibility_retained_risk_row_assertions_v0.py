"""Shared assertions for retained-risk table rows in histogram crosslink contracts."""

from __future__ import annotations

DERIVED_EVIDENCE_RETAINED_RISKS: dict[str, tuple[str, str]] = {
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


def assert_retained_r001_r002_r007_pending_or_derived_evidence(
    rows: dict[str, tuple[str, str]],
) -> None:
    """Accept pending (—) or mapped-by-derived-evidence while INPUT_JSONL_PROVIDED=false."""
    for risk_id, (expected_owner, derived_id) in DERIVED_EVIDENCE_RETAINED_RISKS.items():
        assert risk_id in rows
        owner_cell, status_cell = rows[risk_id]
        lowered = status_cell.lower()
        if "mapped-by-derived-evidence" in lowered:
            assert expected_owner in owner_cell
            assert derived_id in status_cell
        else:
            assert owner_cell == "—"
            assert "pending" in lowered
            assert "mapped" not in lowered
