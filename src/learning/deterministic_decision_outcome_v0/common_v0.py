"""Shared field specs, identity rules, and canonicalization for DDO records v0."""

from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    NULLABILITY_V0,
    UNKNOWN,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import (
    DdoUnsupportedSchemaVersionError,
    DdoValidationError,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    canonicalize_json_value,
    compute_content_hash_v0,
)

SCHEMA_NAME_DECISION_EVENT: Final[str] = "decision_event"
SCHEMA_VERSION_DECISION_EVENT_V0: Final[str] = "decision_event_v0"
SCHEMA_NAME_INCIDENT_RECORD: Final[str] = "incident_record"
SCHEMA_VERSION_INCIDENT_RECORD_V0: Final[str] = "incident_record_v0"
SCHEMA_NAME_OUTCOME_REF: Final[str] = "outcome_ref"
SCHEMA_VERSION_OUTCOME_REF_V0: Final[str] = "outcome_ref_v0"
SCHEMA_NAME_OUTCOME_RECORD: Final[str] = "outcome_record"
SCHEMA_VERSION_OUTCOME_RECORD_V0: Final[str] = "outcome_record_v0"
SCHEMA_NAME_LEDGER_ENVELOPE: Final[str] = "ddo_ledger_envelope"
SCHEMA_VERSION_LEDGER_ENVELOPE_V0: Final[str] = "ddo_ledger_envelope_v0"
SCHEMA_NAME_COUNTERFACTUAL_RECORD: Final[str] = "counterfactual_record"
SCHEMA_VERSION_COUNTERFACTUAL_RECORD_V0: Final[str] = "counterfactual_record_v0"
SCHEMA_NAME_ATTRIBUTION_RECORD: Final[str] = "attribution_record"
SCHEMA_VERSION_ATTRIBUTION_RECORD_V0: Final[str] = "attribution_record_v0"
SCHEMA_NAME_LEARNING_HYPOTHESIS: Final[str] = "learning_hypothesis"
SCHEMA_VERSION_LEARNING_HYPOTHESIS_V0: Final[str] = "learning_hypothesis_v0"
SCHEMA_NAME_CANDIDATE_ARTIFACT: Final[str] = "candidate_artifact"
SCHEMA_VERSION_CANDIDATE_ARTIFACT_V0: Final[str] = "candidate_artifact_v0"
SCHEMA_NAME_VALIDATION_EVIDENCE_PACK: Final[str] = "validation_evidence_pack"
SCHEMA_VERSION_VALIDATION_EVIDENCE_PACK_V0: Final[str] = "validation_evidence_pack_v0"
SCHEMA_NAME_PROMOTION_POLICY: Final[str] = "promotion_policy"
SCHEMA_VERSION_PROMOTION_POLICY_V0: Final[str] = "promotion_policy_v0"
SCHEMA_NAME_PROMOTION_ELIGIBILITY: Final[str] = "promotion_eligibility_record"
SCHEMA_VERSION_PROMOTION_ELIGIBILITY_V0: Final[str] = "promotion_eligibility_record_v0"
SCHEMA_NAME_RELEASE_ARTIFACT: Final[str] = "release_artifact"
SCHEMA_VERSION_RELEASE_ARTIFACT_V0: Final[str] = "release_artifact_v0"
SCHEMA_NAME_DEPLOYMENT_RECORD: Final[str] = "deployment_record"
SCHEMA_VERSION_DEPLOYMENT_RECORD_V0: Final[str] = "deployment_record_v0"
SCHEMA_NAME_ROLLBACK_RECORD: Final[str] = "rollback_record"
SCHEMA_VERSION_ROLLBACK_RECORD_V0: Final[str] = "rollback_record_v0"
SCHEMA_NAME_AUTONOMY_CYCLE: Final[str] = "autonomy_cycle_record"
SCHEMA_VERSION_AUTONOMY_CYCLE_V0: Final[str] = "autonomy_cycle_record_v0"
SCHEMA_NAME_HEALTH_SNAPSHOT: Final[str] = "health_snapshot"
SCHEMA_VERSION_HEALTH_SNAPSHOT_V0: Final[str] = "health_snapshot_v0"

RECORD_ID_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")
SHA256_OR_UNKNOWN_RE: Final[re.Pattern[str]] = re.compile(rf"^(?:{UNKNOWN}|[0-9a-f]{{64}})$")
UTC_EVENT_TIME_RE: Final[re.Pattern[str]] = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,9})?Z$"
)
REF_OR_UNKNOWN_RE: Final[re.Pattern[str]] = re.compile(r"^(?:UNKNOWN|[A-Za-z0-9._:/-]{1,256})$")


