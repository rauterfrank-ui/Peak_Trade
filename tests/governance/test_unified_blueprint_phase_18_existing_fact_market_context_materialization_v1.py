"""Governance proof for Unified Blueprint Phase 18 existing-fact materialization."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.unified_blueprint_phase_18_existing_fact_market_context_materialization_v1 import (
    INTEGRATION_CONFIG,
    WORKPACKAGE_ID,
    build_phase_18_integration_summary_v1,
    prove_unified_blueprint_phase_18_existing_fact_market_context_materialization_v1,
    validate_phase_18_authority_invariants,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _doc() -> dict:
    return json.loads((REPO_ROOT / INTEGRATION_CONFIG).read_text(encoding="utf-8"))


def test_phase_18_proof_passes_on_current_repo() -> None:
    assert prove_unified_blueprint_phase_18_existing_fact_market_context_materialization_v1(
        repo_root=REPO_ROOT
    )


def test_phase_18_authority_invariants() -> None:
    doc = _doc()
    assert doc["workpackage_id"] == WORKPACKAGE_ID
    assert not validate_phase_18_authority_invariants(doc)
    assert doc["family_materialization_status"]["derivatives_state"] == "EXPLICIT_MISSING_PHASE_19"


def test_phase_18_summary_records_runtime_apply_still_next() -> None:
    summary = build_phase_18_integration_summary_v1(repo_root=REPO_ROOT)
    assert summary["phase_18_closure_status"] == "PROVEN_COMPLETE"
    assert summary["market_context_materialization_status"] == "EXISTING_FACT_OFFLINE_PROVEN"
    assert "runtime apply" in summary["first_unproven_dependency_after_closure"].lower()
