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
