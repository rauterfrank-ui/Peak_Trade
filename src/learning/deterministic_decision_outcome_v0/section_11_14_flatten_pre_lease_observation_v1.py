"""Typed observation record for §11.14 flatten pre-lease send-intent capture.

Observation-only. Does not import ops/trading/execution. Does not claim
venue execution, lease consume, wire send, or a singular canonical
correlation identity. Split producer identities remain separate fields.

DDO_TRADING_AUTHORITY=NONE
DDO_EXECUTION_AUTHORITY=NONE
DDO_PERMISSION_AUTHORITY=NONE
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION,
    SCHEMA_VERSION_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION_V1,
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

SEAM_ID: Final[str] = "section_11_14.flatten_pre_lease_send_intent"
PROJECTION_ID: Final[str] = "peak_trade.learning.ddo.section_11_14_flatten_pre_lease_observation_v1"
PRODUCER_OWNER: Final[str] = "ops.section_11_14.flatten_pre_lease_ddo_observation_v1"
AUTHORITY_NONE: Final[str] = "NONE"
FLAG_TRUE: Final[str] = "true"
FLAG_FALSE: Final[str] = "false"
OBSERVATION_FLAG_V1: Final[tuple[str, ...]] = (FLAG_TRUE, FLAG_FALSE)
AUTHORITY_NONE_V1: Final[tuple[str, ...]] = (AUTHORITY_NONE,)
IDENTITY_RELATIONSHIP_STATUS_V1: Final[tuple[str, ...]] = (
    "EQUAL_OBSERVED",
    "DISTINCT_OBSERVED",
    "UNPROVEN",
    "UNKNOWN",
)

SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION_FIELD_SPECS_V1: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("schema_name", "REQUIRED", "string", True, "Immutable schema identity."),
    FieldSpecV0(
        "schema_version",
        "REQUIRED",
        "string",
        True,
        "Version token section_11_14_flatten_pre_lease_observation_v1.",
    ),
    FieldSpecV0("record_id", "REQUIRED", "record_id", True, "Immutable observation identity."),
    FieldSpecV0("event_time_utc", "REQUIRED", "utc_timestamp", True, "Capture event time UTC."),
    FieldSpecV0(
        "correlation_id",
        "REQUIRED",
        "record_id",
        True,
        "Seam-level correlation label. Not a singular canonical identity.",
    ),
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
    FieldSpecV0("seam_id", "REQUIRED", "string", True, "Explicit pre-lease observation seam."),
    FieldSpecV0(
        "observation_only",
        "REQUIRED",
        "enum:OBSERVATION_FLAG_V1",
        True,
        "Always true. Capture does not authorize send.",
    ),
    FieldSpecV0(
        "trading_authority",
        "REQUIRED",
        "enum:AUTHORITY_NONE_V1",
        True,
        "Always NONE. DDO does not own trading semantics.",
    ),
    FieldSpecV0(
        "execution_authority",
        "REQUIRED",
        "enum:AUTHORITY_NONE_V1",
        True,
        "Always NONE. DDO does not own execution semantics.",
    ),
    FieldSpecV0(
        "permission_authority",
        "REQUIRED",
        "enum:AUTHORITY_NONE_V1",
        True,
        "Always NONE. DDO does not own permission semantics.",
    ),
    FieldSpecV0(
        "live_authority_changed",
        "REQUIRED",
        "enum:OBSERVATION_FLAG_V1",
        True,
        "Always false for this observation.",
    ),
    FieldSpecV0("producer_id", "REQUIRED", "string", True, "Host producer identity."),
    FieldSpecV0("authority_owner", "REQUIRED", "string", True, "Host adapter owner label."),
    FieldSpecV0("host", "REQUIRED", "string", True, "Observed request host or UNKNOWN."),
    FieldSpecV0("endpoint", "REQUIRED", "string", True, "Observed request endpoint or UNKNOWN."),
    FieldSpecV0("method", "REQUIRED", "string", True, "Observed request method or UNKNOWN."),
    FieldSpecV0(
        "approved_request_identity",
        "REQUIRED",
        "sha256|UNKNOWN",
        True,
        "Receipt approved_request_identity. Separate from HMAC bind identity.",
    ),
    FieldSpecV0(
        "hmac_bind_request_identity",
        "REQUIRED",
        "sha256|UNKNOWN",
        True,
        "HMAC bind record request_identity. Not renamed onto approved_request_identity.",
    ),
    FieldSpecV0(
        "hmac_signing_input_digest",
        "REQUIRED",
        "sha256|UNKNOWN",
        True,
        "Non-secret HMAC prehash digest. Never raw signature or key material.",
    ),
    FieldSpecV0(
        "hmac_bind_exact_envelope_id",
        "REQUIRED",
        "sha256|UNKNOWN",
        True,
        "HMAC bind exact_envelope_id. Not a frozen-constant alias.",
    ),
    FieldSpecV0(
        "hmac_bind_origin_main_sha",
        "REQUIRED",
        "string",
        True,
        "HMAC bind origin_main_sha as produced. Git SHA or UNKNOWN.",
    ),
    FieldSpecV0(
        "capture_repository_sha",
        "REQUIRED",
        "string",
        True,
        "Capture binding repository SHA or UNKNOWN. Not assumed equal to bind SHA.",
    ),
    FieldSpecV0(
        "network_session_authority_id",
        "REQUIRED",
        "string",
        True,
        "Network-session authority_id from the bind record or UNKNOWN.",
    ),
    FieldSpecV0(
        "network_session_authorized",
        "REQUIRED",
        "enum:OBSERVATION_FLAG_V1",
        True,
        "Observed transport network_session_authorized flag.",
    ),
    FieldSpecV0(
        "lease_consumed",
        "REQUIRED",
        "enum:OBSERVATION_FLAG_V1",
        True,
        "Observed lease flag at this hook. Must be false at capture time.",
    ),
    FieldSpecV0(
        "last_wire_attempted",
        "REQUIRED",
        "enum:OBSERVATION_FLAG_V1",
        True,
        "Observed last_wire_attempted at this hook.",
    ),
    FieldSpecV0(
        "sent_flag",
        "REQUIRED",
        "enum:OBSERVATION_FLAG_V1",
        True,
        "Observed transport _sent flag at this hook.",
    ),
    FieldSpecV0(
        "wire_send_executed",
        "REQUIRED",
        "enum:OBSERVATION_FLAG_V1",
        True,
        "Always false at this hook. No urllib has run.",
    ),
    FieldSpecV0(
        "gate_digest",
        "REQUIRED",
        "sha256|UNKNOWN",
        True,
        "Receipt gate_digest when it is a sha256, else UNKNOWN.",
    ),
    FieldSpecV0(
        "request_body_sha256",
        "REQUIRED",
        "sha256|UNKNOWN",
        True,
        "SHA-256 of the observed request body_text.",
    ),
    FieldSpecV0(
        "identity_relationship_approved_request_to_hmac_bind_request",
        "REQUIRED",
        "enum:IDENTITY_RELATIONSHIP_STATUS_V1",
        True,
        "Byte comparison of the two request-identity fields. Not a canonical merge.",
    ),
    FieldSpecV0(
        "identity_relationship_hmac_bind_origin_main_sha_to_capture_repository_sha",
        "REQUIRED",
        "enum:IDENTITY_RELATIONSHIP_STATUS_V1",
        True,
        "Semantic relationship is UNPROVEN unless a contract proves comparability.",
    ),
    FieldSpecV0(
        "singular_canonical_correlation_id_claimed",
        "REQUIRED",
        "enum:OBSERVATION_FLAG_V1",
        True,
        "Always false. Split identities are not collapsed.",
    ),
    FieldSpecV0(
        "venue_execution_not_claimed",
        "REQUIRED",
        "enum:OBSERVATION_FLAG_V1",
        True,
        "Always true. This seam is not venue_execution.",
    ),
    FieldSpecV0(
        "lease_consume_not_authorized",
        "REQUIRED",
        "enum:OBSERVATION_FLAG_V1",
        True,
        "Always true for this observation workpackage.",
    ),
    FieldSpecV0(
        "wire_send_not_authorized",
        "REQUIRED",
        "enum:OBSERVATION_FLAG_V1",
        True,
        "Always true for this observation workpackage.",
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

SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION_FIELD_SPECS_V1
)


def _token_or_unknown(value: Any) -> str:
    if value is None:
        return UNKNOWN
    if isinstance(value, bool):
        return FLAG_TRUE if value else FLAG_FALSE
    raw = getattr(value, "value", value)
    if isinstance(raw, str) and raw:
        return raw
    return UNKNOWN


def _sha_or_unknown(value: Any) -> str:
    token = _token_or_unknown(value)
    if token == UNKNOWN:
        return UNKNOWN
    if len(token) == 64 and all(ch in "0123456789abcdef" for ch in token):
        return token
    return UNKNOWN


def identity_relationship_for_request_identities_v1(left: Any, right: Any) -> str:
    """Byte comparison only. Does not declare a canonical identity."""
    a = _sha_or_unknown(left)
    b = _sha_or_unknown(right)
    if a == UNKNOWN or b == UNKNOWN:
        return "UNKNOWN"
    if a == b:
        return "EQUAL_OBSERVED"
    return "DISTINCT_OBSERVED"


def project_section_11_14_flatten_pre_lease_observation_v1(
    view: Mapping[str, Any],
    *,
    record_id: str,
    event_time_utc: str,
    correlation_id: str,
    cycle_id: str | None,
    decision_event_ref: str,
    producer_id: str,
    authority_owner: str,
) -> MappingProxyType[str, Any]:
    """Build the typed observation from a duck-typed view. No ops import."""
    approved = _sha_or_unknown(view.get("approved_request_identity"))
    hmac_request = _sha_or_unknown(view.get("hmac_bind_request_identity"))
    origin_rel = _token_or_unknown(
        view.get("identity_relationship_hmac_bind_origin_main_sha_to_capture_repository_sha")
    )
    if origin_rel not in IDENTITY_RELATIONSHIP_STATUS_V1:
        origin_rel = "UNPROVEN"
    payload: dict[str, Any] = {
        "schema_name": SCHEMA_NAME_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION,
        "schema_version": SCHEMA_VERSION_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION_V1,
        "record_id": record_id,
        "event_time_utc": event_time_utc,
        "correlation_id": correlation_id,
        "cycle_id": cycle_id,
        "decision_event_ref": decision_event_ref,
        "seam_id": SEAM_ID,
        "observation_only": FLAG_TRUE,
        "trading_authority": AUTHORITY_NONE,
        "execution_authority": AUTHORITY_NONE,
        "permission_authority": AUTHORITY_NONE,
        "live_authority_changed": FLAG_FALSE,
        "producer_id": producer_id,
        "authority_owner": authority_owner,
        "host": _token_or_unknown(view.get("host")),
        "endpoint": _token_or_unknown(view.get("endpoint")),
        "method": _token_or_unknown(view.get("method")),
        "approved_request_identity": approved,
        "hmac_bind_request_identity": hmac_request,
        "hmac_signing_input_digest": _sha_or_unknown(view.get("hmac_signing_input_digest")),
        "hmac_bind_exact_envelope_id": _sha_or_unknown(view.get("hmac_bind_exact_envelope_id")),
        "hmac_bind_origin_main_sha": _token_or_unknown(view.get("hmac_bind_origin_main_sha")),
        "capture_repository_sha": _token_or_unknown(view.get("capture_repository_sha")),
        "network_session_authority_id": _token_or_unknown(view.get("network_session_authority_id")),
        "network_session_authorized": _token_or_unknown(view.get("network_session_authorized")),
        "lease_consumed": _token_or_unknown(view.get("lease_consumed")),
        "last_wire_attempted": _token_or_unknown(view.get("last_wire_attempted")),
        "sent_flag": _token_or_unknown(view.get("sent_flag")),
        "wire_send_executed": FLAG_FALSE,
        "gate_digest": _sha_or_unknown(view.get("gate_digest")),
        "request_body_sha256": _sha_or_unknown(view.get("request_body_sha256")),
        "identity_relationship_approved_request_to_hmac_bind_request": (
            identity_relationship_for_request_identities_v1(approved, hmac_request)
        ),
        "identity_relationship_hmac_bind_origin_main_sha_to_capture_repository_sha": origin_rel,
        "singular_canonical_correlation_id_claimed": FLAG_FALSE,
        "venue_execution_not_claimed": FLAG_TRUE,
        "lease_consume_not_authorized": FLAG_TRUE,
        "wire_send_not_authorized": FLAG_TRUE,
        "code_sha": UNKNOWN,
        "evidence_hash": UNKNOWN,
        "causal_parent_ids": [decision_event_ref],
    }
    return build_section_11_14_flatten_pre_lease_observation_v1(payload)


def build_section_11_14_flatten_pre_lease_observation_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "section_11_14_flatten_pre_lease_observation")
    reject_unknown_fields(raw, SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION_ALLOWED_FIELDS)
    require_schema(
        raw,
        SCHEMA_NAME_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION,
        SCHEMA_VERSION_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION_V1,
    )
    decision_ref = require_record_id(raw.get("decision_event_ref"), "decision_event_ref")
    canonical: dict[str, Any] = {
        "schema_name": SCHEMA_NAME_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION,
        "schema_version": SCHEMA_VERSION_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION_V1,
        "record_id": require_record_id(raw.get("record_id"), "record_id"),
        "event_time_utc": require_event_time_utc(raw.get("event_time_utc"), "event_time_utc"),
        "correlation_id": require_record_id(raw.get("correlation_id"), "correlation_id"),
        "cycle_id": optional_record_id(raw.get("cycle_id"), "cycle_id"),
        "decision_event_ref": decision_ref,
        "seam_id": require_non_empty_string_or_unknown(raw.get("seam_id"), "seam_id"),
        "observation_only": require_enum(
            raw.get("observation_only"), "observation_only", OBSERVATION_FLAG_V1
        ),
        "trading_authority": require_enum(
            raw.get("trading_authority"), "trading_authority", AUTHORITY_NONE_V1
        ),
        "execution_authority": require_enum(
            raw.get("execution_authority"), "execution_authority", AUTHORITY_NONE_V1
        ),
        "permission_authority": require_enum(
            raw.get("permission_authority"), "permission_authority", AUTHORITY_NONE_V1
        ),
        "live_authority_changed": require_enum(
            raw.get("live_authority_changed"), "live_authority_changed", OBSERVATION_FLAG_V1
        ),
        "producer_id": require_non_empty_string_or_unknown(raw.get("producer_id"), "producer_id"),
        "authority_owner": require_non_empty_string_or_unknown(
            raw.get("authority_owner"), "authority_owner"
        ),
        "host": require_non_empty_string_or_unknown(raw.get("host"), "host"),
        "endpoint": require_non_empty_string_or_unknown(raw.get("endpoint"), "endpoint"),
        "method": require_non_empty_string_or_unknown(raw.get("method"), "method"),
        "approved_request_identity": require_sha256_or_unknown(
            raw.get("approved_request_identity"), "approved_request_identity"
        ),
        "hmac_bind_request_identity": require_sha256_or_unknown(
            raw.get("hmac_bind_request_identity"), "hmac_bind_request_identity"
        ),
        "hmac_signing_input_digest": require_sha256_or_unknown(
            raw.get("hmac_signing_input_digest"), "hmac_signing_input_digest"
        ),
        "hmac_bind_exact_envelope_id": require_sha256_or_unknown(
            raw.get("hmac_bind_exact_envelope_id"), "hmac_bind_exact_envelope_id"
        ),
        "hmac_bind_origin_main_sha": require_non_empty_string_or_unknown(
            raw.get("hmac_bind_origin_main_sha"), "hmac_bind_origin_main_sha"
        ),
        "capture_repository_sha": require_non_empty_string_or_unknown(
            raw.get("capture_repository_sha"), "capture_repository_sha"
        ),
        "network_session_authority_id": require_non_empty_string_or_unknown(
            raw.get("network_session_authority_id"), "network_session_authority_id"
        ),
        "network_session_authorized": require_enum(
            raw.get("network_session_authorized"),
            "network_session_authorized",
            OBSERVATION_FLAG_V1,
        ),
        "lease_consumed": require_enum(
            raw.get("lease_consumed"), "lease_consumed", OBSERVATION_FLAG_V1
        ),
        "last_wire_attempted": require_enum(
            raw.get("last_wire_attempted"), "last_wire_attempted", OBSERVATION_FLAG_V1
        ),
        "sent_flag": require_enum(raw.get("sent_flag"), "sent_flag", OBSERVATION_FLAG_V1),
        "wire_send_executed": require_enum(
            raw.get("wire_send_executed"), "wire_send_executed", OBSERVATION_FLAG_V1
        ),
        "gate_digest": require_sha256_or_unknown(raw.get("gate_digest"), "gate_digest"),
        "request_body_sha256": require_sha256_or_unknown(
            raw.get("request_body_sha256"), "request_body_sha256"
        ),
        "identity_relationship_approved_request_to_hmac_bind_request": require_enum(
            raw.get("identity_relationship_approved_request_to_hmac_bind_request"),
            "identity_relationship_approved_request_to_hmac_bind_request",
            IDENTITY_RELATIONSHIP_STATUS_V1,
        ),
        "identity_relationship_hmac_bind_origin_main_sha_to_capture_repository_sha": require_enum(
            raw.get("identity_relationship_hmac_bind_origin_main_sha_to_capture_repository_sha"),
            "identity_relationship_hmac_bind_origin_main_sha_to_capture_repository_sha",
            IDENTITY_RELATIONSHIP_STATUS_V1,
        ),
        "singular_canonical_correlation_id_claimed": require_enum(
            raw.get("singular_canonical_correlation_id_claimed"),
            "singular_canonical_correlation_id_claimed",
            OBSERVATION_FLAG_V1,
        ),
        "venue_execution_not_claimed": require_enum(
            raw.get("venue_execution_not_claimed"),
            "venue_execution_not_claimed",
            OBSERVATION_FLAG_V1,
        ),
        "lease_consume_not_authorized": require_enum(
            raw.get("lease_consume_not_authorized"),
            "lease_consume_not_authorized",
            OBSERVATION_FLAG_V1,
        ),
        "wire_send_not_authorized": require_enum(
            raw.get("wire_send_not_authorized"),
            "wire_send_not_authorized",
            OBSERVATION_FLAG_V1,
        ),
        "code_sha": require_sha256_or_unknown(raw.get("code_sha"), "code_sha"),
        "evidence_hash": require_sha256_or_unknown(raw.get("evidence_hash"), "evidence_hash"),
        "causal_parent_ids": require_id_list(raw.get("causal_parent_ids"), "causal_parent_ids"),
    }
    if canonical["observation_only"] != FLAG_TRUE:
        raise DdoValidationError("PRE_LEASE_OBSERVATION_MUST_BE_OBSERVATION_ONLY")
    if canonical["singular_canonical_correlation_id_claimed"] != FLAG_FALSE:
        raise DdoValidationError("PRE_LEASE_MUST_NOT_CLAIM_SINGULAR_CANONICAL_CORRELATION")
    if canonical["trading_authority"] != AUTHORITY_NONE:
        raise DdoValidationError("PRE_LEASE_TRADING_AUTHORITY_MUST_BE_NONE")
    if canonical["execution_authority"] != AUTHORITY_NONE:
        raise DdoValidationError("PRE_LEASE_EXECUTION_AUTHORITY_MUST_BE_NONE")
    if canonical["permission_authority"] != AUTHORITY_NONE:
        raise DdoValidationError("PRE_LEASE_PERMISSION_AUTHORITY_MUST_BE_NONE")
    if canonical["wire_send_executed"] != FLAG_FALSE:
        raise DdoValidationError("PRE_LEASE_MUST_NOT_CLAIM_WIRE_SEND")
    if canonical["seam_id"] != SEAM_ID:
        raise DdoValidationError("PRE_LEASE_SEAM_ID_MISMATCH")
    if decision_ref not in canonical["causal_parent_ids"]:
        raise DdoValidationError("OBSERVATION_PARENT_MUST_INCLUDE_DECISION_EVENT_REF")
    hashed = attach_content_hash(canonical)
    if "content_hash" in raw and raw["content_hash"] != hashed["content_hash"]:
        raise DdoValidationError("CONTENT_HASH_MISMATCH")
    return freeze_record(hashed)


def validate_section_11_14_flatten_pre_lease_observation_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    return build_section_11_14_flatten_pre_lease_observation_v1(payload)
