"""S11 KS mode-label ≠ action / post-29Q consumption-guard conformance.

BOUNDED_WORKPACKAGE=
MASTER_V2_DOUBLE_PLAY_BOUNDED_BEHAVIORAL_CONFORMANCE_VECTOR_SET_FROM_PROVEN_CELLS_ONLY_V1
SLICE=S11_KS_MODE_LABEL_NE_ACTION_POST_29Q_GUARD
PRIMARY_OWNER=trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0
TYPED_CONTRACT_OWNER=trading.master_v2.replay_execution_safety_contract_v1
REPLAY_CONSUMER=run_integrated_offline_trading_logic_replay_v1
KILLSWITCH_BINDER=bind_killswitch_boundary_offline_replay_evidence_v0
MODE_OWNER=derive_killswitch_boundary_mode_v0
SAFETY_CONTRACT=derive_replay_execution_safety_v1

Additive behavioral assertions only. No trading-semantics mutation.
Locks already proven V-KS-01..03 cells after S10 conserved the PARTIAL
same-tick binder split. Does not define new policy. Does not repair
inp.side_state vs next_side_state. Does not unify the Safety-kernel
killswitch_blocked flag with FILEGATE or SideState.KILL_ALL.
PENDING_ENTRY_ELIGIBILITY_CANONICALLY_DEFINED remains false.
quantity_status remains NOT_BOUND.
FILEGATE / execution / Live / S12 / 29P/29Q PLAN_ONLY / Golden Vector /
Replay producer of KILL_ALL_REQUIRED / composition-before-transition /
Manifest-vs-Owner envelope qualifier are out of this slice.

Epistemic:
- CANONICAL_AUTHORITY: Master Runbook §11.2.1.A/B SIDESTATE_KILL_ALL_ROLE=
  DOUBLE_PLAY_STRATEGY_STATE_MACHINE; POST_29Q_KS_ADJUDICATED_ROLE=
  POST_29Q_CONSUMPTION_GUARD; POST_29Q_KS_CAN_MUTATE_DECISION_OUTCOME=false;
  POST_29Q_KS_EXECUTION_PERMISSION_AUTHORITY=NONE; FILEGATE distinct
- FORENSIC_RAW_EVIDENCE: KS binder replace() does not write decision_outcome;
  evaluate_offline_killswitch_boundary_v0 hardcodes runtime/order/credential
  NONE; flatten/reduce/cancel are evidence booleans; Replay KS bind is after
  COI and after Safety; typed contract projects POST_29Q_CONSUMPTION_GUARD
- ALREADY_ADJUDICATED: S09 KILL_ALL SM / != flatten; S10 fanout PARTIAL
  binder split conserved; S08 ENTER requires armed direction
- Not claimed: binder next_side_state rewire; Replay KILL_ALL_REQUIRED
  producer; composition-before-transition; Manifest-vs-Owner; PENDING
  ENTER eligibility; quantity algebra; pre-29Q Safety skip-29Q (S12)

Path is tests/trading/ not tests/trading/master_v2/: the Economic Guard treats
tests/trading/master_v2/test_* as forbidden MASTER_V2 mutation surface.
Owner fixtures are reused via import of existing owner test helpers.
"""

from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome
from trading.master_v2.double_play_state import SideState
from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
    CREDENTIAL_EFFECT_NONE,
    ORDER_EFFECT_NONE,
    RUNTIME_AUTHORITY_EFFECT_NONE,
    KillSwitchBoundaryMode,
    KillSwitchBoundaryOfflineReplayContextV0,
    bind_killswitch_boundary_offline_replay_evidence_v0,
    derive_killswitch_boundary_mode_v0,
    evaluate_offline_killswitch_boundary_v0,
)
from trading.master_v2.replay_execution_safety_contract_v1 import (
    CONSUMPTION_GUARD_EFFECT_ENTER_BLOCK,
    POST_29Q_CONSUMPTION_GUARD_ROLE,
    derive_replay_execution_safety_v1,
    typed_post_29q_consumption_guard_blocks_enter_v1,
    typed_pre_29q_entry_blocked_v1,
)

