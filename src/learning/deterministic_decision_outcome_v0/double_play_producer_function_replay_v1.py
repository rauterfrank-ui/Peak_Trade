"""Offline current-code Double-Play producer-function replay v1.

A = CURRENT_CODE_REPLAY. Invokes the public
``evaluate_double_play_entry_exit_policy_v0`` symbol under explicit
capture-disabled isolation. Compares canonical output against a stored typed
output observation joined by ``typed_output_observation_ref``.

This is not C (output-semantic parity) and not D (input reconstruction).
This is not historical code replay B.

REPLAY_CLASS_LETTER=A
REPLAY_CLASS_SEMANTIC=CURRENT_CODE_REPLAY
REPLAY_CLASS_OWNER_TOKEN=A_CURRENT_CODE_REPLAY
HISTORICAL_CODE_PARITY_CLAIM=false
CODE_SHA_INFERENCE_ALLOWED=false
RESULT_DURABILITY=IN_MEMORY_NO_WRITE
REPLAY_TIMEOUT_POLICY=UNSPECIFIED
REPLAY_EXCEPTION_BLIND_RETRY_ALLOWED=false
WRAPPED_BYPASS_ALLOWED=false
OFFLINE_EVALUATION_AUTHORITY=NONE
TRADING_AUTHORITY=NONE
EXECUTION_AUTHORITY=NONE
REPLAY_PRODUCTIVE_AUTHORITY=NONE
HINDSIGHT_LEAKAGE_ALLOWED=false
"""

from __future__ import annotations

import json
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    ddo_replay_capture_disabled_isolation_reason_v0,
)
from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION,
    SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_V1,
    freeze_record,
)
from src.learning.deterministic_decision_outcome_v0.double_play_input_evidence_v1 import (
    PRODUCER_FUNCTION_NAME,
    SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE,
    SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE_V1,
    TYPED_PROJECTION_STATUS as INPUT_TYPED_PROJECTION_STATUS,
    reconstruct_typed_double_play_entry_exit_policy_input_v1,
    validate_double_play_entry_exit_policy_input_evidence_v1,
)
from src.learning.deterministic_decision_outcome_v0.double_play_observation_projection_v1 import (
    PRODUCER_CANONICAL_KEYS,
    PRODUCER_OWNER,
    TYPED_PROJECTION_STATUS,
    validate_double_play_entry_exit_observation_v1,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError

FUNCTION_REPLAY_EVALUATOR_ID: Final[str] = (
    "peak_trade.learning.ddo.double_play_producer_function_replay_v1"
)
REPLAY_CLASS_LETTER: Final[str] = "A"
REPLAY_CLASS_SEMANTIC: Final[str] = "CURRENT_CODE_REPLAY"
REPLAY_CLASS_OWNER_TOKEN: Final[str] = "A_CURRENT_CODE_REPLAY"
HISTORICAL_CODE_PARITY_CLAIM: Final[bool] = False
OFFLINE_EVALUATION_AUTHORITY: Final[str] = "NONE"
TRADING_AUTHORITY: Final[str] = "NONE"
EXECUTION_AUTHORITY: Final[str] = "NONE"
REPLAY_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
RESULT_DURABILITY: Final[str] = "IN_MEMORY_NO_WRITE"
REPLAY_TIMEOUT_POLICY: Final[str] = "UNSPECIFIED"
REPLAY_OPERATION_ATTEMPT_COUNT_MAX: Final[int] = 1
HINDSIGHT_LEAKAGE_ALLOWED: Final[bool] = False

STATUS_MATCH: Final[str] = "MATCH"
STATUS_MISMATCH: Final[str] = "MISMATCH"
STATUS_REPLAY_BLOCKED: Final[str] = "REPLAY_BLOCKED"
STATUS_REPLAY_INDETERMINATE: Final[str] = "REPLAY_INDETERMINATE"

JOIN_FIELD: Final[str] = "typed_output_observation_ref"

_HINDSIGHT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "later_price",
        "later_prices",
        "later_position",
        "later_positions",
        "fill",
        "fills",
        "pnl",
        "later_pnl",
        "outcome_record",
        "attribution",
        "counterfactual",
        "future_bar",
        "future_bars",
        "hindsight",
        "hindsight_label",
        "later_reconciliation",
        "later_information",
        "current_market",
        "current_account",
        "environment_injection",
    }
)


