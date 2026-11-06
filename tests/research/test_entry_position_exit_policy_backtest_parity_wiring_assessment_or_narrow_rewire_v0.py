from __future__ import annotations

import ast
import json
from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import build_trace_matrix
from scripts.research.entry_position_exit_policy_narrow_reuse_first_rewire_v0 import (
    CHAINED_CONTRACT_TEST_PATH,
    ENTRY_EXIT_CONTRACT_TEST_PATH,
    FLAT_BEFORE_CONTRACT_TEST_PATH,
    REUSED_CANONICAL_OWNER,
    REUSED_ENTRY_EXIT_ADAPTER_OWNER,
    REUSED_FLAT_BEFORE_ADAPTER_OWNER,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_entry_position_exit_policy_parity_fixtures_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome, ExitClass
from trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0 import (
    CANONICAL_ENTRY_EXIT_POLICY_OWNER,
    DOUBLE_PLAY_ENTRY_EXIT_SCENARIO_BINDING_ADAPTER_OWNER,
)
from trading.master_v2.flat_before_opposite_side_scenario_binding_adapter_v0 import (
    FLAT_BEFORE_OPPOSITE_SIDE_SCENARIO_BINDING_ADAPTER_OWNER,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _replay_input

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT
    / "docs"
    / "research"
    / "entry_position_exit_policy_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
)
INTEGRATED_REPLAY = ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
OFFLINE_REPLAY = ROOT / "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
ENTRY_EXIT_POLICY = ROOT / "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
ENTRY_EXIT_ADAPTER = (
    ROOT / "src/trading/master_v2/double_play_entry_exit_scenario_binding_adapter_v0.py"
)
FLAT_BEFORE_ADAPTER = (
    ROOT / "src/trading/master_v2/flat_before_opposite_side_scenario_binding_adapter_v0.py"
)
BACKTEST_WIRING = ROOT / "src/backtest/mv2_research_wiring_v1.py"
FLAT_BEFORE_CONTRACT = (
    ROOT
    / "docs/research/flat_before_opposite_side_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
)
ADVERSE_EXIT_CONTRACT = (
    ROOT
    / "docs/research/adverse_exit_and_reversal_preparation_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
)
DOUBLE_PLAY_COMPOSITION_CONTRACT = (
    ROOT
    / "docs/research/double_play_composition_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
)


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _entry_position_exit_surface(inventory: dict) -> dict:
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


def test_contract_surface_flags_assessed_and_pass() -> None:
    data = load_contract()
    assert data["entry_policy_backtest_parity_status"] == "ASSESSED"
    assert data["entry_policy_backtest_parity_pass"] is True
    assert data["position_management_backtest_parity_status"] == "ASSESSED"
    assert data["position_management_backtest_parity_pass"] is True
    assert data["exit_policy_backtest_parity_status"] == "ASSESSED"
    assert data["exit_policy_backtest_parity_pass"] is True
    assert data["partial_fill_semantics_status"] == "ASSESSED"
    assert data["reduce_only_invariant_status"] == "ASSESSED"
    assert data["position_flip_forbidden_status"] == "ASSESSED"
    assert data["narrow_rewire_required"] is False
    assert data["narrow_rewire_implemented"] is False
    assert data["narrow_rewire_performed"] is False
    assert data["canonical_owner_identified"] is True
    assert data["reuse_before_new_checked"] is True
    assert data["full_canonical_chain_wired"] is False
    assert data["backtest_runtime_decision_parity_pass"] is False
    assert data["system_economic_evidence_admissible"] is False
    assert data["runtime_rewire_admissible"] is False


def test_contract_binds_expected_owners_and_call_paths() -> None:
    data = load_contract()
    assert data["canonical_entry_exit_policy_owner"] == CANONICAL_ENTRY_EXIT_POLICY_OWNER
    assert (
        data["canonical_entry_exit_scenario_binding_adapter_owner"]
        == DOUBLE_PLAY_ENTRY_EXIT_SCENARIO_BINDING_ADAPTER_OWNER
    )
    assert (
        data["canonical_flat_before_adapter_owner"]
        == FLAT_BEFORE_OPPOSITE_SIDE_SCENARIO_BINDING_ADAPTER_OWNER
    )
    assert (
        data["canonical_integrated_replay_owner"] == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER
    )
    assert "mv2_research_wiring_v1" in data["backtest_call_path"]
    assert "evaluate_double_play_entry_exit_policy_v0" in data["backtest_call_path"]
    assert "evaluate_scenario_entry_exit_policy_v0" in data["offline_replay_call_path"]
    assert data["assessment_status"] == "WIRED_EXISTING_BACKTEST_PARITY_CHAIN_COMPLETE"


def test_narrow_rewire_not_required_in_wired_assessment_slice() -> None:
    data = load_contract()
    decision = data["narrow_rewire_decision"]
    assert decision["mode"] == "ASSERTION_SURFACE_ONLY"
    assert decision["rewire_implemented"] is False
    assert decision["rewire_required"] is False
    assert decision["admissible_next_slice_if_gap_confirmed"] == "NONE"


def test_inventory_pins_entry_position_exit_backtest_binding_to_parity_contract() -> None:
    inventory = build_inventory(ROOT)
    surface = _entry_position_exit_surface(inventory)
    pinned_paths = {hit["path"] for hit in surface["backtest_binding_candidates"][:5]}
    assert ENTRY_EXIT_CONTRACT_TEST_PATH in pinned_paths
    assert FLAT_BEFORE_CONTRACT_TEST_PATH in pinned_paths
    assert CHAINED_CONTRACT_TEST_PATH in pinned_paths


def test_trace_matrix_confirms_entry_position_exit_offline_parity_bound() -> None:
    inventory = build_inventory(ROOT)
    matrix = build_trace_matrix(inventory)
    edge = next(edge for edge in matrix["trace_edges"] if edge["surface_id"] == SURFACE_ID)
    assert edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    assert load_contract()["trace_rewire_bound"] is True


def test_prior_narrow_rewire_binding_reaches_canonical_owners() -> None:
    decision = evaluate_entry_position_exit_policy_parity_fixtures_v0()
    assert decision.decision_outcome not in (
        DecisionOutcome.ENTER_LONG,
        DecisionOutcome.ENTER_SHORT,
    )
    assert decision.position_flip_allowed is False

    rewire = build_rewire_binding(ROOT)
    binding = rewire["rewire_binding"]
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False
    assert binding["reused_canonical_owner"] == REUSED_CANONICAL_OWNER
    assert binding["reused_entry_exit_adapter_owner"] == REUSED_ENTRY_EXIT_ADAPTER_OWNER
    assert binding["reused_flat_before_adapter_owner"] == REUSED_FLAT_BEFORE_ADAPTER_OWNER


def test_integrated_replay_and_backtest_call_canonical_entry_exit_policy() -> None:
    replay_source = INTEGRATED_REPLAY.read_text(encoding="utf-8")
    backtest_source = BACKTEST_WIRING.read_text(encoding="utf-8")
    policy_source = ENTRY_EXIT_POLICY.read_text(encoding="utf-8")

    assert "evaluate_double_play_entry_exit_policy_v0" in replay_source
    assert "run_integrated_offline_trading_logic_replay_v1" in backtest_source
    assert "_entry_preconditions_met" in policy_source
    assert "partial_fill_or_unknown_blocks_entry" in policy_source
    assert "EXISTING_POSITION" in policy_source
    assert ExitClass.ADVERSE_SCOPE_EXIT.value in policy_source
    assert ExitClass.PROFIT_PROTECTION_EXIT.value in policy_source
    assert ExitClass.TIME_EXIT.value in policy_source
    assert ExitClass.STRATEGY_INVALIDATION_EXIT.value in policy_source
    assert ExitClass.REVERSAL_PREPARATION_EXIT.value in policy_source


def test_offline_replay_routes_through_entry_exit_and_flat_before_adapters() -> None:
    offline_source = OFFLINE_REPLAY.read_text(encoding="utf-8")
    adapter_source = ENTRY_EXIT_ADAPTER.read_text(encoding="utf-8")
    flat_source = FLAT_BEFORE_ADAPTER.read_text(encoding="utf-8")
    tree = ast.parse(offline_source)
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "evaluate_scenario_flat_before_opposite_side_entry_exit_v0"
    }
    assert "evaluate_scenario_flat_before_opposite_side_entry_exit_v0" in calls
    assert "evaluate_double_play_entry_exit_policy_v0" in adapter_source
    assert "evaluate_scenario_reversal_preparation_entry_exit_v0" in flat_source
    assert OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER.endswith(
        "offline_double_play_scenario_replay_v0"
    )


