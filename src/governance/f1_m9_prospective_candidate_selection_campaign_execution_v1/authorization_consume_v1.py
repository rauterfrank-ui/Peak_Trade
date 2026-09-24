"""Atomic exactly-once runtime authorization consumption for F1/M9 campaign orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.orchestration_constants_v1 import (
    CONSUMPTION_LEDGER_FILENAME,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256


class AuthorizationConsumeError(PermissionError):
    """Fail-closed authorization consumption error."""


def consumption_ledger_path_v1(*, campaign_root: Path) -> Path:
    return campaign_root / "authorization" / CONSUMPTION_LEDGER_FILENAME


def _load_consumed_digests(ledger_path: Path) -> set[str]:
    if not ledger_path.is_file():
        return set()
    digests: set[str] = set()
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        digest = str(row.get("authorization_digest") or "")
        if digest:
            digests.add(digest)
    return digests


def atomic_consume_runtime_authorization_v1(
    *,
    campaign_root: Path,
    authorization_id: str,
    authorization_digest: str,
    execution_identity: str,
    consumed_at_utc: str,
    allow_consume: bool,
) -> dict[str, Any]:
    if not allow_consume:
        raise AuthorizationConsumeError("AUTHORIZATION_CONSUMPTION_NOT_ENABLED")
    if not authorization_id or not authorization_digest:
        raise AuthorizationConsumeError("AUTHORIZATION_IDENTITY_INCOMPLETE")

    ledger_path = consumption_ledger_path_v1(campaign_root=campaign_root)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    consumed = _load_consumed_digests(ledger_path)
    if authorization_digest in consumed:
        raise AuthorizationConsumeError("AUTHORIZATION_ALREADY_CONSUMED")

    record = {
        "authorization_id": authorization_id,
        "authorization_digest": authorization_digest,
        "execution_identity": execution_identity,
        "consumed_at_utc": consumed_at_utc,
        "single_use": True,
    }
    line = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()

    return {
        "consumed": True,
        "consumption_record_digest": compute_content_sha256(record),
        "ledger_path": str(ledger_path),
    }


def verify_authorization_not_replay_source_v1(
    *,
    campaign_root: Path,
    sealed_manifest: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    """Replay must not mint new REAL evidence; sealed manifest required for replay-only."""
    if sealed_manifest is None:
        return ("REPLAY_REQUIRES_SEALED_MANIFEST",)
    if sealed_manifest.get("campaign_sealed") is not True:
        return ("REPLAY_SOURCE_NOT_SEALED",)
    ledger = consumption_ledger_path_v1(campaign_root=campaign_root)
    if not ledger.is_file():
        return ("REPLAY_WITHOUT_PRIOR_AUTHORIZATION_CONSUMPTION",)
    return ()


__all__ = [
    "AuthorizationConsumeError",
    "atomic_consume_runtime_authorization_v1",
    "consumption_ledger_path_v1",
    "verify_authorization_not_replay_source_v1",
]
