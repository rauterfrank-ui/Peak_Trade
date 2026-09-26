"""Tiered semantic durability for normalized public facts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import FACT_STORE_SCHEMA
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import (
    PublicMarketFactRecordV1,
    fact_digest,
)


class DurableStoreError(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class DurableStorePathsV1:
    finalized_facts: Path
    provenance_index: Path
    raw_bounded: Path


def default_store_paths_v1(root: Path) -> DurableStorePathsV1:
    base = root / "peak_trade_public_market_data_runtime_v1"
    return DurableStorePathsV1(
        finalized_facts=base / "normalized_finalized_facts.jsonl",
        provenance_index=base / "provenance_index.jsonl",
        raw_bounded=base / "raw_bounded",
    )


def append_fact_v1(
    paths: DurableStorePathsV1, payload: Mapping[str, Any]
) -> PublicMarketFactRecordV1:
    paths.finalized_facts.parent.mkdir(parents=True, exist_ok=True)
    digest = fact_digest(payload)
    record = PublicMarketFactRecordV1(
        schema_version=FACT_STORE_SCHEMA,
        fact_digest=digest,
        payload=dict(payload),
        persisted_at=_utc_now(),
    )
    line = json.dumps(record.to_dict(), sort_keys=True) + "\n"
    with paths.finalized_facts.open("a", encoding="utf-8") as fh:
        fh.write(line)
    prov_line = (
        json.dumps(
            {
                "fact_digest": digest,
                "provenance": payload.get("provenance"),
                "persisted_at": record.persisted_at,
            },
            sort_keys=True,
        )
        + "\n"
    )
    with paths.provenance_index.open("a", encoding="utf-8") as fh:
        fh.write(prov_line)
    return record


def load_all_facts_v1(paths: DurableStorePathsV1) -> list[Mapping[str, Any]]:
    if not paths.finalized_facts.is_file():
        return []
    out: list[Mapping[str, Any]] = []
    for line in paths.finalized_facts.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        out.append(row.get("payload") or row)
    return out


def append_bounded_raw_v1(
    paths: DurableStorePathsV1, name: str, body: bytes, *, max_files: int = 32
) -> Path:
    paths.raw_bounded.mkdir(parents=True, exist_ok=True)
    target = paths.raw_bounded / name
    target.write_bytes(body)
    existing = sorted(paths.raw_bounded.glob("*"))
    if len(existing) > max_files:
        for old in existing[: len(existing) - max_files]:
            old.unlink(missing_ok=True)
    return target
