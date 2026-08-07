"""Fail-closed execution gates for Step-3 surface."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.gate_v1 import (
    evaluate_session_go_gate_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    AUTHORIZATION_ISSUANCE_ALLOWED,
    BINDING_CAPABILITY_ID,
    CANONICAL_INSTRUMENT_ID,
    CAPABILITY_ID,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    CONFIRM_TOKEN_ISSUANCE_ALLOWED,
    NETWORK_SESSION_ALLOWED,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    REAL_NETWORK_REQUESTS_ALLOWED,
    RUNTIME_CAPABILITY_ID,
    SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED,
    TARGET_SESSION_ID,
)

_ALLOWED_AUTH_CAPABILITY_IDS = frozenset(
    {
        CAPABILITY_ID,
        RUNTIME_CAPABILITY_ID,
        BINDING_CAPABILITY_ID,
        "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_NETWORK_ENTRYPOINT_V1",
    }
)


def evaluate_step3_execution_gates_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    now_unix: float,
    owner_go: bool,
    operator_authorization_explicit: bool,
    network_session_go: bool,
    session_go_path: Path | None,
    authorization_present: bool,
    confirm_token_present: bool,
    authorization_artifact: Mapping[str, Any] | None = None,
    expected_instrument_id: str = CANONICAL_INSTRUMENT_ID,
    expected_session_id: str = TARGET_SESSION_ID,
    expected_capability_id: str = CAPABILITY_ID,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        f"RUNTIME_CAPABILITY_ID={RUNTIME_CAPABILITY_ID}",
        "PERMANENT_SIDE_EFFECT_CONSTANTS_MUST_REMAIN_FALSE=true",
    ]
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))

    if expected_capability_id not in {CAPABILITY_ID, RUNTIME_CAPABILITY_ID}:
        blockers.append("CAPABILITY_SCOPE_MISMATCH")
    if not owner_go:
        blockers.append("OWNER_GO_REQUIRED")
    if not operator_authorization_explicit:
        blockers.append("OPERATOR_AUTHORIZATION_REQUIRED")
    if not network_session_go:
        blockers.append("NETWORK_SESSION_GO_REQUIRED")
    if not authorization_present:
        blockers.append("AUTHORIZATION_REQUIRED")
    if not confirm_token_present:
        blockers.append("CONFIRM_TOKEN_HANDOFF_REQUIRED")

    if NETWORK_SESSION_ALLOWED or REAL_NETWORK_REQUESTS_ALLOWED:
        blockers.append("PERMANENT_NETWORK_ALLOW_MUST_REMAIN_FALSE")
    if AUTHORIZATION_ISSUANCE_ALLOWED or AUTHORIZATION_CONSUMPTION_ALLOWED:
        blockers.append("PERMANENT_AUTHORIZATION_ALLOW_MUST_REMAIN_FALSE")
    if CONFIRM_TOKEN_ISSUANCE_ALLOWED or CONFIRM_TOKEN_CONSUMPTION_ALLOWED:
        blockers.append("PERMANENT_CONFIRM_TOKEN_ALLOW_MUST_REMAIN_FALSE")
    if SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED:
        blockers.append("SESSION_EXECUTION_SIDE_EFFECTS_MUST_REMAIN_FALSE")
    if PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED:
        blockers.append("PRODUCTIVE_NETWORK_MUST_REMAIN_UNAUTHORIZED")

    gate = None
    if session_go_path is None:
        blockers.append("SESSION_GO_MISSING")
    else:
        gate = evaluate_session_go_gate_v1(
            expected_repository_sha=expected_repository_sha,
            expected_config_digest=expected_config_digest,
            now_unix=now_unix,
            owner_go=owner_go,
            owner_session_go=True,
            session_go_path=session_go_path,
            authorization_present=authorization_present,
            confirm_token_present=confirm_token_present,
        )
        if not gate.session_go_authority_satisfied:
            blockers.extend(list(gate.blockers or ["SESSION_GO_GATE_FAILED"]))
        notes.extend(list(gate.notes or []))

    if authorization_artifact is not None:
        art = dict(authorization_artifact)
        art_sha = str(art.get("expected_repository_sha") or art.get("repository_sha") or "")
        art_cfg = str(art.get("expected_config_digest") or art.get("config_digest") or "")
        art_session = str(art.get("session_id") or art.get("expected_session_id") or "")
        art_instrument = str(
            art.get("instrument_identity")
            or art.get("canonical_instrument_id")
            or art.get("instrument_id")
            or ""
        )
        art_capability = str(art.get("capability_id") or art.get("expected_capability_id") or "")
        if art_sha and art_sha != expected_repository_sha:
            blockers.append("AUTHORIZATION_SHA_MISMATCH")
        if art_cfg and art_cfg != expected_config_digest:
            blockers.append("AUTHORIZATION_CONFIG_DIGEST_MISMATCH")
        if art_session and art_session != expected_session_id:
            blockers.append("AUTHORIZATION_SESSION_SCOPE_MISMATCH")
        if art_instrument and art_instrument != expected_instrument_id:
            blockers.append("INSTRUMENT_SCOPE_MISMATCH")
        if art_capability and art_capability not in _ALLOWED_AUTH_CAPABILITY_IDS:
            blockers.append("AUTHORIZATION_CAPABILITY_SCOPE_MISMATCH")

    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "notes": notes,
        "owner_go": bool(owner_go),
        "operator_authorization_explicit": bool(operator_authorization_explicit),
        "network_session_go": bool(network_session_go),
        "authorization_present": bool(authorization_present),
        "confirm_token_present": bool(confirm_token_present),
        "session_go_gate": None if gate is None else gate.to_dict(),
        "network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
    }
