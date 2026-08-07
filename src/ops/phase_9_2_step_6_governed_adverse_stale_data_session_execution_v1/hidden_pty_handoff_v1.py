"""Hidden-PTY confirm-token handoff for Step-6 governed session execution."""

from __future__ import annotations

import hashlib
import sys
from typing import Any, Callable, Mapping

from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.constants_v1 import (
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    CONFIRM_TOKEN_ISSUANCE_ALLOWED,
    CONFIRM_TOKEN_OWNER,
    HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
)


def fingerprint_only_v1(plaintext: str) -> str:
    return hashlib.sha256(str(plaintext).encode("utf-8")).hexdigest()


def prove_hidden_pty_confirm_handoff_binding_v1() -> dict[str, Any]:
    return {
        "ok": True,
        "issuance_owner": CONFIRM_TOKEN_OWNER,
        "handoff_owner": HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
        "consumption_path": "canonical_hidden_pty_stdin_only",
        "real_tty_required": True,
        "single_use": True,
        "plaintext_persistence": False,
        "plaintext_argv": False,
        "plaintext_env": False,
        "plaintext_log": False,
        "plaintext_shell_history": False,
        "piped_stdin_without_tty_forbidden": True,
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
            "REAL_TTY_REQUIRED_FOR_SESSION_MODE=true",
        ],
    }


def assert_real_tty_v1(*, stdin_isatty: bool | None = None) -> list[str]:
    tty = bool(sys.stdin.isatty()) if stdin_isatty is None else bool(stdin_isatty)
    if not tty:
        return ["REAL_TTY_REQUIRED", "HIDDEN_PTY_STDIN_NOT_TTY"]
    return []


def acquire_confirm_token_via_hidden_pty_v1(
    *,
    getpass_fn: Callable[[str], str] | None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    require_real_tty: bool = True,
    stdin_isatty: bool | None = None,
) -> dict[str, Any]:
    """Acquire plaintext only via getpass (hidden PTY/stdin). Never persist."""
    blockers: list[str] = []
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))
    if CONFIRM_TOKEN_ISSUANCE_ALLOWED:
        blockers.append("CONFIRM_TOKEN_ISSUANCE_MUST_REMAIN_FALSE")
    if require_real_tty:
        blockers.extend(assert_real_tty_v1(stdin_isatty=stdin_isatty))
    if getpass_fn is None:
        blockers.append("CONFIRM_TOKEN_MISSING")
        return {
            "ok": False,
            "blockers": sorted(set(blockers)),
            "plaintext": "",
            "fingerprint": "",
            "confirm_token_consumed": False,
        }
    if blockers:
        return {
            "ok": False,
            "blockers": sorted(set(blockers)),
            "plaintext": "",
            "fingerprint": "",
            "confirm_token_consumed": False,
        }
    try:
        plaintext = str(getpass_fn("confirm-token: ") or "")
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "blockers": [f"CONFIRM_TOKEN_HANDOFF_FAILED:{type(exc).__name__}"],
            "plaintext": "",
            "fingerprint": "",
            "confirm_token_consumed": False,
        }
    if not plaintext.strip():
        return {
            "ok": False,
            "blockers": ["CONFIRM_TOKEN_MISSING"],
            "plaintext": "",
            "fingerprint": "",
            "confirm_token_consumed": False,
        }
    return {
        "ok": True,
        "blockers": [],
        "plaintext": plaintext,
        "fingerprint": fingerprint_only_v1(plaintext),
        "handoff_owner": HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
        "confirm_token_consumed": False,
    }


def validate_confirm_token_binding_v1(
    *,
    confirm_token_plaintext: str,
    expected_binding_sha256: str,
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
        blockers.append("CONFIRM_TOKEN_INVALID")
    if already_consumed:
        blockers.append("CONFIRM_TOKEN_ALREADY_CONSUMED")
    fp = fingerprint_only_v1(token) if token else ""
    binding = str(expected_binding_sha256 or "").strip().lower()
    if not binding:
        blockers.append("CONFIRM_TOKEN_BINDING_SHA_MISSING")
        blockers.append("CONFIRM_TOKEN_INVALID")
    elif token and binding not in {fp, hashlib.sha256(token.encode()).hexdigest()}:
        if binding != fp:
            blockers.append("CONFIRM_TOKEN_DIGEST_MISMATCH")
            blockers.append("CONFIRM_TOKEN_INVALID")
    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "confirm_token_id": f"tok_{fp[:16]}" if fp else "",
        "fingerprint": fp,
        "binding_sha256": binding,
        "consumed_status": "ALREADY_CONSUMED" if already_consumed else "NOT_CONSUMED",
        "issuance_owner": CONFIRM_TOKEN_OWNER,
        "handoff_owner": HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
        "plaintext_persisted": False,
        "plaintext_exposed": False,
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
