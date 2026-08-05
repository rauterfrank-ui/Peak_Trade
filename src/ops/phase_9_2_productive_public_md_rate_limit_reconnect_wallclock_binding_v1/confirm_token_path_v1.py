"""Canonical confirm-token path guards (no argv plaintext)."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS,
)


def reject_confirm_token_argv_v1(argv: Sequence[str] | None) -> list[str]:
    """Fail-closed if confirm-token plaintext is supplied via argv flags."""
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


def confirm_token_present_via_canonical_path_v1(
    *,
    confirm_token_file: Path | None,
    environ: Mapping[str, str] | None,
    confirm_token_present_flag: bool = False,
) -> bool:
    if confirm_token_present_flag:
        return True
    if confirm_token_file is not None and Path(confirm_token_file).is_file():
        return True
    env = environ or {}
    if str(env.get("PEAK_TRADE_PSO_CONFIRM_TOKEN") or "").strip():
        return True
    return False