def test_no_separate_backtest_entry_or_exit_owner() -> None:
    backtest_source = BACKTEST_WIRING.read_text(encoding="utf-8")
    assert "evaluate_double_play_entry_exit_policy_v0" not in backtest_source
    assert "BacktestEntryPolicy" not in backtest_source
    assert "BacktestExitPolicy" not in backtest_source


def test_exit_invariants_reduce_only_and_position_flip_forbidden() -> None:
    policy_source = ENTRY_EXIT_POLICY.read_text(encoding="utf-8")
    assert "reduce_only=True" in policy_source
    assert "position_flip_allowed=False" in policy_source
    assert "_QUANTITY_STATUS_NOT_BOUND" in policy_source


def test_integrated_replay_consumes_entry_exit_policy_authority_neutral() -> None:
    result = run_integrated_offline_trading_logic_replay_v1(_replay_input())
    decision = result.intermediate.entry_exit_decision
    assert decision.authority_effect == "NONE"
    assert decision.runtime_effect == "NONE"
    assert decision.order_effect == "NONE"
    assert decision.quantity_status == "NOT_BOUND"


def test_gap_review_and_source_evidence_flags() -> None:
    data = load_contract()
    findings = data["gap_review_findings"]
    assert findings["bypass_path_reproducible"] is False
    assert findings["separate_backtest_entry_logic_reproducible"] is False
    assert findings["separate_backtest_exit_logic_reproducible"] is False
    assert findings["integrated_replay_calls_canonical_entry_exit_policy"] is True
    assert findings["scenario_replay_entry_exit_adapter_bound"] is True
    assert findings["scenario_replay_flat_before_adapter_bound"] is True
    assert data["source_evidence_referenced"] is False
    assert data["source_evidence_not_referenced"] is True
    assert data["source_manifest_verify_rc"] == "NOT_APPLICABLE_NO_SOURCE_EVIDENCE_REFERENCED"
    assert FLAT_BEFORE_CONTRACT.is_file()
    assert ADVERSE_EXIT_CONTRACT.is_file()
    assert DOUBLE_PLAY_COMPOSITION_CONTRACT.is_file()
    assert (
        "docs/research/flat_before_opposite_side_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
        in data["source_evidence_contract_refs"]
    )
