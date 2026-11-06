"""Exactly-once work-unit execution ledger for F1/M9 campaign orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class WorkUnitExactlyOnceError(PermissionError):
    """Fail-closed duplicate work-unit execution."""


WORK_UNIT_LEDGER_FILENAME = "work_unit_execution_ledger.jsonl"


def work_unit_ledger_path_v1(*, campaign_root: Path) -> Path:
    return campaign_root / WORK_UNIT_LEDGER_FILENAME


def _completed_ids(ledger_path: Path) -> set[str]:
    if not ledger_path.is_file():
        return set()
    ids: set[str] = set()
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        sid = str(row.get("session_id") or "")
        if sid:
            ids.add(sid)
    return ids


def record_work_unit_execution_v1(
    *,
    campaign_root: Path,
    session_id: str,
    execution_identity: str,
    allow_record: bool,
) -> dict[str, Any]:
    if not allow_record:
        raise WorkUnitExactlyOnceError("WORK_UNIT_RECORD_NOT_ENABLED")
    ledger = work_unit_ledger_path_v1(campaign_root=campaign_root)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    done = _completed_ids(ledger)
    if session_id in done:
        raise WorkUnitExactlyOnceError("WORK_UNIT_ALREADY_EXECUTED")
    record = {
        "session_id": session_id,
        "execution_identity": execution_identity,
        "single_use": True,
    }
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
    return {"recorded": True, "session_id": session_id}


__all__ = [
    "WorkUnitExactlyOnceError",
    "record_work_unit_execution_v1",
    "work_unit_ledger_path_v1",
]
