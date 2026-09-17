"""S14 joined happy-path conformance.

BOUNDED_WORKPACKAGE=
MASTER_V2_DOUBLE_PLAY_BOUNDED_BEHAVIORAL_CONFORMANCE_VECTOR_SET_FROM_PROVEN_CELLS_ONLY_V1
SLICE=S14_JOINED_HAPPY_PATH
PRIMARY_OWNER=run_integrated_offline_trading_logic_replay_v1
VECTOR=V-HP-01

Additive behavioral assertions only. No trading-semantics mutation.
One Replay join over already proven S01–S08 observables for LONG
continuation. Does not define new policy. Does not introduce new oracles.
Does not unify Safety-kernel killswitch_blocked with FILEGATE or
SideState.KILL_ALL. Does not repair the S10 PARTIAL binder split.
PENDING_ENTRY_ELIGIBILITY_CANONICALLY_DEFINED remains false.
FILEGATE / execution / Live / Golden Vector / composition-before-transition
/ Manifest-vs-Owner envelope qualifier / WP-global closeout are out of
this slice.

Epistemic:
- CANONICAL_AUTHORITY: Master Runbook §11.2.1.A/B
  SOLE_COMPUTE_OWNER=run_integrated_offline_trading_logic_replay_v1;
  DOUBLE_PLAY_SIDE_STATE_OWNER=transition_state;
  ENTRY_EXIT_OWNER=entry_exit_policy_v0; RUNTIME_AUTHORIZATION_EFFECT=NONE
- FORENSIC_RAW_EVIDENCE: one Replay call on trusted CMC + missing-prior
  scope init + injected C1 DISTINCT + LONG_ACTIVE OPEN_FULL HOLD
- ALREADY_ADJUDICATED: S01 V-CMC-01; S02 V-SC-01; S03 V-TR-01 same-side;
  S04 V-C1-01; S05 V-CLK-01; S06 V-C4-02; S07 V-SW-02; S08 V-EE-01;
  S13 V-RC-01 / V-NEG-01..03 CONFORMS within proven scope
- Not claimed: Safety-kernel/Kill-Switch blocked-flag unification;
  binder next_side_state rewire; Replay KILL_ALL_REQUIRED producer;
  PENDING ENTER eligibility; FILEGATE; Golden Vector; all OPEN/PARTIAL
  cells resolved; production completeness; WP-global conformance

Path is tests/trading/ not tests/trading/master_v2/: the Economic Guard treats
tests/trading/master_v2/test_* as forbidden MASTER_V2 mutation surface.
Owner fixtures are reused via import of existing owner test helpers.
"""

from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentStatus
from trading.master_v2.double_play_composition_matrix_v1 import CompositionSelectedSide
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    ExistingPositionSide,
    PositionManagementAction,
    PositionState,
)
from trading.master_v2.double_play_state import ActiveSide, SideState, derive_active_side
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import ObservationClassification

