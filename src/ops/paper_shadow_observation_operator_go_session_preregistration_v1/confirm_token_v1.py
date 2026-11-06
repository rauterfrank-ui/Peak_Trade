"""Confirm-token binding and verification (local, no secrets in artifacts)."""

from __future__ import annotations

import hashlib
import hmac
import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.constants_v1 import (
    SCHEMA_VERSION,
)

CONFIRM_TOKEN_POLICY_ID = "ops.paper_shadow_observation_confirm_token_v1"
CONFIRM_TOKEN_PREFIX = "GO_PSO_SESSION_PREREG_V1_"
_SENSITIVE_KEY_FRAGMENTS = frozenset(
    {"secret", "password", "api_key", "apikey", "passphrase", "credential", "plaintext"}
)
_TOKEN_KEY_NAMES = frozenset(
    {
        "confirm_token",
        "go_token",
        "operator_go_token",
        "token_plaintext",
        "raw_token",
    }
)


class ConfirmTokenError(ValueError):
    """Fail-closed confirm-token error."""


@dataclass
class ConfirmTokenVerificationResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    fingerprint: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "fingerprint": self.fingerprint,
            "notes": list(self.notes),
            "policy_id": CONFIRM_TOKEN_POLICY_ID,
            "schema_version": SCHEMA_VERSION,
        }


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fingerprint_confirm_token(token: str) -> str:
    """Non-reversible fingerprint; never persist the raw token."""
    return sha256_text(f"PSO_CONFIRM_FP_V1|{token}")


def compute_confirm_token_binding_sha256(
    *,
    session_id: str,
    scope_digest: str,
    expires_at: float,
    repository_sha: str,
    confirm_token: str,
) -> str:
    material = "|".join(
        [
            "PSO_CONFIRM_BINDING_V1",
            str(session_id),
            str(scope_digest),
            f"{float(expires_at):.6f}",
            str(repository_sha),
            str(confirm_token),
        ]
    )
    return sha256_text(material)


_ALLOWED_SENSITIVE_NAMED_FIELDS = frozenset(
    {
        "confirm_token_binding_sha256",
        "confirm_token_fingerprint",
        "confirm_token_hash_reference",
        "credential_policy",
        "credentials_authorized",
        "credentials_used",
    }
)


def assert_no_plaintext_token_fields(payload: Mapping[str, Any]) -> None:
    for key in payload:
        key_l = str(key).lower()
        if key_l in _TOKEN_KEY_NAMES:
            raise ConfirmTokenError(f"PLAINTEXT_TOKEN_FIELD_FORBIDDEN:{key}")
        if key_l in _ALLOWED_SENSITIVE_NAMED_FIELDS:
            continue
        if any(frag in key_l for frag in _SENSITIVE_KEY_FRAGMENTS):
            raise ConfirmTokenError(f"SENSITIVE_FIELD_FORBIDDEN:{key}")


def redact_mapping_for_logs(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Redact token-like values for logs/evidence hygiene."""
    out: dict[str, Any] = {}
    for key, value in payload.items():
        key_l = str(key).lower()
        if (
            key_l in _TOKEN_KEY_NAMES
            or "token" in key_l
            and "binding" not in key_l
            and "fingerprint" not in key_l
            and "hash" not in key_l
        ):
            out[key] = "[REDACTED]"
        elif isinstance(value, Mapping):
            out[key] = redact_mapping_for_logs(value)
        else:
            out[key] = value
    return out


def validate_token_format(token: str) -> tuple[str, ...]:
    blockers: list[str] = []
    raw = str(token or "")
    if not raw:
        blockers.append("CONFIRM_TOKEN_MISSING")
        return tuple(blockers)
    if not raw.startswith(CONFIRM_TOKEN_PREFIX):
        blockers.append("CONFIRM_TOKEN_PREFIX_INVALID")
    if len(raw) < 40:
        blockers.append("CONFIRM_TOKEN_TOO_SHORT")
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", raw):
        blockers.append("CONFIRM_TOKEN_CHARSET_INVALID")
    return tuple(blockers)


def verify_confirm_token_v1(
    *,
    confirm_token: Optional[str],
    expected_binding_sha256: str,
    session_id: str,
    scope_digest: str,
    expires_at: float,
    repository_sha: str,
    previously_seen_fingerprints: frozenset[str] | None = None,
) -> ConfirmTokenVerificationResultV1:
    """Constant-time binding verification. Never logs the raw token."""
    notes = [
        "CONFIRM_TOKEN_VERIFICATION_LOCAL_ONLY",
        "NO_PLAINTEXT_TOKEN_PERSISTED",
        "NO_NETWORK",
    ]
    blockers: list[str] = []
    raw = "" if confirm_token is None else str(confirm_token)
    blockers.extend(validate_token_format(raw))
    expected = str(expected_binding_sha256 or "").strip().lower()
    if not expected or len(expected) != 64:
        blockers.append("CONFIRM_TOKEN_BINDING_HASH_INVALID")
    if blockers:
        return ConfirmTokenVerificationResultV1(ok=False, blockers=blockers, notes=notes)

    computed = compute_confirm_token_binding_sha256(
        session_id=session_id,
        scope_digest=scope_digest,
        expires_at=expires_at,
        repository_sha=repository_sha,
        confirm_token=raw,
    )
    fp = fingerprint_confirm_token(raw)
    if previously_seen_fingerprints and fp in previously_seen_fingerprints:
        blockers.append("CONFIRM_TOKEN_REPLAY")
    if not hmac.compare_digest(computed, expected):
        blockers.append("CONFIRM_TOKEN_BINDING_MISMATCH")
    return ConfirmTokenVerificationResultV1(
        ok=not blockers,
        blockers=blockers,
        fingerprint=fp,
        notes=notes + (["CONFIRM_TOKEN_VERIFIED"] if not blockers else ["CONFIRM_TOKEN_REJECTED"]),
    )
