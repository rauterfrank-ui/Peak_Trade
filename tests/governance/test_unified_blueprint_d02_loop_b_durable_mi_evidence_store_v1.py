"""Governance proof for Unified Blueprint D02 Loop-B durable MI evidence store."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.unified_blueprint_d02_loop_b_durable_mi_evidence_store_v1 import (
    INTEGRATION_CONFIG,
    WORKPACKAGE_ID,
    build_loop_b_durable_store_summary_v1,
    prove_unified_blueprint_d02_loop_b_durable_mi_evidence_store_v1,
    validate_d02_loop_b_edge_implemented,
    validate_loop_b_authority_invariants,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _doc() -> dict:
    return json.loads((REPO_ROOT / INTEGRATION_CONFIG).read_text(encoding="utf-8"))


def test_loop_b_proof_passes_on_current_repo() -> None:
    assert prove_unified_blueprint_d02_loop_b_durable_mi_evidence_store_v1(repo_root=REPO_ROOT)


def test_loop_b_authority_invariants_and_d02_edge() -> None:
    doc = _doc()
    assert doc["workpackage_id"] == WORKPACKAGE_ID
    assert not validate_loop_b_authority_invariants(doc)
    assert not validate_d02_loop_b_edge_implemented(REPO_ROOT)


def test_loop_b_summary_reports_implemented_edge() -> None:
    summary = build_loop_b_durable_store_summary_v1(repo_root=REPO_ROOT)
    assert summary["d02_loop_b_market_intelligence_offline_status"] == "IMPLEMENTED"
    assert summary["d02_loop_b_durable_mi_evidence_store_status"] == "PROVEN_COMPLETE"
    assert "separate Owner authorization" in str(summary["first_unproven_dependency_after_closure"])
    assert "Phase 11" in str(summary["first_unproven_dependency_after_closure"])
