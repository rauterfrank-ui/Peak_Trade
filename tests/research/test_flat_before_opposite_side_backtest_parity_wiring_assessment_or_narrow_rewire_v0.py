from __future__ import annotations

import ast
import json
from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import build_trace_matrix
from scripts.research.flat_before_opposite_side_narrow_reuse_first_rewire_v0 import (
    CONTRACT_TEST_PATH,
    REUSED_ADAPTER_OWNER,
    REUSED_CANONICAL_OWNER,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_flat_before_opposite_side_parity_fixtures_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    ExistingPositionSide,
    PositionState,
    ReconciliationState,
)
from trading.master_v2.flat_before_opposite_side_scenario_binding_adapter_v0 import (
    FLAT_BEFORE_OPPOSITE_SIDE_SCENARIO_BINDING_ADAPTER_OWNER,
    evaluate_scenario_flat_before_opposite_side_entry_exit_v0,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    evaluate_scenario_matrix_for_side_state_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
)
from trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0 import (
    CANONICAL_ENTRY_EXIT_POLICY_OWNER,
    ScenarioEntryExitPolicyContextV0,
    default_scenario_entry_exit_policy_context_v0,
)
from trading.master_v2.double_play_state import SideState
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _replay_input

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT
    / "docs"
    / "research"
    / "flat_before_opposite_side_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
)
INTEGRATED_REPLAY = ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
OFFLINE_REPLAY = ROOT / "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
ENTRY_EXIT_POLICY = ROOT / "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
FLAT_BEFORE_ADAPTER = (
    ROOT / "src/trading/master_v2/flat_before_opposite_side_scenario_binding_adapter_v0.py"
)
BACKTEST_WIRING = ROOT / "src/backtest/mv2_research_wiring_v1.py"
SCOPE_PASS_ASSERTION = (
    ROOT
    / "docs/research/scope_adverse_exit_reversal_backtest_runtime_decision_parity_pass_assertion_surface_only_v0.json"
)


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _flat_surface(inventory: dict) -> dict:
    return next(s for s in inventory["surfaces"] if s["surface_id"] == SURFACE_ID)


def test_contract_is_authority_neutral_and_no_runtime() -> None:
    data = load_contract()
    assert data["authority_effect"] == "NONE"
    assert data["runtime_effect"] == "NONE"
    assert data["orders_allowed"] is False
    assert data["scheduler_runtime_allowed"] is False
    assert data["live_authorized"] is False
    assert data["shadow_authorized"] is False
    assert data["paper_authorized"] is False
    assert data["testnet_authorized"] is False
    assert data["futures_only"] is True
    assert data["bitcoin_direction_allowed"] is False


def test_contract_surface_flags_wired_and_pass() -> None:
    data = load_contract()
    assert data["flat_before_opposite_side_backtest_parity_status"] == "WIRED"
    assert data["flat_before_opposite_side_backtest_parity_pass"] is True
    assert data["opposite_side_requires_reconciled_flat"] is True
    assert data["venue_flat_alone_sufficient"] is False
    assert data["exit_before_opposite_side"] is True
    assert data["position_flip_allowed"] is False
    assert data["reduce_only_exit_preserved"] is True
    assert data["long_to_short_symmetry_pass"] is True
    assert data["short_to_long_symmetry_pass"] is True
    assert data["backtest_runtime_decision_parity_pass_claim"] is False
    assert data["full_canonical_chain_wired_claim"] is False
    assert data["system_economic_evidence_admissible"] is False
    assert data["runtime_rewire_admissible"] is False


def test_contract_binds_expected_owners_and_call_paths() -> None:
    data = load_contract()
    assert (
        data["canonical_integrated_replay_owner"] == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER
    )
    assert data["canonical_entry_exit_policy_owner"] == CANONICAL_ENTRY_EXIT_POLICY_OWNER
    assert (
        data["canonical_flat_before_adapter_owner"]
        == FLAT_BEFORE_OPPOSITE_SIDE_SCENARIO_BINDING_ADAPTER_OWNER
    )
    assert "mv2_research_wiring_v1" in data["backtest_call_path"]
    assert "evaluate_double_play_entry_exit_policy_v0" in data["backtest_call_path"]
    assert "offline_double_play_scenario_replay_v0" in data["offline_replay_call_path"]
    assert data["assessment_status"] == "WIRED_EXISTING_BACKTEST_PARITY_CHAIN_COMPLETE"


def test_narrow_rewire_not_required_in_wired_assessment_slice() -> None:
    data = load_contract()
    decision = data["narrow_rewire_decision"]
    assert decision["mode"] == "ASSERTION_SURFACE_ONLY"
    assert decision["rewire_implemented"] is False
    assert decision["rewire_required"] is False
    assert decision["admissible_next_slice_if_gap_confirmed"] == "NONE"


def test_inventory_pins_flat_before_backtest_binding_to_parity_contract() -> None:
    inventory = build_inventory(ROOT)
    surface = _flat_surface(inventory)
    pinned_paths = {hit["path"] for hit in surface["backtest_binding_candidates"][:3]}
    assert CONTRACT_TEST_PATH in pinned_paths


def test_trace_matrix_confirms_flat_before_offline_parity_bound() -> None:
    inventory = build_inventory(ROOT)
    matrix = build_trace_matrix(inventory)
    flat_edge = next(edge for edge in matrix["trace_edges"] if edge["surface_id"] == SURFACE_ID)
    assert flat_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    assert load_contract()["trace_rewire_bound"] is True


