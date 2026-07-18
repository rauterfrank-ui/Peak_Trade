from __future__ import annotations

import ast
import json
from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import build_trace_matrix
from scripts.research.scope_adverse_exit_and_reversal_preparation_narrow_reuse_first_rewire_v0 import (
    REVERSAL_CONTRACT_TEST_PATH,
    SCOPE_CONTRACT_TEST_PATH,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_scope_adverse_exit_and_reversal_parity_fixtures_v0,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import CanonicalScopeEventType
from trading.master_v2.double_play_entry_exit_policy_v0 import ExitClass
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
)
from trading.master_v2.reversal_preparation_scenario_binding_adapter_v0 import (
    REVERSAL_PREPARATION_SCENARIO_BINDING_ADAPTER_OWNER,
)
from trading.master_v2.scope_event_generator_scenario_binding_adapter_v0 import (
    CANONICAL_SCOPE_EVENT_GENERATOR_OWNER,
    derive_scope_adverse_exit_signal_v0,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT
    / "docs"
    / "research"
    / "adverse_exit_and_reversal_preparation_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
)
INTEGRATED_REPLAY = ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
OFFLINE_REPLAY = ROOT / "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
FLAT_BEFORE_ADAPTER = (
    ROOT / "src/trading/master_v2/flat_before_opposite_side_scenario_binding_adapter_v0.py"
)
SCOPE_ADAPTER = ROOT / "src/trading/master_v2/scope_event_generator_scenario_binding_adapter_v0.py"
REVERSAL_ADAPTER = (
    ROOT / "src/trading/master_v2/reversal_preparation_scenario_binding_adapter_v0.py"
)
ENTRY_EXIT_POLICY = ROOT / "src/trading/master_v2/double_play_entry_exit_policy_v0.py"


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _scope_surface(inventory: dict) -> dict:
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


def test_contract_surface_flags_assessed_not_pass() -> None:
    data = load_contract()
    assert data["adverse_scope_exit_backtest_parity_status"] == "ASSESSED"
    assert data["reversal_preparation_backtest_parity_status"] == "ASSESSED"
    assert data["scope_exit_reversal_backtest_parity_pass"] is False
    assert data["backtest_runtime_decision_parity_pass_claim"] is False
    assert data["full_canonical_chain_wired_claim"] is False
    assert data["system_economic_evidence_admissible"] is False
    assert data["runtime_rewire_admissible"] is False


def test_contract_binds_expected_owners_and_call_paths() -> None:
    data = load_contract()
    assert data["canonical_adverse_exit_owner"] == CANONICAL_SCOPE_EVENT_GENERATOR_OWNER
    assert (
        data["canonical_reversal_preparation_adapter_owner"]
        == REVERSAL_PREPARATION_SCENARIO_BINDING_ADAPTER_OWNER
    )
    assert "mv2_research_wiring_v1" in data["backtest_call_path"]
    assert "offline_double_play_scenario_replay_v0" in data["offline_replay_call_path"]
    assert data["assessment_status"] in {
        "ASSESSED_EXISTING_BACKTEST_PARITY_WIRING_CANDIDATE_FOUND_REVIEW_REQUIRED",
        "FAIL_CLOSED_OWNER_BOUND_BUT_BACKTEST_WIRING_NOT_PROVEN",
        "FAIL_CLOSED_GAP_CONFIRMED_REWIRE_REQUIRED",
    }


def test_narrow_rewire_not_implemented_in_assessment_slice() -> None:
    data = load_contract()
    decision = data["narrow_rewire_decision"]
    assert decision["mode"] == "ASSESSMENT_FIRST_FAIL_CLOSED"
    assert decision["rewire_implemented"] is False
    assert decision["rewire_required"] is False
    assert (
        decision["admissible_next_slice_if_gap_confirmed"]
        == "SCOPE_ADVERSE_EXIT_AND_REVERSAL_PREPARATION_BACKTEST_PARITY_NARROW_REWIRE_V0"
    )


