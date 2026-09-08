"""Typed Double-Play DDO semantic replay parity v1.

Proves persisted immutable typed observation evidence is sufficient to
reconstruct producer OUTPUT semantics. Does not re-run the producer
function. Classifier replay remains distinct. C remains output-semantic
parity even though producer input is now available via a later capture slice.
"""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path
from typing import Any

import pytest

from src.learning.deterministic_decision_outcome_v0.double_play_observation_projection_v1 import (
    SIDE_STATE_AFTER_STATUS_UNAVAILABLE,
    TYPED_PROJECTION_STATUS,
    UNAVAILABLE_PROJECTION_STATUS,
    project_entry_exit_policy_decision_v1,
)
from src.learning.deterministic_decision_outcome_v0.double_play_semantic_replay_v1 import (
    CLASSIFIER_REPLAY_EVALUATOR_ID,
    COMPARISON_MISMATCH,
    COMPARISON_PASS,
    COMPARISON_UNAVAILABLE,
    EXECUTION_AUTHORITY,
    OFFLINE_EVALUATION_AUTHORITY,
    PRODUCER_FUNCTION_REPLAY_REASON,
    PRODUCER_FUNCTION_REPLAY_REASON_HISTORICAL_AT_C_PERSIST,
    PRODUCER_FUNCTION_REPLAY_STATUS,
    REPLAY_CLASS,
    REPLAY_PRODUCTIVE_AUTHORITY,
    SEMANTIC_REPLAY_EVALUATOR_ID,
    STATUS_INSUFFICIENT_EVIDENCE,
    STATUS_NOT_REPLAYABLE,
    STATUS_REPLAYABLE,
    STATUS_SEMANTIC_MISMATCH,
    STATUS_VERSION_MISMATCH,
    TRADING_AUTHORITY,
    classifier_replay_is_distinct_from_semantic_replay_v1,
    replay_double_play_typed_observation_v1,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.replay_evaluator_v0 import (
    classify_decision_event_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitPolicyDecisionV0,
    serialize_entry_exit_policy_decision_canonical,
)
from tests.learning.test_ddo_current_double_play_decision_capture_parity_v1 import (
    FORBIDDEN_IMPORT_PREFIXES,
    _capture,
    _decision_events,
    _enter_long,
    _enter_short,
    _exit_non_none,
    _hold,
    _no_action,
    _observations,
    _reduce,
    _reversal,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "src" / "learning" / "deterministic_decision_outcome_v0"
SEMANTIC_REPLAY_PATH = PACKAGE_DIR / "double_play_semantic_replay_v1.py"
REPLAY_EVALUATOR_PATH = PACKAGE_DIR / "replay_evaluator_v0.py"


def _producer_payload(decision: EntryExitPolicyDecisionV0) -> dict[str, Any]:
    raw = serialize_entry_exit_policy_decision_canonical(decision)
    payload = json.loads(raw)
    assert isinstance(payload, dict)
    return payload


def _persist(decision: EntryExitPolicyDecisionV0) -> tuple[dict[str, Any], dict[str, Any]]:
    binding = _capture(decision)
    observation = dict(_observations(binding)[0])
    event = dict(_decision_events(binding)[0])
    return observation, event


def _replay(
    observation: dict[str, Any],
    *,
    decision: EntryExitPolicyDecisionV0 | None = None,
    event: dict[str, Any] | None = None,
    later_information: dict[str, Any] | None = None,
) -> Any:
    expected = _producer_payload(decision) if decision is not None else None
    return replay_double_play_typed_observation_v1(
        observation,
        decision_event=event,
        comparison_canonical_payload=expected,
        later_information=later_information,
    )


def test_enter_replay_parity() -> None:
    decision = _enter_long()
    assert decision.decision_outcome is DecisionOutcome.ENTER_LONG
    observation, event = _persist(decision)
    result = _replay(observation, decision=decision, event=event)
    assert result["status"] == STATUS_REPLAYABLE
    assert result["comparison"] == COMPARISON_PASS
    assert result["replayed_semantics"]["decision_outcome"] == "enter_long"
    assert result["mapped_decision_result"] == UNKNOWN


def test_exit_replay_parity() -> None:
    decision = _exit_non_none()
    assert decision.decision_outcome is DecisionOutcome.EXIT
    observation, event = _persist(decision)
    result = _replay(observation, decision=decision, event=event)
    assert result["status"] == STATUS_REPLAYABLE
    assert result["replayed_semantics"]["decision_outcome"] == "exit"
    assert result["replayed_semantics"]["exit_class"] == decision.exit_class.value


def test_hold_and_no_action_replay_parity() -> None:
    hold = _hold()
    no_action = _no_action()
    hold_obs, hold_event = _persist(hold)
    no_action_obs, no_action_event = _persist(no_action)
    hold_result = _replay(hold_obs, decision=hold, event=hold_event)
    no_action_result = _replay(no_action_obs, decision=no_action, event=no_action_event)
    assert hold_result["status"] == STATUS_REPLAYABLE
    assert no_action_result["status"] == STATUS_REPLAYABLE
    assert hold_result["replayed_semantics"]["decision_outcome"] == "hold"
    assert no_action_result["replayed_semantics"]["decision_outcome"] == "no_action"
    assert hold_result["mapped_decision_result"] == UNKNOWN
    assert no_action_result["mapped_decision_result"] == "NO_ACTION"


def test_reversal_semantics_parity() -> None:
    decision = _reversal()
    observation, event = _persist(decision)
    result = _replay(observation, decision=decision, event=event)
    assert result["status"] == STATUS_REPLAYABLE
    semantics = result["replayed_semantics"]
    assert semantics["reversal_state"] == "preparation"
    assert semantics["exit_class"] == "reversal_preparation_exit"
    assert any("reversal" in str(item).lower() for item in semantics["decision_precedence_trace"])


def test_position_management_fields_parity() -> None:
    decision = _hold()
    observation, event = _persist(decision)
    result = _replay(observation, decision=decision, event=event)
    assert result["replayed_semantics"]["position_management_action"] == (
        decision.position_management_action.value
    )
    entered = _enter_long()
    entered_obs, entered_event = _persist(entered)
    entered_result = _replay(entered_obs, decision=entered, event=entered_event)
    assert entered_result["replayed_semantics"]["entry_eligibility"] == "eligible"


def test_precedence_trace_parity() -> None:
    decision = _exit_non_none()
    observation, event = _persist(decision)
    result = _replay(observation, decision=decision, event=event)
    assert list(result["replayed_semantics"]["decision_precedence_trace"]) == list(
        decision.decision_precedence_trace
    )


def test_reduce_only_parity() -> None:
    entered = _enter_long()
    reduced = _reduce()
    entered_obs, entered_event = _persist(entered)
    reduced_obs, reduced_event = _persist(reduced)
    entered_result = _replay(entered_obs, decision=entered, event=entered_event)
    reduced_result = _replay(reduced_obs, decision=reduced, event=reduced_event)
    assert entered_result["replayed_semantics"]["reduce_only"] is False
    assert reduced_result["replayed_semantics"]["reduce_only"] is True


def test_position_flip_allowed_parity() -> None:
    for factory in (_enter_long, _reduce, _hold, _reversal):
        decision = factory()
        observation, event = _persist(decision)
        result = _replay(observation, decision=decision, event=event)
        replayed_payload = result["replayed_semantics"]["producer_canonical_payload"]
        assert replayed_payload["position_flip_allowed"] == decision.position_flip_allowed


def test_position_state_parity() -> None:
    decision = _hold()
    observation, event = _persist(decision)
    result = _replay(observation, decision=decision, event=event)
    assert result["replayed_semantics"]["position_state"] == decision.position_state.value


def test_reconciliation_state_parity_where_evidence_exists() -> None:
    decision = _hold()
    observation, event = _persist(decision)
    result = _replay(observation, decision=decision, event=event)
    assert result["replayed_semantics"]["reconciliation_state"] == (
        decision.reconciliation_state.value
    )


def test_side_state_after_unavailable_preserved() -> None:
    decision = _enter_short()
    observation, event = _persist(decision)
    result = _replay(observation, decision=decision, event=event)
    assert result["side_state_after"] == SIDE_STATE_AFTER_STATUS_UNAVAILABLE
    assert result["unavailable_preserved"] is True
    assert result["replayed_semantics"]["side_state_after"] == SIDE_STATE_AFTER_STATUS_UNAVAILABLE
    assert result["replayed_semantics"]["side_state_before"] == (
        decision.previous_direction_state.value
    )


def test_identical_evidence_stable_replay_result_hash() -> None:
    decision = _enter_long()
    observation, event = _persist(decision)
    first = _replay(observation, decision=decision, event=event)
    second = _replay(observation, decision=decision, event=event)
    assert first["status"] == STATUS_REPLAYABLE
    assert first["replay_input_hash"] == second["replay_input_hash"]
    assert first["replay_result_hash"] == second["replay_result_hash"]
    assert first["replay_result_hash"] != first["replay_input_hash"]


def test_mutated_evidence_deterministic_mismatch() -> None:
    decision = _enter_long()
    observation, event = _persist(decision)
    mutated = copy.deepcopy(observation)
    payload = dict(mutated["producer_canonical_payload"])
    payload["decision_outcome"] = "hold"
    mutated["producer_canonical_payload"] = payload
    del mutated["content_hash"]
    result = replay_double_play_typed_observation_v1(
        mutated,
        decision_event=event,
        comparison_canonical_payload=_producer_payload(decision),
    )
    assert result["status"] == STATUS_SEMANTIC_MISMATCH
    assert result["comparison"] == COMPARISON_MISMATCH
    assert "decision_outcome" in result["mismatched_fields"] or (
        "comparison_canonical_payload" in result["mismatched_fields"]
    )


def test_missing_required_evidence_insufficient() -> None:
    observation = dict(
        project_entry_exit_policy_decision_v1(
            object(),
            record_id="ddo.dpo.replay.missing.0001",
            event_time_utc="2026-09-05T12:00:00Z",
            correlation_id="ddo.corr.dp.replay.v1",
            cycle_id="cycle:dp:replay:0001",
            decision_event_ref="ddo.dec.replay.0001",
        )
    )
    assert observation["projection_status"] == UNAVAILABLE_PROJECTION_STATUS
    result = replay_double_play_typed_observation_v1(observation)
    assert result["status"] == STATUS_INSUFFICIENT_EVIDENCE
    assert result["comparison"] == COMPARISON_UNAVAILABLE
    assert result["input_evidence_complete"] is False


def test_schema_version_mismatch_explicit() -> None:
    decision = _enter_long()
    observation, _event = _persist(decision)
    mutated = copy.deepcopy(observation)
    mutated["schema_version"] = "double_play_entry_exit_observation_v0"
    result = replay_double_play_typed_observation_v1(mutated)
    assert result["status"] == STATUS_VERSION_MISMATCH
    assert result["schema_version_identified"] is False


def test_no_hindsight_leakage() -> None:
    decision = _enter_long()
    observation, event = _persist(decision)
    with pytest.raises(DdoValidationError, match="HINDSIGHT_LEAKAGE_FORBIDDEN"):
        replay_double_play_typed_observation_v1(
            observation,
            decision_event=event,
            comparison_canonical_payload=_producer_payload(decision),
            later_information={"later_pnl": "1", "fills": []},
        )
    result = _replay(observation, decision=decision, event=event)
    assert result["hindsight_leakage"] is False
    assert result["hindsight_leakage_allowed"] is False
    assert result["decision_time_information_set_preserved"] is True


def test_no_productive_authority() -> None:
    decision = _hold()
    observation, event = _persist(decision)
    result = _replay(observation, decision=decision, event=event)
    assert result["offline_evaluation_authority"] == OFFLINE_EVALUATION_AUTHORITY
    assert result["trading_authority"] == TRADING_AUTHORITY
    assert result["execution_authority"] == EXECUTION_AUTHORITY
    assert result["replay_productive_authority"] == REPLAY_PRODUCTIVE_AUTHORITY
    assert result["producer_function_invoked"] is False
    assert result["producer_function_replay_status"] == PRODUCER_FUNCTION_REPLAY_STATUS
    assert result["producer_function_replay_reason"] == PRODUCER_FUNCTION_REPLAY_REASON
    assert (
        PRODUCER_FUNCTION_REPLAY_REASON != PRODUCER_FUNCTION_REPLAY_REASON_HISTORICAL_AT_C_PERSIST
    )
    assert PRODUCER_FUNCTION_REPLAY_REASON != "PRODUCER_INPUT_NOT_IN_IMMUTABLE_EVIDENCE"
    assert result["producer_function_replay_reason"] != ("PRODUCER_INPUT_NOT_IN_IMMUTABLE_EVIDENCE")


def test_no_execution_runtime_import_path_created() -> None:
    hits: list[str] = []
    for path in (SEMANTIC_REPLAY_PATH, REPLAY_EVALUATOR_PATH):
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
    source = SEMANTIC_REPLAY_PATH.read_text(encoding="utf-8")
    assert "evaluate_double_play_entry_exit_policy_v0" in source
    assert "producer_function_invoked" in source
    assert "from trading.master_v2.double_play_entry_exit_policy_v0 import (" in source
    assert "evaluate_double_play_entry_exit_policy_v0," not in source
    assert "evaluate_double_play_entry_exit_policy_v0(" not in source
    assert "PRODUCER_FUNCTION_REPLAY_REASON_HISTORICAL_AT_C_PERSIST" in source
    assert hits == []


def test_classifier_replay_remains_distinguishable() -> None:
    decision = _enter_long()
    observation, event = _persist(decision)
    classifier = classify_decision_event_v0(event)
    semantic = _replay(observation, decision=decision, event=event)
    assert classifier["evaluator_id"] == CLASSIFIER_REPLAY_EVALUATOR_ID
    assert semantic["evaluator_id"] == SEMANTIC_REPLAY_EVALUATOR_ID
    assert semantic["replay_class"] == REPLAY_CLASS
    assert classifier_replay_is_distinct_from_semantic_replay_v1(classifier, semantic)
    assert "producer_canonical_payload" not in classifier
    assert semantic["replayed_semantics"]["decision_outcome"] == "enter_long"


def test_unsupported_schema_not_replayable() -> None:
    decision = _enter_long()
    observation, _event = _persist(decision)
    mutated = copy.deepcopy(observation)
    mutated["schema_name"] = "decision_event"
    result = replay_double_play_typed_observation_v1(mutated)
    assert result["status"] == STATUS_NOT_REPLAYABLE


def test_replay_does_not_call_projection_as_both_sides() -> None:
    decision = _reduce()
    live_payload = _producer_payload(decision)
    observation, event = _persist(decision)
    result = replay_double_play_typed_observation_v1(
        observation,
        decision_event=event,
        comparison_canonical_payload=live_payload,
    )
    assert result["status"] == STATUS_REPLAYABLE
    assert result["replayed_semantics"]["producer_canonical_payload"] == live_payload
    assert observation["projection_status"] == TYPED_PROJECTION_STATUS
    assert result["unknown_preserved"] is True
    assert result["code_sha"] == UNKNOWN
    assert result["code_sha_identified"] is False
    assert result["config_identity_identified"] is False
    assert result["producer_version_identified"] is True
    assert result["schema_version_identified"] is True
    assert result["input_evidence_complete"] is True
