"""Deterministic canonical JSON and SHA-256 for GVEF contracts."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping

from src.evaluation.golden_vectors.contracts.errors import GvefSchemaError
from src.execution.bridge.canonical_json import CanonicalJsonError, dumps_canonical

_SHA256_HEX_RE = re.compile(r"^[a-f0-9]{64}$")
_GIT_SHA_RE = re.compile(r"^[a-f0-9]{40}$")
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_ISO8601_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")
_UUID_V4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        return dumps_canonical(payload)
    except CanonicalJsonError as exc:
        raise GvefSchemaError(str(exc)) from exc


def canonical_json_text(payload: Mapping[str, Any]) -> str:
    return canonical_json_bytes(payload).decode("utf-8")


def sha256_hex(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def require_sha256_hex(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not _SHA256_HEX_RE.fullmatch(value):
        raise GvefSchemaError(f"{field} must be lowercase sha256 hex", field=field)
    return value


def require_git_sha(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not _GIT_SHA_RE.fullmatch(value):
        raise GvefSchemaError(f"{field} must be git sha hex", field=field)
    return value


def require_semver(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not _SEMVER_RE.fullmatch(value):
        raise GvefSchemaError(f"{field} must be semver major.minor.patch", field=field)
    return value


def require_iso8601_utc_z(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not _ISO8601_Z_RE.fullmatch(value):
        raise GvefSchemaError(f"{field} must be ISO8601 UTC with Z suffix", field=field)
    return value


def require_uuid_v4(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not _UUID_V4_RE.fullmatch(value):
        raise GvefSchemaError(f"{field} must be UUID v4", field=field)
    return value.lower()
