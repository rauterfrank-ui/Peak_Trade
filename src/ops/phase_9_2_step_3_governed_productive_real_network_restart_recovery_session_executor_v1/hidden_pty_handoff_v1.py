"""Hidden-PTY confirm-token handoff + digest/ID-only validation for Step-3 executor."""

from __future__ import annotations

import hashlib
from typing import Any, Callable, Mapping

from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.constants_v1 import (
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    CONFIRM_TOKEN_ISSUANCE_ALLOWED,
    CONFIRM_TOKEN_OWNER,
    HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.digest_v1 import (
    sha256_canonical_v1,
)


def fingerprint_only_v1(plaintext: str) -> str:
    return hashlib.sha256(str(plaintext).encode("utf-8")).hexdigest()


def prove_hidden_pty_confirm_handoff_binding_v1() -> dict[str, Any]:
    return {
        "ok": True,
        "issuance_owner": CONFIRM_TOKEN_OWNER,
        "handoff_owner": HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
        "consumption_path": "canonical_hidden_pty_stdin_only",
        "single_use": True,
        "plaintext_persistence": False,
        "plaintext_argv": False,
        "plaintext_env": False,
        "plaintext_log": False,
        "plaintext_shell_history": False,
        "evidence_fields": [
            "confirm_token_id",
            "fingerprint",
            "binding_sha256",
            "scope_digest",
            "consumed_status",
        ],
        "confirm_token_issued": False,
        "confirm_token_consumed": False,
        "notes": [
            "CANONICAL_ISSUANCE_PATH_ONLY=true",
            "HIDDEN_PTY_STDIN_ONLY=true",
            "NO_ARGV_NO_ENV_FALLBACK=true",
        ],
    }


def acquire_confirm_token_via_hidden_pty_v1(
    *,
    getpass_fn: Callable[[str], str] | None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))
    if CONFIRM_TOKEN_ISSUANCE_ALLOWED:
        blockers.append("CONFIRM_TOKEN_ISSUANCE_MUST_REMAIN_FALSE")
    if getpass_fn is None:
        blockers.append("CONFIRM_TOKEN_MISSING")
        return {"ok": False, "blockers": blockers, "plaintext": "", "fingerprint": ""}
    if blockers:
        return {"ok": False, "blockers": blockers, "plaintext": "", "fingerprint": ""}
    try:
        plaintext = str(getpass_fn("confirm-token: ") or "")
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "blockers": [f"CONFIRM_TOKEN_HANDOFF_FAILED:{type(exc).__name__}"],
            "plaintext": "",
            "fingerprint": "",
        }
    if not plaintext.strip():
        return {
            "ok": False,
            "blockers": ["CONFIRM_TOKEN_MISSING"],
            "plaintext": "",
            "fingerprint": "",
        }
    return {
        "ok": True,
        "blockers": [],
        "plaintext": plaintext,
        "fingerprint": fingerprint_only_v1(plaintext),
        "handoff_owner": HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
    }


def validate_confirm_token_binding_v1(
    *,
    confirm_token_plaintext: str,
    expected_binding_sha256: str,
    expected_repository_sha: str,
    expected_session_contract_digest: str,
    expected_binding_config_digest: str,
    expected_session_id: str = TARGET_SESSION_ID,
    expected_scope: str = SESSION_SCOPE,
    expires_at: float,
    now_unix: float,
    already_consumed: bool = False,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))
    if CONFIRM_TOKEN_CONSUMPTION_ALLOWED:
        blockers.append("CONFIRM_TOKEN_CONSUMPTION_MUST_REMAIN_FALSE_IN_CONSTANTS")
    token = str(confirm_token_plaintext or "")
    if not token.strip():
        blockers.append("CONFIRM_TOKEN_MISSING")
    if already_consumed:
        blockers.append("CONFIRM_TOKEN_ALREADY_CONSUMED")
    if float(now_unix) > float(expires_at):
        blockers.append("CONFIRM_TOKEN_EXPIRED")
    binding = str(expected_binding_sha256 or "").strip().lower()
    if not binding:
        blockers.append("CONFIRM_TOKEN_BINDING_SHA_MISSING")
    fp = fingerprint_only_v1(token) if token else ""
    if binding and token and binding not in {fp, hashlib.sha256(token.encode()).hexdigest()}:
        if binding != fp:
            blockers.append("CONFIRM_TOKEN_DIGEST_MISMATCH")

    scope_digest = sha256_canonical_v1(
        {
            "session_id": expected_session_id,
            "scope": expected_scope,
            "repository_sha": expected_repository_sha,
            "session_contract_digest": expected_session_contract_digest,
            "binding_config_digest": expected_binding_config_digest,
        }
    )
    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "confirm_token_id": f"tok_{fp[:16]}" if fp else "",
        "fingerprint": fp,
        "binding_sha256": binding,
        "scope_digest": scope_digest,
        "consumed_status": "ALREADY_CONSUMED" if already_consumed else "NOT_CONSUMED",
        "issuance_owner": CONFIRM_TOKEN_OWNER,
        "handoff_owner": HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
        "plaintext_persisted": False,
        "plaintext_exposed": False,
        "notes": [
            "CONFIRM_TOKEN_VALIDATE_ONLY=true",
            "EVIDENCE_FIELDS_DIGEST_ID_ONLY=true",
        ],
    }


def redact_confirm_token_mapping_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    forbidden = {
        "confirm_token",
        "token_plaintext",
        "raw_token",
        "plaintext",
        "confirm_token_plaintext",
    }
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if str(key).lower() in forbidden:
            out[key] = "[REDACTED]"
        elif isinstance(value, Mapping):
            out[key] = redact_confirm_token_mapping_v1(value)
        else:
            out[key] = value
    return out
