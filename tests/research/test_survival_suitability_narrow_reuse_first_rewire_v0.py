from __future__ import annotations

from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import (
    TRACE_PRIORITY,
    build_trace_matrix,
)
from scripts.research.survival_suitability_narrow_reuse_first_rewire_v0 import (
    CHAINED_CONTRACT_TEST_PATH,
    PLAN_TYPE,
    REUSED_SCENARIO_BINDING_ADAPTER_OWNER,
    REUSED_SUITABILITY_BINDING_OWNER,
    REUSED_SURVIVAL_ASSESSMENT_OWNER,
    SCENARIO_REPLAY_CONTRACT_TEST_PATH,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_survival_suitability_parity_fixtures_v0,
)
from trading.master_v2.survival_assessment_v1 import SurvivalAssessmentStatus
from trading.master_v2.suitability_binding_v1 import SuitabilityBindingStatus


def test_inventory_pins_chained_survival_suitability_backtest_binding_to_parity_contracts() -> None:
    inventory = build_inventory(Path.cwd())
    surface = next(s for s in inventory["surfaces"] if s["surface_id"] == SURFACE_ID)
    pinned_paths = {hit["path"] for hit in surface["backtest_binding_candidates"][:5]}
    assert SCENARIO_REPLAY_CONTRACT_TEST_PATH in pinned_paths
    assert CHAINED_CONTRACT_TEST_PATH in pinned_paths
    assert surface["backtest_binding_candidates"][0]["matched_terms"] == ["rewire_binding_pin"]


def test_rewire_binding_reuses_canonical_owners_without_parallel_owner() -> None:
    rewire = build_rewire_binding(Path.cwd())
    binding = rewire["rewire_binding"]

    assert rewire["schema"] == "SurvivalSuitabilityNarrowReuseFirstRewireV1"
    assert rewire["surface_id"] == SURFACE_ID
    assert rewire["plan_type"] == PLAN_TYPE
    assert rewire["trace_assertion_source_pr"] == 5017
    assert binding["reused_survival_assessment_owner"] == REUSED_SURVIVAL_ASSESSMENT_OWNER
    assert binding["reused_suitability_binding_owner"] == REUSED_SUITABILITY_BINDING_OWNER
    assert binding["reused_scenario_binding_adapter_owner"] == REUSED_SCENARIO_BINDING_ADAPTER_OWNER
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False
    assert binding["double_play_composition_chain_preserved"] is True
    assert binding["survival_hard_fail_blocks_composition"] is True
    assert binding["survival_required_unknown_fail_closed"] is True
    assert binding["suitability_deterministic_strategy_selection"] is True
    assert binding["no_list_order_strategy_override"] is True
    assert binding["no_confidence_only_selection"] is True
    assert binding["cost_model_boundary_bound"] is True
    assert binding["regime_owner_boundary_bound"] is True
    assert binding["survival_suitability_offline_only"] is True
    assert binding["rewire_state"] == "REWIRE_BOUND_OFFLINE_PARITY_PATH"


def test_chained_survival_suitability_parity_fixture_binds_offline_only() -> None:
    result = evaluate_survival_suitability_parity_fixtures_v0()
    assert result.bull_survival.status is SurvivalAssessmentStatus.PASS
    assert result.bull_suitability.status is SuitabilityBindingStatus.PASS
    assert result.bull_survival.authority_effect == "NONE"
    assert result.bull_survival.runtime_effect == "NONE"
    assert result.bull_survival.order_effect == "NONE"
    assert result.bull_suitability.authority_effect == "NONE"
    assert result.bull_suitability.runtime_effect == "NONE"
    assert result.bull_suitability.order_effect == "NONE"


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


def test_trace_matrix_selects_canonical_order_intent_after_survival_suitability_rewire_bound() -> (
    None
):
    inventory = build_inventory(Path.cwd())
    matrix = build_trace_matrix(inventory)
    assert (
        matrix["selected_next_rewire_plan"]["selected_surface_id"]
        == "canonical_order_intent_boundary"
    )
    survival_edge = next(edge for edge in matrix["trace_edges"] if edge["surface_id"] == SURFACE_ID)
    assert survival_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    double_play_edge = next(
        edge for edge in matrix["trace_edges"] if edge["surface_id"] == "double_play_composition"
    )
    assert double_play_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"


def test_trace_chain_preserves_prior_bound_surfaces_through_survival_suitability() -> None:
    inventory = build_inventory(Path.cwd())
    matrix = build_trace_matrix(inventory)
    bound_prior = [
        "capital_risk_sizing",
        "safety_kernel_and_killswitch_boundary",
        "reconciliation_unknown_outcome",
        "promotion_gate_boundary",
        "ai_observability_feedback_boundary",
        "double_play_composition",
        "survival_and_suitability",
    ]
    by_surface = {edge["surface_id"]: edge for edge in matrix["trace_edges"]}
    for surface_id in bound_prior:
        assert by_surface[surface_id]["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    chain_slice = TRACE_PRIORITY[
        TRACE_PRIORITY.index("capital_risk_sizing") : TRACE_PRIORITY.index(SURFACE_ID) + 1
    ]
    assert chain_slice == bound_prior
