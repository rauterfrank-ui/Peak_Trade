"""Governance proof for Unified Blueprint Phase 10 MI-crossing multi-cycle replay."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.unified_blueprint_phase_10_mi_crossing_multi_cycle_offline_replay_v1 import (
    INTEGRATION_CONFIG,
    WORKPACKAGE_ID,
    build_phase_10_integration_summary_v1,
    prove_unified_blueprint_phase_10_mi_crossing_multi_cycle_offline_replay_v1,
    validate_d02_multi_cycle_replay_edge_implemented,
    validate_phase_10_authority_invariants,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _doc() -> dict:
    return json.loads((REPO_ROOT / INTEGRATION_CONFIG).read_text(encoding="utf-8"))


def test_phase_10_proof_passes_on_current_repo() -> None:
    assert prove_unified_blueprint_phase_10_mi_crossing_multi_cycle_offline_replay_v1(
        repo_root=REPO_ROOT
    )


def test_phase_10_authority_invariants_and_d02_edge() -> None:
    doc = _doc()
    assert doc["workpackage_id"] == WORKPACKAGE_ID
    assert not validate_phase_10_authority_invariants(doc)
    assert not validate_d02_multi_cycle_replay_edge_implemented(REPO_ROOT)


def test_phase_10_summary_reports_implemented_m8_edge() -> None:
    summary = build_phase_10_integration_summary_v1(repo_root=REPO_ROOT)
    assert summary["d02_multi_cycle_replay_m8_status"] == "IMPLEMENTED"
    assert summary["phase_10_mi_crossing_multi_cycle_offline_replay_status"] == "PROVEN_COMPLETE"
    assert "d02_loop_b" in str(summary["first_unproven_dependency_after_closure"])
