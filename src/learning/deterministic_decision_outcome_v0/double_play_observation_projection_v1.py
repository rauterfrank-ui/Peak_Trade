"""Versioned observation projection of EntryExitPolicyDecisionV0.

Observation-only. Does not import trading at module load (avoids a capture
circular import). Producer enums remain owned by Double Play. DDO stores
exact producer-owned values and explicit UNAVAILABLE sentinels.

TRADING_AUTHORITY=NONE
DDO_MAY_REWRITE_PRODUCER_SEMANTICS=false
SELECTED_SIDE_IS_NOT_BULL_BEAR_NEXT_STATE=true
"""

from __future__ import annotations

import json
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION,
    SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_V1,
    FieldSpecV0,
    attach_content_hash,
    freeze_record,
    optional_record_id,
    reject_unknown_fields,
    require_enum,
    require_event_time_utc,
    require_id_list,
    require_mapping,
    require_non_empty_string_or_unknown,
    require_record_id,
    require_schema,
    require_sha256_or_unknown,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError

PROJECTION_ID: Final[str] = (
    "peak_trade.learning.ddo.double_play_entry_exit_observation_projection_v1"
)
TRADING_AUTHORITY_NONE: Final[str] = "NONE"
SIDE_STATE_AFTER_STATUS_UNAVAILABLE: Final[str] = "UNAVAILABLE"
SELECTED_SIDE_SEMANTIC_CLASS: Final[str] = "COMPOSITION_SELECTED_SIDE"
PREVIOUS_DIRECTION_STATE_SEMANTIC_CLASS: Final[str] = (
    "ENTRY_EXIT_DIRECTION_STATE_NOT_FULL_SIDESTATE"
)
PRODUCER_OWNER: Final[str] = "trading.master_v2.double_play_entry_exit_policy_v0"
TYPED_PROJECTION_STATUS: Final[str] = "TYPED_PRODUCER_OBJECT"
UNAVAILABLE_PROJECTION_STATUS: Final[str] = "UNAVAILABLE"

# Exact key set of serialize_entry_exit_policy_decision_canonical.
PRODUCER_CANONICAL_KEYS: Final[tuple[str, ...]] = (
    "policy_decision_id",
    "instrument_id",
    "trading_epoch",
    "composition_result_ref",
    "previous_direction_state",
    "position_state",
    "reconciliation_state",
    "decision_outcome",
    "entry_eligibility",
    "exit_class",
    "position_management_action",
    "reversal_state",
    "reduce_only",
    "position_flip_allowed",
    "quantity_status",
    "selected_side",
    "reason_codes",
    "decision_precedence_trace",
    "policy_version",
    "input_digest",
    "execution_eligible",
    "adapter_compatible",
    "authority_effect",
    "runtime_effect",
    "order_effect",
    "risk_sizing_effect",
)

_REQUIRED_TYPED_ATTRS: Final[tuple[str, ...]] = PRODUCER_CANONICAL_KEYS + ("semantic_digest",)

SIDE_STATE_AFTER_STATUS_V1: Final[tuple[str, ...]] = (
    SIDE_STATE_AFTER_STATUS_UNAVAILABLE,
    UNKNOWN,
)
PROJECTION_STATUS_V1: Final[tuple[str, ...]] = (
    TYPED_PROJECTION_STATUS,
    UNAVAILABLE_PROJECTION_STATUS,
)
TRADING_AUTHORITY_V1: Final[tuple[str, ...]] = (TRADING_AUTHORITY_NONE,)

DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_FIELD_SPECS_V1: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("schema_name", "REQUIRED", "string", True, "Observation schema identity."),
    FieldSpecV0(
        "schema_version",
        "REQUIRED",
        "string",
        True,
        "Version token double_play_entry_exit_observation_v1.",
    ),
    FieldSpecV0("record_id", "REQUIRED", "record_id", True, "Immutable observation identity."),
    FieldSpecV0("event_time_utc", "REQUIRED", "utc_timestamp", True, "Capture event time UTC."),
    FieldSpecV0("correlation_id", "REQUIRED", "record_id", True, "Correlation identity."),
    FieldSpecV0(
        "cycle_id",
        "CONDITIONALLY_REQUIRED",
        "record_id|null",
        True,
        "Null until a proven cycle producer exists.",
    ),
    FieldSpecV0(
        "decision_event_ref",
        "REQUIRED",
        "record_id",
        True,
        "Lineage to the generic DecisionEvent. Not trading authority.",
    ),
    FieldSpecV0("projection_id", "REQUIRED", "string", True, "Versioned projection identity."),
    FieldSpecV0(
        "projection_status",
        "REQUIRED",
        "enum:PROJECTION_STATUS_V1",
        True,
        "TYPED_PRODUCER_OBJECT or UNAVAILABLE.",
    ),
    FieldSpecV0(
        "trading_authority",
        "REQUIRED",
        "enum:TRADING_AUTHORITY_V1",
        True,
        "Always NONE. DDO does not own trading semantics.",
    ),
    FieldSpecV0("producer_owner", "REQUIRED", "string", True, "Producer-declared owner label."),
    FieldSpecV0(
        "producer_canonical_payload",
        "CONDITIONALLY_REQUIRED",
        "object|null",
        True,
        "Exact serialize_entry_exit_policy_decision_canonical payload, or null if unavailable.",
    ),
    FieldSpecV0(
        "semantic_digest",
        "CONDITIONALLY_REQUIRED",
        "sha256|UNKNOWN|null",
        True,
        "Producer semantic_digest. Null when typed producer object is unavailable.",
    ),
    FieldSpecV0(
        "selected_side_semantic_class",
        "REQUIRED",
        "string",
        True,
        "Composition selected_side is not SideState.",
    ),
    FieldSpecV0(
        "previous_direction_state_semantic_class",
        "REQUIRED",
        "string",
        True,
        "Producer previous_direction_state is EntryExitDirectionState, not full SideState.",
    ),
    FieldSpecV0(
        "side_state_after_status",
        "REQUIRED",
        "enum:SIDE_STATE_AFTER_STATUS_V1",
        True,
        "UNAVAILABLE unless a proven SideState-after reference exists.",
    ),
    FieldSpecV0(
        "side_state_after",
        "REQUIRED",
        "string",
        True,
        "Exact SideState-after token or UNAVAILABLE/UNKNOWN. Never selected_side.",
    ),
    FieldSpecV0("code_sha", "REQUIRED", "sha256|UNKNOWN", True, "UNKNOWN is explicit semantics."),
    FieldSpecV0(
        "evidence_hash", "REQUIRED", "sha256|UNKNOWN", True, "UNKNOWN is explicit semantics."
    ),
    FieldSpecV0(
        "causal_parent_ids", "REQUIRED", "record_id[]", True, "DecisionEvent is the parent."
    ),
    FieldSpecV0("content_hash", "REQUIRED", "sha256", False, "Computed; excluded from hash scope."),
)

DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_FIELD_SPECS_V1
)

_PRODUCER_NO_ACTION_OUTCOME: Final[str] = "no_action"
_GENERIC_NO_ENTRY_OUTCOMES: Final[frozenset[str]] = frozenset(
    {"no_action", "observe", "blocked", "cancel_pending", "reconcile_only"}
)


def is_typed_entry_exit_policy_decision_v1(obj: Any) -> bool:
    """True when obj is the current typed producer object (class or duck-typed)."""
    if obj is None or isinstance(obj, Mapping):
        return False
    typed_cls = _entry_exit_decision_class()
    if typed_cls is not None and isinstance(obj, typed_cls):
        return True
    return all(hasattr(obj, key) for key in _REQUIRED_TYPED_ATTRS)


def producer_canonical_payload_from_decision_v1(decision: Any) -> dict[str, Any]:
    """Exact producer canonical payload. Prefers the producer serializer."""
    if not is_typed_entry_exit_policy_decision_v1(decision):
        raise DdoValidationError("DOUBLE_PLAY_OBSERVATION_REQUIRES_TYPED_DECISION")
    serializer = _canonical_serializer()
    if serializer is not None:
        raw = serializer(decision)
        if not isinstance(raw, str):
            raise DdoValidationError("PRODUCER_CANONICAL_SERIALIZER_MUST_RETURN_STRING")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise DdoValidationError("PRODUCER_CANONICAL_PAYLOAD_MUST_BE_OBJECT")
        _require_canonical_keys(payload)
        return payload
    return _duck_typed_canonical_payload(decision)


