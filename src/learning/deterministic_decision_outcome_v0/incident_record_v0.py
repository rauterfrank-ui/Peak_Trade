"""IncidentRecord schema v0. Offline contract only. No capture. No safety authority."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_INCIDENT_RECORD,
    SCHEMA_VERSION_INCIDENT_RECORD_V0,
    FieldSpecV0,
    attach_content_hash,
    freeze_record,
    optional_enum,
    optional_ref,
    optional_string_or_unknown,
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
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    INCIDENT_CLASS_V0,
    KILL_SWITCH_CORRECTNESS_V0,
    KILL_SWITCH_TIMING_LABEL_V0,
    STALE_ROOT_CAUSE_V0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.reason_codes_v0 import (
    validate_hard_block_reasons_v0,
    validate_reason_codes_v0,
)

INCIDENT_RECORD_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("schema_name", "REQUIRED", "string", True, "incident_record identity."),
    FieldSpecV0("schema_version", "REQUIRED", "string", True, "incident_record_v0."),
    FieldSpecV0("record_id", "REQUIRED", "record_id", True, "Immutable record identity."),
    FieldSpecV0("incident_id", "REQUIRED", "record_id", True, "Incident identity."),
    FieldSpecV0("correlation_id", "REQUIRED", "record_id", True, "Correlation identity."),
    FieldSpecV0("cycle_id", "CONDITIONALLY_REQUIRED", "record_id|null", True, "Null until proven."),
    FieldSpecV0("event_time_utc", "REQUIRED", "utc_timestamp", True, "Incident event time UTC."),
    FieldSpecV0(
        "incident_class", "REQUIRED", "enum:INCIDENT_CLASS_V0", True, "Blueprint incident class."
    ),
    FieldSpecV0("reason_codes", "REQUIRED", "coded_ref[]", True, "Namespaced reason codes."),
    FieldSpecV0(
        "hard_block_reasons", "REQUIRED", "coded_ref[]", True, "Namespaced hard-block codes."
    ),
    FieldSpecV0(
        "kill_switch_correctness",
        "OPTIONAL",
        "enum|null",
        True,
        "Optional slot. Not computed. Not a safety-authority claim.",
    ),
    FieldSpecV0(
        "kill_switch_timing_label",
        "OPTIONAL",
        "enum|null",
        True,
        "Optional slot. Independent of profitability. Not computed.",
    ),
    FieldSpecV0(
        "stale_root_cause",
        "OPTIONAL",
        "enum|null",
        True,
        "Optional stale attribution class. UNKNOWN admissible. Not computed.",
    ),
    FieldSpecV0(
        "decision_event_ref", "OPTIONAL", "record_id|null", True, "Optional decision link."
    ),
    FieldSpecV0(
        "decision_time_information_set_ref",
        "CONDITIONALLY_REQUIRED",
        "ref|null",
        True,
        "Opaque ref or null.",
    ),
    FieldSpecV0("market_snapshot_ref", "CONDITIONALLY_REQUIRED", "ref|null", True, "Opaque ref."),
    FieldSpecV0("data_quality_ref", "CONDITIONALLY_REQUIRED", "ref|null", True, "Opaque ref."),
    FieldSpecV0("risk_snapshot_ref", "CONDITIONALLY_REQUIRED", "ref|null", True, "Opaque ref."),
    FieldSpecV0("position_snapshot_ref", "CONDITIONALLY_REQUIRED", "ref|null", True, "Opaque ref."),
    FieldSpecV0("code_sha", "REQUIRED", "sha256|UNKNOWN", True, "UNKNOWN allowed."),
    FieldSpecV0("config_hash", "REQUIRED", "sha256|UNKNOWN", True, "UNKNOWN allowed."),
    FieldSpecV0(
        "artifact_model_version", "OPTIONAL", "string|null", True, "Null when not applicable."
    ),
    FieldSpecV0("authority_owner", "REQUIRED", "string", True, "Producer-declared owner label."),
    FieldSpecV0("producer_id", "REQUIRED", "string", True, "Does not confer authority."),
    FieldSpecV0("producer_version", "OPTIONAL", "string|null", True, "Optional producer version."),
    FieldSpecV0("evidence_hash", "REQUIRED", "sha256|UNKNOWN", True, "UNKNOWN allowed."),
    FieldSpecV0(
        "causal_parent_ids", "REQUIRED", "record_id[]", True, "Empty list is a valid root."
    ),
    FieldSpecV0("evidence_source_refs", "REQUIRED", "ref[]", True, "Opaque source refs."),
    FieldSpecV0("supersedes_id", "OPTIONAL", "record_id|null", True, "Append-only supersession."),
    FieldSpecV0("corrects_id", "OPTIONAL", "record_id|null", True, "Append-only correction."),
    FieldSpecV0(
        "attribution_refs", "OPTIONAL", "record_id[]", True, "Forward refs; empty allowed."
    ),
    FieldSpecV0(
        "counterfactual_refs", "OPTIONAL", "record_id[]", True, "Forward refs; empty allowed."
    ),
    FieldSpecV0("candidate_refs", "OPTIONAL", "record_id[]", True, "Forward refs; empty allowed."),
    FieldSpecV0("content_hash", "REQUIRED", "sha256", False, "Computed; excluded from hash scope."),
)

INCIDENT_RECORD_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in INCIDENT_RECORD_FIELD_SPECS_V0
)


def _evidence_refs(value: Any) -> list[str]:
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


def build_incident_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "incident_record")
    reject_unknown_fields(raw, INCIDENT_RECORD_ALLOWED_FIELDS)
    require_schema(raw, SCHEMA_NAME_INCIDENT_RECORD, SCHEMA_VERSION_INCIDENT_RECORD_V0)
    canonical: dict[str, Any] = {
        "schema_name": SCHEMA_NAME_INCIDENT_RECORD,
        "schema_version": SCHEMA_VERSION_INCIDENT_RECORD_V0,
        "record_id": require_record_id(raw.get("record_id"), "record_id"),
        "incident_id": require_record_id(raw.get("incident_id"), "incident_id"),
        "correlation_id": require_record_id(raw.get("correlation_id"), "correlation_id"),
        "cycle_id": None
        if raw.get("cycle_id") is None
        else require_record_id(raw.get("cycle_id"), "cycle_id"),
        "event_time_utc": require_event_time_utc(raw.get("event_time_utc"), "event_time_utc"),
        "incident_class": require_enum(
            raw.get("incident_class"), "incident_class", INCIDENT_CLASS_V0
        ),
        "reason_codes": validate_reason_codes_v0(raw.get("reason_codes")),
        "hard_block_reasons": validate_hard_block_reasons_v0(raw.get("hard_block_reasons")),
        "kill_switch_correctness": optional_enum(
            raw.get("kill_switch_correctness"),
            "kill_switch_correctness",
            KILL_SWITCH_CORRECTNESS_V0,
        ),
        "kill_switch_timing_label": optional_enum(
            raw.get("kill_switch_timing_label"),
            "kill_switch_timing_label",
            KILL_SWITCH_TIMING_LABEL_V0,
        ),
        "stale_root_cause": optional_enum(
            raw.get("stale_root_cause"), "stale_root_cause", STALE_ROOT_CAUSE_V0
        ),
        "decision_event_ref": None
        if raw.get("decision_event_ref") is None
        else require_record_id(raw.get("decision_event_ref"), "decision_event_ref"),
        "decision_time_information_set_ref": optional_ref(
            raw.get("decision_time_information_set_ref"),
            "decision_time_information_set_ref",
        ),
        "market_snapshot_ref": optional_ref(raw.get("market_snapshot_ref"), "market_snapshot_ref"),
        "data_quality_ref": optional_ref(raw.get("data_quality_ref"), "data_quality_ref"),
        "risk_snapshot_ref": optional_ref(raw.get("risk_snapshot_ref"), "risk_snapshot_ref"),
        "position_snapshot_ref": optional_ref(
            raw.get("position_snapshot_ref"), "position_snapshot_ref"
        ),
        "code_sha": require_sha256_or_unknown(raw.get("code_sha"), "code_sha"),
        "config_hash": require_sha256_or_unknown(raw.get("config_hash"), "config_hash"),
        "artifact_model_version": optional_string_or_unknown(
            raw.get("artifact_model_version"), "artifact_model_version"
        ),
        "authority_owner": require_non_empty_string_or_unknown(
            raw.get("authority_owner"), "authority_owner"
        ),
        "producer_id": require_non_empty_string_or_unknown(raw.get("producer_id"), "producer_id"),
        "producer_version": optional_string_or_unknown(
            raw.get("producer_version"), "producer_version"
        ),
        "evidence_hash": require_sha256_or_unknown(raw.get("evidence_hash"), "evidence_hash"),
        "causal_parent_ids": require_id_list(raw.get("causal_parent_ids"), "causal_parent_ids"),
        "evidence_source_refs": _evidence_refs(raw.get("evidence_source_refs")),
        "supersedes_id": None
        if raw.get("supersedes_id") is None
        else require_record_id(raw.get("supersedes_id"), "supersedes_id"),
        "corrects_id": None
        if raw.get("corrects_id") is None
        else require_record_id(raw.get("corrects_id"), "corrects_id"),
        "attribution_refs": require_id_list(raw.get("attribution_refs"), "attribution_refs"),
        "counterfactual_refs": require_id_list(
            raw.get("counterfactual_refs"), "counterfactual_refs"
        ),
        "candidate_refs": require_id_list(raw.get("candidate_refs"), "candidate_refs"),
    }
    hashed = attach_content_hash(canonical)
    if "content_hash" in raw and raw["content_hash"] != hashed["content_hash"]:
        raise DdoValidationError("CONTENT_HASH_MISMATCH")
    return freeze_record(hashed)


def validate_incident_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_incident_record_v0(payload)