def test_inventory_pins_scope_reversal_backtest_binding_to_parity_contracts() -> None:
    inventory = build_inventory(ROOT)
    surface = _scope_surface(inventory)
    pinned_paths = {hit["path"] for hit in surface["backtest_binding_candidates"][:3]}
    assert SCOPE_CONTRACT_TEST_PATH in pinned_paths
    assert REVERSAL_CONTRACT_TEST_PATH in pinned_paths


def test_trace_matrix_confirms_scope_reversal_offline_parity_bound() -> None:
    inventory = build_inventory(ROOT)
    matrix = build_trace_matrix(inventory)
    scope_edge = next(edge for edge in matrix["trace_edges"] if edge["surface_id"] == SURFACE_ID)
    assert scope_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    assert load_contract()["trace_rewire_bound"] is True


def test_prior_narrow_rewire_binding_reaches_canonical_owners() -> None:
    scope_binding, reversal_decision = evaluate_scope_adverse_exit_and_reversal_parity_fixtures_v0()
    assert "adverse_exit" in scope_binding.scope_event_evidence.matched_conditions
    assert scope_binding.scope_event_evidence.event_type in (
        CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE,
        CanonicalScopeEventType.DOWNSCOPE_CANDIDATE,
        CanonicalScopeEventType.DOWNSCOPE_CONFIRMED,
    )
    assert scope_binding.scope_adverse_exit_signal.triggered is True
    assert reversal_decision.exit_class is ExitClass.REVERSAL_PREPARATION_EXIT

    rewire = build_rewire_binding(ROOT)
    binding = rewire["rewire_binding"]
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False


def test_assessment_documents_integrated_replay_scope_signal_gap_at_assessment_time() -> None:
    data = load_contract()
    findings = data["gap_review_findings"]
    assert findings["integrated_replay_derives_scope_adverse_exit_signal"] is False
    assert findings["integrated_replay_scope_signal_passthrough_gap"] is True


def test_scenario_adapter_derives_scope_adverse_exit_signal_from_evidence() -> None:
    scope_binding, _ = evaluate_scope_adverse_exit_and_reversal_parity_fixtures_v0()
    derived = derive_scope_adverse_exit_signal_v0(scope_binding.scope_event_evidence)
    assert derived.triggered is True
    assert "adverse" in derived.reason_code


def test_offline_replay_routes_through_scope_and_reversal_adapters() -> None:
    offline_source = OFFLINE_REPLAY.read_text(encoding="utf-8")
    flat_before_source = FLAT_BEFORE_ADAPTER.read_text(encoding="utf-8")
    tree = ast.parse(offline_source)
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id
        in {
            "evaluate_scenario_scope_event_v0",
            "evaluate_scenario_flat_before_opposite_side_entry_exit_v0",
        }
    }
    assert "evaluate_scenario_scope_event_v0" in calls
    assert "evaluate_scenario_flat_before_opposite_side_entry_exit_v0" in calls
    assert "evaluate_scenario_reversal_preparation_entry_exit_v0" in flat_before_source
    assert OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER.endswith(
        "offline_double_play_scenario_replay_v0"
    )


def test_entry_exit_policy_preserves_exit_before_reversal_and_reduce_only() -> None:
    data = load_contract()
    precedence = data["decision_precedence_evidence"]
    assert precedence["exit_before_reversal"] is True
    assert precedence["reduce_only"] is True
    assert precedence["position_flip_allowed"] is False
    assert precedence["opposite_side_requires_reconciled_flat"] is True

    policy_source = ENTRY_EXIT_POLICY.read_text(encoding="utf-8")
    assert "MANDATORY_EXIT" in policy_source
    assert "REVERSAL_PREPARATION_EXIT" in policy_source
    assert "reduce_only=True" in policy_source.replace(" ", "")
    assert INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER.endswith(
        "integrated_offline_trading_logic_replay_v1"
    )
    assert SCOPE_ADAPTER.is_file()
    assert REVERSAL_ADAPTER.is_file()
