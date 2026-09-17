"""S13 recon + negative suite-invariants conformance.

BOUNDED_WORKPACKAGE=
MASTER_V2_DOUBLE_PLAY_BOUNDED_BEHAVIORAL_CONFORMANCE_VECTOR_SET_FROM_PROVEN_CELLS_ONLY_V1
SLICE=S13_RECON_NEGATIVE_SUITE_INVARIANTS
PRIMARY_OWNER=trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0
ENTRY_EXIT_OWNER=trading.master_v2.double_play_entry_exit_policy_v0
REPLAY_CONSUMER=run_integrated_offline_trading_logic_replay_v1
RECON_BINDER=bind_reconciliation_unknown_outcome_offline_replay_evidence_v0

Additive behavioral assertions only. No trading-semantics mutation.
Locks already proven V-RC-01 and V-NEG-01..03 cells after S12 locked
29P / pre-29Q Safety / 29Q PLAN_ONLY. Does not define new policy.
Does not unify Safety-kernel killswitch_blocked with FILEGATE or
SideState.KILL_ALL. Does not repair the S10 PARTIAL binder split.
PENDING_ENTRY_ELIGIBILITY_CANONICALLY_DEFINED remains false.
FILEGATE / execution / Live / S14 joined happy path / Golden Vector /
composition-before-transition / Manifest-vs-Owner envelope qualifier
are out of this slice.

Epistemic:
- CANONICAL_AUTHORITY: Master Runbook §11.2.1.A/B 29Q_PLAN_ONLY=true;
  DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED=false; FILEGATE distinct from
  Replay Safety and post-29Q KS; RUNTIME_AUTHORIZATION_EFFECT=NONE
- FORENSIC_RAW_EVIDENCE: EntryExit RECONCILE_ONLY on recon-required;
  recon binder maps recon-required and never writes decision_outcome;
  binder runtime/order/credential NONE; Replay binds recon after COI
  and before KS; mapper module absent from Replay/recon owners
- ALREADY_ADJUDICATED: S12 V-29P-01..02 / V-SAF-01 / V-29Q-01 CONFORMS
  within proven scope; S01 V-NEG-02 Teil (CMC bind is not authority)
- Not claimed: Safety-kernel/Kill-Switch blocked-flag unification;
  binder next_side_state rewire; Replay KILL_ALL_REQUIRED producer;
  PENDING ENTER eligibility; FILEGATE; S14 joined happy path

Path is tests/trading/ not tests/trading/master_v2/: the Economic Guard treats
tests/trading/master_v2/test_* as forbidden MASTER_V2 mutation surface.
Owner fixtures are reused via import of existing owner test helpers.
"""

from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryEligibility,
    PositionState,
    ReconciliationState,
)
from trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0 import (
    CREDENTIAL_EFFECT_NONE,
    ORDER_EFFECT_NONE,
    RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE,
    RUNTIME_AUTHORITY_EFFECT_NONE,
    ReconciliationUnknownOutcomeOfflineReplayContextV0,
    bind_reconciliation_unknown_outcome_offline_replay_evidence_v0,
    evaluate_offline_reconciliation_unknown_outcome_boundary_v0,
    reconciliation_unknown_outcome_binding_non_authority_boundary_ok_v0,
)

from tests.trading.master_v2.test_double_play_entry_exit_policy_v0 import _evaluate
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPLAY_SOURCE = _REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_RECON_SOURCE = (
    _REPO_ROOT
    / "src/trading/master_v2/reconciliation_unknown_outcome_offline_replay_binding_adapter_v0.py"
)
_RECON_BIND_OWNER = "bind_reconciliation_unknown_outcome_offline_replay_evidence_v0"
_KS_BIND_OWNER = "bind_killswitch_boundary_offline_replay_evidence_v0"
_COI_BIND_OWNER = "bind_canonical_order_intent_offline_replay_evidence_v0"
_MAPPER_MODULE = "intended_action_mapper_v1"
_FILEGATE_TOKENS = (
    "kill_switch_should_block_trading",
    "KillSwitchState",
    "StatePersistence",
    "PEAK_KILL_SWITCH",
)
_ENTER_OUTCOMES = frozenset({DecisionOutcome.ENTER_LONG.value, DecisionOutcome.ENTER_SHORT.value})


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


