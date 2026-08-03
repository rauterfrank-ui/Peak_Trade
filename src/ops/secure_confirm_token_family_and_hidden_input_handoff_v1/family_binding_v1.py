"""Authenticated family+purpose binding (blocks cross-family substitution).

Even when PSO and S03 share the same body-prefix format, a token bound to one
family_id/purpose cannot verify under another.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    fingerprint_confirm_token,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.constants_v1 import (
    BINDING_DOMAIN,
    SCHEMA_VERSION,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.errors_v1 import (
    CrossFamilySubstitutionError,
    SecureConfirmTokenError,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.family_matrix_v1 import (
    assert_purpose_matches_family_v1,
    require_activatable_family_v1,
)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_family_binding_digest_v1(
    *,
    family_id: str,
    purpose: str,
    token_fingerprint: str,
    session_id: str,
    repository_sha: str,
    consumer_id: str,
) -> str:
    material = "|".join(
        [
            BINDING_DOMAIN,
            SCHEMA_VERSION,
            str(family_id),
            str(purpose),
            str(token_fingerprint),
            str(session_id),
            str(repository_sha),
            str(consumer_id),
        ]
    )
    return _sha256_text(material)


@dataclass(frozen=True)
class FamilyBoundTokenMetadataV1:
    family_id: str
    purpose: str
    token_fingerprint: str
    family_binding_digest: str
    session_id: str
    repository_sha: str
    consumer_id: str
    schema_version: str = SCHEMA_VERSION

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "family_id": self.family_id,
            "purpose": self.purpose,
            "token_fingerprint": self.token_fingerprint,
            "family_binding_digest": self.family_binding_digest,
            "session_id": self.session_id,
            "repository_sha": self.repository_sha,
            "consumer_id": self.consumer_id,
            "schema_version": self.schema_version,
            "plaintext_persisted": False,
        }


def bind_plaintext_to_family_v1(
    *,
    confirm_token: str,
    family_id: str,
    purpose: str,
    session_id: str,
    repository_sha: str,
    consumer_id: str,
) -> FamilyBoundTokenMetadataV1:
    if not isinstance(confirm_token, str) or not confirm_token:
        raise SecureConfirmTokenError("confirm_token_empty")
    require_activatable_family_v1(family_id)
    assert_purpose_matches_family_v1(family_id=family_id, purpose=purpose)
    fp = fingerprint_confirm_token(confirm_token)
    digest = compute_family_binding_digest_v1(
        family_id=family_id,
        purpose=purpose,
        token_fingerprint=fp,
        session_id=session_id,
        repository_sha=repository_sha,
        consumer_id=consumer_id,
    )
    return FamilyBoundTokenMetadataV1(
        family_id=family_id,
        purpose=purpose,
        token_fingerprint=fp,
        family_binding_digest=digest,
        session_id=str(session_id),
        repository_sha=str(repository_sha),
        consumer_id=str(consumer_id),
    )


def verify_family_bound_token_v1(
    *,
    confirm_token: str,
    expected: Mapping[str, Any],
    family_id: str,
    purpose: str,
    session_id: str,
    repository_sha: str,
    consumer_id: str,
    previously_seen_fingerprints: Optional[frozenset[str]] = None,
) -> FamilyBoundTokenMetadataV1:
    """Verify token against authenticated family metadata. Never logs plaintext."""
    actual = bind_plaintext_to_family_v1(
        confirm_token=confirm_token,
        family_id=family_id,
        purpose=purpose,
        session_id=session_id,
        repository_sha=repository_sha,
        consumer_id=consumer_id,
    )
    expected_family = str(expected.get("family_id") or "")
    expected_purpose = str(expected.get("purpose") or "")
    expected_fp = str(expected.get("token_fingerprint") or "")
    expected_digest = str(expected.get("family_binding_digest") or "")

    if expected_family != family_id or expected_purpose != purpose:
        raise CrossFamilySubstitutionError(
            "expected_metadata_family_or_purpose_mismatch",
            payload={"expected_family": expected_family, "requested_family": family_id},
        )
    if previously_seen_fingerprints and actual.token_fingerprint in previously_seen_fingerprints:
        raise SecureConfirmTokenError("CONFIRM_TOKEN_REPLAY")
    if not hmac.compare_digest(actual.token_fingerprint, expected_fp):
        raise CrossFamilySubstitutionError("token_fingerprint_mismatch")
    if not hmac.compare_digest(actual.family_binding_digest, expected_digest):
        raise CrossFamilySubstitutionError("family_binding_digest_mismatch")
    if str(expected.get("session_id") or "") != session_id:
        raise SecureConfirmTokenError("SESSION_BINDING_MISMATCH")
    if str(expected.get("repository_sha") or "") != repository_sha:
        raise SecureConfirmTokenError("REPOSITORY_SHA_BINDING_MISMATCH")
    if str(expected.get("consumer_id") or "") != consumer_id:
        raise SecureConfirmTokenError("CONSUMER_BINDING_MISMATCH")
    return actual


def assert_not_cross_family_v1(
    *,
    confirm_token: str,
    bound_family_id: str,
    requested_family_id: str,
    bound_purpose: str,
    requested_purpose: str,
) -> None:
    if bound_family_id != requested_family_id or bound_purpose != requested_purpose:
        # Touch fingerprint so callers cannot skip token presence checks silently.
        _ = fingerprint_confirm_token(confirm_token)
        raise CrossFamilySubstitutionError(
            "family_or_purpose_substitution_attempt",
            payload={
                "bound_family_id": bound_family_id,
                "requested_family_id": requested_family_id,
            },
        )
