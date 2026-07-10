from __future__ import annotations

import ast
import json
from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import build_trace_matrix
from scripts.research.bull_bear_state_switch_narrow_reuse_first_rewire_v0 import (
    build_rewire_binding,
    evaluate_bull_bear_parity_fixtures_v0,
)
from src.research.owner_bindings.bull_bear_state_switch_owner_binding_v0 import (
    build_bull_bear_state_switch_owner_binding_v0,
)
from trading.master_v2.bull_bear_state_switch_scenario_binding_adapter_v0 import (
    CANONICAL_STATE_SWITCH_OWNER,
    mirrored_side_states_parity_ok_v0,
    state_switch_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.double_play_state import ScopeEvent, SideState
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    canonical_owner_refs_v0,
    evaluate_scenario_state_switch_for_fixture_v0,
    extract_state_switch_parity_envelope_v0,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/research/bull_bear_state_switch_backtest_parity_narrow_rewire_v0.json"
ASSESSMENT_CONTRACT = (
    ROOT
    / "docs/research/bull_bear_state_switch_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
)
BACKTEST_CONSUMER = ROOT / "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
ADAPTER = ROOT / "src/trading/master_v2/bull_bear_state_switch_scenario_binding_adapter_v0.py"
PARITY_CONTRACT = (
    ROOT
    / "tests/trading/master_v2/test_bull_bear_state_switch_scenario_replay_binding_parity_rewire_contract_v0.py"
)


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _bull_bear_surface(inventory: dict) -> dict:
    return next(s for s in inventory["surfaces"] if s["surface_id"] == "bull_bear_state_switch")


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


def test_contract_classifies_review_no_rewire_required() -> None:
    data = load_contract()
    decision = data["narrow_rewire_decision"]
    assert decision["classification"] == "REVIEW_NO_REWIRE_REQUIRED"
    assert decision["rewire_implemented"] is False
    assert data["gap_confirmed"] is False
    assert (
        data["verdict"]
        == "PASS_BULL_BEAR_STATE_SWITCH_BACKTEST_PARITY_REVIEW_NO_REWIRE_REQUIRED_V0"
    )
    findings = data["gap_review_findings"]
    assert all(value is False for value in findings.values())


def test_contract_does_not_claim_system_economic_or_runtime_parity() -> None:
    data = load_contract()
    assert data["system_economic_evidence_admissible"] is False
    assert data["runtime_rewire_admissible"] is False
    assert data["economic_evaluation_authorized"] is False
    assert data["full_canonical_chain_wired_claim"] is False
    assert data["backtest_runtime_decision_parity_pass_claim"] is False


def test_contract_preserves_assessment_backtest_reference_inventory() -> None:
    data = load_contract()
    assessment = json.loads(ASSESSMENT_CONTRACT.read_text(encoding="utf-8"))
    assert data["backtest_direct_reference_count"] == 20
    assert data["backtest_direct_references"] == assessment["backtest_direct_references"]
    assert data["assessment_source_pr"] == 5057
    assert data["source_evidence_manifest_verify_rc"] == 0


def test_owner_binding_matches_canonical_owner_without_parallel_owner() -> None:
    binding = build_bull_bear_state_switch_owner_binding_v0()
    contract = binding.as_contract()
    data = load_contract()

    assert contract["canonical_owner"] == data["canonical_owner"]
    assert contract["reuse_decision"] == "REUSE_WITH_NARROW_ADAPTER"
    assert "NO_PARALLEL_STATE_SWITCH_OWNER" in contract["required_parity_assertions"]


def test_canonical_owner_refs_and_adapter_reuse() -> None:
    refs = canonical_owner_refs_v0()
    data = load_contract()

    assert refs["state_switch"] == CANONICAL_STATE_SWITCH_OWNER
    assert refs["state_switch"] == data["canonical_owner_module"]
    assert (ROOT / data["canonical_adapter_path"]).is_file()
    assert (ROOT / data["backtest_consumer_path"]).is_file()
    assert (ROOT / data["parity_contract_path"]).is_file()


def test_backtest_consumer_invokes_adapter_not_bypass() -> None:
    replay_text = BACKTEST_CONSUMER.read_text(encoding="utf-8")
    adapter_text = ADAPTER.read_text(encoding="utf-8")

    assert "evaluate_scenario_state_switch_v0" in replay_text
    assert "def _bull_layer_state" not in replay_text
    assert "def _bear_layer_state" not in replay_text
    assert "transition_state" in adapter_text
    assert "def transition_state" not in adapter_text


def test_adapter_calls_canonical_transition_state_only() -> None:
    tree = ast.parse(ADAPTER.read_text(encoding="utf-8"))
    transition_calls = 0
    local_transition_defs = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "transition_state":
                transition_calls += 1
        if isinstance(node, ast.FunctionDef) and node.name == "transition_state":
            local_transition_defs += 1

    assert transition_calls >= 1
    assert local_transition_defs == 0


def test_mirrored_bull_bear_behavior_through_canonical_owner() -> None:
    bull_binding, bear_binding = evaluate_bull_bear_parity_fixtures_v0()
    assert bull_binding.side_state_after == SideState.LONG_ARMED
    assert bear_binding.side_state_after == SideState.SHORT_ARMED
    assert mirrored_side_states_parity_ok_v0(
        bull_binding.side_state_after,
        bear_binding.side_state_after,
    )
    for binding in (bull_binding, bear_binding):
        env = extract_state_switch_parity_envelope_v0(binding)
        assert env.state_switch_ref
        assert state_switch_binding_non_authority_boundary_ok_v0(binding)


def test_harness_fixture_path_reaches_canonical_owner() -> None:
    binding = evaluate_scenario_state_switch_for_fixture_v0(
        side_state=SideState.NEUTRAL_OBSERVE,
        scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
        instrument_id="SYNTH_FUTURES_BTCUSDT_PERP",
        trading_epoch=48,
        context_reference="narrow-rewire-review-v0",
    )
    assert binding.side_state_after == SideState.LONG_ARMED
    assert binding.state_switch_ref
    assert state_switch_binding_non_authority_boundary_ok_v0(binding)


def test_prior_narrow_rewire_binding_remains_functional_without_new_parallel_owner() -> None:
    rewire = build_rewire_binding(ROOT)
    binding = rewire["rewire_binding"]
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False
    assert binding["reused_canonical_owner"] == CANONICAL_STATE_SWITCH_OWNER


def test_inventory_and_trace_matrix_mark_bull_bear_rewire_bound_negative_bypass_guard() -> None:
    inventory = build_inventory(ROOT)
    surface = _bull_bear_surface(inventory)
    matrix = build_trace_matrix(inventory)
    data = load_contract()
    edge = next(e for e in matrix["trace_edges"] if e["surface_id"] == "bull_bear_state_switch")

    assert edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    assert data["trace_rewire_bound"] is True
    assert surface["backtest_binding_candidates"][0]["path"] == data["parity_contract_path"]
    assert PARITY_CONTRACT.is_file()


def test_legacy_duplicate_state_switch_logic_absent_negative() -> None:
    replay_text = BACKTEST_CONSUMER.read_text(encoding="utf-8")
    forbidden_tokens = (
        "def transition_state",
        "def _derive_active_side",
        "class TransitionDecision",
    )
    for token in forbidden_tokens:
        assert token not in replay_text
