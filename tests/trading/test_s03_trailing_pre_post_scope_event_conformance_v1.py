"""S03 trailing PRE/POST and ScopeEvent generation/mapping conformance.

BOUNDED_WORKPACKAGE=
MASTER_V2_DOUBLE_PLAY_BOUNDED_BEHAVIORAL_CONFORMANCE_VECTOR_SET_FROM_PROVEN_CELLS_ONLY_V1
SLICE=S03_TRAILING_PRE_POST_SCOPE_EVENT
PRIMARY_OWNER=update_dynamic_boundaries
SCOPE_EVENT_OWNER=generate_deterministic_scope_event
MAPPING_OWNER=integrated_offline_trading_logic_replay_v1._canonical_scope_event_to_scope_event

Additive behavioral assertions only. No trading-semantics mutation.
PRE trailing uses current ActiveSide. POST trailing uses next ActiveSide.
ScopeEventEvidenceV1 is evidentiary. Mapped ScopeEvent is not an S03 SM oracle.
FILEGATE / execution / Live / S04 / S05 / S07 are out of this slice.

Epistemic:
- CANONICAL_AUTHORITY: update_dynamic_boundaries; generate_deterministic_scope_event
- FORENSIC_RAW_EVIDENCE: Replay PRE/POST call sites; generator NOOP; ADVERSE mapping
- ALREADY_ADJUDICATED: V-TR-01/02; V-SE-01 generation; V-SE-02 mapping;
  init scope_event_generated=false; derive_scope_event_distances_v1 unbound
- Not claimed: transition_state hold; CANDIDATE_ACK; confirmation clocks;
  CHOP emission; Model-C distances; compose_double_play_decision as owner

Path is tests/trading/ not tests/trading/master_v2/: the Economic Guard treats
tests/trading/master_v2/test_* as forbidden MASTER_V2 mutation surface.
Owner fixtures are reused via import of existing owner test helpers.
"""

from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.deterministic_scope_event_generator_v1 import (
    CanonicalScopeEventType,
    ScopeCandidateKind,
)
from trading.master_v2.double_play_state import (
    ActiveSide,
    DynamicScopeRules,
    RuntimeEnvelope,
    RuntimeScopeState,
    ScopeEvent,
    SideState,
    StaticHardLimits,
    derive_active_side,
    update_dynamic_boundaries,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    _canonical_scope_event_to_scope_event,
)

