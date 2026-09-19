"""Learning evidence record v1 — offline export from non-authorizing learning state.

Projects validated learning_state_record_v0 into an optimization-consumable
evidence shape. Opaque tokens only; no numeric calibration, regime inference,
or trading/promotion authority.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_LEARNING_EVIDENCE_RECORD,
    SCHEMA_VERSION_LEARNING_EVIDENCE_RECORD_V1,
    SHARED_IDENTITY_FIELD_SPECS_V0,
    FieldSpecV0,
    finalize_record_v0,
    optional_string_or_unknown,
    parse_shared_envelope_v0,
    reject_unknown_fields,
    require_event_time_utc,
    require_mapping,
    require_non_empty_string_or_unknown,
    require_record_id,
    require_sha256_or_unknown,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.learning_state_record_v0 import (
    require_positive_int as require_state_positive_int,
)

UNIVERSE_CLASS_SELF_LEARNING: Final[str] = "SELF_LEARNING_UNIVERSE"
EVIDENCE_CLASS_LEARNING: Final[str] = "LEARNING_EVIDENCE"
LEARNING_EVIDENCE_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"

_EVIDENCE_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0(
        "source_learning_state_record_ref",
        "REQUIRED",
        "record_id",
        True,
        "Lineage anchor to exported learning_state_record.",
    ),
    FieldSpecV0("state_scope_id", "REQUIRED", "string", True, "Copied from source state scope."),
    FieldSpecV0(
        "state_version",
        "REQUIRED",
        "positive_int",
        True,
        "Copied from source state version at export time.",
    ),
    FieldSpecV0(
        "evaluation_bundle_fingerprint",
        "REQUIRED",
        "sha256",
        True,
        "Copied bundle fingerprint for reproducibility.",
    ),
    FieldSpecV0(
        "decision_event_ref",
        "REQUIRED",
        "record_id",
        True,
        "Decision lineage copied from learning state.",
    ),
    FieldSpecV0(
        "observed_at_utc",
        "REQUIRED",
        "utc_timestamp",
        True,
        "Source last_event_time_utc (outcome ordering anchor).",
    ),
    FieldSpecV0(
        "economic_score_label",
        "REQUIRED",
        "string",
        True,
        "Opaque label token; not numeric score.",
    ),
    FieldSpecV0(
        "evaluation_horizon",
        "REQUIRED",
        "string",
        True,
        "Opaque horizon token copy.",
    ),
    FieldSpecV0(
        "actual_outcome_ref",
        "REQUIRED",
        "ref",
        True,
        "Opaque measurement ref copy.",
    ),
    FieldSpecV0(
        "decision_score_label",
        "OPTIONAL",
        "string|null",
        True,
        "Opaque token copy; not model quality authority.",
    ),
    FieldSpecV0(
        "safety_score_label",
        "OPTIONAL",
        "string|null",
        True,
        "Opaque token copy; not safety authority.",
    ),
    FieldSpecV0(
        "universe_class",
        "REQUIRED",
        "string",
        True,
        "Must be SELF_LEARNING_UNIVERSE.",
    ),
    FieldSpecV0(
        "evidence_class",
        "REQUIRED",
        "string",
        True,
        "Must be LEARNING_EVIDENCE.",
    ),
    FieldSpecV0("productive_authority", "REQUIRED", "string", True, "Must be NONE."),
    FieldSpecV0("runtime_reachability", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_auto_promote", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_core", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_risk", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_safety", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_deploy", "REQUIRED", "bool", True, "Must be false."),
)

LEARNING_EVIDENCE_RECORD_FIELD_SPECS_V1: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _EVIDENCE_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
LEARNING_EVIDENCE_RECORD_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in LEARNING_EVIDENCE_RECORD_FIELD_SPECS_V1
)


def _require_false_authority(raw: Mapping[str, Any]) -> dict[str, bool | str]:
    if raw.get("productive_authority") != "NONE":
        raise DdoValidationError("LEARNING_EVIDENCE_PRODUCTIVE_AUTHORITY_MUST_BE_NONE")
    if raw.get("universe_class") != UNIVERSE_CLASS_SELF_LEARNING:
        raise DdoValidationError("LEARNING_EVIDENCE_UNIVERSE_CLASS_INVALID")
    if raw.get("evidence_class") != EVIDENCE_CLASS_LEARNING:
        raise DdoValidationError("LEARNING_EVIDENCE_CLASS_INVALID")
    for flag in (
        "runtime_reachability",
        "can_auto_promote",
        "can_mutate_core",
        "can_mutate_risk",
        "can_mutate_safety",
        "can_deploy",
    ):
        if raw.get(flag) is not False:
            raise DdoValidationError(f"LEARNING_EVIDENCE_{flag.upper()}_MUST_BE_FALSE")
    return {
        "productive_authority": "NONE",
        "runtime_reachability": False,
        "can_auto_promote": False,
        "can_mutate_core": False,
        "can_mutate_risk": False,
        "can_mutate_safety": False,
        "can_deploy": False,
        "universe_class": UNIVERSE_CLASS_SELF_LEARNING,
        "evidence_class": EVIDENCE_CLASS_LEARNING,
    }


def build_learning_evidence_record_v1(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "learning_evidence_record")
    reject_unknown_fields(raw, LEARNING_EVIDENCE_RECORD_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_LEARNING_EVIDENCE_RECORD,
        schema_version=SCHEMA_VERSION_LEARNING_EVIDENCE_RECORD_V1,
    )
    canonical: dict[str, Any] = {
        **envelope,
        "source_learning_state_record_ref": require_record_id(
            raw.get("source_learning_state_record_ref"),
            "source_learning_state_record_ref",
        ),
        "state_scope_id": require_non_empty_string_or_unknown(
            raw.get("state_scope_id"), "state_scope_id"
        ),
        "state_version": require_state_positive_int(raw.get("state_version"), "state_version"),
        "evaluation_bundle_fingerprint": require_sha256_or_unknown(
            raw.get("evaluation_bundle_fingerprint"), "evaluation_bundle_fingerprint"
        ),
        "decision_event_ref": require_record_id(
            raw.get("decision_event_ref"), "decision_event_ref"
        ),
        "observed_at_utc": require_event_time_utc(raw.get("observed_at_utc"), "observed_at_utc"),
        "economic_score_label": require_non_empty_string_or_unknown(
            raw.get("economic_score_label"), "economic_score_label"
        ),
        "evaluation_horizon": require_non_empty_string_or_unknown(
            raw.get("evaluation_horizon"), "evaluation_horizon"
        ),
        "actual_outcome_ref": require_non_empty_string_or_unknown(
            raw.get("actual_outcome_ref"), "actual_outcome_ref"
        ),
        "decision_score_label": optional_string_or_unknown(
            raw.get("decision_score_label"), "decision_score_label"
        ),
        "safety_score_label": optional_string_or_unknown(
            raw.get("safety_score_label"), "safety_score_label"
        ),
        **_require_false_authority(raw),
    }
    if canonical["evaluation_bundle_fingerprint"] == UNKNOWN:
        raise DdoValidationError("LEARNING_EVIDENCE_FINGERPRINT_UNKNOWN_FORBIDDEN")
    return finalize_record_v0(canonical, raw)


def validate_learning_evidence_record_v1(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_learning_evidence_record_v1(payload)
