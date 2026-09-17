"""S12 29P / pre-29Q Safety / 29Q PLAN_ONLY conformance.

BOUNDED_WORKPACKAGE=
MASTER_V2_DOUBLE_PLAY_BOUNDED_BEHAVIORAL_CONFORMANCE_VECTOR_SET_FROM_PROVEN_CELLS_ONLY_V1
SLICE=S12_29P_PRE_29Q_SAFETY_29Q_PLAN_ONLY
PRIMARY_OWNER=trading.master_v2.integrated_offline_trading_logic_replay_v1
SIZING_BINDER=bind_capital_risk_sizing_offline_replay_evidence_v0
SAFETY_BINDER=bind_safety_kernel_offline_replay_evidence_v0
INTENT_BINDER=bind_canonical_order_intent_offline_replay_evidence_v0
TYPED_CONTRACT_OWNER=trading.master_v2.replay_execution_safety_contract_v1

Additive behavioral assertions only. No trading-semantics mutation.
Locks already proven V-29P-01..02, V-SAF-01, and V-29Q-01 cells after S11
separated post-29Q KS consumption-guard from pre-29Q Safety. Does not
define new policy. Does not unify Safety-kernel killswitch_blocked with
FILEGATE or SideState.KILL_ALL. Does not repair the S10 PARTIAL binder
split. PENDING_ENTRY_ELIGIBILITY_CANONICALLY_DEFINED remains false.
FILEGATE / execution / Live / S13 recon-negative / Golden Vector /
composition-before-transition / Manifest-vs-Owner envelope qualifier
are out of this slice.

Epistemic:
- CANONICAL_AUTHORITY: Master Runbook §11.2.1.A/B SAFETY_ORDER=
  29P_THEN_SAFETY_THEN_29Q; NO_29Q_BEFORE_SAFETY=true; 29Q_PLAN_ONLY=true;
  REPLAY_SAFETY_ROLE=PRE_29Q_DECISION_ADMISSION; POST_29Q_KS is not Safety
- FORENSIC_RAW_EVIDENCE: Replay bind order 29P then Safety then 29Q;
  enter_blocked_by_safety skips COI only for ENTER outcomes; HOLD is
  non-actionable and leaves quantity NOT_BOUND; COI submission flags stay
  false
- ALREADY_ADJUDICATED: S11 V-KS-01..03 CONFORMS (mode-label ≠ action;
  post-29Q HOLD/DENY without outcome rewrite; typed_pre_29q False on KS-only)
- Not claimed: Safety-kernel/Kill-Switch blocked-flag unification;
  binder next_side_state rewire; Replay KILL_ALL_REQUIRED producer;
  PENDING ENTER eligibility; FILEGATE; S13 recon/negative suite

Path is tests/trading/ not tests/trading/master_v2/: the Economic Guard treats
tests/trading/master_v2/test_* as forbidden MASTER_V2 mutation surface.
Owner fixtures are reused via import of existing owner test helpers.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from src.governance.canonical_order_intent_v1 import IntentAction
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    RISK_SIZING_EFFECT_BOUND_OFFLINE,
    RISK_SIZING_EFFECT_NONE,
)
from trading.master_v2.capital_risk_sizing_safety_intent_restore_v1 import (
    safety_context_from_integrated_replay_input_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    ExistingPositionSide,
    PositionState,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.replay_execution_safety_contract_v1 import (
    derive_replay_execution_safety_v1,
    typed_post_29q_consumption_guard_blocks_enter_v1,
    typed_pre_29q_entry_blocked_v1,
)
from trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 import (
    evaluate_offline_safety_kernel_boundary_v0,
)

from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run
from tests.trading.master_v2.test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1 import (
    _confirmed_replay_input,
    _exit_replay_input,
    _patch_replay_owners,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPLAY_SOURCE = _REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_CRS_BIND_OWNER = "bind_capital_risk_sizing_offline_replay_evidence_v0"
_SAFETY_BIND_OWNER = "bind_safety_kernel_offline_replay_evidence_v0"
_COI_BIND_OWNER = "bind_canonical_order_intent_offline_replay_evidence_v0"
_KS_BIND_OWNER = "bind_killswitch_boundary_offline_replay_evidence_v0"
_QUANTITY_STATUS_NOT_BOUND = "NOT_BOUND"
_ENTER_OUTCOMES = frozenset({DecisionOutcome.ENTER_LONG.value, DecisionOutcome.ENTER_SHORT.value})
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


def _replay_fn() -> ast.FunctionDef:
    replay_tree = ast.parse(_REPLAY_SOURCE.read_text(encoding="utf-8"))
    return _function_def(replay_tree, "run_integrated_offline_trading_logic_replay_v1")


def test_s12_t01_actionable_enter_sizes_without_side_rewrite() -> None:
    """S12-T01 / V-29P-01 + V-29Q-01: ENTER sizes; side unchanged; COI PLAN_ONLY."""
    result = run_integrated_offline_trading_logic_replay_v1(_confirmed_replay_input(side="LONG"))
    assert result.intermediate is not None
    evidence = result.evidence
    composition = result.intermediate.composition_result
    assert evidence.decision_outcome == DecisionOutcome.ENTER_LONG.value
    assert evidence.selected_side == composition.selected_side.value
    assert evidence.risk_sizing_effect == RISK_SIZING_EFFECT_BOUND_OFFLINE
    assert evidence.quantity_status != _QUANTITY_STATUS_NOT_BOUND
    intent = result.intermediate.canonical_order_intent
    assert intent is not None
    assert intent.intent_action == IntentAction.ENTER_LONG.value
    assert intent.submission_authorized is False
    assert intent.execution_eligible is False

    replay_fn = _replay_fn()
    calls = [call for call in _ordered_calls(replay_fn) if _call_name(call) is not None]
    crs = [call for call in calls if _call_name(call) == _CRS_BIND_OWNER]
    safety = [call for call in calls if _call_name(call) == _SAFETY_BIND_OWNER]
    coi = [call for call in calls if _call_name(call) == _COI_BIND_OWNER]
    assert len(crs) == 1
    assert len(safety) == 1
    assert len(coi) == 1
    assert crs[0].lineno < safety[0].lineno < coi[0].lineno


def test_s12_t02_hold_is_not_quantity_bound() -> None:
    """S12-T02 / V-29P-02: non-actionable HOLD is not 29P-bound and produces no COI."""
    replay = _run(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        side_state=SideState.LONG_ACTIVE,
    )
    assert replay.intermediate is not None
    assert replay.evidence.decision_outcome == DecisionOutcome.HOLD.value
    assert replay.evidence.quantity_status == _QUANTITY_STATUS_NOT_BOUND
    assert replay.evidence.risk_sizing_effect == RISK_SIZING_EFFECT_NONE
    assert replay.intermediate.canonical_order_intent is None
    assert (
        replay.evidence.selected_side == replay.intermediate.composition_result.selected_side.value
    )


def test_s12_t03_pre_29q_enter_hard_block_skips_29q(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """S12-T03 / V-SAF-01: ENTER + Safety hard-block skips 29Q/COI; outcome unchanged.

    Hard-block is injected at the Safety binder, not via EntryExit SafetyMode.
    Owner fixture `_patch_replay_owners(force_safety_hard_block=True)` is the
    already-proven skip-29Q oracle.
    """
    inp = _confirmed_replay_input(side="LONG")
    order, counts = _patch_replay_owners(monkeypatch, force_safety_hard_block=True)
    result = run_integrated_offline_trading_logic_replay_v1(inp)
    assert result.evidence.decision_outcome == DecisionOutcome.ENTER_LONG.value
    assert result.evidence.decision_outcome in _ENTER_OUTCOMES
    assert "29Q" not in order
    assert order == ["29P", "SAFETY", "RECON", "KS"]
    assert counts["29P"] == 1
    assert counts["SAFETY"] == 1
    assert counts["29Q"] == 0
    assert result.intermediate is not None
    assert result.intermediate.canonical_order_intent is None
    assert "entry_blocked_by_safety_kernel_boundary" in result.evidence.reason_codes

    blocked_ctx = replace(
        safety_context_from_integrated_replay_input_v1(inp),
        killswitch_blocked=True,
        safety_decision_allowed=False,
    )
    boundary = evaluate_offline_safety_kernel_boundary_v0(
        blocked_ctx, decision_outcome=result.evidence.decision_outcome
    )
    typed = derive_replay_execution_safety_v1(safety_boundary=boundary)
    assert typed_pre_29q_entry_blocked_v1(typed) is True
    assert typed_post_29q_consumption_guard_blocks_enter_v1(typed) is False
    assert boundary.runtime_authority_effect == "NONE"

    replay_src = _REPLAY_SOURCE.read_text(encoding="utf-8")
    assert "enter_blocked_by_safety" in replay_src
    assert "if not enter_blocked_by_safety:" in replay_src
    replay_fn = _replay_fn()
    bind_body = ast.get_source_segment(replay_src, replay_fn)
    assert bind_body is not None
    assert bind_body.index(_SAFETY_BIND_OWNER) < bind_body.index("enter_blocked_by_safety")
    assert bind_body.index("if not enter_blocked_by_safety:") < bind_body.index(_COI_BIND_OWNER)


def test_s12_t04_exit_is_not_blanket_killed_by_pre_29q_safety(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """S12-T04 / V-SAF-01 + V-29P-01: EXIT still reaches 29Q; side unchanged."""
    order, counts = _patch_replay_owners(monkeypatch)
    result = run_integrated_offline_trading_logic_replay_v1(_exit_replay_input())
    assert result.evidence.decision_outcome == DecisionOutcome.EXIT.value
    assert result.evidence.decision_outcome not in _ENTER_OUTCOMES
    assert counts["29P"] == 1
    assert counts["SAFETY"] == 1
    assert counts["29Q"] == 1
    assert "SAFETY" in order and "29Q" in order
    assert order.index("SAFETY") < order.index("29Q")
    assert result.intermediate is not None
    assert (
        result.evidence.selected_side == result.intermediate.composition_result.selected_side.value
    )
    intent = result.intermediate.canonical_order_intent
    if intent is not None:
        assert intent.intent_action == IntentAction.EXIT.value
        assert intent.submission_authorized is False
        assert intent.execution_eligible is False
        assert intent.intent_action not in {
            IntentAction.ENTER_LONG.value,
            IntentAction.ENTER_SHORT.value,
        }


def test_s12_t05_open_remainder_and_s13_successor_present() -> None:
    """S12-T05: S10/S11 remainder stays open; S13 successor file exists; no FILEGATE/execution."""
    s11_path = (
        _REPO_ROOT
        / "tests/trading/test_s11_ks_mode_label_ne_action_post_29q_guard_conformance_v1.py"
    )
    assert s11_path.is_file()
    s11_src = s11_path.read_text(encoding="utf-8")
    assert "Does not unify the Safety-kernel" in s11_src
    assert "PENDING_ENTRY_ELIGIBILITY_CANONICALLY_DEFINED remains false" in s11_src
    s10_path = (
        _REPO_ROOT / "tests/trading/test_s10_kill_all_fanout_partial_same_tick_conformance_v1.py"
    )
    s10_src = s10_path.read_text(encoding="utf-8")
    assert "Does not repair the PARTIAL/DEVIATES binder-input cell" in s10_src
    assert "composition-before-transition semantics" in s10_src
    assert "Manifest-vs-Owner envelope" in s10_src
    assert "KILL_ALL_REQUIRED" in s10_src
    this_src = Path(__file__).read_text(encoding="utf-8")
    assert "PENDING_ENTRY_ELIGIBILITY_CANONICALLY_DEFINED remains false" in this_src
    assert "Safety-kernel/Kill-Switch blocked-flag unification" in this_src
    s13_path = (
        _REPO_ROOT / "tests/trading/test_s13_recon_negative_suite_invariants_conformance_v1.py"
    )
    assert s13_path.is_file()
    assert list(_REPO_ROOT.glob("tests/trading/test_s13_*.py")) == [s13_path]
    this_tree = ast.parse(this_src)
    imported = _imported_names(this_tree)
    assert all("src.execution" not in name for name in imported)
    assert all(not name.startswith("src.live") for name in imported)
    assert all("kill_switch_should_block_trading" not in name for name in imported)
    assert all("construct_live_execution_port_v1" not in name for name in imported)
    assert all("test_s13_" not in name for name in imported)
    replay_src = _REPLAY_SOURCE.read_text(encoding="utf-8")
    for token in _FILEGATE_TOKENS:
        assert token not in replay_src
    replay_fn = _replay_fn()
    calls = [call for call in _ordered_calls(replay_fn) if _call_name(call) is not None]
    ks = [call for call in calls if _call_name(call) == _KS_BIND_OWNER]
    coi = [call for call in calls if _call_name(call) == _COI_BIND_OWNER]
    assert len(ks) == 1
    assert coi[0].lineno < ks[0].lineno