def replay_double_play_producer_function_current_code_v1(
    input_evidence: Mapping[str, Any],
    typed_output_observations: Sequence[Mapping[str, Any]],
) -> MappingProxyType[str, Any]:
    """Run isolated current-code producer-function replay. In-memory only."""
    stored_code_sha = UNKNOWN
    try:
        _reject_hindsight_mapping(input_evidence, "input_evidence")
        if not isinstance(typed_output_observations, Sequence) or isinstance(
            typed_output_observations, (str, bytes, bytearray)
        ):
            return _finish(
                status=STATUS_REPLAY_BLOCKED,
                reason_codes=("TYPED_OUTPUT_OBSERVATIONS_MUST_BE_SEQUENCE",),
                stored_code_sha=stored_code_sha,
            )
        for item in typed_output_observations:
            if not isinstance(item, Mapping):
                return _finish(
                    status=STATUS_REPLAY_BLOCKED,
                    reason_codes=("TYPED_OUTPUT_OBSERVATION_MUST_BE_OBJECT",),
                    stored_code_sha=stored_code_sha,
                )
            _reject_hindsight_mapping(item, "typed_output_observation")
        validated_input = validate_double_play_entry_exit_policy_input_evidence_v1(input_evidence)
        stored_code_sha = _stored_code_sha(validated_input)
        schema_block = _input_schema_identity_failure(validated_input)
        if schema_block is not None:
            return _finish(
                status=STATUS_REPLAY_BLOCKED,
                reason_codes=schema_block,
                stored_code_sha=stored_code_sha,
            )
        observation, join_block = _resolve_typed_output_observation(
            validated_input,
            typed_output_observations,
        )
        if join_block is not None:
            return _finish(
                status=STATUS_REPLAY_BLOCKED,
                reason_codes=join_block,
                stored_code_sha=stored_code_sha,
            )
        assert observation is not None
        reconstructed_input = reconstruct_typed_double_play_entry_exit_policy_input_v1(
            validated_input
        )
        policy = _reconstruct_policy(validated_input)
    except DdoValidationError as exc:
        return _finish(
            status=STATUS_REPLAY_BLOCKED,
            reason_codes=("INPUT_OR_JOIN_OR_RECONSTRUCTION_FAILURE", type(exc).__name__),
            stored_code_sha=stored_code_sha,
            exception_class=type(exc).__name__,
        )
    except Exception as exc:  # noqa: BLE001
        return _finish(
            status=STATUS_REPLAY_BLOCKED,
            reason_codes=("INPUT_OR_JOIN_OR_RECONSTRUCTION_FAILURE", type(exc).__name__),
            stored_code_sha=stored_code_sha,
            exception_class=type(exc).__name__,
        )

    isolation_reason = ddo_replay_capture_disabled_isolation_reason_v0()
    if isolation_reason is not None:
        return _finish(
            status=STATUS_REPLAY_BLOCKED,
            reason_codes=("CAPTURE_ISOLATION_FAILED", isolation_reason),
            stored_code_sha=stored_code_sha,
            stored_semantic_digest=_stored_digest(observation),
        )

    return _invoke_and_compare(
        reconstructed_input=reconstructed_input,
        policy=policy,
        observation=observation,
        stored_code_sha=stored_code_sha,
    )


