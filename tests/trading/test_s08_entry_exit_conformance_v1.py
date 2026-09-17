"""S08 ENTRY/EXIT HOLD/ENTER/EXIT/REDUCE/NO_IMPLICIT_FLIP conformance.

BOUNDED_WORKPACKAGE=
MASTER_V2_DOUBLE_PLAY_BOUNDED_BEHAVIORAL_CONFORMANCE_VECTOR_SET_FROM_PROVEN_CELLS_ONLY_V1
SLICE=S08_ENTRY_EXIT
PRIMARY_OWNER=trading.master_v2.double_play_entry_exit_policy_v0.evaluate_double_play_entry_exit_policy_v0
REPLAY_CONSUMER=run_integrated_offline_trading_logic_replay_v1
ENTRY_EXIT_MAPPING_OWNER=_side_state_to_entry_exit_direction

Additive behavioral assertions only. No trading-semantics mutation.
Locks the existing entry_exit_policy_v0 owner and Replay join after S07
closed SideState transition ownership. Does not define new policy.
PENDING SideState→ARMED mapping remains mapping-only;
PENDING_ENTRY_ELIGIBILITY_CANONICALLY_DEFINED is not claimed.
FILEGATE / execution / Live / S09+ / Kill-Switch taxonomy / 29P/29Q are
out of this slice.

Epistemic:
- CANONICAL_AUTHORITY: Master Runbook ENTRY_EXIT_OWNER=entry_exit_policy_v0;
  ENTRY_EXIT_MAPPING_OWNER=_side_state_to_entry_exit_direction;
  evaluate_double_play_entry_exit_policy_v0 precedence and flags
- FORENSIC_RAW_EVIDENCE: Replay single policy join; HOLD/ENTER/EXIT/REDUCE
  outcomes; position_flip_allowed always false in owner
- ALREADY_ADJUDICATED: S06 selected_side ownership; S07 transition_state
  SideState ownership
- Not claimed: quantity algebra; PENDING ENTER eligibility; Kill-All flatten;
  29P/29Q; FILEGATE; implicit close+reverse as authorized flip

Path is tests/trading/ not tests/trading/master_v2/: the Economic Guard treats
tests/trading/master_v2/test_* as forbidden MASTER_V2 mutation surface.
Owner fixtures are reused via import of existing owner test helpers.
"""

from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentStatus
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionSelectedSide,
    CompositionStatus,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryEligibility,
    EntryExitDirectionState,
    ExistingPositionSide,
    ExitClass,
    PolicySignalV0,
    PositionManagementAction,
    PositionState,
    ReversalState,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.suitability_binding_v1 import SuitabilityBindingStatus
from trading.master_v2.survival_assessment_v1 import SurvivalAssessmentStatus