def project_entry_exit_policy_decision_v1(
    decision: Any,
    *,
    record_id: str,
    event_time_utc: str,
    correlation_id: str,
    cycle_id: str | None,
    decision_event_ref: str,
) -> MappingProxyType[str, Any]:
    """Build a frozen observation record from a typed producer decision."""
    if not is_typed_entry_exit_policy_decision_v1(decision):
        return build_double_play_entry_exit_observation_v1(
            {
                "schema_name": SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION,
                "schema_version": SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_V1,
                "record_id": record_id,
                "event_time_utc": event_time_utc,
                "correlation_id": correlation_id,
                "cycle_id": cycle_id,
                "decision_event_ref": decision_event_ref,
                "projection_id": PROJECTION_ID,
                "projection_status": UNAVAILABLE_PROJECTION_STATUS,
                "trading_authority": TRADING_AUTHORITY_NONE,
                "producer_owner": PRODUCER_OWNER,
                "producer_canonical_payload": None,
                "semantic_digest": None,
                "selected_side_semantic_class": SELECTED_SIDE_SEMANTIC_CLASS,
                "previous_direction_state_semantic_class": (
                    PREVIOUS_DIRECTION_STATE_SEMANTIC_CLASS
                ),
                "side_state_after_status": SIDE_STATE_AFTER_STATUS_UNAVAILABLE,
                "side_state_after": SIDE_STATE_AFTER_STATUS_UNAVAILABLE,
                "code_sha": UNKNOWN,
                "evidence_hash": UNKNOWN,
                "causal_parent_ids": [decision_event_ref],
            }
        )
    canonical = producer_canonical_payload_from_decision_v1(decision)
    digest = getattr(decision, "semantic_digest", None)
    if not isinstance(digest, str) or not digest:
        raise DdoValidationError("TYPED_DECISION_SEMANTIC_DIGEST_MISSING")
    return build_double_play_entry_exit_observation_v1(
        {
            "schema_name": SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION,
            "schema_version": SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_V1,
            "record_id": record_id,
            "event_time_utc": event_time_utc,
            "correlation_id": correlation_id,
            "cycle_id": cycle_id,
            "decision_event_ref": decision_event_ref,
            "projection_id": PROJECTION_ID,
            "projection_status": TYPED_PROJECTION_STATUS,
            "trading_authority": TRADING_AUTHORITY_NONE,
            "producer_owner": PRODUCER_OWNER,
            "producer_canonical_payload": canonical,
            "semantic_digest": digest,
            "selected_side_semantic_class": SELECTED_SIDE_SEMANTIC_CLASS,
            "previous_direction_state_semantic_class": PREVIOUS_DIRECTION_STATE_SEMANTIC_CLASS,
            "side_state_after_status": SIDE_STATE_AFTER_STATUS_UNAVAILABLE,
            "side_state_after": SIDE_STATE_AFTER_STATUS_UNAVAILABLE,
            "code_sha": UNKNOWN,
            "evidence_hash": UNKNOWN,
            "causal_parent_ids": [decision_event_ref],
        }
    )


def generic_decision_result_for_producer_outcome_v1(decision_outcome: str) -> str:
    """Keep DDO DecisionResult small. Exact outcome lives in the projection."""
    if decision_outcome == _PRODUCER_NO_ACTION_OUTCOME:
        return "NO_ACTION"
    return UNKNOWN


def generic_decision_type_for_producer_outcome_v1(decision_outcome: str) -> str:
    """Do not copy Double-Play enums into DECISION_TYPE_V0."""
    if decision_outcome in _GENERIC_NO_ENTRY_OUTCOMES:
        return "NO_ENTRY"
    return UNKNOWN


