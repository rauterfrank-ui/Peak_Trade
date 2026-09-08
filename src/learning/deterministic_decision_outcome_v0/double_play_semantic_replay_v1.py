"""Offline typed Double-Play semantic replay v1.

Reconstructs producer OUTPUT semantics from immutable typed DDO observation
evidence and compares them with the persisted projection / DecisionEvent.

This is NOT classifier/token replay. It does NOT re-run
``evaluate_double_play_entry_exit_policy_v0``: producer INPUT is not persisted
on current DDO evidence, so producer-function replay is NOT_REPLAYABLE.

OFFLINE_EVALUATION_AUTHORITY=NONE
TRADING_AUTHORITY=NONE
EXECUTION_AUTHORITY=NONE
HINDSIGHT_LEAKAGE_ALLOWED=false
"""

from __future__ import annotations

import json
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_DECISION_EVENT,
    SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION,
    SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_V1,
    freeze_record,
)
from src.learning.deterministic_decision_outcome_v0.double_play_observation_projection_v1 import (
    PRODUCER_CANONICAL_KEYS,
    PRODUCER_OWNER,
    SIDE_STATE_AFTER_STATUS_UNAVAILABLE,
    TYPED_PROJECTION_STATUS,
    UNAVAILABLE_PROJECTION_STATUS,
    generic_decision_result_for_producer_outcome_v1,
    generic_decision_type_for_producer_outcome_v1,
    validate_double_play_entry_exit_observation_v1,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.hindsight_guard_v0 import (
    assert_no_hindsight_safety_relabel_v0,
    assert_safety_inputs_exclude_later_economics_v0,
)
from src.learning.deterministic_decision_outcome_v0.replay_evaluator_v0 import (
    REPLAY_EVALUATOR_ID,
    classify_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    compute_content_hash_v0,
)

SEMANTIC_REPLAY_EVALUATOR_ID: Final[str] = "peak_trade.learning.ddo.double_play_semantic_replay_v1"
REPLAY_CLASS: Final[str] = "TYPED_PRODUCER_OUTPUT_SEMANTIC_REPLAY"
CLASSIFIER_REPLAY_EVALUATOR_ID: Final[str] = REPLAY_EVALUATOR_ID
OFFLINE_EVALUATION_AUTHORITY: Final[str] = "NONE"
TRADING_AUTHORITY: Final[str] = "NONE"
EXECUTION_AUTHORITY: Final[str] = "NONE"
REPLAY_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
HINDSIGHT_LEAKAGE_ALLOWED: Final[bool] = False
PRODUCER_FUNCTION_REPLAY_STATUS: Final[str] = "NOT_REPLAYABLE"
PRODUCER_FUNCTION_REPLAY_REASON: Final[str] = "PRODUCER_INPUT_NOT_IN_IMMUTABLE_EVIDENCE"
PRODUCER_FUNCTION_NAME: Final[str] = "evaluate_double_play_entry_exit_policy_v0"

STATUS_REPLAYABLE: Final[str] = "REPLAYABLE"
STATUS_NOT_REPLAYABLE: Final[str] = "NOT_REPLAYABLE"
STATUS_INSUFFICIENT_EVIDENCE: Final[str] = "INSUFFICIENT_EVIDENCE"
STATUS_VERSION_MISMATCH: Final[str] = "VERSION_MISMATCH"
STATUS_SEMANTIC_MISMATCH: Final[str] = "SEMANTIC_MISMATCH"

COMPARISON_PASS: Final[str] = "PASS"
COMPARISON_MISMATCH: Final[str] = "MISMATCH"
COMPARISON_UNAVAILABLE: Final[str] = "UNAVAILABLE"
COMPARISON_NOT_REPLAYABLE: Final[str] = "NOT_REPLAYABLE"

_HINDSIGHT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "later_price",
        "later_prices",
        "fill",
        "fills",
        "pnl",
        "later_pnl",
        "later_outcome",
        "actual_outcome_ref",
        "attribution_label",
        "attribution_labels",
        "later_reconciliation_result",
        "later_reconciliation_results",
        "later_economic_path",
        "later_favorable_price_move",
        "economic_score",
        "evaluation_time_information_set_ref",
    }
)

