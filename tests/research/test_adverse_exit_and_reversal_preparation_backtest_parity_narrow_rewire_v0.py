from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path

from scripts.research.adverse_exit_and_reversal_preparation_backtest_parity_narrow_rewire_v0 import (
    BACKTEST_CONSUMER,
    INTEGRATED_REPLAY_PATH,
    REVERSAL_ADAPTER_PATH,
    SCOPE_ADAPTER_PATH,
    build_rewire_binding,
    evaluate_adverse_exit_integrated_backtest_parity_fixtures_v0,
    evaluate_reversal_preparation_integrated_backtest_parity_fixtures_v0,
)
from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.scope_adverse_exit_and_reversal_preparation_narrow_reuse_first_rewire_v0 import (
    SURFACE_ID,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    CanonicalScopeEventType,
    ScopeDirectionState,
)
from trading.master_v2.directional_assessment_v1 import mirror_price_path_for_short
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionSelectedSide,
    CompositionStatus,
    PositionManagementContext,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitDirectionState,
    ExitClass,
    ExistingPositionSide,
    PolicySignalV0,
    PositionState,
    ReconciliationState,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    resolve_integrated_reversal_preparation_entry_exit_binding_v0,
    resolve_integrated_scope_adverse_exit_signal_v0,
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    evaluate_reversal_preparation_matrix_v0,
)
from trading.master_v2.reversal_preparation_scenario_binding_adapter_v0 import (
    REVERSAL_PREPARATION_SCENARIO_BINDING_ADAPTER_OWNER,
    reversal_preparation_decision_is_reduce_only_preparation_v0,
)
from trading.master_v2.scope_event_generator_scenario_binding_adapter_v0 import (
    CANONICAL_SCOPE_EVENT_GENERATOR_OWNER,
    SCOPE_EVENT_GENERATOR_SCENARIO_BINDING_ADAPTER_OWNER,
    derive_scope_adverse_exit_signal_v0,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _market_context,
    _replay_input,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT
    / "docs/research/adverse_exit_and_reversal_preparation_backtest_parity_narrow_rewire_v0.json"
)
ASSESSMENT_CONTRACT = (
    ROOT
    / "docs/research/adverse_exit_and_reversal_preparation_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
)
BACKTEST_WIRING = ROOT / BACKTEST_CONSUMER
INTEGRATED_REPLAY = ROOT / INTEGRATED_REPLAY_PATH


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _scope_surface(inventory: dict) -> dict:
    return next(s for s in inventory["surfaces"] if s["surface_id"] == SURFACE_ID)


def _long_adverse_replay_input():
    return _replay_input(
        canonical_market_context=_market_context(mark_price=100.0),
        price_path=(100.0, 96.0),
        current_price=96.0,
        scope_direction_state=ScopeDirectionState.LONG,
        position_management_context=PositionManagementContext.LONG_POSITION,
        existing_position_side=ExistingPositionSide.LONG,
        position_state=PositionState.OPEN_FULL,
        side_state=SideState.LONG_ACTIVE,
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
        venue_flat=False,
        scope_adverse_exit_signal=PolicySignalV0(triggered=False),
        up_distance=2.0,
        adverse_exit_distance=2.0,
        reversal_distance=4.0,
    )


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


def test_contract_surface_parity_pass_without_global_parity_claim() -> None:
    data = load_contract()
    assert data["adverse_scope_exit_backtest_parity_status"] == "WIRED"
    assert data["reversal_preparation_backtest_parity_status"] == "WIRED"
    assert data["scope_exit_reversal_backtest_parity_pass"] is True
    assert data["backtest_runtime_decision_parity_pass_claim"] is False
    assert data["full_canonical_chain_wired_claim"] is False
    assert data["system_economic_evidence_admissible"] is False
    assert data["runtime_rewire_admissible"] is False
    assert (
        data["verdict"]
        == "PASS_SCOPE_ADVERSE_EXIT_AND_REVERSAL_PREPARATION_BACKTEST_PARITY_NARROW_REWIRE_V0"
    )


