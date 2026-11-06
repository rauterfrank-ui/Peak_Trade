"""Partition planner — monthly immutable partitions with lifecycle bounds."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from src.research.longer_chronological_pit_acquisition_v1 import (
    DATASET_ID,
    FREQUENCY,
    MARKET_TYPE,
    TARGET_PERIOD_END,
    TARGET_PERIOD_START,
    VENUE,
)

_BTC_BASES = frozenset({"BTC", "XBT", "WBTC", "BTCB"})
_SPOT_MARKERS = frozenset({"SPOT", "MARGIN"})


class PartitionPlanError(ValueError):
    """Fail-closed partition planning error."""


@dataclass(frozen=True)
class InstrumentLifecycleV1:
    instrument_id: str
    native_instrument_id: str
    base_asset: str
    quote_asset: str
    market_type: str
    listing_time: str | None
    delisting_time: str | None
    state: str = "KNOWN"


def _parse_utc(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def _fmt(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _month_starts(period_start: str, period_end: str) -> list[tuple[datetime, datetime]]:
    start = _parse_utc(period_start)
    end = _parse_utc(period_end)
    if end <= start:
        raise PartitionPlanError("INVALID_PERIOD_ORDER")
    cur = datetime(start.year, start.month, 1, tzinfo=timezone.utc)
    out: list[tuple[datetime, datetime]] = []
    while cur < end:
        if cur.month == 12:
            nxt = datetime(cur.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            nxt = datetime(cur.year, cur.month + 1, 1, tzinfo=timezone.utc)
        seg_start = max(cur, start)
        seg_end = min(nxt, end)
        if seg_end > seg_start:
            out.append((seg_start, seg_end))
        cur = nxt
    return out


def _is_btc(inst: InstrumentLifecycleV1) -> bool:
    base = inst.base_asset.upper()
    if base in _BTC_BASES:
        return True
    # also catch native ids like BTC-USDT-SWAP
    native = inst.native_instrument_id.upper()
    return bool(re.search(r"(^|[^A-Z])(BTC|XBT|WBTC)([^A-Z]|$)", native))


def _is_spot(inst: InstrumentLifecycleV1) -> bool:
    mt = inst.market_type.upper()
    if mt in _SPOT_MARKERS or "SPOT" in mt:
        return True
    native = inst.native_instrument_id.upper()
    return native.endswith("-USDT") and not native.endswith("-SWAP") and "SWAP" not in native


def assert_instrument_admissible(inst: InstrumentLifecycleV1) -> None:
    if inst.state.upper() in {"UNKNOWN", "UNTRUSTED", ""}:
        raise PartitionPlanError(f"UNKNOWN_INSTRUMENT_STATE:{inst.instrument_id}")
    if _is_btc(inst):
        raise PartitionPlanError(f"BTC_EXCLUDED:{inst.instrument_id}")
    if _is_spot(inst):
        raise PartitionPlanError(f"SPOT_EXCLUDED:{inst.instrument_id}")
    if inst.market_type.lower() not in {
        "linear_usdt_perpetual",
        "linear_perpetual",
        MARKET_TYPE,
    }:
        # allow linear_perpetual alias from universe schema
        if "linear" not in inst.market_type.lower() or "perp" not in inst.market_type.lower():
            raise PartitionPlanError(f"MARKET_TYPE_EXCLUDED:{inst.instrument_id}")


def partition_id_for(
    *,
    instrument_id: str,
    period_start: str,
    period_end: str,
    kind: str = "ohlcv_pt1h",
) -> str:
    raw = f"{DATASET_ID}|{instrument_id}|{period_start}|{period_end}|{kind}|{FREQUENCY}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    # human-stable prefix
    yyyymm = period_start[0:4] + period_start[5:7]
    safe_inst = re.sub(r"[^a-zA-Z0-9_\-]+", "_", instrument_id)[:64]
    return f"{kind}_{safe_inst}_{yyyymm}_{digest}"


def plan_partitions_for_instrument(
    inst: InstrumentLifecycleV1,
    *,
    period_start: str = TARGET_PERIOD_START,
    period_end: str = TARGET_PERIOD_END,
    kind: str = "ohlcv_pt1h",
) -> list[dict[str, Any]]:
    assert_instrument_admissible(inst)
    listing = _parse_utc(inst.listing_time) if inst.listing_time else None
    delisting = _parse_utc(inst.delisting_time) if inst.delisting_time else None
    rows: list[dict[str, Any]] = []
    for seg_start, seg_end in _month_starts(period_start, period_end):
        # clip to lifecycle
        if listing is not None and seg_end <= listing:
            continue
        if delisting is not None and seg_start >= delisting:
            continue
        clipped_start = max(seg_start, listing) if listing is not None else seg_start
        clipped_end = min(seg_end, delisting) if delisting is not None else seg_end
        if clipped_end <= clipped_start:
            continue
        ps = _fmt(clipped_start)
        pe = _fmt(clipped_end)
        pid = partition_id_for(
            instrument_id=inst.instrument_id,
            period_start=ps,
            period_end=pe,
            kind=kind,
        )
        rows.append(
            {
                "partition_id": pid,
                "dataset_id": DATASET_ID,
                "venue": VENUE,
                "market_type": MARKET_TYPE,
                "instrument_id": inst.instrument_id,
                "native_instrument_id": inst.native_instrument_id,
                "normalized_symbol": inst.native_instrument_id,
                "period_start": ps,
                "period_end": pe,
                "frequency": FREQUENCY,
                "kind": kind,
                "status": "PLANNED",
            }
        )
    return rows


def plan_partitions(
    instruments: Sequence[InstrumentLifecycleV1 | Mapping[str, Any]],
    *,
    period_start: str = TARGET_PERIOD_START,
    period_end: str = TARGET_PERIOD_END,
    kind: str = "ohlcv_pt1h",
    max_partitions: int | None = None,
) -> dict[str, Any]:
    planned: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    for raw in instruments:
        if isinstance(raw, InstrumentLifecycleV1):
            inst = raw
        else:
            inst = InstrumentLifecycleV1(
                instrument_id=str(raw["instrument_id"]),
                native_instrument_id=str(raw["native_instrument_id"]),
                base_asset=str(raw.get("base_asset") or ""),
                quote_asset=str(raw.get("quote_asset") or "USDT"),
                market_type=str(raw.get("market_type") or MARKET_TYPE),
                listing_time=raw.get("listing_time"),  # type: ignore[arg-type]
                delisting_time=raw.get("delisting_time"),  # type: ignore[arg-type]
                state=str(raw.get("state") or "KNOWN"),
            )
        try:
            planned.extend(
                plan_partitions_for_instrument(
                    inst,
                    period_start=period_start,
                    period_end=period_end,
                    kind=kind,
                )
            )
        except PartitionPlanError as exc:
            excluded.append({"instrument_id": inst.instrument_id, "reason": str(exc)})
    planned.sort(key=lambda r: (r["period_start"], r["instrument_id"], r["partition_id"]))
    truncated = False
    if max_partitions is not None and len(planned) > max_partitions:
        planned = planned[: max(0, int(max_partitions))]
        truncated = True
    return {
        "dataset_id": DATASET_ID,
        "period_start": period_start,
        "period_end": period_end,
        "frequency": FREQUENCY,
        "partition_scheme": "monthly_clipped_to_lifecycle",
        "partition_count": len(planned),
        "truncated": truncated,
        "partitions": planned,
        "excluded": excluded,
    }