def _invoke_and_compare(
    *,
    reconstructed_input: Any,
    policy: Any,
    observation: Mapping[str, Any],
    stored_code_sha: str,
) -> MappingProxyType[str, Any]:
    from trading.master_v2.double_play_entry_exit_policy_v0 import (  # noqa: PLC0415
        compute_entry_exit_policy_semantic_digest,
        evaluate_double_play_entry_exit_policy_v0,
        serialize_entry_exit_policy_decision_canonical,
    )

    producer = evaluate_double_play_entry_exit_policy_v0
    decision = None
    try:
        decision = producer(reconstructed_input, policy)
    except Exception as exc:  # noqa: BLE001
        return _finish(
            status=STATUS_REPLAY_INDETERMINATE,
            reason_codes=("PRODUCER_INVOCATION_EXCEPTION", type(exc).__name__),
            stored_code_sha=stored_code_sha,
            stored_semantic_digest=_stored_digest(observation),
            producer_function_invoked=True,
            producer_invocation_count=1,
            public_producer_symbol_used=True,
            exception_class=type(exc).__name__,
        )

    try:
        serialized = serialize_entry_exit_policy_decision_canonical(decision)
        if not isinstance(serialized, str):
            raise DdoValidationError("PRODUCER_CANONICAL_SERIALIZER_MUST_RETURN_STRING")
        replayed_payload = json.loads(serialized)
        if not isinstance(replayed_payload, dict):
            raise DdoValidationError("PRODUCER_CANONICAL_PAYLOAD_MUST_BE_OBJECT")
        replayed_digest = compute_entry_exit_policy_semantic_digest(decision)
        if not isinstance(replayed_digest, str):
            raise DdoValidationError("PRODUCER_SEMANTIC_DIGEST_MUST_BE_STRING")
        stored_payload = observation.get("producer_canonical_payload")
        if not isinstance(stored_payload, Mapping):
            raise DdoValidationError("STORED_PRODUCER_CANONICAL_PAYLOAD_MISSING")
        stored_digest = observation.get("semantic_digest")
        if not isinstance(stored_digest, str):
            raise DdoValidationError("STORED_SEMANTIC_DIGEST_MISSING")
        mismatch_fields = _enumerate_mismatch_fields(
            replayed_payload=replayed_payload,
            stored_payload=dict(stored_payload),
            replayed_digest=replayed_digest,
            stored_digest=stored_digest,
        )
    except Exception as exc:  # noqa: BLE001
        return _finish(
            status=STATUS_REPLAY_INDETERMINATE,
            reason_codes=("SERIALIZATION_OR_DIGEST_OR_COMPARE_FAILURE", type(exc).__name__),
            stored_code_sha=stored_code_sha,
            stored_semantic_digest=_stored_digest(observation),
            producer_function_invoked=True,
            producer_invocation_count=1,
            public_producer_symbol_used=True,
            exception_class=type(exc).__name__,
        )

    matched = not mismatch_fields
    return _finish(
        status=STATUS_MATCH if matched else STATUS_MISMATCH,
        reason_codes=("SEMANTIC_MATCH",) if matched else ("SEMANTIC_MISMATCH", *mismatch_fields),
        stored_code_sha=stored_code_sha,
        stored_semantic_digest=stored_digest,
        replayed_semantic_digest=replayed_digest,
        mismatch_fields=mismatch_fields,
        producer_function_invoked=True,
        producer_invocation_count=1,
        public_producer_symbol_used=True,
        replayed_payload=replayed_payload,
    )


def _enumerate_mismatch_fields(
    *,
    replayed_payload: Mapping[str, Any],
    stored_payload: Mapping[str, Any],
    replayed_digest: str,
    stored_digest: str,
) -> tuple[str, ...]:
    mismatched: list[str] = []
    if dict(replayed_payload) != dict(stored_payload):
        mismatched.append("producer_canonical_payload")
        for key in PRODUCER_CANONICAL_KEYS:
            if replayed_payload.get(key) != stored_payload.get(key):
                mismatched.append(key)
    if replayed_digest != stored_digest:
        mismatched.append("semantic_digest")
    return tuple(dict.fromkeys(mismatched))


def _resolve_typed_output_observation(
    validated_input: Mapping[str, Any],
    typed_output_observations: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any] | None, tuple[str, ...] | None]:
    ref = validated_input.get(JOIN_FIELD)
    if ref is None or ref == "" or ref == UNKNOWN:
        return None, ("TYPED_OUTPUT_OBSERVATION_REF_MISSING",)
    if not isinstance(ref, str):
        return None, ("TYPED_OUTPUT_OBSERVATION_REF_MISSING",)
    matches = [item for item in typed_output_observations if item.get("record_id") == ref]
    if not matches:
        return None, ("TYPED_OUTPUT_OBSERVATION_REF_UNRESOLVED",)
    if len(matches) != 1:
        return None, ("TYPED_OUTPUT_OBSERVATION_REF_AMBIGUOUS",)
    try:
        validated_obs = validate_double_play_entry_exit_observation_v1(matches[0])
    except DdoValidationError:
        return None, ("TYPED_OUTPUT_OBSERVATION_IDENTITY_INVALID",)
    if validated_obs.get("schema_name") != SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION:
        return None, ("TYPED_OUTPUT_OBSERVATION_SCHEMA_MISMATCH",)
    if validated_obs.get("schema_version") != SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_V1:
        return None, ("TYPED_OUTPUT_OBSERVATION_SCHEMA_MISMATCH",)
    if validated_obs.get("producer_owner") != PRODUCER_OWNER:
        return None, ("TYPED_OUTPUT_OBSERVATION_PRODUCER_IDENTITY_MISMATCH",)
    if validated_obs.get("projection_status") != TYPED_PROJECTION_STATUS:
        return None, ("TYPED_OUTPUT_OBSERVATION_NOT_TYPED",)
    return validated_obs, None


