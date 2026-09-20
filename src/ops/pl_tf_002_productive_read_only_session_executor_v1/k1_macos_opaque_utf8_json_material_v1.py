"""Parse K1 macOS Keychain opaque UTF-8 JSON into ephemeral K1 session fields.

Closed-world field names for OKX venue auth only. Not SecretRef. Not vault file.
Not Canary JSON. Does not persist or emit secrets.
"""

from __future__ import annotations

import json
from typing import Mapping

from src.ops.pl_tf_002_productive_read_only_session_executor_v1.constants_v1 import (
    K1_KEYCHAIN_UTF8_JSON_FIELD_API_KEY,
    K1_KEYCHAIN_UTF8_JSON_FIELD_PASSPHRASE,
    K1_KEYCHAIN_UTF8_JSON_FIELD_SECRET_KEY,
    K1_KEYCHAIN_UTF8_JSON_REQUIRED_FIELDS,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.errors_v1 import (
    PlTf002ProductiveReadOnlySessionError,
)

JOIN_SEAM_ID = "PL_TF_002_K1_MACOS_OPAQUE_UTF8_JSON_MATERIAL_V1"


def parse_k1_keychain_utf8_json_material_v1(opaque: bytes) -> tuple[str, str, str]:
    """Decode opaque Keychain bytes to apiKey/secretKey/passphrase. Fail closed."""

    if not isinstance(opaque, (bytes, bytearray)) or len(opaque) == 0:
        raise PlTf002ProductiveReadOnlySessionError("K1_OPAQUE_EMPTY")
    try:
        text = bytes(opaque).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PlTf002ProductiveReadOnlySessionError("K1_OPAQUE_UTF8_DECODE_FAIL") from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PlTf002ProductiveReadOnlySessionError("K1_OPAQUE_JSON_MALFORMED") from exc
    if not isinstance(payload, Mapping):
        raise PlTf002ProductiveReadOnlySessionError("K1_OPAQUE_JSON_NOT_OBJECT")
    keys = frozenset(str(k) for k in payload.keys())
    if keys != K1_KEYCHAIN_UTF8_JSON_REQUIRED_FIELDS:
        raise PlTf002ProductiveReadOnlySessionError("K1_OPAQUE_JSON_FIELD_SET_MISMATCH")
    api_key = str(payload.get(K1_KEYCHAIN_UTF8_JSON_FIELD_API_KEY) or "").strip()
    secret = str(payload.get(K1_KEYCHAIN_UTF8_JSON_FIELD_SECRET_KEY) or "").strip()
    phrase = str(payload.get(K1_KEYCHAIN_UTF8_JSON_FIELD_PASSPHRASE) or "").strip()
    if not api_key or not secret or not phrase:
        raise PlTf002ProductiveReadOnlySessionError("K1_CREDENTIAL_FIELDS_INCOMPLETE")
    return api_key, secret, phrase
