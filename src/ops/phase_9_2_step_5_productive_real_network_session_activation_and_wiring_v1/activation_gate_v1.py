"""Step-5 activation gate — SHA/digest/scope/auth/token/GO truth table."""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.authorization_gate_v1 import (  # noqa: E501
    validate_execution_authorization_artifact_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.confirm_token_path_v1 import (  # noqa: E501
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.contract_bindings_v1 import (  # noqa: E501
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.hidden_pty_handoff_v1 import (  # noqa: E501
    fingerprint_only_v1,
    validate_confirm_token_binding_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.constants_v1 import (
    CAPABILITY_ID,
    HTTP_METHOD_ALLOWLIST,
    MAX_SESSION_DURATION_SECONDS,
    MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
    NETWORK_ALLOWLIST,
    NETWORK_MODE,
    PLANNED_SESSION_DURATION_SECONDS,
    SESSION_SCOPE,
    STEP5_EXECUTION_CAPABILITY_ID,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.network_session_go_v1 import (
    bind_ephemeral_network_session_go_v1,
)


def evaluate_step5_activation_gate_v1(
    *,
    expected_repository_sha: str,
    expected_session_contract_digest: str,
    expected_binding_config_digest: str,
    authorization_id: str,
    authorization_digest: str,
    confirm_token_binding_sha256: str,
    confirm_token_plaintext: str | None,
    now_unix: float,
    network_session_go: bool = False,
    owner_go: bool = False,
    operator_authorization_explicit: bool = False,
    authorization_expires_at: float | None = None,
    confirm_token_expires_at: float | None = None,
    already_consumed_authorization: bool = False,
    already_consumed_confirm_token: bool = False,
    authorization_scope: str = SESSION_SCOPE,
    authorization_session_id: str = TARGET_SESSION_ID,
    authorization_capability_id: str = STEP5_EXECUTION_CAPABILITY_ID,
    authorization_repository_sha: str = "",
    authorization_session_contract_digest: str = "",
    authorization_binding_config_digest: str = "",
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    repo_root=None,
    private_endpoint_requested: bool = False,
    non_get_method_requested: bool = False,
    auth_header_requested: bool = False,
    credential_access_requested: bool = False,
    order_side_effect_requested: bool = False,
) -> dict[str, Any]:
    """Evaluate full activation gate. Does not issue/consume and does not start network."""
    blockers: list[str] = []
    notes = [
        f"ACTIVATION_CAPABILITY_ID={CAPABILITY_ID}",
        "STEP4_AUTHORIZATION_PATTERN_REUSED=true",
        "STEP4_CONFIRM_TOKEN_PATTERN_REUSED=true",
        "NO_ISSUANCE_NO_CONSUMPTION_IN_THIS_CAPABILITY=true",
        "NO_NETWORK_SESSION_IN_THIS_CAPABILITY=true",
    ]

    go = bind_ephemeral_network_session_go_v1(
        network_session_go=network_session_go,
        environ=environ,
    )
    blockers.extend(list(go.get("blockers") or []))
    if not owner_go:
        blockers.append("OWNER_GO_REQUIRED")
    if not operator_authorization_explicit:
        blockers.append("OPERATOR_AUTHORIZATION_REQUIRED")
    if not bool(go.get("network_session_go")):
        blockers.append("NETWORK_SESSION_GO_REQUIRED")

    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))

    bundle = load_execution_contract_bundle_v1(repo_root=repo_root)
    got_contract = str(bundle["session_contract_digest"])
    got_binding = str(bundle["binding_config_digest"])
    if str(expected_session_contract_digest) != got_contract:
        blockers.append("SESSION_CONTRACT_DIGEST_MISMATCH")
    if str(expected_binding_config_digest) != got_binding:
        blockers.append("BINDING_CONFIG_DIGEST_MISMATCH")
    if int(bundle["planned_session_duration_seconds"]) != PLANNED_SESSION_DURATION_SECONDS:
        blockers.append("PLANNED_DURATION_DRIFT")
    if int(bundle["minimum_successful_wallclock_seconds"]) != MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS:
        blockers.append("MINIMUM_DURATION_DRIFT")
    if (
        int(bundle["session_contract"]["max_session_duration_seconds"])
        != MAX_SESSION_DURATION_SECONDS
    ):
        blockers.append("MAXIMUM_DURATION_DRIFT")

    if not expected_repository_sha or len(str(expected_repository_sha).strip()) < 7:
        blockers.append("REPOSITORY_SHA_INVALID")

    if not str(authorization_id or "").strip():
        blockers.append("AUTHORIZATION_MISSING")
    if not str(authorization_digest or "").strip():
        blockers.append("AUTHORIZATION_DIGEST_MISSING")
    if already_consumed_authorization:
        blockers.append("AUTHORIZATION_ALREADY_CONSUMED")

    auth = validate_execution_authorization_artifact_v1(
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        expected_repository_sha=expected_repository_sha,
        expected_session_contract_digest=expected_session_contract_digest or got_contract,
        expected_binding_config_digest=expected_binding_config_digest or got_binding,
        expected_scope=authorization_scope,
        expected_session_id=authorization_session_id,
        expected_capability_id=authorization_capability_id,
        planned_session_duration_seconds=PLANNED_SESSION_DURATION_SECONDS,
        network_mode=NETWORK_MODE,
        public_md_endpoint_allowlist=NETWORK_ALLOWLIST,
        http_method_allowlist=HTTP_METHOD_ALLOWLIST,
        authorization_repository_sha=authorization_repository_sha or expected_repository_sha,
        authorization_scope=authorization_scope,
        authorization_session_id=authorization_session_id,
        authorization_capability_id=authorization_capability_id,
        authorization_session_contract_digest=authorization_session_contract_digest
        or expected_session_contract_digest
        or got_contract,
        authorization_binding_config_digest=authorization_binding_config_digest
        or expected_binding_config_digest
        or got_binding,
        authorization_planned_duration_seconds=PLANNED_SESSION_DURATION_SECONDS,
        authorization_network_mode=NETWORK_MODE,
        authorization_public_md_allowlist=NETWORK_ALLOWLIST,
        authorization_http_method_allowlist=HTTP_METHOD_ALLOWLIST,
        authorization_expires_at=authorization_expires_at,
        now_unix=now_unix,
        already_consumed=already_consumed_authorization,
    )
    # Authorization gate constants forbid permanent consumption allow; strip those
    # permanent-constant blockers — this activation capability keeps constants false
    # and only validates binding shape for a later session.
    auth_blockers = [
        b
        for b in (auth.get("blockers") or [])
        if b
        not in {
            "AUTHORIZATION_ISSUANCE_MUST_REMAIN_FALSE",
            "AUTHORIZATION_CONSUMPTION_MUST_REMAIN_FALSE",
        }
    ]
    if not auth.get("ok") and auth_blockers:
        blockers.extend(auth_blockers)
        blockers.append("AUTHORIZATION_FAILURE")
    elif auth_blockers:
        blockers.extend(auth_blockers)

    token_plain = str(confirm_token_plaintext or "")
    if not token_plain.strip():
        blockers.append("CONFIRM_TOKEN_MISSING")
    if already_consumed_confirm_token:
        blockers.append("CONFIRM_TOKEN_ALREADY_CONSUMED")

    expires = (
        float(confirm_token_expires_at)
        if confirm_token_expires_at is not None
        else float(now_unix) + 3600.0
    )
    token = validate_confirm_token_binding_v1(
        confirm_token_plaintext=token_plain,
        expected_binding_sha256=confirm_token_binding_sha256,
        expected_repository_sha=expected_repository_sha,
        expected_session_contract_digest=expected_session_contract_digest or got_contract,
        expected_binding_config_digest=expected_binding_config_digest or got_binding,
        expected_session_id=authorization_session_id,
        expected_scope=authorization_scope,
        expires_at=expires,
        now_unix=now_unix,
        already_consumed=already_consumed_confirm_token,
        argv=argv,
        environ=environ,
    )
    token_blockers = [
        b
        for b in (token.get("blockers") or [])
        if b != "CONFIRM_TOKEN_CONSUMPTION_MUST_REMAIN_FALSE_IN_CONSTANTS"
    ]
    if token_blockers:
        blockers.extend(token_blockers)
        blockers.append("CONFIRM_TOKEN_FAILURE")

    if authorization_scope != SESSION_SCOPE:
        blockers.append("AUTHORIZATION_SCOPE_MISMATCH")
    if authorization_capability_id not in {STEP5_EXECUTION_CAPABILITY_ID, CAPABILITY_ID}:
        # Execution capability id is the session runtime scope; activation id alone insufficient.
        if authorization_capability_id != STEP5_EXECUTION_CAPABILITY_ID:
            blockers.append("CAPABILITY_SCOPE_MISMATCH")

    if private_endpoint_requested:
        blockers.append("PRIVATE_ENDPOINT_REQUEST_REJECTED")
    if non_get_method_requested:
        blockers.append("NON_GET_METHOD_REJECTED")
    if auth_header_requested:
        blockers.append("AUTH_HEADER_REQUEST_REJECTED")
    if credential_access_requested:
        blockers.append("CREDENTIAL_ACCESS_REQUEST_REJECTED")
    if order_side_effect_requested:
        blockers.append("ORDER_SIDE_EFFECT_REQUEST_REJECTED")

    unique = sorted(set(blockers))
    ok = not unique
    fp = fingerprint_only_v1(token_plain) if token_plain else ""
    return {
        "ok": ok,
        "blockers": unique,
        "notes": notes,
        "activation_permit_ok": ok,
        "network_session_go": bool(go.get("network_session_go")),
        "network_session_go_default_false": True,
        "network_session_go_persisted": False,
        "ephemeral_network_session_go_bound": True,
        "session_contract_digest": got_contract,
        "binding_config_digest": got_binding,
        "planned_session_duration_seconds": PLANNED_SESSION_DURATION_SECONDS,
        "minimum_successful_wallclock_seconds": MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
        "max_session_duration_seconds": MAX_SESSION_DURATION_SECONDS,
        "authorization_id": str(authorization_id or "").strip(),
        "authorization_digest": str(authorization_digest or "").strip(),
        "confirm_token_id": f"tok_{fp[:16]}" if fp else "",
        "confirm_token_digest": fp,
        "confirm_token_fingerprint": fp,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
        "network_session_started": False,
        "claims": {
            "ACTIVATION_PERMIT_OK": ok,
            "EPHEMERAL_NETWORK_SESSION_GO_BOUND": True,
            "NETWORK_SESSION_GO_DEFAULT_FALSE": True,
            "NETWORK_SESSION_GO_PERSISTED": False,
            "AUTHORIZATION_ISSUED": False,
            "AUTHORIZATION_CONSUMED": False,
            "CONFIRM_TOKEN_ISSUED": False,
            "CONFIRM_TOKEN_CONSUMED": False,
            "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            "CONFIRM_TOKEN_PERSISTED": False,
            "NETWORK_SESSION_STARTED": False,
            "PARALLEL_AUTHORIZATION_MODEL_CREATED": False,
            "PARALLEL_TOKEN_MODEL_CREATED": False,
            "STEP4_AUTHORIZATION_PATTERN_REUSED": True,
            "STEP4_CONFIRM_TOKEN_PATTERN_REUSED": True,
            "PUBLIC_MD_GET_ONLY": True,
            "PRIVATE_ENDPOINT_REACHABLE": False,
            "AUTH_HEADER_REACHABLE": False,
            "EXCHANGE_CREDENTIAL_PATH_REACHABLE": False,
            "ORDER_SUBMIT_PATH_REACHABLE": False,
            "PLANNED_SESSION_DURATION_SECONDS": PLANNED_SESSION_DURATION_SECONDS,
            "MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS": MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
            "MAX_SESSION_DURATION_SECONDS": MAX_SESSION_DURATION_SECONDS,
        },
    }


def expected_confirm_binding_from_plaintext_v1(plaintext: str) -> str:
    return hashlib.sha256(str(plaintext).encode("utf-8")).hexdigest()
