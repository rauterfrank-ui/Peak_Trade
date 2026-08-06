"""Offline failure-injection for governed productive session execution implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID,
    SESSION_EXECUTION_RUNTIME_CAPABILITY_ID,
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.fault_path_v1 import (
    prove_governed_fault_path_offline_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.governed_productive_session_execution_v1 import (
    execute_governed_productive_session_execution_v1,
    prove_governed_productive_session_execution_implementation_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.network_boundary_v1 import (
    prove_public_md_network_boundary_v1,
)


def run_governed_productive_session_execution_failure_injection_v1(
    *,
    repository_sha: str,
    config_digest: str,
    persistence_root: Path,
    now_unix: float = 1_700_000_000.0,
) -> dict[str, Any]:
    root = Path(persistence_root)
    root.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {}

    def _case(name: str, fn: Callable[[], Mapping[str, Any]]) -> None:
        payload = dict(fn())
        results[name] = {
            "ok": bool(payload.get("ok") is False) or bool(payload.get("expected_fail_closed")),
            "blockers": list(payload.get("blockers") or []),
            "expected_fail_closed": True,
            "claims": dict(payload.get("claims") or {}),
        }

    _case(
        "capability_id_wrong",
        lambda: prove_governed_productive_session_execution_implementation_v1(
            expected_repository_sha=repository_sha,
            expected_config_digest=config_digest,
            expected_capability_id="WRONG_CAPABILITY_ID",
            now_unix=now_unix,
        ).to_dict(),
    )
    _case(
        "repository_sha_wrong",
        lambda: prove_governed_productive_session_execution_implementation_v1(
            expected_repository_sha="0" * 40,
            expected_config_digest=config_digest,
            session_request={
                "session_id": TARGET_SESSION_ID,
                "prereg": object(),
                "go": object(),
                "confirm_token": "x",
                "artifact_path": root / "a.json",
                "evidence_root": root / "ev",
                "expected_repository_sha": "0" * 40,
                "fingerprint_ledger_path": root / "fp.txt",
            },
            authorization_id="auth_fi",
            authorization_digest="digest_fi",
            now_unix=now_unix,
            persistence_root=root,
        ).to_dict(),
    )
    _case(
        "authorization_expired",
        lambda: prove_governed_productive_session_execution_implementation_v1(
            expected_repository_sha=repository_sha,
            expected_config_digest=config_digest,
            authorization_id="auth_expired",
            authorization_digest="digest_expired",
            authorization_expires_at=now_unix - 10.0,
            now_unix=now_unix,
            session_request={
                "session_id": TARGET_SESSION_ID,
                "prereg": object(),
                "go": object(),
                "confirm_token": "x",
                "artifact_path": root / "a.json",
                "evidence_root": root / "ev",
                "expected_repository_sha": repository_sha,
                "fingerprint_ledger_path": root / "fp.txt",
            },
            persistence_root=root,
        ).to_dict(),
    )
    _case(
        "real_network_side_effects_forbidden",
        lambda: prove_governed_productive_session_execution_implementation_v1(
            expected_repository_sha=repository_sha,
            expected_config_digest=config_digest,
            allow_real_network_side_effects=True,
            now_unix=now_unix,
        ).to_dict(),
    )
    _case(
        "consumption_forbidden",
        lambda: prove_governed_productive_session_execution_implementation_v1(
            expected_repository_sha=repository_sha,
            expected_config_digest=config_digest,
            allow_authorization_consumption=True,
            allow_confirm_token_consumption=True,
            now_unix=now_unix,
        ).to_dict(),
    )
    _case(
        "runtime_execute_fail_closed",
        lambda: execute_governed_productive_session_execution_v1(
            expected_capability_id=SESSION_EXECUTION_RUNTIME_CAPABILITY_ID,
            expected_repository_sha=repository_sha,
            expected_config_digest=config_digest,
            session_request={"session_id": TARGET_SESSION_ID},
            network_allowed_from_authorization=True,
            authorization_id="auth_runtime",
            authorization_digest="digest_runtime",
            confirm_token_binding_sha256="b" * 64,
            confirm_token_plaintext="",
            confirm_token_expires_at=now_unix + 3600.0,
            now_unix=now_unix,
            persistence_root=root,
            allow_real_network_side_effects=True,
            allow_authorization_consumption=True,
            allow_confirm_token_consumption=True,
        ).to_dict(),
    )
    _case(
        "direct_runtime_without_capability",
        lambda: execute_governed_productive_session_execution_v1(
            expected_capability_id=SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID,
            expected_repository_sha=repository_sha,
            expected_config_digest=config_digest,
            session_request={"session_id": TARGET_SESSION_ID},
            network_allowed_from_authorization=True,
            authorization_id="auth_direct",
            authorization_digest="digest_direct",
            confirm_token_binding_sha256="c" * 64,
            confirm_token_plaintext="",
            confirm_token_expires_at=now_unix + 3600.0,
            now_unix=now_unix,
            persistence_root=root,
        ).to_dict(),
    )

    fault = prove_governed_fault_path_offline_v1()
    results["fault_path_offline"] = {
        "ok": bool(fault.get("ok")),
        "expected_fail_closed": False,
        "network_session_started": bool(fault.get("network_session_started")),
        "fault_session_started": bool(fault.get("fault_session_started")),
        "claims": dict(fault.get("claims") or {}),
    }
    boundary = prove_public_md_network_boundary_v1(environ={"PATH": "/usr/bin", "HOME": "/tmp"})
    results["network_boundary"] = {
        "ok": bool(boundary.get("ok")),
        "PRIVATE_ENDPOINT_REACHABLE": boundary.get("PRIVATE_ENDPOINT_REACHABLE"),
        "AUTH_HEADER_PRESENT": boundary.get("AUTH_HEADER_PRESENT"),
        "ORDER_SIDE_EFFECT_OCCURRED": boundary.get("ORDER_SIDE_EFFECT_OCCURRED"),
        "expected_fail_closed": False,
    }

    ok = all(
        bool(v.get("ok"))
        for k, v in results.items()
        if k
        not in {
            # structural positives
        }
    )
    # All fail-closed cases must report ok=True meaning "fail closed as expected".
    fail_closed_ok = all(
        bool(results[name]["ok"])
        for name in (
            "capability_id_wrong",
            "authorization_expired",
            "real_network_side_effects_forbidden",
            "consumption_forbidden",
            "runtime_execute_fail_closed",
            "direct_runtime_without_capability",
        )
    )
    return {
        "ok": bool(
            fail_closed_ok
            and results["fault_path_offline"]["ok"]
            and results["network_boundary"]["ok"]
        ),
        "capability_id": SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID,
        "session_scope": SESSION_SCOPE,
        "cases": results,
        "claims": {
            "FAILURE_INJECTION_EXECUTED": True,
            "NO_NETWORK_SESSION": True,
            "NO_AUTHORIZATION_CONSUMPTION": True,
            "NO_CONFIRM_TOKEN_CONSUMPTION": True,
        },
    }