_ENUM_FIELDS: Final[tuple[tuple[str, str], ...]] = (
    ("previous_direction_state", "EntryExitDirectionState"),
    ("position_state", "PositionState"),
    ("reconciliation_state", "ReconciliationState"),
    ("decision_outcome", "DecisionOutcome"),
    ("entry_eligibility", "EntryEligibility"),
    ("exit_class", "ExitClass"),
    ("position_management_action", "PositionManagementAction"),
    ("reversal_state", "ReversalState"),
    ("selected_side", "CompositionSelectedSide"),
)


def replay_double_play_typed_observation_v1(
    observation: Mapping[str, Any],
    *,
    decision_event: Mapping[str, Any] | None = None,
    comparison_canonical_payload: Mapping[str, Any] | None = None,
    later_information: Mapping[str, Any] | None = None,
) -> MappingProxyType[str, Any]:
    """Replay typed Double-Play producer OUTPUT semantics from immutable evidence."""
    _reject_hindsight(observation, decision_event, later_information)
    schema_name = observation.get("schema_name")
    schema_version = observation.get("schema_version")
    if schema_name != SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION:
        return _finish(
            status=STATUS_NOT_REPLAYABLE,
            comparison=COMPARISON_NOT_REPLAYABLE,
            reason_codes=("UNSUPPORTED_SCHEMA",),
            observation=observation,
            decision_event=decision_event,
            replayed_payload=None,
            mismatched_fields=(),
        )
    if schema_version != SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_V1:
        return _finish(
            status=STATUS_VERSION_MISMATCH,
            comparison=COMPARISON_NOT_REPLAYABLE,
            reason_codes=("SCHEMA_VERSION_MISMATCH",),
            observation=observation,
            decision_event=decision_event,
            replayed_payload=None,
            mismatched_fields=(),
        )
    validated = validate_double_play_entry_exit_observation_v1(observation)
    if validated["projection_status"] != TYPED_PROJECTION_STATUS:
        reason = (
            "TYPED_PROJECTION_UNAVAILABLE"
            if validated["projection_status"] == UNAVAILABLE_PROJECTION_STATUS
            else "TYPED_PROJECTION_REQUIRED"
        )
        return _finish(
            status=STATUS_INSUFFICIENT_EVIDENCE,
            comparison=COMPARISON_UNAVAILABLE,
            reason_codes=(reason,),
            observation=validated,
            decision_event=decision_event,
            replayed_payload=None,
            mismatched_fields=(),
        )
    persisted_payload = validated["producer_canonical_payload"]
    if not isinstance(persisted_payload, Mapping):
        return _finish(
            status=STATUS_INSUFFICIENT_EVIDENCE,
            comparison=COMPARISON_UNAVAILABLE,
            reason_codes=("PRODUCER_CANONICAL_PAYLOAD_MISSING",),
            observation=validated,
            decision_event=decision_event,
            replayed_payload=None,
            mismatched_fields=(),
        )
    reconstructed = _reconstruct_typed_decision_v1(
        dict(persisted_payload),
        semantic_digest=str(validated["semantic_digest"]),
    )
    if reconstructed is None:
        return _finish(
            status=STATUS_NOT_REPLAYABLE,
            comparison=COMPARISON_NOT_REPLAYABLE,
            reason_codes=("PRODUCER_TYPES_UNAVAILABLE",),
            observation=validated,
            decision_event=decision_event,
            replayed_payload=None,
            mismatched_fields=(),
        )
    if isinstance(reconstructed, str):
        return _finish(
            status=STATUS_NOT_REPLAYABLE,
            comparison=COMPARISON_NOT_REPLAYABLE,
            reason_codes=(reconstructed,),
            observation=validated,
            decision_event=decision_event,
            replayed_payload=None,
            mismatched_fields=(),
        )
    serializer, digest_fn = _producer_helpers()
    if serializer is None or digest_fn is None:
        return _finish(
            status=STATUS_NOT_REPLAYABLE,
            comparison=COMPARISON_NOT_REPLAYABLE,
            reason_codes=("PRODUCER_SERIALIZER_UNAVAILABLE",),
            observation=validated,
            decision_event=decision_event,
            replayed_payload=None,
            mismatched_fields=(),
        )
    replayed_raw = serializer(reconstructed)
    if not isinstance(replayed_raw, str):
        raise DdoValidationError("PRODUCER_CANONICAL_SERIALIZER_MUST_RETURN_STRING")
    replayed_payload = json.loads(replayed_raw)
    if not isinstance(replayed_payload, dict):
        raise DdoValidationError("PRODUCER_CANONICAL_PAYLOAD_MUST_BE_OBJECT")
    recomputed_digest = digest_fn(reconstructed)
    mismatched: list[str] = []
    if replayed_payload != dict(persisted_payload):
        mismatched.append("producer_canonical_payload")
        for key in PRODUCER_CANONICAL_KEYS:
            if replayed_payload.get(key) != persisted_payload.get(key):
                mismatched.append(key)
    if recomputed_digest != validated["semantic_digest"]:
        mismatched.append("semantic_digest")
    if comparison_canonical_payload is not None:
        expected = dict(comparison_canonical_payload)
        if replayed_payload != expected:
            mismatched.append("comparison_canonical_payload")
            for key in PRODUCER_CANONICAL_KEYS:
                if replayed_payload.get(key) != expected.get(key):
                    mismatched.append(f"expected:{key}")
    mapped_result = generic_decision_result_for_producer_outcome_v1(
        str(replayed_payload["decision_outcome"])
    )
    mapped_type = generic_decision_type_for_producer_outcome_v1(
        str(replayed_payload["decision_outcome"])
    )
    if decision_event is not None:
        if decision_event.get("schema_name") != SCHEMA_NAME_DECISION_EVENT:
            return _finish(
                status=STATUS_NOT_REPLAYABLE,
                comparison=COMPARISON_NOT_REPLAYABLE,
                reason_codes=("DECISION_EVENT_SCHEMA_REQUIRED",),
                observation=validated,
                decision_event=decision_event,
                replayed_payload=replayed_payload,
                mismatched_fields=tuple(dict.fromkeys(mismatched)),
            )
        classified = classify_decision_event_v0(decision_event)
        if classified["decision_result"] != mapped_result:
            mismatched.append("decision_result")
        if classified["decision_type"] != mapped_type:
            mismatched.append("decision_type")
        if classified["evaluator_id"] != CLASSIFIER_REPLAY_EVALUATOR_ID:
            mismatched.append("classifier_evaluator_id")
    side_after = validated["side_state_after"]
    if side_after != SIDE_STATE_AFTER_STATUS_UNAVAILABLE:
        mismatched.append("side_state_after")
    if validated["side_state_after_status"] != SIDE_STATE_AFTER_STATUS_UNAVAILABLE:
        mismatched.append("side_state_after_status")
    unique_mismatched = tuple(dict.fromkeys(mismatched))
    if unique_mismatched:
        return _finish(
            status=STATUS_SEMANTIC_MISMATCH,
            comparison=COMPARISON_MISMATCH,
            reason_codes=("SEMANTIC_MISMATCH", *unique_mismatched),
            observation=validated,
            decision_event=decision_event,
            replayed_payload=replayed_payload,
            mismatched_fields=unique_mismatched,
            mapped_decision_result=mapped_result,
            mapped_decision_type=mapped_type,
            reconstructed_digest=recomputed_digest,
        )
    return _finish(
        status=STATUS_REPLAYABLE,
        comparison=COMPARISON_PASS,
        reason_codes=("SEMANTIC_REPLAY_PARITY",),
        observation=validated,
        decision_event=decision_event,
        replayed_payload=replayed_payload,
        mismatched_fields=(),
        mapped_decision_result=mapped_result,
        mapped_decision_type=mapped_type,
        reconstructed_digest=recomputed_digest,
    )