from tests.trading.master_v2.test_double_play_entry_exit_policy_v0 import (
    _evaluate,
    _long_selected_composition,
    _short_selected_composition,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run
from tests.trading.master_v2.test_post_confirmation_survival_suitability_composition_binding_v1 import (
    _key,
    _policies_confirm_once,
    _session,
)
from tests.trading.test_s05_c1_c3_vs_scope_confirmation_clock_conformance_v1 import (
    _empty_scope_confirmation,
    _injected_c1,
)
from tests.trading.test_s06_c4_selected_side_ownership_conformance_v1 import (
    _policies_confirm_once as _s06_policies_confirm_once,
)
from tests.trading.test_s07_sidestate_transition_boundary_conformance_v1 import (
    _CONFIRMED_SCOPE_EVENTS,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPLAY_SOURCE = _REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_POLICY_SOURCE = _REPO_ROOT / "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
_STATE_SOURCE = _REPO_ROOT / "src/trading/master_v2/double_play_state.py"
_POLICY_OWNER = "evaluate_double_play_entry_exit_policy_v0"
_MAPPING_OWNER = "_side_state_to_entry_exit_direction"
_COMPOSE_ORACLE = "compose_double_play_decision"
_ENTER_OUTCOMES = frozenset({DecisionOutcome.ENTER_LONG, DecisionOutcome.ENTER_SHORT})
_EXIT_OR_REDUCE = frozenset({DecisionOutcome.EXIT, DecisionOutcome.REDUCE})
_HOLD_NOT_ENTRY_EXIT = frozenset(_ENTER_OUTCOMES | _EXIT_OR_REDUCE)


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


def _kw_constant(call: ast.Call, keyword: str) -> object:
    for kw in call.keywords:
        if kw.arg == keyword:
            if isinstance(kw.value, ast.Constant):
                return kw.value.value
            return ast.dump(kw.value)
    return None


def _keyword_constants_and_names(tree: ast.AST, keyword: str) -> tuple[list[object], list[str]]:
    constants: list[object] = []
    names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.keyword) or node.arg != keyword:
            continue
        if isinstance(node.value, ast.Constant):
            constants.append(node.value.value)
        elif isinstance(node.value, ast.Name):
            names.append(node.value.id)
        else:
            raise AssertionError(f"unexpected {keyword} value {ast.dump(node.value)}")
    return constants, names


def _enter_long_replay_kwargs() -> dict[str, object]:
    return {
        "policies": _policies_confirm_once(),
        "price_path": (3500.0, 3570.0),
        "observation_acceptance_result": _injected_c1(),
        "scope_confirmation_state": _empty_scope_confirmation(),
        "confirmation_progress_session_id": _session(),
        "confirmation_progress_venue": "okx_eea",
        "confirmation_progress_instrument": _key(),
        "side_state": SideState.LONG_ARMED,
    }


def _enter_short_replay_kwargs() -> dict[str, object]:
    return {
        "policies": _policies_confirm_once(),
        "price_path": (3500.0, 3430.0),
        "observation_acceptance_result": _injected_c1(),
        "scope_confirmation_state": _empty_scope_confirmation(),
        "confirmation_progress_session_id": _session(),
        "confirmation_progress_venue": "okx_eea",
        "confirmation_progress_instrument": _key(),
        "side_state": SideState.SHORT_ARMED,
        "direction_state": EntryExitDirectionState.SHORT_ARMED,
        "scope_direction_state": ScopeDirectionState.SHORT,
    }


def _assert_no_implicit_flip(decision) -> None:
    assert decision.position_flip_allowed is False
    assert decision.decision_outcome not in _ENTER_OUTCOMES or decision.reduce_only is False
    if decision.decision_outcome in _EXIT_OR_REDUCE:
        assert decision.reduce_only is True
        assert decision.decision_outcome not in _ENTER_OUTCOMES


def test_s08_t01_replay_has_single_entry_exit_owner_join() -> None:
    """S08-T01: productive Replay path has exactly one entry/exit policy join."""
    replay_tree = ast.parse(_REPLAY_SOURCE.read_text(encoding="utf-8"))
    replay_fn = _function_def(replay_tree, "run_integrated_offline_trading_logic_replay_v1")
    policy_calls = [call for call in _ordered_calls(replay_fn) if _call_name(call) == _POLICY_OWNER]
    mapping_calls = [
        call for call in _ordered_calls(replay_fn) if _call_name(call) == _MAPPING_OWNER
    ]
    assert len(policy_calls) == 1
    assert len(mapping_calls) == 1
    defined = {
        node.name
        for node in ast.walk(replay_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert _POLICY_OWNER not in defined
    assert _MAPPING_OWNER in defined
    imported = _imported_names(replay_tree)
    assert any(name.endswith(_POLICY_OWNER) for name in imported)
    assert all(_COMPOSE_ORACLE not in name for name in imported)
    assert all("src.execution" not in name for name in imported)

    join = policy_calls[0]
    assert _call_name(join) == _POLICY_OWNER
    mapping = mapping_calls[0]
    assert mapping.args and _attr_path(mapping.args[0]) == "next_side_state"


def test_s08_t02_hold_emits_no_entry_or_exit() -> None:
    """S08-T02: HOLD on existing same-side exposure emits neither ENTER nor EXIT."""
    policy = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        composition_result=_long_selected_composition(),
    )
    assert policy.decision_outcome is DecisionOutcome.HOLD
    assert policy.position_management_action is PositionManagementAction.HOLD
    assert policy.exit_class is ExitClass.NONE
    assert policy.decision_outcome not in _HOLD_NOT_ENTRY_EXIT
    assert policy.position_flip_allowed is False
    assert policy.reduce_only is False

    replay = _run(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        side_state=SideState.LONG_ACTIVE,
    )
    assert replay.intermediate is not None
    hold = replay.intermediate.entry_exit_decision
    assert replay.evidence.decision_outcome == DecisionOutcome.HOLD.value
    assert hold.decision_outcome is DecisionOutcome.HOLD
    assert hold.position_management_action is PositionManagementAction.HOLD
    assert hold.decision_outcome not in _HOLD_NOT_ENTRY_EXIT
    assert hold.position_flip_allowed is False

    confirmed_hold_kwargs = _enter_long_replay_kwargs()
    confirmed_hold_kwargs.update(
        {
            "side_state": SideState.LONG_ACTIVE,
            "position_state": PositionState.OPEN_FULL,
            "existing_position_side": ExistingPositionSide.LONG,
        }
    )
    confirmed_hold = _run(**confirmed_hold_kwargs)
    assert confirmed_hold.intermediate is not None
    assert (
        confirmed_hold.intermediate.composition_result.selected_side is CompositionSelectedSide.LONG
    )
    assert confirmed_hold.evidence.decision_outcome == DecisionOutcome.HOLD.value
    assert (
        confirmed_hold.intermediate.entry_exit_decision.decision_outcome not in _HOLD_NOT_ENTRY_EXIT
    )


def test_s08_t03_enter_only_under_documented_preconditions() -> None:
    """S08-T03: ENTER requires armed matching selected side on flat reconciled."""
    enter_long = _evaluate(
        composition_result=_long_selected_composition(),
        direction_state=EntryExitDirectionState.LONG_ARMED,
    )
    assert enter_long.decision_outcome is DecisionOutcome.ENTER_LONG
    assert enter_long.entry_eligibility is EntryEligibility.ELIGIBLE
    assert enter_long.position_flip_allowed is False
    assert enter_long.reduce_only is False
    assert enter_long.position_management_action is PositionManagementAction.NONE

    enter_short = _evaluate(
        composition_result=_short_selected_composition(),
        direction_state=EntryExitDirectionState.SHORT_ARMED,
    )
    assert enter_short.decision_outcome is DecisionOutcome.ENTER_SHORT
    assert enter_short.entry_eligibility is EntryEligibility.ELIGIBLE

    not_armed = _evaluate(
        composition_result=_long_selected_composition(),
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
    )
    assert not_armed.decision_outcome is not DecisionOutcome.ENTER_LONG
    assert not_armed.decision_outcome is DecisionOutcome.BLOCKED
    assert "direction_not_armed" in not_armed.reason_codes

    not_flat = _evaluate(
        composition_result=_long_selected_composition(),
        direction_state=EntryExitDirectionState.LONG_ARMED,
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.NONE,
    )
    assert not_flat.decision_outcome is not DecisionOutcome.ENTER_LONG

    mismatch = _evaluate(
        composition_result=_long_selected_composition(),
        direction_state=EntryExitDirectionState.SHORT_ARMED,
    )
    assert mismatch.decision_outcome not in _ENTER_OUTCOMES

    replay_long = _run(**_enter_long_replay_kwargs())
    assert replay_long.intermediate is not None
    assert replay_long.intermediate.bull_assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert replay_long.intermediate.bull_survival.status is SurvivalAssessmentStatus.PASS
    assert replay_long.intermediate.bull_suitability.status is SuitabilityBindingStatus.PASS
    assert replay_long.intermediate.composition_result.selected_side is CompositionSelectedSide.LONG
    assert (
        replay_long.intermediate.composition_result.composition_status
        is CompositionStatus.LONG_SELECTED
    )
    assert replay_long.evidence.decision_outcome == DecisionOutcome.ENTER_LONG.value
    assert replay_long.intermediate.entry_exit_decision.position_flip_allowed is False

    replay_short = _run(**_enter_short_replay_kwargs())
    assert replay_short.intermediate is not None
    assert replay_short.evidence.decision_outcome == DecisionOutcome.ENTER_SHORT.value
    assert (
        replay_short.intermediate.composition_result.selected_side is CompositionSelectedSide.SHORT
    )


def test_s08_t04_exit_acts_on_existing_exposure() -> None:
    """S08-T04: EXIT classes close/reduce existing exposure; never ENTER."""
    safety = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        safety_exit_signal=PolicySignalV0(triggered=True, reason_code="safety"),
    )
    assert safety.decision_outcome is DecisionOutcome.EXIT
    assert safety.exit_class is ExitClass.SAFETY_EXIT
    assert safety.position_management_action is PositionManagementAction.EXIT
    assert safety.reduce_only is True
    assert safety.position_flip_allowed is False
    assert safety.decision_outcome not in _ENTER_OUTCOMES

    profit = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        profit_protection_signal=PolicySignalV0(triggered=True, reason_code="profit_lock"),
    )
    assert profit.decision_outcome is DecisionOutcome.EXIT
    assert profit.exit_class is ExitClass.PROFIT_PROTECTION_EXIT
    assert profit.reduce_only is True

    replay = _run(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        side_state=SideState.LONG_ACTIVE,
        safety_exit_signal=PolicySignalV0(triggered=True, reason_code="safety"),
    )
    assert replay.intermediate is not None
    assert replay.evidence.decision_outcome == DecisionOutcome.EXIT.value
    assert replay.intermediate.entry_exit_decision.exit_class is ExitClass.SAFETY_EXIT
    assert replay.intermediate.entry_exit_decision.reduce_only is True
    assert replay.intermediate.entry_exit_decision.position_flip_allowed is False
    assert replay.evidence.decision_outcome != DecisionOutcome.ENTER_LONG.value


