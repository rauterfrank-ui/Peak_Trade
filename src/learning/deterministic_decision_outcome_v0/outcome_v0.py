"""OutcomeRef and minimal structural OutcomeRecord v0.

OutcomeEngine / outcome computation is out of scope. Scores, horizons and
root-cause values are stored as declared tokens or UNKNOWN; they are not
computed here.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_OUTCOME_RECORD,
    SCHEMA_NAME_OUTCOME_REF,
    SCHEMA_VERSION_OUTCOME_RECORD_V0,
    SCHEMA_VERSION_OUTCOME_REF_V0,
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
    COUNTERFACTUAL_ADMISSIBILITY_V0,
    OUTCOME_LINK_STATUS_V0,
    OUTCOME_ROOT_CAUSE_V0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError

OUTCOME_REF_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("schema_name", "REQUIRED", "string", True, "outcome_ref identity."),
    FieldSpecV0("schema_version", "REQUIRED", "string", True, "outcome_ref_v0."),
    FieldSpecV0(
        "link_status", "REQUIRED", "enum:OUTCOME_LINK_STATUS_V0", True, "ABSENT/PRESENT/UNKNOWN."
    ),
    FieldSpecV0(
        "outcome_record_id",
        "CONDITIONALLY_REQUIRED",
        "record_id|null",
        True,
        "Required when link_status=PRESENT; null when ABSENT.",
    ),
)

OUTCOME_RECORD_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("schema_name", "REQUIRED", "string", True, "outcome_record identity."),
    FieldSpecV0("schema_version", "REQUIRED", "string", True, "outcome_record_v0."),
    FieldSpecV0("record_id", "REQUIRED", "record_id", True, "Immutable record identity."),
    FieldSpecV0("decision_event_ref", "REQUIRED", "record_id", True, "DecisionEvent lineage link."),
    FieldSpecV0(
        "incident_record_ref", "OPTIONAL", "record_id|null", True, "Optional incident link."
    ),
    FieldSpecV0(
        "evaluation_horizon",
        "REQUIRED",
        "string",
        True,
        "Opaque horizon token. Numeric policy is not bound in v0.",
    ),
    FieldSpecV0(
        "actual_outcome_ref",
        "CONDITIONALLY_REQUIRED",
        "ref|null",
        True,
        "Opaque observed-outcome evidence ref or null/UNKNOWN. Not computed.",
    ),
    FieldSpecV0(
        "counterfactual_admissibility",
        "REQUIRED",
        "enum:COUNTERFACTUAL_ADMISSIBILITY_V0",
        True,
        "Blueprint admissibility. No counterfactual engine.",
    ),
    FieldSpecV0(
        "safety_score", "OPTIONAL", "string|null", True, "Opaque token or UNKNOWN. Not computed."
    ),
    FieldSpecV0(
        "decision_score", "OPTIONAL", "string|null", True, "Opaque token or UNKNOWN. Not computed."
    ),
    FieldSpecV0(
        "economic_score", "OPTIONAL", "string|null", True, "Opaque token or UNKNOWN. Not computed."
    ),
    FieldSpecV0("root_cause", "OPTIONAL", "enum|null", True, "Blueprint family or UNKNOWN/null."),
    FieldSpecV0(
        "confidence", "OPTIONAL", "string|null", True, "Opaque token or UNKNOWN. Not computed."
    ),
    FieldSpecV0(
        "event_time_utc", "REQUIRED", "utc_timestamp", True, "Outcome record event time UTC."
    ),
    FieldSpecV0("correlation_id", "REQUIRED", "record_id", True, "Correlation identity."),
    FieldSpecV0("cycle_id", "CONDITIONALLY_REQUIRED", "record_id|null", True, "Null until proven."),
    FieldSpecV0(
        "causal_parent_ids", "REQUIRED", "record_id[]", True, "Typically the decision/incident."
    ),
    FieldSpecV0("producer_id", "REQUIRED", "string", True, "Does not confer authority."),
    FieldSpecV0("producer_version", "OPTIONAL", "string|null", True, "Optional producer version."),
    FieldSpecV0("authority_owner", "REQUIRED", "string", True, "Producer-declared owner label."),
    FieldSpecV0("code_sha", "REQUIRED", "sha256|UNKNOWN", True, "UNKNOWN allowed."),
    FieldSpecV0("config_hash", "REQUIRED", "sha256|UNKNOWN", True, "UNKNOWN allowed."),
    FieldSpecV0(
        "artifact_model_version", "OPTIONAL", "string|null", True, "Null when not applicable."
    ),
    FieldSpecV0("evidence_hash", "REQUIRED", "sha256|UNKNOWN", True, "UNKNOWN allowed."),
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

OUTCOME_REF_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in OUTCOME_REF_FIELD_SPECS_V0
)
OUTCOME_RECORD_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in OUTCOME_RECORD_FIELD_SPECS_V0
)

OUTCOME_RECORD_SEMANTICS_STATUS: Final[str] = (
    "STRUCTURAL_SCHEMA_ONLY_NO_OUTCOME_ENGINE_SCORES_NOT_COMPUTED"
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


def validate_outcome_ref_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "outcome_ref")
    reject_unknown_fields(raw, OUTCOME_REF_ALLOWED_FIELDS)
    require_schema(raw, SCHEMA_NAME_OUTCOME_REF, SCHEMA_VERSION_OUTCOME_REF_V0)
    link_status = require_enum(raw.get("link_status"), "link_status", OUTCOME_LINK_STATUS_V0)
    outcome_record_id = raw.get("outcome_record_id")
    if link_status == "ABSENT":
        if outcome_record_id is not None:
            raise DdoValidationError("OUTCOME_REF_ABSENT_MUST_HAVE_NULL_ID")
        outcome_id = None
    elif link_status == "PRESENT":
        outcome_id = require_record_id(outcome_record_id, "outcome_record_id")
    else:
        outcome_id = (
            None
            if outcome_record_id is None
            else require_record_id(outcome_record_id, "outcome_record_id")
        )
    return freeze_record(
        {
            "schema_name": SCHEMA_NAME_OUTCOME_REF,
            "schema_version": SCHEMA_VERSION_OUTCOME_REF_V0,
            "link_status": link_status,
            "outcome_record_id": outcome_id,
        }
    )


def build_outcome_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "outcome_record")
    reject_unknown_fields(raw, OUTCOME_RECORD_ALLOWED_FIELDS)
    require_schema(raw, SCHEMA_NAME_OUTCOME_RECORD, SCHEMA_VERSION_OUTCOME_RECORD_V0)
    canonical: dict[str, Any] = {
        "schema_name": SCHEMA_NAME_OUTCOME_RECORD,
        "schema_version": SCHEMA_VERSION_OUTCOME_RECORD_V0,
        "record_id": require_record_id(raw.get("record_id"), "record_id"),
        "decision_event_ref": require_record_id(
            raw.get("decision_event_ref"), "decision_event_ref"
        ),
        "incident_record_ref": None
        if raw.get("incident_record_ref") is None
        else require_record_id(raw.get("incident_record_ref"), "incident_record_ref"),
        "evaluation_horizon": require_non_empty_string_or_unknown(
            raw.get("evaluation_horizon"), "evaluation_horizon"
        ),
        "actual_outcome_ref": optional_ref(raw.get("actual_outcome_ref"), "actual_outcome_ref"),
        "counterfactual_admissibility": require_enum(
            raw.get("counterfactual_admissibility"),
            "counterfactual_admissibility",
            COUNTERFACTUAL_ADMISSIBILITY_V0,
        ),
        "safety_score": optional_string_or_unknown(raw.get("safety_score"), "safety_score"),
        "decision_score": optional_string_or_unknown(raw.get("decision_score"), "decision_score"),
        "economic_score": optional_string_or_unknown(raw.get("economic_score"), "economic_score"),
        "root_cause": optional_enum(raw.get("root_cause"), "root_cause", OUTCOME_ROOT_CAUSE_V0),
        "confidence": optional_string_or_unknown(raw.get("confidence"), "confidence"),
        "event_time_utc": require_event_time_utc(raw.get("event_time_utc"), "event_time_utc"),
        "correlation_id": require_record_id(raw.get("correlation_id"), "correlation_id"),
        "cycle_id": None
        if raw.get("cycle_id") is None
        else require_record_id(raw.get("cycle_id"), "cycle_id"),
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
        "evidence_hash": require_sha256_or_unknown(raw.get("evidence_hash"), "evidence_hash"),
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


def validate_outcome_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_outcome_record_v0(payload)
