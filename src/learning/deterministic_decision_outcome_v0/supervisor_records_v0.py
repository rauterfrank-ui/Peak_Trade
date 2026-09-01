"""AutonomyCycleRecord and HealthSnapshot schemas v0.

Offline supervisor evidence only. No runtime reachability. No execution
permission grant. HealthSnapshot is an input snapshot, not a permit.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_AUTONOMY_CYCLE,
    SCHEMA_NAME_HEALTH_SNAPSHOT,
    SCHEMA_VERSION_AUTONOMY_CYCLE_V0,
    SCHEMA_VERSION_HEALTH_SNAPSHOT_V0,
    SHARED_IDENTITY_FIELD_SPECS_V0,
    FieldSpecV0,
    finalize_record_v0,
    optional_ref,
    optional_string_or_unknown,
    parse_shared_envelope_v0,
    reject_unknown_fields,
    require_enum,
    require_mapping,
    require_non_empty_string_or_unknown,
    require_record_id,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    SUPERVISOR_ACTION_V0,
    SUPERVISOR_EVENT_V0,
    SUPERVISOR_OUTCOME_V0,
    SUPERVISOR_STATE_V0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.reason_codes_v0 import validate_reason_codes_v0

_CYCLE_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("from_state", "REQUIRED", "enum:SUPERVISOR_STATE_V0", True, "Prior durable state."),
    FieldSpecV0("to_state", "REQUIRED", "enum:SUPERVISOR_STATE_V0", True, "Next durable state."),
    FieldSpecV0("event", "REQUIRED", "enum:SUPERVISOR_EVENT_V0", True, "Transition event."),
    FieldSpecV0(
        "outcome", "REQUIRED", "enum:SUPERVISOR_OUTCOME_V0", True, "Control-plane outcome."
    ),
    FieldSpecV0("actions", "REQUIRED", "enum[]", True, "Explicit actions. Empty list valid."),
    FieldSpecV0(
        "reason_codes", "REQUIRED", "coded_ref[]", True, "Namespaced reason codes. Empty valid."
    ),
    FieldSpecV0(
        "health_snapshot_ref", "OPTIONAL", "record_id|null", True, "Health snapshot identity."
    ),
    FieldSpecV0(
        "authority_snapshot_ref",
        "OPTIONAL",
        "ref|null",
        True,
        "Opaque authority snapshot identity. Not a grant.",
    ),
    FieldSpecV0(
        "rejected_transition",
        "REQUIRED",
        "bool",
        True,
        "True when the attempted transition was recorded and refused.",
    ),
    FieldSpecV0(
        "execution_reachable",
        "REQUIRED",
        "bool",
        True,
        "Must be false in this offline package.",
    ),
)

_HEALTH_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0(
        "freshness_readiness",
        "REQUIRED",
        "string",
        True,
        "Opaque freshness input. UNKNOWN admissible. Not a permit.",
    ),
    FieldSpecV0(
        "dependency_readiness",
        "REQUIRED",
        "string",
        True,
        "Opaque dependency input. UNKNOWN admissible.",
    ),
    FieldSpecV0(
        "venue_account_readiness",
        "REQUIRED",
        "string",
        True,
        "Opaque venue/account input. UNKNOWN admissible.",
    ),
    FieldSpecV0(
        "permission_readiness",
        "REQUIRED",
        "string",
        True,
        "Readiness input only. Not an execution permit.",
    ),
    FieldSpecV0(
        "safety_readiness",
        "REQUIRED",
        "string",
        True,
        "Opaque safety readiness input. UNKNOWN admissible.",
    ),
    FieldSpecV0(
        "clock_trust",
        "REQUIRED",
        "string",
        True,
        "Clock/NTP trust input. UNKNOWN admissible.",
    ),
    FieldSpecV0(
        "ledger_integrity",
        "REQUIRED",
        "string",
        True,
        "Ledger integrity input. UNKNOWN admissible.",
    ),
    FieldSpecV0(
        "execution_permit",
        "REQUIRED",
        "bool",
        True,
        "Must be false. HealthSnapshot cannot grant execution.",
    ),
)

AUTONOMY_CYCLE_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _CYCLE_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
HEALTH_SNAPSHOT_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _HEALTH_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
AUTONOMY_CYCLE_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in AUTONOMY_CYCLE_FIELD_SPECS_V0
)
HEALTH_SNAPSHOT_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in HEALTH_SNAPSHOT_FIELD_SPECS_V0
)


def _action_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise DdoValidationError("ACTIONS_MUST_BE_LIST")
    return [require_enum(item, "actions", SUPERVISOR_ACTION_V0) for item in value]


def build_autonomy_cycle_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "autonomy_cycle_record")
    reject_unknown_fields(raw, AUTONOMY_CYCLE_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_AUTONOMY_CYCLE,
        schema_version=SCHEMA_VERSION_AUTONOMY_CYCLE_V0,
        cycle_id_required=True,
    )
    rejected = raw.get("rejected_transition")
    reachable = raw.get("execution_reachable")
    if not isinstance(rejected, bool):
        raise DdoValidationError("REJECTED_TRANSITION_MUST_BE_BOOL")
    if reachable is not False:
        raise DdoValidationError("AUTONOMY_SUPERVISOR_EXECUTION_UNREACHABLE")
    canonical = {
        **envelope,
        "from_state": require_enum(raw.get("from_state"), "from_state", SUPERVISOR_STATE_V0),
        "to_state": require_enum(raw.get("to_state"), "to_state", SUPERVISOR_STATE_V0),
        "event": require_enum(raw.get("event"), "event", SUPERVISOR_EVENT_V0),
        "outcome": require_enum(raw.get("outcome"), "outcome", SUPERVISOR_OUTCOME_V0),
        "actions": _action_list(raw.get("actions")),
        "reason_codes": validate_reason_codes_v0(raw.get("reason_codes")),
        "health_snapshot_ref": None
        if raw.get("health_snapshot_ref") is None
        else require_record_id(raw.get("health_snapshot_ref"), "health_snapshot_ref"),
        "authority_snapshot_ref": optional_ref(
            raw.get("authority_snapshot_ref"), "authority_snapshot_ref"
        ),
        "rejected_transition": rejected,
        "execution_reachable": False,
    }
    return finalize_record_v0(canonical, raw)


def validate_autonomy_cycle_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_autonomy_cycle_record_v0(payload)


def build_health_snapshot_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "health_snapshot")
    reject_unknown_fields(raw, HEALTH_SNAPSHOT_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_HEALTH_SNAPSHOT,
        schema_version=SCHEMA_VERSION_HEALTH_SNAPSHOT_V0,
    )
    if raw.get("execution_permit") is not False:
        raise DdoValidationError("HEALTH_SNAPSHOT_MUST_NOT_GRANT_EXECUTION")
    canonical = {
        **envelope,
        "freshness_readiness": require_non_empty_string_or_unknown(
            raw.get("freshness_readiness"), "freshness_readiness"
        ),
        "dependency_readiness": require_non_empty_string_or_unknown(
            raw.get("dependency_readiness"), "dependency_readiness"
        ),
        "venue_account_readiness": require_non_empty_string_or_unknown(
            raw.get("venue_account_readiness"), "venue_account_readiness"
        ),
        "permission_readiness": require_non_empty_string_or_unknown(
            raw.get("permission_readiness"), "permission_readiness"
        ),
        "safety_readiness": require_non_empty_string_or_unknown(
            raw.get("safety_readiness"), "safety_readiness"
        ),
        "clock_trust": require_non_empty_string_or_unknown(raw.get("clock_trust"), "clock_trust"),
        "ledger_integrity": require_non_empty_string_or_unknown(
            raw.get("ledger_integrity"), "ledger_integrity"
        ),
        "execution_permit": False,
    }
    return finalize_record_v0(canonical, raw)


def validate_health_snapshot_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_health_snapshot_v0(payload)
