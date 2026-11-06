"""Versioned control-state record classes.

Implemented core: B/C/D plus shared identity primitives.
Future-only: E/F/G. Observation-only evidence (A) is the DDO owner and is
rejected here.
"""

from __future__ import annotations

from typing import Any, Final, Mapping

from src.learning.mutation_critical_control_state_storage_v1.errors_v1 import (
    ControlStateFutureOnlyError,
    ControlStateValidationError,
    ControlStateWrongOwnerError,
)
from src.learning.mutation_critical_control_state_storage_v1.serialization_v1 import (
    canonicalize_json_value,
    compute_content_hash_v1,
)

SCHEMA_NAME: Final[str] = "mutation_critical_control_state_record_v1"
SCHEMA_VERSION: Final[str] = "v1"

STATE_CLASS_A_OBSERVATION_ONLY_EVIDENCE: Final[str] = "A_OBSERVATION_ONLY_EVIDENCE"
STATE_CLASS_B_SUPERVISOR_CONTROL_STATE: Final[str] = "B_SUPERVISOR_CONTROL_STATE"
STATE_CLASS_C_EXECUTION_ACTION_IDENTITY: Final[str] = "C_EXECUTION_ACTION_IDENTITY"
STATE_CLASS_D_AMBIGUOUS_MUTATION_OBLIGATION: Final[str] = "D_AMBIGUOUS_MUTATION_OBLIGATION"
STATE_CLASS_E_RECONCILIATION_OBLIGATION: Final[str] = "E_RECONCILIATION_OBLIGATION"
STATE_CLASS_F_ACTIVE_ARTIFACT_IDENTITY_FUTURE_ONLY: Final[str] = (
    "F_ACTIVE_ARTIFACT_IDENTITY_FUTURE_ONLY"
)
STATE_CLASS_G_ROLLBACK_KNOWN_GOOD_IDENTITY_FUTURE_ONLY: Final[str] = (
    "G_ROLLBACK_KNOWN_GOOD_IDENTITY_FUTURE_ONLY"
)

IMPLEMENTED_STATE_CLASSES: Final[frozenset[str]] = frozenset(
    {
        STATE_CLASS_B_SUPERVISOR_CONTROL_STATE,
        STATE_CLASS_C_EXECUTION_ACTION_IDENTITY,
        STATE_CLASS_D_AMBIGUOUS_MUTATION_OBLIGATION,
    }
)
FUTURE_ONLY_STATE_CLASSES: Final[frozenset[str]] = frozenset(
    {
        STATE_CLASS_E_RECONCILIATION_OBLIGATION,
        STATE_CLASS_F_ACTIVE_ARTIFACT_IDENTITY_FUTURE_ONLY,
        STATE_CLASS_G_ROLLBACK_KNOWN_GOOD_IDENTITY_FUTURE_ONLY,
    }
)
AMBIGUOUS_MUTATION_CLASSES: Final[frozenset[str]] = frozenset(
    {STATE_CLASS_D_AMBIGUOUS_MUTATION_OBLIGATION}
)

REQUIRED_RECORD_FIELDS: Final[tuple[str, ...]] = (
    "schema_name",
    "schema_version",
    "record_id",
    "state_class",
    "payload",
)


def _require_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ControlStateValidationError(f"RECORD_ID_REQUIRED:{field}")
    if value != value.strip():
        raise ControlStateValidationError(f"RECORD_ID_PADDED:{field}")
    return value


def validate_control_state_record_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    canonical = canonicalize_json_value(record)
    if not isinstance(canonical, dict):
        raise ControlStateValidationError("RECORD_MUST_BE_OBJECT")
    for field in REQUIRED_RECORD_FIELDS:
        if field not in canonical:
            raise ControlStateValidationError(f"RECORD_FIELD_REQUIRED:{field}")
    if canonical["schema_name"] != SCHEMA_NAME:
        raise ControlStateValidationError("SCHEMA_NAME_MISMATCH")
    if canonical["schema_version"] != SCHEMA_VERSION:
        raise ControlStateValidationError("SCHEMA_VERSION_MISMATCH")
    record_id = _require_id(canonical["record_id"], "record_id")
    state_class = canonical["state_class"]
    if state_class == STATE_CLASS_A_OBSERVATION_ONLY_EVIDENCE:
        raise ControlStateWrongOwnerError("A_OBSERVATION_ONLY_EVIDENCE_BELONGS_TO_DDO_OWNER")
    if state_class in FUTURE_ONLY_STATE_CLASSES:
        raise ControlStateFutureOnlyError(f"FUTURE_ONLY_STATE_CLASS:{state_class}")
    if state_class not in IMPLEMENTED_STATE_CLASSES:
        raise ControlStateValidationError(f"UNKNOWN_STATE_CLASS:{state_class}")
    payload = canonical["payload"]
    if not isinstance(payload, dict):
        raise ControlStateValidationError("PAYLOAD_MUST_BE_OBJECT")
    depends_on = canonical.get("depends_on_record_id")
    if depends_on is not None:
        depends_on = _require_id(depends_on, "depends_on_record_id")
    correlation_id = canonical.get("correlation_id")
    if correlation_id is not None:
        correlation_id = _require_id(correlation_id, "correlation_id")
    normalized = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "record_id": record_id,
        "state_class": state_class,
        "payload": payload,
        "depends_on_record_id": depends_on,
        "correlation_id": correlation_id,
    }
    content_hash = compute_content_hash_v1(normalized)
    supplied = canonical.get("content_hash")
    if supplied is not None and supplied != content_hash:
        raise ControlStateValidationError("CONTENT_HASH_MISMATCH")
    normalized["content_hash"] = content_hash
    return normalized
