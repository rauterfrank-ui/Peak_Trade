"""Deterministic serialization. Null, UNKNOWN, UNCLASSIFIED, NONE, false, ABSENT stay distinct."""

from __future__ import annotations

import json
from typing import Any

CANONICAL_JSON_SEPARATORS = (",", ":")


def dumps_canonical(payload: Any) -> str:
    """Byte-stable JSON for contract comparison. No timestamps or UUIDs."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=CANONICAL_JSON_SEPARATORS,
        ensure_ascii=False,
        allow_nan=False,
    )


def dumps_canonical_bytes(payload: Any) -> bytes:
    return dumps_canonical(payload).encode("utf-8")
