from __future__ import annotations

from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import build_trace_matrix
from scripts.research.promotion_gate_boundary_narrow_reuse_first_rewire_v0 import (
    BOUNDARY_BACKTEST_CONTRACT_TEST_PATH,
    CHAINED_CONTRACT_TEST_PATH,
    OFFLINE_REPLAY_CONTRACT_TEST_PATH,
    PLAN_TYPE,
    REUSED_CANONICAL_OWNER,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_promotion_gate_boundary_parity_fixtures_v0,
)
from trading.master_v2.promotion_gate_boundary_offline_replay_binding_adapter_v0 import (
    PROMOTION_GATE_BOUNDARY_EFFECT_BOUND_OFFLINE,
)


def test_inventory_pins_chained_promotion_gate_backtest_binding_to_parity_contracts() -> None:
    inventory = build_inventory(Path.cwd())
    surface = next(s for s in inventory["surfaces"] if s["surface_id"] == SURFACE_ID)
    pinned_paths = {hit["path"] for hit in surface["backtest_binding_candidates"][:3]}
    assert OFFLINE_REPLAY_CONTRACT_TEST_PATH in pinned_paths
    assert BOUNDARY_BACKTEST_CONTRACT_TEST_PATH in pinned_paths
    assert CHAINED_CONTRACT_TEST_PATH in pinned_paths
    assert surface["backtest_binding_candidates"][0]["matched_terms"] == ["rewire_binding_pin"]


def test_rewire_binding_reuses_canonical_owners_without_parallel_owner() -> None:
    rewire = build_rewire_binding(Path.cwd())
    binding = rewire["rewire_binding"]

    assert rewire["schema"] == "PromotionGateBoundaryNarrowReuseFirstRewireV1"
    assert rewire["surface_id"] == SURFACE_ID
    assert rewire["plan_type"] == PLAN_TYPE
    assert rewire["trace_assertion_source_pr"] == 5014
    assert binding["reused_canonical_owner"] == REUSED_CANONICAL_OWNER
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False
    assert binding["reconciliation_unknown_outcome_chain_preserved"] is True
    assert binding["promotion_gate_semantics_represented"] is True
    assert binding["no_runtime_authority_from_promotion_represented"] is True
    assert binding["economic_validity_required_for_promotion_represented"] is True
    assert binding["rewire_state"] == "REWIRE_BOUND_OFFLINE_PARITY_PATH"


def test_chained_promotion_gate_parity_fixture_binds_offline_only() -> None:
    binding = evaluate_promotion_gate_boundary_parity_fixtures_v0()
    assert binding.binding_applied is True
    assert binding.promotion_gate_boundary_effect == PROMOTION_GATE_BOUNDARY_EFFECT_BOUND_OFFLINE
    assert binding.promotion_gate_boundary_ref
    assert binding.boundary.promotion_gate_semantics_represented is True
    assert binding.boundary.no_runtime_authority_from_promotion_represented is True
    assert binding.gate_result.runtime_eligible is False
    assert binding.gate_result.execution_allowed is False


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


def test_trace_matrix_keeps_promotion_gate_and_canonical_order_intent_bound_in_chain() -> None:
    inventory = build_inventory(Path.cwd())
    matrix = build_trace_matrix(inventory)
    promotion_edge = next(
        edge for edge in matrix["trace_edges"] if edge["surface_id"] == SURFACE_ID
    )
    assert promotion_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
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