from tests.trading.master_v2.test_canonical_scope_initialization_v1 import (
    _initialize,
)
from tests.trading.master_v2.test_deterministic_scope_event_generator_v1 import (
    _generate,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPLAY_SOURCE = _REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_STATE_SOURCE = _REPO_ROOT / "src/trading/master_v2/double_play_state.py"
_INIT_SOURCE = _REPO_ROOT / "src/trading/master_v2/canonical_scope_initialization_v1.py"
_COMPOSE_ORACLE = "compose_double_play_decision"
_DERIVE_DISTANCES = "derive_scope_event_distances_v1"

_ENVELOPE = RuntimeEnvelope(
    static=StaticHardLimits(
        max_notional=1.0,
        max_leverage=1.0,
        max_switches_per_window=100,
        min_band_width=1.0,
        max_band_width=100.0,
    ),
    live_authorization=False,
)
_RULES = DynamicScopeRules(
    min_band_width=1.0,
    max_band_width=50.0,
    min_switch_cooldown_ticks=0,
    max_switches_per_window=1_000_000,
    volatility_estimate=0.1,
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


def _kw(call: ast.Call, key: str) -> ast.AST | None:
    for keyword in call.keywords:
        if keyword.arg == key:
            return keyword.value
    return None


def _name_or_attr(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_name_or_attr(node.value)}.{node.attr}"
    return ""


def _assign_value(fn: ast.AST, target: str) -> ast.AST | None:
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign):
            for assigned in node.targets:
                if isinstance(assigned, ast.Name) and assigned.id == target:
                    return node.value
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == target:
                return node.value
    return None


def _trail(
    *,
    mark_price: float,
    side: ActiveSide,
    st: RuntimeScopeState,
) -> RuntimeScopeState:
    out = update_dynamic_boundaries(
        mark_price=mark_price,
        side=side,
        st=st,
        rules=_RULES,
        env=_ENVELOPE,
    )
    assert isinstance(out, RuntimeScopeState)
    assert not isinstance(out, SideState)
    return out


def test_s03_t01_v_tr_01_same_side_pre_post_does_not_loosen() -> None:
    """S03-T01 / V-TR-01: PRE current ActiveSide; same-side POST does not loosen."""
    prior = RuntimeScopeState(anchor_price=100.0, now_tick=0)

    pre_long = _trail(mark_price=120.0, side=ActiveSide.LONG, st=prior)
    assert pre_long.anchor_price == 120.0
    assert pre_long.current_downscope_boundary < pre_long.anchor_price
    post_long = _trail(mark_price=110.0, side=ActiveSide.LONG, st=pre_long)
    assert post_long.anchor_price == 120.0

    pre_short = _trail(mark_price=80.0, side=ActiveSide.SHORT, st=prior)
    assert pre_short.anchor_price == 80.0
    assert pre_short.current_upscope_boundary > pre_short.anchor_price
    post_short = _trail(mark_price=90.0, side=ActiveSide.SHORT, st=pre_short)
    assert post_short.anchor_price == 80.0


def test_s03_t02_v_tr_02_post_uses_next_active_side_not_current() -> None:
    """S03-T02 / V-TR-02: POST follows next ActiveSide; CURRENT != NEXT discriminator."""
    prior = RuntimeScopeState(anchor_price=100.0, now_tick=0)
    pre_long = _trail(mark_price=120.0, side=ActiveSide.LONG, st=prior)
    assert pre_long.anchor_price == 120.0

    post_opposite = _trail(mark_price=110.0, side=ActiveSide.SHORT, st=pre_long)
    post_same = _trail(mark_price=110.0, side=ActiveSide.LONG, st=pre_long)
    assert post_same.anchor_price == 120.0
    assert post_opposite.anchor_price == 110.0
    assert post_opposite.anchor_price != post_same.anchor_price

    pending = SideState.SWITCH_LONG_TO_SHORT_PENDING
    assert derive_active_side(pending) is ActiveSide.NEUTRAL
    frozen = _trail(
        mark_price=180.0,
        side=derive_active_side(pending),
        st=pre_long,
    )
    assert frozen.anchor_price == pre_long.anchor_price
    assert frozen.current_downscope_boundary == pre_long.current_downscope_boundary
    assert frozen.current_upscope_boundary == pre_long.current_upscope_boundary


def test_s03_t03_v_se_01_generator_noop_evidence_without_sm_claim() -> None:
    """S03-T03 / V-SE-01 generation only: no-match still emits NOOP evidence."""
    scope = _generate(current_price=3500.0).current_scope_ref
    evidence = _generate(current_price=3500.0, current_scope=scope)
    assert evidence.event_type is CanonicalScopeEventType.NOOP
    assert evidence.current_scope_ref is scope
    assert evidence.authority_effect == "NONE"
    assert evidence.runtime_effect == "NONE"
    assert evidence.order_effect == "NONE"
    assert evidence.position_effect == "NONE"

    init = _initialize()
    assert init.scope_event_generated is False

    init_tree = ast.parse(_INIT_SOURCE.read_text(encoding="utf-8"))
    result_cls = next(
        node
        for node in ast.walk(init_tree)
        if isinstance(node, ast.ClassDef) and node.name == "CanonicalScopeInitializationResultV1"
    )
    generated_field = next(
        node
        for node in result_cls.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "scope_event_generated"
    )
    assert isinstance(generated_field.value, ast.Constant)
    assert generated_field.value.value is False

    replay_fn = _function_def(
        ast.parse(_REPLAY_SOURCE.read_text(encoding="utf-8")),
        "run_integrated_offline_trading_logic_replay_v1",
    )
    ordered = _ordered_calls(replay_fn)
    updates = [call for call in ordered if _call_name(call) == "update_dynamic_boundaries"]
    generate = next(
        call for call in ordered if _call_name(call) == "generate_deterministic_scope_event"
    )
    transition = next(call for call in ordered if _call_name(call) == "transition_state")
    assert len(updates) >= 2
    assert updates[0].lineno < generate.lineno < transition.lineno < updates[1].lineno


def test_s03_t04_v_se_02_adverse_without_downscope_maps_scope_unknown() -> None:
    """S03-T04 / V-SE-02 mapping only: ADVERSE without downscope -> SCOPE_UNKNOWN."""
    evidence = _generate(current_price=3410.0)
    assert evidence.event_type is CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE
    assert ScopeCandidateKind.DOWNSCOPE.value not in evidence.matched_conditions
    mapped = _canonical_scope_event_to_scope_event(
        evidence.event_type,
        matched_conditions=tuple(evidence.matched_conditions),
    )
    assert mapped is ScopeEvent.SCOPE_UNKNOWN


def test_s03_t05_v_neg_replay_pre_post_wiring_and_unbound_distances() -> None:
    """S03-T05 / V-NEG: Replay PRE/POST side sources; trailing is not SideState writer."""
    replay_tree = ast.parse(_REPLAY_SOURCE.read_text(encoding="utf-8"))
    state_tree = ast.parse(_STATE_SOURCE.read_text(encoding="utf-8"))
    replay_fn = _function_def(replay_tree, "run_integrated_offline_trading_logic_replay_v1")
    trail_fn = _function_def(state_tree, "update_dynamic_boundaries")

    trail_assign = _assign_value(replay_fn, "active_for_trail")
    assert isinstance(trail_assign, ast.Call)
    assert _call_name(trail_assign) == "derive_active_side"
    assert _name_or_attr(trail_assign.args[0]) == "inp.side_state"

    updates = [
        call
        for call in _ordered_calls(replay_fn)
        if _call_name(call) == "update_dynamic_boundaries"
    ]
    assert len(updates) >= 2
    pre_side = _kw(updates[0], "side")
    post_side = _kw(updates[1], "side")
    assert isinstance(pre_side, ast.Name)
    assert pre_side.id == "active_for_trail"
    assert isinstance(post_side, ast.Call)
    assert _call_name(post_side) == "derive_active_side"
    assert _name_or_attr(post_side.args[0]) == "next_side_state"

    imported = _imported_names(replay_tree)
    assert all(_DERIVE_DISTANCES not in name for name in imported)
    assert all(_call_name(call) != _DERIVE_DISTANCES for call in _ordered_calls(replay_fn))
    assert all(_COMPOSE_ORACLE not in name for name in imported)
    assert all(_call_name(call) != _COMPOSE_ORACLE for call in _ordered_calls(replay_fn))

    assert isinstance(trail_fn.returns, ast.Name)
    assert trail_fn.returns.id == "RuntimeScopeState"
    assert all(_call_name(call) != "transition_state" for call in _ordered_calls(trail_fn))
    this_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    assert all(_COMPOSE_ORACLE not in name for name in _imported_names(this_tree))
    assert all(_call_name(call) != _COMPOSE_ORACLE for call in _ordered_calls(this_tree))
    assert all(_call_name(call) != "transition_state" for call in _ordered_calls(this_tree))
