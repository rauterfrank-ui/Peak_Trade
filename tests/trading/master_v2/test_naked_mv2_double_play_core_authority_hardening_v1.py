"""Contract + adversarial tests: Naked MV2+Double Play core authority hardening v1."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1.constants_v1 import (
    AUTONOMY_TRADING_DECISION_AUTHORITY,
    FULL_AUTONOMY_TRADING_DECISION_AUTHORITY,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.constants_v1 import (
    PRODUCTIVE_DECISION_OWNER,
)
from src.ops.full_core_live_path_composition_root_v1.composition_root_v1 import (
    compose_core_live_execution_intent_v1,
)
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    initial_directional_confirmation_side_state_carrier_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitDirectionState,
    ExistingPositionSide,
    PolicySignalV0,
    PositionState,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayInputV1,
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.double_play_sole_authority_quarantine_v1 import (
    CompetingAuthorityEscalationError,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
from trading.master_v2.double_play_state import SideState
from trading.master_v2.evaluate_double_play_authority_boundary_v0 import (
    classify_ops_evaluate_double_play_authority,
)
from trading.master_v2.naked_mv2_double_play_core_authority_hardening_v1 import (
    LEGACY_INTEGRATED_REPLAY_CALL_ORDER_ENTER_LONG_TEST_ACCEPTANCE,
    DOWNSTREAM_REDECISION_AUTHORITY,
    EXECUTION_TRADING_DECISION_AUTHORITY,
    IndependentTradingDecisionAuthorityError,
    IngressSurfaceClass,
    LEARNING_TRADING_DECISION_AUTHORITY,
    NAKED_CORE_COMPONENTS,
    OPTIMIZATION_TRADING_DECISION_AUTHORITY,
    OptimizationSurfaceNotAdmittedError,
    PACKAGE_MARKER,
    ProductiveCoreMutationFromResearchError,
    TERMINAL_DECISION_FIELD,
    TRADING_DECISION_AUTHORITY_OWNER,
    assert_downstream_preserves_terminal_decision_outcome_v1,
    assert_optimization_core_touch_surface_admitted_v1,
    build_naked_mv2_double_play_core_authority_status_fields_v1,
    deny_independent_trading_decision_authority_v1,
    deny_productive_core_mutation_from_research_v1,
    optimization_touch_admission_template_v1,
)
from trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 import (
    bind_safety_kernel_offline_replay_evidence_v0,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _replay_input,
)
from tests.trading.master_v2.test_post_confirmation_survival_suitability_composition_binding_v1 import (
    _distinct_acceptor,
    _key,
    _policies_confirm_once,
    _session,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
HARDENING_TEST_MODULE = Path(__file__)
LEGACY_DRIFT_TEST_NAME = "test_call_order_pass_path_enter_long"


def _armed_lane_replay_input_for_non_interference_v1(
    *, side: str
) -> IntegratedOfflineReplayInputV1:
    """Long/short armed lane vectors for deterministic non-interference only (no ENTER assert)."""
    acceptor, _committed = _distinct_acceptor()
    carrier = initial_directional_confirmation_side_state_carrier_v1(
        session_id=_session(),
        venue="okx_eea",
        instrument=_key(),
    )
    if side == "LONG":
        return _replay_input(
            side_state=SideState.LONG_ARMED,
            direction_state=EntryExitDirectionState.LONG_ARMED,
            scope_direction_state=ScopeDirectionState.LONG,
            policies=_policies_confirm_once(),
            price_path=(3500.0, 3570.0),
            directional_confirmation_progress=carrier,
            observation_acceptance_result=acceptor,
            confirmation_progress_session_id=_session(),
            confirmation_progress_venue="okx_eea",
            confirmation_progress_instrument=_key(),
        )
    return _replay_input(
        side_state=SideState.SHORT_ARMED,
        direction_state=EntryExitDirectionState.SHORT_ARMED,
        scope_direction_state=ScopeDirectionState.SHORT,
        policies=_policies_confirm_once(),
        price_path=(3500.0, 3430.0),
        directional_confirmation_progress=carrier,
        observation_acceptance_result=acceptor,
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
    )


def _exit_precedence_replay_input_v1() -> IntegratedOfflineReplayInputV1:
    return _replay_input(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        side_state=SideState.LONG_ACTIVE,
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
        safety_exit_signal=PolicySignalV0(triggered=True, reason_code="safety"),
    )


HARDENING_MODULE = (
    REPO_ROOT / "src/trading/master_v2/naked_mv2_double_play_core_authority_hardening_v1.py"
)
DECISION_JSON = (
    REPO_ROOT
    / "config/governance/naked_mv2_double_play_core_authority_hardening_v1_decision_v1.json"
)
SAFETY_MODULE = (
    REPO_ROOT / "src/trading/master_v2/safety_kernel_offline_replay_binding_adapter_v0.py"
)
COMPOSE_MODULE = (
    REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1/composition_root_v1.py"
)
REPLAY_MODULE = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"


def test_package_marker_and_status_fields_align_with_forensic_baseline() -> None:
    assert PACKAGE_MARKER in HARDENING_MODULE.read_text(encoding="utf-8")
    fields = build_naked_mv2_double_play_core_authority_status_fields_v1()
    assert fields["TRADING_DECISION_AUTHORITY_OWNER"] == TRADING_DECISION_AUTHORITY_OWNER
    assert fields["TERMINAL_DECISION_FIELD"] == TERMINAL_DECISION_FIELD
    assert fields["DOWNSTREAM_REDECISION_AUTHORITY"] == DOWNSTREAM_REDECISION_AUTHORITY
    assert fields["LEARNING_TRADING_DECISION_AUTHORITY"] == LEARNING_TRADING_DECISION_AUTHORITY
    assert (
        fields["OPTIMIZATION_TRADING_DECISION_AUTHORITY"] == OPTIMIZATION_TRADING_DECISION_AUTHORITY
    )
    assert fields["EXECUTION_TRADING_DECISION_AUTHORITY"] == EXECUTION_TRADING_DECISION_AUTHORITY
    assert fields["MV2_DOUBLE_PLAY_SOLE_TRADING_DECISION_AUTHORITY"] == "true"
    assert len(NAKED_CORE_COMPONENTS) == 11


def test_governance_decision_json_matches_constants() -> None:
    payload = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    assert payload["trading_decision_authority_owner"] == TRADING_DECISION_AUTHORITY_OWNER
    assert payload["terminal_decision_field"] == TERMINAL_DECISION_FIELD
    assert payload["external_effect_authorized"] is False
    assert payload["f3_build_authorized"] is False
    assert payload["core_hot_path_mutation_performed"] is False
    assert payload["legacy_drift_test_used_as_acceptance_gate"] is False


def test_productive_decision_owner_constants_crosslink() -> None:
    assert PRODUCTIVE_DECISION_OWNER == TRADING_DECISION_AUTHORITY_OWNER


@pytest.mark.parametrize(
    ("surface_class", "surface_id"),
    [
        (IngressSurfaceClass.LEARNING, "learning.loop_v1"),
        (IngressSurfaceClass.OPTIMIZATION, "experiments.optimizer_v1"),
        (IngressSurfaceClass.META_LEARNING, "meta_learning.ingest_v1"),
        (IngressSurfaceClass.AUTONOMY, "full_autonomy_orchestrator_v1"),
        (IngressSurfaceClass.RESEARCH_SHADOW, "numeric_policy_shadow_campaign_v1"),
    ],
)
def test_ingress_denies_independent_trading_decision(
    surface_class: IngressSurfaceClass,
    surface_id: str,
) -> None:
    with pytest.raises(IndependentTradingDecisionAuthorityError):
        deny_independent_trading_decision_authority_v1(
            surface_id=surface_id,
            surface_class=surface_class,
            claims_trading_decision_authority=True,
        )


def test_legacy_evaluator_escalation_denied() -> None:
    with pytest.raises(IndependentTradingDecisionAuthorityError):
        deny_independent_trading_decision_authority_v1(
            surface_id="src.ops.double_play.specialists.evaluate_double_play",
            surface_class=IngressSurfaceClass.LEGACY_DOUBLE_PLAY,
            claims_trading_decision_authority=True,
        )
    with pytest.raises(CompetingAuthorityEscalationError):
        deny_independent_trading_decision_authority_v1(
            surface_id="src.ops.double_play.specialists.evaluate_double_play",
            surface_class=IngressSurfaceClass.LEGACY_DOUBLE_PLAY,
            claims_trading_decision_authority=False,
            claims_productive_path=True,
        )
    assert classify_ops_evaluate_double_play_authority() == "LEGACY_NON_AUTHORITATIVE"


def test_autonomy_flags_remain_non_authoritative() -> None:
    assert AUTONOMY_TRADING_DECISION_AUTHORITY is False
    assert FULL_AUTONOMY_TRADING_DECISION_AUTHORITY is False
    deny_independent_trading_decision_authority_v1(
        surface_id="autonomy_orchestrator",
        surface_class=IngressSurfaceClass.AUTONOMY,
        claims_trading_decision_authority=False,
    )


def test_research_core_mutation_denied_without_governance() -> None:
    with pytest.raises(ProductiveCoreMutationFromResearchError):
        deny_productive_core_mutation_from_research_v1(
            surface_id="optimization_candidate_v1",
            surface_class=IngressSurfaceClass.OPTIMIZATION,
            targets_immutable_core_semantic=True,
            productive_mutation_requested=True,
            separate_governance_owner_go_present=False,
        )


def test_optimization_touch_admission_fail_closed_on_missing_metadata() -> None:
    with pytest.raises(OptimizationSurfaceNotAdmittedError):
        assert_optimization_core_touch_surface_admitted_v1({"target_parameter_or_component": "x"})
    admitted = optimization_touch_admission_template_v1(
        target_parameter_or_component="research_only_param"
    )
    assert_optimization_core_touch_surface_admitted_v1(admitted)


def test_downstream_preserves_terminal_decision_outcome_helper() -> None:
    assert_downstream_preserves_terminal_decision_outcome_v1(
        terminal_before="observe",
        observed_after="observe",
        layer_id="safety_kernel",
    )
    with pytest.raises(Exception):
        assert_downstream_preserves_terminal_decision_outcome_v1(
            terminal_before="enter_long",
            observed_after="enter_short",
            layer_id="forbidden_layer",
        )


def test_safety_kernel_binding_does_not_assign_new_decision_outcome() -> None:
    tree = ast.parse(SAFETY_MODULE.read_text(encoding="utf-8"))
    source = ast.unparse(tree)
    assert "decision_outcome=evidence.decision_outcome" in source
    assert "decision_outcome=" in source
    # Must not replace evidence.decision_outcome with a new outcome literal in bind path.
    assert "replace(\n        evidence,\n        decision_outcome=" not in source


def test_compose_module_consumes_replay_decision_outcome() -> None:
    text = COMPOSE_MODULE.read_text(encoding="utf-8")
    assert "replay.evidence.decision_outcome" in text
    assert "compose_core_live_execution_intent_v1" in text


def test_integrated_replay_module_not_wired_to_hardening_hot_path() -> None:
    replay_src = REPLAY_MODULE.read_text(encoding="utf-8")
    assert "naked_mv2_double_play_core_authority_hardening_v1" not in replay_src


def _replay_snapshot(replay_result: object) -> dict[str, str]:
    inter = replay_result.intermediate
    assert inter is not None
    comp = inter.composition_result
    assert comp is not None
    return {
        "decision_outcome": str(replay_result.evidence.decision_outcome),
        "composition_id": str(comp.composition_id),
        "composition_status": str(comp.composition_status.value),
        "selected_side": str(comp.selected_side.value),
        "next_side_state": str(inter.state_switch.next_side_state),
        "bull_ref": str(replay_result.evidence.bull_assessment_ref or ""),
        "bear_ref": str(replay_result.evidence.bear_assessment_ref or ""),
    }


def test_legacy_call_order_enter_long_not_hardening_acceptance_gate() -> None:
    assert LEGACY_INTEGRATED_REPLAY_CALL_ORDER_ENTER_LONG_TEST_ACCEPTANCE is False
    tree = ast.parse(HARDENING_TEST_MODULE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "integrated_replay_safety_before_intent" not in node.module
    decision = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    assert decision["legacy_drift_test_name"] == LEGACY_DRIFT_TEST_NAME
    assert decision["legacy_drift_test_used_as_acceptance_gate"] is False


def test_non_interference_replay_deterministic_twice_long_armed_lane() -> None:
    inp = _armed_lane_replay_input_for_non_interference_v1(side="LONG")
    first = run_integrated_offline_trading_logic_replay_v1(inp)
    second = run_integrated_offline_trading_logic_replay_v1(inp)
    assert _replay_snapshot(first) == _replay_snapshot(second)


def test_non_interference_replay_deterministic_twice_short_armed_lane() -> None:
    inp = _armed_lane_replay_input_for_non_interference_v1(side="SHORT")
    first = run_integrated_offline_trading_logic_replay_v1(inp)
    second = run_integrated_offline_trading_logic_replay_v1(inp)
    assert _replay_snapshot(first) == _replay_snapshot(second)


def test_long_path_regression_reuses_entry_exit_contract_owner() -> None:
    from tests.trading.master_v2 import test_double_play_entry_exit_policy_v0 as entry_exit_tests

    entry_exit_tests.test_1_flat_reconciled_long_admissible_enter_long()


def test_short_path_regression_reuses_entry_exit_contract_owner() -> None:
    from tests.trading.master_v2 import test_double_play_entry_exit_policy_v0 as entry_exit_tests

    entry_exit_tests.test_2_flat_reconciled_short_admissible_enter_short()


def test_exit_path_regression_safety_exit_precedence() -> None:
    result = run_integrated_offline_trading_logic_replay_v1(_exit_precedence_replay_input_v1())
    assert result.evidence.decision_outcome == DecisionOutcome.EXIT.value


def test_hold_observe_path_replay_deterministic() -> None:
    inp = _replay_input(
        side_state=SideState.NEUTRAL_OBSERVE,
        direction_state=EntryExitDirectionState.NEUTRAL,
        scope_direction_state=ScopeDirectionState.LONG,
    )
    first = run_integrated_offline_trading_logic_replay_v1(inp)
    second = run_integrated_offline_trading_logic_replay_v1(inp)
    assert _replay_snapshot(first) == _replay_snapshot(second)
    assert first.evidence.decision_outcome in {
        DecisionOutcome.OBSERVE.value,
        DecisionOutcome.NO_ACTION.value,
        DecisionOutcome.HOLD.value,
        DecisionOutcome.BLOCKED.value,
    }


def test_compose_denies_hold_without_redecision() -> None:
    from src.ops.full_core_live_path_composition_root_v1.constants_v1 import MODE_LIVE
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

    replay = run_integrated_offline_trading_logic_replay_v1(_replay_input())
    bound = BoundInstrumentV1(
        instrument_id=str(replay.evidence.instrument_id),
        venue_native_id=str(replay.evidence.instrument_id),
        selection_id="sel-1",
        ranking_snapshot_id="rank-1",
        ranking_integrity_digest="b" * 64,
        universe_snapshot_id="uni-1",
        selection_integrity_digest="a" * 64,
        selection_state="SELECTED",
    )
    status, reasons, intent = compose_core_live_execution_intent_v1(
        replay=replay,
        bound_instrument=bound,
        mode=MODE_LIVE,
        composed_epoch="test-epoch",
    )
    assert intent is None
    assert status.value == "DENY"
    assert reasons
    assert replay.evidence.decision_outcome in {
        DecisionOutcome.HOLD.value,
        DecisionOutcome.OBSERVE.value,
        DecisionOutcome.NO_ACTION.value,
        DecisionOutcome.BLOCKED.value,
    }


def test_safety_bind_preserves_terminal_decision_outcome_non_interference() -> None:
    from trading.master_v2.double_play_entry_exit_policy_v0 import (
        ReconciliationState,
        SafetyMode,
        TradingGate,
    )
    from trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 import (
        SafetyKernelOfflineReplayContextV0,
    )

    replay = run_integrated_offline_trading_logic_replay_v1(
        _armed_lane_replay_input_for_non_interference_v1(side="LONG")
    )
    before = replay.evidence.decision_outcome
    ctx = SafetyKernelOfflineReplayContextV0(
        safety_mode=SafetyMode.NORMAL,
        safety_exit_signal=PolicySignalV0(triggered=False),
        reconciliation_state=ReconciliationState.RECONCILED,
        position_state=PositionState.FLAT_RECONCILED,
        trading_gate=TradingGate.ENTRY_ALLOWED,
        killswitch_blocked=False,
        safety_decision_allowed=True,
    )
    bound = bind_safety_kernel_offline_replay_evidence_v0(replay.evidence, context=ctx)
    assert bound.evidence.decision_outcome == before
