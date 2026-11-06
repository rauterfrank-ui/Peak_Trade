"""Historical query/replay without live WebSocket dependency."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
    DurableStorePathsV1,
    default_store_paths_v1,
    load_all_facts_v1,
)


@dataclass(frozen=True)
class HistoricalQueryResultV1:
    facts: tuple[Mapping[str, Any], ...]
    source: str
    live_ws_required: bool


def query_historical_facts_v1(
    store_root: Path,
    *,
    fact_kind: Optional[str] = None,
    venue_native_id: Optional[str] = None,
) -> HistoricalQueryResultV1:
    paths = default_store_paths_v1(store_root)
    rows = load_all_facts_v1(paths)
    filtered: list[Mapping[str, Any]] = []
    for row in rows:
        if fact_kind and row.get("fact_kind") != fact_kind:
            continue
        inst = row.get("instrument") or {}
        if venue_native_id and inst.get("venue_native_id") != venue_native_id:
            continue
        filtered.append(row)
    return HistoricalQueryResultV1(
        facts=tuple(filtered),
        source="durable_store",
        live_ws_required=False,
    )


def replay_ranking_marks_from_store_v1(store_root: Path) -> Sequence[Mapping[str, Any]]:
    result = query_historical_facts_v1(store_root, fact_kind="FinalizedPt1mMarkFactV1")
    return result.facts
