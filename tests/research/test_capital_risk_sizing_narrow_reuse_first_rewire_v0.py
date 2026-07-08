from __future__ import annotations

from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import build_trace_matrix
from scripts.research.capital_risk_sizing_narrow_reuse_first_rewire_v0 import (
    BOUNDARY_BACKTEST_CONTRACT_TEST_PATH,
    CHAINED_CONTRACT_TEST_PATH,
    OFFLINE_REPLAY_CONTRACT_TEST_PATH,
    PLAN_TYPE,
    REUSED_CANONICAL_OWNER,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_capital_risk_sizing_parity_fixtures_v0,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    RISK_SIZING_EFFECT_BOUND_OFFLINE,
)


def test_inventory_pins_chained_capital_risk_sizing_backtest_binding_to_parity_contracts() -> None:
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

    assert rewire["schema"] == "CapitalRiskSizingNarrowReuseFirstRewireV1"
    assert rewire["surface_id"] == SURFACE_ID
    assert rewire["plan_type"] == PLAN_TYPE
    assert rewire["trace_assertion_source_pr"] == 5011
    assert binding["reused_canonical_owner"] == REUSED_CANONICAL_OWNER
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False
    assert binding["entry_exit_policy_chain_preserved"] is True
    assert binding["rewire_state"] == "REWIRE_BOUND_OFFLINE_PARITY_PATH"


def test_chained_capital_risk_sizing_parity_fixture_binds_offline_only() -> None:
    binding = evaluate_capital_risk_sizing_parity_fixtures_v0()
    assert binding.binding_applied is True
    assert binding.risk_sizing_effect == RISK_SIZING_EFFECT_BOUND_OFFLINE
    assert binding.quantity_provenance_ref
    assert binding.risk_sizing_ref


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


def test_trace_matrix_keeps_capital_risk_sizing_rewire_bound_in_chain() -> None:
    inventory = build_inventory(Path.cwd())
    matrix = build_trace_matrix(inventory)
    sizing_edge = next(edge for edge in matrix["trace_edges"] if edge["surface_id"] == SURFACE_ID)
    assert sizing_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    entry_edge = next(
        edge for edge in matrix["trace_edges"] if edge["surface_id"] == "entry_position_exit_policy"
    )
    assert entry_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
