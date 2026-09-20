"""Validate and encode K1 provisioning material without emitting secrets."""

from __future__ import annotations

import hashlib
import json

from src.ops.k1_productive_macos_credential_store_provisioning_authority_v1.constants_v1 import (
    K1_KEYCHAIN_UTF8_JSON_FIELD_API_KEY,
    K1_KEYCHAIN_UTF8_JSON_FIELD_PASSPHRASE,
    K1_KEYCHAIN_UTF8_JSON_FIELD_SECRET_KEY,
    K1_KEYCHAIN_UTF8_JSON_REQUIRED_FIELDS,
    MIN_OKX_MATERIAL_FIELD_LEN,
    MINIMAL_TRIPLE_STUB_OPAQUE_LEN,
)
from src.ops.k1_productive_macos_credential_store_provisioning_authority_v1.errors_v1 import (
    K1ProductiveMacosKeychainProvisioningError,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.k1_macos_opaque_utf8_json_material_v1 import (
    parse_k1_keychain_utf8_json_material_v1,
)


def _field_fp(value: str) -> str:
    return hashlib.sha256(str(value or "").strip().encode("utf-8")).hexdigest()[:16]


def assert_provisioning_material_policy_v1(
    *,
    api_key: str,
    api_secret: str,
    passphrase: str,
) -> bytes:
    """Return canonical opaque UTF-8 JSON bytes. Fail closed on placeholder classes."""

    key = str(api_key or "").strip()
    secret = str(api_secret or "").strip()
    phrase = str(passphrase or "").strip()
    if not key or not secret or not phrase:
        raise K1ProductiveMacosKeychainProvisioningError("MALFORMED_SCHEMA_FIELDS_INCOMPLETE")
    fps = (_field_fp(key), _field_fp(secret), _field_fp(phrase))
    if len(set(fps)) == 1:
        raise K1ProductiveMacosKeychainProvisioningError("PLACEHOLDER_IDENTICAL_THREE_FIELD_CLASS")
    lengths = (len(key), len(secret), len(phrase))
    if min(lengths) < MIN_OKX_MATERIAL_FIELD_LEN:
        raise K1ProductiveMacosKeychainProvisioningError("PLACEHOLDER_MINIMAL_MATERIAL_CLASS")
    payload = {
        K1_KEYCHAIN_UTF8_JSON_FIELD_API_KEY: key,
        K1_KEYCHAIN_UTF8_JSON_FIELD_SECRET_KEY: secret,
        K1_KEYCHAIN_UTF8_JSON_FIELD_PASSPHRASE: phrase,
    }
    if frozenset(payload.keys()) != K1_KEYCHAIN_UTF8_JSON_REQUIRED_FIELDS:
        raise K1ProductiveMacosKeychainProvisioningError("MALFORMED_SCHEMA_FIELD_SET")
    opaque = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    if len(opaque) <= MINIMAL_TRIPLE_STUB_OPAQUE_LEN and len(set(fps)) == 1:
        raise K1ProductiveMacosKeychainProvisioningError("PLACEHOLDER_MINIMAL_OPAQUE_CLASS")
    # Round-trip through the PL-TF-002 parser seam (fail-closed field contract).
    parse_k1_keychain_utf8_json_material_v1(opaque)
    return opaque


def public_material_shape_proof_v1(*, opaque: bytes) -> dict[str, str]:
    """Non-secret shape attestation for post-write verification contracts."""

    api_key, secret, phrase = parse_k1_keychain_utf8_json_material_v1(opaque)
    try:
        return {
            "opaque_len": str(len(opaque)),
            "opaque_fp_prefix": hashlib.sha256(opaque).hexdigest()[:16],
            "api_key_len": str(len(api_key.strip())),
            "secret_len": str(len(secret.strip())),
            "passphrase_len": str(len(phrase.strip())),
            "identical_field_fp_class": str(
                len({_field_fp(api_key), _field_fp(secret), _field_fp(phrase)}) == 1
            ).lower(),
        }
    finally:
        api_key = ""
        secret = ""
        phrase = ""
