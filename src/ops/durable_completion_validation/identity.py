"""Shared digest and identity validation helpers."""

from __future__ import annotations

import re

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def sorted_unique(items: list[str]) -> list[str]:
    return sorted(dict.fromkeys(items))


def valid_sha256_digest(value: str) -> bool:
    return bool(_SHA256_HEX_RE.match(value))


def valid_commit_sha(value: str) -> bool:
    return bool(_COMMIT_SHA_RE.match(value))
