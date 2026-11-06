"""S09 KILL_ALL state-machine conformance.

BOUNDED_WORKPACKAGE=
MASTER_V2_DOUBLE_PLAY_BOUNDED_BEHAVIORAL_CONFORMANCE_VECTOR_SET_FROM_PROVEN_CELLS_ONLY_V1
SLICE=S09_KILL_ALL_STATE_MACHINE
PRIMARY_OWNER=trading.master_v2.double_play_state.transition_state
REPLAY_CONSUMER=run_integrated_offline_trading_logic_replay_v1
MAPPER_NON_PRODUCER=_canonical_scope_event_to_scope_event

Additive behavioral assertions only. No trading-semantics mutation.
Locks the existing transition_state KILL_ALL cells after S08 closed
ENTRY/EXIT ownership. Does not define new policy. Does not couple
SideState.KILL_ALL to Kill-Switch, FILEGATE, flatten, or fanout.
PENDING_ENTRY_ELIGIBILITY_CANONICALLY_DEFINED remains false.
quantity_status remains NOT_BOUND.
FILEGATE / execution / Live / S10+ / Kill-Switch mode-vs-action /
29P/29Q / Golden Vector / same-tick fanout are out of this slice.

Epistemic:
- CANONICAL_AUTHORITY: Master Runbook DOUBLE_PLAY_SIDE_STATE_OWNER=
  transition_state; SIDESTATE_KILL_ALL_ROLE=
  DOUBLE_PLAY_STRATEGY_STATE_MACHINE
- FORENSIC_RAW_EVIDENCE: transition_state KILL_ALL / ALREADY_KILL_ALL /
  IN_KILL_ALL; envelope-invalid precedes KILL_ALL_REQUIRED; Replay
  single transition_state join; mapper has no KILL_ALL_REQUIRED
- ALREADY_ADJUDICATED: S07 transition_state SideState ownership; S08
  ENTRY/EXIT HOLD/ENTER/EXIT/REDUCE/NO_IMPLICIT_FLIP
- Not claimed: Replay producer of KILL_ALL_REQUIRED; killswitch_blocked
  OR; flatten/liquidation action; reset/release/re-entry; quantity;
  PENDING ENTER eligibility

Path is tests/trading/ not tests/trading/master_v2/: the Economic Guard treats
tests/trading/master_v2/test_* as forbidden MASTER_V2 mutation surface.
Owner fixtures are reused via import of existing owner test helpers.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

from trading.master_v2.double_play_state import (
    RuntimeEnvelope,
    ScopeEvent,
    SideState,
    StaticHardLimits,
    TransitionDecision,
    transition_state,
)

from tests.trading.master_v2.test_double_play_state import (
    EMPTY_ST,
    GOOD_ENVELOPE,
    GOOD_RULES,
    _t,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run
from tests.trading.test_s05_c1_c3_vs_scope_confirmation_clock_conformance_v1 import (
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
_GENERATOR_SOURCE = _REPO_ROOT / "src/trading/master_v2/deterministic_scope_event_generator_v1.py"
_COMPOSE_ORACLE = "compose_double_play_decision"
_SM_OWNER = "transition_state"
_MAPPER = "_canonical_scope_event_to_scope_event"
_NON_KILL_ALL_STATES = tuple(state for state in SideState if state is not SideState.KILL_ALL)
_NON_KILL_ALL_EVENTS = tuple(
    event for event in ScopeEvent if event is not ScopeEvent.KILL_ALL_REQUIRED
)
_ABSENT_DOWNSTREAM_TOKENS = (
    "cancel_all",
    "cancel all",
    "flatten",
    "kill_switch",
    "killswitch",
    "ks_a",
    "ks_b",
    "integrity_state",
    "json.dump",
    "path.open",
    "write_text",
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


def _dict_string_keys(fn: ast.FunctionDef) -> set[str]:
    keys: set[str] = set()
    for node in ast.walk(fn):
        if not isinstance(node, ast.Dict):
            continue
        for key in node.keys:
            if isinstance(key, ast.Attribute):
                keys.add(key.attr)
            elif isinstance(key, ast.Constant) and isinstance(key.value, str):
                keys.add(key.value)
    return keys


def _replay_kwargs(*, side_state: SideState) -> dict[str, object]:
    return {
        "policies": _policies_confirm_once(),
        "price_path": (3500.0, 3570.0),
        "observation_acceptance_result": _injected_c1(),
        "scope_confirmation_state": _empty_scope_confirmation(),
        "confirmation_progress_session_id": _session(),
        "confirmation_progress_venue": "okx_eea",
        "confirmation_progress_instrument": _key(),
        "side_state": side_state,
    }


def test_s09_t01_replay_has_single_kill_all_sm_owner_join() -> None:
    """S09-T01: Replay has one transition_state join; mapper is not KILL_ALL producer."""
    replay_tree = ast.parse(_REPLAY_SOURCE.read_text(encoding="utf-8"))
    replay_fn = _function_def(replay_tree, "run_integrated_offline_trading_logic_replay_v1")
    sm_calls = [call for call in _ordered_calls(replay_fn) if _call_name(call) == _SM_OWNER]
    mapper_calls = [call for call in _ordered_calls(replay_fn) if _call_name(call) == _MAPPER]
    assert len(sm_calls) == 1
    assert len(mapper_calls) == 1
    defined = {
        node.name
        for node in ast.walk(replay_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert _SM_OWNER not in defined
    assert _MAPPER in defined
    imported = _imported_names(replay_tree)
    assert any(name.endswith(_SM_OWNER) for name in imported)
    assert all(_COMPOSE_ORACLE not in name for name in imported)
    assert all("src.execution" not in name for name in imported)
    assert all("kill_switch_should_block_trading" not in name for name in imported)

    join = sm_calls[0]
    assert _kw_path(join, "side_state") == "inp.side_state"
    assert _kw_path(join, "event") == "mapped_event"
    assert "selected_side" not in (_kw_path(join, "side_state") or "")

    mapper_fn = _function_def(replay_tree, _MAPPER)
    mapper_keys = _dict_string_keys(mapper_fn)
    assert "KILL_ALL_REQUIRED" not in mapper_keys
    assert "kill_all_required" not in mapper_keys
    assert "KILL_ALL" not in mapper_keys
    mapper_src = ast.get_source_segment(_REPLAY_SOURCE.read_text(encoding="utf-8"), mapper_fn)
    assert mapper_src is not None
    assert "KILL_ALL_REQUIRED" not in mapper_src
    assert "ScopeEvent.KILL_ALL" not in mapper_src

    gen_src = _GENERATOR_SOURCE.read_text(encoding="utf-8")
    assert "KILL_ALL_REQUIRED" not in gen_src
    assert "kill_all_required" not in gen_src


def test_s09_t02_kill_all_required_from_any_non_terminal_state() -> None:
    """S09-T02: KILL_ALL_REQUIRED from every non-KILL_ALL SideState → KILL_ALL."""
    for from_state in _NON_KILL_ALL_STATES:
        next_side, scope_after, decision = _t(from_state, ScopeEvent.KILL_ALL_REQUIRED, EMPTY_ST, 7)
        assert next_side is SideState.KILL_ALL
        assert decision.allowed is True
        assert decision.reason_code == "KILL_ALL"
        assert decision.live_authorization_granted is False
        assert isinstance(decision, TransitionDecision)
        assert scope_after.last_switch_tick == 7
        assert scope_after.now_tick == 7
        assert from_state is not SideState.KILL_ALL


def test_s09_t03_kill_all_required_is_idempotent_when_already_kill_all() -> None:
    """S09-T03: KILL_ALL + KILL_ALL_REQUIRED stays KILL_ALL / ALREADY_KILL_ALL."""
    seeded = replace(EMPTY_ST, last_switch_tick=3, now_tick=3)
    next_side, scope_after, decision = _t(
        SideState.KILL_ALL, ScopeEvent.KILL_ALL_REQUIRED, seeded, 11
    )
    assert next_side is SideState.KILL_ALL
    assert decision.allowed is True
    assert decision.reason_code == "ALREADY_KILL_ALL"
    assert decision.live_authorization_granted is False
    assert scope_after.last_switch_tick == 3
    assert scope_after.now_tick == 11
    assert scope_after.switches_in_window == seeded.switches_in_window


def test_s09_t04_kill_all_is_absorbing_no_reset_or_state_switch() -> None:
    """S09-T04: non-KILL_ALL_REQUIRED events cannot leave KILL_ALL; no reset."""
    seeded = replace(EMPTY_ST, last_switch_tick=4, chop_latched=True)
    for event in _NON_KILL_ALL_EVENTS:
        next_side, scope_after, decision = _t(SideState.KILL_ALL, event, seeded, 9)
        assert next_side is SideState.KILL_ALL
        assert decision.allowed is False
        assert decision.reason_code == "IN_KILL_ALL"
        assert decision.live_authorization_granted is False
        assert scope_after.last_switch_tick == 4
        assert next_side is not SideState.NEUTRAL_OBSERVE
        assert next_side not in (
            SideState.LONG_ACTIVE,
            SideState.SHORT_ACTIVE,
            SideState.SWITCH_LONG_TO_SHORT_PENDING,
            SideState.SWITCH_SHORT_TO_LONG_PENDING,
            SideState.LONG_ARMED,
            SideState.SHORT_ARMED,
            SideState.CHOP_GUARD_BLOCK,
        )
    noop_side, _, noop_decision = _t(SideState.KILL_ALL, ScopeEvent.NOOP, seeded, 9)
    assert noop_side is SideState.KILL_ALL
    assert noop_decision.reason_code != "NOOP"
    assert noop_decision.reason_code != "CHOP_CLEAR"


def test_s09_t05_replay_consumes_absorbing_kill_all_without_override() -> None:
    """S09-T05: Replay join keeps KILL_ALL; confirmed/NOOP path cannot override."""
    replay = _run(**_replay_kwargs(side_state=SideState.KILL_ALL))
    assert replay.intermediate is not None
    switch = replay.intermediate.state_switch
    decision = replay.intermediate.transition_decision
    assert switch.previous_side_state == SideState.KILL_ALL.value
    assert switch.next_side_state == SideState.KILL_ALL.value
    assert switch.transition_allowed is False
    assert switch.transition_reason_code == "IN_KILL_ALL"
    assert decision is not None
    assert decision.reason_code == "IN_KILL_ALL"
    assert decision.allowed is False
    assert replay.intermediate.scope_event.event_type.value != ScopeEvent.KILL_ALL_REQUIRED.value


def test_s09_t06_state_is_not_downstream_action_and_replay_does_not_invent_kill_all() -> None:
    """S09-T06: SM has no flatten/KS write; Replay NOOP does not invent KILL_ALL."""
    state_src = _STATE_SOURCE.read_text(encoding="utf-8")
    lowered = state_src.lower()
    for token in _ABSENT_DOWNSTREAM_TOKENS:
        assert token not in lowered, token
    state_tree = ast.parse(state_src)
    sm_fn = _function_def(state_tree, _SM_OWNER)
    assert all(_call_name(call) != "open" for call in _ordered_calls(sm_fn))
    owner_side, _, owner_decision = _t(
        SideState.LONG_ACTIVE, ScopeEvent.KILL_ALL_REQUIRED, EMPTY_ST, 0
    )
    assert owner_side is SideState.KILL_ALL
    assert owner_decision.live_authorization_granted is False

    replay = _run(**_replay_kwargs(side_state=SideState.LONG_ARMED))
    assert replay.intermediate is not None
    switch = replay.intermediate.state_switch
    assert switch.previous_side_state == SideState.LONG_ARMED.value
    assert switch.next_side_state != SideState.KILL_ALL.value
    assert switch.transition_reason_code != "KILL_ALL"
    assert switch.transition_reason_code != "ALREADY_KILL_ALL"
    assert replay.intermediate.transition_decision is not None
    assert replay.intermediate.transition_decision.reason_code == "NOOP"


def test_s09_t07_invalid_envelope_or_rules_block_kill_all_required() -> None:
    """S09-T07: envelope/rules invalid precedes KILL_ALL_REQUIRED; no invented entry."""
    live_env = RuntimeEnvelope(static=GOOD_ENVELOPE.static, live_authorization=True)
    live_side, _, live_decision = transition_state(
        side_state=SideState.LONG_ACTIVE,
        event=ScopeEvent.KILL_ALL_REQUIRED,
        scope_state=EMPTY_ST,
        rules=GOOD_RULES,
        envelope=live_env,
        now_tick=1,
    )
    assert live_side is SideState.LONG_ACTIVE
    assert live_decision.allowed is False
    assert live_decision.reason_code == "ENVELOPE_OR_RULES_INVALID"
    assert live_side is not SideState.KILL_ALL

    bad_static = StaticHardLimits(
        max_notional=1.0,
        max_leverage=1.0,
        max_switches_per_window=100,
        min_band_width=0.0,
        max_band_width=100.0,
    )
    bad_env = RuntimeEnvelope(static=bad_static, live_authorization=False)
    bad_side, _, bad_decision = transition_state(
        side_state=SideState.SHORT_ACTIVE,
        event=ScopeEvent.KILL_ALL_REQUIRED,
        scope_state=EMPTY_ST,
        rules=GOOD_RULES,
        envelope=bad_env,
        now_tick=1,
    )
    assert bad_side is SideState.SHORT_ACTIVE
    assert bad_decision.reason_code == "ENVELOPE_OR_RULES_INVALID"

    already_side, _, already_decision = transition_state(
        side_state=SideState.KILL_ALL,
        event=ScopeEvent.KILL_ALL_REQUIRED,
        scope_state=EMPTY_ST,
        rules=replace(GOOD_RULES, min_band_width=-1.0),
        envelope=GOOD_ENVELOPE,
        now_tick=2,
    )
    assert already_side is SideState.KILL_ALL
    assert already_decision.allowed is False
    assert already_decision.reason_code == "ENVELOPE_OR_RULES_INVALID"
    assert already_decision.reason_code != "ALREADY_KILL_ALL"


def test_s09_t08_s10_absent_and_open_items_unchanged() -> None:
    """S09-T08: S10 successor file exists; S08 open items remain; no execution/KS surface."""
    s10_path = (
        _REPO_ROOT / "tests/trading/test_s10_kill_all_fanout_partial_same_tick_conformance_v1.py"
    )
    assert s10_path.is_file()
    assert list(_REPO_ROOT.glob("tests/trading/test_s10_*.py")) == [s10_path]
    s08_path = _REPO_ROOT / "tests/trading/test_s08_entry_exit_conformance_v1.py"
    assert s08_path.is_file()
    this_src = Path(__file__).read_text(encoding="utf-8")
    assert "PENDING_ENTRY_ELIGIBILITY_CANONICALLY_DEFINED remains false" in this_src
    assert "quantity_status remains NOT_BOUND" in this_src
    this_tree = ast.parse(this_src)
    imported = _imported_names(this_tree)
    assert all(_COMPOSE_ORACLE not in name for name in imported)
    assert all("src.execution" not in name for name in imported)
    assert all(not name.startswith("src.live") for name in imported)
    assert all("kill_switch_should_block_trading" not in name for name in imported)
    assert all("construct_live_execution_port_v1" not in name for name in imported)
    assert all("test_s10_" not in name for name in imported)
