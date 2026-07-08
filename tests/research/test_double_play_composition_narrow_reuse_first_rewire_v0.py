from __future__ import annotations

from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import (
    TRACE_PRIORITY,
    build_trace_matrix,
)
from scripts.research.double_play_composition_narrow_reuse_first_rewire_v0 import (
    CHAINED_CONTRACT_TEST_PATH,
    PLAN_TYPE,
    REUSED_CANONICAL_OWNER,
    REUSED_SCENARIO_MATRIX_ADAPTER_OWNER,
    SCENARIO_MATRIX_PARITY_CONTRACT_TEST_PATH,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_double_play_composition_parity_fixtures_v0,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionConflictStatus,
    CompositionSelectedSide,
    CompositionStatus,
)


def test_inventory_pins_chained_double_play_composition_backtest_binding_to_parity_contracts() -> (
    None
):
    inventory = build_inventory(Path.cwd())
    surface = next(s for s in inventory["surfaces"] if s["surface_id"] == SURFACE_ID)
    pinned_paths = {hit["path"] for hit in surface["backtest_binding_candidates"][:5]}
    assert SCENARIO_MATRIX_PARITY_CONTRACT_TEST_PATH in pinned_paths
    assert CHAINED_CONTRACT_TEST_PATH in pinned_paths
    assert surface["backtest_binding_candidates"][0]["matched_terms"] == ["rewire_binding_pin"]


def test_rewire_binding_reuses_canonical_owners_without_parallel_owner() -> None:
    rewire = build_rewire_binding(Path.cwd())
    binding = rewire["rewire_binding"]

    assert rewire["schema"] == "DoublePlayCompositionNarrowReuseFirstRewireV1"
    assert rewire["surface_id"] == SURFACE_ID
    assert rewire["plan_type"] == PLAN_TYPE
    assert rewire["trace_assertion_source_pr"] == 5016
    assert binding["reused_canonical_owner"] == REUSED_CANONICAL_OWNER
    assert binding["reused_scenario_matrix_adapter_owner"] == REUSED_SCENARIO_MATRIX_ADAPTER_OWNER
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False
    assert binding["ai_observability_feedback_boundary_chain_preserved"] is True
    assert binding["both_sides_confirmed_resolves_to_chop_guard_block"] is True
    assert binding["no_implicit_scoring_override"] is True
    assert binding["no_list_order_strategy_override"] is True
    assert binding["composition_matrix_complete"] is True
    assert binding["composition_conflict_rule_represented"] is True
    assert binding["composition_offline_only"] is True
    assert binding["rewire_state"] == "REWIRE_BOUND_OFFLINE_PARITY_PATH"


def test_chained_double_play_composition_parity_fixture_binds_offline_only() -> None:
    result = evaluate_double_play_composition_parity_fixtures_v0()
    assert result.composition_status is CompositionStatus.CHOP_GUARD_BLOCK
    assert result.conflict_status is CompositionConflictStatus.BOTH_SIDES_CONFIRMED
    assert result.selected_side is CompositionSelectedSide.NONE
    assert "no_new_entry" in result.reason_codes
    assert "existing_position_management_continues" in result.reason_codes
    assert result.authority_effect == "NONE"
    assert result.runtime_effect == "NONE"
    assert result.order_effect == "NONE"


def test_rewire_makes_no_forbidden_claims() -> None:
    rewire = build_rewire_binding(Path.cwd())
    assert rewire["runtime_authority"] is False
    assert rewire["orders_allowed"] is False
    assert rewire["economic_claim"] is False
    assert rewire["full_canonical_chain_wired_claimed"] is False
    assert rewire["backtest_runtime_decision_parity_pass_claimed"] is False
    assert rewire["system_economic_evidence_admissible"] is False

    forbidden = rewire["forbidden_claims_remain_false"]
    assert all(value is False for value in forbidden.values())


def test_trace_matrix_keeps_double_play_and_canonical_order_intent_bound_in_chain() -> None:
    inventory = build_inventory(Path.cwd())
    matrix = build_trace_matrix(inventory)
    double_play_edge = next(
        edge for edge in matrix["trace_edges"] if edge["surface_id"] == SURFACE_ID
    )
    assert double_play_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    intent_edge = next(
        edge
        for edge in matrix["trace_edges"]
        if edge["surface_id"] == "canonical_order_intent_boundary"
    )
    assert intent_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    ai_feedback_edge = next(
        edge
        for edge in matrix["trace_edges"]
        if edge["surface_id"] == "ai_observability_feedback_boundary"
    )
    assert ai_feedback_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"


def test_trace_chain_preserves_prior_bound_surfaces_through_double_play_composition() -> None:
    inventory = build_inventory(Path.cwd())
    matrix = build_trace_matrix(inventory)
    bound_prior = [
        "capital_risk_sizing",
        "safety_kernel_and_killswitch_boundary",
        "reconciliation_unknown_outcome",
        "promotion_gate_boundary",
        "ai_observability_feedback_boundary",
        "double_play_composition",
    ]
    by_surface = {edge["surface_id"]: edge for edge in matrix["trace_edges"]}
    for surface_id in bound_prior:
        assert by_surface[surface_id]["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    chain_slice = TRACE_PRIORITY[
        TRACE_PRIORITY.index("capital_risk_sizing") : TRACE_PRIORITY.index(SURFACE_ID) + 1
    ]
    assert chain_slice == bound_prior