from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _EPOCH,
    _INSTRUMENT,
    _run,
)
from tests.trading.master_v2.test_post_confirmation_survival_suitability_composition_binding_v1 import (
    _key,
    _policies_confirm_once,
    _session,
)
from tests.trading.test_s01_cmc_identity_trust_fail_closed_conformance_v1 import (
    _CMC_IDENTITY_FAIL_REASONS,
)
from tests.trading.test_s05_c1_c3_vs_scope_confirmation_clock_conformance_v1 import (
    _SCOPE_CONFIRMED,
    _empty_scope_confirmation,
    _injected_c1,
    _replay_c2_cursor,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPLAY_SOURCE = _REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_COMPOSE_ORACLE = "compose_double_play_decision"
_MAPPER_MODULE = "intended_action_mapper_v1"
_FILEGATE_TOKENS = (
    "kill_switch_should_block_trading",
    "KillSwitchState",
    "StatePersistence",
    "PEAK_KILL_SWITCH",
)
_HOLD_NOT_ENTRY_EXIT = frozenset(
    {
        DecisionOutcome.ENTER_LONG,
        DecisionOutcome.ENTER_SHORT,
        DecisionOutcome.EXIT,
        DecisionOutcome.REDUCE,
    }
)
_FORBIDDEN_NEW_ORACLE_CALLS = frozenset(
    {
        "evaluate_double_play_entry_exit_policy_v0",
        "evaluate_double_play_composition_matrix_v1",
        "initialize_canonical_scope",
        "bind_canonical_market_context_event",
        "transition_state",
        "update_dynamic_boundaries",
        "compose_double_play_decision",
        "evaluate_offline_killswitch_boundary_v0",
        "evaluate_offline_safety_kernel_boundary_v0",
        "bind_reconciliation_unknown_outcome_offline_replay_evidence_v0",
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


def test_s14_t01_v_hp_01_joined_long_continuation_over_s01_s08_observables() -> None:
    """S14-T01 / V-HP-01: one Replay join of proven S01–S08 LONG-continuation cells."""
    injected = _injected_c1()
    assert injected.classification is ObservationClassification.DISTINCT

    replay = _run(
        policies=_policies_confirm_once(),
        price_path=(3500.0, 3570.0),
        observation_acceptance_result=injected,
        scope_confirmation_state=_empty_scope_confirmation(),
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
        side_state=SideState.LONG_ACTIVE,
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        existing_scope=None,
    )
    assert replay.compute_owner == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER
    assert replay.intermediate is not None
    mid = replay.intermediate

    # S01 / V-CMC-01: trusted CMC identity join; no CMC fail-closed reasons.
    assert not (_CMC_IDENTITY_FAIL_REASONS & set(replay.fail_reasons))
    assert replay.evidence.instrument_id == mid.market_context.instrument_id == _INSTRUMENT
    assert replay.evidence.trading_epoch == mid.market_context.trading_epoch == _EPOCH
    assert replay.evidence.authority_effect == "NONE"
    assert replay.evidence.runtime_effect == "NONE"
    assert replay.evidence.execution_eligible is False

    # S02 / V-SC-01: missing prior scope is initialized; Replay remains consumer.
    assert mid.scope_initialization is not None
    assert mid.current_scope is not None
    assert mid.runtime_scope_state_before is not None
    assert mid.runtime_scope_state_after is not None

    # S03 / V-TR-01: PRE and POST ActiveSide stay LONG; trailing is not SideState writer.
    previous = SideState(mid.state_switch.previous_side_state)
    nxt = SideState(mid.state_switch.next_side_state)
    assert previous is SideState.LONG_ACTIVE
    assert nxt is SideState.LONG_ACTIVE
    assert derive_active_side(previous) is ActiveSide.LONG
    assert derive_active_side(nxt) is ActiveSide.LONG

    # S04 / V-C1-01: injected DISTINCT may advance the C2/C3 cursor.
    cursor = _replay_c2_cursor(replay)
    assert cursor[0] == 1 or cursor[2] == 1

    # S05 / V-CLK-01: C3 CONFIRMED is not Scope CONFIRMED.
    assert mid.bull_assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert mid.scope_event.event_type not in _SCOPE_CONFIRMED

    # S06 / V-C4-02: composition selects LONG; selected_side is not SideState.
    assert mid.composition_result.selected_side is CompositionSelectedSide.LONG
    assert mid.composition_result.selected_side is not SideState.LONG_ACTIVE
    assert CompositionSelectedSide is not SideState

    # S07 / V-SW-02: LONG_ACTIVE continuation holds SideState.
    assert mid.state_switch.previous_side_state == SideState.LONG_ACTIVE.value
    assert mid.state_switch.next_side_state == SideState.LONG_ACTIVE.value
    assert mid.transition_decision is not None
    assert mid.transition_decision.reason_code in {"NOOP", "CANDIDATE_ACK"}

    # S08 / V-EE-01: existing LONG exposure HOLDs; no ENTER/EXIT/flip.
    hold = mid.entry_exit_decision
    assert replay.evidence.decision_outcome == DecisionOutcome.HOLD.value
    assert hold.decision_outcome is DecisionOutcome.HOLD
    assert hold.position_management_action is PositionManagementAction.HOLD
    assert hold.decision_outcome not in _HOLD_NOT_ENTRY_EXIT
    assert hold.position_flip_allowed is False
    assert hold.decision_outcome is not DecisionOutcome.RECONCILE_ONLY


def test_s14_t02_no_new_oracles_open_partial_unchanged_unification_not_claimed() -> None:
    """S14-T02: no new oracles; OPEN/PARTIAL conserved; FILEGATE/unification not claimed."""
    this_src = Path(__file__).read_text(encoding="utf-8")
    this_tree = ast.parse(this_src)
    imported = _imported_names(this_tree)
    assert all(_COMPOSE_ORACLE not in name for name in imported)
    assert all(_MAPPER_MODULE not in name for name in imported)
    assert all("src.execution" not in name for name in imported)
    assert all(not name.startswith("src.live") for name in imported)
    assert all("kill_switch_should_block_trading" not in name for name in imported)
    assert all("construct_live_execution_port_v1" not in name for name in imported)
    defined_calls = {_call_name(node) for node in ast.walk(this_tree) if isinstance(node, ast.Call)}
    assert defined_calls.isdisjoint(_FORBIDDEN_NEW_ORACLE_CALLS)
    assert "Safety-kernel/Kill-Switch blocked-flag unification" in this_src
    assert "PENDING_ENTRY_ELIGIBILITY_CANONICALLY_DEFINED remains false" in this_src
    assert "WP-global conformance" in this_src

    s10_path = (
        _REPO_ROOT / "tests/trading/test_s10_kill_all_fanout_partial_same_tick_conformance_v1.py"
    )
    s10_src = s10_path.read_text(encoding="utf-8")
    assert "Does not repair the PARTIAL/DEVIATES binder-input cell" in s10_src
    s12_path = (
        _REPO_ROOT / "tests/trading/test_s12_29p_pre_29q_safety_29q_plan_only_conformance_v1.py"
    )
    s12_src = s12_path.read_text(encoding="utf-8")
    assert "Safety-kernel/Kill-Switch blocked-flag unification" in s12_src
    s13_path = (
        _REPO_ROOT / "tests/trading/test_s13_recon_negative_suite_invariants_conformance_v1.py"
    )
    s13_src = s13_path.read_text(encoding="utf-8")
    assert "Safety-kernel/Kill-Switch blocked-flag unification" in s13_src
    assert "PENDING_ENTRY_ELIGIBILITY_CANONICALLY_DEFINED remains false" in s13_src

    replay_src = _REPLAY_SOURCE.read_text(encoding="utf-8")
    for token in _FILEGATE_TOKENS:
        assert token not in replay_src
    assert list(_REPO_ROOT.glob("tests/trading/test_s15_*.py")) == []
    assert list(_REPO_ROOT.glob("tests/trading/test_s14_*.py")) == [Path(__file__).resolve()]
