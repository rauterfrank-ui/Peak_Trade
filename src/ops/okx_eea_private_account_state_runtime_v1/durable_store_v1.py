"""Durable private-state projections and reconciliation snapshots."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import STATE_STORE_SCHEMA
from src.ops.okx_eea_private_account_state_runtime_v1.state_contracts_v1 import (
    PrivateStateRecordV1,
    body_digest,
)


class DurablePrivateStoreError(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class DurablePrivateStorePathsV1:
    normalized_state: Path
    reconciliation_snapshots: Path
    provenance_index: Path
    fill_dedup_index: Path


def default_private_store_paths_v1(root: Path) -> DurablePrivateStorePathsV1:
    base = root / "okx_eea_private_account_state_runtime_v1"
    return DurablePrivateStorePathsV1(
        normalized_state=base / "normalized_private_state.jsonl",
        reconciliation_snapshots=base / "reconciliation_snapshots.jsonl",
        provenance_index=base / "provenance_index.jsonl",
        fill_dedup_index=base / "fill_trade_ids.jsonl",
    )


def append_private_state_v1(
    paths: DurablePrivateStorePathsV1, payload: Mapping[str, Any]
) -> PrivateStateRecordV1:
    paths.normalized_state.parent.mkdir(parents=True, exist_ok=True)
    digest = body_digest(payload)
    record = PrivateStateRecordV1(
        schema_version=STATE_STORE_SCHEMA,
        state_digest=digest,
        payload=dict(payload),
        persisted_at=_utc_now(),
    )
    line = json.dumps(record.to_dict(), sort_keys=True) + "\n"
    with paths.normalized_state.open("a", encoding="utf-8") as fh:
        fh.write(line)
    prov = payload.get("provenance")
    if prov:
        with paths.provenance_index.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "state_digest": digest,
                        "provenance": prov,
                        "persisted_at": record.persisted_at,
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    if payload.get("fact_kind") == "FillFactV1":
        trade_id = str(payload.get("tradeId") or "")
        if trade_id:
            with paths.fill_dedup_index.open("a", encoding="utf-8") as fh:
                fh.write(
                    json.dumps({"tradeId": trade_id, "state_digest": digest}, sort_keys=True) + "\n"
                )
    return record


def load_all_private_state_v1(paths: DurablePrivateStorePathsV1) -> list[Mapping[str, Any]]:
    if not paths.normalized_state.is_file():
        return []
    out: list[Mapping[str, Any]] = []
    for line in paths.normalized_state.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        out.append(row.get("payload") or row)
    return out


def load_known_fill_trade_ids_v1(paths: DurablePrivateStorePathsV1) -> set[str]:
    if not paths.fill_dedup_index.is_file():
        return set()
    ids: set[str] = set()
    for line in paths.fill_dedup_index.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        tid = str(row.get("tradeId") or "")
        if tid:
            ids.add(tid)
    return ids