def test_s08_t05_reduce_does_not_increase_exposure() -> None:
    """S08-T05: REDUCE is reduce_only and never ENTER."""
    adverse = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        scope_adverse_exit_signal=PolicySignalV0(triggered=True, reason_code="adverse_scope"),
    )
    assert adverse.decision_outcome is DecisionOutcome.REDUCE
    assert adverse.exit_class is ExitClass.ADVERSE_SCOPE_EXIT
    assert adverse.position_management_action is PositionManagementAction.REDUCE
    assert adverse.reduce_only is True
    assert adverse.position_flip_allowed is False
    assert adverse.decision_outcome not in _ENTER_OUTCOMES

    hard_risk = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        hard_risk_reduction_signal=PolicySignalV0(triggered=True, reason_code="hard_risk"),
    )
    assert hard_risk.decision_outcome is DecisionOutcome.REDUCE
    assert hard_risk.exit_class is ExitClass.HARD_RISK_EXIT
    assert hard_risk.reduce_only is True

    replay = _run(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        side_state=SideState.LONG_ACTIVE,
        scope_adverse_exit_signal=PolicySignalV0(triggered=True, reason_code="adverse_scope"),
    )
    assert replay.intermediate is not None
    assert replay.evidence.decision_outcome == DecisionOutcome.REDUCE.value
    assert replay.intermediate.entry_exit_decision.reduce_only is True
    assert replay.intermediate.entry_exit_decision.position_flip_allowed is False
    assert replay.evidence.decision_outcome not in {
        DecisionOutcome.ENTER_LONG.value,
        DecisionOutcome.ENTER_SHORT.value,
    }
    policy_tree = ast.parse(_POLICY_SOURCE.read_text(encoding="utf-8"))
    exit_fn = _function_def(policy_tree, "_exit_decision")
    assert (
        _kw_constant(
            next(
                node
                for node in ast.walk(exit_fn)
                if isinstance(node, ast.Call) and _call_name(node) == "_finalize_decision"
            ),
            "reduce_only",
        )
        is True
    )


