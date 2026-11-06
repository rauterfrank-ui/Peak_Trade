"""Governance proof for Unified Blueprint Phase 25 DP Attribution closure."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.unified_blueprint_phase_25_dp_attribution_v1 import (
    INTEGRATION_CONFIG,
    WORKPACKAGE_ID,
    build_phase_25_integration_summary_v1,
    prove_unified_blueprint_phase_25_dp_attribution_v1,
    validate_phase_25_authority_invariants,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _doc() -> dict:
    return json.loads((REPO_ROOT / INTEGRATION_CONFIG).read_text(encoding="utf-8"))


def test_phase_25_proof_passes_on_current_repo() -> None:
    assert prove_unified_blueprint_phase_25_dp_attribution_v1(repo_root=REPO_ROOT)


def test_phase_25_dp_attribution_proven_in_config() -> None:
    doc = _doc()
    assert doc["workpackage_id"] == WORKPACKAGE_ID
    assert not validate_phase_25_authority_invariants(doc)
    assert doc["dp_attribution_proof"]["dp_attribution_proven"] is True


def test_phase_25_summary_points_to_phase_26_boundary() -> None:
    summary = build_phase_25_integration_summary_v1(repo_root=REPO_ROOT)
    assert summary["phase_25_closure_status"] == "PROVEN_COMPLETE"
    assert "phase 26" in summary["next_implementation_boundary"].lower()
