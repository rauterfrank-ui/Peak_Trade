"""Canonical JSON serialization and digests (no semantic normalization)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


class CanonicalJsonErrorV1(ValueError):
    """Payload is not safely JSON-serializable under the contract rules."""


def canonical_json_text_v1(payload: Mapping[str, Any]) -> str:
    """Return deterministic compact JSON text for a JSON object.

    Rules:
    - sort_keys=True (key order independent of input insertion order)
    - UTF-8 text (ensure_ascii=False)
    - separators=(',', ':') — no insignificant whitespace
    - allow_nan=False — reject NaN/Inf
    - no field invention, enum coercion, or float rounding
    """
    if not isinstance(payload, Mapping):
        raise CanonicalJsonErrorV1("payload must be a mapping/JSON object")
    try:
        return json.dumps(
            dict(payload),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CanonicalJsonErrorV1(str(exc)) from exc


def canonical_json_file_body_v1(payload: Mapping[str, Any]) -> str:
    """Canonical on-disk body: compact JSON + trailing newline."""
    return canonical_json_text_v1(payload) + "\n"


def canonical_digest_v1(payload: Mapping[str, Any]) -> str:
    """SHA-256 hex digest over the canonical JSON text (no trailing newline)."""
    body = canonical_json_text_v1(payload)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()
