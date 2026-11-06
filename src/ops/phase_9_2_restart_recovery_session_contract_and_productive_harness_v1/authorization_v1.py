"""Fixture-level single-use authorization binding for restart segments.

This module never issues live authorizations and never starts a network session.
It only records and enforces single-use consumption inside controlled fixture
ledgers for the productive harness contract.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.constants_v1 import (
    AUTHORIZATION_LEDGER_FILENAME,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.digest_v1 import (
    sha256_canonical_v1,
)


class RestartAuthorizationError(RuntimeError):
    """Fail-closed authorization error for restart harness fixtures."""


def authorization_digest_v1(
    *,
    authorization_id: str,
    segment_role: str,
    restart_campaign_id: str,
    runtime_session_id: str,
) -> str:
    return sha256_canonical_v1(
        {
            "authorization_id": authorization_id,
            "segment_role": segment_role,
            "restart_campaign_id": restart_campaign_id,
            "runtime_session_id": runtime_session_id,
            "single_use": True,
        }
    )


def load_consumed_authorization_ids_v1(ledger_path: Path) -> set[str]:
    if not ledger_path.is_file():
        return set()
    consumed: set[str] = set()
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        consumed.add(str(row["authorization_id"]))
    return consumed


def consume_authorization_once_v1(
    *,
    ledger_path: Path,
    authorization_id: str,
    authorization_digest: str,
    segment_id: str,
    segment_role: str,
    runtime_session_id: str,
) -> dict[str, Any]:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    consumed = load_consumed_authorization_ids_v1(ledger_path)
    if authorization_id in consumed:
        raise RestartAuthorizationError("authorization_reuse_forbidden")
    record = {
        "authorization_id": authorization_id,
        "authorization_digest": authorization_digest,
        "segment_id": segment_id,
        "segment_role": segment_role,
        "runtime_session_id": runtime_session_id,
        "single_use": True,
        "reused": False,
    }
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
    return record


def ledger_path_for_root_v1(persistence_root: Path) -> Path:
    return Path(persistence_root) / AUTHORIZATION_LEDGER_FILENAME
