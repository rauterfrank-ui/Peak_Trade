from __future__ import annotations

from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import build_trace_matrix
from scripts.research.entry_position_exit_policy_narrow_reuse_first_rewire_v0 import (
    CHAINED_CONTRACT_TEST_PATH,
    ENTRY_EXIT_CONTRACT_TEST_PATH,
    FLAT_BEFORE_CONTRACT_TEST_PATH,
    PLAN_TYPE,
    REUSED_CANONICAL_OWNER,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_entry_position_exit_policy_parity_fixtures_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome


def test_inventory_pins_chained_entry_position_exit_backtest_binding_to_parity_contracts() -> None:
    inventory = build_inventory(Path.cwd())
    surface = next(
        s for s in inventory["surfaces"] if s["surface_id"] == "entry_position_exit_policy"
    )
    pinned_paths = {hit["path"] for hit in surface["backtest_binding_candidates"][:3]}
    assert ENTRY_EXIT_CONTRACT_TEST_PATH in pinned_paths
    assert FLAT_BEFORE_CONTRACT_TEST_PATH in pinned_paths
    assert CHAINED_CONTRACT_TEST_PATH in pinned_paths
    assert surface["backtest_binding_candidates"][0]["matched_terms"] == ["rewire_binding_pin"]


def test_rewire_binding_reuses_canonical_owners_without_parallel_owner() -> None:
    rewire = build_rewire_binding(Path.cwd())
    binding = rewire["rewire_binding"]

    assert rewire["schema"] == "EntryPositionExitPolicyNarrowReuseFirstRewireV1"
    assert rewire["surface_id"] == SURFACE_ID
    assert rewire["plan_type"] == PLAN_TYPE
    assert rewire["trace_assertion_source_pr"] == 5010
    assert binding["reused_canonical_owner"] == REUSED_CANONICAL_OWNER
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False
    assert binding["flat_before_context_merged_into_entry_exit_policy"] is True
    assert binding["adverse_scope_signal_wired_into_entry_exit_policy"] is True
    assert binding["rewire_state"] == "REWIRE_BOUND_OFFLINE_PARITY_PATH"


def test_chained_entry_position_exit_parity_fixture_blocks_opposite_entry() -> None:
    decision = evaluate_entry_position_exit_policy_parity_fixtures_v0()
    assert decision.decision_outcome not in (
        DecisionOutcome.ENTER_LONG,
        DecisionOutcome.ENTER_SHORT,
    )
    assert decision.position_flip_allowed is False
    assert decision.policy_decision_id
    assert decision.decision_precedence_trace


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


def test_trace_matrix_selects_capital_risk_sizing_after_entry_position_exit_rewire_bound() -> None:
    inventory = build_inventory(Path.cwd())
    matrix = build_trace_matrix(inventory)
    assert matrix["selected_next_rewire_plan"]["selected_surface_id"] == "capital_risk_sizing"
    assert matrix["selected_next_rewire_plan"]["plan_type"] == "NARROW_REUSE_FIRST_REWIRE"
    entry_edge = matrix["trace_edges"][3]
    assert entry_edge["surface_id"] == SURFACE_ID
    assert entry_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    flat_edge = matrix["trace_edges"][2]
    assert flat_edge["surface_id"] == "flat_before_opposite_side"
    assert flat_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
