"""Fail-closed mandatory identity/safety bindings for authorization_artifact_v2."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
    AUTHORIZED_NETWORK_SCOPE,
    AUTHORIZED_VENUE,
    EFFECTIVE_SESSION_CONFIG_DIGEST_KEY,
    MANDATORY_SAFETY_BOUNDARIES,
    NETWORK_SCOPE_FIELD,
    REQUIRED_SESSION_DURATION_SECONDS,
    VENUE_FIELD,
)


class MandatoryBindingError(ValueError):
    """Fail-closed mandatory binding error."""


def _reject_non_bool(value: object, *, field: str) -> bool:
    if value is None:
        raise MandatoryBindingError(f"MANDATORY_BOOL_NULL:{field}")
    if type(value) is not bool:
        raise MandatoryBindingError(f"MANDATORY_BOOL_TYPE:{field}")
    return value


def validate_mandatory_safety_boundaries_v1(safety: Mapping[str, Any]) -> dict[str, bool]:
    if not isinstance(safety, dict):
        raise MandatoryBindingError("SAFETY_BOUNDARIES_NOT_OBJECT")
    if not safety:
        raise MandatoryBindingError("SAFETY_BOUNDARIES_EMPTY")
    missing = sorted(set(MANDATORY_SAFETY_BOUNDARIES) - set(safety))
    if missing:
        raise MandatoryBindingError("SAFETY_FIELD_MISSING:" + ",".join(missing))
    out: dict[str, bool] = {}
    for key, expected in MANDATORY_SAFETY_BOUNDARIES.items():
        actual = _reject_non_bool(safety[key], field=key)
        if actual is not expected:
            raise MandatoryBindingError(f"SAFETY_VALUE_REJECTED:{key}")
        out[key] = actual
    # Additional keys must be strict bools (no coercion).
    for key, value in safety.items():
        if key in MANDATORY_SAFETY_BOUNDARIES:
            continue
        out[str(key)] = _reject_non_bool(value, field=str(key))
    return out


def validate_mandatory_top_level_safety_flags_v1(raw: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    for field, expected in (
        ("forced_wiring_fixture_mode", False),
        ("no_implicit_resume", True),
    ):
        if field not in raw:
            blockers.append(f"AUTH_FIELD_MISSING:{field}")
            continue
        value = raw[field]
        if value is None:
            blockers.append(f"MANDATORY_BOOL_NULL:{field}")
            continue
        if type(value) is not bool:
            blockers.append(f"MANDATORY_BOOL_TYPE:{field}")
            continue
        if value is not expected:
            blockers.append(f"SAFETY_VALUE_REJECTED:{field}")
    return blockers


def validate_mandatory_session_duration_v1(duration: object) -> int:
    if type(duration) is not int:
        raise MandatoryBindingError("SESSION_DURATION_TYPE")
    if duration != REQUIRED_SESSION_DURATION_SECONDS:
        raise MandatoryBindingError("SESSION_DURATION_REJECTED")
    return duration


def validate_mandatory_session_config_digest_binding_v1(
    *,
    session_config_digest: object,
    config_digests: Mapping[str, Any],
) -> str:
    if session_config_digest is None or session_config_digest == "":
        raise MandatoryBindingError("SESSION_CONFIG_DIGEST_MISSING")
    if not isinstance(session_config_digest, str) or len(session_config_digest) != 64:
        raise MandatoryBindingError("SESSION_CONFIG_DIGEST_INVALID")
    if not isinstance(config_digests, dict) or not config_digests:
        raise MandatoryBindingError("CONFIG_DIGESTS_INCOMPLETE")
    if EFFECTIVE_SESSION_CONFIG_DIGEST_KEY not in config_digests:
        raise MandatoryBindingError("EFFECTIVE_SESSION_CONFIG_DIGEST_KEY_MISSING")
    embedded = config_digests[EFFECTIVE_SESSION_CONFIG_DIGEST_KEY]
    if not isinstance(embedded, str) or len(embedded) != 64:
        raise MandatoryBindingError("EFFECTIVE_SESSION_CONFIG_DIGEST_INVALID")
    if embedded != session_config_digest:
        raise MandatoryBindingError("SESSION_CONFIG_DIGEST_MISMATCH_INTERNAL")
    for key, value in config_digests.items():
        if not isinstance(key, str) or not isinstance(value, str) or len(value) != 64:
            raise MandatoryBindingError("CONFIG_DIGESTS_INVALID")
    return session_config_digest


def validate_expires_at_present_v1(raw: Mapping[str, Any]) -> float:
    if "expires_at" not in raw:
        raise MandatoryBindingError("AUTH_FIELD_MISSING:expires_at")
    value = raw["expires_at"]
    if value is None:
        raise MandatoryBindingError("EXPIRES_AT_NULL")
    if type(value) not in (int, float):
        raise MandatoryBindingError("EXPIRES_AT_TYPE")
    return float(value)


def validate_mandatory_venue_v1(venue: object) -> str:
    """Fail-closed venue binding. No default, no coercion, no case/whitespace normalize."""
    if venue is None:
        raise MandatoryBindingError("VENUE_MISSING")
    if type(venue) is not str:
        raise MandatoryBindingError("VENUE_TYPE")
    if venue == "":
        raise MandatoryBindingError("VENUE_EMPTY")
    if venue != AUTHORIZED_VENUE:
        raise MandatoryBindingError(f"VENUE_REJECTED:{venue}")
    return venue


def validate_mandatory_network_scope_v1(network_scope: object) -> str:
    if network_scope is None:
        raise MandatoryBindingError("NETWORK_SCOPE_MISSING")
    if type(network_scope) is not str:
        raise MandatoryBindingError("NETWORK_SCOPE_TYPE")
    if network_scope == "":
        raise MandatoryBindingError("NETWORK_SCOPE_EMPTY")
    if network_scope != AUTHORIZED_NETWORK_SCOPE:
        raise MandatoryBindingError(f"NETWORK_SCOPE_REJECTED:{network_scope}")
    return network_scope


def validate_mandatory_venue_and_network_scope_fields_v1(
    raw: Mapping[str, Any],
) -> tuple[str, str]:
    if VENUE_FIELD not in raw:
        raise MandatoryBindingError(f"AUTH_FIELD_MISSING:{VENUE_FIELD}")
    if NETWORK_SCOPE_FIELD not in raw:
        raise MandatoryBindingError(f"AUTH_FIELD_MISSING:{NETWORK_SCOPE_FIELD}")
    return (
        validate_mandatory_venue_v1(raw[VENUE_FIELD]),
        validate_mandatory_network_scope_v1(raw[NETWORK_SCOPE_FIELD]),
    )