def classifier_replay_is_distinct_from_semantic_replay_v1(
    classifier_result: Mapping[str, Any],
    semantic_result: Mapping[str, Any],
) -> bool:
    """True when classifier replay is not the typed semantic replay."""
    return (
        classifier_result.get("evaluator_id") == CLASSIFIER_REPLAY_EVALUATOR_ID
        and semantic_result.get("evaluator_id") == SEMANTIC_REPLAY_EVALUATOR_ID
        and classifier_result.get("evaluator_id") != semantic_result.get("evaluator_id")
        and semantic_result.get("replay_class") == REPLAY_CLASS
        and "producer_canonical_payload" not in classifier_result
    )


def _reject_hindsight(
    observation: Mapping[str, Any],
    decision_event: Mapping[str, Any] | None,
    later_information: Mapping[str, Any] | None,
) -> None:
    if later_information is not None:
        if not isinstance(later_information, Mapping):
            raise DdoValidationError("LATER_INFORMATION_MUST_BE_OBJECT")
        extra = sorted(key for key in later_information if key in _HINDSIGHT_KEYS)
        if extra or later_information:
            raise DdoValidationError(
                f"HINDSIGHT_LEAKAGE_FORBIDDEN:{extra or sorted(later_information)}"
            )
        assert_safety_inputs_exclude_later_economics_v0(later_information)
    _scan_hindsight_keys(observation, "observation")
    if decision_event is not None:
        _scan_hindsight_keys(decision_event, "decision_event")
        assert_no_hindsight_safety_relabel_v0(decision_event)
    assert_no_hindsight_safety_relabel_v0(observation)