def test_contract_binds_canonical_owners_and_backtest_consumer() -> None:
    data = load_contract()
    assert data["canonical_owner"] == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER
    assert data["backtest_consumer"] == BACKTEST_CONSUMER
    assert data["reuse_decision"] == "REUSE_WITH_NARROW_INTEGRATED_CONSUMER_BINDING"
    assert (
        data["canonical_scope_adapter_owner"]
        == SCOPE_EVENT_GENERATOR_SCENARIO_BINDING_ADAPTER_OWNER
    )
    assert (
        data["canonical_reversal_preparation_adapter_owner"]
        == REVERSAL_PREPARATION_SCENARIO_BINDING_ADAPTER_OWNER
    )
    assert data["canonical_adverse_exit_owner"] == CANONICAL_SCOPE_EVENT_GENERATOR_OWNER
    assert BACKTEST_WIRING.is_file()
    assert INTEGRATED_REPLAY.is_file()
    assert (ROOT / SCOPE_ADAPTER_PATH).is_file()
    assert (ROOT / REVERSAL_ADAPTER_PATH).is_file()


def test_narrow_rewire_implemented_without_parallel_owner() -> None:
    data = load_contract()
    decision = data["narrow_rewire_decision"]
    assert decision["rewire_implemented"] is True
    assert decision["new_parallel_owner_created"] is False
    assert decision["functional_rewire_performed"] is True
    rewire = build_rewire_binding(ROOT)
    assert rewire["rewire_binding"]["new_parallel_owner_created"] is False


def test_ADVERSE_SCOPE_EXIT_WIRED_TO_BACKTEST() -> None:
    source = INTEGRATED_REPLAY.read_text(encoding="utf-8")
    assert "derive_scope_adverse_exit_signal_v0" in source
    assert "resolve_integrated_scope_adverse_exit_signal_v0" in source
    backtest_source = BACKTEST_WIRING.read_text(encoding="utf-8")
    assert "run_integrated_offline_trading_logic_replay_v1" in backtest_source

    long_result, short_result = evaluate_adverse_exit_integrated_backtest_parity_fixtures_v0()
    for result in (long_result, short_result):
        assert result.intermediate is not None
        assert (
            result.intermediate.scope_event.event_type
            is CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE
        )
        derived = resolve_integrated_scope_adverse_exit_signal_v0(
            result.intermediate.scope_event,
            PolicySignalV0(triggered=False),
        )
        assert derived.triggered is True


def test_REVERSAL_PREPARATION_WIRED_TO_BACKTEST() -> None:
    source = INTEGRATED_REPLAY.read_text(encoding="utf-8")
    assert "resolve_integrated_reversal_preparation_entry_exit_binding_v0" in source
    assert "project_composition_for_reversal_preparation_entry_exit_v0" in source
    long_decision, short_decision = (
        evaluate_reversal_preparation_integrated_backtest_parity_fixtures_v0()
    )
    assert long_decision.exit_class is ExitClass.REVERSAL_PREPARATION_EXIT
    assert short_decision.exit_class is ExitClass.REVERSAL_PREPARATION_EXIT


def test_REVERSAL_PREPARATION_PRODUCES_EXIT_BEFORE_OPPOSITE_ENTRY() -> None:
    long_inp = _long_adverse_replay_input()
    matrix = evaluate_reversal_preparation_matrix_v0(
        instrument_id=long_inp.instrument_id,
        trading_epoch=long_inp.trading_epoch,
        context_reference=f"{long_inp.context_reference}-precedence",
    )
    projected, _, _, _ = resolve_integrated_reversal_preparation_entry_exit_binding_v0(
        matrix,
        long_inp,
    )
    assert projected.composition_status is CompositionStatus.REVERSAL_PREPARATION
    replay = run_integrated_offline_trading_logic_replay_v1(long_inp)
    assert replay.intermediate is not None
    adverse_signal = resolve_integrated_scope_adverse_exit_signal_v0(
        replay.intermediate.scope_event,
        PolicySignalV0(triggered=False),
    )
    assert adverse_signal.triggered is True
    assert replay.intermediate.entry_exit_decision.exit_class in (
        ExitClass.ADVERSE_SCOPE_EXIT,
        ExitClass.REVERSAL_PREPARATION_EXIT,
    )
    assert replay.intermediate.entry_exit_decision.decision_outcome not in (
        DecisionOutcome.ENTER_LONG,
        DecisionOutcome.ENTER_SHORT,
    )


def test_OPPOSITE_SIDE_REQUIRES_RECONCILED_FLAT() -> None:
    inp = _replay_input(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        side_state=SideState.SHORT_ARMED,
        direction_state=EntryExitDirectionState.SHORT_ARMED,
        reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED,
        venue_flat=False,
        scope_direction_state=ScopeDirectionState.SHORT,
    )
    result = run_integrated_offline_trading_logic_replay_v1(inp)
    assert result.intermediate is not None
    assert result.intermediate.entry_exit_decision.decision_outcome != DecisionOutcome.ENTER_SHORT