@dataclass(frozen=True)
class FieldSpecV0:
    name: str
    nullability: str
    value_kind: str
    in_content_hash: bool
    notes: str

    def __post_init__(self) -> None:
        if self.nullability not in NULLABILITY_V0:
            raise DdoValidationError(f"INVALID_NULLABILITY:{self.name}")


def require_mapping(payload: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise DdoValidationError(f"{label}_MUST_BE_OBJECT")
    return payload


def require_record_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not RECORD_ID_RE.fullmatch(value):
        raise DdoValidationError(f"INVALID_RECORD_ID:{field}")
    return value


def optional_record_id(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return require_record_id(value, field)


def require_event_time_utc(value: Any, field: str) -> str:
    if not isinstance(value, str) or not UTC_EVENT_TIME_RE.fullmatch(value):
        raise DdoValidationError(f"INVALID_EVENT_TIME_UTC:{field}")
    return value


def require_sha256_or_unknown(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SHA256_OR_UNKNOWN_RE.fullmatch(value):
        raise DdoValidationError(f"INVALID_SHA256_OR_UNKNOWN:{field}")
    return value


def optional_sha256_or_unknown(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return require_sha256_or_unknown(value, field)


def optional_ref(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not REF_OR_UNKNOWN_RE.fullmatch(value):
        raise DdoValidationError(f"INVALID_REF:{field}")
    return value


def require_non_empty_string_or_unknown(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise DdoValidationError(f"INVALID_STRING:{field}")
    return value


def optional_string_or_unknown(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return require_non_empty_string_or_unknown(value, field)


def require_enum(value: Any, field: str, allowed: tuple[str, ...]) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise DdoValidationError(f"UNKNOWN_ENUM_VALUE:{field}:{value!r}")
    return value


def optional_enum(value: Any, field: str, allowed: tuple[str, ...]) -> str | None:
    if value is None:
        return None
    return require_enum(value, field, allowed)


def require_id_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise DdoValidationError(f"{field}_MUST_BE_LIST")
    out: list[str] = []
    seen: set[str] = set()
    for item in value:
        ident = require_record_id(item, field)
        if ident in seen:
            raise DdoValidationError(f"{field}_DUPLICATE_ID:{ident}")
        seen.add(ident)
        out.append(ident)
    return out


def require_schema(payload: Mapping[str, Any], schema_name: str, schema_version: str) -> None:
    name = payload.get("schema_name")
    version = payload.get("schema_version")
    if name != schema_name:
        raise DdoValidationError(f"SCHEMA_NAME_MISMATCH:{name!r}")
    if version != schema_version:
        raise DdoUnsupportedSchemaVersionError(
            f"UNSUPPORTED_SCHEMA_VERSION:{schema_name}:{version!r}"
        )


def reject_unknown_fields(payload: Mapping[str, Any], allowed: frozenset[str]) -> None:
    extra = sorted(set(payload.keys()) - allowed)
    if extra:
        raise DdoValidationError(f"UNEXPECTED_FIELD:{extra}")


def freeze_record(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    canonical = canonicalize_json_value(payload)
    if not isinstance(canonical, dict):
        raise DdoValidationError("RECORD_MUST_BE_OBJECT")
    return MappingProxyType(canonical)


def attach_content_hash(payload: dict[str, Any]) -> dict[str, Any]:
    hashed = dict(payload)
    hashed.pop("content_hash", None)
    digest = compute_content_hash_v0(hashed)
    hashed["content_hash"] = digest
    return hashed


SHARED_IDENTITY_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("schema_name", "REQUIRED", "string", True, "Immutable schema identity."),
    FieldSpecV0("schema_version", "REQUIRED", "string", True, "Immutable schema version."),
    FieldSpecV0("record_id", "REQUIRED", "record_id", True, "Immutable record identity."),
    FieldSpecV0("event_time_utc", "REQUIRED", "utc_timestamp", True, "Record event time UTC."),
    FieldSpecV0("correlation_id", "REQUIRED", "record_id", True, "Correlation identity."),
    FieldSpecV0(
        "cycle_id",
        "CONDITIONALLY_REQUIRED",
        "record_id|null",
        True,
        "Null until a proven cycle producer exists, except autonomy_cycle_record.",
    ),
    FieldSpecV0(
        "causal_parent_ids", "REQUIRED", "record_id[]", True, "Empty list is a valid root."
    ),
    FieldSpecV0("producer_id", "REQUIRED", "string", True, "Does not confer authority."),
    FieldSpecV0("producer_version", "OPTIONAL", "string|null", True, "Optional producer version."),
    FieldSpecV0("authority_owner", "REQUIRED", "string", True, "Producer-declared owner label."),
    FieldSpecV0("code_sha", "REQUIRED", "sha256|UNKNOWN", True, "UNKNOWN is explicit semantics."),
    FieldSpecV0(
        "config_hash", "REQUIRED", "sha256|UNKNOWN", True, "UNKNOWN is explicit semantics."
    ),
    FieldSpecV0(
        "artifact_model_version",
        "OPTIONAL",
        "string|null",
        True,
        "Null when no artifact/model applies.",
    ),
    FieldSpecV0(
        "environment_fingerprint",
        "OPTIONAL",
        "string|null",
        True,
        "Opaque environment identity. UNKNOWN admissible. Not computed.",
    ),
    FieldSpecV0(
        "evidence_hash", "REQUIRED", "sha256|UNKNOWN", True, "UNKNOWN is explicit semantics."
    ),
    FieldSpecV0("evidence_source_refs", "REQUIRED", "ref[]", True, "Opaque source evidence refs."),
    FieldSpecV0("supersedes_id", "OPTIONAL", "record_id|null", True, "Append-only supersession."),
    FieldSpecV0("corrects_id", "OPTIONAL", "record_id|null", True, "Append-only correction."),
    FieldSpecV0("content_hash", "REQUIRED", "sha256", False, "Computed; excluded from hash scope."),
)


def parse_evidence_source_refs_v0(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise DdoValidationError("EVIDENCE_SOURCE_REFS_MUST_BE_LIST")
    out: list[str] = []
    for item in value:
        ref = optional_ref(item, "evidence_source_refs")
        if ref is None:
            raise DdoValidationError("EVIDENCE_SOURCE_REF_NULL_FORBIDDEN")
        out.append(ref)
    return out


def parse_shared_envelope_v0(
    raw: Mapping[str, Any],
    *,
    schema_name: str,
    schema_version: str,
    cycle_id_required: bool = False,
) -> dict[str, Any]:
    require_schema(raw, schema_name, schema_version)
    cycle_raw = raw.get("cycle_id")
    if cycle_id_required:
        cycle_id = require_record_id(cycle_raw, "cycle_id")
    else:
        cycle_id = None if cycle_raw is None else require_record_id(cycle_raw, "cycle_id")
    return {
        "schema_name": schema_name,
        "schema_version": schema_version,
        "record_id": require_record_id(raw.get("record_id"), "record_id"),
        "event_time_utc": require_event_time_utc(raw.get("event_time_utc"), "event_time_utc"),
        "correlation_id": require_record_id(raw.get("correlation_id"), "correlation_id"),
        "cycle_id": cycle_id,
        "causal_parent_ids": require_id_list(raw.get("causal_parent_ids"), "causal_parent_ids"),
        "producer_id": require_non_empty_string_or_unknown(raw.get("producer_id"), "producer_id"),
        "producer_version": optional_string_or_unknown(
            raw.get("producer_version"), "producer_version"
        ),
        "authority_owner": require_non_empty_string_or_unknown(
            raw.get("authority_owner"), "authority_owner"
        ),
        "code_sha": require_sha256_or_unknown(raw.get("code_sha"), "code_sha"),
        "config_hash": require_sha256_or_unknown(raw.get("config_hash"), "config_hash"),
        "artifact_model_version": optional_string_or_unknown(
            raw.get("artifact_model_version"), "artifact_model_version"
        ),
        "environment_fingerprint": optional_string_or_unknown(
            raw.get("environment_fingerprint"), "environment_fingerprint"
        ),
        "evidence_hash": require_sha256_or_unknown(raw.get("evidence_hash"), "evidence_hash"),
        "evidence_source_refs": parse_evidence_source_refs_v0(raw.get("evidence_source_refs")),
        "supersedes_id": optional_record_id(raw.get("supersedes_id"), "supersedes_id"),
        "corrects_id": optional_record_id(raw.get("corrects_id"), "corrects_id"),
    }


def finalize_record_v0(
    canonical: dict[str, Any], raw: Mapping[str, Any]
) -> MappingProxyType[str, Any]:
    hashed = attach_content_hash(canonical)
    if "content_hash" in raw and raw["content_hash"] != hashed["content_hash"]:
        raise DdoValidationError("CONTENT_HASH_MISMATCH")
    return freeze_record(hashed)
