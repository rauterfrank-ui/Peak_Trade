"""Deterministic integrity digests for authorization lifecycle artifacts."""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    canonical_json_dumps,
)


DIGEST_EXCLUDED_FIELDS: frozenset[str] = frozenset(
    {"integrity_digest", "digest_scope", "authorization_digest"}
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def integrity_digest_v1(payload: Mapping[str, Any]) -> str:
    material = {k: v for k, v in payload.items() if k not in DIGEST_EXCLUDED_FIELDS}
    return sha256_text(canonical_json_dumps(material))


def stamp_integrity_digest(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out.pop("integrity_digest", None)
    out.pop("digest_scope", None)
    digest = integrity_digest_v1(out)
    out["integrity_digest"] = digest
    out["digest_scope"] = "sha256_canonical_json_excluding_integrity_digest_and_digest_scope"
    return out


def verify_integrity_digest(payload: Mapping[str, Any]) -> str:
    stored = str(payload.get("integrity_digest") or "")
    recomputed = integrity_digest_v1(payload)
    if not stored or stored != recomputed:
        raise ValueError(f"INTEGRITY_DIGEST_MISMATCH:stored={stored}:recomputed={recomputed}")
    return recomputed
