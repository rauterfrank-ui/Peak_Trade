from __future__ import annotations

from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import build_trace_matrix
from scripts.research.flat_before_opposite_side_narrow_reuse_first_rewire_v0 import (
    CONTRACT_TEST_PATH,
    PLAN_TYPE,
    REUSED_CANONICAL_OWNER,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_flat_before_opposite_side_parity_fixtures_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome


def _flat_surface(inventory: dict) -> dict:
    return next(s for s in inventory["surfaces"] if s["surface_id"] == SURFACE_ID)


def test_inventory_pins_flat_before_opposite_side_backtest_binding_to_parity_contract() -> None:
    inventory = build_inventory(Path.cwd())
    surface = _flat_surface(inventory)
    pinned_paths = {hit["path"] for hit in surface["backtest_binding_candidates"][:2]}
    assert CONTRACT_TEST_PATH in pinned_paths
    assert surface["backtest_binding_candidates"][0]["matched_terms"] == ["rewire_binding_pin"]


def test_rewire_binding_reuses_canonical_owners_without_parallel_owner() -> None:
    rewire = build_rewire_binding(Path.cwd())
    binding = rewire["rewire_binding"]

    assert rewire["schema"] == "FlatBeforeOppositeSideNarrowReuseFirstRewireV1"
    assert rewire["plan_type"] == PLAN_TYPE
    assert rewire["trace_assertion_source_pr"] == 5008
    assert binding["reused_canonical_owner"] == REUSED_CANONICAL_OWNER
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False
    assert binding["rewire_state"] == "REWIRE_BOUND_OFFLINE_PARITY_PATH"


def test_flat_before_opposite_side_parity_fixture_blocks_opposite_entry() -> None:
    decision = evaluate_flat_before_opposite_side_parity_fixtures_v0()
    assert decision.decision_outcome is not DecisionOutcome.ENTER_SHORT
    assert decision.position_flip_allowed is False
    assert decision.policy_decision_id


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


def test_trace_matrix_selects_entry_position_exit_after_flat_before_rewire_bound() -> None:
    inventory = build_inventory(Path.cwd())
    matrix = build_trace_matrix(inventory)
    assert (
        matrix["selected_next_rewire_plan"]["selected_surface_id"] == "entry_position_exit_policy"
    )
    assert matrix["selected_next_rewire_plan"]["plan_type"] == PLAN_TYPE
    scope_edge = matrix["trace_edges"][1]
    assert scope_edge["surface_id"] == "scope_adverse_exit_and_reversal_preparation"
    assert scope_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    flat_edge = matrix["trace_edges"][2]
    assert flat_edge["surface_id"] == SURFACE_ID
    assert flat_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    assert flat_edge["backtest_candidate"] == CONTRACT_TEST_PATH
