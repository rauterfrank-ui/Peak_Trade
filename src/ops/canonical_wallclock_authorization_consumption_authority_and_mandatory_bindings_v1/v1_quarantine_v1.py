"""Quarantine productive AuthorizationArtifactV1 consumption authority."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.constants_v1 import (
    AUTHORIZATION_SCHEMA,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.legacy_formal_authorization_v1 import (
    classify_legacy_formal_authorization_v1,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
    AUTHORIZATION_ARTIFACT_V1_CLASSIFICATION,
    AUTHORIZATION_SCHEMA_REJECTED_LEGACY,
)


def is_authorization_artifact_v1_payload(raw: Mapping[str, Any]) -> bool:
    """Detect paper-shadow AuthorizationArtifactV1 productive schema (no v2 schema field)."""
    if raw.get("schema") == AUTHORIZATION_SCHEMA:
        return False
    # V1 shape: schema_version + capability_id + arming_state + consumed bool, no schema=v2.
    markers = (
        "arming_state" in raw
        and "capability_id" in raw
        and "schema_version" in raw
        and "authorization_id" in raw
        and "consumed" in raw
        and "schema" not in raw
    )
    return bool(markers)


def classify_authorization_schema_for_wallclock_v1(
    raw: Mapping[str, Any],
) -> tuple[str, list[str]]:
    """Return (kind, blockers). kind in {v2, legacy_formal, legacy_v1, unknown}."""
    if raw.get("schema") == AUTHORIZATION_SCHEMA:
        return "v2", []
    if is_authorization_artifact_v1_payload(raw):
        return "legacy_v1", [AUTHORIZATION_SCHEMA_REJECTED_LEGACY]
    legacy = classify_legacy_formal_authorization_v1(raw)
    if legacy.classification == "LEGACY_FORMAL_AUTHORIZATION_V1" or legacy.ok:
        return "legacy_formal", [AUTHORIZATION_SCHEMA_REJECTED_LEGACY]
    return "unknown", [AUTHORIZATION_SCHEMA_REJECTED_LEGACY]


def quarantine_authorization_artifact_v1_result(
    *,
    notes: Optional[list[str]] = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "blockers": [AUTHORIZATION_SCHEMA_REJECTED_LEGACY],
        "classification": AUTHORIZATION_ARTIFACT_V1_CLASSIFICATION,
        "consumable": False,
        "session_start_reachable": False,
        "legacy_to_v2_silent_conversion": False,
        "legacy_compatibility_fallback": False,
        "transport_open_allowed": False,
        "session_started": False,
        "notes": list(notes or [])
        + [
            AUTHORIZATION_ARTIFACT_V1_CLASSIFICATION,
            "NO_TOKEN_IN_ERROR",
            "NO_ARTIFACT_DUMP",
        ],
    }
