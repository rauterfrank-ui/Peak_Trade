"""Thin confirm-token validate/consume bindings for Step-4 activation.

Canonical path only: file | env | in-memory. Never argv plaintext. Never persist
plaintext — only fingerprint / binding digest / consumption status.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    fingerprint_confirm_token,
    validate_token_format,
    verify_confirm_token_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.confirm_token_path_v1 import (
    confirm_token_present_via_canonical_path_v1,
    reject_confirm_token_argv_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
    sha256_canonical_v1,
)


class ActivationConfirmTokenError(RuntimeError):
    """Fail-closed confirm-token binding error."""


def load_confirm_token_plaintext_canonical_v1(
    *,
    confirm_token_in_memory: str | None = None,
    confirm_token_file: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> tuple[str, list[str]]:
    """Load plaintext via in-memory | file | env only. Never from argv."""
    blockers: list[str] = []
    if confirm_token_in_memory is not None and str(confirm_token_in_memory).strip():
        return str(confirm_token_in_memory), []
    if confirm_token_file is not None:
        path = Path(confirm_token_file)
        if not path.is_file():
            return "", ["CONFIRM_TOKEN_FILE_MISSING"]
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            return "", ["CONFIRM_TOKEN_FILE_EMPTY"]
        return raw, []
    env = environ if environ is not None else os.environ
    env_confirm = str(env.get("PEAK_TRADE_PSO_CONFIRM_TOKEN") or "").strip()
    if env_confirm:
        return env_confirm, []
    blockers.append("CONFIRM_TOKEN_MISSING")
    return "", blockers


def validate_confirm_token_binding_v1(
    *,
    confirm_token: str,
    expected_binding_sha256: str,
    expected_repository_sha: str,
    expected_scope_digest: str = SESSION_SCOPE,
    expected_session_id: str = TARGET_SESSION_ID,
    expires_at: float,
    previously_seen_fingerprints: frozenset[str] | None = None,
    argv: list[str] | None = None,
) -> dict[str, Any]:
    """Validate confirm-token binding without consuming."""
    blockers = reject_confirm_token_argv_v1(argv)
    format_blockers = validate_token_format(confirm_token)
    blockers.extend(format_blockers)
    if blockers:
        return {
            "ok": False,
            "blockers": sorted(set(blockers)),
            "confirm_token_valid": False,
            "confirm_token_scope_match": False,
            "confirm_token_sha_match": False,
            "fingerprint": "",
            "consumed": False,
            "notes": ["CONFIRM_TOKEN_VALIDATE_FAILED_NO_CONSUME=true"],
        }
    verified = verify_confirm_token_v1(
        **{"confirm_token": confirm_token},
        expected_binding_sha256=expected_binding_sha256,
        session_id=expected_session_id,
        scope_digest=expected_scope_digest,
        expires_at=float(expires_at),
        repository_sha=expected_repository_sha,
        previously_seen_fingerprints=previously_seen_fingerprints,
    )
    blockers.extend(list(verified.blockers))
    scope_ok = "CONFIRM_TOKEN_BINDING_MISMATCH" not in blockers
    sha_ok = scope_ok and verified.ok
    return {
        "ok": bool(verified.ok) and not blockers,
        "blockers": sorted(set(blockers)),
        "confirm_token_valid": bool(verified.ok) and not blockers,
        "confirm_token_scope_match": scope_ok,
        "confirm_token_sha_match": sha_ok,
        "fingerprint": verified.fingerprint,
        "consumed": False,
        "notes": list(verified.notes)
        + [
            "CONFIRM_TOKEN_VALIDATE_ONLY_NO_CONSUME=true",
            "CONFIRM_TOKEN_PLAINTEXT_NOT_RETURNED=true",
        ],
    }


def consume_confirm_token_binding_v1(
    *,
    ledger_path: Path,
    confirm_token_fingerprint: str,
    session_id: str = TARGET_SESSION_ID,
    now_unix: float,
) -> dict[str, Any]:
    """Consume confirm-token by fingerprint only (no plaintext persistence)."""
    fp = str(confirm_token_fingerprint or "").strip()
    if not fp:
        raise ActivationConfirmTokenError("CONFIRM_TOKEN_FINGERPRINT_MISSING")
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    if ledger_path.is_file():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            seen.add(str(row.get("confirm_token_fingerprint") or ""))
    if fp in seen:
        raise ActivationConfirmTokenError("CONFIRM_TOKEN_REPLAY_FORBIDDEN")
    record = {
        "confirm_token_fingerprint": fp,
        "session_id": session_id,
        "consumed_at": float(now_unix),
        "plaintext_persisted": False,
        "single_use": True,
    }
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
    return {
        "ok": True,
        "consumed": True,
        "confirm_token_fingerprint": fp,
        "record_digest": sha256_canonical_v1(record),
        "notes": ["CONFIRM_TOKEN_CONSUMED_AT_START_BOUNDARY=true", "PLAINTEXT_NOT_PERSISTED=true"],
    }


def resolve_confirm_token_presence_v1(
    *,
    confirm_token_in_memory: str | None = None,
    confirm_token_file: Path | None = None,
    confirm_token_present_flag: bool = False,
    environ: Mapping[str, str] | None = None,
) -> bool:
    if confirm_token_in_memory is not None and str(confirm_token_in_memory).strip():
        return True
    return confirm_token_present_via_canonical_path_v1(
        confirm_token_file=confirm_token_file,
        environ=environ,
        confirm_token_present_flag=confirm_token_present_flag,
    )


def fingerprint_only_v1(confirm_token: str) -> str:
    return fingerprint_confirm_token(confirm_token)
