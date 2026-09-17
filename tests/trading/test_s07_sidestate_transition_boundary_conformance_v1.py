"""S07 SideState transition-boundary conformance.

BOUNDED_WORKPACKAGE=
MASTER_V2_DOUBLE_PLAY_BOUNDED_BEHAVIORAL_CONFORMANCE_VECTOR_SET_FROM_PROVEN_CELLS_ONLY_V1
SLICE=S07_SIDESTATE_TRANSITION_BOUNDARY
PRIMARY_OWNER=trading.master_v2.double_play_state.transition_state
REPLAY_CONSUMER=run_integrated_offline_trading_logic_replay_v1
MAPPER_NON_WRITER=_canonical_scope_event_to_scope_event
RESTORE_SEAM_NOT_SM=parse_persisted_side_state_v1

Additive behavioral assertions only. No trading-semantics mutation.
transition_state remains the sole SideState/Switch SM writer.
Replay consumes inp.side_state + mapped ScopeEvent. Composition selected_side
is not SideState and is not an SM writer. CANDIDATE_ACK holds SideState.
CONFIRMED pipelines are locked against existing owner oracles only.
FILEGATE / execution / Live / S08+ / Kill-Switch taxonomy / EntryExit are
out of this slice.

Epistemic:
- CANONICAL_AUTHORITY: transition_state; Sole-Authority quarantine constants
- FORENSIC_RAW_EVIDENCE: Replay single transition_state join; restore seam
- ALREADY_ADJUDICATED: S06 selected_side ownership; S05 C3≠Scope CONFIRMED
- Not claimed: SHORT-mapping repair; Kill-All flatten; EntryExit; clock
  unification; Dynamic-Scope trailing rewrite; host consumers as writers

Path is tests/trading/ not tests/trading/master_v2/: the Economic Guard treats
tests/trading/master_v2/test_* as forbidden MASTER_V2 mutation surface.
Owner fixtures are reused via import of existing owner test helpers.
"""

from __future__ import annotations

import ast
from dataclasses import fields, replace
from pathlib import Path

from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.sidestate_restore_v1 import (
    SIDESTATE_RESTORE_OWNER,
    parse_persisted_side_state_v1,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import CanonicalScopeEventType
from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentStatus
from trading.master_v2.double_play_composition_matrix_v1 import CompositionSelectedSide
from trading.master_v2.double_play_sole_authority_quarantine_v1 import (
    BACKTEST_POSITION_FEEDBACK_MAY_WRITE_SIDE_STATE,
    CANONICAL_BULL_BEAR_STATE_OWNER,
    CANONICAL_SWITCH_AUTHORITY,
    CHOP_CAN_MUTATE_SIDE_STATE,
    OPS_MAY_WRITE_SIDE_STATE,
    SCENARIO_SCOPE_EVENT_INJECTION_STATUS,
)
from trading.master_v2.double_play_state import ScopeEvent, SideState, TransitionDecision
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OfflineDoublePlayScenarioReplayInputV0,
    OfflineDoublePlayScenarioTickV0,
    run_offline_double_play_scenario_replay_v0,
    validate_offline_double_play_scenario_replay_input_v0,
)

