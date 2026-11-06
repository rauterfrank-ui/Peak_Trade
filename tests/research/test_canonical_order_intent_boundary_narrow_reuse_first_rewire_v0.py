from __future__ import annotations

from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import (
    TRACE_PRIORITY,
    build_trace_matrix,
)
from scripts.research.canonical_order_intent_boundary_narrow_reuse_first_rewire_v0 import (
    BOUNDARY_BACKTEST_CONTRACT_TEST_PATH,
    CHAINED_CONTRACT_TEST_PATH,
    OFFLINE_REPLAY_CONTRACT_TEST_PATH,
    PLAN_TYPE,
    REUSED_CANONICAL_OWNER,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_canonical_order_intent_boundary_parity_fixtures_v0,
)
from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
    ORDER_INTENT_EFFECT_BOUND_OFFLINE,
)


def test_inventory_pins_chained_canonical_order_intent_backtest_binding_to_parity_contracts() -> (
    None
):
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

    assert rewire["schema"] == "CanonicalOrderIntentBoundaryNarrowReuseFirstRewireV1"
    assert rewire["surface_id"] == SURFACE_ID
    assert rewire["plan_type"] == PLAN_TYPE
    assert rewire["trace_assertion_source_pr"] == 5019
    assert binding["reused_canonical_owner"] == REUSED_CANONICAL_OWNER
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False
    assert binding["capital_risk_sizing_chain_preserved"] is True
    assert binding["intent_bound_for_actionable_enter"] is True
    assert binding["intent_compatibility_firewall_represented"] is True
    assert binding["canonical_order_intent_offline_only"] is True
    assert binding["rewire_state"] == "REWIRE_BOUND_OFFLINE_PARITY_PATH"


def test_chained_canonical_order_intent_parity_fixture_binds_offline_only() -> None:
    binding = evaluate_canonical_order_intent_boundary_parity_fixtures_v0()
    assert binding.binding_applied is True
    assert binding.order_intent_effect == ORDER_INTENT_EFFECT_BOUND_OFFLINE
    assert binding.order_intent_ref
    assert binding.canonical_intent is not None
    assert binding.evidence.authority_effect == "NONE"
    assert binding.evidence.runtime_effect == "NONE"
    assert binding.evidence.order_effect == "NONE"


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


def test_trace_matrix_chain_bound_complete_after_canonical_order_intent_rewire() -> None:
    inventory = build_inventory(Path.cwd())
    matrix = build_trace_matrix(inventory)
    assert matrix["selected_next_rewire_plan"]["selected_surface_id"] == "NONE"
    assert (
        matrix["selected_next_rewire_plan"]["plan_type"] == "CHAIN_BOUND_AWAITING_FULL_PARITY_PROOF"
    )
    intent_edge = next(edge for edge in matrix["trace_edges"] if edge["surface_id"] == SURFACE_ID)
    assert intent_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"


def test_trace_chain_preserves_all_twelve_bound_surfaces_through_canonical_order_intent() -> None:
    inventory = build_inventory(Path.cwd())
    matrix = build_trace_matrix(inventory)
    bound_all = list(TRACE_PRIORITY)
    by_surface = {edge["surface_id"]: edge for edge in matrix["trace_edges"]}
    for surface_id in bound_all:
        assert by_surface[surface_id]["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    assert bound_all == TRACE_PRIORITY
