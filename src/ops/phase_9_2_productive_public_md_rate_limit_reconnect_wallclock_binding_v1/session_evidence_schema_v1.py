"""Step-4 session evidence schema for a later governed real Public-MD session.

This wiring capability materializes the schema/template only. It does not record
observed productive rate-limit/reconnect session outcomes.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    CONFIRMATION_SESSION_ID,
    SESSION_EVIDENCE_REQUIRED_FIELDS,
    SESSION_EVIDENCE_SCHEMA_VERSION,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
    sha256_canonical_v1,
)


def build_session_evidence_template_v1(
    *,
    repository_sha: str,
    config_digest: str,
    authorization_id_or_digest: str = "",
    session_id: str = TARGET_SESSION_ID,
    confirmation_session_id: str = CONFIRMATION_SESSION_ID,
) -> dict[str, Any]:
    """Return a complete schema-shaped template with non-observed defaults."""
    payload: dict[str, Any] = {
        "schema_version": SESSION_EVIDENCE_SCHEMA_VERSION,
        "repository_sha": repository_sha,
        "config_digest": config_digest,
        "authorization_id_or_digest": authorization_id_or_digest,
        "session_id": session_id,
        "runtime_session_id": "",
        "confirmation_session_id": confirmation_session_id,
        "started_at": None,
        "ended_at": None,
        "public_endpoint_classification": "PUBLIC_GET_ONLY_NOT_YET_OBSERVED",
        "request_count": 0,
        "request_interval_distribution": {},
        "rate_limit_event_count": 0,
        "rate_limit_classifications": [],
        "retry_count": 0,
        "backoff_timeline": [],
        "reconnect_count": 0,
        "reconnect_timeline": [],
        "stale_state_transitions": [],
        "heartbeat_state_transitions": [],
        "duplicate_observation_count": 0,
        "confirmation_advance_count": 0,
        "fill_count": 0,
        "process_health_before": None,
        "process_health_after": None,
        "state_digest_before": "",
        "state_digest_after": "",
        "private_endpoint_reachable": False,
        "auth_header_present": False,
        "credential_access_reachable": False,
        "order_side_effect_occurred": False,
        "manifest_digest": "",
        "verifier_result": {
            "ok": False,
            "observed_session": False,
            "notes": ["TEMPLATE_ONLY_WIRING_CAPABILITY"],
        },
        "claims": {
            "OBSERVED_SESSION": False,
            "RATE_LIMIT_PATH_PRODUCTIVELY_OBSERVED": False,
            "RECONNECT_PATH_PRODUCTIVELY_OBSERVED": False,
            "RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED": False,
        },
    }
    payload["manifest_digest"] = sha256_canonical_v1(payload)
    return payload


def validate_session_evidence_schema_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if str(payload.get("schema_version") or "") != SESSION_EVIDENCE_SCHEMA_VERSION:
        blockers.append("SESSION_EVIDENCE_SCHEMA_MISMATCH")
    missing = [f for f in SESSION_EVIDENCE_REQUIRED_FIELDS if f not in payload]
    if missing:
        blockers.append("SESSION_EVIDENCE_FIELDS_MISSING:" + ",".join(missing))
    # Reachability must not be promoted to observed closure.
    claims = dict(payload.get("claims") or {})
    if bool(claims.get("RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED")) and not bool(
        claims.get("OBSERVED_SESSION")
    ):
        blockers.append("LADDER_CLOSED_WITHOUT_OBSERVED_SESSION")
    if bool(payload.get("private_endpoint_reachable")):
        blockers.append("PRIVATE_ENDPOINT_MUST_REMAIN_FALSE")
    if bool(payload.get("auth_header_present")):
        blockers.append("AUTH_HEADER_MUST_REMAIN_FALSE")
    if bool(payload.get("credential_access_reachable")):
        blockers.append("CREDENTIAL_ACCESS_MUST_REMAIN_FALSE")
    if bool(payload.get("order_side_effect_occurred")):
        blockers.append("ORDER_SIDE_EFFECT_MUST_REMAIN_FALSE")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "required_fields": list(SESSION_EVIDENCE_REQUIRED_FIELDS),
        "schema_version": SESSION_EVIDENCE_SCHEMA_VERSION,
    }
