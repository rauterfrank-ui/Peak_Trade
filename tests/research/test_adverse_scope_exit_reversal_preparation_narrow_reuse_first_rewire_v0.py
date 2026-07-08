from __future__ import annotations

from pathlib import Path

from scripts.research.adverse_scope_exit_reversal_preparation_narrow_reuse_first_rewire_v0 import (
    CHAINED_CONTRACT_TEST_PATH,
    PLAN_TYPE,
    REUSED_SCOPE_CANONICAL_OWNER,
    REVERSAL_CONTRACT_TEST_PATH,
    SCOPE_CONTRACT_TEST_PATH,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_adverse_scope_exit_reversal_preparation_parity_fixtures_v0,
)
from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import build_trace_matrix
from trading.master_v2.deterministic_scope_event_generator_v1 import CanonicalScopeEventType
from trading.master_v2.double_play_entry_exit_policy_v0 import ExitClass


def test_inventory_pins_chained_scope_reversal_backtest_binding_to_parity_contracts() -> None:
    inventory = build_inventory(Path.cwd())
    scope_surface = next(
        s
        for s in inventory["surfaces"]
        if s["surface_id"] == "scope_adverse_exit_and_reversal_preparation"
    )
    pinned_paths = {hit["path"] for hit in scope_surface["backtest_binding_candidates"][:3]}
    assert SCOPE_CONTRACT_TEST_PATH in pinned_paths
    assert REVERSAL_CONTRACT_TEST_PATH in pinned_paths
    assert CHAINED_CONTRACT_TEST_PATH in pinned_paths
    assert scope_surface["backtest_binding_candidates"][0]["matched_terms"] == [
        "rewire_binding_pin"
    ]


def test_rewire_binding_reuses_canonical_owners_without_parallel_owner() -> None:
    rewire = build_rewire_binding(Path.cwd())
    binding = rewire["rewire_binding"]

    assert rewire["schema"] == "AdverseScopeExitReversalPreparationNarrowReuseFirstRewireV1"
    assert rewire["surface_id"] == SURFACE_ID
    assert rewire["plan_type"] == PLAN_TYPE
    assert rewire["trace_assertion_source_pr"] == 5009
    assert binding["reused_scope_canonical_owner"] == REUSED_SCOPE_CANONICAL_OWNER
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False
    assert binding["scope_signal_wired_into_reversal_preparation"] is True
    assert binding["rewire_state"] == "REWIRE_BOUND_OFFLINE_PARITY_PATH"


def test_chained_scope_and_reversal_parity_fixtures_reach_canonical_owners() -> None:
    scope_binding, reversal_decision = (
        evaluate_adverse_scope_exit_reversal_preparation_parity_fixtures_v0()
    )
    assert (
        scope_binding.scope_event_evidence.event_type
        is CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE
    )
    assert scope_binding.scope_adverse_exit_signal.triggered is True
    assert scope_binding.scope_event_ref
    assert reversal_decision.exit_class in (
        ExitClass.REVERSAL_PREPARATION_EXIT,
        ExitClass.ADVERSE_SCOPE_EXIT,
    )
    assert reversal_decision.policy_decision_id


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


def test_trace_matrix_chain_bound_after_adverse_scope_exit_rewire_bound() -> None:
    inventory = build_inventory(Path.cwd())
    matrix = build_trace_matrix(inventory)
    assert matrix["selected_next_rewire_plan"]["selected_surface_id"] == "NONE"
    assert (
        matrix["selected_next_rewire_plan"]["plan_type"] == "CHAIN_BOUND_AWAITING_FULL_PARITY_PROOF"
    )
    assert matrix["next_unbound_node"] == "NONE"
    flat_edge = matrix["trace_edges"][2]
    assert flat_edge["surface_id"] == "flat_before_opposite_side"
    assert flat_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    scope_edge = matrix["trace_edges"][1]
    assert scope_edge["surface_id"] == "scope_adverse_exit_and_reversal_preparation"
    assert scope_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
