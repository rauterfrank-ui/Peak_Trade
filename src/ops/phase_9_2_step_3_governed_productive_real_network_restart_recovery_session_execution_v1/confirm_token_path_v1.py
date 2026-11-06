"""Confirm-token path guards for Step-3 surface (no argv/env plaintext)."""

from __future__ import annotations

from typing import Mapping, Sequence

from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.constants_v1 import (
    FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS,
    FORBIDDEN_CONFIRM_TOKEN_ENV_KEYS,
)


def reject_confirm_token_argv_v1(argv: Sequence[str] | None) -> list[str]:
    if not argv:
        return []
    blockers: list[str] = []
    for token in argv:
        raw = str(token)
        flag = raw.split("=", 1)[0]
        if flag in FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS:
            blockers.append("CONFIRM_TOKEN_IN_ARGV_FORBIDDEN")
            break
        if raw.startswith("--confirm-token=") or raw.startswith("--confirm_token="):
            blockers.append("CONFIRM_TOKEN_IN_ARGV_FORBIDDEN")
            break
    return sorted(set(blockers))


def reject_confirm_token_env_fallback_v1(environ: Mapping[str, str] | None) -> list[str]:
    """Surface forbids env fallback; hidden PTY/stdin only for later sessions."""
    if not environ:
        return []
    blockers: list[str] = []
    for key in FORBIDDEN_CONFIRM_TOKEN_ENV_KEYS:
        if str(environ.get(key) or "").strip():
            blockers.append("CONFIRM_TOKEN_ENV_FALLBACK_FORBIDDEN")
            break
    if str(environ.get("PEAK_TRADE_PSO_CONFIRM_TOKEN") or "").strip():
        blockers.append("CONFIRM_TOKEN_ENV_FALLBACK_FORBIDDEN")
    return sorted(set(blockers))


def redact_confirm_token_mapping_v1(payload: Mapping[str, object]) -> dict[str, object]:
    """Strip plaintext confirm-token fields from operator-visible payloads."""
    out: dict[str, object] = {}
    forbidden_keys = {
        "confirm_token",
        "confirm_token_plaintext",
        "plaintext",
        "token_plaintext",
    }
    for key, value in payload.items():
        lk = str(key).lower()
        if lk in forbidden_keys or "plaintext" in lk and "confirm" in lk:
            continue
        if isinstance(value, dict):
            out[key] = redact_confirm_token_mapping_v1(value)
        else:
            out[key] = value
    return out
