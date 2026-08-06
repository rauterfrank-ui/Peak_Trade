"""Confirm-token binding helpers for Step-5 (digest/ID only; no plaintext)."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.constants_v1 import (
    CONFIRM_TOKEN_OWNER,
    HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.digest_v1 import (
    sha256_canonical_v1,
)


def validate_confirm_token_binding_v1(
    *,
    confirm_token_id: str,
    confirm_token_fingerprint: str,
    binding_sha256: str,
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_session_id: str = TARGET_SESSION_ID,
    expected_scope: str = SESSION_SCOPE,
    token_session_id: str = TARGET_SESSION_ID,
    token_scope: str = SESSION_SCOPE,
    token_repository_sha: str = "",
    token_config_digest: str = "",
    already_consumed: bool = False,
    step4_token_reuse: bool = False,
    plaintext_present: bool = False,
) -> dict[str, Any]:
    blockers: list[str] = []
    token_id = str(confirm_token_id or "").strip()
    fingerprint = str(confirm_token_fingerprint or "").strip()
    binding = str(binding_sha256 or "").strip()
    if not token_id:
        blockers.append("CONFIRM_TOKEN_ID_MISSING")
    if not fingerprint:
        blockers.append("CONFIRM_TOKEN_FINGERPRINT_MISSING")
    if not binding:
        blockers.append("CONFIRM_TOKEN_BINDING_SHA_MISSING")
    if already_consumed:
        blockers.append("CONFIRM_TOKEN_ALREADY_CONSUMED")
    if step4_token_reuse:
        blockers.append("STEP4_CONFIRM_TOKEN_REUSE_FORBIDDEN")
    if plaintext_present:
        blockers.append("CONFIRM_TOKEN_PLAINTEXT_FORBIDDEN_IN_EVIDENCE")
    if str(token_session_id) != str(expected_session_id):
        blockers.append("CONFIRM_TOKEN_SESSION_MISMATCH")
    if str(token_scope) != str(expected_scope):
        blockers.append("CONFIRM_TOKEN_SCOPE_MISMATCH")
    repo_sha = str(token_repository_sha or expected_repository_sha).strip()
    cfg = str(token_config_digest or expected_config_digest).strip()
    if repo_sha != str(expected_repository_sha):
        blockers.append("CONFIRM_TOKEN_SHA_MISMATCH")
    if cfg != str(expected_config_digest):
        blockers.append("CONFIRM_TOKEN_CONFIG_MISMATCH")
    scope_digest = sha256_canonical_v1(
        {
            "session_id": expected_session_id,
            "scope": expected_scope,
            "repository_sha": expected_repository_sha,
            "config_digest": expected_config_digest,
        }
    )
    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "confirm_token_id": token_id,
        "fingerprint": fingerprint,
        "binding_sha256": binding,
        "scope_digest": scope_digest,
        "consumed_status": "ALREADY_CONSUMED" if already_consumed else "NOT_CONSUMED",
        "issuance_owner": CONFIRM_TOKEN_OWNER,
        "consumption_path_owner": HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
        "plaintext_persisted": False,
        "notes": [
            "CONFIRM_TOKEN_VALIDATE_ONLY_NO_CONSUME=true",
            "EVIDENCE_FIELDS_DIGEST_ID_ONLY=true",
            "STEP4_CONFIRM_TOKEN_REUSE_FORBIDDEN=true",
        ],
    }


def redact_confirm_token_mapping_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    forbidden = {"confirm_token", "token_plaintext", "raw_token", "plaintext"}
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if str(key).lower() in forbidden:
            out[key] = "[REDACTED]"
        elif isinstance(value, Mapping):
            out[key] = redact_confirm_token_mapping_v1(value)
        else:
            out[key] = value
    return out
