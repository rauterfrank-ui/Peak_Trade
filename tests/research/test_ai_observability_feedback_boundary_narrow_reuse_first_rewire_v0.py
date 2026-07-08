from __future__ import annotations

from pathlib import Path

from scripts.research.ai_observability_feedback_boundary_narrow_reuse_first_rewire_v0 import (
    AI_OBSERVABILITY_BOUNDARY_BACKTEST_CONTRACT_TEST_PATH,
    AI_OBSERVABILITY_OFFLINE_REPLAY_CONTRACT_TEST_PATH,
    CHAINED_CONTRACT_TEST_PATH,
    FEEDBACK_LEARNING_BOUNDARY_BACKTEST_CONTRACT_TEST_PATH,
    FEEDBACK_LEARNING_OFFLINE_REPLAY_CONTRACT_TEST_PATH,
    PLAN_TYPE,
    REUSED_AI_OBSERVABILITY_CANONICAL_OWNER,
    REUSED_FEEDBACK_LEARNING_CANONICAL_OWNER,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_ai_observability_feedback_boundary_parity_fixtures_v0,
)
from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import build_trace_matrix
from trading.master_v2.ai_observability_boundary_offline_replay_binding_adapter_v0 import (
    AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED,
    AI_OBSERVABILITY_BOUNDARY_EFFECT_BOUND_OFFLINE,
)
from trading.master_v2.feedback_learning_boundary_offline_replay_binding_adapter_v0 import (
    FEEDBACK_LEARNING_BOUNDARY_DOCUMENTED,
    FEEDBACK_LEARNING_BOUNDARY_EFFECT_BOUND_OFFLINE,
)


def test_inventory_pins_chained_ai_observability_feedback_backtest_binding_to_parity_contracts() -> (
    None
):
    inventory = build_inventory(Path.cwd())
    surface = next(s for s in inventory["surfaces"] if s["surface_id"] == SURFACE_ID)
    pinned_paths = {hit["path"] for hit in surface["backtest_binding_candidates"][:5]}
    assert AI_OBSERVABILITY_OFFLINE_REPLAY_CONTRACT_TEST_PATH in pinned_paths
    assert AI_OBSERVABILITY_BOUNDARY_BACKTEST_CONTRACT_TEST_PATH in pinned_paths
    assert FEEDBACK_LEARNING_OFFLINE_REPLAY_CONTRACT_TEST_PATH in pinned_paths
    assert FEEDBACK_LEARNING_BOUNDARY_BACKTEST_CONTRACT_TEST_PATH in pinned_paths
    assert CHAINED_CONTRACT_TEST_PATH in pinned_paths
    assert surface["backtest_binding_candidates"][0]["matched_terms"] == ["rewire_binding_pin"]


def test_rewire_binding_reuses_canonical_owners_without_parallel_owner() -> None:
    rewire = build_rewire_binding(Path.cwd())
    binding = rewire["rewire_binding"]

    assert rewire["schema"] == "AiObservabilityFeedbackBoundaryNarrowReuseFirstRewireV1"
    assert rewire["surface_id"] == SURFACE_ID
    assert rewire["plan_type"] == PLAN_TYPE
    assert rewire["trace_assertion_source_pr"] == 5015
    assert (
        binding["reused_ai_observability_canonical_owner"]
        == REUSED_AI_OBSERVABILITY_CANONICAL_OWNER
    )
    assert (
        binding["reused_feedback_learning_canonical_owner"]
        == REUSED_FEEDBACK_LEARNING_CANONICAL_OWNER
    )
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False
    assert binding["promotion_gate_boundary_chain_preserved"] is True
    assert binding["ai_layer_observability_boundary_documented"] is True
    assert binding["feedback_learning_boundary_documented"] is True
    assert binding["ai_observability_read_only_evidence_only"] is True
    assert binding["feedback_learning_observe_only_no_mutation"] is True
    assert binding["rewire_state"] == "REWIRE_BOUND_OFFLINE_PARITY_PATH"


def test_chained_ai_observability_feedback_parity_fixture_binds_offline_only() -> None:
    ai_binding, feedback_binding = evaluate_ai_observability_feedback_boundary_parity_fixtures_v0()
    assert AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED is True
    assert FEEDBACK_LEARNING_BOUNDARY_DOCUMENTED is True
    assert ai_binding.binding_applied is True
    assert feedback_binding.binding_applied is True
    assert (
        ai_binding.ai_observability_boundary_effect
        == AI_OBSERVABILITY_BOUNDARY_EFFECT_BOUND_OFFLINE
    )
    assert (
        feedback_binding.feedback_learning_boundary_effect
        == FEEDBACK_LEARNING_BOUNDARY_EFFECT_BOUND_OFFLINE
    )
    assert ai_binding.ai_observability_boundary_ref
    assert feedback_binding.feedback_learning_boundary_ref
    assert ai_binding.boundary.no_ai_trade_authority is True
    assert feedback_binding.boundary.no_promotion_mutation is True
    assert feedback_binding.boundary.no_runtime_eligibility_mutation is True


def test_rewire_makes_no_forbidden_claims() -> None:
    rewire = build_rewire_binding(Path.cwd())
    assert rewire["runtime_authority"] is False
    assert rewire["orders_allowed"] is False
    assert rewire["economic_claim"] is False
    assert rewire["full_canonical_chain_wired_claimed"] is False
    assert rewire["backtest_runtime_decision_parity_pass_claimed"] is False
    assert rewire["system_economic_evidence_admissible"] is False

    forbidden = rewire["forbidden_claims_remain_false"]
    assert forbidden["FULL_CANONICAL_CHAIN_WIRED"] is False
    assert forbidden["BACKTEST_RUNTIME_DECISION_PARITY_PASS"] is False
    assert forbidden["SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE"] is False
    assert forbidden["RUNTIME_REWIRE_ADMISSIBLE"] is False
    assert forbidden["RUNTIME_AUTHORITY"] is False
    assert forbidden["ORDERS_ALLOWED"] is False
    assert forbidden["ECONOMIC_CLAIM"] is False
    assert all(value is False for value in forbidden.values())


def test_trace_matrix_selects_survival_and_suitability_after_double_play_composition_rewire_bound() -> (
    None
):
    inventory = build_inventory(Path.cwd())
    matrix = build_trace_matrix(inventory)
    assert matrix["selected_next_rewire_plan"]["selected_surface_id"] == "survival_and_suitability"
    ai_feedback_edge = next(
        edge for edge in matrix["trace_edges"] if edge["surface_id"] == SURFACE_ID
    )
    assert ai_feedback_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    promotion_edge = next(
        edge for edge in matrix["trace_edges"] if edge["surface_id"] == "promotion_gate_boundary"
    )
    assert promotion_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
