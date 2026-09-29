"""PRE-POST request envelope: signed OKX auth headers without venue POST.

Binds permit + final-order envelope + non-secret signing proof. Never exports
credential material.

RUNTIME_AUTHORIZATION_EFFECT=PRE_POST_ENVELOPE_CONSTRUCTION_ONLY
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final, Mapping

from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    FullCoreK1BoundVenueAuthHandleV1,
    build_k1_okx_venue_auth_headers_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    ExternalEffectPermitV1,
    assert_permit_matches_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)

ENVELOPE_OWNER: Final[str] = "governance.current_productive_k1_pre_post_request_envelope_v1"
PRE_POST_SCHEMA_VERSION: Final[str] = "current_productive_k1_pre_post_request_envelope/v1"
_SECRET_HEADER_VALUES_FORBIDDEN = ("sk-", "ak-", "pp-")


class CurrentProductiveK1PrePostRequestEnvelopeError(RuntimeError):
    """Fail-closed PRE-POST request envelope violation."""


@dataclass(frozen=True)
class CurrentProductiveK1PrePostRequestEnvelopeV1:
    schema_version: str
    envelope_id: str
    envelope_digest: str
    permit_id: str
    request_method: str
    request_url: str
    request_signing_performed: bool
    header_names: tuple[str, ...]
    pre_post_digest: str
    post_allowed: bool
    real_venue_post_allowed: bool

    def to_public_dict_v1(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "envelope_id": self.envelope_id,
            "envelope_digest": self.envelope_digest,
            "permit_id": self.permit_id,
            "request_method": self.request_method,
            "request_url": self.request_url,
            "request_signing_performed": self.request_signing_performed,
            "header_names": list(self.header_names),
            "pre_post_digest": self.pre_post_digest,
            "post_allowed": self.post_allowed,
            "real_venue_post_allowed": self.real_venue_post_allowed,
        }

    def __repr__(self) -> str:
        return "CurrentProductiveK1PrePostRequestEnvelopeV1(redacted)"


def _canonical_pre_post_body(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _assert_public_surface_safe(payload: Mapping[str, Any]) -> None:
    blob = _canonical_pre_post_body(payload)
    lower = blob.lower()
    for token in _SECRET_HEADER_VALUES_FORBIDDEN:
        if token in lower:
            raise CurrentProductiveK1PrePostRequestEnvelopeError(
                "SECRET_LIKE_VALUE_IN_PUBLIC_SURFACE"
            )


def build_and_validate_current_productive_k1_pre_post_request_envelope_v1(
    *,
    envelope: FinalOrderEnvelopeV1,
    permit: ExternalEffectPermitV1,
    signing_handle: FullCoreK1BoundVenueAuthHandleV1,
    request_url: str,
    request_method: str = "POST",
    request_body: str = "",
) -> CurrentProductiveK1PrePostRequestEnvelopeV1:
    """Build PRE-POST envelope with OKX signing headers. No network I/O."""

    assert_envelope_unmodified_v1(envelope)
    assert_permit_matches_envelope_v1(permit, envelope)
    if signing_handle.bound is not True or signing_handle.can_sign is not True:
        raise CurrentProductiveK1PrePostRequestEnvelopeError("SIGNING_HANDLE_NOT_READY")
    method = str(request_method or "POST").upper()
    url = str(request_url or "").strip()
    if not url.startswith("https://"):
        raise CurrentProductiveK1PrePostRequestEnvelopeError("REQUEST_URL_INVALID")
    headers = build_k1_okx_venue_auth_headers_v1(
        handle=signing_handle,
        url=url,
        method=method,
        body=request_body,
    )
    required = ("OK-ACCESS-KEY", "OK-ACCESS-SIGN", "OK-ACCESS-TIMESTAMP", "OK-ACCESS-PASSPHRASE")
    for name in required:
        if name not in headers:
            raise CurrentProductiveK1PrePostRequestEnvelopeError(f"HEADER_MISSING:{name}")
    header_names = tuple(sorted(str(k) for k in headers.keys()))
    public = {
        "schema_version": PRE_POST_SCHEMA_VERSION,
        "envelope_id": envelope.envelope_id,
        "envelope_digest": envelope.envelope_digest,
        "permit_id": permit.permit_id,
        "request_method": method,
        "request_url": url,
        "request_signing_performed": True,
        "header_names": list(header_names),
        "post_allowed": False,
        "real_venue_post_allowed": False,
    }
    _assert_public_surface_safe(public)
    pre_post_digest = compute_content_sha256(public)
    if not pre_post_digest:
        raise CurrentProductiveK1PrePostRequestEnvelopeError("PRE_POST_DIGEST_FAIL")
    result = CurrentProductiveK1PrePostRequestEnvelopeV1(
        schema_version=PRE_POST_SCHEMA_VERSION,
        envelope_id=envelope.envelope_id,
        envelope_digest=envelope.envelope_digest,
        permit_id=permit.permit_id,
        request_method=method,
        request_url=url,
        request_signing_performed=True,
        header_names=header_names,
        pre_post_digest=pre_post_digest,
        post_allowed=False,
        real_venue_post_allowed=False,
    )
    _assert_public_surface_safe(result.to_public_dict_v1())
    return result


def validate_pre_post_envelope_bindings_v1(
    *,
    pre_post: CurrentProductiveK1PrePostRequestEnvelopeV1,
    envelope: FinalOrderEnvelopeV1,
    permit: ExternalEffectPermitV1,
) -> bool:
    if pre_post.envelope_id != envelope.envelope_id:
        return False
    if pre_post.envelope_digest != envelope.envelope_digest:
        return False
    if pre_post.permit_id != permit.permit_id:
        return False
    if pre_post.request_signing_performed is not True:
        return False
    if pre_post.post_allowed is True or pre_post.real_venue_post_allowed is True:
        return False
    return True


__all__ = [
    "ENVELOPE_OWNER",
    "PRE_POST_SCHEMA_VERSION",
    "CurrentProductiveK1PrePostRequestEnvelopeError",
    "CurrentProductiveK1PrePostRequestEnvelopeV1",
    "build_and_validate_current_productive_k1_pre_post_request_envelope_v1",
    "validate_pre_post_envelope_bindings_v1",
]
