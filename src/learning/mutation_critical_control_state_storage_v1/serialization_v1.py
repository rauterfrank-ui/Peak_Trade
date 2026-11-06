"""Canonical JSON and content hashing for control-state records.

Dialect is the Peak_Trade majority canonical JSON primitive. This module
does not import DDO, Cap 6.4, or SQLite helpers. It is not a second hash
authority.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from src.learning.mutation_critical_control_state_storage_v1.errors_v1 import (
    ControlStateValidationError,
)

CANONICAL_JSON_ALGORITHM_ID = "json.dumps.sort_keys.separators_comma_colon.ensure_ascii_true"
CONTENT_HASH_ALGORITHM_ID = "sha256"
CONTENT_HASH_ENCODING = "utf-8"
_HASH_EXCLUDED_FIELDS = frozenset({"content_hash", "transaction_id", "sequence"})


def _reject_default(obj: Any) -> Any:
    raise ControlStateValidationError(f"UNSUPPORTED_JSON_TYPE:{type(obj).__name__}")


def canonicalize_json_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        raise ControlStateValidationError("FLOAT_FORBIDDEN_IN_CANONICAL_JSON")
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, inner in value.items():
            if not isinstance(key, str):
                raise ControlStateValidationError("CANONICAL_JSON_KEY_MUST_BE_STRING")
            out[key] = canonicalize_json_value(inner)
        return out
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [canonicalize_json_value(item) for item in value]
    raise ControlStateValidationError(f"UNSUPPORTED_JSON_TYPE:{type(value).__name__}")


def canonical_json_dumps_v1(payload: Mapping[str, Any] | Sequence[Any]) -> str:
    canonical = canonicalize_json_value(payload)
    try:
        return json.dumps(
            canonical,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
            default=_reject_default,
        )
    except ValueError as exc:
        raise ControlStateValidationError(f"CANONICAL_JSON_REJECTED:{exc}") from exc


def sha256_hex_v1(text: str) -> str:
    return hashlib.sha256(text.encode(CONTENT_HASH_ENCODING)).hexdigest()


def sha256_bytes_v1(payload: bytes) -> bytes:
    return hashlib.sha256(payload).digest()


def compute_content_hash_v1(payload: Mapping[str, Any]) -> str:
    body = {
        key: value
        for key, value in canonicalize_json_value(payload).items()
        if key not in _HASH_EXCLUDED_FIELDS
    }
    return sha256_hex_v1(canonical_json_dumps_v1(body))
