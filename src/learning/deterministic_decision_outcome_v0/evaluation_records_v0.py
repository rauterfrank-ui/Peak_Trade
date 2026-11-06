"""CounterfactualRecord and AttributionRecord schemas v0.

Fixture/offline contracts only. No outcome engine. No hindsight relabeling.
No safety or trading authority.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_ATTRIBUTION_RECORD,
    SCHEMA_NAME_COUNTERFACTUAL_RECORD,
    SCHEMA_VERSION_ATTRIBUTION_RECORD_V0,
    SCHEMA_VERSION_COUNTERFACTUAL_RECORD_V0,
    SHARED_IDENTITY_FIELD_SPECS_V0,
    FieldSpecV0,
    finalize_record_v0,
    optional_enum,
    optional_ref,
    optional_string_or_unknown,
    parse_shared_envelope_v0,
    reject_unknown_fields,
    require_enum,
    require_mapping,
    require_record_id,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    COUNTERFACTUAL_ADMISSIBILITY_V0,
    KILL_SWITCH_CORRECTNESS_V0,
    KILL_SWITCH_TIMING_LABEL_V0,
    OUTCOME_ROOT_CAUSE_V0,
    STALE_ROOT_CAUSE_V0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError

_COUNTERFACTUAL_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("decision_event_ref", "REQUIRED", "record_id", True, "DecisionEvent lineage link."),
    FieldSpecV0(
        "incident_record_ref", "OPTIONAL", "record_id|null", True, "Optional incident link."
    ),
    FieldSpecV0("outcome_record_ref", "OPTIONAL", "record_id|null", True, "Optional outcome link."),
    FieldSpecV0(
        "counterfactual_admissibility",
        "REQUIRED",
        "enum:COUNTERFACTUAL_ADMISSIBILITY_V0",
        True,
        "OBSERVED/REPLAYABLE/MODELLED/UNAVAILABLE/UNKNOWN.",
    ),
    FieldSpecV0(
        "assumptions",
        "CONDITIONALLY_REQUIRED",
        "string|null",
        True,
        "Mandatory when admissibility=MODELLED. Null otherwise unless supplied.",
    ),
    FieldSpecV0(
        "confidence",
        "OPTIONAL",
        "string|null",
        True,
        "Opaque confidence token or UNKNOWN. Not computed.",
    ),
    FieldSpecV0(
        "alternative_result_ref",
        "OPTIONAL",
        "ref|null",
        True,
        "Must be null when admissibility=UNAVAILABLE.",
    ),
    FieldSpecV0(
        "decision_time_information_set_ref",
        "CONDITIONALLY_REQUIRED",
        "ref|null",
        True,
        "Immutable decision-time information set. Correctness uses this set.",
    ),
    FieldSpecV0(
        "evaluation_time_information_set_ref",
        "OPTIONAL",
        "ref|null",
        True,
        "May be larger than decision-time. Must not relabel safety correctness.",
    ),
)

_ATTRIBUTION_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0(
        "decision_event_ref", "OPTIONAL", "record_id|null", True, "DecisionEvent link if present."
    ),
    FieldSpecV0(
        "incident_record_ref", "OPTIONAL", "record_id|null", True, "Incident link if present."
    ),
    FieldSpecV0(
        "outcome_record_ref", "OPTIONAL", "record_id|null", True, "Outcome link if present."
    ),
    FieldSpecV0(
        "root_cause",
        "OPTIONAL",
        "enum|null",
        True,
        "Blueprint family or UNKNOWN/null. Not computed.",
    ),
    FieldSpecV0(
        "kill_switch_correctness",
        "OPTIONAL",
        "enum|null",
        True,
        "Optional slot. Independent of later market path.",
    ),
    FieldSpecV0(
        "kill_switch_timing_label",
        "OPTIONAL",
        "enum|null",
        True,
        "Optional slot. Independent of profitability.",
    ),
    FieldSpecV0(
        "stale_root_cause",
        "OPTIONAL",
        "enum|null",
        True,
        "Optional stale attribution class. UNKNOWN admissible.",
    ),
    FieldSpecV0(
        "safety_correctness_uses_decision_time_information_set",
        "REQUIRED",
        "bool",
        True,
        "Must be true. Economic hindsight cannot rewrite safety correctness.",
    ),
)

COUNTERFACTUAL_RECORD_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1]
    + _COUNTERFACTUAL_EXTRA
    + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
ATTRIBUTION_RECORD_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _ATTRIBUTION_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
COUNTERFACTUAL_RECORD_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in COUNTERFACTUAL_RECORD_FIELD_SPECS_V0
)
ATTRIBUTION_RECORD_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in ATTRIBUTION_RECORD_FIELD_SPECS_V0
)


def build_counterfactual_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "counterfactual_record")
    reject_unknown_fields(raw, COUNTERFACTUAL_RECORD_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_COUNTERFACTUAL_RECORD,
        schema_version=SCHEMA_VERSION_COUNTERFACTUAL_RECORD_V0,
    )
    admissibility = require_enum(
        raw.get("counterfactual_admissibility"),
        "counterfactual_admissibility",
        COUNTERFACTUAL_ADMISSIBILITY_V0,
    )
    assumptions = optional_string_or_unknown(raw.get("assumptions"), "assumptions")
    alternative = optional_ref(raw.get("alternative_result_ref"), "alternative_result_ref")
    if admissibility == "MODELLED" and assumptions is None:
        raise DdoValidationError("MODELLED_COUNTERFACTUAL_REQUIRES_ASSUMPTIONS")
    if admissibility == "UNAVAILABLE" and alternative is not None:
        raise DdoValidationError("UNAVAILABLE_COUNTERFACTUAL_MUST_NOT_HAVE_ALTERNATIVE")
    canonical = {
        **envelope,
        "decision_event_ref": require_record_id(
            raw.get("decision_event_ref"), "decision_event_ref"
        ),
        "incident_record_ref": None
        if raw.get("incident_record_ref") is None
        else require_record_id(raw.get("incident_record_ref"), "incident_record_ref"),
        "outcome_record_ref": None
        if raw.get("outcome_record_ref") is None
        else require_record_id(raw.get("outcome_record_ref"), "outcome_record_ref"),
        "counterfactual_admissibility": admissibility,
        "assumptions": assumptions,
        "confidence": optional_string_or_unknown(raw.get("confidence"), "confidence"),
        "alternative_result_ref": alternative,
        "decision_time_information_set_ref": optional_ref(
            raw.get("decision_time_information_set_ref"),
            "decision_time_information_set_ref",
        ),
        "evaluation_time_information_set_ref": optional_ref(
            raw.get("evaluation_time_information_set_ref"),
            "evaluation_time_information_set_ref",
        ),
    }
    return finalize_record_v0(canonical, raw)


def validate_counterfactual_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_counterfactual_record_v0(payload)


def build_attribution_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "attribution_record")
    reject_unknown_fields(raw, ATTRIBUTION_RECORD_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_ATTRIBUTION_RECORD,
        schema_version=SCHEMA_VERSION_ATTRIBUTION_RECORD_V0,
    )
    decision_id = (
        None
        if raw.get("decision_event_ref") is None
        else require_record_id(raw.get("decision_event_ref"), "decision_event_ref")
    )
    incident_id = (
        None
        if raw.get("incident_record_ref") is None
        else require_record_id(raw.get("incident_record_ref"), "incident_record_ref")
    )
    if decision_id is None and incident_id is None:
        raise DdoValidationError("ATTRIBUTION_REQUIRES_DECISION_OR_INCIDENT_REF")
    safety_uses_decision_time = raw.get("safety_correctness_uses_decision_time_information_set")
    if safety_uses_decision_time is not True:
        raise DdoValidationError("SAFETY_CORRECTNESS_MUST_USE_DECISION_TIME_INFORMATION_SET")
    canonical = {
        **envelope,
        "decision_event_ref": decision_id,
        "incident_record_ref": incident_id,
        "outcome_record_ref": None
        if raw.get("outcome_record_ref") is None
        else require_record_id(raw.get("outcome_record_ref"), "outcome_record_ref"),
        "root_cause": optional_enum(raw.get("root_cause"), "root_cause", OUTCOME_ROOT_CAUSE_V0),
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
        "safety_correctness_uses_decision_time_information_set": True,
    }
    return finalize_record_v0(canonical, raw)


def validate_attribution_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_attribution_record_v0(payload)
