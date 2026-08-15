"""Canary-scoped SecretRef URI validation (§11.13.5 only)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    FORBIDDEN_CREDENTIAL_CLASS_MARKERS,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
    SECRETREF_CANARY_PATH_MARKER,
    SECRETREF_FORBIDDEN_CROSS_PACKAGE_MARKERS,
    SECRETREF_FORBIDDEN_PATH_MARKERS,
    SECRETREF_URI_PREFIX,
)


class LiveCanarySecretRefError(RuntimeError):
    """Fail-closed canary SecretRef violation."""


_SAFE_REF_RE = re.compile(r"^secretref://[a-z0-9][a-z0-9._/\-]*$", re.IGNORECASE)


@dataclass(frozen=True)
class LiveCanarySecretRefMetadataV1:
    secretref_uri: str
    credential_class: str
    log_safe_id: str
    uri_digest: str
    plaintext_present: bool = False
    material_loaded: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "secretref_uri": self.secretref_uri,
            "credential_class": self.credential_class,
            "log_safe_id": self.log_safe_id,
            "uri_digest": self.uri_digest,
            "plaintext_present": self.plaintext_present,
            "material_loaded": self.material_loaded,
        }


def validate_live_canary_secretref_uri_v1(secretref_uri: str) -> str:
    ref = str(secretref_uri or "").strip()
    if not ref:
        raise LiveCanarySecretRefError("SECRETREF_REQUIRED")
    if ref.startswith("plaintext:") or ref.startswith("sk-"):
        raise LiveCanarySecretRefError("PLAINTEXT_SECRET_FORBIDDEN")
    if not ref.startswith(SECRETREF_URI_PREFIX):
        raise LiveCanarySecretRefError("SECRETREF_URI_PREFIX_REQUIRED")
    if not _SAFE_REF_RE.match(ref):
        raise LiveCanarySecretRefError("SECRETREF_URI_MALFORMED")
    lowered = ref.lower()
    if SECRETREF_CANARY_PATH_MARKER not in lowered:
        raise LiveCanarySecretRefError("SECRETREF_CANARY_PATH_MARKER_REQUIRED")
    for marker in SECRETREF_FORBIDDEN_PATH_MARKERS:
        if marker in lowered:
            raise LiveCanarySecretRefError(f"SECRETREF_FORBIDDEN_PATH:{marker}")
    for marker in SECRETREF_FORBIDDEN_CROSS_PACKAGE_MARKERS:
        if marker in lowered:
            raise LiveCanarySecretRefError(f"SECRETREF_CROSS_PACKAGE_FORBIDDEN:{marker}")
    if ref != REQUIRED_SECRETREF_URI:
        raise LiveCanarySecretRefError("SECRETREF_URI_BINDING_MISMATCH")
    return ref


def validate_live_canary_credential_class_v1(credential_class: str) -> str:
    klass = str(credential_class or "").strip()
    if not klass:
        raise LiveCanarySecretRefError("CREDENTIAL_CLASS_REQUIRED")
    if klass != REQUIRED_CREDENTIAL_CLASS:
        raise LiveCanarySecretRefError("CREDENTIAL_CLASS_MISMATCH")
    upper = klass.upper()
    for marker in FORBIDDEN_CREDENTIAL_CLASS_MARKERS:
        if marker in upper:
            raise LiveCanarySecretRefError(f"CREDENTIAL_CLASS_FORBIDDEN_MARKER:{marker}")
    return klass


def build_live_canary_secretref_metadata_v1(
    *,
    secretref_uri: str,
    credential_class: str = REQUIRED_CREDENTIAL_CLASS,
) -> LiveCanarySecretRefMetadataV1:
    ref = validate_live_canary_secretref_uri_v1(secretref_uri)
    klass = validate_live_canary_credential_class_v1(credential_class)
    digest = hashlib.sha256(ref.encode("utf-8")).hexdigest()
    return LiveCanarySecretRefMetadataV1(
        secretref_uri=ref,
        credential_class=klass,
        log_safe_id=f"secretref-digest:{digest[:16]}",
        uri_digest=digest,
    )
