from __future__ import annotations

from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import build_trace_matrix
from scripts.research.bull_bear_state_switch_narrow_reuse_first_rewire_v0 import (
    CONTRACT_TEST_PATH,
    PLAN_TYPE,
    REUSED_CANONICAL_OWNER,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_bull_bear_parity_fixtures_v0,
)
from trading.master_v2.double_play_state import SideState


def _bull_bear_surface(inventory: dict) -> dict:
    return next(s for s in inventory["surfaces"] if s["surface_id"] == SURFACE_ID)


def test_inventory_pins_bull_bear_backtest_binding_to_parity_contract() -> None:
    inventory = build_inventory(Path.cwd())
    surface = _bull_bear_surface(inventory)
    assert surface["backtest_binding_candidates"][0]["path"] == CONTRACT_TEST_PATH
    assert surface["backtest_binding_candidates"][0]["matched_terms"] == ["rewire_binding_pin"]


def test_rewire_binding_reuses_canonical_owner_without_parallel_owner() -> None:
    rewire = build_rewire_binding(Path.cwd())
    binding = rewire["rewire_binding"]

    assert rewire["schema"] == "BullBearStateSwitchNarrowReuseFirstRewireV1"
    assert rewire["plan_type"] == PLAN_TYPE
    assert rewire["trace_assertion_source_pr"] == 5006
    assert binding["reused_canonical_owner"] == REUSED_CANONICAL_OWNER
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False
    assert binding["rewire_state"] == "REWIRE_BOUND_OFFLINE_PARITY_PATH"


def test_bull_bear_parity_fixtures_reach_canonical_owner_symmetrically() -> None:
    bull_binding, bear_binding = evaluate_bull_bear_parity_fixtures_v0()
    assert bull_binding.side_state_after == SideState.LONG_ARMED
    assert bear_binding.side_state_after == SideState.SHORT_ARMED
    assert bull_binding.state_switch_ref
    assert bear_binding.state_switch_ref


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


def test_trace_matrix_bull_bear_marked_rewire_bound_after_inventory_pin() -> None:
    inventory = build_inventory(Path.cwd())
    matrix = build_trace_matrix(inventory)
    edge = matrix["trace_edges"][0]
    assert edge["surface_id"] == "bull_bear_state_switch"
    assert edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    assert edge["backtest_candidate"] == CONTRACT_TEST_PATH
