"""Fail-closed binding gate for real Public-MD restart wallclock path.

Unlock requires bound ACTIVE Session-GO + Owner-GO + Owner-Session-GO +
segment authorization present + confirm-token via canonical path.
Permanent PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED remains false.
Env-alone never unlocks.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.confirm_token_path_v1 import (
    confirm_token_present_via_canonical_path_v1,
    reject_confirm_token_argv_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.constants_v1 import (
    AUTHORITY_OWNER,
    CANONICAL_WALLCLOCK_RUNNER,
    CAPABILITY_ID,
    NETWORK_SESSION_ALLOWED_BY_CAPABILITY_CONFIG,
    NO_PERMANENT_UNSCOPED_ENABLE_FLAG,
    PRODUCTIVE_ENTRYPOINT_ID,
    PRODUCTIVE_ENTRYPOINT_PATH,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    REAL_NETWORK_ENV,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.models_v1 import (
    BindingGateResultV1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.gate_v1 import (
    evaluate_session_go_gate_v1,
)


def evaluate_real_network_wallclock_binding_gate_v1(
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
    ]
    blockers: list[str] = []

    argv_blockers = reject_confirm_token_argv_v1(argv)
    blockers.extend(argv_blockers)

    if (
        PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED
        or NETWORK_SESSION_ALLOWED_BY_CAPABILITY_CONFIG
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
            real_public_md_network_path_bound=True,
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
    notes.extend(list(gate.notes))
    blockers.extend(list(gate.blockers))

    authority = gate.authority
    if authority is not None and request_real_network:
        if not bool(authority.network_session_execution_authorized_by_this_go):
            blockers.append("SESSION_GO_NETWORK_EXECUTION_NOT_AUTHORIZED_BY_THIS_GO")

    real_network_may = (
        bool(gate.ok)
        and bool(gate.productive_session_execution_permitted)
        and bool(gate.network_may_proceed)
        and request_real_network
        and authority is not None
        and bool(authority.network_session_execution_authorized_by_this_go)
        and not blockers
    )

    result = BindingGateResultV1(
        ok=(not blockers) and bool(gate.ok),
        blockers=sorted(set(blockers)),
        notes=notes
        + [
            "REAL_PUBLIC_MD_RESTART_BINDING_IMPLEMENTED=true",
            f"REQUEST_REAL_NETWORK={request_real_network}",
        ],
        real_public_md_network_path_bound=True,
        session_go_authority_satisfied=bool(gate.session_go_authority_satisfied),
        productive_session_execution_permitted=bool(gate.productive_session_execution_permitted),
        real_network_may_proceed=bool(real_network_may),
        authorization_may_proceed=bool(gate.authorization_may_proceed),
        confirm_token_path_ok=confirm_ok,
        network_session_started=False,
    )
    if request_real_network and not real_network_may and "SESSION_GO_MISSING" not in blockers:
        if not result.blockers:
            result.blockers = ["REAL_NETWORK_BINDING_GATES_NOT_SATISFIED"]
            result.ok = False
    return result


def assert_no_parallel_productive_authority_v1() -> dict[str, Any]:
    """Reuse-before-new inventory: sole wallclock + restart surfaces."""
    return {
        "ok": True,
        "parallel_productive_authority_detected": False,
        "canonical_wallclock_runner": CANONICAL_WALLCLOCK_RUNNER,
        "productive_entrypoint_id": PRODUCTIVE_ENTRYPOINT_ID,
        "productive_entrypoint_path": PRODUCTIVE_ENTRYPOINT_PATH,
        "notes": [
            "REUSES_PR5665_RESTART_HARNESS",
            "REUSES_PR5666_ENTRYPOINT_IDENTITY",
            "REUSES_PR5667_SESSION_GO",
            "REUSES_PR5668_POST_UNLOCK_PATTERN",
            "NO_SECOND_WALLCLOCK_RUNNER",
        ],
    }
