"""DecisionEvent schema v0. Offline contract only. No capture. No authority."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_DECISION_EVENT,
    SCHEMA_VERSION_DECISION_EVENT_V0,
    FieldSpecV0,
    attach_content_hash,
    freeze_record,
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
    DECISION_RESULT_V0,
    DECISION_TYPE_V0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.outcome_v0 import validate_outcome_ref_v0
from src.learning.deterministic_decision_outcome_v0.reason_codes_v0 import (
    validate_hard_block_reasons_v0,
    validate_reason_codes_v0,
)

DECISION_EVENT_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("schema_name", "REQUIRED", "string", True, "Immutable schema identity."),
    FieldSpecV0("schema_version", "REQUIRED", "string", True, "Version token decision_event_v0."),
    FieldSpecV0("record_id", "REQUIRED", "record_id", True, "Immutable record identity."),
    FieldSpecV0("event_id", "REQUIRED", "record_id", True, "Decision event identity."),
    FieldSpecV0("correlation_id", "REQUIRED", "record_id", True, "Correlation identity."),
    FieldSpecV0(
        "cycle_id",
        "CONDITIONALLY_REQUIRED",
        "record_id|null",
        True,
        "Present as a field; null until a proven cycle producer exists. Not invented.",
    ),
    FieldSpecV0("event_time_utc", "REQUIRED", "utc_timestamp", True, "Decision event time UTC."),
    FieldSpecV0(
        "decision_type", "REQUIRED", "enum:DECISION_TYPE_V0", True, "Blueprint decision type."
    ),
    FieldSpecV0(
        "decision_result",
        "REQUIRED",
        "enum:DECISION_RESULT_V0",
        True,
        "v0 binds NO_ACTION and UNKNOWN only.",
    ),
    FieldSpecV0("reason_codes", "REQUIRED", "coded_ref[]", True, "Namespaced reason codes."),
    FieldSpecV0(
        "hard_block_reasons",
        "REQUIRED",
        "coded_ref[]",
        True,
        "Namespaced hard-block codes. Empty list is valid.",
    ),
    FieldSpecV0(
        "decision_time_information_set_ref",
        "CONDITIONALLY_REQUIRED",
        "ref|null",
        True,
        "Snapshot/ref identity; null if producer did not supply.",
    ),
    FieldSpecV0("market_snapshot_ref", "CONDITIONALLY_REQUIRED", "ref|null", True, "Opaque ref."),
    FieldSpecV0("feature_snapshot_ref", "CONDITIONALLY_REQUIRED", "ref|null", True, "Opaque ref."),
    FieldSpecV0("data_quality_ref", "CONDITIONALLY_REQUIRED", "ref|null", True, "Opaque ref."),
    FieldSpecV0("risk_snapshot_ref", "CONDITIONALLY_REQUIRED", "ref|null", True, "Opaque ref."),
    FieldSpecV0("position_snapshot_ref", "CONDITIONALLY_REQUIRED", "ref|null", True, "Opaque ref."),
    FieldSpecV0(
        "selected_instrument_ref",
        "CONDITIONALLY_REQUIRED",
        "ref|null",
        True,
        "Opaque ref. Not a selection-authority claim.",
    ),
    FieldSpecV0(
        "core_state_before_ref",
        "OPTIONAL",
        "ref|null",
        True,
        "Applicable core-state before ref. Null when not applicable.",
    ),
    FieldSpecV0(
        "core_state_after_ref",
        "OPTIONAL",
        "ref|null",
        True,
        "Applicable core-state after ref. Null when not applicable.",
    ),
    FieldSpecV0("plan_ref", "OPTIONAL", "ref|null", True, "Null when not applicable."),
    FieldSpecV0("execution_ref", "OPTIONAL", "ref|null", True, "Null when not applicable."),
    FieldSpecV0(
        "expected_outcome_ref", "OPTIONAL", "outcome_ref|null", True, "Link only; no engine."
    ),
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
    FieldSpecV0("authority_owner", "REQUIRED", "string", True, "Producer-declared owner label."),
    FieldSpecV0("producer_id", "REQUIRED", "string", True, "Does not confer authority."),
    FieldSpecV0("producer_version", "OPTIONAL", "string|null", True, "Optional producer version."),
    FieldSpecV0(
        "evidence_hash", "REQUIRED", "sha256|UNKNOWN", True, "UNKNOWN is explicit semantics."
    ),
    FieldSpecV0(
        "causal_parent_ids", "REQUIRED", "record_id[]", True, "Empty list is a valid root."
    ),
    FieldSpecV0("evidence_source_refs", "REQUIRED", "ref[]", True, "Opaque source evidence refs."),
    FieldSpecV0("supersedes_id", "OPTIONAL", "record_id|null", True, "Append-only supersession."),
    FieldSpecV0("corrects_id", "OPTIONAL", "record_id|null", True, "Append-only correction."),
    FieldSpecV0(
        "attribution_refs",
        "OPTIONAL",
        "record_id[]",
        True,
        "Forward refs to attribution_record. Empty until those records exist.",
    ),
    FieldSpecV0(
        "counterfactual_refs",
        "OPTIONAL",
        "record_id[]",
        True,
        "Forward refs to counterfactual_record. Empty until those records exist.",
    ),
    FieldSpecV0(
        "candidate_refs",
        "OPTIONAL",
        "record_id[]",
        True,
        "Forward refs to candidate_artifact. Empty until those records exist.",
    ),
    FieldSpecV0("content_hash", "REQUIRED", "sha256", False, "Computed; excluded from hash scope."),
)

DECISION_EVENT_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in DECISION_EVENT_FIELD_SPECS_V0
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


def build_decision_event_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "decision_event")
    reject_unknown_fields(raw, DECISION_EVENT_ALLOWED_FIELDS)
    require_schema(raw, SCHEMA_NAME_DECISION_EVENT, SCHEMA_VERSION_DECISION_EVENT_V0)
    expected_outcome = raw.get("expected_outcome_ref")
    canonical: dict[str, Any] = {
        "schema_name": SCHEMA_NAME_DECISION_EVENT,
        "schema_version": SCHEMA_VERSION_DECISION_EVENT_V0,
        "record_id": require_record_id(raw.get("record_id"), "record_id"),
        "event_id": require_record_id(raw.get("event_id"), "event_id"),
        "correlation_id": require_record_id(raw.get("correlation_id"), "correlation_id"),
        "cycle_id": None
        if raw.get("cycle_id") is None
        else require_record_id(raw.get("cycle_id"), "cycle_id"),
        "event_time_utc": require_event_time_utc(raw.get("event_time_utc"), "event_time_utc"),
        "decision_type": require_enum(raw.get("decision_type"), "decision_type", DECISION_TYPE_V0),
        "decision_result": require_enum(
            raw.get("decision_result"), "decision_result", DECISION_RESULT_V0
        ),
        "reason_codes": validate_reason_codes_v0(raw.get("reason_codes")),
        "hard_block_reasons": validate_hard_block_reasons_v0(raw.get("hard_block_reasons")),
        "decision_time_information_set_ref": optional_ref(
            raw.get("decision_time_information_set_ref"),
            "decision_time_information_set_ref",
        ),
        "market_snapshot_ref": optional_ref(raw.get("market_snapshot_ref"), "market_snapshot_ref"),
        "feature_snapshot_ref": optional_ref(
            raw.get("feature_snapshot_ref"), "feature_snapshot_ref"
        ),
        "data_quality_ref": optional_ref(raw.get("data_quality_ref"), "data_quality_ref"),
        "risk_snapshot_ref": optional_ref(raw.get("risk_snapshot_ref"), "risk_snapshot_ref"),
        "position_snapshot_ref": optional_ref(
            raw.get("position_snapshot_ref"), "position_snapshot_ref"
        ),
        "selected_instrument_ref": optional_ref(
            raw.get("selected_instrument_ref"), "selected_instrument_ref"
        ),
        "core_state_before_ref": optional_ref(
            raw.get("core_state_before_ref"), "core_state_before_ref"
        ),
        "core_state_after_ref": optional_ref(
            raw.get("core_state_after_ref"), "core_state_after_ref"
        ),
        "plan_ref": optional_ref(raw.get("plan_ref"), "plan_ref"),
        "execution_ref": optional_ref(raw.get("execution_ref"), "execution_ref"),
        "expected_outcome_ref": None
        if expected_outcome is None
        else dict(validate_outcome_ref_v0(expected_outcome)),
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


def validate_decision_event_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_decision_event_v0(payload)
