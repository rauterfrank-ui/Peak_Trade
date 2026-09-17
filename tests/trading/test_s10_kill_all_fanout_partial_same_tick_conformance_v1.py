"""S10 KILL_ALL fanout / partial same-tick conformance.

BOUNDED_WORKPACKAGE=
MASTER_V2_DOUBLE_PLAY_BOUNDED_BEHAVIORAL_CONFORMANCE_VECTOR_SET_FROM_PROVEN_CELLS_ONLY_V1
SLICE=S10_KILL_ALL_FANOUT_PARTIAL_SAME_TICK
PRIMARY_OWNER=trading.master_v2.double_play_state.transition_state
REPLAY_CONSUMER=run_integrated_offline_trading_logic_replay_v1
ENTRY_EXIT_MAPPING_OWNER=_side_state_to_entry_exit_direction
COMPOSITION_FANOUT_OWNER=compose_double_play_decision
SAFETY_BINDER=safety_context_from_integrated_replay_input_v1
KILLSWITCH_BINDER=derive_killswitch_boundary_mode_v0

Additive behavioral assertions only. No trading-semantics mutation.
Locks already adjudicated KILL_ALL fanout / same-tick cells after S09
closed the KILL_ALL state machine. Does not define new policy.
Does not repair the PARTIAL/DEVIATES binder-input cell.
Current Behavior and Owner-Norm remain separate observables.
PENDING_ENTRY_ELIGIBILITY_CANONICALLY_DEFINED remains false.
quantity_status remains NOT_BOUND.
FILEGATE / execution / Live / S11 / Replay producer of
KILL_ALL_REQUIRED / killswitch_blocked taxonomy / 29P/29Q /
Golden Vector / composition-before-transition semantics are out of
this slice.

Epistemic:
- CANONICAL_AUTHORITY: Master Runbook DOUBLE_PLAY_SIDE_STATE_OWNER=
  transition_state; SIDESTATE_KILL_ALL_ROLE=
  DOUBLE_PLAY_STRATEGY_STATE_MACHINE; KILL_ALL != FILEGATE
- FORENSIC_RAW_EVIDENCE: Replay entry_exit mapping consumes
  next_side_state; Safety/KS binders consume inp.side_state;
  KILL_ALL maps to EntryExitDirectionState.NEUTRAL; compose
  KILL_ALL reason is no new activation
- ALREADY_ADJUDICATED: S09 KILL_ALL SM / != flatten; S08 ENTER
  requires armed direction; CHAR-1 composition no-new-activation
- Not claimed: Replay producer of KILL_ALL_REQUIRED; further
  composition-before-transition semantics; Replay
  killswitch_blocked taxonomy; Manifest-vs-Owner envelope
  qualifier; PENDING ENTER eligibility; quantity algebra

Path is tests/trading/ not tests/trading/master_v2/: the Economic Guard treats
tests/trading/master_v2/test_* as forbidden MASTER_V2 mutation surface.
Owner fixtures are reused via import of existing owner test helpers.
"""

from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.capital_risk_sizing_safety_intent_restore_v1 import (
    safety_context_from_integrated_replay_input_v1,
)
from trading.master_v2.double_play_composition import (
    DoublePlayCompositionBlockReason,
    DoublePlayCompositionStatus,
    RequestedSide,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryEligibility,
    EntryExitDirectionState,
)
from trading.master_v2.double_play_state import ScopeEvent, SideState, TransitionDecision
from trading.master_v2.double_play_suitability import SideCompatibility, SuitabilityClass
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    _side_state_to_entry_exit_direction,
)

from tests.trading.master_v2.test_double_play_composition import (
    _compose,
    _suit,
    _surv_ok,
)
from tests.trading.master_v2.test_double_play_entry_exit_policy_v0 import (
    _evaluate,
    _long_selected_composition,
)
from tests.trading.master_v2.test_double_play_state import EMPTY_ST, _t
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _replay_input,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPLAY_SOURCE = _REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_RESTORE_SOURCE = (
    _REPO_ROOT / "src/trading/master_v2/capital_risk_sizing_safety_intent_restore_v1.py"
)
_STATE_SOURCE = _REPO_ROOT / "src/trading/master_v2/double_play_state.py"
_SM_OWNER = "transition_state"
_MAPPING_OWNER = "_side_state_to_entry_exit_direction"
_COMPOSE_ORACLE = "compose_double_play_decision"
_SAFETY_BINDER = "safety_context_from_integrated_replay_input_v1"
_KS_MODE_OWNER = "derive_killswitch_boundary_mode_v0"
_KS_CTX = "KillSwitchBoundaryOfflineReplayContextV0"
_CURRENT_BEHAVIOR_ORACLE = "inp.side_state"
_OWNER_NORM_ORACLE = "next_side_state"
_ENTER_OUTCOMES = frozenset({DecisionOutcome.ENTER_LONG, DecisionOutcome.ENTER_SHORT})
_ABSENT_FLATTEN_TOKENS = ("cancel_all", "cancel all", "flatten")
_OPEN_PRODUCER_TOKENS = ("KILL_ALL_REQUIRED", "kill_all_required")


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


