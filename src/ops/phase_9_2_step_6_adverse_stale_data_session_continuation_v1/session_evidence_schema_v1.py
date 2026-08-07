"""Step-6 session evidence schema for a later governed adverse/stale session."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.constants_v1 import (
    CONFIRMATION_SESSION_ID,
    SESSION_EVIDENCE_REQUIRED_FIELDS,
    SESSION_EVIDENCE_SCHEMA_VERSION,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.digest_v1 import (
    sha256_canonical_v1,
)


def build_session_evidence_template_v1(
    *,
    repository_sha: str,
    config_digest: str,
    session_id: str = TARGET_SESSION_ID,
    confirmation_session_id: str = CONFIRMATION_SESSION_ID,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": SESSION_EVIDENCE_SCHEMA_VERSION,
        "repository_sha": repository_sha,
        "config_digest": config_digest,
        "session_id": session_id,
        "runtime_session_id": "",
        "confirmation_session_id": confirmation_session_id,
        "started_at": None,
        "ended_at": None,
        "distinct_observation_count": 0,
        "duplicate_observation_count": 0,
        "stale_observation_count": 0,
        "confirmation_advance_count": 0,
        "stale_confirmation_advance_count": 0,
        "duplicate_confirmation_advance_count": 0,
        "fill_count": 0,
        "fabricated_observation_count": 0,
        "retry_count": 0,
        "backoff_timeline": [],
        "minimum_request_interval_seconds": 2.0,
        "stale_state_transitions": [],
        "private_endpoint_reachable": False,
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
            "STALE_CONDITION_OBSERVED": False,
            "ADVERSE_CONDITION_OBSERVED": False,
            "ADVERSE_STALE_DATA_LADDER_STEP_CLOSED": False,
            "DUPLICATE_CONFIRMATION_ADVANCE": False,
            "STALE_CONFIRMATION_ADVANCE": False,
            "DUPLICATE_FILL": False,
            "ZERO_INTERVAL_RETRY_BURST": False,
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
    claims = dict(payload.get("claims") or {})
    if bool(claims.get("ADVERSE_STALE_DATA_LADDER_STEP_CLOSED")) and not bool(
        claims.get("OBSERVED_SESSION")
    ):
        blockers.append("LADDER_CLOSED_WITHOUT_OBSERVED_SESSION")
    if bool(payload.get("private_endpoint_reachable")):
        blockers.append("PRIVATE_ENDPOINT_MUST_REMAIN_FALSE")
    if bool(payload.get("credential_access_reachable")):
        blockers.append("CREDENTIAL_ACCESS_MUST_REMAIN_FALSE")
    if bool(payload.get("order_side_effect_occurred")):
        blockers.append("ORDER_SIDE_EFFECT_MUST_REMAIN_FALSE")
    if int(payload.get("fabricated_observation_count") or 0) != 0:
        blockers.append("FABRICATED_OBSERVATION_MUST_REMAIN_ZERO")
    if float(payload.get("minimum_request_interval_seconds") or 0) <= 0:
        blockers.append("ZERO_INTERVAL_RETRY_BURST")
    return {"ok": not blockers, "blockers": blockers}
