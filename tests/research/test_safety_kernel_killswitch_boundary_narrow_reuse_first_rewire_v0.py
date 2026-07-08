from __future__ import annotations

from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import build_trace_matrix
from scripts.research.safety_kernel_killswitch_boundary_narrow_reuse_first_rewire_v0 import (
    CHAINED_CONTRACT_TEST_PATH,
    KILLSWITCH_BOUNDARY_BACKTEST_CONTRACT_TEST_PATH,
    KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_CONTRACT_TEST_PATH,
    PLAN_TYPE,
    REUSED_KILLSWITCH_FENCING_OWNER,
    REUSED_RUNTIME_ELIGIBILITY_OWNER,
    SAFETY_KERNEL_OFFLINE_REPLAY_CONTRACT_TEST_PATH,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_safety_kernel_killswitch_boundary_parity_fixtures_v0,
)
from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
    KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE,
)
from trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 import (
    SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE,
)


def test_inventory_pins_chained_safety_kernel_killswitch_backtest_binding_to_parity_contracts() -> (
    None
):
    inventory = build_inventory(Path.cwd())
    surface = next(s for s in inventory["surfaces"] if s["surface_id"] == SURFACE_ID)
    pinned_paths = {hit["path"] for hit in surface["backtest_binding_candidates"][:3]}
    assert SAFETY_KERNEL_OFFLINE_REPLAY_CONTRACT_TEST_PATH in pinned_paths
    assert KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_CONTRACT_TEST_PATH in pinned_paths
    assert KILLSWITCH_BOUNDARY_BACKTEST_CONTRACT_TEST_PATH in pinned_paths
    assert CHAINED_CONTRACT_TEST_PATH in {
        hit["path"] for hit in surface["backtest_binding_candidates"]
    }
    assert surface["backtest_binding_candidates"][0]["matched_terms"] == ["rewire_binding_pin"]


def test_rewire_binding_reuses_canonical_owners_without_parallel_owner() -> None:
    rewire = build_rewire_binding(Path.cwd())
    binding = rewire["rewire_binding"]

    assert rewire["schema"] == "SafetyKernelKillswitchBoundaryNarrowReuseFirstRewireV1"
    assert rewire["surface_id"] == SURFACE_ID
    assert rewire["plan_type"] == PLAN_TYPE
    assert rewire["trace_assertion_source_pr"] == 5012
    assert binding["reused_runtime_eligibility_owner"] == REUSED_RUNTIME_ELIGIBILITY_OWNER
    assert binding["reused_killswitch_fencing_owner"] == REUSED_KILLSWITCH_FENCING_OWNER
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False
    assert binding["capital_risk_sizing_chain_preserved"] is True
    assert binding["kill_switch_boundary_semantics_represented"] is True
    assert binding["rewire_state"] == "REWIRE_BOUND_OFFLINE_PARITY_PATH"


def test_chained_safety_kernel_killswitch_parity_fixture_binds_offline_only() -> None:
    fixture = evaluate_safety_kernel_killswitch_boundary_parity_fixtures_v0()
    assert fixture.safety_binding.binding_applied is True
    assert fixture.safety_binding.safety_boundary_effect == SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE
    assert fixture.safety_binding.safety_boundary_ref
    assert fixture.killswitch_binding.binding_applied is True
    assert fixture.killswitch_binding.killswitch_boundary_effect == (
        KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE
    )
    assert fixture.killswitch_binding.killswitch_boundary_ref
    assert fixture.killswitch_binding.boundary.block_new_entry is True
    assert fixture.killswitch_binding.boundary.emergency_flatten_boundary_only is True


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


def test_trace_matrix_keeps_safety_kernel_killswitch_rewire_bound_in_chain() -> None:
    inventory = build_inventory(Path.cwd())
    matrix = build_trace_matrix(inventory)
    surface_edge = next(edge for edge in matrix["trace_edges"] if edge["surface_id"] == SURFACE_ID)
    assert surface_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    sizing_edge = next(
        edge for edge in matrix["trace_edges"] if edge["surface_id"] == "capital_risk_sizing"
    )
    assert sizing_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
