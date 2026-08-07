"""Confirm-token path guards for Step-6 execution (no argv/env plaintext)."""

from __future__ import annotations

from typing import Mapping, Sequence

from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.constants_v1 import (
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
    if not environ:
        return []
    blockers: list[str] = []
    for key in FORBIDDEN_CONFIRM_TOKEN_ENV_KEYS:
        if str(environ.get(key) or "").strip():
            blockers.append("CONFIRM_TOKEN_ENV_FALLBACK_FORBIDDEN")
            break
    return sorted(set(blockers))
