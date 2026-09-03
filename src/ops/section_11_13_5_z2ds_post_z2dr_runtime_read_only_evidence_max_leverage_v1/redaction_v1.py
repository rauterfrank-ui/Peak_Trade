"""Sanitized non-secret persistence helpers for Z2DS evidence."""

from __future__ import annotations

import hashlib
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlsplit

from src.ops.section_11_13_5_z2ds_post_z2dr_runtime_read_only_evidence_max_leverage_v1.constants_v1 import (
    ACCOUNT_CONFIG_PERSIST_FIELDS,
    ACCOUNT_CONFIG_REDACT_FIELDS,
    BOUND_ACCOUNT_SCOPE,
    REUSED_CREDENTIAL_CLASS,
)

_SECRET_VALUE_PREFIXES = ("ok-access-", "plaintext:", "sk-")
_SECRET_VALUE_KEYS = {
    "api_secret",
    "api-secret",
    "passphrase",
    "ok-access-key",
    "ok-access-sign",
    "ok-access-passphrase",
    "ok-access-timestamp",
    "api_key",
    "secret",
}


class Z2DSRedactionError(RuntimeError):
    """Fail-closed secret leakage in evidence."""


def account_binding_fingerprint_v1(uid: str) -> str:
    material = f"CREATE_ACCOUNT_IDENTITY|{REUSED_CREDENTIAL_CLASS}|{str(uid or '').strip()}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def query_parameters_v1(endpoint: str) -> dict[str, str]:
    parsed = urlsplit(str(endpoint or ""))
    query = parsed.query
    if not query and "?" in str(endpoint or ""):
        query = str(endpoint).split("?", 1)[1]
    return {str(k): str(v) for k, v in parse_qsl(query, keep_blank_values=True)}


def sanitize_account_config_row_v1(row: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key in ACCOUNT_CONFIG_PERSIST_FIELDS:
        if key not in row:
            continue
        value = row[key]
        if key == "uid" or key == "mainUid":
            text = "" if value is None else str(value).strip()
            out[f"{key}_bound_match"] = text == BOUND_ACCOUNT_SCOPE
            out[f"{key}_fingerprint"] = account_binding_fingerprint_v1(text)
            if text == BOUND_ACCOUNT_SCOPE:
                out[key] = text
            else:
                out[key] = "<FINGERPRINT_ONLY>"
            continue
        out[key] = value
    for key in ACCOUNT_CONFIG_REDACT_FIELDS:
        if key in row:
            out[key] = "<REDACTED>"
    return out


def assert_no_secrets_in_payload_v1(payload: Mapping[str, Any] | list[Any] | None) -> None:
    def _walk(value: Any, key: str = "") -> None:
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                _walk(child, str(child_key))
            return
        if isinstance(value, list):
            for item in value:
                _walk(item, key)
            return
        if not isinstance(value, str):
            return
        key_l = str(key).strip().lower()
        text = value.strip()
        lowered = text.lower()
        if (
            key_l in _SECRET_VALUE_KEYS
            and text
            and text
            not in {
                "<REDACTED>",
                "<REF_ONLY>",
                "<FINGERPRINT_ONLY>",
            }
        ):
            raise Z2DSRedactionError("SECRET_IN_EVIDENCE")
        if any(lowered.startswith(prefix) for prefix in _SECRET_VALUE_PREFIXES):
            raise Z2DSRedactionError("SECRET_IN_EVIDENCE")

    if payload is None:
        return
    _walk(payload)
