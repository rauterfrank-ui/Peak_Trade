from __future__ import annotations

from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import build_trace_matrix
from scripts.research.bull_bear_state_switch_narrow_trace_assertion_v0 import (
    PLAN_TYPE,
    SURFACE_ID,
    TRACE_ASSERTION_STATE,
    build_narrow_trace_assertion,
)


def test_bull_bear_surface_trace_assertion_records_read_only_edge_from_repo() -> None:
    repo_root = Path.cwd()
    inventory = build_inventory(repo_root)
    matrix = build_trace_matrix(inventory)
    assertion = build_narrow_trace_assertion(repo_root, matrix)

    assert assertion["schema"] == "BullBearStateSwitchNarrowTraceAssertionV1"
    assert assertion["surface_id"] == SURFACE_ID
    assert assertion["plan_type"] == PLAN_TYPE
    assert assertion["trace_assertion_state"] == TRACE_ASSERTION_STATE
    assert assertion["functional_rewire_performed"] is False
    assert matrix["selected_next_rewire_plan"]["selected_surface_id"] == SURFACE_ID
    assert matrix["selected_next_rewire_plan"]["plan_type"] == PLAN_TYPE

    edge = assertion["trace_assertion_edge"]
    assert edge["surface_id"] == SURFACE_ID
    assert edge["functional_rewire_performed"] is False
    assert edge["canonical_trace_markers_found"]
    assert edge["backtest_trace_markers_found"]
    assert edge["runtime_boundary_trace_markers_found"]
    assert (repo_root / edge["canonical_candidate"]).is_file()
    assert (repo_root / edge["backtest_candidate"]).is_file()
    assert (repo_root / edge["runtime_boundary_candidate"]).is_file()


def test_bull_bear_trace_assertion_makes_no_forbidden_claims() -> None:
    repo_root = Path.cwd()
    matrix = build_trace_matrix(build_inventory(repo_root))
    assertion = build_narrow_trace_assertion(repo_root, matrix)

    assert assertion["runtime_authority"] is False
    assert assertion["orders_allowed"] is False
    assert assertion["economic_claim"] is False
    assert assertion["full_canonical_chain_wired_claimed"] is False
    assert assertion["backtest_runtime_decision_parity_pass_claimed"] is False
    assert assertion["system_economic_evidence_admissible"] is False

    forbidden = assertion["forbidden_claims_remain_false"]
    assert forbidden["FULL_CANONICAL_CHAIN_WIRED"] is False
    assert forbidden["BACKTEST_RUNTIME_DECISION_PARITY_PASS"] is False
    assert forbidden["RUNTIME_AUTHORITY"] is False
    assert forbidden["ORDERS_ALLOWED"] is False
    assert forbidden["ECONOMIC_CLAIM"] is False


def test_bull_bear_trace_assertion_does_not_claim_functional_rewire() -> None:
    repo_root = Path.cwd()
    matrix = build_trace_matrix(build_inventory(repo_root))
    assertion = build_narrow_trace_assertion(repo_root, matrix)

    assert assertion["functional_rewire_performed"] is False
    assert assertion["trace_assertion_edge"]["trace_assertion_state"] == TRACE_ASSERTION_STATE
    assert (
        assertion["trace_assertion_edge"]["required_status"]
        == "BULL_BEAR_STATE_SWITCH_WIRED_TO_BACKTEST"
    )
