"""Verifier for post-unlock runtime invocation evidence/manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.constants_v1 import (  # noqa: E501
    CANONICAL_RUNTIME_RUNNER,
    CAPABILITY_ID,
    INVOCATION_MANIFEST_FILENAME,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.digest_v1 import (  # noqa: E501
    read_json_v1,
)


def verify_post_unlock_invocation_manifest_v1(
    *,
    persistence_root: Path,
    expected_ok: bool | None = None,
) -> dict[str, Any]:
    """Fail-closed verifier: missing runtime invocation / consume / lock is rejected."""
    root = Path(persistence_root)
    path = root / INVOCATION_MANIFEST_FILENAME
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        f"CANONICAL_RUNTIME_RUNNER={CANONICAL_RUNTIME_RUNNER}",
        "CLAIMS_MUST_MATCH_TELEMETRY=true",
    ]
    if not path.is_file():
        return {
            "ok": False,
            "verified": False,
            "blockers": ["INVOCATION_MANIFEST_MISSING"],
            "notes": notes,
            "claims_match_telemetry": False,
        }

    payload = read_json_v1(path)
    if str(payload.get("session_id") or "") != TARGET_SESSION_ID:
        blockers.append("SESSION_ID_MISMATCH")

    claims = dict(payload.get("claims") or {})
    telemetry_ok = True

    if bool(payload.get("ok")):
        required_true = (
            "canonical_runner_invoked",
            "authorization_consumed",
            "authorization_consumed_exactly_once",
            "session_lock_acquired",
            "session_lock_released",
            "restart_recovery_completed",
            "reconciliation_before_alpha",
        )
        for key in required_true:
            if not bool(payload.get(key)):
                blockers.append(f"PASS_MANIFEST_MISSING_{key.upper()}")
                telemetry_ok = False
        if int(payload.get("canonical_runner_invocation_count") or 0) != 1:
            blockers.append("PASS_MANIFEST_RUNNER_COUNT_NOT_ONE")
            telemetry_ok = False
        if bool(payload.get("network_session_started")):
            blockers.append("PASS_MANIFEST_NETWORK_SESSION_STARTED_TRUE")
            telemetry_ok = False
        if claims.get("PARALLEL_RUNNER_ADDED") is True:
            blockers.append("PARALLEL_RUNNER_CLAIMED")
            telemetry_ok = False
        if claims.get("AUTHORIZATION_CONSUMED_EXACTLY_ONCE") is not True:
            blockers.append("CLAIM_CONSUME_ONCE_MISMATCH")
            telemetry_ok = False
        if claims.get("AUTHORIZATION_CONSUMED_EXACTLY_ONCE") != bool(
            payload.get("authorization_consumed_exactly_once")
        ):
            blockers.append("CLAIM_TELEMETRY_CONSUME_MISMATCH")
            telemetry_ok = False
    else:
        # Fail/abort manifests must not claim a successful runner handoff without telemetry.
        if (
            bool(payload.get("canonical_runner_invoked"))
            and int(payload.get("canonical_runner_invocation_count") or 0) < 1
        ):
            blockers.append("FAIL_MANIFEST_RUNNER_CLAIM_WITHOUT_COUNT")
            telemetry_ok = False

    if expected_ok is not None and bool(payload.get("ok")) != bool(expected_ok):
        blockers.append("EXPECTED_OK_MISMATCH")

    # Reject surgically manipulated claim sets.
    if (
        "POST_UNLOCK_RUNTIME_INVOCATION_ADDED" in claims
        and claims.get("POST_UNLOCK_RUNTIME_INVOCATION_ADDED") is not True
    ):
        blockers.append("INVOCATION_CLAIM_FALSE")

    ok = not blockers and telemetry_ok
    return {
        "ok": ok,
        "verified": ok,
        "blockers": sorted(set(blockers)),
        "notes": notes,
        "claims_match_telemetry": telemetry_ok and not blockers,
        "manifest": payload if isinstance(payload, Mapping) else {},
    }
