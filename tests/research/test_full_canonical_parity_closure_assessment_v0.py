from __future__ import annotations

from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import SURFACES, build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import (
    TRACE_PRIORITY,
    TRACE_REWIRE_BOUND_STATE,
    build_trace_matrix,
    compute_chain_surface_binding_complete,
    compute_next_unbound_node,
)
from scripts.research.full_canonical_parity_closure_assessment_v0 import (
    ASSESSMENT_ID,
    FORBIDDEN_POSITIVE_CLAIM_LITERALS,
    SCHEMA,
    SLICE_CHANGED_FILES,
    build_closure_assessment,
    scan_forbidden_positive_claims,
)

REQUIRED_SURFACES = (
    "capital_risk_sizing",
    "safety_kernel_and_killswitch_boundary",
    "reconciliation_unknown_outcome",
    "promotion_gate_boundary",
    "ai_observability_feedback_boundary",
    "double_play_composition",
    "survival_and_suitability",
    "canonical_order_intent_boundary",
)


def test_closure_assessment_schema_and_fail_closed_status() -> None:
    assessment = build_closure_assessment(Path.cwd())
    assert assessment["schema"] == SCHEMA
    assert assessment["assessment"] == ASSESSMENT_ID
    assert assessment["chain_surface_binding_complete"] is True
    assert assessment["known_unbound_parity_node"] == "NONE"
    assert assessment["next_unbound_node"] == "NONE"
    assert assessment["parity_pass_claim_deferred"] is True
    assert assessment["no_runtime_authority"] is True
    assert assessment["no_order_authority"] is True
    assert assessment["no_economic_evidence"] is True
    assert assessment["full_canonical_chain_wired"] is False
    assert assessment["backtest_runtime_decision_parity_pass"] is False
    assert assessment["system_economic_evidence_admissible"] is False
    assert assessment["runtime_rewire_admissible"] is False
    assert assessment["trace_rewire_bound_surface_count"] == 12
    assert assessment["inventory_surface_count"] == len(SURFACES)


def test_closure_assessment_includes_all_required_surfaces_in_trace_chain() -> None:
    assessment = build_closure_assessment(Path.cwd())
    by_surface = {edge["surface_id"]: edge for edge in assessment["trace_edges"]}
    for surface_id in REQUIRED_SURFACES:
        assert surface_id in by_surface
        assert by_surface[surface_id]["trace_state"] == TRACE_REWIRE_BOUND_STATE


def test_trace_matrix_next_unbound_node_none_when_all_surfaces_bound() -> None:
    inventory = build_inventory(Path.cwd())
    matrix = build_trace_matrix(inventory)
    assert matrix["next_unbound_node"] == "NONE"
    assert matrix["known_unbound_parity_node"] == "NONE"
    assert matrix["chain_surface_binding_complete"] is True
    assert matrix["parity_pass_claim_deferred"] is True
    assert matrix["selected_next_rewire_plan"]["selected_surface_id"] == "NONE"
    assert (
        matrix["selected_next_rewire_plan"]["plan_type"] == "CHAIN_BOUND_AWAITING_FULL_PARITY_PROOF"
    )


def test_trace_matrix_all_twelve_surfaces_trace_rewire_bound() -> None:
    inventory = build_inventory(Path.cwd())
    matrix = build_trace_matrix(inventory)
    by_surface = {edge["surface_id"]: edge for edge in matrix["trace_edges"]}
    for surface_id in TRACE_PRIORITY:
        assert by_surface[surface_id]["trace_state"] == TRACE_REWIRE_BOUND_STATE
    assert compute_next_unbound_node(matrix["trace_edges"]) == "NONE"
    assert compute_chain_surface_binding_complete(matrix["trace_edges"]) is True


def test_forbidden_positive_claims_scan_allows_context_protected_literals() -> None:
    violations = scan_forbidden_positive_claims(Path.cwd(), list(SLICE_CHANGED_FILES))
    assert violations == []


def test_forbidden_positive_claim_literals_are_documented_not_claimed() -> None:
    assessment = build_closure_assessment(Path.cwd())
    assert assessment["forbidden_positive_claim_literals"] == list(
        FORBIDDEN_POSITIVE_CLAIM_LITERALS
    )
    assert assessment["full_canonical_chain_wired_claimed"] is False
    assert assessment["backtest_runtime_decision_parity_pass_claimed"] is False
