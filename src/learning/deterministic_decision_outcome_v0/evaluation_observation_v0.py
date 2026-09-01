"""Evaluation-time observation input for the offline DDO engine v0.

This is an engine input, not a ledger record type. Missing facts remain
UNKNOWN/UNAVAILABLE. The observation cannot confer safety or trading
authority and cannot relabel decision-time safety correctness.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    freeze_record,
    optional_enum,
    optional_ref,
    optional_string_or_unknown,
    reject_unknown_fields,
    require_enum,
    require_event_time_utc,
    require_mapping,
    require_record_id,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    COUNTERFACTUAL_ADMISSIBILITY_V0,
    DECISION_SCORE_V0,
    EVALUATION_HORIZON_V0,
    KILL_SWITCH_TIMING_LABEL_V0,
    OUTCOME_ROOT_CAUSE_V0,
    PROTECTED_CONDITION_V0,
    STALE_ROOT_CAUSE_V0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.hindsight_guard_v0 import (
    assert_no_hindsight_safety_relabel_v0,
)

EVALUATION_OBSERVATION_SCHEMA_NAME: Final[str] = "evaluation_observation"
EVALUATION_OBSERVATION_SCHEMA_VERSION: Final[str] = "evaluation_observation_v0"

EVALUATION_OBSERVATION_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "schema_name",
        "schema_version",
        "decision_event_ref",
        "incident_record_ref",
        "evaluation_horizon",
        "evaluation_time_utc",
        "evaluation_time_information_set_ref",
        "protected_condition",
        "kill_switch_timing_label",
        "stale_root_cause",
        "root_cause",
        "actual_outcome_ref",
        "economic_score",
        "declared_decision_score",
        "observed_alternative_ref",
        "alternative_decision_event",
        "counterfactual_assumptions",
        "counterfactual_admissibility_claim",
        "later_economic_path",
        "later_favorable_price_move",
        "confidence",
    }
)


def validate_evaluation_observation_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "evaluation_observation")
    reject_unknown_fields(raw, EVALUATION_OBSERVATION_ALLOWED_FIELDS)
    schema_name = raw.get("schema_name", EVALUATION_OBSERVATION_SCHEMA_NAME)
    schema_version = raw.get("schema_version", EVALUATION_OBSERVATION_SCHEMA_VERSION)
    if schema_name != EVALUATION_OBSERVATION_SCHEMA_NAME:
        raise DdoValidationError(f"SCHEMA_NAME_MISMATCH:{schema_name!r}")
    if schema_version != EVALUATION_OBSERVATION_SCHEMA_VERSION:
        raise DdoValidationError(f"UNSUPPORTED_SCHEMA_VERSION:{schema_name}:{schema_version!r}")
    later = raw.get("later_economic_path")
    if later is not None and not isinstance(later, Mapping):
        raise DdoValidationError("LATER_ECONOMIC_PATH_MUST_BE_OBJECT")
    assert_no_hindsight_safety_relabel_v0(raw)
    claim = raw.get("counterfactual_admissibility_claim")
    alternative_event = raw.get("alternative_decision_event")
    if alternative_event is not None and not isinstance(alternative_event, Mapping):
        raise DdoValidationError("ALTERNATIVE_DECISION_EVENT_MUST_BE_OBJECT")
    later_move = raw.get("later_favorable_price_move")
    if later_move is not None and later_move not in (True, False):
        raise DdoValidationError("LATER_FAVORABLE_PRICE_MOVE_MUST_BE_BOOL")
    canonical = {
        "schema_name": EVALUATION_OBSERVATION_SCHEMA_NAME,
        "schema_version": EVALUATION_OBSERVATION_SCHEMA_VERSION,
        "decision_event_ref": require_record_id(
            raw.get("decision_event_ref"), "decision_event_ref"
        ),
        "incident_record_ref": None
        if raw.get("incident_record_ref") is None
        else require_record_id(raw.get("incident_record_ref"), "incident_record_ref"),
        "evaluation_horizon": require_enum(
            raw.get("evaluation_horizon"), "evaluation_horizon", EVALUATION_HORIZON_V0
        ),
        "evaluation_time_utc": require_event_time_utc(
            raw.get("evaluation_time_utc"), "evaluation_time_utc"
        ),
        "evaluation_time_information_set_ref": optional_ref(
            raw.get("evaluation_time_information_set_ref"),
            "evaluation_time_information_set_ref",
        ),
        "protected_condition": optional_enum(
            raw.get("protected_condition"), "protected_condition", PROTECTED_CONDITION_V0
        ),
        "kill_switch_timing_label": optional_enum(
            raw.get("kill_switch_timing_label"),
            "kill_switch_timing_label",
            KILL_SWITCH_TIMING_LABEL_V0,
        ),
        "stale_root_cause": optional_enum(
            raw.get("stale_root_cause"), "stale_root_cause", STALE_ROOT_CAUSE_V0
        ),
        "root_cause": optional_enum(raw.get("root_cause"), "root_cause", OUTCOME_ROOT_CAUSE_V0),
        "actual_outcome_ref": optional_ref(raw.get("actual_outcome_ref"), "actual_outcome_ref"),
        "economic_score": optional_string_or_unknown(raw.get("economic_score"), "economic_score"),
        "declared_decision_score": optional_enum(
            raw.get("declared_decision_score"), "declared_decision_score", DECISION_SCORE_V0
        ),
        "observed_alternative_ref": optional_ref(
            raw.get("observed_alternative_ref"), "observed_alternative_ref"
        ),
        "alternative_decision_event": (
            None if alternative_event is None else dict(alternative_event)
        ),
        "counterfactual_assumptions": optional_string_or_unknown(
            raw.get("counterfactual_assumptions"), "counterfactual_assumptions"
        ),
        "counterfactual_admissibility_claim": None
        if claim is None
        else require_enum(
            claim, "counterfactual_admissibility_claim", COUNTERFACTUAL_ADMISSIBILITY_V0
        ),
        "later_economic_path": None if later is None else dict(later),
        "later_favorable_price_move": later_move,
        "confidence": optional_string_or_unknown(raw.get("confidence"), "confidence"),
    }
    return freeze_record(canonical)
