"""Authority-specific confirm-token adapter (no plaintext persistence).

Reuses the secure fingerprint/hash helpers from the existing confirm-token
surface without creating a second token authority.
"""

from __future__ import annotations

from typing import Any, Mapping

from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.constants_v2 import (
    CONFIRM_TOKEN_ADAPTER_ID,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.models_v2 import (
    AdditionalEvidenceSessionAuthorizationV2Error,
    sha256_hex_text,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    assert_no_plaintext_token_fields,
    fingerprint_confirm_token,
    sha256_text,
)


def bind_confirm_token_v2(
    *,
    confirm_token: str,
    authorization_id: str,
    preregistration_id: str,
    preregistration_digest: str,
    execution_sha: str,
) -> dict[str, str]:
    if not isinstance(confirm_token, str) or not confirm_token.strip():
        raise AdditionalEvidenceSessionAuthorizationV2Error("confirm_token_required")
    if any(ch.isspace() for ch in confirm_token):
        # Allow internal spaces only if already present in GO tokens; reject empty.
        pass
    fp = fingerprint_confirm_token(confirm_token)
    digest = f"sha256:{sha256_text(confirm_token)}"
    binding = sha256_hex_text(
        "|".join(
            [
                CONFIRM_TOKEN_ADAPTER_ID,
                authorization_id,
                preregistration_id,
                preregistration_digest,
                execution_sha,
                fp,
                digest,
            ]
        )
    )
    return {
        "confirm_token_fingerprint": fp,
        "confirm_token_digest": digest,
        "confirm_token_binding_sha256": binding,
    }


def assert_confirm_token_matches_v2(
    *,
    artifact_fingerprint: str,
    artifact_digest: str,
    artifact_binding: str,
    confirm_token: str,
    authorization_id: str,
    preregistration_id: str,
    preregistration_digest: str,
    execution_sha: str,
    previously_seen_fingerprints: frozenset[str] | None = None,
) -> None:
    bound = bind_confirm_token_v2(
        confirm_token=confirm_token,
        authorization_id=authorization_id,
        preregistration_id=preregistration_id,
        preregistration_digest=preregistration_digest,
        execution_sha=execution_sha,
    )
    if previously_seen_fingerprints and bound["confirm_token_fingerprint"] in (
        previously_seen_fingerprints
    ):
        raise AdditionalEvidenceSessionAuthorizationV2Error("confirm_token_replay_rejected")
    if bound["confirm_token_fingerprint"] != artifact_fingerprint:
        raise AdditionalEvidenceSessionAuthorizationV2Error("confirm_token_fingerprint_mismatch")
    if bound["confirm_token_digest"] != artifact_digest:
        raise AdditionalEvidenceSessionAuthorizationV2Error("confirm_token_digest_mismatch")
    if bound["confirm_token_binding_sha256"] != artifact_binding:
        raise AdditionalEvidenceSessionAuthorizationV2Error("confirm_token_binding_mismatch")


def assert_authorization_payload_token_safe_v2(payload: Mapping[str, Any]) -> None:
    assert_no_plaintext_token_fields(payload)
    for key in payload:
        key_l = str(key).lower()
        if key_l in {"confirm_token", "token_plaintext", "raw_token", "go_token"}:
            raise AdditionalEvidenceSessionAuthorizationV2Error(
                f"plaintext_token_field_forbidden:{key}"
            )