def test_s08_t06_no_implicit_flip_on_opposite_selected_side() -> None:
    """S08-T06: opposite selected_side is reversal REDUCE, not close+reverse ENTER."""
    policy = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        composition_result=_short_selected_composition(),
        direction_state=EntryExitDirectionState.SHORT_ARMED,
    )
    assert policy.exit_class is ExitClass.REVERSAL_PREPARATION_EXIT
    assert policy.reversal_state is ReversalState.PREPARATION
    assert policy.decision_outcome is DecisionOutcome.REDUCE
    assert policy.decision_outcome is not DecisionOutcome.ENTER_SHORT
    assert policy.decision_outcome is not DecisionOutcome.ENTER_LONG
    _assert_no_implicit_flip(policy)

    mirrored = _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.SHORT,
        composition_result=_long_selected_composition(),
        direction_state=EntryExitDirectionState.LONG_ARMED,
    )
    assert mirrored.exit_class is ExitClass.REVERSAL_PREPARATION_EXIT
    assert mirrored.decision_outcome is not DecisionOutcome.ENTER_LONG
    _assert_no_implicit_flip(mirrored)

    replay_kwargs = _enter_short_replay_kwargs()
    replay_kwargs.update(
        {
            "side_state": SideState.LONG_ACTIVE,
            "position_state": PositionState.OPEN_FULL,
            "existing_position_side": ExistingPositionSide.LONG,
            "direction_state": EntryExitDirectionState.LONG_ACTIVE,
        }
    )
    replay = _run(**replay_kwargs)
    assert replay.intermediate is not None
    assert replay.intermediate.composition_result.selected_side is CompositionSelectedSide.SHORT
    flip = replay.intermediate.entry_exit_decision
    assert replay.evidence.decision_outcome == DecisionOutcome.REDUCE.value
    assert flip.exit_class is ExitClass.REVERSAL_PREPARATION_EXIT
    assert flip.decision_outcome is not DecisionOutcome.ENTER_SHORT
    _assert_no_implicit_flip(flip)

    policy_tree = ast.parse(_POLICY_SOURCE.read_text(encoding="utf-8"))
    flip_constants, flip_names = _keyword_constants_and_names(policy_tree, "position_flip_allowed")
    assert flip_constants
    assert all(flag is False for flag in flip_constants)
    assert True not in flip_constants
    assert flip_names == ["position_flip_allowed"]