def test_prior_narrow_rewire_binding_reaches_canonical_owners() -> None:
    decision = evaluate_flat_before_opposite_side_parity_fixtures_v0()
    assert decision.decision_outcome is not DecisionOutcome.ENTER_SHORT
    assert decision.position_flip_allowed is False

    rewire = build_rewire_binding(ROOT)
    binding = rewire["rewire_binding"]
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False
    assert binding["reused_canonical_owner"] == REUSED_CANONICAL_OWNER
    assert binding["reused_adapter_owner"] == REUSED_ADAPTER_OWNER


def test_offline_replay_routes_through_flat_before_adapter() -> None:
    offline_source = OFFLINE_REPLAY.read_text(encoding="utf-8")
    tree = ast.parse(offline_source)
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "evaluate_scenario_flat_before_opposite_side_entry_exit_v0"
    }
    assert "evaluate_scenario_flat_before_opposite_side_entry_exit_v0" in calls
    assert OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER.endswith(
        "offline_double_play_scenario_replay_v0"
    )


def test_integrated_replay_and_backtest_call_canonical_policy() -> None:
    replay_source = INTEGRATED_REPLAY.read_text(encoding="utf-8")
    backtest_source = BACKTEST_WIRING.read_text(encoding="utf-8")
    policy_source = ENTRY_EXIT_POLICY.read_text(encoding="utf-8")

    assert "evaluate_double_play_entry_exit_policy_v0" in replay_source
    assert "run_integrated_offline_trading_logic_replay_v1" in backtest_source
    assert "_effective_flat" in policy_source
    assert "position_flip_allowed=False" in policy_source.replace(" ", "")
    assert INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER.endswith(
        "integrated_offline_trading_logic_replay_v1"
    )
    assert FLAT_BEFORE_ADAPTER.is_file()


def test_decision_precedence_flags_and_gap_review() -> None:
    data = load_contract()
    precedence = data["decision_precedence_evidence"]
    assert precedence["opposite_side_requires_reconciled_flat"] is True
    assert precedence["venue_flat_alone_sufficient"] is False
    assert precedence["exit_before_opposite_side"] is True
    assert precedence["position_flip_allowed"] is False
    assert precedence["reduce_only_exit_preserved"] is True

    findings = data["gap_review_findings"]
    assert findings["bypass_path_reproducible"] is False
    assert findings["integrated_replay_calls_canonical_entry_exit_policy"] is True
    assert findings["scenario_replay_flat_before_adapter_bound"] is True
    assert findings["venue_flat_without_reconciled_state_blocked_confirmed"] is True


def test_scenario_negative_paths_block_opposite_entry() -> None:
    short_matrix = evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.SHORT_ARMED,
        instrument_id="SYNTHETIC:ETH-USDT-PERP",
        trading_epoch=54,
        context_reference="flat-before-assessment-v0",
    )
    blocked = evaluate_scenario_flat_before_opposite_side_entry_exit_v0(
        instrument_id="SYNTHETIC:ETH-USDT-PERP",
        trading_epoch=54,
        context_reference="flat-before-assessment-v0",
        composition_result=short_matrix,
        side_state=SideState.LONG_ACTIVE,
        policy_context=default_scenario_entry_exit_policy_context_v0(),
    )
    assert blocked.decision_outcome is not DecisionOutcome.ENTER_SHORT
    assert blocked.position_flip_allowed is False

    venue_flat_unresolved = evaluate_scenario_flat_before_opposite_side_entry_exit_v0(
        instrument_id="SYNTHETIC:ETH-USDT-PERP",
        trading_epoch=54,
        context_reference="flat-before-assessment-v0",
        composition_result=short_matrix,
        side_state=SideState.SHORT_ARMED,
        policy_context=ScenarioEntryExitPolicyContextV0(
            position_state=PositionState.RECONCILIATION_REQUIRED,
            reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED,
            existing_position_side=ExistingPositionSide.NONE,
            venue_flat=True,
        ),
    )
    assert venue_flat_unresolved.decision_outcome is DecisionOutcome.RECONCILE_ONLY


def test_integrated_replay_blocks_unreconciled_and_open_position_opposite_entry() -> None:
    unreconciled = run_integrated_offline_trading_logic_replay_v1(
        _replay_input(
            venue_flat=True,
            reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED,
            position_state=PositionState.RECONCILIATION_REQUIRED,
        )
    )
    assert unreconciled.evidence.decision_outcome == DecisionOutcome.RECONCILE_ONLY.value

    open_position = run_integrated_offline_trading_logic_replay_v1(
        _replay_input(
            position_state=PositionState.OPEN_FULL,
            existing_position_side=ExistingPositionSide.LONG,
            side_state=SideState.LONG_ACTIVE,
            venue_flat=False,
        )
    )
    assert open_position.evidence.decision_outcome != DecisionOutcome.ENTER_SHORT.value


def test_scope_pass_assertion_is_prior_surface_reference() -> None:
    data = load_contract()
    scope_pass = json.loads(SCOPE_PASS_ASSERTION.read_text(encoding="utf-8"))
    assert (
        scope_pass["next_parity_surface"]
        == "FLAT_BEFORE_OPPOSITE_SIDE_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0"
    )
    assert data["scope_pass_assertion_source_pr"] == 5062
    assert data["source_manifest_verify_rc"] == 0
