"""Campaign verifier for Step-7 multi-session continuity bundles."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.constants_v1 import (
    CAMPAIGN_VERIFIER_OWNER,
    MULTI_SESSION_REQUIREMENT_EXPRESSION,
    multi_session_requirement_satisfied_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.per_session_evidence_contract_v1 import (
    verify_per_session_evidence_v1,
)


FORBIDDEN_TRUE_BINDING_CLAIMS = {
    "NETWORK_SESSION_STARTED",
    "AUTHORIZATION_CONSUMED",
    "CONFIRM_TOKEN_MINTED",
    "CONFIRM_TOKEN_CONSUMED",
    "CAMPAIGN_EXECUTED",
    "MULTI_SESSION_CONTINUITY_LADDER_STEP_CLOSED",
    "PHASE_9_2_SESSION_LADDER_COMPLETE",
    "CAPABILITY_CLOSED",
    "STEP7_STARTED",
}


def _transition_allows_v1(
    *,
    from_repo: str,
    from_cfg: str,
    to_repo: str,
    to_cfg: str,
    transitions: list[Mapping[str, Any]],
) -> bool:
    for item in transitions:
        if (
            str(item.get("from_repository_sha") or "") == from_repo
            and str(item.get("from_config_digest") or "") == from_cfg
            and str(item.get("to_repository_sha") or "") == to_repo
            and str(item.get("to_config_digest") or "") == to_cfg
            and bool(item.get("explicitly_governed"))
        ):
            return True
    return False


def verify_binding_manifest_v1(manifest: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    claims = dict(manifest.get("claims") or {})
    for key in FORBIDDEN_TRUE_BINDING_CLAIMS:
        if bool(claims.get(key)):
            blockers.append(f"FORBIDDEN_CLAIM_TRUE:{key}")
    if not bool(claims.get("STEP7_BINDING_IMPLEMENTED")):
        blockers.append("MISSING_BINDING_IMPLEMENTED_CLAIM")
    if not bool(claims.get("STEP7_CAMPAIGN_OWNER_PRESENT")):
        blockers.append("MISSING_CAMPAIGN_OWNER_CLAIM")
    if not bool(claims.get("STEP7_CAMPAIGN_HARNESS_BOUND")):
        blockers.append("MISSING_CAMPAIGN_HARNESS_CLAIM")
    if not bool(claims.get("STEP7_PER_SESSION_EVIDENCE_CONTRACT_PRESENT")):
        blockers.append("MISSING_PER_SESSION_EVIDENCE_CONTRACT_CLAIM")
    if not bool(claims.get("STEP7_CAMPAIGN_BUNDLE_OWNER_PRESENT")):
        blockers.append("MISSING_CAMPAIGN_BUNDLE_OWNER_CLAIM")
    if not bool(claims.get("STEP7_CAMPAIGN_VERIFIER_PRESENT")):
        blockers.append("MISSING_CAMPAIGN_VERIFIER_CLAIM")
    if not bool(claims.get("READY_FOR_SEPARATE_OWNER_GO_CAMPAIGN_EXECUTION")):
        blockers.append("MISSING_READY_FOR_SEPARATE_CAMPAIGN_EXECUTION_CLAIM")
    if str(claims.get("PHASE_9_2_STEP_7_STATUS") or "") != "OPEN":
        blockers.append("STEP7_STATUS_MUST_REMAIN_OPEN")
    if bool(claims.get("PHASE_9_2_SESSION_LADDER_COMPLETE")):
        blockers.append("SESSION_LADDER_MUST_REMAIN_INCOMPLETE")
    if str(claims.get("MULTI_SESSION_REQUIREMENT_EXPRESSION") or "") != (
        MULTI_SESSION_REQUIREMENT_EXPRESSION
    ):
        blockers.append("MULTI_SESSION_REQUIREMENT_EXPRESSION_DRIFT")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "verified": not blockers,
        "claims": claims,
        "domain": "IMPLEMENTATION_PROOF",
        "owner": CAMPAIGN_VERIFIER_OWNER,
    }


def verify_campaign_bundle_v1(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Verify a read-only aggregated multi-session campaign bundle."""
    blockers: list[str] = []
    sessions = list(bundle.get("sessions") or [])
    session_count = len(sessions)
    if not multi_session_requirement_satisfied_v1(session_count):
        blockers.append(
            f"MULTI_SESSION_REQUIREMENT_NOT_MET:"
            f"count={session_count}:need{MULTI_SESSION_REQUIREMENT_EXPRESSION}"
        )

    expected_repo = str(bundle.get("expected_repository_sha") or "")
    expected_cfg = str(bundle.get("expected_config_digest") or "")
    transitions = [dict(t) for t in (bundle.get("allowed_binding_transitions") or [])]

    auth_ids: set[str] = set()
    confirm_fps: set[str] = set()
    total_dup_advances = 0
    total_dup_fills = 0
    per_session: list[dict[str, Any]] = []

    for idx, session in enumerate(sessions):
        verdict = verify_per_session_evidence_v1(session)
        per_session.append(verdict)
        if not bool(verdict.get("ok")):
            blockers.append(
                f"SESSION_VERIFIER_FAIL:{session.get('session_id')}:{','.join(verdict['blockers'])}"
            )

        repo = str(session.get("repository_sha") or "")
        cfg = str(session.get("config_digest") or "")
        if expected_repo and repo != expected_repo:
            if not _transition_allows_v1(
                from_repo=expected_repo,
                from_cfg=expected_cfg,
                to_repo=repo,
                to_cfg=cfg,
                transitions=transitions,
            ):
                blockers.append(f"REPO_BINDING_MISMATCH:{session.get('session_id')}")
        if expected_cfg and cfg != expected_cfg:
            if not _transition_allows_v1(
                from_repo=expected_repo or repo,
                from_cfg=expected_cfg,
                to_repo=repo,
                to_cfg=cfg,
                transitions=transitions,
            ):
                blockers.append(f"CONFIG_BINDING_MISMATCH:{session.get('session_id')}")

        auth_id = str(session.get("authorization_id") or "")
        if auth_id:
            if auth_id in auth_ids:
                blockers.append(f"AUTHORIZATION_REUSED_ACROSS_SESSIONS:{auth_id}")
            auth_ids.add(auth_id)
        confirm_fp = str(session.get("confirm_token_fingerprint") or "")
        if confirm_fp:
            if confirm_fp in confirm_fps:
                blockers.append(f"CONFIRM_TOKEN_REUSED_ACROSS_SESSIONS:{confirm_fp}")
            confirm_fps.add(confirm_fp)

        total_dup_advances += int(session.get("duplicate_confirmation_advance_count") or 0)
        total_dup_fills += int(session.get("duplicate_fill_count") or 0)
        if bool(session.get("private_endpoint_reachable")):
            blockers.append(f"PRIVATE_ENDPOINT_REACHED:{session.get('session_id')}")
        if bool(session.get("credential_access_reachable")):
            blockers.append(f"EXCHANGE_CREDENTIAL_PATH_REACHED:{session.get('session_id')}")
        if bool(session.get("order_side_effect_occurred")):
            blockers.append(f"ORDER_SIDE_EFFECT_OCCURRED:{session.get('session_id')}")

        if idx > 0:
            prev = sessions[idx - 1]
            prev_after = str(prev.get("state_root_after") or "")
            cur_before = str(session.get("state_root_before") or "")
            if not prev_after or not cur_before or prev_after != cur_before:
                blockers.append(
                    f"STATE_DISCONTINUITY:{prev.get('session_id')}->{session.get('session_id')}"
                )
            prev_repo = str(prev.get("repository_sha") or "")
            prev_cfg = str(prev.get("config_digest") or "")
            if (repo != prev_repo or cfg != prev_cfg) and not _transition_allows_v1(
                from_repo=prev_repo,
                from_cfg=prev_cfg,
                to_repo=repo,
                to_cfg=cfg,
                transitions=transitions,
            ):
                blockers.append(
                    f"CROSS_SESSION_BINDING_MISMATCH_UNGOVERNED:"
                    f"{prev.get('session_id')}->{session.get('session_id')}"
                )

    if total_dup_advances:
        blockers.append("DUPLICATE_CONFIRMATION_ADVANCE_IN_CAMPAIGN")
    if total_dup_fills:
        blockers.append("DUPLICATE_FILL_IN_CAMPAIGN")

    # Evidence claims must correspond to telemetry (per-session already checks;
    # campaign-level also rejects any CLAIMS_MATCH_TELEMETRY=false).
    for verdict in per_session:
        if verdict.get("CLAIMS_MATCH_TELEMETRY") is False:
            blockers.append(f"CLAIMS_TELEMETRY_MISMATCH_CAMPAIGN:{verdict.get('session_id')}")

    ok = not blockers
    return {
        "ok": ok,
        "verified": ok,
        "blockers": blockers,
        "session_count": session_count,
        "multi_session_requirement_expression": MULTI_SESSION_REQUIREMENT_EXPRESSION,
        "multi_session_requirement_satisfied": multi_session_requirement_satisfied_v1(
            session_count
        ),
        "per_session_verdicts": per_session,
        "owner": CAMPAIGN_VERIFIER_OWNER,
        "domain": "STEP7_CAMPAIGN_BUNDLE",
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_MINTED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "PHASE_9_2_SESSION_LADDER_COMPLETE": False,
        "PHASE_9_2_STEP_7_STATUS": "OPEN",
    }
