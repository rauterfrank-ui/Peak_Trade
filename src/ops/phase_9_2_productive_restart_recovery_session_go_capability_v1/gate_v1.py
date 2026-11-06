"""Session-GO gate: fail-closed unlock evaluation before auth/lock/network/session."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.constants_v1 import (
    ACTIVATION_STATUS_ACTIVE,
    ACTIVATION_STATUS_EXPIRED,
    ACTIVATION_STATUS_INACTIVE,
    ACTIVATION_STATUS_REVOKED,
    AUTHORITY_OWNER,
    TARGET_ENTRYPOINT_ID,
    TARGET_ENTRYPOINT_PATH,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.contract_v1 import (
    SessionGoContractError,
    load_session_go_authority_v1,
    parse_session_go_authority_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.models_v1 import (
    SessionGoAuthorityV1,
    SessionGoGateResultV1,
)


def evaluate_session_go_gate_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_session_id: str = TARGET_SESSION_ID,
    expected_entrypoint_id: str = TARGET_ENTRYPOINT_ID,
    expected_entrypoint_path: str = TARGET_ENTRYPOINT_PATH,
    now_unix: float,
    owner_go: bool,
    owner_session_go: bool,
    session_go_path: Path | None = None,
    session_go_payload: Mapping[str, Any] | SessionGoAuthorityV1 | None = None,
    authorization_present: bool = False,
    confirm_token_present: bool = False,
) -> SessionGoGateResultV1:
    """Evaluate Session-GO before any authorization/lock/network/session side effect.

    This gate never consumes authorization, acquires locks, opens network, or starts a
    session. It only decides whether those later steps are permitted.
    """
    notes = [
        f"SESSION_GO_AUTHORITY_OWNER={AUTHORITY_OWNER}",
        "SESSION_GO_EVALUATION_BEFORE_AUTHORIZATION=true",
        "SESSION_GO_EVALUATION_BEFORE_LOCK=true",
        "SESSION_GO_EVALUATION_BEFORE_NETWORK=true",
        "SESSION_GO_EVALUATION_BEFORE_SESSION_START=true",
        "NO_SIDE_EFFECTS_IN_SESSION_GO_GATE=true",
    ]
    blockers: list[str] = []
    authority: Optional[SessionGoAuthorityV1] = None

    if session_go_path is None and session_go_payload is None:
        return SessionGoGateResultV1(
            ok=False,
            blockers=["SESSION_GO_MISSING"],
            notes=notes + ["MISSING_SESSION_GO_FAILS_CLOSED=true"],
        )

    try:
        if session_go_payload is not None:
            if isinstance(session_go_payload, SessionGoAuthorityV1):
                authority = session_go_payload
            else:
                authority = parse_session_go_authority_v1(session_go_payload)
        else:
            assert session_go_path is not None
            authority = load_session_go_authority_v1(session_go_path)
    except SessionGoContractError as exc:
        return SessionGoGateResultV1(
            ok=False,
            blockers=[str(exc)],
            notes=notes + ["SESSION_GO_PARSE_OR_SCHEMA_FAIL_CLOSED=true"],
        )

    if authority.fixture_non_authoritative:
        blockers.append("SESSION_GO_FIXTURE_NON_AUTHORITATIVE")
    if authority.activation_status == ACTIVATION_STATUS_INACTIVE:
        blockers.append("SESSION_GO_INACTIVE")
    if authority.activation_status == ACTIVATION_STATUS_REVOKED:
        blockers.append("SESSION_GO_REVOKED")
    if authority.activation_status == ACTIVATION_STATUS_EXPIRED or float(now_unix) >= float(
        authority.expires_at
    ):
        blockers.append("SESSION_GO_EXPIRED")
    if float(now_unix) < float(authority.not_before):
        blockers.append("SESSION_GO_NOT_YET_VALID")
    if (
        authority.activation_status != ACTIVATION_STATUS_ACTIVE
        and "SESSION_GO_EXPIRED" not in blockers
    ):
        if authority.activation_status not in {
            ACTIVATION_STATUS_INACTIVE,
            ACTIVATION_STATUS_REVOKED,
            ACTIVATION_STATUS_EXPIRED,
        }:
            blockers.append(f"SESSION_GO_ACTIVATION_STATUS_INVALID:{authority.activation_status}")

    if authority.expected_repository_sha != expected_repository_sha:
        blockers.append("SESSION_GO_REPOSITORY_SHA_MISMATCH")
    if authority.expected_config_digest != expected_config_digest:
        blockers.append("SESSION_GO_CONFIG_DIGEST_MISMATCH")
    if authority.session_id != expected_session_id:
        blockers.append("SESSION_GO_SESSION_ID_MISMATCH")
    if authority.entrypoint_id != expected_entrypoint_id:
        blockers.append("SESSION_GO_ENTRYPOINT_ID_MISMATCH")
    if authority.entrypoint_path != expected_entrypoint_path:
        blockers.append("SESSION_GO_ENTRYPOINT_PATH_MISMATCH")
    if not authority.network_session_execution_authorized_by_this_go:
        blockers.append("SESSION_GO_NETWORK_EXECUTION_NOT_AUTHORIZED_BY_THIS_GO")

    if not owner_go:
        blockers.append("OWNER_GO_REQUIRED")
    if not owner_session_go:
        blockers.append("OWNER_SESSION_GO_REQUIRED")
    if owner_go and not owner_session_go:
        notes.append("OWNER_GO_WITHOUT_SESSION_GO_INSUFFICIENT=true")
    if owner_session_go and not owner_go:
        notes.append("OWNER_SESSION_GO_WITHOUT_OWNER_GO_INSUFFICIENT=true")

    if blockers:
        return SessionGoGateResultV1(
            ok=False,
            blockers=sorted(set(blockers)),
            notes=notes,
            authority=authority,
            session_go_authority_satisfied=False,
        )

    # Session-GO authority is satisfied. Still require separate single-use auth + confirm
    # before any side-effect-capable step.
    auth_blockers: list[str] = []
    if not authorization_present:
        auth_blockers.append("SESSION_GO_VALID_BUT_AUTHORIZATION_REQUIRED")
    if not confirm_token_present:
        auth_blockers.append("SESSION_GO_VALID_BUT_CONFIRM_TOKEN_REQUIRED")

    if auth_blockers:
        return SessionGoGateResultV1(
            ok=False,
            blockers=sorted(set(auth_blockers)),
            notes=notes
            + [
                "SESSION_GO_AUTHORITY_SATISFIED=true",
                "SESSION_GO_SEPARATE_FROM_SINGLE_USE_AUTHORIZATION=true",
                "AUTHORIZATION_CONSUMPTION_BLOCKED_UNTIL_PRESENT=true",
            ],
            authority=authority,
            session_go_authority_satisfied=True,
            productive_session_execution_permitted=False,
            authorization_may_proceed=False,
            lock_may_proceed=False,
            network_may_proceed=False,
            session_start_may_proceed=False,
        )

    return SessionGoGateResultV1(
        ok=True,
        blockers=[],
        notes=notes
        + [
            "SESSION_GO_AUTHORITY_SATISFIED=true",
            "PRODUCTIVE_SESSION_EXECUTION_PERMITTED=true",
            "SIDE_EFFECTS_STILL_REQUIRE_CANONICAL_RUNTIME_INVOCATION=true",
        ],
        authority=authority,
        session_go_authority_satisfied=True,
        productive_session_execution_permitted=True,
        authorization_may_proceed=True,
        lock_may_proceed=True,
        network_may_proceed=True,
        session_start_may_proceed=True,
    )
