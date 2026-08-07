"""Consume Step-3 surface validation without duplicating or weakening it."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.constants_v1 import (
    NETWORK_SESSION_ALLOWED as SURFACE_NETWORK_SESSION_ALLOWED,
    PRODUCTIVE_ENTRYPOINT_PATH as SURFACE_ENTRYPOINT_PATH,
    REAL_NETWORK_REQUESTS_ALLOWED as SURFACE_REAL_NETWORK_REQUESTS_ALLOWED,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.governed_execution_surface_v1 import (
    assemble_execution_request_v1 as surface_assemble_execution_request_v1,
    prove_step3_execution_surface_implementation_v1,
    request_real_network_fail_closed_v1 as surface_request_real_network_fail_closed_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.constants_v1 import (
    SURFACE_CLI_PATH,
    SURFACE_PACKAGE,
    repo_root_v1,
)


def consume_surface_implementation_proof_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Path | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    proof = prove_step3_execution_surface_implementation_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
        argv=argv,
        environ=environ,
    )
    payload = proof.to_dict()
    # Surface must remain fail-closed for real network.
    surface_refuse = surface_request_real_network_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        argv=argv,
        environ=environ,
    )
    refuse_payload = surface_refuse.to_dict()
    surface_unchanged_fail_closed = (
        (not surface_refuse.ok)
        and "REAL_NETWORK_FORBIDDEN_IN_SURFACE_IMPLEMENTATION" in list(surface_refuse.blockers)
        and SURFACE_NETWORK_SESSION_ALLOWED is False
        and SURFACE_REAL_NETWORK_REQUESTS_ALLOWED is False
    )
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    surface_cli = root / SURFACE_CLI_PATH
    return {
        "ok": bool(proof.ok) and surface_unchanged_fail_closed and surface_cli.is_file(),
        "blockers": list(proof.blockers)
        + ([] if surface_unchanged_fail_closed else ["SURFACE_FAIL_CLOSED_DRIFT"]),
        "surface_proof": payload,
        "surface_request_real_network": refuse_payload,
        "surface_package": SURFACE_PACKAGE,
        "surface_entrypoint": SURFACE_ENTRYPOINT_PATH,
        "surface_cli_path": SURFACE_CLI_PATH,
        "STEP3_EXECUTION_SURFACE_FOUND": surface_cli.is_file(),
        "STEP3_EXECUTION_SURFACE_CANONICAL": True,
        "STEP3_EXECUTION_SURFACE_RUNTIME_REACHABLE": bool(proof.ok),
        "STEP3_EXECUTION_SURFACE_UNCHANGED_FAIL_CLOSED": surface_unchanged_fail_closed,
        "SURFACE_NOT_DUPLICATED": True,
        "network_session_started": False,
    }


def consume_surface_assemble_request_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Path | None = None,
    authorization_id: str = "",
    authorization_digest: str = "",
    confirm_token_binding_sha256: str = "",
) -> dict[str, Any]:
    return surface_assemble_execution_request_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        confirm_token_binding_sha256=confirm_token_binding_sha256,
    )
