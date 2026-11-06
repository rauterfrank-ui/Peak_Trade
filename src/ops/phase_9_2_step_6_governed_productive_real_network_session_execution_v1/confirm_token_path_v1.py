"""Confirm-token argv/env rejection (no mint/consume in implementation prove path)."""

from __future__ import annotations

from typing import Mapping

from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.constants_v1 import (
    FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS,
    FORBIDDEN_CONFIRM_TOKEN_ENV_KEYS,
)


def reject_confirm_token_argv_v1(argv: list[str] | None = None) -> list[str]:
    blockers: list[str] = []
    if not argv:
        return blockers
    lowered = [str(a).lower() for a in argv]
    for flag in FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS:
        if flag.lower() in lowered:
            blockers.append(f"CONFIRM_TOKEN_ARGV_FORBIDDEN:{flag}")
    return blockers


def reject_confirm_token_env_fallback_v1(
    environ: Mapping[str, str] | None = None,
) -> list[str]:
    blockers: list[str] = []
    if environ is None:
        return blockers
    for key in FORBIDDEN_CONFIRM_TOKEN_ENV_KEYS:
        raw = environ.get(key)
        if raw is None:
            continue
        if str(raw).strip():
            blockers.append(f"CONFIRM_TOKEN_ENV_FORBIDDEN:{key}")
    return blockers
