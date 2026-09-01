"""Canonical serialization and content hashing adapter v0.

Reuse rule: this adapter does not invent a new hash dialect. It applies the
majority Peak_Trade canonical JSON primitive:

    json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=True)

This is algorithm-equivalent to helpers such as
``src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1.canonical_json_dumps``
and ``src.ops.canonical_runtime_environment_contract_v1.digest_v1.canonical_json_dumps_v1``.

It does **not** import those modules: they live on runtime/ops surfaces that
this offline package must not take as a dependency.

Documented adapter deltas (strictness, not a fourth dialect):

- ``allow_nan=False``: NaN/Infinity are rejected fail-closed.
- no ``default=`` coercion: unsupported types fail-closed.
- content-hash scope is explicit per schema and excludes volatile envelope
  metadata (ingestion time, ledger sequence, previous ledger hash).

Non-equivalence (do not silently unify):

- ``src.meta.learning_loop.contract_safety_v1.deterministic_json_dumps`` uses
  ``ensure_ascii=False``. This adapter does not import or match that dialect.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from src.learning.deterministic_decision_outcome_v0.errors_v0 import (
    DdoValidationError,
)

CANONICAL_JSON_ALGORITHM_ID = "json.dumps.sort_keys.separators_comma_colon.ensure_ascii_true"
CANONICAL_JSON_ALGORITHM_EQUIVALENT_TO = (
    "src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1."
    "atomic_io_v1.canonical_json_dumps"
)
CONTENT_HASH_ALGORITHM_ID = "sha256"
CONTENT_HASH_ENCODING = "utf-8"
ADAPTER_DEVIATION_ALLOW_NAN_FALSE = True
ADAPTER_DEVIATION_NO_DEFAULT_COERCION = True
LEARNING_LOOP_ENSURE_ASCII_FALSE_DIALECT_IMPORTED = False

_HASH_EXCLUDED_RECORD_FIELDS = frozenset({"content_hash"})
_ENVELOPE_VOLATILE_FIELDS = frozenset(
    {
        "ingested_at_utc",
        "sequence",
        "prev_ledger_hash",
        "ledger_entry_hash",
    }
)


def _reject_default(obj: Any) -> Any:
    raise DdoValidationError(f"UNSUPPORTED_JSON_TYPE:{type(obj).__name__}")


def canonicalize_json_value(value: Any) -> Any:
    """Return a JSON-canonical Python value. Reject floats and unknown types."""
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        raise DdoValidationError("FLOAT_FORBIDDEN_IN_CANONICAL_JSON")
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, inner in value.items():
            if not isinstance(key, str):
                raise DdoValidationError("CANONICAL_JSON_KEY_MUST_BE_STRING")
            out[key] = canonicalize_json_value(inner)
        return out
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [canonicalize_json_value(item) for item in value]
    raise DdoValidationError(f"UNSUPPORTED_JSON_TYPE:{type(value).__name__}")


def canonical_json_dumps_v0(payload: Mapping[str, Any] | Sequence[Any]) -> str:
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
        raise DdoValidationError(f"CANONICAL_JSON_REJECTED:{exc}") from exc


def sha256_hex_v0(text: str) -> str:
    return hashlib.sha256(text.encode(CONTENT_HASH_ENCODING)).hexdigest()


def compute_content_hash_v0(
    payload: Mapping[str, Any],
    *,
    extra_excluded_fields: frozenset[str] | None = None,
) -> str:
    """Hash the canonical record body excluding identity-volatile fields."""
    excluded = _HASH_EXCLUDED_RECORD_FIELDS | _ENVELOPE_VOLATILE_FIELDS
    if extra_excluded_fields:
        excluded = excluded | extra_excluded_fields
    body = {
        key: value for key, value in canonicalize_json_value(payload).items() if key not in excluded
    }
    return sha256_hex_v0(canonical_json_dumps_v0(body))


def hash_scope_payload_v0(payload: Mapping[str, Any]) -> dict[str, Any]:
    canonical = canonicalize_json_value(payload)
    if not isinstance(canonical, dict):
        raise DdoValidationError("HASH_SCOPE_REQUIRES_OBJECT")
    return {
        key: value
        for key, value in canonical.items()
        if key not in _HASH_EXCLUDED_RECORD_FIELDS | _ENVELOPE_VOLATILE_FIELDS
    }
