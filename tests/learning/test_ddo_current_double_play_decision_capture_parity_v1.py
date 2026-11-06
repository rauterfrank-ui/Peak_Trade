"""Typed Double-Play → DDO observation capture parity v1.

Observation-only. Does not grant DDO trading, risk, execution, or promotion
authority. Producer objects come from evaluate_double_play_entry_exit_policy_v0.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    DdoCaptureBindingV0,
    SEAM_DOUBLE_PLAY_ENTRY_EXIT,
    bind_capture_session_v0,
    bind_host_cycle_capture_context_v0,
    observe_producer_result_v0,
    record_productive_cycle_capture_v0,
    reset_capture_session_v0,
)
from src.learning.deterministic_decision_outcome_v0.double_play_observation_projection_v1 import (
    PREVIOUS_DIRECTION_STATE_SEMANTIC_CLASS,
    PRODUCER_CANONICAL_KEYS,
    SELECTED_SIDE_SEMANTIC_CLASS,
    SIDE_STATE_AFTER_STATUS_UNAVAILABLE,
    TRADING_AUTHORITY_NONE,
    TYPED_PROJECTION_STATUS,
    is_typed_entry_exit_policy_decision_v1,
    producer_canonical_payload_from_decision_v1,
    project_entry_exit_policy_decision_v1,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitDirectionState,
    EntryExitPolicyDecisionV0,
    ExistingPositionSide,
    ExitClass,
    PolicySignalV0,
    PositionManagementAction,
    PositionState,
    ReversalState,
    evaluate_double_play_entry_exit_policy_v0,
    serialize_entry_exit_policy_decision_canonical,
)
from tests.trading.master_v2.test_double_play_entry_exit_policy_v0 import (
    _evaluate,
    _long_selected_composition,
    _short_selected_composition,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "src" / "learning" / "deterministic_decision_outcome_v0"
EVENT_TIME = "2026-09-05T12:00:00Z"
CORR_ID = "ddo.corr.dp.parity.v1"
CYCLE_ID = "cycle:dp:parity:0001"
EVENT_UNIX = 1_757_088_000.0

FORBIDDEN_IMPORT_PREFIXES = (
    "src.trading",
    "src.execution",
    "src.live",
    "src.risk",
    "src.risk_layer",
    "src.governance.promotion",
    "src.ops",
)

TRADE_OUTCOMES = frozenset(
    {
        DecisionOutcome.ENTER_LONG.value,
        DecisionOutcome.ENTER_SHORT.value,
        DecisionOutcome.EXIT.value,
        DecisionOutcome.REDUCE.value,
        DecisionOutcome.HOLD.value,
    }
)


def _project(decision: EntryExitPolicyDecisionV0) -> Any:
    return project_entry_exit_policy_decision_v1(
        decision,
        record_id="ddo.dpo.parity.0001",
        event_time_utc=EVENT_TIME,
        correlation_id=CORR_ID,
        cycle_id=CYCLE_ID,
        decision_event_ref="ddo.dec.parity.0001",
    )


def _capture(decision: EntryExitPolicyDecisionV0) -> DdoCaptureBindingV0:
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=None)
    observe_producer_result_v0(
        binding,
        seam_id=SEAM_DOUBLE_PLAY_ENTRY_EXIT,
        result=decision,
        event_time_utc=EVENT_TIME,
        correlation_id=CORR_ID,
        cycle_id=CYCLE_ID,
        repository_sha=UNKNOWN,
    )
    return binding


def _decision_events(binding: DdoCaptureBindingV0) -> list[dict[str, Any]]:
    return [item for item in binding.captured_records if item["schema_name"] == "decision_event"]


def _double_play_events(binding: DdoCaptureBindingV0) -> list[dict[str, Any]]:
    return [
        item
        for item in _decision_events(binding)
        if item.get("producer_id") == "double_play_entry_exit_policy_v0"
    ]


def _observations(binding: DdoCaptureBindingV0) -> list[dict[str, Any]]:
    return [
        item
        for item in binding.captured_records
        if item["schema_name"] == "double_play_entry_exit_observation"
    ]


def _enter_long() -> EntryExitPolicyDecisionV0:
    return _evaluate()


def _enter_short() -> EntryExitPolicyDecisionV0:
    return _evaluate(
        composition_result=_short_selected_composition(),
        direction_state=EntryExitDirectionState.SHORT_ARMED,
    )


def _exit_non_none() -> EntryExitPolicyDecisionV0:
    return _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        profit_protection_signal=PolicySignalV0(triggered=True, reason_code="profit_lock"),
    )


def _reduce() -> EntryExitPolicyDecisionV0:
    return _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        scope_adverse_exit_signal=PolicySignalV0(triggered=True, reason_code="adverse_scope"),
    )


def _hold() -> EntryExitPolicyDecisionV0:
    return _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        composition_result=_long_selected_composition(),
    )


def _no_action() -> EntryExitPolicyDecisionV0:
    from trading.master_v2.directional_assessment_v1 import (
        DirectionalAssessmentSide,
        DirectionalAssessmentStatus,
    )
    from trading.master_v2.double_play_composition_matrix_v1 import (
        BothCandidateOutcome,
        BothInvalidOutcome,
        DoublePlayCompositionPolicyV1,
        evaluate_double_play_composition_matrix_v1,
    )
    from tests.trading.master_v2.test_double_play_entry_exit_policy_v0 import (
        _composition_input,
        _side_bundle,
    )

    bull, bull_s, bull_u = _side_bundle(
        DirectionalAssessmentSide.LONG,
        assessment_status=DirectionalAssessmentStatus.INVALID,
    )
    bear, bear_s, bear_u = _side_bundle(
        DirectionalAssessmentSide.SHORT,
        assessment_status=DirectionalAssessmentStatus.INVALID,
    )
    composition_input = _composition_input(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=bull_s,
        bear_survival_result=bear_s,
        bull_suitability_result=bull_u,
        bear_suitability_result=bear_u,
    )
    composition_policy = DoublePlayCompositionPolicyV1(
        validity_epochs=3,
        both_candidate_outcome=BothCandidateOutcome.OBSERVE,
        both_invalid_outcome=BothInvalidOutcome.NO_ACTION,
        policy_version="double_play_composition_matrix_policy_v1",
    )
    composition = evaluate_double_play_composition_matrix_v1(composition_input, composition_policy)
    return _evaluate(composition_result=composition)


def _reversal() -> EntryExitPolicyDecisionV0:
    return _evaluate(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        composition_result=_short_selected_composition(),
        direction_state=EntryExitDirectionState.SHORT_ARMED,
    )


def test_typed_enter_long_projection_keeps_exact_token() -> None:
    decision = _enter_long()
    assert isinstance(decision, EntryExitPolicyDecisionV0)
    assert decision.decision_outcome is DecisionOutcome.ENTER_LONG
    observation = _project(decision)
    payload = dict(observation["producer_canonical_payload"])
    assert payload["decision_outcome"] == "enter_long"
    assert payload["decision_outcome"] != "NO_ACTION"
    assert payload["decision_outcome"] != UNKNOWN
    assert observation["projection_status"] == TYPED_PROJECTION_STATUS
    binding = _capture(decision)
    event = _decision_events(binding)[0]
    assert event["decision_result"] != "NO_ACTION"
    assert event["decision_result"] == UNKNOWN
    assert dict(_observations(binding)[0]["producer_canonical_payload"])["decision_outcome"] == (
        "enter_long"
    )


def test_typed_enter_short_projection_keeps_exact_token() -> None:
    decision = _enter_short()
    assert decision.decision_outcome is DecisionOutcome.ENTER_SHORT
    payload = dict(_project(decision)["producer_canonical_payload"])
    assert payload["decision_outcome"] == "enter_short"
    event = _decision_events(_capture(decision))[0]
    assert event["decision_result"] != "NO_ACTION"


def test_typed_exit_with_non_none_exit_class() -> None:
    decision = _exit_non_none()
    assert decision.decision_outcome is DecisionOutcome.EXIT
    assert decision.exit_class is not ExitClass.NONE
    payload = dict(_project(decision)["producer_canonical_payload"])
    assert payload["decision_outcome"] == "exit"
    assert payload["exit_class"] == decision.exit_class.value
    assert payload["exit_class"] != "none"


def test_typed_reduce_projection() -> None:
    decision = _reduce()
    assert decision.decision_outcome is DecisionOutcome.REDUCE
    payload = dict(_project(decision)["producer_canonical_payload"])
    assert payload["decision_outcome"] == "reduce"
    event = _decision_events(_capture(decision))[0]
    assert event["decision_result"] != "NO_ACTION"


def test_typed_hold_is_not_no_action() -> None:
    hold = _hold()
    no_action = _no_action()
    assert hold.decision_outcome is DecisionOutcome.HOLD
    assert no_action.decision_outcome is DecisionOutcome.NO_ACTION
    hold_payload = dict(_project(hold)["producer_canonical_payload"])
    no_action_payload = dict(_project(no_action)["producer_canonical_payload"])
    assert hold_payload["decision_outcome"] == "hold"
    assert no_action_payload["decision_outcome"] == "no_action"
    assert hold_payload["decision_outcome"] != no_action_payload["decision_outcome"]
    hold_event = _decision_events(_capture(hold))[0]
    no_action_event = _decision_events(_capture(no_action))[0]
    assert hold_event["decision_result"] == UNKNOWN
    assert no_action_event["decision_result"] == "NO_ACTION"
    assert hold_event["decision_result"] != no_action_event["decision_result"]


def test_reversal_preparation_fields() -> None:
    decision = _reversal()
    assert decision.exit_class is ExitClass.REVERSAL_PREPARATION_EXIT
    assert decision.reversal_state is ReversalState.PREPARATION
    payload = dict(_project(decision)["producer_canonical_payload"])
    assert payload["reversal_state"] == "preparation"
    assert payload["exit_class"] == "reversal_preparation_exit"
    assert any("reversal" in str(item).lower() for item in payload["decision_precedence_trace"])


def test_position_lifecycle_fields() -> None:
    decision = _hold()
    payload = dict(_project(decision)["producer_canonical_payload"])
    assert payload["position_state"] == PositionState.OPEN_FULL.value
    assert payload["reconciliation_state"] == decision.reconciliation_state.value
    assert payload["position_management_action"] == PositionManagementAction.HOLD.value


def test_reduce_only_true_and_false_retained() -> None:
    entered = dict(_project(_enter_long())["producer_canonical_payload"])
    reduced = dict(_project(_reduce())["producer_canonical_payload"])
    assert entered["reduce_only"] is False
    assert reduced["reduce_only"] is True


def test_position_flip_allowed_retained_exactly() -> None:
    for decision in (_enter_long(), _reduce(), _hold(), _reversal()):
        payload = dict(_project(decision)["producer_canonical_payload"])
        assert payload["position_flip_allowed"] is decision.position_flip_allowed


def test_entry_eligibility_exact() -> None:
    decision = _enter_long()
    payload = dict(_project(decision)["producer_canonical_payload"])
    assert payload["entry_eligibility"] == decision.entry_eligibility.value


def test_instrument_id_and_trading_epoch_exact() -> None:
    decision = _enter_long()
    payload = dict(_project(decision)["producer_canonical_payload"])
    assert payload["instrument_id"] == decision.instrument_id
    assert payload["trading_epoch"] == decision.trading_epoch


def test_selected_side_is_not_bull_bear_next_state() -> None:
    decision = _enter_long()
    observation = _project(decision)
    payload = dict(observation["producer_canonical_payload"])
    assert payload["selected_side"] == decision.selected_side.value
    assert observation["selected_side_semantic_class"] == SELECTED_SIDE_SEMANTIC_CLASS
    assert observation["side_state_after"] != payload["selected_side"]
    assert observation["side_state_after"] == SIDE_STATE_AFTER_STATUS_UNAVAILABLE
    assert observation["side_state_after_status"] == SIDE_STATE_AFTER_STATUS_UNAVAILABLE
    assert (
        observation["previous_direction_state_semantic_class"]
        == PREVIOUS_DIRECTION_STATE_SEMANTIC_CLASS
    )
    assert payload["previous_direction_state"] == decision.previous_direction_state.value


def test_side_state_after_remains_explicit_unavailable() -> None:
    observation = _project(_enter_short())
    assert observation["side_state_after_status"] == SIDE_STATE_AFTER_STATUS_UNAVAILABLE
    assert observation["side_state_after"] in {SIDE_STATE_AFTER_STATUS_UNAVAILABLE, UNKNOWN}


def test_projection_parity_against_producer_canonical_serializer() -> None:
    decisions = (
        _enter_long(),
        _enter_short(),
        _exit_non_none(),
        _reduce(),
        _hold(),
        _no_action(),
        _reversal(),
    )
    for decision in decisions:
        assert is_typed_entry_exit_policy_decision_v1(decision)
        expected = json.loads(serialize_entry_exit_policy_decision_canonical(decision))
        projected = producer_canonical_payload_from_decision_v1(decision)
        assert set(projected) == set(PRODUCER_CANONICAL_KEYS)
        assert projected == expected
        observation = _project(decision)
        assert dict(observation["producer_canonical_payload"]) == expected
        assert observation["semantic_digest"] == decision.semantic_digest
        assert observation["trading_authority"] == TRADING_AUTHORITY_NONE
        for key in PRODUCER_CANONICAL_KEYS:
            assert projected[key] == expected[key]


def test_real_host_cycle_typed_capture() -> None:
    decision = _enter_long()
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=None)
    replay = SimpleNamespace(
        intermediate=SimpleNamespace(entry_exit_decision=decision),
        evidence=None,
    )
    summary = record_productive_cycle_capture_v0(
        binding,
        repository_sha=UNKNOWN,
        session_id="host-dp-parity",
        cycle_index=1,
        event_ts_unix=EVENT_UNIX,
        replay=replay,
    )
    assert summary["ok"] is True
    assert summary["decision_unchanged"] is True
    observations = _observations(binding)
    assert len(observations) == 1
    payload = dict(observations[0]["producer_canonical_payload"])
    assert payload["decision_outcome"] == "enter_long"
    events = _double_play_events(binding)
    assert len(events) == 1
    assert events[0]["decision_result"] != "NO_ACTION"
    assert events[0]["producer_id"] == "double_play_entry_exit_policy_v0"


def test_dual_capture_does_not_duplicate_same_decision_event() -> None:
    decision = _enter_long()
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=None)
    bind_host_cycle_capture_context_v0(
        binding,
        event_ts_unix=EVENT_UNIX,
        session_id="host-dp-parity",
        cycle_index=1,
        repository_sha=UNKNOWN,
    )
    observe_producer_result_v0(
        binding,
        seam_id=SEAM_DOUBLE_PLAY_ENTRY_EXIT,
        result=decision,
    )
    first_dp_event_ids = tuple(item["record_id"] for item in _double_play_events(binding))
    first_obs_ids = tuple(item["record_id"] for item in _observations(binding))
    replay = SimpleNamespace(
        intermediate=SimpleNamespace(entry_exit_decision=decision),
        evidence=None,
    )
    record_productive_cycle_capture_v0(
        binding,
        repository_sha=UNKNOWN,
        session_id="host-dp-parity",
        cycle_index=1,
        event_ts_unix=EVENT_UNIX,
        replay=replay,
    )
    assert tuple(item["record_id"] for item in _double_play_events(binding)) == first_dp_event_ids
    assert tuple(item["record_id"] for item in _observations(binding)) == first_obs_ids
    assert len(first_dp_event_ids) == 1
    assert len(first_obs_ids) == 1


def test_capture_disabled_vs_enabled_producer_result_equal() -> None:
    from trading.master_v2.double_play_entry_exit_policy_v0 import DoublePlayEntryExitPolicyV0
    from tests.trading.master_v2.test_double_play_entry_exit_policy_v0 import _policy_input

    inp = _policy_input()
    policy = DoublePlayEntryExitPolicyV0()
    without = evaluate_double_play_entry_exit_policy_v0(inp, policy)
    disabled = DdoCaptureBindingV0(enabled=False, ledger_path=None)
    token = bind_capture_session_v0(disabled)
    try:
        with_disabled = evaluate_double_play_entry_exit_policy_v0(inp, policy)
    finally:
        reset_capture_session_v0(token)
    enabled = DdoCaptureBindingV0(enabled=True, ledger_path=None)
    bind_host_cycle_capture_context_v0(
        enabled,
        event_ts_unix=EVENT_UNIX,
        session_id="parity-enable",
        cycle_index=1,
        repository_sha=UNKNOWN,
    )
    token = bind_capture_session_v0(enabled)
    try:
        with_enabled = evaluate_double_play_entry_exit_policy_v0(inp, policy)
    finally:
        reset_capture_session_v0(token)
    assert with_disabled == without
    assert with_enabled == without
    assert enabled.captured_records


def test_capture_exception_keeps_productive_return_identical() -> None:
    from trading.master_v2.double_play_entry_exit_policy_v0 import DoublePlayEntryExitPolicyV0
    from tests.trading.master_v2.test_double_play_entry_exit_policy_v0 import _policy_input

    inp = _policy_input()
    policy = DoublePlayEntryExitPolicyV0()
    without = evaluate_double_play_entry_exit_policy_v0(inp, policy)
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=None)
    token = bind_capture_session_v0(binding)
    import src.learning.deterministic_decision_outcome_v0.capture_v0 as capture_mod

    original = capture_mod.observe_producer_result_v0

    def _boom(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("forced-ddo-capture-failure")

    try:
        capture_mod.observe_producer_result_v0 = _boom  # type: ignore[method-assign]
        with_capture = evaluate_double_play_entry_exit_policy_v0(inp, policy)
    finally:
        capture_mod.observe_producer_result_v0 = original
        reset_capture_session_v0(token)
    assert with_capture == without
    assert binding.last_error is not None
    assert "forced-ddo-capture-failure" in str(binding.last_error)


def test_ddo_failure_does_not_propagate_to_trading_producer() -> None:
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=None)
    token = bind_capture_session_v0(binding)
    original = observe_producer_result_v0
    try:
        import src.learning.deterministic_decision_outcome_v0.capture_v0 as capture_mod

        def _boom(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("ddo-isolated")

        capture_mod.observe_producer_result_v0 = _boom  # type: ignore[method-assign]
        produced = _evaluate()
    finally:
        capture_mod.observe_producer_result_v0 = original
        reset_capture_session_v0(token)
    assert produced.decision_outcome is DecisionOutcome.ENTER_LONG
    assert binding.last_error is not None
    assert produced.authority_effect == "NONE"


def test_no_ddo_import_into_29p_safety_29q_execution_live() -> None:
    hits: list[str] = []
    for path in (
        PACKAGE_DIR / "capture_v0.py",
        PACKAGE_DIR / "double_play_observation_projection_v1.py",
        PACKAGE_DIR / "double_play_input_evidence_v1.py",
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            for name in names:
                if any(
                    name == prefix or name.startswith(prefix + ".")
                    for prefix in FORBIDDEN_IMPORT_PREFIXES
                ):
                    hits.append(f"{path.name}:{name}")
                lowered = name.lower()
                if any(
                    token in lowered
                    for token in (
                        "step_29p",
                        "capital_risk_sizing",
                        "safety_kernel",
                        "step_29q",
                        "canonical_order_intent",
                    )
                ):
                    hits.append(f"{path.name}:{name}")
    assert hits == []


def test_trade_tokens_are_not_all_serialized_as_no_action() -> None:
    for factory in (_enter_long(), _enter_short(), _exit_non_none(), _reduce(), _hold()):
        payload = dict(_project(factory)["producer_canonical_payload"])
        assert payload["decision_outcome"] in TRADE_OUTCOMES
        event = _decision_events(_capture(factory))[0]
        assert event["decision_result"] != "NO_ACTION"
        assert event["decision_type"] == UNKNOWN