def _bind_fn() -> ast.FunctionDef:
    recon_tree = ast.parse(_RECON_SOURCE.read_text(encoding="utf-8"))
    return _function_def(recon_tree, _RECON_BIND_OWNER)


def test_s13_t01_v_rc_01_position_recon_required_fail_closed_entry() -> None:
    """S13-T01 / V-RC-01: position recon-required is RECONCILE_ONLY; entry blocked."""
    owner = _evaluate(position_state=PositionState.RECONCILIATION_REQUIRED)
    assert owner.decision_outcome is DecisionOutcome.RECONCILE_ONLY
    assert owner.entry_eligibility is EntryEligibility.BLOCKED
    assert owner.position_flip_allowed is False

    replay = _run(position_state=PositionState.RECONCILIATION_REQUIRED)
    assert replay.evidence.decision_outcome == DecisionOutcome.RECONCILE_ONLY.value
    assert replay.evidence.decision_outcome not in _ENTER_OUTCOMES
    assert replay.intermediate is not None
    assert (
        replay.intermediate.entry_exit_decision.decision_outcome is DecisionOutcome.RECONCILE_ONLY
    )
    assert replay.evidence.reconciliation_unknown_outcome_effect == (
        RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE
    )
    assert replay.evidence.reconciliation_unknown_outcome_ref

    ctx = ReconciliationUnknownOutcomeOfflineReplayContextV0(
        position_state=PositionState.RECONCILIATION_REQUIRED,
    )
    boundary = evaluate_offline_reconciliation_unknown_outcome_boundary_v0(
        ctx, decision_outcome=replay.evidence.decision_outcome
    )
    assert boundary.reconciliation_required_maps_to_reconcile_only is True
    assert "reconciliation_required_blocks_new_exposure" in boundary.hard_block_reasons
    assert boundary.runtime_authority_effect == RUNTIME_AUTHORITY_EFFECT_NONE
    assert boundary.order_effect == ORDER_EFFECT_NONE
    assert boundary.credential_effect == CREDENTIAL_EFFECT_NONE
    binding = bind_reconciliation_unknown_outcome_offline_replay_evidence_v0(
        replay.evidence, context=ctx
    )
    assert binding.evidence.decision_outcome == DecisionOutcome.RECONCILE_ONLY.value
    assert reconciliation_unknown_outcome_binding_non_authority_boundary_ok_v0(binding)


def test_s13_t02_v_rc_01_venue_flat_recon_required_is_not_entry() -> None:
    """S13-T02 / V-RC-01: venue_flat + recon-required stays RECONCILE_ONLY.

    Owner fixture test_22 / test_26 is the already-proven oracle: venue_flat
    alone is not a reconciled-flat entry grant.
    """
    owner = _evaluate(
        position_state=PositionState.RECONCILIATION_REQUIRED,
        venue_flat=True,
    )
    assert owner.decision_outcome is DecisionOutcome.RECONCILE_ONLY

    replay = _run(
        position_state=PositionState.RECONCILIATION_REQUIRED,
        reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED,
        venue_flat=True,
    )
    assert replay.evidence.decision_outcome == DecisionOutcome.RECONCILE_ONLY.value
    assert replay.evidence.decision_outcome not in _ENTER_OUTCOMES

    ctx = ReconciliationUnknownOutcomeOfflineReplayContextV0(
        position_state=PositionState.RECONCILIATION_REQUIRED,
        reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED,
        venue_flat=True,
    )
    boundary = evaluate_offline_reconciliation_unknown_outcome_boundary_v0(
        ctx, decision_outcome=replay.evidence.decision_outcome
    )
    assert boundary.reconciliation_required_maps_to_reconcile_only is True
    assert boundary.venue_flat_alone_insufficient is True
    assert "venue_flat_alone_insufficient" in boundary.hard_block_reasons
    assert boundary.runtime_authority_effect == RUNTIME_AUTHORITY_EFFECT_NONE


