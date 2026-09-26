"""Governance proof for Unified Blueprint Phase 14 decision attribution."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.unified_blueprint_phase_14_decision_attribution_v1 import (
    INTEGRATION_CONFIG,
    WORKPACKAGE_ID,
    build_phase_14_integration_summary_v1,
    prove_unified_blueprint_phase_14_decision_attribution_v1,
    validate_phase_14_authority_invariants,
    validate_phase_14_runtime,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _doc() -> dict:
    return json.loads((REPO_ROOT / INTEGRATION_CONFIG).read_text(encoding="utf-8"))


def test_phase_14_proof_passes_on_current_repo() -> None:
    assert prove_unified_blueprint_phase_14_decision_attribution_v1(repo_root=REPO_ROOT)


def test_phase_14_authority_invariants() -> None:
    doc = _doc()
    assert doc["workpackage_id"] == WORKPACKAGE_ID
    assert not validate_phase_14_authority_invariants(doc)
    assert not validate_phase_14_runtime(REPO_ROOT)


def test_phase_14_summary_records_next_boundary() -> None:
    summary = build_phase_14_integration_summary_v1(repo_root=REPO_ROOT)
    assert summary["phase_14_decision_attribution_status"] == "PROVEN_COMPLETE"
    assert summary.get("first_unproven_dependency_after_closure")
