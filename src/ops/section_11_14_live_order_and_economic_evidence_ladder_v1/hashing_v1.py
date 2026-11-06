"""Canonical JSON serialization and content hashing for §11.14 records."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

CANONICAL_JSON_SEPARATORS = (",", ":")


def canonical_json_bytes_v1(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(payload),
        sort_keys=True,
        separators=CANONICAL_JSON_SEPARATORS,
        ensure_ascii=True,
    ).encode("utf-8")


def content_hash_v1(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes_v1(payload)).hexdigest()


def hashed_record_v1(
    payload: Mapping[str, Any], *, hash_key: str = "content_hash"
) -> dict[str, Any]:
    body = {key: value for key, value in payload.items() if key != hash_key}
    record = dict(body)
    record[hash_key] = content_hash_v1(body)
    return record
