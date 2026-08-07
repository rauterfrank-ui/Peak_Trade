"""Verifiers for Step-6 binding manifests and later productive session evidence."""

from __future__ import annotations

from typing import Any, Mapping


FORBIDDEN_TRUE_BINDING_CLAIMS = {
    "NETWORK_SESSION_STARTED",
    "FAULT_SESSION_STARTED",
    "ADVERSE_STALE_DATA_LADDER_STEP_CLOSED",
    "CAPABILITY_CLOSED",
    "PHASE_9_2_COMPLETE",
    "AUTHORIZATION_CONSUMED",
    "CONFIRM_TOKEN_CONSUMED",
    "AUTHORIZATION_ISSUED",
    "CONFIRM_TOKEN_ISSUED",
}


def verify_binding_manifest_v1(manifest: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    claims = dict(manifest.get("claims") or {})
    for key in FORBIDDEN_TRUE_BINDING_CLAIMS:
        if bool(claims.get(key)):
            blockers.append(f"FORBIDDEN_CLAIM_TRUE:{key}")
    if not bool(claims.get("STEP6_BINDING_IMPLEMENTED")):
        blockers.append("MISSING_BINDING_IMPLEMENTED_CLAIM")
    if not bool(claims.get("READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION")):
        blockers.append("MISSING_READY_FOR_SEPARATE_SESSION_CLAIM")
    if str(claims.get("PHASE_9_2_STEP_6_STATUS") or "") != "OPEN":
        blockers.append("STEP6_STATUS_MUST_REMAIN_OPEN")
    if not bool(claims.get("STALE_DATA_CLASSIFIER_BOUND")):
        blockers.append("MISSING_STALE_CLASSIFIER_BOUND")
    if not bool(claims.get("ADVERSE_DATA_CLASSIFIER_BOUND")):
        blockers.append("MISSING_ADVERSE_CLASSIFIER_BOUND")
    if not bool(claims.get("FAILURE_INJECTION_BOUND")):
        blockers.append("MISSING_FAILURE_INJECTION_BOUND")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "verified": not blockers,
        "claims": claims,
        "domain": "IMPLEMENTATION_PROOF",
    }


def verify_productive_session_evidence_v1(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Contract for a later governed Step-6 network session (not executed here)."""
    blockers: list[str] = []
    claims = dict(evidence.get("claims") or {})
    telemetry = dict(evidence.get("telemetry") or evidence)

    def _req_true(key: str) -> None:
        if not bool(claims.get(key, telemetry.get(key))):
            blockers.append(f"REQUIRED_TRUE_MISSING:{key}")

    def _req_false(key: str) -> None:
        if bool(claims.get(key, telemetry.get(key))):
            blockers.append(f"REQUIRED_FALSE_VIOLATED:{key}")

    _req_true("STALE_CONDITION_OBSERVED")
    _req_true("ADVERSE_CONDITION_OBSERVED")
    _req_false("DUPLICATE_CONFIRMATION_ADVANCE")
    _req_false("STALE_CONFIRMATION_ADVANCE")
    _req_false("DUPLICATE_FILL")
    _req_false("ZERO_INTERVAL_RETRY_BURST")
    _req_false("PRIVATE_ENDPOINT_REACHED")
    _req_false("EXCHANGE_CREDENTIAL_PATH_REACHED")
    _req_false("ORDER_SIDE_EFFECT_OCCURRED")

    for count_key in (
        "STALE_OBSERVATION_COUNT",
        "DISTINCT_OBSERVATION_COUNT",
        "DUPLICATE_OBSERVATION_COUNT",
    ):
        raw = claims.get(count_key, telemetry.get(count_key.lower(), telemetry.get(count_key)))
        if raw is None:
            blockers.append(f"COUNT_MISSING:{count_key}")

    if not bool(claims.get("BOUNDED_RETRY_OBSERVED", telemetry.get("BOUNDED_RETRY_OBSERVED"))):
        blockers.append("BOUNDED_RETRY_NOT_OBSERVED")
    if not bool(claims.get("BOUNDED_BACKOFF_OBSERVED", telemetry.get("BOUNDED_BACKOFF_OBSERVED"))):
        blockers.append("BOUNDED_BACKOFF_NOT_OBSERVED")

    if int(telemetry.get("fabricated_observation_count") or 0) != 0:
        blockers.append("FABRICATED_OBSERVATION_PRESENT")
    if int(telemetry.get("stale_confirmation_advance_count") or 0) != 0:
        blockers.append("STALE_CONFIRMATION_ADVANCE_COUNT_NONZERO")
    if int(telemetry.get("duplicate_confirmation_advance_count") or 0) != 0:
        blockers.append("DUPLICATE_CONFIRMATION_ADVANCE_COUNT_NONZERO")
    if float(telemetry.get("minimum_request_interval_seconds") or 0) <= 0:
        blockers.append("ZERO_INTERVAL_RETRY_BURST")

    claims_match = not blockers
    return {
        "ok": claims_match,
        "blockers": blockers,
        "verified": claims_match,
        "CLAIMS_MATCH_EVIDENCE": claims_match,
        "domain": "AUTHORIZED_PRODUCTIVE_SESSION",
        "claims": claims,
    }