def test_POSITION_FLIP_NOT_ALLOWED() -> None:
    long_decision, short_decision = (
        evaluate_reversal_preparation_integrated_backtest_parity_fixtures_v0()
    )
    for decision in (long_decision, short_decision):
        assert decision.position_flip_allowed is False
        assert decision.decision_outcome not in (
            DecisionOutcome.ENTER_LONG,
            DecisionOutcome.ENTER_SHORT,
        )


def test_REDUCE_ONLY_EXIT_PRESERVED() -> None:
    long_decision, short_decision = (
        evaluate_reversal_preparation_integrated_backtest_parity_fixtures_v0()
    )
    for decision in (long_decision, short_decision):
        assert reversal_preparation_decision_is_reduce_only_preparation_v0(decision)
        assert decision.reduce_only is True


def test_mirrored_long_and_short_adverse_fixtures_v0() -> None:
    long_path = (100.0, 96.0)
    short_path = mirror_price_path_for_short(long_path, reference=100.0)
    long_inp = _long_adverse_replay_input()
    short_inp = replace(
        long_inp,
        scope_direction_state=ScopeDirectionState.SHORT,
        position_management_context=PositionManagementContext.SHORT_POSITION,
        existing_position_side=ExistingPositionSide.SHORT,
        side_state=SideState.SHORT_ACTIVE,
        direction_state=EntryExitDirectionState.SHORT_ACTIVE,
        price_path=short_path,
        current_price=float(short_path[-1]),
    )
    long_scope = run_integrated_offline_trading_logic_replay_v1(long_inp).intermediate.scope_event
    short_scope = run_integrated_offline_trading_logic_replay_v1(short_inp).intermediate.scope_event
    assert long_scope.event_type is CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE
    assert short_scope.event_type is CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE
    assert derive_scope_adverse_exit_signal_v0(long_scope).triggered is True
    assert derive_scope_adverse_exit_signal_v0(short_scope).triggered is True


def test_integrated_replay_derives_scope_adverse_exit_signal_positive() -> None:
    result = run_integrated_offline_trading_logic_replay_v1(_long_adverse_replay_input())
    assert result.intermediate is not None
    derived = resolve_integrated_scope_adverse_exit_signal_v0(
        result.intermediate.scope_event,
        PolicySignalV0(triggered=False),
    )
    assert derived.triggered is True


def test_integrated_replay_passthrough_when_scope_not_adverse_negative() -> None:
    inp = _replay_input(scope_adverse_exit_signal=PolicySignalV0(triggered=False))
    result = run_integrated_offline_trading_logic_replay_v1(inp)
    assert result.intermediate is not None
    derived = resolve_integrated_scope_adverse_exit_signal_v0(
        result.intermediate.scope_event,
        inp.scope_adverse_exit_signal,
    )
    assert derived.triggered is False


def test_no_parallel_ssot_imports_in_integrated_replay_negative() -> None:
    tree = ast.parse(INTEGRATED_REPLAY.read_text(encoding="utf-8"))
    defined_generators = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and "generate_deterministic_scope_event" in node.name
    }
    assert defined_generators == set()
    source = INTEGRATED_REPLAY.read_text(encoding="utf-8")
    assert "class ScopeEventGenerator" not in source


def test_inventory_still_pins_scope_reversal_contracts() -> None:
    inventory = build_inventory(ROOT)
    surface = _scope_surface(inventory)
    pinned = {hit["path"] for hit in surface["backtest_binding_candidates"][:3]}
    assert (
        "tests/trading/master_v2/test_scope_event_generator_scenario_replay_binding_parity_rewire_contract_v0.py"
        in pinned
    )
    assert (
        "tests/trading/master_v2/test_reversal_preparation_scenario_replay_binding_parity_rewire_contract_v0.py"
        in pinned
    )


def test_assessment_contract_unchanged_historical_gap_documented() -> None:
    assessment = json.loads(ASSESSMENT_CONTRACT.read_text(encoding="utf-8"))
    assert (
        assessment["gap_review_findings"]["integrated_replay_derives_scope_adverse_exit_signal"]
        is False
    )
    assert assessment["scope_exit_reversal_backtest_parity_pass"] is False
