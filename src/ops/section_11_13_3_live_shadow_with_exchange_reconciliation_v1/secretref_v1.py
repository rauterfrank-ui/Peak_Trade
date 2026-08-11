"""SecretRef / credential-class isolation for §11.13.3 Live shadow reconciliation."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.constants_v1 import (
    FORBIDDEN_CREDENTIAL_CLASS_MARKERS,
    REQUIRED_CREDENTIAL_CLASS,
    SECRETREF_FORBIDDEN_PATH_MARKERS,
    SECRETREF_LIVE_PATH_MARKER,
    SECRETREF_URI_PREFIX,
)


class LiveShadowReconSecretRefError(RuntimeError):
    """Fail-closed SecretRef / credential isolation violation."""


_SAFE_REF_RE = re.compile(r"^secretref://[a-z0-9][a-z0-9._/\-]*$", re.IGNORECASE)


@dataclass(frozen=True)
class LiveShadowReconSecretRefMetadataV1:
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


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_live_shadow_recon_secretref_uri_v1(secretref_uri: str) -> str:
    ref = str(secretref_uri or "").strip()
    if not ref:
        raise LiveShadowReconSecretRefError("SECRETREF_REQUIRED")
    if ref.startswith("plaintext:") or ref.startswith("sk-"):
        raise LiveShadowReconSecretRefError("PLAINTEXT_SECRET_FORBIDDEN")
    if not ref.startswith(SECRETREF_URI_PREFIX):
        raise LiveShadowReconSecretRefError("SECRETREF_URI_PREFIX_REQUIRED")
    if not _SAFE_REF_RE.match(ref):
        raise LiveShadowReconSecretRefError("SECRETREF_URI_MALFORMED")
    lowered = ref.lower()
    if SECRETREF_LIVE_PATH_MARKER not in lowered:
        raise LiveShadowReconSecretRefError("SECRETREF_LIVE_PATH_MARKER_REQUIRED")
    for marker in SECRETREF_FORBIDDEN_PATH_MARKERS:
        if marker in lowered:
            raise LiveShadowReconSecretRefError(f"SECRETREF_FORBIDDEN_PATH:{marker}")
    return ref


def validate_live_shadow_recon_credential_class_v1(credential_class: str) -> str:
    klass = str(credential_class or "").strip()
    if not klass:
        raise LiveShadowReconSecretRefError("CREDENTIAL_CLASS_REQUIRED")
    upper = klass.upper()
    for marker in FORBIDDEN_CREDENTIAL_CLASS_MARKERS:
        if marker in upper:
            raise LiveShadowReconSecretRefError(f"FORBIDDEN_CREDENTIAL_CLASS:{klass}")
    if klass != REQUIRED_CREDENTIAL_CLASS:
        raise LiveShadowReconSecretRefError("LIVE_SHADOW_RECON_CREDENTIAL_CLASS_REQUIRED")
    return klass


def reject_cross_environment_secretref_use_v1(
    *,
    secretref_uri: str,
    requested_environment: str,
) -> None:
    """Demo/Testnet refs cannot be used for Live; Live refs cannot be used for Demo/Testnet."""
    ref = str(secretref_uri or "").strip().lower()
    env = str(requested_environment or "").strip().upper()
    has_live = SECRETREF_LIVE_PATH_MARKER in ref
    has_non_live = any(m in ref for m in SECRETREF_FORBIDDEN_PATH_MARKERS)
    if env == "LIVE":
        if has_non_live or not has_live:
            raise LiveShadowReconSecretRefError("CROSS_BIND_DEMO_TESTNET_REF_TO_LIVE_REJECT")
        return
    if env in {"DEMO", "TESTNET", "PAPER", "SIMULATED"}:
        if has_live:
            raise LiveShadowReconSecretRefError("CROSS_BIND_LIVE_REF_TO_DEMO_TESTNET_REJECT")
        return
    raise LiveShadowReconSecretRefError(f"UNSUPPORTED_ENVIRONMENT_FOR_SECRETREF:{env}")


def build_live_shadow_recon_secretref_metadata_v1(
    *,
    secretref_uri: str,
    credential_class: str,
) -> LiveShadowReconSecretRefMetadataV1:
    ref = validate_live_shadow_recon_secretref_uri_v1(secretref_uri)
    klass = validate_live_shadow_recon_credential_class_v1(credential_class)
    digest = _digest(ref)
    return LiveShadowReconSecretRefMetadataV1(
        secretref_uri=ref,
        credential_class=klass,
        log_safe_id=f"secretref-digest:{digest[:16]}",
        uri_digest=digest,
        plaintext_present=False,
        material_loaded=False,
    )


def refuse_credential_material_borrow_v1(*, reason: str) -> None:
    raise LiveShadowReconSecretRefError(f"CREDENTIAL_MATERIAL_BORROW_REFUSED:{reason}")
