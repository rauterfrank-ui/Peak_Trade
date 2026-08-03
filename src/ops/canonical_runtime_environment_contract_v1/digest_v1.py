"""Deterministic redacted digests for parent and effective environments."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from src.ops.canonical_runtime_environment_contract_v1.constants_v1 import (
    SENSITIVE_ALLOWLIST_KEYS,
)


def canonical_json_dumps_v1(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex_v1(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _redact_value_v1(*, key: str, value: str) -> str:
    text = str(value)
    if key in SENSITIVE_ALLOWLIST_KEYS:
        return f"sha256:{sha256_hex_v1(text)}"
    upper = key.upper()
    if any(
        frag in upper
        for frag in (
            "SECRET",
            "TOKEN",
            "PASSWORD",
            "PASSPHRASE",
            "API_KEY",
            "ACCESS_KEY",
            "PRIVATE",
            "CREDENTIAL",
        )
    ):
        return f"sha256:{sha256_hex_v1(text)}"
    if len(text) > 256:
        return f"sha256:{sha256_hex_v1(text)}"
    return text


def redact_environment_mapping_v1(environ: Mapping[str, str]) -> dict[str, str]:
    return {str(k): _redact_value_v1(key=str(k), value=str(v)) for k, v in sorted(environ.items())}


def parent_environment_digest_v1(parent_environ: Mapping[str, str]) -> str:
    redacted = redact_environment_mapping_v1(parent_environ)
    return sha256_hex_v1(canonical_json_dumps_v1(redacted))


def effective_environment_digest_v1(effective_environ: Mapping[str, str]) -> str:
    # Effective allowlist env must not contain secret plaintext by construction;
    # still hash sensitive path-like keys for attestation stability without leaking paths.
    material = {
        str(k): (
            f"sha256:{sha256_hex_v1(str(v))}" if str(k) in SENSITIVE_ALLOWLIST_KEYS else str(v)
        )
        for k, v in sorted(effective_environ.items())
    }
    return sha256_hex_v1(canonical_json_dumps_v1(material))
