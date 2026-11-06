"""Governance proof for Unified Blueprint Phase 13 M10 promotion boundary."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.unified_blueprint_phase_13_m10_promotion_boundary_v1 import (
    INTEGRATION_CONFIG,
    WORKPACKAGE_ID,
    build_phase_13_integration_summary_v1,
    prove_unified_blueprint_phase_13_m10_promotion_boundary_v1,
    validate_phase_13_authority_invariants,
    validate_phase_13_runtime,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _doc() -> dict:
    return json.loads((REPO_ROOT / INTEGRATION_CONFIG).read_text(encoding="utf-8"))


def test_phase_13_proof_passes_on_current_repo() -> None:
    assert prove_unified_blueprint_phase_13_m10_promotion_boundary_v1(repo_root=REPO_ROOT)


def test_phase_13_authority_invariants() -> None:
    doc = _doc()
    assert doc["workpackage_id"] == WORKPACKAGE_ID
    assert not validate_phase_13_authority_invariants(doc)
    assert not validate_phase_13_runtime(REPO_ROOT)


def test_phase_13_summary_points_to_phase_14() -> None:
    summary = build_phase_13_integration_summary_v1(repo_root=REPO_ROOT)
    assert summary["phase_13_m10_promotion_boundary_status"] == "PROVEN_COMPLETE"
    assert "Phase 14" in str(summary["first_unproven_dependency_after_closure"])