from tests.trading.master_v2.test_double_play_state import EMPTY_ST, _t
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _default_policies,
    _replay_input,
    _run,
)
from tests.trading.test_s05_c1_c3_vs_scope_confirmation_clock_conformance_v1 import (
    _SCOPE_CONFIRMED,
    _empty_scope_confirmation,
    _injected_c1,
)
from tests.trading.test_s06_c4_selected_side_ownership_conformance_v1 import (
    _key,
    _policies_confirm_once,
    _session,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPLAY_SOURCE = _REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_STATE_SOURCE = _REPO_ROOT / "src/trading/master_v2/double_play_state.py"
_RESTORE_SOURCE = (
    _REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "sidestate_restore_v1.py"
)
_COMPOSE_ORACLE = "compose_double_play_decision"
_CONFIRMED_SCOPE_EVENTS = frozenset(
    {
        CanonicalScopeEventType.UPSCOPE_CONFIRMED,
        CanonicalScopeEventType.DOWNSCOPE_CONFIRMED,
    }
)
_ACTIVE_OR_PENDING = frozenset(
    {
        SideState.LONG_ACTIVE,
        SideState.SHORT_ACTIVE,
        SideState.SWITCH_LONG_TO_SHORT_PENDING,
        SideState.SWITCH_SHORT_TO_LONG_PENDING,
    }
)


def _imported_names(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
            names.extend(f"{node.module}.{alias.name}" for alias in node.names)
    return names


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _ordered_calls(tree: ast.AST) -> list[ast.Call]:
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    return sorted(calls, key=lambda node: (node.lineno, node.col_offset))


def _function_def(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"missing function {name}")


def _attr_path(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_attr_path(node.value)}.{node.attr}"
    return ""


def _kw_path(call: ast.Call, keyword: str) -> str | None:
    for kw in call.keywords:
        if kw.arg == keyword:
            return _attr_path(kw.value)
    return None


def _c3_confirmed_without_scope_confirmed():
    policies = replace(
        _default_policies(),
        directional=replace(_default_policies().directional, confirmation_epochs=1),
    )
    inp = _replay_input(
        observation_acceptance_result=_injected_c1(),
        scope_confirmation_state=_empty_scope_confirmation(),
        policies=policies,
    )
    return inp, _run(
        observation_acceptance_result=_injected_c1(),
        scope_confirmation_state=_empty_scope_confirmation(),
        policies=policies,
    )


def test_s07_t01_replay_has_single_transition_state_join_on_mapped_event() -> None:
    """S07-T01: productive Replay path has exactly one transition_state join."""
    assert CANONICAL_SWITCH_AUTHORITY.endswith("transition_state")
    assert CANONICAL_BULL_BEAR_STATE_OWNER == CANONICAL_SWITCH_AUTHORITY
    replay_tree = ast.parse(_REPLAY_SOURCE.read_text(encoding="utf-8"))
    replay_fn = _function_def(replay_tree, "run_integrated_offline_trading_logic_replay_v1")
    transition_calls = [
        call for call in _ordered_calls(replay_fn) if _call_name(call) == "transition_state"
    ]
    assert len(transition_calls) == 1
    join = transition_calls[0]
    assert _kw_path(join, "side_state") == "inp.side_state"
    assert _kw_path(join, "event") == "mapped_event"
    assert _kw_path(join, "side_state") != "composition_result.selected_side"
    assert "selected_side" not in (_kw_path(join, "event") or "")

    defined = {
        node.name
        for node in ast.walk(replay_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "transition_state" not in defined
    imported = _imported_names(replay_tree)
    assert all(_COMPOSE_ORACLE not in name for name in imported)
    assert all("src.execution" not in name for name in imported)


def test_s07_t02_candidate_ack_holds_previous_sidestate() -> None:
    """S07-T02: UPSCOPE/DOWNSCOPE CANDIDATE → CANDIDATE_ACK; SideState unchanged."""
    for event in (ScopeEvent.UPSCOPE_CANDIDATE, ScopeEvent.DOWNSCOPE_CANDIDATE):
        next_side, scope_after, decision = _t(SideState.LONG_ACTIVE, event, EMPTY_ST, 1)
        assert next_side is SideState.LONG_ACTIVE
        assert decision.allowed is True
        assert decision.reason_code == "CANDIDATE_ACK"
        assert scope_after.scope_stability_ticks == EMPTY_ST.scope_stability_ticks + 1

    replay = _run(
        current_price=3500.0,
        price_path=(3500.0, 3500.0),
        scope_confirmation_state=_empty_scope_confirmation(),
        side_state=SideState.LONG_ARMED,
    )
    assert replay.intermediate is not None
    assert replay.intermediate.scope_event.event_type is CanonicalScopeEventType.NOOP
    assert replay.intermediate.state_switch.previous_side_state == SideState.LONG_ARMED.value
    assert replay.intermediate.state_switch.next_side_state == SideState.LONG_ARMED.value
    assert replay.intermediate.transition_decision is not None
    assert replay.intermediate.transition_decision.reason_code == "NOOP"


def test_s07_t03_confirmed_pipeline_steps_only_via_transition_state() -> None:
    """S07-T03: lock existing CONFIRMED pipeline oracles; no new mapping."""
    side, st, decision = _t(SideState.LONG_ACTIVE, ScopeEvent.DOWNSCOPE_CONFIRMED, EMPTY_ST, 0)
    assert side is SideState.SWITCH_LONG_TO_SHORT_PENDING
    assert decision.allowed is True
    side, st, decision = _t(side, ScopeEvent.DOWNSCOPE_CONFIRMED, st, 1)
    assert side is SideState.LONG_BLOCKED
    side, st, decision = _t(side, ScopeEvent.DOWNSCOPE_CONFIRMED, st, 2)
    assert side is SideState.SHORT_ARMED_SWITCH_TERMINAL
    side, _, decision = _t(side, ScopeEvent.DOWNSCOPE_CONFIRMED, st, 3)
    assert side is SideState.SHORT_ACTIVE
    assert decision.reason_code == "SHORT_ACTIVE"

    side, _, decision = _t(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 1)
    assert decision.allowed is True
    assert side is SideState.LONG_ARMED_NEUTRAL_START

    side, st, _ = _t(SideState.SHORT_ACTIVE, ScopeEvent.DOWNSCOPE_CONFIRMED, EMPTY_ST, 0)
    assert side is SideState.SWITCH_SHORT_TO_LONG_PENDING
    side, st, _ = _t(side, ScopeEvent.DOWNSCOPE_CONFIRMED, st, 1)
    assert side is SideState.SHORT_BLOCKED
    side, st, _ = _t(side, ScopeEvent.DOWNSCOPE_CONFIRMED, st, 2)
    assert side is SideState.LONG_ARMED_SWITCH_TERMINAL
    side, _, decision = _t(side, ScopeEvent.UPSCOPE_CONFIRMED, st, 3)
    assert side is SideState.LONG_ACTIVE

    state_tree = ast.parse(_STATE_SOURCE.read_text(encoding="utf-8"))
    assert "transition_state" in {
        node.name for node in ast.walk(state_tree) if isinstance(node, ast.FunctionDef)
    }


def test_s07_t04_selected_side_does_not_write_sidestate() -> None:
    """S07-T04: Composition selected_side does not change SideState."""
    assert CompositionSelectedSide is not SideState
    inp = _replay_input(
        policies=_policies_confirm_once(),
        price_path=(3500.0, 3570.0),
        observation_acceptance_result=_injected_c1(),
        scope_confirmation_state=_empty_scope_confirmation(),
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
        side_state=SideState.LONG_ARMED,
    )
    replay = _run(
        policies=_policies_confirm_once(),
        price_path=(3500.0, 3570.0),
        observation_acceptance_result=_injected_c1(),
        scope_confirmation_state=_empty_scope_confirmation(),
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
        side_state=SideState.LONG_ARMED,
    )
    assert replay.intermediate is not None
    assert replay.intermediate.composition_result.selected_side is CompositionSelectedSide.LONG
    assert replay.intermediate.scope_event.event_type not in _CONFIRMED_SCOPE_EVENTS
    assert replay.intermediate.state_switch.previous_side_state == inp.side_state.value
    assert replay.intermediate.state_switch.next_side_state == inp.side_state.value
    assert replay.intermediate.state_switch.next_side_state != CompositionSelectedSide.LONG.value


def test_s07_t05_c3_confirmed_without_mapped_confirmed_does_not_switch() -> None:
    """S07-T05: C3 CONFIRMED without mapped *_CONFIRMED ScopeEvent does not switch."""
    inp, replay = _c3_confirmed_without_scope_confirmed()
    assert replay.intermediate is not None
    assert replay.intermediate.bull_assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert replay.intermediate.scope_event.event_type not in _SCOPE_CONFIRMED
    assert replay.intermediate.scope_event.event_type not in _CONFIRMED_SCOPE_EVENTS
    assert replay.intermediate.state_switch.previous_side_state == inp.side_state.value
    assert replay.intermediate.state_switch.next_side_state == inp.side_state.value
    decision = replay.intermediate.transition_decision
    assert decision is not None
    assert decision.reason_code in {"NOOP", "CANDIDATE_ACK"}
    assert side_from_value(replay.intermediate.state_switch.next_side_state) not in (
        SideState.SWITCH_LONG_TO_SHORT_PENDING,
        SideState.SWITCH_SHORT_TO_LONG_PENDING,
    )


def side_from_value(value: str) -> SideState:
    return SideState(value)


def test_s07_t06_ops_backtest_restore_are_not_sidestate_sm_writers() -> None:
    """S07-T06: Ops/Backtest/restore are not SideState SM writers."""
    assert OPS_MAY_WRITE_SIDE_STATE != "true"
    assert OPS_MAY_WRITE_SIDE_STATE == "false"
    assert BACKTEST_POSITION_FEEDBACK_MAY_WRITE_SIDE_STATE == "false"
    assert CHOP_CAN_MUTATE_SIDE_STATE == "false"
    assert "transition_state" not in SIDESTATE_RESTORE_OWNER
    restored = parse_persisted_side_state_v1(SideState.LONG_ARMED.value)
    assert restored is SideState.LONG_ARMED

    restore_tree = ast.parse(_RESTORE_SOURCE.read_text(encoding="utf-8"))
    assert all(_call_name(call) != "transition_state" for call in _ordered_calls(restore_tree))
    assert "transition_state" not in {
        node.name for node in ast.walk(restore_tree) if isinstance(node, ast.FunctionDef)
    }
    restore_src = _RESTORE_SOURCE.read_text(encoding="utf-8")
    assert "Not Double Play" in restore_src
    assert "transition_state" in restore_src


def test_s07_t07_unmarked_scenario_scope_event_remains_test_only_guarded() -> None:
    """S07-T07: unmarked scenario tick.scope_event remains TEST_ONLY_GUARDED."""
    assert SCENARIO_SCOPE_EVENT_INJECTION_STATUS == "TEST_ONLY_GUARDED"
    field_names = {f.name for f in fields(OfflineDoublePlayScenarioReplayInputV0)}
    assert "allow_test_scope_event_injection" in field_names
    default = next(
        f.default
        for f in fields(OfflineDoublePlayScenarioReplayInputV0)
        if f.name == "allow_test_scope_event_injection"
    )
    assert default is False

    tick = OfflineDoublePlayScenarioTickV0(
        tick_index=0,
        timestamp_ms=1,
        price=100.0,
        scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
        scope_event_provenance="UNMARKED",
    )
    inp = OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id="ETH-PERP",
        ticks=(tick,),
        allow_test_scope_event_injection=False,
    )
    reasons = validate_offline_double_play_scenario_replay_input_v0(inp)
    assert any(
        "scenario_scope_event_injection_requires_explicit_test_harness_flag" in r for r in reasons
    )
    result = run_offline_double_play_scenario_replay_v0(inp)
    assert result.replay_pass is False


def test_s07_t08_candidate_ack_is_not_active_or_pending_transition() -> None:
    """S07-T08: CANDIDATE_ACK is not *_ACTIVE / *_PENDING transition."""
    for prior in (SideState.LONG_ACTIVE, SideState.LONG_ARMED, SideState.NEUTRAL_OBSERVE):
        next_side, _, decision = _t(prior, ScopeEvent.DOWNSCOPE_CANDIDATE, EMPTY_ST, 1)
        assert decision.reason_code == "CANDIDATE_ACK"
        assert next_side is prior
        if prior not in _ACTIVE_OR_PENDING:
            assert next_side not in _ACTIVE_OR_PENDING
        if prior is not SideState.LONG_ACTIVE:
            assert next_side is not SideState.LONG_ACTIVE
        assert next_side is not SideState.SWITCH_LONG_TO_SHORT_PENDING
        assert next_side is not SideState.SWITCH_SHORT_TO_LONG_PENDING

    next_side, _, decision = _t(
        SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CANDIDATE, EMPTY_ST, 1
    )
    assert decision.reason_code == "CANDIDATE_ACK"
    assert next_side is SideState.NEUTRAL_OBSERVE
    assert isinstance(decision, TransitionDecision)

    this_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imported = _imported_names(this_tree)
    assert all(_COMPOSE_ORACLE not in name for name in imported)
    assert all("src.execution" not in name for name in imported)
    assert all(not name.startswith("src.live") for name in imported)
    assert all("kill_switch_should_block_trading" not in name for name in imported)
