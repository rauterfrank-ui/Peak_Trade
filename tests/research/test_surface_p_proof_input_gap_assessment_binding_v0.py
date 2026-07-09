"""Surface P required proof-input gap assessment binding contract (offline only)."""

from __future__ import annotations

import json
from pathlib import Path

from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    get_surface_p_required_proof_input_binding_v0,
    render_parity_gap_matrix_json_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_surface_p_required_proof_input_binding_is_fail_closed() -> None:
    binding = get_surface_p_required_proof_input_binding_v0(REPO_ROOT)

    assert binding["surface_id"] == "P"
    assert binding["required_proof_input_id"] == "backtest_offline_replay_runtime_decision_parity"
    assert binding["required_proof_input_binding_status"] == "BOUND_FROM_REPAIRED_SOURCE_EVIDENCE"
    assert binding["accepted_source_status"] == "PARTIAL"
    assert binding["partial_reason_required"] == "RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED"
    assert binding["proof_input_satisfied"] is True

    assert binding["full_canonical_chain_wired"] is False
    assert binding["backtest_runtime_decision_parity_pass"] is False
    assert binding["system_economic_evidence_admissible"] is False
    assert binding["runtime_rewire_admissible"] is False
    assert binding["claim_promotion_allowed"] is False

    assert binding["runtime_authority_effect"] == "NONE"
    assert binding["order_authority_effect"] == "NONE"
    assert binding["safety_semantics_changed"] is False
    assert binding["economic_claim_changed"] is False
    assert binding["no_runtime_authority_confirmed"] is True
    assert binding["no_economic_claim_confirmed"] is True


def test_parity_gap_matrix_json_includes_surface_p_proof_input_binding() -> None:
    payload = json.loads(render_parity_gap_matrix_json_v0())
    top_binding = payload["surface_p_required_proof_input_binding"]
    surface_p = next(item for item in payload["surfaces"] if item["surface_id"] == "P")

    assert (
        top_binding["required_proof_input_binding_status"] == "BOUND_FROM_REPAIRED_SOURCE_EVIDENCE"
    )
    assert surface_p["surface_p_required_proof_input_binding"]["proof_input_satisfied"] is True
    assert payload["summary"]["full_canonical_chain_wired"] is False
    assert payload["summary"]["backtest_runtime_decision_parity_pass"] is False