def _same_tick_kill_all_from_armed() -> tuple[SideState, SideState]:
    incoming = SideState.LONG_ARMED
    next_side, _, decision = _t(incoming, ScopeEvent.KILL_ALL_REQUIRED, EMPTY_ST, 7)
    assert next_side is SideState.KILL_ALL
    assert decision.reason_code == "KILL_ALL"
    assert incoming is not next_side
    return incoming, next_side


def test_s10_t01_same_tick_entry_exit_conforms_binders_read_incoming() -> None:
    """S10-T01: same-tick ENTER mapping uses next_side_state; binders use inp.side_state."""
    replay_src = _REPLAY_SOURCE.read_text(encoding="utf-8")
    replay_tree = ast.parse(replay_src)
    replay_fn = _function_def(replay_tree, "run_integrated_offline_trading_logic_replay_v1")
    sm_calls = [call for call in _ordered_calls(replay_fn) if _call_name(call) == _SM_OWNER]
    mapping_calls = [
        call for call in _ordered_calls(replay_fn) if _call_name(call) == _MAPPING_OWNER
    ]
    ks_mode_calls = [
        call for call in _ordered_calls(replay_fn) if _call_name(call) == _KS_MODE_OWNER
    ]
    ks_ctx_calls = [call for call in _ordered_calls(replay_fn) if _call_name(call) == _KS_CTX]
    matrix_calls = [
        call
        for call in _ordered_calls(replay_fn)
        if _call_name(call) == "evaluate_double_play_composition_matrix_v1"
    ]
    assert len(sm_calls) == 1
    assert len(mapping_calls) == 1
    assert len(ks_mode_calls) == 1
    assert len(ks_ctx_calls) == 1
    assert len(matrix_calls) == 1
    compose_calls = [
        call for call in _ordered_calls(replay_fn) if _call_name(call) == _COMPOSE_ORACLE
    ]
    assert compose_calls == []
    assert _kw_path(sm_calls[0], "side_state") == _CURRENT_BEHAVIOR_ORACLE
    assert mapping_calls[0].args
    assert _attr_path(mapping_calls[0].args[0]) == _OWNER_NORM_ORACLE
    assert _kw_path(ks_mode_calls[0], "side_state") == _CURRENT_BEHAVIOR_ORACLE
    assert _kw_path(ks_ctx_calls[0], "side_state") == _CURRENT_BEHAVIOR_ORACLE
    assert _kw_path(ks_mode_calls[0], "side_state") != _OWNER_NORM_ORACLE
    assert _kw_path(ks_ctx_calls[0], "side_state") != _OWNER_NORM_ORACLE
    assert matrix_calls[0].lineno < sm_calls[0].lineno
    assert mapping_calls[0].lineno > sm_calls[0].lineno
    assert ks_mode_calls[0].lineno > sm_calls[0].lineno
    assert "inp.side_state is SideState.KILL_ALL" in replay_src
    assert "next_side_state is SideState.KILL_ALL" not in replay_src

    restore_src = _RESTORE_SOURCE.read_text(encoding="utf-8")
    restore_tree = ast.parse(restore_src)
    restore_fn = _function_def(restore_tree, _SAFETY_BINDER)
    restore_segment = ast.get_source_segment(restore_src, restore_fn)
    assert restore_segment is not None
    assert "inp.side_state is SideState.KILL_ALL" in restore_segment
    assert "next_side_state" not in restore_segment


def test_s10_t02_same_tick_enter_new_activation_blocking_conforms() -> None:
    """S10-T02: same-tick KILL_ALL owner-norm blocks ENTER / new activation."""
    incoming, next_side = _same_tick_kill_all_from_armed()
    mapped = _side_state_to_entry_exit_direction(next_side)
    assert mapped is EntryExitDirectionState.NEUTRAL
    assert _side_state_to_entry_exit_direction(incoming) is EntryExitDirectionState.LONG_ARMED

    blocked = _evaluate(
        composition_result=_long_selected_composition(),
        direction_state=mapped,
    )
    assert blocked.decision_outcome not in _ENTER_OUTCOMES
    assert blocked.decision_outcome is DecisionOutcome.BLOCKED
    assert blocked.entry_eligibility is EntryEligibility.BLOCKED
    assert "direction_not_armed" in blocked.reason_codes
    assert blocked.quantity_status == "NOT_BOUND"

    would_enter = _evaluate(
        composition_result=_long_selected_composition(),
        direction_state=_side_state_to_entry_exit_direction(incoming),
    )
    assert would_enter.decision_outcome is DecisionOutcome.ENTER_LONG

    composed = _compose(
        transition=TransitionDecision(True, "KILL_ALL", False),
        state=next_side,
        surv=_surv_ok(),
        suit=_suit(
            sclass=SuitabilityClass.BOTH_SIDES_CANDIDATE,
            can_long=True,
            can_short=True,
            can_neutral=True,
            side_c=SideCompatibility.BOTH,
        ),
        req=RequestedSide.LONG_BULL,
    )
    assert composed.status is DoublePlayCompositionStatus.KILL_ALL
    assert DoublePlayCompositionBlockReason.STATE_KILL_ALL in composed.block_reasons
    assert composed.reason == "State is KILL_ALL; no new activation."
    assert composed.live_authorization is False


