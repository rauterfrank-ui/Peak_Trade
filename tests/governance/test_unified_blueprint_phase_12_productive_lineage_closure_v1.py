"""Governance proof for Unified Blueprint Phase 12 productive lineage closure."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.unified_blueprint_phase_12_productive_lineage_closure_v1 import (
    INTEGRATION_CONFIG,
    WORKPACKAGE_ID,
    build_phase_12_integration_summary_v1,
    prove_unified_blueprint_phase_12_productive_lineage_closure_v1,
    validate_phase_12_authority_invariants,
    validate_phase_12_runtime,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _doc() -> dict:
    return json.loads((REPO_ROOT / INTEGRATION_CONFIG).read_text(encoding="utf-8"))


def test_phase_12_proof_passes_on_current_repo() -> None:
    assert prove_unified_blueprint_phase_12_productive_lineage_closure_v1(repo_root=REPO_ROOT)


def test_phase_12_authority_invariants() -> None:
    doc = _doc()
    assert doc["workpackage_id"] == WORKPACKAGE_ID
    assert not validate_phase_12_authority_invariants(doc)
    assert not validate_phase_12_runtime(REPO_ROOT)


def test_phase_12_summary_points_to_phase_13() -> None:
    summary = build_phase_12_integration_summary_v1(repo_root=REPO_ROOT)
    assert summary["phase_12_productive_lineage_closure_status"] == "PROVEN_COMPLETE"
    assert "Phase 13" in str(summary["first_unproven_dependency_after_closure"])