from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPLAY_SOURCE = _REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_KS_SOURCE = (
    _REPO_ROOT / "src/trading/master_v2/killswitch_boundary_offline_replay_binding_adapter_v0.py"
)
_CONTRACT_SOURCE = _REPO_ROOT / "src/trading/master_v2/replay_execution_safety_contract_v1.py"
_BIND_OWNER = "bind_killswitch_boundary_offline_replay_evidence_v0"
_SAFETY_BIND_OWNER = "bind_safety_kernel_offline_replay_evidence_v0"
_COI_BIND_OWNER = "bind_canonical_order_intent_offline_replay_evidence_v0"
_TYPED_OWNER = "derive_replay_execution_safety_v1"
_EVAL_OWNER = "evaluate_offline_killswitch_boundary_v0"
_EVIDENCE_ONLY_FLAGS = (
    "flatten_only",
    "reduce_only",
    "cancel_only",
    "emergency_flatten_boundary_only",
    "reduce_to_flat_boundary_only",
    "cancel_pending_boundary_only",
)
_ABSENT_ACTION_TOKENS = ("cancel_all", "flatten_position", "FILEGATE_KILLED")
_FILEGATE_TOKENS = (
    "kill_switch_should_block_trading",
    "KillSwitchState",
    "StatePersistence",
    "PEAK_KILL_SWITCH",
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
    if isinstance(node.func, ast.Name):
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


def _replace_keywords(fn: ast.FunctionDef) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and _call_name(node) == "replace":
            names.update(kw.arg for kw in node.keywords if kw.arg is not None)
    return names


def _ks_ctx(**overrides: object) -> KillSwitchBoundaryOfflineReplayContextV0:
    payload = dict(overrides)
    return KillSwitchBoundaryOfflineReplayContextV0(**payload)


def _kw_const(call: ast.Call, keyword: str) -> str | None:
    for kw in call.keywords:
        if kw.arg != keyword:
            continue
        value = kw.value
        if isinstance(value, ast.Name):
            return value.id
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return value.value
    return None


def test_s11_t01_flatten_reduce_cancel_fields_are_evidence_only() -> None:
    """S11-T01 / V-KS-01: flatten/reduce/cancel are evidence flags; authority NONE."""
    flatten_ctx = _ks_ctx(
        boundary_mode=KillSwitchBoundaryMode.EMERGENCY_FLATTEN,
        killswitch_active=True,
    )
    reduce_ctx = _ks_ctx(
        boundary_mode=KillSwitchBoundaryMode.REDUCE_TO_FLAT,
        killswitch_active=True,
    )
    cancel_ctx = _ks_ctx(
        boundary_mode=KillSwitchBoundaryMode.CANCEL_PENDING,
        killswitch_active=True,
    )
    flatten_ks = evaluate_offline_killswitch_boundary_v0(
        flatten_ctx, decision_outcome=DecisionOutcome.ENTER_LONG.value
    )
    reduce_ks = evaluate_offline_killswitch_boundary_v0(reduce_ctx)
    cancel_ks = evaluate_offline_killswitch_boundary_v0(cancel_ctx)
    flatten_typed = derive_replay_execution_safety_v1(killswitch_boundary=flatten_ks)
    reduce_typed = derive_replay_execution_safety_v1(killswitch_boundary=reduce_ks)
    cancel_typed = derive_replay_execution_safety_v1(killswitch_boundary=cancel_ks)

    assert flatten_ks.emergency_flatten_boundary_only is True
    assert flatten_ks.reduce_to_flat_boundary_only is True
    assert flatten_typed.flatten_only is True
    assert reduce_typed.reduce_only is True
    assert cancel_typed.cancel_only is True
    for boundary in (flatten_ks, reduce_ks, cancel_ks):
        assert boundary.runtime_authority_effect == RUNTIME_AUTHORITY_EFFECT_NONE
        assert boundary.order_effect == ORDER_EFFECT_NONE
        assert boundary.credential_effect == CREDENTIAL_EFFECT_NONE
    for typed in (flatten_typed, reduce_typed, cancel_typed):
        assert typed.runtime_authority_effect == RUNTIME_AUTHORITY_EFFECT_NONE

    ks_src = _KS_SOURCE.read_text(encoding="utf-8")
    ks_tree = ast.parse(ks_src)
    eval_fn = _function_def(ks_tree, _EVAL_OWNER)
    eval_calls = [call for call in _ordered_calls(eval_fn) if _call_name(call) is not None]
    ctor_calls = [
        call
        for call in eval_calls
        if _call_name(call) == "KillSwitchBoundaryOfflineReplayBoundaryV0"
    ]
    assert len(ctor_calls) == 1
    assert _kw_const(ctor_calls[0], "runtime_authority_effect") == "RUNTIME_AUTHORITY_EFFECT_NONE"
    assert _kw_const(ctor_calls[0], "order_effect") == "ORDER_EFFECT_NONE"
    assert _kw_const(ctor_calls[0], "credential_effect") == "CREDENTIAL_EFFECT_NONE"

    contract_src = _CONTRACT_SOURCE.read_text(encoding="utf-8")
    for field in ("flatten_only", "reduce_only", "cancel_only"):
        assert field in contract_src


def test_s11_t02_mode_label_is_not_flatten_action_or_filegate() -> None:
    """S11-T02 / V-KS-02: EMERGENCY_FLATTEN is a mode label, not an action/FILEGATE write."""
    default_ctx = _ks_ctx()
    mode = derive_killswitch_boundary_mode_v0(
        safety_mode=default_ctx.safety_mode,
        side_state=SideState.KILL_ALL,
        trading_gate=default_ctx.trading_gate,
        safety_exit_signal=default_ctx.safety_exit_signal,
        hard_risk_reduction_signal=default_ctx.hard_risk_reduction_signal,
        safety_decision_allowed=True,
    )
    assert mode is KillSwitchBoundaryMode.EMERGENCY_FLATTEN
    assert mode.value == "emergency_flatten"

    ks = evaluate_offline_killswitch_boundary_v0(
        KillSwitchBoundaryOfflineReplayContextV0(
            boundary_mode=mode,
            killswitch_active=True,
            side_state=SideState.KILL_ALL,
        ),
        decision_outcome=DecisionOutcome.ENTER_LONG.value,
    )
    typed = derive_replay_execution_safety_v1(killswitch_boundary=ks)
    assert typed.emergency_mode == KillSwitchBoundaryMode.EMERGENCY_FLATTEN.value
    assert typed.flatten_only is True
    assert typed.runtime_authority_effect == RUNTIME_AUTHORITY_EFFECT_NONE
    assert ks.order_effect == ORDER_EFFECT_NONE
    assert "FILEGATE_KILLED" not in ks.reason_codes
    assert all("FILEGATE" not in code for code in ks.reason_codes)
    assert "killswitch_emergency_flatten" in ks.reason_codes

    ks_src = _KS_SOURCE.read_text(encoding="utf-8")
    for token in _ABSENT_ACTION_TOKENS:
        assert token not in ks_src
    for token in _FILEGATE_TOKENS:
        assert token not in ks_src
    this_src = Path(__file__).read_text(encoding="utf-8")
    for field in _EVIDENCE_ONLY_FLAGS:
        assert field in this_src


def test_s11_t03_post_29q_guard_holds_without_rewriting_outcome() -> None:
    """S11-T03 / V-KS-03: post-29Q HOLD/DENY; decision_outcome unchanged; not Safety."""
    replay = _run()
    original_outcome = replay.evidence.decision_outcome
    bound = bind_killswitch_boundary_offline_replay_evidence_v0(
        replay.evidence,
        context=KillSwitchBoundaryOfflineReplayContextV0(
            boundary_mode=KillSwitchBoundaryMode.EMERGENCY_FLATTEN,
            killswitch_active=True,
        ),
    )
    typed = derive_replay_execution_safety_v1(killswitch_boundary=bound.boundary)
    assert bound.evidence.decision_outcome == original_outcome
    assert bound.boundary.runtime_authority_effect == RUNTIME_AUTHORITY_EFFECT_NONE
    assert bound.boundary.order_effect == ORDER_EFFECT_NONE
    assert typed.post_29q_role == POST_29Q_CONSUMPTION_GUARD_ROLE
    assert typed.consumption_guard_effect == CONSUMPTION_GUARD_EFFECT_ENTER_BLOCK
    assert typed_post_29q_consumption_guard_blocks_enter_v1(typed) is True
    assert typed_pre_29q_entry_blocked_v1(typed) is False
    assert bound.evidence.execution_eligible is False

    ks_tree = ast.parse(_KS_SOURCE.read_text(encoding="utf-8"))
    bind_fn = _function_def(ks_tree, _BIND_OWNER)
    assert "decision_outcome" not in _replace_keywords(bind_fn)
    assert "execution_eligible" not in _replace_keywords(bind_fn)
    assert "order_effect" not in _replace_keywords(bind_fn)

    replay_src = _REPLAY_SOURCE.read_text(encoding="utf-8")
    replay_tree = ast.parse(replay_src)
    replay_fn = _function_def(replay_tree, "run_integrated_offline_trading_logic_replay_v1")
    calls = _ordered_calls(replay_fn)
    safety_calls = [call for call in calls if _call_name(call) == _SAFETY_BIND_OWNER]
    coi_calls = [call for call in calls if _call_name(call) == _COI_BIND_OWNER]
    ks_calls = [call for call in calls if _call_name(call) == _BIND_OWNER]
    typed_calls = [call for call in calls if _call_name(call) == _TYPED_OWNER]
    assert len(safety_calls) == 1
    assert len(coi_calls) == 1
    assert len(ks_calls) == 1
    assert len(typed_calls) == 1
    assert safety_calls[0].lineno < coi_calls[0].lineno
    assert coi_calls[0].lineno < ks_calls[0].lineno
    assert ks_calls[0].lineno < typed_calls[0].lineno


def test_s11_t04_s10_open_remainder_and_s12_absent() -> None:
    """S11-T04: S10 remainder stays open; S12 not started; no FILEGATE/execution surface."""
    s10_path = (
        _REPO_ROOT / "tests/trading/test_s10_kill_all_fanout_partial_same_tick_conformance_v1.py"
    )
    assert s10_path.is_file()
    s10_src = s10_path.read_text(encoding="utf-8")
    assert "Does not repair the PARTIAL/DEVIATES binder-input cell" in s10_src
    assert "PENDING_ENTRY_ELIGIBILITY_CANONICALLY_DEFINED remains false" in s10_src
    assert "quantity_status remains NOT_BOUND" in s10_src
    assert "composition-before-transition semantics" in s10_src
    assert "Manifest-vs-Owner envelope" in s10_src
    assert "KILL_ALL_REQUIRED" in s10_src
    assert list(_REPO_ROOT.glob("tests/trading/test_s12_*.py")) == []
    this_src = Path(__file__).read_text(encoding="utf-8")
    assert "PENDING_ENTRY_ELIGIBILITY_CANONICALLY_DEFINED remains false" in this_src
    assert "quantity_status remains NOT_BOUND" in this_src
    this_tree = ast.parse(this_src)
    imported = _imported_names(this_tree)
    assert all("src.execution" not in name for name in imported)
    assert all(not name.startswith("src.live") for name in imported)
    assert all("kill_switch_should_block_trading" not in name for name in imported)
    assert all("construct_live_execution_port_v1" not in name for name in imported)
    assert all("test_s12_" not in name for name in imported)
    assert all("capital_risk_sizing" not in name for name in imported)