def _scan_hindsight_keys(payload: Mapping[str, Any], label: str) -> None:
    extra = sorted(key for key in payload if key in _HINDSIGHT_KEYS)
    if extra:
        raise DdoValidationError(f"HINDSIGHT_LEAKAGE_FORBIDDEN:{label}:{extra}")


def _reconstruct_typed_decision_v1(
    payload: dict[str, Any],
    *,
    semantic_digest: str,
) -> Any:
    types = _producer_types()
    if types is None:
        return None
    missing = [key for key in PRODUCER_CANONICAL_KEYS if key not in payload]
    if missing:
        return f"PRODUCER_CANONICAL_KEYS_MISSING:{missing}"
    enums = {
        "EntryExitDirectionState": types["EntryExitDirectionState"],
        "PositionState": types["PositionState"],
        "ReconciliationState": types["ReconciliationState"],
        "DecisionOutcome": types["DecisionOutcome"],
        "EntryEligibility": types["EntryEligibility"],
        "ExitClass": types["ExitClass"],
        "PositionManagementAction": types["PositionManagementAction"],
        "ReversalState": types["ReversalState"],
        "CompositionSelectedSide": types["CompositionSelectedSide"],
    }
    converted: dict[str, Any] = {}
    for field, enum_name in _ENUM_FIELDS:
        raw = payload[field]
        try:
            converted[field] = enums[enum_name](raw)
        except ValueError:
            return f"PRODUCER_TOKEN_UNSUPPORTED:{field}:{raw}"
    for key in ("reduce_only", "position_flip_allowed", "execution_eligible", "adapter_compatible"):
        value = payload[key]
        if not isinstance(value, bool):
            return f"PRODUCER_FIELD_MUST_BE_BOOL:{key}"
        converted[key] = value
    epoch = payload["trading_epoch"]
    if not isinstance(epoch, int) or isinstance(epoch, bool):
        return "PRODUCER_TRADING_EPOCH_MUST_BE_INT"
    reason_codes = payload["reason_codes"]
    trace = payload["decision_precedence_trace"]
    if not isinstance(reason_codes, list) or not all(
        isinstance(item, str) for item in reason_codes
    ):
        return "PRODUCER_REASON_CODES_MUST_BE_STRING_LIST"
    if not isinstance(trace, list) or not all(isinstance(item, str) for item in trace):
        return "PRODUCER_PRECEDENCE_TRACE_MUST_BE_STRING_LIST"
    cls = types["EntryExitPolicyDecisionV0"]
    return cls(
        policy_decision_id=str(payload["policy_decision_id"]),
        instrument_id=str(payload["instrument_id"]),
        trading_epoch=epoch,
        composition_result_ref=str(payload["composition_result_ref"]),
        previous_direction_state=converted["previous_direction_state"],
        position_state=converted["position_state"],
        reconciliation_state=converted["reconciliation_state"],
        decision_outcome=converted["decision_outcome"],
        entry_eligibility=converted["entry_eligibility"],
        exit_class=converted["exit_class"],
        position_management_action=converted["position_management_action"],
        reversal_state=converted["reversal_state"],
        reduce_only=converted["reduce_only"],
        position_flip_allowed=converted["position_flip_allowed"],
        quantity_status=str(payload["quantity_status"]),
        selected_side=converted["selected_side"],
        reason_codes=tuple(reason_codes),
        decision_precedence_trace=tuple(trace),
        policy_version=str(payload["policy_version"]),
        input_digest=str(payload["input_digest"]),
        semantic_digest=semantic_digest,
        execution_eligible=converted["execution_eligible"],
        adapter_compatible=converted["adapter_compatible"],
        authority_effect=str(payload["authority_effect"]),
        runtime_effect=str(payload["runtime_effect"]),
        order_effect=str(payload["order_effect"]),
        risk_sizing_effect=str(payload["risk_sizing_effect"]),
    )


