"""Governance proof for Unified Blueprint Phase 22 incremental research."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.unified_blueprint_phase_22_incremental_research_v1 import (
    INTEGRATION_CONFIG,
    WORKPACKAGE_ID,
    build_current_optimization_research_census_v1,
    build_phase_22_integration_summary_v1,
    prove_unified_blueprint_phase_22_incremental_research_v1,
    validate_phase_22_authority_invariants,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _doc() -> dict:
    return json.loads((REPO_ROOT / INTEGRATION_CONFIG).read_text(encoding="utf-8"))


def test_phase_22_proof_passes_on_current_repo() -> None:
    assert prove_unified_blueprint_phase_22_incremental_research_v1(repo_root=REPO_ROOT)


def test_phase_22_authority_invariants() -> None:
    doc = _doc()
    assert doc["workpackage_id"] == WORKPACKAGE_ID
    assert not validate_phase_22_authority_invariants(doc)


def test_phase_22_census_marks_true_l2_missing() -> None:
    census = build_current_optimization_research_census_v1()
    assert census["true_l2_research_substrate"] == "MISSING"
    assert census["optimization_universe"] == "PROVEN_CURRENT"


def test_phase_22_summary_points_to_phase_23_boundary() -> None:
    summary = build_phase_22_integration_summary_v1(repo_root=REPO_ROOT)
    assert summary["phase_22_closure_status"] == "PROVEN_COMPLETE"
    assert summary["b5_status"] == "DEFERRED_NOT_CURRENTLY_ADMISSIBLE"
    assert "phase 23" in summary["next_implementation_boundary"].lower()
