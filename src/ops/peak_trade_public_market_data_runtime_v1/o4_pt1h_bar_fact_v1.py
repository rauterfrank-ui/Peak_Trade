"""Finalized PT1H O4 bar facts for WP-A historical query (DDO o4_bars compatible)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping, Sequence

from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import O4_AUTHORITATIVE_INTERVAL
from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
    append_fact_v1,
    default_store_paths_v1,
    load_all_facts_v1,
)

FACT_KIND_FINALIZED_PT1H_O4_BAR: Final[str] = "FinalizedPt1hO4BarFactV1"
O4_BAR_ELEMENT_REQUIRED_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "canonical_instrument_id",
        "venue_instrument_id",
        "venue",
        "interval",
        "bar_open_time",
        "bar_close_time",
        "finalization_state",
        "quality_state",
        "last_observation_identity",
        "session_id",
        "repository_sha",
        "config_digest",
        "close",
        "revision",
    }
)


def canonical_bar_envelope_to_o4_bar_element_v1(envelope: Mapping[str, Any]) -> dict[str, Any]:
    """Map authoritative O4 envelope fields to DDO bridge bar element shape."""
    missing = sorted(O4_BAR_ELEMENT_REQUIRED_FIELDS - set(envelope.keys()))
    if missing:
        raise ValueError(f"O4_ENVELOPE_MISSING_FIELDS:{missing}")
    return {
        "canonical_instrument_id": envelope["canonical_instrument_id"],
        "venue_instrument_id": envelope["venue_instrument_id"],
        "venue": envelope["venue"],
        "interval": envelope["interval"],
        "bar_open_time": float(envelope["bar_open_time"]),
        "bar_close_time": float(envelope["bar_close_time"]),
        "finalization_state": str(envelope["finalization_state"]),
        "quality_state": str(envelope["quality_state"]),
        "last_observation_identity": dict(envelope["last_observation_identity"]),
        "session_id": envelope["session_id"],
        "repository_sha": envelope["repository_sha"],
        "config_digest": envelope["config_digest"],
        "close": float(envelope["close"]),
        "revision": int(envelope["revision"]),
    }


@dataclass(frozen=True)
class FinalizedPt1hO4BarFactV1:
    bar: Mapping[str, Any]
    fact_kind: str = FACT_KIND_FINALIZED_PT1H_O4_BAR

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_kind": self.fact_kind,
            "interval_id": O4_AUTHORITATIVE_INTERVAL,
            "bar": dict(self.bar),
            "bar_open_time": float(self.bar["bar_open_time"]),
            "canonical_instrument_id": str(self.bar["canonical_instrument_id"]),
        }


def append_finalized_pt1h_o4_bar_fact_v1(
    store_root: Path, *, bar_element: Mapping[str, Any]
) -> str:
    """Append one finalized PT1H O4 bar fact; returns fact_digest."""
    element = canonical_bar_envelope_to_o4_bar_element_v1(bar_element)
    if str(element.get("interval", "")).upper() not in {"PT1H", "1H", "60M"}:
        raise ValueError("O4_BAR_INTERVAL_MUST_BE_PT1H")
    paths = default_store_paths_v1(store_root)
    record = append_fact_v1(paths, FinalizedPt1hO4BarFactV1(bar=element).to_dict())
    return record.fact_digest


def load_finalized_pt1h_o4_bar_elements_v1(store_root: Path) -> tuple[dict[str, Any], ...]:
    """Load deduplicated finalized O4 bar elements from WP-A durable store."""
    paths = default_store_paths_v1(store_root)
    rows = load_all_facts_v1(paths)
    by_open: dict[tuple[str, float], dict[str, Any]] = {}
    for row in rows:
        if row.get("fact_kind") != FACT_KIND_FINALIZED_PT1H_O4_BAR:
            continue
        bar_raw = row.get("bar")
        if not isinstance(bar_raw, Mapping):
            continue
        bar = canonical_bar_envelope_to_o4_bar_element_v1(bar_raw)
        key = (str(bar["canonical_instrument_id"]), float(bar["bar_open_time"]))
        by_open[key] = bar
    return tuple(bar for _, bar in sorted(by_open.items(), key=lambda item: item[0][1]))


def sync_finalized_envelopes_to_wp_a_store_v1(
    store_root: Path,
    envelopes: Sequence[Mapping[str, Any]],
    *,
    finalized_states: frozenset[str],
) -> dict[str, Any]:
    """Persist newly finalized O4 envelopes into WP-A facts (idempotent by bar open)."""
    existing = {
        (str(b["canonical_instrument_id"]), float(b["bar_open_time"]))
        for b in load_finalized_pt1h_o4_bar_elements_v1(store_root)
    }
    appended = 0
    skipped = 0
    for env in envelopes:
        if str(env.get("finalization_state") or "") not in finalized_states:
            continue
        bar = canonical_bar_envelope_to_o4_bar_element_v1(env)
        key = (str(bar["canonical_instrument_id"]), float(bar["bar_open_time"]))
        if key in existing:
            skipped += 1
            continue
        append_finalized_pt1h_o4_bar_fact_v1(store_root, bar_element=bar)
        existing.add(key)
        appended += 1
    return {
        "appended": appended,
        "skipped": skipped,
        "store_root": str(store_root),
    }
