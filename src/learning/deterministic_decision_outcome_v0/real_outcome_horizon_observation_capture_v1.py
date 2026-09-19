"""Capture projection for productive REAL N_BARS horizon observations.

Observation-only. Does not mint supplier evidence or alter trading decisions.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
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
from src.learning.deterministic_decision_outcome_v0.evaluation_observation_v0 import (
    EVALUATION_OBSERVATION_SCHEMA_NAME,
    validate_evaluation_observation_v0,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_engine_v1 import (
    REAL_OUTCOME_HORIZON_ENGINE_CAPTURE_SEAM,
    REAL_OUTCOME_HORIZON_ENGINE_ID,
)

SCHEMA_NAME: Final[str] = "real_outcome_horizon_observation_capture"
SCHEMA_VERSION: Final[str] = "real_outcome_horizon_observation_capture_v1"
PROJECTION_ID: Final[str] = "peak_trade.learning.ddo.real_outcome_horizon_observation_capture_v1"
TRADING_AUTHORITY_NONE: Final[str] = "NONE"
OBSERVATION_FLAG_V1: Final[tuple[str, ...]] = ("true", "false")
AUTHORITY_NONE_V1: Final[tuple[str, ...]] = (TRADING_AUTHORITY_NONE,)

REAL_OUTCOME_HORIZON_OBSERVATION_CAPTURE_FIELD_SPECS_V1: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("schema_name", "REQUIRED", "string", True, "Capture schema identity."),
    FieldSpecV0("schema_version", "REQUIRED", "string", True, "Capture schema version."),
    FieldSpecV0("record_id", "REQUIRED", "record_id", True, "Observation record id."),
    FieldSpecV0("event_time_utc", "REQUIRED", "utc_timestamp", True, "Capture event time."),
    FieldSpecV0("correlation_id", "REQUIRED", "record_id", True, "Correlation id."),
    FieldSpecV0("cycle_id", "CONDITIONALLY_REQUIRED", "record_id|null", True, "Cycle id."),
    FieldSpecV0("decision_event_ref", "REQUIRED", "record_id", True, "Parent decision event."),
    FieldSpecV0("seam_id", "REQUIRED", "string", True, "Capture seam id."),
    FieldSpecV0("observation_only", "REQUIRED", "string", True, "Observation-only flag."),
    FieldSpecV0("trading_authority", "REQUIRED", "string", True, "Trading authority marker."),
    FieldSpecV0("execution_authority", "REQUIRED", "string", True, "Execution authority marker."),
    FieldSpecV0("producer_id", "REQUIRED", "string", True, "Producer id."),
    FieldSpecV0("authority_owner", "REQUIRED", "string", True, "Authority owner."),
    FieldSpecV0("projection_id", "REQUIRED", "string", True, "Projection id."),
    FieldSpecV0("horizon_engine_id", "REQUIRED", "string", True, "Horizon engine id."),
    FieldSpecV0(
        "evaluation_observation_schema_name",
        "REQUIRED",
        "string",
        True,
        "Nested observation schema.",
    ),
    FieldSpecV0(
        "evaluation_observation",
        "REQUIRED",
        "object",
        True,
        "Validated evaluation_observation payload.",
    ),
    FieldSpecV0("code_sha", "REQUIRED", "string", True, "Code sha."),
    FieldSpecV0("evidence_hash", "REQUIRED", "string", True, "Evidence hash."),
    FieldSpecV0("causal_parent_ids", "REQUIRED", "record_id_list", True, "Causal parents."),
    FieldSpecV0("content_hash", "REQUIRED", "sha256", True, "Content hash."),
)

REAL_OUTCOME_HORIZON_OBSERVATION_CAPTURE_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in REAL_OUTCOME_HORIZON_OBSERVATION_CAPTURE_FIELD_SPECS_V1
)


def project_real_outcome_horizon_observation_capture_v1(
    evaluation_observation: Mapping[str, Any],
    *,
    record_id: str,
    event_time_utc: str,
    correlation_id: str,
    cycle_id: str | None,
    decision_event_ref: str,
    producer_id: str,
    authority_owner: str,
) -> MappingProxyType[str, Any]:
    obs = validate_evaluation_observation_v0(evaluation_observation)
    payload: dict[str, Any] = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "record_id": record_id,
        "event_time_utc": event_time_utc,
        "correlation_id": correlation_id,
        "cycle_id": cycle_id,
        "decision_event_ref": decision_event_ref,
        "seam_id": REAL_OUTCOME_HORIZON_ENGINE_CAPTURE_SEAM,
        "observation_only": "true",
        "trading_authority": TRADING_AUTHORITY_NONE,
        "execution_authority": TRADING_AUTHORITY_NONE,
        "producer_id": producer_id,
        "authority_owner": authority_owner,
        "projection_id": PROJECTION_ID,
        "horizon_engine_id": REAL_OUTCOME_HORIZON_ENGINE_ID,
        "evaluation_observation_schema_name": EVALUATION_OBSERVATION_SCHEMA_NAME,
        "evaluation_observation": dict(obs),
        "code_sha": UNKNOWN,
        "evidence_hash": UNKNOWN,
        "causal_parent_ids": [decision_event_ref],
    }
    return build_real_outcome_horizon_observation_capture_v1(payload)


def build_real_outcome_horizon_observation_capture_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "real_outcome_horizon_observation_capture")
    reject_unknown_fields(raw, REAL_OUTCOME_HORIZON_OBSERVATION_CAPTURE_ALLOWED_FIELDS)
    require_schema(raw, SCHEMA_NAME, SCHEMA_VERSION)
    nested = require_mapping(raw.get("evaluation_observation"), "evaluation_observation")
    validate_evaluation_observation_v0(nested)
    canonical: dict[str, Any] = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "record_id": require_record_id(raw.get("record_id"), "record_id"),
        "event_time_utc": require_event_time_utc(raw.get("event_time_utc"), "event_time_utc"),
        "correlation_id": require_record_id(raw.get("correlation_id"), "correlation_id"),
        "cycle_id": optional_record_id(raw.get("cycle_id"), "cycle_id"),
        "decision_event_ref": require_record_id(
            raw.get("decision_event_ref"), "decision_event_ref"
        ),
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
        "producer_id": require_non_empty_string_or_unknown(raw.get("producer_id"), "producer_id"),
        "authority_owner": require_non_empty_string_or_unknown(
            raw.get("authority_owner"), "authority_owner"
        ),
        "projection_id": require_non_empty_string_or_unknown(
            raw.get("projection_id"), "projection_id"
        ),
        "horizon_engine_id": require_non_empty_string_or_unknown(
            raw.get("horizon_engine_id"), "horizon_engine_id"
        ),
        "evaluation_observation_schema_name": require_non_empty_string_or_unknown(
            raw.get("evaluation_observation_schema_name"),
            "evaluation_observation_schema_name",
        ),
        "evaluation_observation": dict(nested),
        "code_sha": require_sha256_or_unknown(raw.get("code_sha"), "code_sha"),
        "evidence_hash": require_sha256_or_unknown(raw.get("evidence_hash"), "evidence_hash"),
        "causal_parent_ids": require_id_list(raw.get("causal_parent_ids"), "causal_parent_ids"),
    }
    return attach_content_hash(freeze_record(canonical))


def validate_real_outcome_horizon_observation_capture_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    return build_real_outcome_horizon_observation_capture_v1(payload)