def test_s10_t03_kill_all_flatten_conforms_false() -> None:
    """S10-T03: KILL_ALL fanout is no-new-activation, not flatten."""
    _, next_side = _same_tick_kill_all_from_armed()
    composed = _compose(
        transition=TransitionDecision(True, "KILL_ALL", False),
        state=next_side,
        surv=_surv_ok(),
        suit=_suit(
            sclass=SuitabilityClass.BOTH_SIDES_CANDIDATE,
            can_long=True,
            can_short=True,
            can_neutral=True,
            side_c=SideCompatibility.BOTH,
        ),
        req=RequestedSide.LONG_BULL,
    )
    assert composed.status is DoublePlayCompositionStatus.KILL_ALL
    assert "flatten" not in composed.reason.lower()
    assert composed.status is not DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY
    names = {field.name for field in type(composed).__dataclass_fields__.values()}
    for forbidden in ("cancel", "flatten", "kill_switch", "integrity"):
        assert all(forbidden not in name for name in names)

    state_src = _STATE_SOURCE.read_text(encoding="utf-8").lower()
    for token in _ABSENT_FLATTEN_TOKENS:
        assert token not in state_src, token


def test_s10_t04_current_behavior_vs_owner_norm_partial_deviates() -> None:
    """S10-T04: conserve PARTIAL/DEVIATES binder input; do not normalize it."""
    incoming, next_side = _same_tick_kill_all_from_armed()
    current_inp = _replay_input(side_state=incoming)
    owner_norm_inp = _replay_input(side_state=next_side)
    current_ctx = safety_context_from_integrated_replay_input_v1(current_inp)
    owner_norm_ctx = safety_context_from_integrated_replay_input_v1(owner_norm_inp)
    assert current_inp.side_state is incoming
    assert owner_norm_inp.side_state is next_side
    assert current_inp.side_state is not owner_norm_inp.side_state
    assert current_ctx != owner_norm_ctx
    this_src = Path(__file__).read_text(encoding="utf-8")
    assert '_CURRENT_BEHAVIOR_ORACLE = "inp.side_state"' in this_src
    assert '_OWNER_NORM_ORACLE = "next_side_state"' in this_src
    assert _CURRENT_BEHAVIOR_ORACLE != _OWNER_NORM_ORACLE
    replay_src = _REPLAY_SOURCE.read_text(encoding="utf-8")
    replay_tree = ast.parse(replay_src)
    replay_fn = _function_def(replay_tree, "run_integrated_offline_trading_logic_replay_v1")
    ks_ctx_calls = [call for call in _ordered_calls(replay_fn) if _call_name(call) == _KS_CTX]
    assert _kw_path(ks_ctx_calls[0], "side_state") == _CURRENT_BEHAVIOR_ORACLE
    assert _kw_path(ks_ctx_calls[0], "side_state") != _OWNER_NORM_ORACLE


def test_s10_t05_open_cells_remain_open_and_s11_absent() -> None:
    """S10-T05: listed OPEN cells stay open; S11 successor file exists; no execution/KS surface."""
    replay_tree = ast.parse(_REPLAY_SOURCE.read_text(encoding="utf-8"))
    mapper_fn = _function_def(replay_tree, "_canonical_scope_event_to_scope_event")
    mapper_src = ast.get_source_segment(_REPLAY_SOURCE.read_text(encoding="utf-8"), mapper_fn)
    assert mapper_src is not None
    for token in _OPEN_PRODUCER_TOKENS:
        assert token not in mapper_src
    this_src = Path(__file__).read_text(encoding="utf-8")
    assert "PENDING_ENTRY_ELIGIBILITY_CANONICALLY_DEFINED remains false" in this_src
    assert "quantity_status remains NOT_BOUND" in this_src
    assert "killswitch_blocked taxonomy" in this_src
    assert "composition-before-transition semantics" in this_src
    assert "Manifest-vs-Owner envelope" in this_src
    s11_path = (
        _REPO_ROOT
        / "tests/trading/test_s11_ks_mode_label_ne_action_post_29q_guard_conformance_v1.py"
    )
    assert s11_path.is_file()
    assert list(_REPO_ROOT.glob("tests/trading/test_s11_*.py")) == [s11_path]
    this_tree = ast.parse(this_src)
    imported = _imported_names(this_tree)
    assert all("src.execution" not in name for name in imported)
    assert all(not name.startswith("src.live") for name in imported)
    assert all("kill_switch_should_block_trading" not in name for name in imported)
    assert all("construct_live_execution_port_v1" not in name for name in imported)
    assert all("test_s11_" not in name for name in imported)
    s09_path = _REPO_ROOT / "tests/trading/test_s09_kill_all_state_machine_conformance_v1.py"
    assert s09_path.is_file()
