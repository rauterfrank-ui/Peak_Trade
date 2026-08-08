"""Hidden-confirm digest binding for §11.12.8 productive path (no plaintext)."""

from __future__ import annotations

import hashlib
import re
from typing import Mapping

from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_path_v1.constants_v1 import (
    FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS,
    FORBIDDEN_CONFIRM_TOKEN_ENV_KEYS,
)

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class Productive11128ConfirmTokenBindingError(RuntimeError):
    """Fail-closed confirm-token binding violation."""


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


def digest_confirm_token_v1(*, plaintext: str) -> str:
    """Compute SHA-256 digest. Callers must not log/persist plaintext."""
    if not plaintext or not str(plaintext).strip():
        raise Productive11128ConfirmTokenBindingError("CONFIRM_TOKEN_PLAINTEXT_EMPTY")
    return hashlib.sha256(str(plaintext).encode("utf-8")).hexdigest()


def bind_confirm_token_digest_v1(
    *,
    confirm_token_digest: str,
    expected_confirm_token_digest: str | None = None,
    plaintext: str | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Bind digest-only confirm token. Rejects plaintext persistence/argv/env leaks."""
    blockers = reject_confirm_token_argv_v1(argv)
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))
    if plaintext is not None:
        raise Productive11128ConfirmTokenBindingError(
            "CONFIRM_TOKEN_PLAINTEXT_FORBIDDEN_IN_BINDING"
        )
    digest = str(confirm_token_digest or "").strip().lower()
    if not _HEX64.match(digest):
        raise Productive11128ConfirmTokenBindingError("CONFIRM_TOKEN_DIGEST_INVALID")
    if expected_confirm_token_digest is not None:
        expected = str(expected_confirm_token_digest).strip().lower()
        if not _HEX64.match(expected):
            raise Productive11128ConfirmTokenBindingError("CONFIRM_TOKEN_EXPECTED_DIGEST_INVALID")
        if digest != expected:
            raise Productive11128ConfirmTokenBindingError("CONFIRM_TOKEN_DIGEST_MISMATCH")
    if blockers:
        raise Productive11128ConfirmTokenBindingError(";".join(blockers))
    return {
        "confirm_token_digest_bound": True,
        "confirm_token_digest": digest,
        "confirm_token_plaintext_persisted": False,
        "confirm_token_minted": False,
        "confirm_token_consumed": False,
    }
