"""Governed Step-4 execution binding: auth-derived network_allowed + Hidden-PTY + lock.

Proves the productive call graph through session lock, exactly-once consumption, and
an injected wallclock runner stub. Never opens sockets / DNS / HTTP.
``GOVERNED_EXECUTION_BINDING_REAL_NETWORK_SIDE_EFFECTS_AUTHORIZED`` remains false.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, MutableMapping, Optional

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_lock_v1 import (
    SessionLockError,
    SessionLockV1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.authorization_binding_v1 import (
    consume_authorization_binding_v1,
    load_consumed_authorization_ids_from_ledger_v1,
    validate_authorization_binding_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.confirm_token_binding_v1 import (
    consume_confirm_token_binding_v1,
    fingerprint_only_v1,
    validate_confirm_token_binding_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    AUTHORIZATION_LEDGER_FILENAME,
    CONFIRM_TOKEN_LEDGER_FILENAME,
    GOVERNED_EXECUTION_BINDING_CAPABILITY_ID,
    GOVERNED_EXECUTION_BINDING_REAL_NETWORK_SIDE_EFFECTS_AUTHORIZED,
    HTTP_METHOD_ALLOWLIST,
    NETWORK_ALLOWLIST,
    SESSION_LOCK_OWNER,
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.network_boundary_v1 import (
    prove_public_md_network_boundary_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.runner_invoke_binding_v1 import (
    build_canonical_wallclock_runner_kwargs_v1,
)

WallclockRunnerV1 = Callable[..., Any]

CALL_GRAPH_AFTER = [
    "Authorization issuance artifacts",
    "build_canonical_session_request_from_issuance_artifacts_v1",
    "explicit governed-public-network mode",
    "network_allowed=true only from validated authorization scope",
    "canonical hidden-PTY confirm-token acquisition",
    "validate_authorization_binding_v1",
    "validate_confirm_token_binding_v1",
    "SessionLockV1.acquire",
    "consume_authorization_binding_v1",
    "consume_confirm_token_binding_v1",
    "run_productive_wallclock_session_v1 (injected stub only in this capability)",
]

CALL_GRAPH_BEFORE = [
    "Authorization issuance artifacts",
    "build_canonical_session_request_from_issuance_artifacts_v1",
    "ADAPTER_FORBIDS_USE_REAL_NETWORK / SESSION_REQUEST_ADAPTER_CAPABILITY_FORBIDS_NETWORK_SESSION",
    "dry probe only (network_session_allowed must remain false)",
]


@dataclass
class GovernedExecutionBindingResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)
    authorization_consumed: bool = False
    confirm_token_consumed: bool = False
    session_lock_acquired: bool = False
    wallclock_runner_invoked: bool = False
    network_session_executed: bool = False
    real_network_request_count: int = 0
    runner_result: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "claims": dict(self.claims),
            "authorization_consumed": self.authorization_consumed,
            "confirm_token_consumed": self.confirm_token_consumed,
            "session_lock_acquired": self.session_lock_acquired,
            "wallclock_runner_invoked": self.wallclock_runner_invoked,
            "network_session_executed": self.network_session_executed,
            "real_network_request_count": self.real_network_request_count,
            "runner_result": self.runner_result,
            "capability_id": GOVERNED_EXECUTION_BINDING_CAPABILITY_ID,
            "call_graph_before": list(CALL_GRAPH_BEFORE),
            "call_graph_after": list(CALL_GRAPH_AFTER),
        }


def execute_governed_step4_execution_binding_v1(
    *,
    session_request: Mapping[str, Any],
    network_allowed_from_authorization: bool,
    expected_repository_sha: str,
    expected_config_digest: str,
    authorization_id: str,
    authorization_digest: str,
    confirm_token_binding_sha256: str,
    confirm_token_plaintext: str,
    confirm_token_expires_at: float,
    now_unix: float,
    persistence_root: Path,
    wallclock_runner: WallclockRunnerV1 | None,
    allow_real_network_side_effects: bool = False,
    environ: Mapping[str, str] | None = None,
    argv: list[str] | None = None,
    authorization_scope: str = SESSION_SCOPE,
    authorization_session_id: str | None = None,
    confirm_token_expected_session_id: str | None = None,
    confirm_token_expected_scope_digest: str | None = None,
    runtime_session_id: str | None = None,
) -> GovernedExecutionBindingResultV1:
    """Validate → lock → consume → invoke injected runner. No real network."""
    blockers: list[str] = []
    notes = [
        f"GOVERNED_EXECUTION_BINDING_CAPABILITY_ID={GOVERNED_EXECUTION_BINDING_CAPABILITY_ID}",
        f"SESSION_LOCK_OWNER={SESSION_LOCK_OWNER}",
        "NO_REAL_NETWORK_SIDE_EFFECTS_IN_THIS_CAPABILITY=true",
        "PARALLEL_SESSION_REQUEST_MODEL_CREATED=false",
    ]
    auth_consumed = False
    token_consumed = False
    lock_acquired = False
    runner_invoked = False
    runner_result: Optional[dict[str, Any]] = None
    lock: SessionLockV1 | None = None
    session_id = str(runtime_session_id or session_request.get("session_id") or TARGET_SESSION_ID)
    auth_session_id = str(authorization_session_id or session_id)
    token_session_id = str(confirm_token_expected_session_id or session_id)
    token_scope = str(confirm_token_expected_scope_digest or SESSION_SCOPE)

    if GOVERNED_EXECUTION_BINDING_REAL_NETWORK_SIDE_EFFECTS_AUTHORIZED:
        blockers.append("PERMANENT_UNSCOPED_NETWORK_SIDE_EFFECTS_MUST_REMAIN_FALSE")
    if allow_real_network_side_effects:
        blockers.append("REAL_NETWORK_SIDE_EFFECTS_FORBIDDEN_IN_BINDING_CAPABILITY")
    if not network_allowed_from_authorization:
        blockers.append("NETWORK_ALLOWED_FROM_AUTHORIZATION_REQUIRED")
    if wallclock_runner is None:
        blockers.append("INJECTED_WALLCLOCK_RUNNER_REQUIRED_FOR_BINDING")

    boundary = prove_public_md_network_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend([f"NETWORK_BOUNDARY:{b}" for b in boundary.get("blockers") or []])
    if NETWORK_ALLOWLIST != "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY":
        blockers.append("PUBLIC_MD_ALLOWLIST_DRIFT")
    if HTTP_METHOD_ALLOWLIST != "GET_ONLY":
        blockers.append("HTTP_METHOD_ALLOWLIST_DRIFT")

    if blockers:
        return GovernedExecutionBindingResultV1(
            ok=False,
            blockers=sorted(set(blockers)),
            notes=notes + ["FAIL_CLOSED_BEFORE_SESSION_LOCK=true"],
            claims={
                "NETWORK_SESSION_EXECUTED": False,
                "REAL_NETWORK_REQUEST_COUNT": 0,
                "AUTHORIZATION_CONSUMED": False,
                "CONFIRM_TOKEN_CONSUMED": False,
                "SESSION_LOCK_ACQUIRED": False,
                "PRIVATE_ENDPOINT_REACHABLE": False,
                "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
                "ORDER_SIDE_EFFECT_REACHABLE": False,
            },
        )

    already = load_consumed_authorization_ids_from_ledger_v1(
        Path(persistence_root) / AUTHORIZATION_LEDGER_FILENAME
    )
    auth_check = validate_authorization_binding_v1(
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        expected_scope=authorization_scope,
        expected_session_id=auth_session_id,
        authorization_scope=authorization_scope,
        authorization_session_id=auth_session_id,
        authorization_repository_sha=expected_repository_sha,
        authorization_config_digest=expected_config_digest,
        already_consumed=authorization_id in already,
    )
    if not auth_check.get("ok"):
        blockers.extend([str(b) for b in auth_check.get("blockers") or []])
        blockers.append("AUTHORIZATION_VALIDATION_FAILED")
        return GovernedExecutionBindingResultV1(
            ok=False,
            blockers=sorted(set(blockers)),
            notes=notes + ["FAIL_CLOSED_BEFORE_SESSION_LOCK=true"],
            claims={
                "NETWORK_SESSION_EXECUTED": False,
                "AUTHORIZATION_CONSUMED": False,
                "CONFIRM_TOKEN_CONSUMED": False,
                "SESSION_LOCK_ACQUIRED": False,
            },
        )

    token_check = validate_confirm_token_binding_v1(
        **{
            "confirm_token": confirm_token_plaintext,
            "expected_binding_sha256": confirm_token_binding_sha256,
            "expected_repository_sha": expected_repository_sha,
            "expected_scope_digest": token_scope,
            "expected_session_id": token_session_id,
            "expires_at": float(confirm_token_expires_at),
            "argv": argv,
        }
    )
    token_fp = str(token_check.get("fingerprint") or "") or fingerprint_only_v1(
        confirm_token_plaintext
    )
    # Drop caller plaintext reference responsibility after fingerprinting.
    if not token_check.get("ok"):
        blockers.extend([str(b) for b in token_check.get("blockers") or []])
        blockers.append("CONFIRM_TOKEN_VALIDATION_FAILED")
        return GovernedExecutionBindingResultV1(
            ok=False,
            blockers=sorted(set(blockers)),
            notes=notes + ["FAIL_CLOSED_BEFORE_SESSION_LOCK=true"],
            claims={
                "NETWORK_SESSION_EXECUTED": False,
                "AUTHORIZATION_CONSUMED": False,
                "CONFIRM_TOKEN_CONSUMED": False,
                "SESSION_LOCK_ACQUIRED": False,
                "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            },
        )

    try:
        kwargs = build_canonical_wallclock_runner_kwargs_v1(session_request)
    except ValueError as exc:
        blockers.append(str(exc))
        return GovernedExecutionBindingResultV1(
            ok=False,
            blockers=sorted(set(blockers)),
            notes=notes + ["FAIL_CLOSED_BEFORE_SESSION_LOCK=true"],
            claims={"NETWORK_SESSION_EXECUTED": False, "AUTHORIZATION_CONSUMED": False},
        )

    # Force no real network side effects even if session_request carries True.
    invoke_kwargs = dict(kwargs)
    invoke_kwargs["use_real_network"] = False

    persistence = Path(persistence_root)
    persistence.mkdir(parents=True, exist_ok=True)
    lock_path = persistence / f"{session_id}.session.lock"
    lock = SessionLockV1(
        lock_path=lock_path,
        session_id=session_id,
        owner=SESSION_LOCK_OWNER,
    )
    try:
        lock.acquire()
        lock_acquired = True
        lock.assert_held()
    except SessionLockError as exc:
        blockers.append(f"SESSION_LOCK_FAILED:{exc}")
        return GovernedExecutionBindingResultV1(
            ok=False,
            blockers=sorted(set(blockers)),
            notes=notes + ["FAIL_CLOSED_AT_SESSION_LOCK=true"],
            session_lock_acquired=False,
            claims={
                "NETWORK_SESSION_EXECUTED": False,
                "AUTHORIZATION_CONSUMED": False,
                "CONFIRM_TOKEN_CONSUMED": False,
                "SESSION_LOCK_ACQUIRED": False,
            },
        )

    try:
        consume_authorization_binding_v1(
            ledger_path=persistence / AUTHORIZATION_LEDGER_FILENAME,
            authorization_id=authorization_id,
            authorization_digest=authorization_digest,
            session_id=session_id,
            now_unix=now_unix,
        )
        auth_consumed = True
        consume_confirm_token_binding_v1(
            ledger_path=persistence / CONFIRM_TOKEN_LEDGER_FILENAME,
            confirm_token_fingerprint=token_fp,
            session_id=session_id,
            now_unix=now_unix,
        )
        token_consumed = True

        assert wallclock_runner is not None
        raw_result = wallclock_runner(**invoke_kwargs)
        runner_invoked = True
        if isinstance(raw_result, Mapping):
            runner_result = {k: v for k, v in raw_result.items() if k != "confirm_token"}
        else:
            runner_result = {"ok": True, "stub": True}
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"BINDING_INVOKE_FAILED:{type(exc).__name__}")
        return GovernedExecutionBindingResultV1(
            ok=False,
            blockers=sorted(set(blockers)),
            notes=notes + ["FAIL_CLOSED_AFTER_PARTIAL_PROGRESS=true"],
            authorization_consumed=auth_consumed,
            confirm_token_consumed=token_consumed,
            session_lock_acquired=lock_acquired,
            wallclock_runner_invoked=runner_invoked,
            claims={
                "NETWORK_SESSION_EXECUTED": False,
                "REAL_NETWORK_REQUEST_COUNT": 0,
                "AUTHORIZATION_CONSUMED": auth_consumed,
                "CONFIRM_TOKEN_CONSUMED": token_consumed,
                "SESSION_LOCK_ACQUIRED": lock_acquired,
                "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            },
        )
    finally:
        if lock is not None and lock.acquired:
            lock.release()

    return GovernedExecutionBindingResultV1(
        ok=True,
        notes=notes
        + [
            "GOVERNED_EXECUTION_BINDING_PROVEN=true",
            "REAL_NETWORK_NOT_EXECUTED=true",
            "INJECTED_RUNNER_ONLY=true",
        ],
        authorization_consumed=auth_consumed,
        confirm_token_consumed=token_consumed,
        session_lock_acquired=lock_acquired,
        wallclock_runner_invoked=runner_invoked,
        network_session_executed=False,
        real_network_request_count=0,
        runner_result=runner_result,
        claims={
            "NETWORK_SESSION_EXECUTED": False,
            "REAL_NETWORK_REQUEST_COUNT": 0,
            "AUTHORIZATION_CONSUMED": auth_consumed,
            "CONFIRM_TOKEN_CONSUMED": token_consumed,
            "SESSION_LOCK_ACQUIRED": lock_acquired,
            "WALLCLOCK_RUNNER_INVOKED": runner_invoked,
            "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            "CONFIRM_TOKEN_PERSISTED": False,
            "PRIVATE_ENDPOINT_REACHABLE": False,
            "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
            "ORDER_SIDE_EFFECT_REACHABLE": False,
            "PUBLIC_MD_ALLOWLIST": NETWORK_ALLOWLIST,
            "HTTP_METHOD_ALLOWLIST": HTTP_METHOD_ALLOWLIST,
            "USE_REAL_NETWORK_FORCED_FALSE_IN_BINDING": True,
            "GOVERNED_EXECUTION_BINDING_CAPABILITY_ID": GOVERNED_EXECUTION_BINDING_CAPABILITY_ID,
        },
    )