def _input_schema_identity_failure(
    validated_input: Mapping[str, Any],
) -> tuple[str, ...] | None:
    if (
        validated_input.get("schema_name")
        != SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE
    ):
        return ("INPUT_SCHEMA_MISMATCH",)
    if (
        validated_input.get("schema_version")
        != SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE_V1
    ):
        return ("INPUT_SCHEMA_VERSION_MISMATCH",)
    if validated_input.get("producer_function_name") != PRODUCER_FUNCTION_NAME:
        return ("INPUT_PRODUCER_FUNCTION_IDENTITY_MISMATCH",)
    if validated_input.get("projection_status") != INPUT_TYPED_PROJECTION_STATUS:
        return ("INPUT_TYPED_PROJECTION_REQUIRED",)
    return None


def _reconstruct_policy(validated_input: Mapping[str, Any]) -> Any:
    from trading.master_v2.double_play_entry_exit_policy_v0 import (  # noqa: PLC0415
        DoublePlayEntryExitPolicyV0,
    )

    version = validated_input.get("producer_call_policy_version")
    if not isinstance(version, str) or not version or version == UNKNOWN:
        raise DdoValidationError("POLICY_VERSION_UNAVAILABLE")
    return DoublePlayEntryExitPolicyV0(policy_version=version)


def _stored_code_sha(payload: Mapping[str, Any]) -> str:
    raw = payload.get("code_sha", UNKNOWN)
    if not isinstance(raw, str) or not raw:
        return UNKNOWN
    return raw


def _stored_digest(observation: Mapping[str, Any] | None) -> str | None:
    if observation is None:
        return None
    digest = observation.get("semantic_digest")
    if isinstance(digest, str):
        return digest
    return None


def _reject_hindsight_mapping(payload: Mapping[str, Any], label: str) -> None:
    extra = sorted(key for key in payload if key in _HINDSIGHT_KEYS)
    if extra:
        raise DdoValidationError(f"HINDSIGHT_LEAKAGE_FORBIDDEN:{label}:{extra}")


def _finish(
    *,
    status: str,
    reason_codes: tuple[str, ...],
    stored_code_sha: str,
    stored_semantic_digest: str | None = None,
    replayed_semantic_digest: str | None = None,
    mismatch_fields: tuple[str, ...] = (),
    producer_function_invoked: bool = False,
    producer_invocation_count: int = 0,
    public_producer_symbol_used: bool = False,
    exception_class: str | None = None,
    replayed_payload: Mapping[str, Any] | None = None,
) -> MappingProxyType[str, Any]:
    semantic_match = status == STATUS_MATCH
    body: dict[str, Any] = {
        "evaluator_id": FUNCTION_REPLAY_EVALUATOR_ID,
        "replay_class_letter": REPLAY_CLASS_LETTER,
        "replay_class_semantic": REPLAY_CLASS_SEMANTIC,
        "replay_class_owner_token": REPLAY_CLASS_OWNER_TOKEN,
        "historical_code_parity_claim": HISTORICAL_CODE_PARITY_CLAIM,
        "offline_evaluation_authority": OFFLINE_EVALUATION_AUTHORITY,
        "trading_authority": TRADING_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "replay_productive_authority": REPLAY_PRODUCTIVE_AUTHORITY,
        "hindsight_leakage_allowed": HINDSIGHT_LEAKAGE_ALLOWED,
        "result_durability": RESULT_DURABILITY,
        "replay_timeout_policy": REPLAY_TIMEOUT_POLICY,
        "replay_operation_attempt_count": producer_invocation_count,
        "replay_operation_attempt_count_max": REPLAY_OPERATION_ATTEMPT_COUNT_MAX,
        "producer_function_name": PRODUCER_FUNCTION_NAME,
        "producer_function_invoked": producer_function_invoked,
        "producer_invocation_count": producer_invocation_count,
        "public_producer_symbol_used": public_producer_symbol_used,
        "wrapped_bypass_used": False,
        "status": status,
        "semantic_match": semantic_match,
        "reason_codes": list(reason_codes),
        "mismatch_fields": list(mismatch_fields),
        "stored_code_sha": stored_code_sha,
        "stored_semantic_digest": stored_semantic_digest,
        "replayed_semantic_digest": replayed_semantic_digest,
        "exception_class": exception_class,
        "replayed_canonical_payload": (
            dict(replayed_payload) if replayed_payload is not None else None
        ),
    }
    return freeze_record(body)
