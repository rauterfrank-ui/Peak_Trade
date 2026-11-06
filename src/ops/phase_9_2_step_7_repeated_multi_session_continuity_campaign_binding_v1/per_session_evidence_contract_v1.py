"""Per-session evidence contract for Step-7 continuity campaign sessions."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.constants_v1 import (
    PER_SESSION_EVIDENCE_CONTRACT_OWNER,
    PER_SESSION_REQUIRED_FIELDS,
    SESSION_EVIDENCE_SCHEMA_VERSION,
    TARGET_SESSION_ID_PREFIX,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.digest_v1 import (
    sha256_canonical_v1,
)


def build_per_session_evidence_template_v1(
    *,
    session_id: str,
    repository_sha: str,
    config_digest: str,
    session_ordinal: int = 1,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": SESSION_EVIDENCE_SCHEMA_VERSION,
        "owner": PER_SESSION_EVIDENCE_CONTRACT_OWNER,
        "session_id": session_id,
        "session_ordinal": int(session_ordinal),
        "session_id_prefix": TARGET_SESSION_ID_PREFIX,
        "repository_sha": repository_sha,
        "config_digest": config_digest,
        "authorization_id": "",
        "authorization_digest": "",
        "confirm_token_fingerprint": "",
        "session_result": {
            "ok": False,
            "status": "TEMPLATE_ONLY",
            "observed_session": False,
        },
        "restart_recovery_result": {
            "ok": False,
            "status": "MISSING",
            "reused_owner": (
                "ops.phase_9_2_step_3_governed_productive_real_network_"
                "restart_recovery_session_execution_v1"
            ),
        },
        "reconnect_result": {
            "ok": False,
            "status": "MISSING",
            "reused_owner": (
                "ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1"
            ),
        },
        "stale_adverse_result": {
            "ok": False,
            "status": "MISSING",
            "reused_owner": (
                "ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1."
                "governed_injected_stale_data_fault_v1"
            ),
        },
        "state_root_before": "",
        "state_root_after": "",
        "confirmation_advance_count": 0,
        "duplicate_confirmation_advance_count": 0,
        "fill_count": 0,
        "duplicate_fill_count": 0,
        "private_endpoint_reachable": False,
        "credential_access_reachable": False,
        "order_side_effect_occurred": False,
        "telemetry": {},
        "verifier_result": {
            "ok": False,
            "status": "TEMPLATE_ONLY",
            "blockers": ["TEMPLATE_ONLY_BINDING_CAPABILITY"],
        },
        "claims": {
            "OBSERVED_SESSION": False,
            "PER_SESSION_AUTHORIZATION_USED": False,
            "AUTHORIZATION_REUSED": False,
            "CONFIRM_TOKEN_REUSED": False,
            "RESTART_RECOVERY_PROVED": False,
            "BOUNDED_RECONNECT_PROVED": False,
            "STALE_ADVERSE_PROVED": False,
            "DUPLICATE_CONFIRMATION_ADVANCE": False,
            "DUPLICATE_FILL": False,
            "PRIVATE_ENDPOINT_REACHED": False,
            "EXCHANGE_CREDENTIAL_PATH_REACHED": False,
            "ORDER_SIDE_EFFECT_OCCURRED": False,
            "CLAIMS_MATCH_TELEMETRY": False,
        },
        "evidence_digest": "",
    }
    payload["evidence_digest"] = sha256_canonical_v1(payload)
    return payload


def validate_per_session_evidence_contract_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if str(payload.get("schema_version") or "") != SESSION_EVIDENCE_SCHEMA_VERSION:
        blockers.append("SESSION_EVIDENCE_SCHEMA_MISMATCH")
    missing = [f for f in PER_SESSION_REQUIRED_FIELDS if f not in payload]
    if missing:
        blockers.append("SESSION_EVIDENCE_FIELDS_MISSING:" + ",".join(missing))
    sid = str(payload.get("session_id") or "")
    if not sid:
        blockers.append("SESSION_ID_MISSING")
    if bool(payload.get("private_endpoint_reachable")):
        blockers.append("PRIVATE_ENDPOINT_MUST_REMAIN_FALSE")
    if bool(payload.get("credential_access_reachable")):
        blockers.append("CREDENTIAL_ACCESS_MUST_REMAIN_FALSE")
    if bool(payload.get("order_side_effect_occurred")):
        blockers.append("ORDER_SIDE_EFFECT_MUST_REMAIN_FALSE")
    return {"ok": not blockers, "blockers": blockers}


def verify_per_session_evidence_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Verify one completed Step-7 session evidence record (read-only)."""
    schema = validate_per_session_evidence_contract_v1(payload)
    blockers = list(schema["blockers"])
    claims = dict(payload.get("claims") or {})
    telemetry = dict(payload.get("telemetry") or {})
    session_result = dict(payload.get("session_result") or {})
    restart = dict(payload.get("restart_recovery_result") or {})
    reconnect = dict(payload.get("reconnect_result") or {})
    stale = dict(payload.get("stale_adverse_result") or {})
    verifier = dict(payload.get("verifier_result") or {})

    if not bool(session_result.get("ok")):
        blockers.append("SESSION_RESULT_NOT_PASS")
    if not bool(verifier.get("ok")):
        blockers.append("SESSION_VERIFIER_NOT_PASS")
    if not bool(restart.get("ok")):
        blockers.append("RESTART_RECOVERY_PROOF_MISSING_OR_FAIL")
    if not bool(reconnect.get("ok")):
        blockers.append("BOUNDED_RECONNECT_PROOF_MISSING_OR_FAIL")
    if not bool(stale.get("ok")):
        blockers.append("STALE_ADVERSE_PROOF_MISSING_OR_FAIL")
    if not str(payload.get("state_root_before") or ""):
        blockers.append("STATE_ROOT_BEFORE_MISSING")
    if not str(payload.get("state_root_after") or ""):
        blockers.append("STATE_ROOT_AFTER_MISSING")
    if not str(payload.get("authorization_id") or ""):
        blockers.append("AUTHORIZATION_BINDING_MISSING")
    if not str(payload.get("authorization_digest") or ""):
        blockers.append("AUTHORIZATION_DIGEST_MISSING")
    if not str(payload.get("confirm_token_fingerprint") or ""):
        blockers.append("CONFIRM_TOKEN_FINGERPRINT_MISSING")
    if bool(claims.get("AUTHORIZATION_REUSED")):
        blockers.append("AUTHORIZATION_REUSE_FORBIDDEN")
    if bool(claims.get("CONFIRM_TOKEN_REUSED")):
        blockers.append("CONFIRM_TOKEN_REUSE_FORBIDDEN")
    if bool(claims.get("DUPLICATE_CONFIRMATION_ADVANCE")) or int(
        payload.get("duplicate_confirmation_advance_count") or 0
    ):
        blockers.append("DUPLICATE_CONFIRMATION_ADVANCE")
    if bool(claims.get("DUPLICATE_FILL")) or int(payload.get("duplicate_fill_count") or 0):
        blockers.append("DUPLICATE_FILL")
    if bool(claims.get("PRIVATE_ENDPOINT_REACHED")) or bool(
        payload.get("private_endpoint_reachable")
    ):
        blockers.append("PRIVATE_ENDPOINT_REACHED")
    if bool(claims.get("EXCHANGE_CREDENTIAL_PATH_REACHED")) or bool(
        payload.get("credential_access_reachable")
    ):
        blockers.append("EXCHANGE_CREDENTIAL_PATH_REACHED")
    if bool(claims.get("ORDER_SIDE_EFFECT_OCCURRED")) or bool(
        payload.get("order_side_effect_occurred")
    ):
        blockers.append("ORDER_SIDE_EFFECT_OCCURRED")

    # Claims must match telemetry where both surfaces exist.
    claim_telem_pairs = (
        ("DUPLICATE_CONFIRMATION_ADVANCE", "duplicate_confirmation_advance_count"),
        ("DUPLICATE_FILL", "duplicate_fill_count"),
        ("PRIVATE_ENDPOINT_REACHED", "private_endpoint_reachable"),
        ("EXCHANGE_CREDENTIAL_PATH_REACHED", "credential_access_reachable"),
        ("ORDER_SIDE_EFFECT_OCCURRED", "order_side_effect_occurred"),
    )
    for claim_key, telem_key in claim_telem_pairs:
        if telem_key not in telemetry and telem_key not in payload:
            continue
        raw = telemetry.get(telem_key, payload.get(telem_key))
        truthy = bool(raw) if not isinstance(raw, (int, float)) else int(raw) != 0
        if bool(claims.get(claim_key)) != truthy:
            blockers.append(f"CLAIMS_TELEMETRY_MISMATCH:{claim_key}")

    if not bool(claims.get("RESTART_RECOVERY_PROVED")):
        blockers.append("CLAIM_RESTART_RECOVERY_PROVED_MISSING")
    if not bool(claims.get("BOUNDED_RECONNECT_PROVED")):
        blockers.append("CLAIM_BOUNDED_RECONNECT_PROVED_MISSING")
    if not bool(claims.get("STALE_ADVERSE_PROVED")):
        blockers.append("CLAIM_STALE_ADVERSE_PROVED_MISSING")

    ok = not blockers
    return {
        "ok": ok,
        "verified": ok,
        "blockers": blockers,
        "session_id": str(payload.get("session_id") or ""),
        "CLAIMS_MATCH_TELEMETRY": not any(
            b.startswith("CLAIMS_TELEMETRY_MISMATCH:") for b in blockers
        ),
        "domain": "STEP7_PER_SESSION_EVIDENCE",
    }
