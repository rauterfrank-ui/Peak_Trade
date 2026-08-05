"""Thin authorization validate/consume bindings for Step-4 activation.

Reuses repository-canonical authorization surfaces. Does not invent session,
fault, retry, backoff, or reconnect semantics. Confirm-token plaintext is never
persisted — only digests / ids / consumption status.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
    sha256_canonical_v1,
)


class ActivationAuthorizationError(RuntimeError):
    """Fail-closed authorization binding error."""


def validate_authorization_binding_v1(
    *,
    authorization_id: str,
    authorization_digest: str,
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_scope: str = SESSION_SCOPE,
    expected_session_id: str = TARGET_SESSION_ID,
    authorization_scope: str = SESSION_SCOPE,
    authorization_session_id: str = TARGET_SESSION_ID,
    authorization_repository_sha: str = "",
    authorization_config_digest: str = "",
    live_trading_allowed: bool = False,
    testnet_allowed: bool = False,
    private_endpoint_access_allowed: bool = False,
    exchange_credential_use_allowed: bool = False,
    real_capital_movement_allowed: bool = False,
    already_consumed: bool = False,
) -> dict[str, Any]:
    """Validate authorization binding without consuming."""
    blockers: list[str] = []
    auth_id = str(authorization_id or "").strip()
    auth_digest = str(authorization_digest or "").strip()
    if not auth_id:
        blockers.append("AUTHORIZATION_ID_MISSING")
    if not auth_digest:
        blockers.append("AUTHORIZATION_DIGEST_MISSING")
    if already_consumed:
        blockers.append("AUTHORIZATION_ALREADY_CONSUMED")
    if str(authorization_scope) != str(expected_scope):
        blockers.append("AUTHORIZATION_SCOPE_MISMATCH")
    if str(authorization_session_id) != str(expected_session_id):
        blockers.append("AUTHORIZATION_SESSION_ID_MISMATCH")
    repo_sha = str(authorization_repository_sha or expected_repository_sha).strip()
    cfg = str(authorization_config_digest or expected_config_digest).strip()
    if repo_sha != str(expected_repository_sha):
        blockers.append("AUTHORIZATION_SHA_MISMATCH")
    if cfg != str(expected_config_digest):
        blockers.append("AUTHORIZATION_CONFIG_MISMATCH")
    if live_trading_allowed:
        blockers.append("LIVE_TRADING_SCOPE_FORBIDDEN")
    if testnet_allowed:
        blockers.append("TESTNET_SCOPE_FORBIDDEN")
    if private_endpoint_access_allowed:
        blockers.append("PRIVATE_ENDPOINT_SCOPE_FORBIDDEN")
    if exchange_credential_use_allowed:
        blockers.append("EXCHANGE_CREDENTIAL_SCOPE_FORBIDDEN")
    if real_capital_movement_allowed:
        blockers.append("REAL_CAPITAL_MOVEMENT_SCOPE_FORBIDDEN")
    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "authorization_id": auth_id,
        "authorization_digest": auth_digest,
        "authorization_valid": not blockers,
        "authorization_scope_match": "AUTHORIZATION_SCOPE_MISMATCH" not in blockers,
        "authorization_sha_match": "AUTHORIZATION_SHA_MISMATCH" not in blockers,
        "consumed": False,
        "notes": ["AUTHORIZATION_VALIDATE_ONLY_NO_CONSUME=true"],
    }


def consume_authorization_binding_v1(
    *,
    ledger_path: Path,
    authorization_id: str,
    authorization_digest: str,
    session_id: str = TARGET_SESSION_ID,
    now_unix: float,
) -> dict[str, Any]:
    """Single-use authorization consumption at the session-start boundary."""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    consumed_ids: set[str] = set()
    if ledger_path.is_file():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            consumed_ids.add(str(row.get("authorization_id") or ""))
    if authorization_id in consumed_ids:
        raise ActivationAuthorizationError("AUTHORIZATION_REUSE_FORBIDDEN")
    record = {
        "authorization_id": authorization_id,
        "authorization_digest": authorization_digest,
        "session_id": session_id,
        "consumed_at": float(now_unix),
        "single_use": True,
        "plaintext_persisted": False,
    }
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
    return {
        "ok": True,
        "consumed": True,
        "authorization_id": authorization_id,
        "authorization_digest": authorization_digest,
        "record_digest": sha256_canonical_v1(record),
        "notes": ["AUTHORIZATION_CONSUMED_AT_START_BOUNDARY=true"],
    }


def load_consumed_authorization_ids_from_ledger_v1(ledger_path: Path) -> set[str]:
    if not ledger_path.is_file():
        return set()
    out: set[str] = set()
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        out.add(str(row.get("authorization_id") or ""))
    return out


def redact_authorization_mapping_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Evidence-safe view: never include token plaintext fields."""
    forbidden = {
        "confirm_token",
        "token_plaintext",
        "raw_token",
        "go_token",
        "operator_go_token",
    }
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if str(key).lower() in forbidden:
            out[key] = "[REDACTED]"
        elif isinstance(value, Mapping):
            out[key] = redact_authorization_mapping_v1(value)
        else:
            out[key] = value
    return out