def _producer_types() -> dict[str, Any] | None:
    try:
        from trading.master_v2.double_play_composition_matrix_v1 import (  # noqa: PLC0415
            CompositionSelectedSide,
        )
        from trading.master_v2.double_play_entry_exit_policy_v0 import (  # noqa: PLC0415
            DecisionOutcome,
            EntryEligibility,
            EntryExitDirectionState,
            EntryExitPolicyDecisionV0,
            ExitClass,
            PositionManagementAction,
            PositionState,
            ReconciliationState,
            ReversalState,
        )
    except ImportError:
        return None
    return {
        "CompositionSelectedSide": CompositionSelectedSide,
        "DecisionOutcome": DecisionOutcome,
        "EntryEligibility": EntryEligibility,
        "EntryExitDirectionState": EntryExitDirectionState,
        "EntryExitPolicyDecisionV0": EntryExitPolicyDecisionV0,
        "ExitClass": ExitClass,
        "PositionManagementAction": PositionManagementAction,
        "PositionState": PositionState,
        "ReconciliationState": ReconciliationState,
        "ReversalState": ReversalState,
    }


def _producer_helpers() -> tuple[Any, Any]:
    try:
        from trading.master_v2.double_play_entry_exit_policy_v0 import (  # noqa: PLC0415
            compute_entry_exit_policy_semantic_digest,
            serialize_entry_exit_policy_decision_canonical,
        )
    except ImportError:
        return None, None
    return serialize_entry_exit_policy_decision_canonical, compute_entry_exit_policy_semantic_digest