def test_s13_t03_v_neg_01_plan_only_no_order_boundary() -> None:
    """S13-T03 / V-NEG-01: recon-required path stays PLAN_ONLY with no order grant."""
    replay = _run(position_state=PositionState.RECONCILIATION_REQUIRED)
    evidence = replay.evidence
    assert evidence.decision_outcome == DecisionOutcome.RECONCILE_ONLY.value
    assert evidence.execution_eligible is False
    assert evidence.adapter_compatible is False
    assert evidence.order_effect == ORDER_EFFECT_NONE
    assert evidence.authority_effect == RUNTIME_AUTHORITY_EFFECT_NONE
    assert evidence.runtime_effect == RUNTIME_AUTHORITY_EFFECT_NONE
    assert replay.intermediate is not None
    assert replay.intermediate.canonical_order_intent is None
    binding = bind_reconciliation_unknown_outcome_offline_replay_evidence_v0(
        evidence,
        context=ReconciliationUnknownOutcomeOfflineReplayContextV0(
            position_state=PositionState.RECONCILIATION_REQUIRED,
        ),
    )
    assert binding.boundary.order_effect == ORDER_EFFECT_NONE
    assert binding.evidence.execution_eligible is False
    assert reconciliation_unknown_outcome_binding_non_authority_boundary_ok_v0(binding)


def test_s13_t04_v_neg_02_mapper_is_not_decision_owner() -> None:
    """S13-T04 / V-NEG-02: recon binder does not rewrite outcome; mapper is absent."""
    bind_fn = _bind_fn()
    replace_keywords: set[str] = set()
    for node in ast.walk(bind_fn):
        if isinstance(node, ast.Call) and _call_name(node) == "replace":
            replace_keywords.update(kw.arg for kw in node.keywords if kw.arg)
    assert "decision_outcome" not in replace_keywords

    replay = _run(position_state=PositionState.RECONCILIATION_REQUIRED)
    assert replay.intermediate is not None
    assert (
        replay.evidence.decision_outcome
        == replay.intermediate.entry_exit_decision.decision_outcome.value
    )

    for source in (_RECON_SOURCE, _REPLAY_SOURCE, Path(__file__)):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        imported = _imported_names(tree)
        assert all(_MAPPER_MODULE not in name for name in imported)
        assert all("src.execution" not in name for name in imported)
        assert all(not name.startswith("src.live") for name in imported)


def test_s13_t05_v_neg_03_filegate_absent_and_s14_not_started() -> None:
    """S13-T05 / V-NEG-03: FILEGATE/execution absent; S12 remainder open; S14 absent."""
    s12_path = (
        _REPO_ROOT / "tests/trading/test_s12_29p_pre_29q_safety_29q_plan_only_conformance_v1.py"
    )
    assert s12_path.is_file()
    s12_src = s12_path.read_text(encoding="utf-8")
    assert "Safety-kernel/Kill-Switch blocked-flag unification" in s12_src
    assert "PENDING_ENTRY_ELIGIBILITY_CANONICALLY_DEFINED remains false" in s12_src
    s10_path = (
        _REPO_ROOT / "tests/trading/test_s10_kill_all_fanout_partial_same_tick_conformance_v1.py"
    )
    s10_src = s10_path.read_text(encoding="utf-8")
    assert "Does not repair the PARTIAL/DEVIATES binder-input cell" in s10_src
    this_src = Path(__file__).read_text(encoding="utf-8")
    assert "Safety-kernel/Kill-Switch blocked-flag unification" in this_src
    assert "PENDING_ENTRY_ELIGIBILITY_CANONICALLY_DEFINED remains false" in this_src
    assert list(_REPO_ROOT.glob("tests/trading/test_s14_*.py")) == []
    this_tree = ast.parse(this_src)
    imported = _imported_names(this_tree)
    assert all("src.execution" not in name for name in imported)
    assert all(not name.startswith("src.live") for name in imported)
    assert all("kill_switch_should_block_trading" not in name for name in imported)
    assert all("construct_live_execution_port_v1" not in name for name in imported)
    assert all("test_s14_" not in name for name in imported)
    for source_path in (_REPLAY_SOURCE, _RECON_SOURCE):
        source_text = source_path.read_text(encoding="utf-8")
        for token in _FILEGATE_TOKENS:
            assert token not in source_text
    replay_fn = _replay_fn()
    calls = [call for call in _ordered_calls(replay_fn) if _call_name(call) is not None]
    recon = [call for call in calls if _call_name(call) == _RECON_BIND_OWNER]
    ks = [call for call in calls if _call_name(call) == _KS_BIND_OWNER]
    coi = [call for call in calls if _call_name(call) == _COI_BIND_OWNER]
    assert len(recon) == 1
    assert len(ks) == 1
    assert len(coi) == 1
    assert coi[0].lineno < recon[0].lineno < ks[0].lineno