def build_double_play_entry_exit_observation_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "double_play_entry_exit_observation")
    reject_unknown_fields(raw, DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_ALLOWED_FIELDS)
    require_schema(
        raw,
        SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION,
        SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_V1,
    )
    status = require_enum(raw.get("projection_status"), "projection_status", PROJECTION_STATUS_V1)
    canonical_raw = raw.get("producer_canonical_payload")
    digest_raw = raw.get("semantic_digest")
    if status == TYPED_PROJECTION_STATUS:
        if not isinstance(canonical_raw, dict):
            raise DdoValidationError("TYPED_PROJECTION_REQUIRES_CANONICAL_PAYLOAD")
        _require_canonical_keys(canonical_raw)
        digest = require_sha256_or_unknown(digest_raw, "semantic_digest")
        canonical: dict[str, Any] | None = dict(canonical_raw)
    else:
        if canonical_raw is not None:
            raise DdoValidationError("UNAVAILABLE_PROJECTION_MUST_NOT_CARRY_CANONICAL_PAYLOAD")
        if digest_raw is not None:
            raise DdoValidationError("UNAVAILABLE_PROJECTION_MUST_NOT_CARRY_SEMANTIC_DIGEST")
        digest = None
        canonical = None
    decision_ref = require_record_id(raw.get("decision_event_ref"), "decision_event_ref")
    side_after = raw.get("side_state_after")
    if not isinstance(side_after, str) or not side_after:
        raise DdoValidationError("SIDE_STATE_AFTER_REQUIRED")
    if side_after not in {SIDE_STATE_AFTER_STATUS_UNAVAILABLE, UNKNOWN}:
        raise DdoValidationError("SIDE_STATE_AFTER_MUST_BE_UNAVAILABLE_OR_UNKNOWN")
    canonical_record: dict[str, Any] = {
        "schema_name": SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION,
        "schema_version": SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_V1,
        "record_id": require_record_id(raw.get("record_id"), "record_id"),
        "event_time_utc": require_event_time_utc(raw.get("event_time_utc"), "event_time_utc"),
        "correlation_id": require_record_id(raw.get("correlation_id"), "correlation_id"),
        "cycle_id": optional_record_id(raw.get("cycle_id"), "cycle_id"),
        "decision_event_ref": decision_ref,
        "projection_id": require_non_empty_string_or_unknown(
            raw.get("projection_id"), "projection_id"
        ),
        "projection_status": status,
        "trading_authority": require_enum(
            raw.get("trading_authority"), "trading_authority", TRADING_AUTHORITY_V1
        ),
        "producer_owner": require_non_empty_string_or_unknown(
            raw.get("producer_owner"), "producer_owner"
        ),
        "producer_canonical_payload": canonical,
        "semantic_digest": digest,
        "selected_side_semantic_class": require_non_empty_string_or_unknown(
            raw.get("selected_side_semantic_class"), "selected_side_semantic_class"
        ),
        "previous_direction_state_semantic_class": require_non_empty_string_or_unknown(
            raw.get("previous_direction_state_semantic_class"),
            "previous_direction_state_semantic_class",
        ),
        "side_state_after_status": require_enum(
            raw.get("side_state_after_status"),
            "side_state_after_status",
            SIDE_STATE_AFTER_STATUS_V1,
        ),
        "side_state_after": side_after,
        "code_sha": require_sha256_or_unknown(raw.get("code_sha"), "code_sha"),
        "evidence_hash": require_sha256_or_unknown(raw.get("evidence_hash"), "evidence_hash"),
        "causal_parent_ids": require_id_list(raw.get("causal_parent_ids"), "causal_parent_ids"),
    }
    if decision_ref not in canonical_record["causal_parent_ids"]:
        raise DdoValidationError("OBSERVATION_PARENT_MUST_INCLUDE_DECISION_EVENT_REF")
    hashed = attach_content_hash(canonical_record)
    if "content_hash" in raw and raw["content_hash"] != hashed["content_hash"]:
        raise DdoValidationError("CONTENT_HASH_MISMATCH")
    return freeze_record(hashed)


def validate_double_play_entry_exit_observation_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    return build_double_play_entry_exit_observation_v1(payload)


def _require_canonical_keys(payload: Mapping[str, Any]) -> None:
    missing = [key for key in PRODUCER_CANONICAL_KEYS if key not in payload]
    if missing:
        raise DdoValidationError(f"PRODUCER_CANONICAL_KEYS_MISSING:{missing}")
    extra = sorted(set(payload.keys()) - set(PRODUCER_CANONICAL_KEYS))
    if extra:
        raise DdoValidationError(f"PRODUCER_CANONICAL_UNEXPECTED_KEY:{extra}")


def _duck_typed_canonical_payload(decision: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key in PRODUCER_CANONICAL_KEYS:
        value = getattr(decision, key)
        if key in {"reason_codes", "decision_precedence_trace"}:
            payload[key] = [_token(item) for item in value]
        elif key in {
            "reduce_only",
            "position_flip_allowed",
            "execution_eligible",
            "adapter_compatible",
        }:
            if not isinstance(value, bool):
                raise DdoValidationError(f"PRODUCER_FIELD_MUST_BE_BOOL:{key}")
            payload[key] = value
        elif key == "trading_epoch":
            if not isinstance(value, int) or isinstance(value, bool):
                raise DdoValidationError("PRODUCER_TRADING_EPOCH_MUST_BE_INT")
            payload[key] = value
        else:
            token = _token(value)
            if not token and key not in {"composition_result_ref", "input_digest"}:
                raise DdoValidationError(f"PRODUCER_FIELD_EMPTY:{key}")
            payload[key] = token
    return payload


def _token(value: Any) -> str:
    raw = getattr(value, "value", value)
    if not isinstance(raw, str):
        raise DdoValidationError("PRODUCER_TOKEN_MUST_BE_STRING")
    return raw


def _entry_exit_decision_class() -> type[Any] | None:
    try:
        from trading.master_v2.double_play_entry_exit_policy_v0 import (  # noqa: PLC0415
            EntryExitPolicyDecisionV0,
        )
    except ImportError:
        return None
    return EntryExitPolicyDecisionV0


def _canonical_serializer() -> Any | None:
    try:
        from trading.master_v2.double_play_entry_exit_policy_v0 import (  # noqa: PLC0415
            serialize_entry_exit_policy_decision_canonical,
        )
    except ImportError:
        return None
    return serialize_entry_exit_policy_decision_canonical
