from __future__ import annotations

from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import build_trace_matrix
from scripts.research.reconciliation_unknown_outcome_narrow_reuse_first_rewire_v0 import (
    BOUNDARY_BACKTEST_CONTRACT_TEST_PATH,
    CHAINED_CONTRACT_TEST_PATH,
    OFFLINE_REPLAY_CONTRACT_TEST_PATH,
    PLAN_TYPE,
    REUSED_ENTRY_EXIT_POLICY_OWNER,
    REUSED_RUNTIME_STATE_RECONCILIATION_OWNER,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_reconciliation_unknown_outcome_parity_fixtures_v0,
)
from trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0 import (
    RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE,
)


def test_inventory_pins_chained_reconciliation_backtest_binding_to_parity_contracts() -> None:
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

    assert rewire["schema"] == "ReconciliationUnknownOutcomeNarrowReuseFirstRewireV1"
    assert rewire["surface_id"] == SURFACE_ID
    assert rewire["plan_type"] == PLAN_TYPE
    assert rewire["trace_assertion_source_pr"] == 5013
    assert binding["reused_runtime_state_reconciliation_owner"] == (
        REUSED_RUNTIME_STATE_RECONCILIATION_OWNER
    )
    assert binding["reused_entry_exit_policy_owner"] == REUSED_ENTRY_EXIT_POLICY_OWNER
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False
    assert binding["safety_kernel_killswitch_chain_preserved"] is True
    assert binding["submission_unknown_semantics_represented"] is True
    assert binding["unknown_outcome_never_auto_resubmits"] is True
    assert binding["rewire_state"] == "REWIRE_BOUND_OFFLINE_PARITY_PATH"


def test_chained_reconciliation_parity_fixture_binds_offline_only() -> None:
    binding = evaluate_reconciliation_unknown_outcome_parity_fixtures_v0()
    assert binding.binding_applied is True
    assert binding.reconciliation_unknown_outcome_effect == (
        RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE
    )
    assert binding.reconciliation_unknown_outcome_ref
    assert binding.boundary.submission_unknown_blocks_new_exposure is True
    assert binding.boundary.unknown_outcome_never_auto_resubmits is True
    assert binding.boundary.no_auto_resubmit is True


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


def test_trace_matrix_selects_promotion_gate_after_reconciliation_rewire_bound() -> None:
    inventory = build_inventory(Path.cwd())
    matrix = build_trace_matrix(inventory)
    assert matrix["selected_next_rewire_plan"]["selected_surface_id"] == "promotion_gate_boundary"
    assert matrix["selected_next_rewire_plan"]["plan_type"] == "NARROW_TRACE_ASSERTION_FIRST"
    reconciliation_edge = next(
        edge for edge in matrix["trace_edges"] if edge["surface_id"] == SURFACE_ID
    )
    assert reconciliation_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    safety_edge = next(
        edge
        for edge in matrix["trace_edges"]
        if edge["surface_id"] == "safety_kernel_and_killswitch_boundary"
    )
    assert safety_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
