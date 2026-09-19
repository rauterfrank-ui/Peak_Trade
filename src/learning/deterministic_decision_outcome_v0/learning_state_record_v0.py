"""Learning state record v0 — append-only non-authorizing learning state snapshots.

Holds provenance-bound evidence lineage and opaque observation tokens only.
Does not confer trading, promotion, drift-monitor, or calibration authority.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_LEARNING_STATE_RECORD,
    SCHEMA_VERSION_LEARNING_STATE_RECORD_V0,
    SHARED_IDENTITY_FIELD_SPECS_V0,
    FieldSpecV0,
    finalize_record_v0,
    optional_ref,
    optional_string_or_unknown,
    parse_shared_envelope_v0,
    reject_unknown_fields,
    require_event_time_utc,
    require_mapping,
    require_non_empty_string_or_unknown,
    require_record_id,
    require_sha256_or_unknown,
    optional_record_id,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError

LEARNING_STATE_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"

_STATE_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0(
        "state_scope_id",
        "REQUIRED",
        "string",
        True,
        "Stable scope for replay/restart reconstruction within one durable ledger.",
    ),
    FieldSpecV0(
        "state_version",
        "REQUIRED",
        "positive_int",
        True,
        "Monotonic version within state_scope_id. +1 per non-idempotent ingest.",
    ),
    FieldSpecV0(
        "prior_state_record_ref",
        "OPTIONAL",
        "record_id|null",
        True,
        "Immediate predecessor learning_state_record in scope chain.",
    ),
    FieldSpecV0(
        "evaluation_bundle_fingerprint",
        "REQUIRED",
        "sha256",
        True,
        "Deterministic fingerprint of outcome+attribution+counterfactual content hashes.",
    ),
    FieldSpecV0("outcome_record_ref", "REQUIRED", "record_id", True, "Ingested outcome lineage."),
    FieldSpecV0(
        "attribution_record_ref", "REQUIRED", "record_id", True, "Ingested attribution lineage."
    ),
    FieldSpecV0(
        "counterfactual_record_ref",
        "REQUIRED",
        "record_id",
        True,
        "Ingested counterfactual lineage.",
    ),
    FieldSpecV0(
        "decision_event_ref",
        "REQUIRED",
        "record_id",
        True,
        "DecisionEvent ref copied from outcome record.",
    ),
    FieldSpecV0(
        "last_event_time_utc",
        "REQUIRED",
        "utc_timestamp",
        True,
        "Outcome record event time; ordering anchor for fail-closed ingest.",
    ),
    FieldSpecV0(
        "ingest_sequence",
        "REQUIRED",
        "positive_int",
        True,
        "Count of successful non-idempotent ingests in scope (includes this transition).",
    ),
    FieldSpecV0(
        "next_cycle_economic_score_label",
        "REQUIRED",
        "string",
        True,
        "Opaque token forwarded to next-cycle evaluation label seam only.",
    ),
    FieldSpecV0(
        "last_evaluation_horizon",
        "REQUIRED",
        "string",
        True,
        "Observation-only copy of outcome evaluation_horizon token.",
    ),
    FieldSpecV0(
        "last_actual_outcome_ref",
        "REQUIRED",
        "ref",
        True,
        "Observation-only opaque measurement ref copy.",
    ),
    FieldSpecV0(
        "last_decision_score",
        "OPTIONAL",
        "string|null",
        True,
        "Observation-only opaque token. Not model calibration.",
    ),
    FieldSpecV0(
        "last_safety_score",
        "OPTIONAL",
        "string|null",
        True,
        "Observation-only opaque token. Not safety authority.",
    ),
    FieldSpecV0(
        "last_economic_score",
        "OPTIONAL",
        "string|null",
        True,
        "Observation-only opaque token from outcome. Not numeric calibration.",
    ),
    FieldSpecV0("productive_authority", "REQUIRED", "string", True, "Must be NONE."),
    FieldSpecV0("runtime_reachability", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_auto_promote", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_core", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_risk", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_safety", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_deploy", "REQUIRED", "bool", True, "Must be false."),
)

LEARNING_STATE_RECORD_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _STATE_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
LEARNING_STATE_RECORD_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in LEARNING_STATE_RECORD_FIELD_SPECS_V0
)


def _require_false_authority(raw: Mapping[str, Any]) -> dict[str, bool | str]:
    if raw.get("productive_authority") != "NONE":
        raise DdoValidationError("LEARNING_STATE_PRODUCTIVE_AUTHORITY_MUST_BE_NONE")
    for flag in (
        "runtime_reachability",
        "can_auto_promote",
        "can_mutate_core",
        "can_mutate_risk",
        "can_mutate_safety",
        "can_deploy",
    ):
        if raw.get(flag) is not False:
            raise DdoValidationError(f"LEARNING_STATE_{flag.upper()}_MUST_BE_FALSE")
    return {
        "productive_authority": "NONE",
        "runtime_reachability": False,
        "can_auto_promote": False,
        "can_mutate_core": False,
        "can_mutate_risk": False,
        "can_mutate_safety": False,
        "can_deploy": False,
    }


def require_positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DdoValidationError(f"INVALID_POSITIVE_INT:{field}")
    if value <= 0:
        raise DdoValidationError(f"POSITIVE_INT_REQUIRED:{field}")
    return value


def build_learning_state_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "learning_state_record")
    reject_unknown_fields(raw, LEARNING_STATE_RECORD_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_LEARNING_STATE_RECORD,
        schema_version=SCHEMA_VERSION_LEARNING_STATE_RECORD_V0,
    )
    canonical: dict[str, Any] = {
        **envelope,
        "state_scope_id": require_non_empty_string_or_unknown(
            raw.get("state_scope_id"), "state_scope_id"
        ),
        "state_version": require_positive_int(raw.get("state_version"), "state_version"),
        "prior_state_record_ref": optional_record_id(
            raw.get("prior_state_record_ref"), "prior_state_record_ref"
        ),
        "evaluation_bundle_fingerprint": require_sha256_or_unknown(
            raw.get("evaluation_bundle_fingerprint"), "evaluation_bundle_fingerprint"
        ),
        "outcome_record_ref": require_record_id(
            raw.get("outcome_record_ref"), "outcome_record_ref"
        ),
        "attribution_record_ref": require_record_id(
            raw.get("attribution_record_ref"), "attribution_record_ref"
        ),
        "counterfactual_record_ref": require_record_id(
            raw.get("counterfactual_record_ref"), "counterfactual_record_ref"
        ),
        "decision_event_ref": require_record_id(
            raw.get("decision_event_ref"), "decision_event_ref"
        ),
        "last_event_time_utc": require_event_time_utc(
            raw.get("last_event_time_utc"), "last_event_time_utc"
        ),
        "ingest_sequence": require_positive_int(raw.get("ingest_sequence"), "ingest_sequence"),
        "next_cycle_economic_score_label": require_non_empty_string_or_unknown(
            raw.get("next_cycle_economic_score_label"), "next_cycle_economic_score_label"
        ),
        "last_evaluation_horizon": require_non_empty_string_or_unknown(
            raw.get("last_evaluation_horizon"), "last_evaluation_horizon"
        ),
        "last_actual_outcome_ref": optional_ref(
            raw.get("last_actual_outcome_ref"), "last_actual_outcome_ref"
        )
        or UNKNOWN,
        "last_decision_score": optional_string_or_unknown(
            raw.get("last_decision_score"), "last_decision_score"
        ),
        "last_safety_score": optional_string_or_unknown(
            raw.get("last_safety_score"), "last_safety_score"
        ),
        "last_economic_score": optional_string_or_unknown(
            raw.get("last_economic_score"), "last_economic_score"
        ),
        **_require_false_authority(raw),
    }
    if canonical["evaluation_bundle_fingerprint"] == UNKNOWN:
        raise DdoValidationError("LEARNING_STATE_FINGERPRINT_UNKNOWN_FORBIDDEN")
    return finalize_record_v0(canonical, raw)


def validate_learning_state_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_learning_state_record_v0(payload)