def test_s08_t07_ownership_consumption_does_not_collapse_sidestate_or_scope() -> None:
    """S08-T07: selected_side/SideState/confirmation/scope stay on documented owners."""
    assert CompositionSelectedSide is not SideState
    policy_src = _POLICY_SOURCE.read_text(encoding="utf-8")
    policy_tree = ast.parse(policy_src)
    assert "transition_state" not in {
        node.name for node in ast.walk(policy_tree) if isinstance(node, ast.FunctionDef)
    }
    assert all(_call_name(call) != "transition_state" for call in _ordered_calls(policy_tree))
    assert "selected_side=inp.composition_result.selected_side" in policy_src.replace(" ", "")

    replay_tree = ast.parse(_REPLAY_SOURCE.read_text(encoding="utf-8"))
    replay_fn = _function_def(replay_tree, "run_integrated_offline_trading_logic_replay_v1")
    transition_calls = [
        call for call in _ordered_calls(replay_fn) if _call_name(call) == "transition_state"
    ]
    assert len(transition_calls) == 1
    assert _kw_path(transition_calls[0], "side_state") == "inp.side_state"
    assert "selected_side" not in (_kw_path(transition_calls[0], "side_state") or "")

    ctor_calls = [
        call
        for call in _ordered_calls(replay_fn)
        if _call_name(call) == "DoublePlayEntryExitPolicyInputV0"
    ]
    assert ctor_calls
    assert all(
        _kw_path(call, "composition_result") == "composition_for_policy" for call in ctor_calls
    )
    assert all(_kw_path(call, "direction_state") == "effective_direction" for call in ctor_calls)
    assert all(
        "selected_side" not in (_kw_path(call, "direction_state") or "") for call in ctor_calls
    )

    replay = _run(**_enter_long_replay_kwargs())
    assert replay.intermediate is not None
    assert replay.intermediate.scope_event.event_type not in _CONFIRMED_SCOPE_EVENTS
    assert replay.intermediate.state_switch.previous_side_state == SideState.LONG_ARMED.value
    assert replay.intermediate.composition_result.selected_side is CompositionSelectedSide.LONG
    assert replay.intermediate.composition_result.selected_side is not SideState.LONG_ARMED
    assert replay.intermediate.entry_exit_decision.selected_side is CompositionSelectedSide.LONG
    assert _s06_policies_confirm_once().directional.confirmation_epochs == 1

    state_tree = ast.parse(_STATE_SOURCE.read_text(encoding="utf-8"))
    assert all(_call_name(call) != _POLICY_OWNER for call in _ordered_calls(state_tree))


def test_s08_t08_s09_absent_and_non_execution_surface() -> None:
    """S08-T08: S09 not started; this slice does not import execution/Live/KS."""
    assert list(_REPO_ROOT.glob("tests/trading/test_s09_*.py")) == []
    this_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imported = _imported_names(this_tree)
    assert all(_COMPOSE_ORACLE not in name for name in imported)
    assert all("src.execution" not in name for name in imported)
    assert all(not name.startswith("src.live") for name in imported)
    assert all("kill_switch_should_block_trading" not in name for name in imported)
    assert all("construct_live_execution_port_v1" not in name for name in imported)
    s07_path = _REPO_ROOT / "tests/trading/test_s07_sidestate_transition_boundary_conformance_v1.py"
    assert s07_path.is_file()
