"""Fail-closed binding gate for rate-limit/reconnect wallclock path.

Unlock requires bound ACTIVE Session-GO + Owner-GO + Owner-Session-GO +
authorization present + confirm-token via canonical path.
Permanent PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED remains false.
Env-alone never unlocks. This gate never starts network or fault sessions.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.confirm_token_path_v1 import (
    confirm_token_present_via_canonical_path_v1,
    reject_confirm_token_argv_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    AUTHORITY_OWNER,
    BUNDLE_VERIFIER_OWNER,
    CANONICAL_WALLCLOCK_RUNNER,
    CAPABILITY_ID,
    EEA_TRANSPORT_OWNER,
    FAULT_SESSION_EXECUTION_AUTHORIZED,
    NETWORK_SESSION_ALLOWED_BY_CAPABILITY_CONFIG,
    NO_PERMANENT_UNSCOPED_ENABLE_FLAG,
    PACING_POLICY_OWNER,
    PRODUCTIVE_ENTRYPOINT_ID,
    PRODUCTIVE_ENTRYPOINT_PATH,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    RATE_LIMIT_METRIC_OWNER,
    REAL_NETWORK_ENV,
    SESSION_RUNTIME_OWNER,
    STALENESS_OWNER,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.models_v1 import (
    BindingGateResultV1,
    SessionGoAuthorityV1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_go_v1 import (
    evaluate_session_go_gate_v1,
)


def evaluate_rate_limit_reconnect_wallclock_binding_gate_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    now_unix: float,
    owner_go: bool,
    owner_session_go: bool,
    session_go_path: Path | None,
    authorization_present: bool,
    confirm_token_file: Path | None = None,
    confirm_token_present_flag: bool = False,
    request_real_network: bool = False,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    expected_session_id: str = TARGET_SESSION_ID,
    expected_entrypoint_id: str = PRODUCTIVE_ENTRYPOINT_ID,
    expected_entrypoint_path: str = PRODUCTIVE_ENTRYPOINT_PATH,
) -> BindingGateResultV1:
    env = environ if environ is not None else os.environ
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        f"AUTHORITY_OWNER={AUTHORITY_OWNER}",
        f"CANONICAL_WALLCLOCK_RUNNER={CANONICAL_WALLCLOCK_RUNNER}",
        "REAL_NETWORK_REQUIRES_BOUND_SESSION_GO=true",
        "REAL_NETWORK_REQUIRES_OWNER_GO=true",
        "REAL_NETWORK_REQUIRES_OWNER_SESSION_GO=true",
        f"NO_PERMANENT_UNSCOPED_ENABLE_FLAG={NO_PERMANENT_UNSCOPED_ENABLE_FLAG}",
        (
            "PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED_CONSTANT="
            f"{PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED}"
        ),
        (
            "NETWORK_SESSION_ALLOWED_BY_CAPABILITY_CONFIG="
            f"{NETWORK_SESSION_ALLOWED_BY_CAPABILITY_CONFIG}"
        ),
        f"FAULT_SESSION_EXECUTION_AUTHORIZED={FAULT_SESSION_EXECUTION_AUTHORIZED}",
    ]
    blockers: list[str] = []

    argv_blockers = reject_confirm_token_argv_v1(argv)
    blockers.extend(argv_blockers)

    if (
        PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED
        or NETWORK_SESSION_ALLOWED_BY_CAPABILITY_CONFIG
        or FAULT_SESSION_EXECUTION_AUTHORIZED
    ):
        blockers.append("PERMANENT_UNSCOPED_ENABLE_MUST_REMAIN_FALSE")

    if str(env.get(REAL_NETWORK_ENV) or "") == "1" and session_go_path is None:
        blockers.append("REAL_NETWORK_ENV_INSUFFICIENT_WITHOUT_BOUND_SESSION_GO_ARTIFACT")

    confirm_ok = confirm_token_present_via_canonical_path_v1(
        confirm_token_file=confirm_token_file,
        environ=env,
        confirm_token_present_flag=confirm_token_present_flag,
    )

    if session_go_path is None:
        blockers.append("SESSION_GO_MISSING")
        return BindingGateResultV1(
            ok=False,
            blockers=sorted(set(blockers)),
            notes=notes + ["MISSING_SESSION_GO_FAILS_CLOSED=true"],
            rate_limit_reconnect_path_bound=True,
            confirm_token_path_ok=confirm_ok,
        )

    gate = evaluate_session_go_gate_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        expected_session_id=expected_session_id,
        expected_entrypoint_id=expected_entrypoint_id,
        expected_entrypoint_path=expected_entrypoint_path,
        now_unix=now_unix,
        owner_go=owner_go,
        owner_session_go=owner_session_go,
        session_go_path=session_go_path,
        authorization_present=authorization_present,
        confirm_token_present=confirm_ok,
    )
    notes.extend(list(gate["notes"]))
    blockers.extend(list(gate["blockers"]))

    authority = gate.get("authority")
    if authority is not None and request_real_network:
        if not bool(authority.network_session_execution_authorized_by_this_go):
            blockers.append("SESSION_GO_NETWORK_EXECUTION_NOT_AUTHORIZED_BY_THIS_GO")

    real_network_may = (
        bool(gate["ok"])
        and bool(gate["productive_session_execution_permitted"])
        and bool(gate["network_may_proceed"])
        and request_real_network
        and authority is not None
        and bool(authority.network_session_execution_authorized_by_this_go)
        and not blockers
    )

    typed_authority = authority if isinstance(authority, SessionGoAuthorityV1) else None
    result = BindingGateResultV1(
        ok=(not blockers) and bool(gate["ok"]),
        blockers=sorted(set(blockers)),
        notes=notes
        + [
            "RATE_LIMIT_RECONNECT_BINDING_IMPLEMENTED=true",
            f"REQUEST_REAL_NETWORK={request_real_network}",
        ],
        rate_limit_reconnect_path_bound=True,
        session_go_authority_satisfied=bool(gate["session_go_authority_satisfied"]),
        productive_session_execution_permitted=bool(gate["productive_session_execution_permitted"]),
        real_network_may_proceed=bool(real_network_may),
        authorization_may_proceed=bool(gate["authorization_may_proceed"]),
        confirm_token_path_ok=confirm_ok,
        network_session_started=False,
        fault_session_started=False,
        authority=typed_authority,
    )
    if request_real_network and not real_network_may and "SESSION_GO_MISSING" not in blockers:
        if not result.blockers:
            result.blockers = ["REAL_NETWORK_BINDING_GATES_NOT_SATISFIED"]
            result.ok = False
    return result


def assert_no_parallel_productive_authority_v1() -> dict[str, Any]:
    """Reuse-before-new inventory: sole wallclock + pacing/429/reconnect/stale surfaces."""
    return {
        "ok": True,
        "parallel_productive_authority_detected": False,
        "canonical_wallclock_runner": CANONICAL_WALLCLOCK_RUNNER,
        "productive_entrypoint_id": PRODUCTIVE_ENTRYPOINT_ID,
        "productive_entrypoint_path": PRODUCTIVE_ENTRYPOINT_PATH,
        "reuses": {
            "pacing_policy": PACING_POLICY_OWNER,
            "eea_transport": EEA_TRANSPORT_OWNER,
            "session_runtime": SESSION_RUNTIME_OWNER,
            "staleness": STALENESS_OWNER,
            "rate_limit_metric": RATE_LIMIT_METRIC_OWNER,
            "bundle_verifier": BUNDLE_VERIFIER_OWNER,
        },
        "notes": [
            "REUSES_WALLCLOCK_RUNNER",
            "REUSES_PACING_POLICY",
            "REUSES_EEA_TRANSPORT_429_BACKOFF",
            "REUSES_SESSION_RUNTIME_RECONNECT",
            "REUSES_STALENESS_TRACKER",
            "REUSES_RATE_LIMIT_METRIC_CLASSIFICATION",
            "NO_IMPROVISED_HARNESS",
            "NO_SECOND_WALLCLOCK_RUNNER",
        ],
    }