def _finish(
    *,
    status: str,
    comparison: str,
    reason_codes: tuple[str, ...],
    observation: Mapping[str, Any],
    decision_event: Mapping[str, Any] | None,
    replayed_payload: dict[str, Any] | None,
    mismatched_fields: tuple[str, ...],
    mapped_decision_result: str | None = None,
    mapped_decision_type: str | None = None,
    reconstructed_digest: str | None = None,
) -> MappingProxyType[str, Any]:
    payload = observation.get("producer_canonical_payload")
    persisted_payload = dict(payload) if isinstance(payload, Mapping) else None
    producer_version = None
    if persisted_payload is not None:
        producer_version = persisted_payload.get("policy_version")
    code_sha = observation.get("code_sha", UNKNOWN)
    evidence_hash = observation.get("evidence_hash", UNKNOWN)
    config_hash = UNKNOWN
    if decision_event is not None:
        config_hash = decision_event.get("config_hash", UNKNOWN)
    input_complete = (
        status in {STATUS_REPLAYABLE, STATUS_SEMANTIC_MISMATCH}
        and persisted_payload is not None
        and observation.get("projection_status") == TYPED_PROJECTION_STATUS
    )
    replayed_semantics = None
    if replayed_payload is not None:
        replayed_semantics = {
            "decision_outcome": replayed_payload["decision_outcome"],
            "exit_class": replayed_payload["exit_class"],
            "reversal_state": replayed_payload["reversal_state"],
            "position_management_action": replayed_payload["position_management_action"],
            "entry_eligibility": replayed_payload["entry_eligibility"],
            "reduce_only": replayed_payload["reduce_only"],
            "position_flip_allowed": replayed_payload["position_flip_allowed"],
            "decision_precedence_trace": list(replayed_payload["decision_precedence_trace"]),
            "position_state": replayed_payload["position_state"],
            "reconciliation_state": replayed_payload["reconciliation_state"],
            "side_state_before": replayed_payload["previous_direction_state"],
            "side_state_after": observation.get("side_state_after"),
            "producer_canonical_payload": replayed_payload,
        }
    body = {
        "evaluator_id": SEMANTIC_REPLAY_EVALUATOR_ID,
        "replay_class": REPLAY_CLASS,
        "classifier_replay_evaluator_id": CLASSIFIER_REPLAY_EVALUATOR_ID,
        "classifier_replay_distinct": True,
        "offline_evaluation_authority": OFFLINE_EVALUATION_AUTHORITY,
        "trading_authority": TRADING_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_productive_authority": REPLAY_PRODUCTIVE_AUTHORITY,
        "hindsight_leakage_allowed": False,
        "hindsight_leakage": False,
        "uses_decision_time_information_set": True,
        "decision_time_information_set_preserved": True,
        "producer_function_replay_status": PRODUCER_FUNCTION_REPLAY_STATUS,
        "producer_function_replay_reason": PRODUCER_FUNCTION_REPLAY_REASON,
        "producer_function_name": PRODUCER_FUNCTION_NAME,
        "producer_function_invoked": False,
        "status": status,
        "comparison": comparison,
        "reason_codes": list(reason_codes),
        "mismatched_fields": list(mismatched_fields),
        "schema_name": observation.get("schema_name"),
        "schema_version": observation.get("schema_version"),
        "schema_version_identified": schema_version_ok(observation),
        "projection_id": observation.get("projection_id"),
        "projection_status": observation.get("projection_status"),
        "producer_owner": observation.get("producer_owner", PRODUCER_OWNER),
        "producer_version_ref": producer_version,
        "producer_version_identified": isinstance(producer_version, str) and bool(producer_version),
        "code_sha": code_sha,
        "code_sha_identified": isinstance(code_sha, str) and code_sha != UNKNOWN,
        "config_identity": config_hash,
        "config_identity_identified": isinstance(config_hash, str) and config_hash != UNKNOWN,
        "source_decision_ref": observation.get("decision_event_ref"),
        "source_evidence_hash": evidence_hash,
        "source_observation_content_hash": observation.get("content_hash"),
        "input_evidence_complete": bool(input_complete),
        "unknown_preserved": code_sha == UNKNOWN,
        "unavailable_preserved": observation.get("side_state_after")
        == SIDE_STATE_AFTER_STATUS_UNAVAILABLE,
        "side_state_after": observation.get("side_state_after"),
        "side_state_after_status": observation.get("side_state_after_status"),
        "mapped_decision_result": mapped_decision_result,
        "mapped_decision_type": mapped_decision_type,
        "reconstructed_semantic_digest": reconstructed_digest,
        "persisted_semantic_digest": observation.get("semantic_digest"),
        "replayed_semantics": replayed_semantics,
        "persisted_canonical_payload": persisted_payload,
    }
    replay_input_hash = compute_content_hash_v0(
        {
            "observation_content_hash": observation.get("content_hash"),
            "decision_event_content_hash": (
                decision_event.get("content_hash") if decision_event is not None else None
            ),
            "schema_version": observation.get("schema_version"),
            "projection_id": observation.get("projection_id"),
            "comparison_present": comparison != COMPARISON_UNAVAILABLE,
        }
    )
    replay_result_hash = compute_content_hash_v0(
        {
            "status": status,
            "comparison": comparison,
            "reason_codes": list(reason_codes),
            "mismatched_fields": list(mismatched_fields),
            "replayed_semantics": replayed_semantics,
            "mapped_decision_result": mapped_decision_result,
            "mapped_decision_type": mapped_decision_type,
            "reconstructed_semantic_digest": reconstructed_digest,
            "side_state_after": observation.get("side_state_after"),
        }
    )
    body["replay_input_hash"] = replay_input_hash
    body["replay_result_hash"] = replay_result_hash
    return freeze_record(body)


def schema_version_ok(observation: Mapping[str, Any]) -> bool:
    return observation.get("schema_version") == SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_V1
