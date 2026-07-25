"""Selected-instrument OKX OHLCV readmodel materializer (public candles + trades)."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.okx_captured_at_freshness_policy_v1 import (
    classify_freshness_v1,
    load_freshness_policy_v1,
    provider_ms_to_utc_iso,
    utc_now_iso,
)
from src.ops.okx_public_market_data_client_v1 import OkxPublicMarketDataClientV1

PACKAGE_MARKER = "OKX_SELECTED_INSTRUMENT_OHLCV_READMODEL_V1=true"
OHLCV_SCHEMA = "okx_selected_instrument_ohlcv_readmodel.v1"
OHLCV_RELATIVE_PATH = "readmodels/okx_selected_instrument_ohlcv_readmodel.v1.json"
UNIVERSE_SELECTION_RELATIVE_PATH = "readmodels/universe_selection_readmodel.v1.json"
REFRESH_LOCK_NAME = ".okx_selected_instrument_ohlcv_refresh.lock"
DEFAULT_BAR = "1H"
DEFAULT_LIMIT = 100
DEFAULT_TRADES_LIMIT = 100
MAX_APPLIED_TRADE_IDS = 500
# Recent candles endpoint includes the incomplete open candle (confirm=0).
OKX_CANDLES_PATH = "/api/v5/market/candles"
# Public recent trades — server-side only; revises the active open PT1H candle.
OKX_TRADES_PATH = "/api/v5/market/trades"
OKX_MARK_PRICE_PATH = "/api/v5/public/mark-price"
LIVE_MARK_PROJECTION_V1 = "okx_ohlcv_live_mark_v1"
OPEN_CANDLE_LIVE_SOURCE_V1 = "okx_public_trades_into_pt1h_v1"
# OKX SWAP trade `sz` is contract count (not quote/base currency).
TRADE_VOLUME_UNIT = "contracts"
# Bounded dashboard refresh: visible intrabar feedback ≤5s under normal availability.
DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS = 3


class OkxOhlcvReadmodelError(ValueError):
    """Fail-closed OHLCV materialization error."""


@dataclass(frozen=True)
class OhlcvBarV1:
    ts: str
    open: str
    high: str
    low: str
    close: str
    volume: str
    volume_ccy: str | None
    confirm: bool
    provider_ts_ms: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OkxPublicTradeV1:
    """One authentic OKX public trade print (`/api/v5/market/trades`)."""

    trade_id: str
    price: str
    size: str
    side: str
    ts: str
    provider_ts_ms: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def _dec(value: Any, *, field: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise OkxOhlcvReadmodelError(f"INVALID_OHLCV_NUMBER:{field}") from exc
    return parsed


def _bar_ohlcv_tuple(bar: OhlcvBarV1) -> tuple[str, str, str, str, str]:
    return (bar.open, bar.high, bar.low, bar.close, bar.volume)


def _as_ohlcv_bar(raw: Mapping[str, Any] | OhlcvBarV1) -> OhlcvBarV1:
    if isinstance(raw, OhlcvBarV1):
        return raw
    confirm_raw = raw.get("confirm")
    if confirm_raw is None:
        confirm = True
    elif isinstance(confirm_raw, bool):
        confirm = confirm_raw
    else:
        confirm = str(confirm_raw) in {"1", "true", "True"}
    return OhlcvBarV1(
        ts=str(raw["ts"]),
        open=format(_dec(raw.get("open"), field="open"), "f"),
        high=format(_dec(raw.get("high"), field="high"), "f"),
        low=format(_dec(raw.get("low"), field="low"), "f"),
        close=format(_dec(raw.get("close"), field="close"), "f"),
        volume=format(_dec(raw.get("volume"), field="volume"), "f"),
        volume_ccy=(
            None
            if raw.get("volume_ccy") in (None, "")
            else format(_dec(raw.get("volume_ccy"), field="volume_ccy"), "f")
        ),
        confirm=confirm,
        provider_ts_ms=str(raw.get("provider_ts_ms") or ""),
    )


def reduce_okx_ohlcv_bars_v1(
    previous: Sequence[Mapping[str, Any] | OhlcvBarV1] | None,
    incoming: Sequence[Mapping[str, Any] | OhlcvBarV1],
    *,
    interval_seconds: int = 3600,
) -> tuple[list[OhlcvBarV1], str]:
    """Reduce authentic OKX candle series revisions for one selected instrument.

    Revision kinds:
    - BOOTSTRAP: no previous series
    - NO_OP: same final timestamp and identical O/H/L/C/V
    - SAME_TIMESTAMP_REVISION: final timestamp equal, OHLCV changed → replace tip only
    - NEW_INTERVAL_APPEND: final timestamp advanced by exactly one interval → append once
    - AUTHENTIC_FULL_REPLACE: longer authentic window / bootstrap alignment from OKX

    Open-candle invariants for SAME_TIMESTAMP_REVISION:
    open fixed; high may only increase; low may only decrease; close/volume follow source.
    """
    if not incoming:
        raise OkxOhlcvReadmodelError("OHLCV_REDUCE_EMPTY_INCOMING")
    nxt = [_as_ohlcv_bar(b) for b in incoming]
    nxt.sort(key=lambda b: b.ts)
    seen: set[str] = set()
    for bar in nxt:
        if bar.ts in seen:
            raise OkxOhlcvReadmodelError(f"DUPLICATE_CANDLE_TIMESTAMP:{bar.ts}")
        seen.add(bar.ts)

    if not previous:
        return nxt, "BOOTSTRAP"

    prev = [_as_ohlcv_bar(b) for b in previous]
    prev.sort(key=lambda b: b.ts)
    if not prev:
        return nxt, "BOOTSTRAP"

    prev_last = prev[-1]
    next_last = nxt[-1]
    if prev_last.ts == next_last.ts:
        if len(prev) != len(nxt):
            # Same tip timestamp but different window length — accept authentic OKX window
            # only when historical prefixes for the overlapping closed range are unchanged.
            return nxt, "AUTHENTIC_FULL_REPLACE"
        for older_p, older_n in zip(prev[:-1], nxt[:-1]):
            if older_p.ts != older_n.ts or _bar_ohlcv_tuple(older_p) != _bar_ohlcv_tuple(older_n):
                # Authentic upstream correction of sealed history → accept OKX window.
                return nxt, "AUTHENTIC_FULL_REPLACE"
        if _bar_ohlcv_tuple(prev_last) == _bar_ohlcv_tuple(next_last):
            # Identical OHLCV at same timestamp is a no-op (preserve prior confirm/metadata).
            return prev, "NO_OP"
        # Open-candle revision rules.
        if _dec(next_last.open, field="open") != _dec(prev_last.open, field="open"):
            raise OkxOhlcvReadmodelError(f"OPEN_REGRESSION:{prev_last.ts}")
        if _dec(next_last.high, field="high") < _dec(prev_last.high, field="high"):
            raise OkxOhlcvReadmodelError(f"HIGH_REGRESSION:{prev_last.ts}")
        if _dec(next_last.low, field="low") > _dec(prev_last.low, field="low"):
            raise OkxOhlcvReadmodelError(f"LOW_REGRESSION:{prev_last.ts}")
        if _dec(next_last.volume, field="volume") < 0:
            raise OkxOhlcvReadmodelError(f"NEGATIVE_VOLUME:{prev_last.ts}")
        # Open tip volume is monotonic non-decreasing across authentic revisions
        # (candles + prior trade aggregation must never regress volume).
        prev_vol = _dec(prev_last.volume, field="volume")
        next_vol = _dec(next_last.volume, field="volume")
        if (not prev_last.confirm) and (not next_last.confirm) and next_vol < prev_vol:
            next_last = OhlcvBarV1(
                ts=next_last.ts,
                open=next_last.open,
                high=next_last.high,
                low=next_last.low,
                close=next_last.close,
                volume=prev_last.volume,
                volume_ccy=next_last.volume_ccy or prev_last.volume_ccy,
                confirm=False,
                provider_ts_ms=next_last.provider_ts_ms,
            )
        reduced = list(prev[:-1]) + [next_last]
        return reduced, "SAME_TIMESTAMP_REVISION"

    prev_dt = datetime.fromisoformat(prev_last.ts.replace("Z", "+00:00"))
    next_dt = datetime.fromisoformat(next_last.ts.replace("Z", "+00:00"))
    delta = (next_dt - prev_dt).total_seconds()
    if abs(delta - float(interval_seconds)) <= 1e-9:
        # Seal prior tip from incoming prefix when present; else mark previous tip closed.
        sealed = prev_last
        if len(nxt) >= 2 and nxt[-2].ts == prev_last.ts:
            sealed = nxt[-2]
            if not sealed.confirm:
                sealed = OhlcvBarV1(
                    ts=sealed.ts,
                    open=sealed.open,
                    high=sealed.high,
                    low=sealed.low,
                    close=sealed.close,
                    volume=sealed.volume,
                    volume_ccy=sealed.volume_ccy,
                    confirm=True,
                    provider_ts_ms=sealed.provider_ts_ms,
                )
        elif not sealed.confirm:
            sealed = OhlcvBarV1(
                ts=sealed.ts,
                open=sealed.open,
                high=sealed.high,
                low=sealed.low,
                close=sealed.close,
                volume=sealed.volume,
                volume_ccy=sealed.volume_ccy,
                confirm=True,
                provider_ts_ms=sealed.provider_ts_ms,
            )
        # Historical prefix before sealed tip must remain unchanged when lengths align.
        if len(prev) >= 2 and len(nxt) >= 2 and nxt[-2].ts == sealed.ts:
            overlap_prev = prev[:-1]
            overlap_in = nxt[:-2]
            if len(overlap_in) == len(overlap_prev):
                for older_p, older_n in zip(overlap_prev, overlap_in):
                    if older_p.ts != older_n.ts or _bar_ohlcv_tuple(older_p) != _bar_ohlcv_tuple(
                        older_n
                    ):
                        return nxt, "AUTHENTIC_FULL_REPLACE"
        reduced = list(prev[:-1]) + [sealed, next_last]
        return reduced, "NEW_INTERVAL_APPEND"

    # Non-adjacent advance or rewind: accept only full authentic replacement window.
    return nxt, "AUTHENTIC_FULL_REPLACE"


def merge_open_tip_cumulative_interval_volume_v1(
    previous_bars: Sequence[Mapping[str, Any] | OhlcvBarV1] | None,
    next_bars: Sequence[Mapping[str, Any] | OhlcvBarV1],
) -> tuple[list[OhlcvBarV1], dict[str, Any]]:
    """MODEL_A: cumulative open-tip volume is monotonic non-decreasing.

    OKX ``/market/candles`` tip volume may temporarily under-report relative to a
    prior trade-augmented cumulative tip (AUTHENTIC_FULL_REPLACE / window churn).
    Closed historical candles are never rewritten.
    """
    nxt = [_as_ohlcv_bar(b) for b in next_bars]
    meta: dict[str, Any] = {
        "volume_semantic_model": "MODEL_A_CUMULATIVE_INTERVAL_VOLUME",
        "open_tip_volume_preserved": False,
        "open_tip_high_merged": False,
        "open_tip_low_merged": False,
    }
    if not previous_bars or not nxt:
        return nxt, meta
    prev = [_as_ohlcv_bar(b) for b in previous_bars]
    if not prev:
        return nxt, meta
    prev_tip = prev[-1]
    next_tip = nxt[-1]
    if prev_tip.ts != next_tip.ts:
        return nxt, meta
    if prev_tip.confirm or next_tip.confirm:
        # Sealed tip must remain immutable; do not re-open or rewrite.
        return nxt, meta
    if _dec(next_tip.open, field="open") != _dec(prev_tip.open, field="open"):
        raise OkxOhlcvReadmodelError(f"OPEN_REGRESSION:{prev_tip.ts}")

    prev_high = _dec(prev_tip.high, field="high")
    next_high = _dec(next_tip.high, field="high")
    prev_low = _dec(prev_tip.low, field="low")
    next_low = _dec(next_tip.low, field="low")
    prev_vol = _dec(prev_tip.volume, field="volume")
    next_vol = _dec(next_tip.volume, field="volume")

    merged_high = max(prev_high, next_high)
    merged_low = min(prev_low, next_low)
    merged_vol = max(prev_vol, next_vol)
    meta["open_tip_high_merged"] = merged_high != next_high
    meta["open_tip_low_merged"] = merged_low != next_low
    meta["open_tip_volume_preserved"] = merged_vol != next_vol

    if (
        merged_high == next_high
        and merged_low == next_low
        and merged_vol == next_vol
        and next_tip.close == prev_tip.close
    ):
        return nxt, meta

    merged_tip = OhlcvBarV1(
        ts=next_tip.ts,
        open=next_tip.open,
        high=format(merged_high, "f"),
        low=format(merged_low, "f"),
        close=next_tip.close,
        volume=format(merged_vol, "f"),
        volume_ccy=next_tip.volume_ccy or prev_tip.volume_ccy,
        confirm=False,
        provider_ts_ms=next_tip.provider_ts_ms or prev_tip.provider_ts_ms,
    )
    return list(nxt[:-1]) + [merged_tip], meta


def parse_okx_public_trades_v1(rows: Sequence[Any]) -> list[OkxPublicTradeV1]:
    """Parse OKX public trades rows (newest-first dicts with tradeId/px/sz/side/ts)."""
    out: list[OkxPublicTradeV1] = []
    seen: set[str] = set()
    for raw in rows:
        if not isinstance(raw, Mapping):
            continue
        trade_id = str(raw.get("tradeId") or "").strip()
        if not trade_id or trade_id in seen:
            continue
        ts_iso = provider_ms_to_utc_iso(raw.get("ts"))
        if ts_iso is None:
            continue
        px = format(_dec(raw.get("px"), field="trade_px"), "f")
        sz = format(_dec(raw.get("sz"), field="trade_sz"), "f")
        if _dec(sz, field="trade_sz") < 0:
            raise OkxOhlcvReadmodelError(f"NEGATIVE_TRADE_SIZE:{trade_id}")
        seen.add(trade_id)
        out.append(
            OkxPublicTradeV1(
                trade_id=trade_id,
                price=px,
                size=sz,
                side=str(raw.get("side") or "").strip().lower(),
                ts=ts_iso,
                provider_ts_ms=str(raw.get("ts") or ""),
            )
        )
    out.sort(key=lambda t: (int(t.provider_ts_ms or "0"), t.trade_id))
    return out


def _bucket_start_utc(ts_iso: str, *, interval_seconds: int) -> datetime:
    dt = datetime.fromisoformat(ts_iso.replace("Z", "+00:00")).astimezone(timezone.utc)
    if interval_seconds != 3600:
        raise OkxOhlcvReadmodelError("UNSUPPORTED_TRADE_BUCKET_INTERVAL")
    return dt.replace(minute=0, second=0, microsecond=0)


def apply_okx_public_trades_to_open_candle_v1(
    bars: Sequence[Mapping[str, Any] | OhlcvBarV1],
    trades: Sequence[OkxPublicTradeV1],
    *,
    previously_applied_trade_ids: Sequence[str] | None = None,
    interval_seconds: int = 3600,
) -> tuple[list[OhlcvBarV1], str, list[str], dict[str, Any]]:
    """Revise the active PT1H candle from authentic OKX public trades.

    Bootstrap rule: when no trade IDs were applied yet, seed IDs already present in
    the current bucket without mutating geometry (candle bootstrap already priced
    them). Subsequent new trade IDs revise the open tip:

    - open preserved from candle bootstrap (or first trade when appending a bucket)
    - high = max(previous high, trade price)
    - low = min(previous low, trade price)
    - close = newest applied trade price
    - volume += trade size (OKX SWAP ``sz`` = contracts)
    - closed historical candles are never rewritten
    """
    if not bars:
        raise OkxOhlcvReadmodelError("TRADE_REDUCE_EMPTY_BARS")
    working = [_as_ohlcv_bar(b) for b in bars]
    working.sort(key=lambda b: b.ts)
    applied = {str(x) for x in (previously_applied_trade_ids or []) if str(x)}
    meta: dict[str, Any] = {
        "old_trade_count": 0,
        "duplicate_trade_count": 0,
        "new_trade_count": 0,
        "seeded": False,
        "trade_volume_unit": TRADE_VOLUME_UNIT,
    }
    if not trades:
        return working, "NO_OP", sorted(applied)[-MAX_APPLIED_TRADE_IDS:], meta

    tip = working[-1]
    tip_start = datetime.fromisoformat(tip.ts.replace("Z", "+00:00")).astimezone(timezone.utc)
    tip_end = tip_start + timedelta(seconds=interval_seconds)

    # First observation after candle bootstrap / new bucket: seed current-bucket
    # IDs only so candle-included prints are not double-counted into volume.
    if previously_applied_trade_ids is None:
        seeded = [
            t.trade_id
            for t in trades
            if tip_start
            <= datetime.fromisoformat(t.ts.replace("Z", "+00:00")).astimezone(timezone.utc)
            < tip_end
        ]
        meta["seeded"] = True
        meta["new_trade_count"] = 0
        return working, "NO_OP", seeded[-MAX_APPLIED_TRADE_IDS:], meta

    revision_kind = "NO_OP"
    for trade in trades:
        trade_dt = datetime.fromisoformat(trade.ts.replace("Z", "+00:00")).astimezone(timezone.utc)
        tip = working[-1]
        tip_start = datetime.fromisoformat(tip.ts.replace("Z", "+00:00")).astimezone(timezone.utc)
        tip_end = tip_start + timedelta(seconds=interval_seconds)
        px = _dec(trade.price, field="trade_px")
        sz = _dec(trade.size, field="trade_sz")

        if trade_dt < tip_start:
            meta["old_trade_count"] += 1
            continue

        if trade.trade_id in applied:
            meta["duplicate_trade_count"] += 1
            continue

        if trade_dt >= tip_end:
            # Next PT1H bucket from an authentic trade print.
            bucket_ts = _bucket_start_utc(trade.ts, interval_seconds=interval_seconds)
            # Only append when the trade lands in the immediate next bucket (or later
            # empty buckets advanced one-at-a-time from the tip).
            expected_next = tip_end
            if bucket_ts != expected_next:
                # Non-adjacent: ignore until candle history realigns (fail-soft).
                meta["old_trade_count"] += 1
                continue
            sealed = tip
            if not sealed.confirm:
                sealed = OhlcvBarV1(
                    ts=sealed.ts,
                    open=sealed.open,
                    high=sealed.high,
                    low=sealed.low,
                    close=sealed.close,
                    volume=sealed.volume,
                    volume_ccy=sealed.volume_ccy,
                    confirm=True,
                    provider_ts_ms=sealed.provider_ts_ms,
                )
            new_tip = OhlcvBarV1(
                ts=bucket_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                open=format(px, "f"),
                high=format(px, "f"),
                low=format(px, "f"),
                close=format(px, "f"),
                volume=format(sz, "f"),
                volume_ccy=None,
                confirm=False,
                provider_ts_ms=trade.provider_ts_ms,
            )
            working = list(working[:-1]) + [sealed, new_tip]
            applied.add(trade.trade_id)
            meta["new_trade_count"] += 1
            revision_kind = "NEW_INTERVAL_APPEND"
            continue

        # Same open-candle bucket revision.
        if tip.confirm:
            # Sealed tip must not be rewritten by late prints.
            meta["old_trade_count"] += 1
            continue
        new_high = max(_dec(tip.high, field="high"), px)
        new_low = min(_dec(tip.low, field="low"), px)
        new_vol = _dec(tip.volume, field="volume") + sz
        new_tip = OhlcvBarV1(
            ts=tip.ts,
            open=tip.open,
            high=format(new_high, "f"),
            low=format(new_low, "f"),
            close=format(px, "f"),
            volume=format(new_vol, "f"),
            volume_ccy=tip.volume_ccy,
            confirm=False,
            provider_ts_ms=trade.provider_ts_ms or tip.provider_ts_ms,
        )
        working = list(working[:-1]) + [new_tip]
        applied.add(trade.trade_id)
        meta["new_trade_count"] += 1
        if revision_kind != "NEW_INTERVAL_APPEND":
            revision_kind = "SAME_TIMESTAMP_REVISION"

    return working, revision_kind, sorted(applied)[-MAX_APPLIED_TRADE_IDS:], meta


def parse_okx_history_candles(
    rows: Sequence[Sequence[Any]],
) -> tuple[list[OhlcvBarV1], list[str]]:
    """Parse OKX candle rows: [ts,o,h,l,c,vol,volCcy,volCcyQuote,confirm]."""
    bars: list[OhlcvBarV1] = []
    reasons: list[str] = []
    seen_ts: set[str] = set()
    for raw in rows:
        if not isinstance(raw, (list, tuple)) or len(raw) < 6:
            reasons.append("MALFORMED_CANDLE_ROW")
            continue
        ts_iso = provider_ms_to_utc_iso(raw[0])
        if ts_iso is None:
            reasons.append("INVALID_CANDLE_TS")
            continue
        if ts_iso in seen_ts:
            raise OkxOhlcvReadmodelError(f"DUPLICATE_CANDLE_TIMESTAMP:{ts_iso}")
        seen_ts.add(ts_iso)
        o = _dec(raw[1], field="open")
        h = _dec(raw[2], field="high")
        l = _dec(raw[3], field="low")
        c = _dec(raw[4], field="close")
        vol = _dec(raw[5], field="volume")
        vol_ccy = None
        if len(raw) > 6 and raw[6] not in (None, ""):
            vol_ccy = format(_dec(raw[6], field="volume_ccy"), "f")
        confirm = True
        if len(raw) > 8:
            confirm = str(raw[8]) in {"1", "true", "True"}
        if h < max(o, c, l) or l > min(o, c, h):
            raise OkxOhlcvReadmodelError(f"INVALID_OHLC_RELATION:{ts_iso}")
        if vol < 0:
            raise OkxOhlcvReadmodelError(f"NEGATIVE_VOLUME:{ts_iso}")
        bars.append(
            OhlcvBarV1(
                ts=ts_iso,
                open=format(o, "f"),
                high=format(h, "f"),
                low=format(l, "f"),
                close=format(c, "f"),
                volume=format(vol, "f"),
                volume_ccy=vol_ccy,
                confirm=confirm,
                provider_ts_ms=str(raw[0]),
            )
        )
    bars.sort(key=lambda b: b.ts)
    # Gap detection for PT1H closed bars only.
    gap_count = 0
    closed = [b for b in bars if b.confirm]
    for prev, cur in zip(closed, closed[1:]):
        prev_dt = datetime.fromisoformat(prev.ts.replace("Z", "+00:00"))
        cur_dt = datetime.fromisoformat(cur.ts.replace("Z", "+00:00"))
        delta_h = (cur_dt - prev_dt).total_seconds() / 3600.0
        if abs(delta_h - 1.0) > 1e-9:
            gap_count += int(max(0, round(delta_h - 1.0)))
    return bars, [f"GAP_COUNT:{gap_count}", *reasons]


def materialize_selected_okx_ohlcv_readmodel_v1(
    *,
    archive_root: Path,
    selected_instrument: str,
    selected_provider_instrument_id: str,
    selected_venue: str,
    selection_bundle_id: str,
    selection_path: Path,
    bar: str = DEFAULT_BAR,
    limit: int = DEFAULT_LIMIT,
    client: OkxPublicMarketDataClientV1 | None = None,
) -> dict[str, Any]:
    if selected_venue.lower() not in {"okx", "okx_europe_eea"}:
        raise OkxOhlcvReadmodelError("SELECTED_VENUE_NOT_OKX")
    if not selected_instrument or not selected_provider_instrument_id:
        raise OkxOhlcvReadmodelError("SELECTED_INSTRUMENT_EMPTY")
    if selected_instrument != selected_provider_instrument_id:
        # For OKX SWAP, canonical display symbol equals provider instId in this path.
        if selected_instrument.upper() != selected_provider_instrument_id.upper():
            raise OkxOhlcvReadmodelError("SELECTION_IDENTITY_MISMATCH")
    if "BTC" in selected_instrument.upper().split("-"):
        raise OkxOhlcvReadmodelError("BTC_EXCLUDED")
    if bar.upper() not in {"1H", "PT1H"}:
        raise OkxOhlcvReadmodelError("UNSUPPORTED_BAR_INTERVAL")
    okx_bar = "1H"

    http = client or OkxPublicMarketDataClientV1()
    envelope = http.get_json(
        OKX_CANDLES_PATH,
        {
            "instId": selected_provider_instrument_id,
            "bar": okx_bar,
            "limit": str(limit),
        },
    )
    payload = json.loads(envelope.raw_body_utf8)
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise OkxOhlcvReadmodelError("OHLCV_EMPTY")
    incoming_bars, notes = parse_okx_history_candles(data)
    if not incoming_bars:
        raise OkxOhlcvReadmodelError("OHLCV_PARSE_EMPTY")

    existing_doc = load_ohlcv_readmodel_v1(archive_root)
    previous_bars: list[Any] | None = None
    if (
        isinstance(existing_doc, Mapping)
        and str(existing_doc.get("instrument_id") or "") == selected_instrument
        and str(existing_doc.get("venue") or "").lower() in {"okx", "okx_europe_eea"}
        and isinstance(existing_doc.get("bars"), list)
    ):
        previous_bars = list(existing_doc["bars"])
    bars, candle_revision_kind = reduce_okx_ohlcv_bars_v1(previous_bars, incoming_bars)

    # Public trades revise the open candle when the candles endpoint is static.
    trades_envelope = http.get_json(
        OKX_TRADES_PATH,
        {
            "instId": selected_provider_instrument_id,
            "limit": str(DEFAULT_TRADES_LIMIT),
        },
    )
    trades_payload = json.loads(trades_envelope.raw_body_utf8)
    trades_data = trades_payload.get("data")
    if not isinstance(trades_data, list):
        raise OkxOhlcvReadmodelError("TRADES_PAYLOAD_INVALID")
    trades = parse_okx_public_trades_v1(trades_data)
    prev_applied: list[str] | None = None
    if (
        isinstance(existing_doc, Mapping)
        and previous_bars
        and bars
        and _as_ohlcv_bar(previous_bars[-1]).ts == bars[-1].ts
        and "applied_trade_ids" in existing_doc
    ):
        raw_ids = existing_doc.get("applied_trade_ids")
        if isinstance(raw_ids, list):
            prev_applied = [str(x) for x in raw_ids]
        else:
            prev_applied = []
    bars, trade_revision_kind, applied_trade_ids, trade_meta = (
        apply_okx_public_trades_to_open_candle_v1(
            bars,
            trades,
            previously_applied_trade_ids=prev_applied,
        )
    )
    # Stale trade capture must not overwrite a fresher on-disk open tip.
    stale_overwrite_rejected = False
    if isinstance(existing_doc, Mapping) and previous_bars:
        prior_trades_cap = _parse_aware_utc(existing_doc.get("trades_captured_at"))
        new_trades_cap = _parse_aware_utc(trades_envelope.captured_at)
        if (
            prior_trades_cap is not None
            and new_trades_cap is not None
            and new_trades_cap < prior_trades_cap
            and _as_ohlcv_bar(previous_bars[-1]).ts == bars[-1].ts
        ):
            bars = [_as_ohlcv_bar(b) for b in previous_bars]
            trade_revision_kind = "STALE_SOURCE_REJECTED"
            applied_trade_ids = [
                str(x) for x in (existing_doc.get("applied_trade_ids") or []) if str(x)
            ][-MAX_APPLIED_TRADE_IDS:]
            trade_meta = {
                **trade_meta,
                "stale_source_rejected": True,
                "prior_trades_captured_at": existing_doc.get("trades_captured_at"),
                "new_trades_captured_at": trades_envelope.captured_at,
            }
            stale_overwrite_rejected = True

    bars, cumulative_meta = merge_open_tip_cumulative_interval_volume_v1(previous_bars, bars)
    if trade_revision_kind in {"SAME_TIMESTAMP_REVISION", "NEW_INTERVAL_APPEND"}:
        revision_kind = trade_revision_kind
    elif stale_overwrite_rejected:
        revision_kind = "STALE_SOURCE_REJECTED"
    elif cumulative_meta.get("open_tip_volume_preserved"):
        revision_kind = "SAME_TIMESTAMP_REVISION"
    else:
        revision_kind = candle_revision_kind

    closed = [b for b in bars if b.confirm]
    last_closed = closed[-1] if closed else None
    as_of = utc_now_iso()
    policy = load_freshness_policy_v1()
    # Live open-candle freshness keys off the public trades capture clock (the
    # authentic revision source). Mark-only ticks never drive OHLCV freshness.
    candle_captured_at = trades_envelope.captured_at
    candle_effective_at = trades_envelope.effective_at or trades_envelope.captured_at
    freshness_state, is_stale, stale_reason = classify_freshness_v1(
        reference_at=candle_captured_at,
        as_of=as_of,
        source_type="ohlcv_latest_candle",
        policy=policy,
    )
    gap_count = 0
    for note in notes:
        if note.startswith("GAP_COUNT:"):
            gap_count = int(note.split(":", 1)[1])

    live_mark_price: str | None = None
    live_mark_provider_ts: str | None = None
    live_mark_request_url: str | None = None
    live_mark_raw_digest: str | None = None
    mark_envelope = http.get_json(
        OKX_MARK_PRICE_PATH,
        {
            "instType": "SWAP",
            "instId": selected_provider_instrument_id,
        },
    )
    mark_payload = json.loads(mark_envelope.raw_body_utf8)
    mark_rows = mark_payload.get("data")
    if not isinstance(mark_rows, list) or not mark_rows:
        raise OkxOhlcvReadmodelError("MARK_PRICE_EMPTY")
    mark_row = mark_rows[0]
    if not isinstance(mark_row, Mapping):
        raise OkxOhlcvReadmodelError("MARK_PRICE_ROW_INVALID")
    mark_inst = str(mark_row.get("instId") or "").strip()
    if mark_inst and mark_inst.upper() != selected_provider_instrument_id.upper():
        raise OkxOhlcvReadmodelError("MARK_PRICE_INSTRUMENT_MISMATCH")
    live_mark_price = format(_dec(mark_row.get("markPx"), field="markPx"), "f")
    live_mark_provider_ts = provider_ms_to_utc_iso(mark_row.get("ts"))
    live_mark_request_url = mark_envelope.request_url
    live_mark_raw_digest = mark_envelope.raw_payload_digest

    raw_path = (
        archive_root / "raw" / "okx_ohlcv" / f"{selected_provider_instrument_id}_{okx_bar}.json"
    )
    _atomic_write_text(raw_path, envelope.raw_body_utf8)
    trades_raw_path = (
        archive_root / "raw" / "okx_trades" / f"{selected_provider_instrument_id}.json"
    )
    _atomic_write_text(trades_raw_path, trades_envelope.raw_body_utf8)
    mark_raw_path = (
        archive_root / "raw" / "okx_mark_price" / f"{selected_provider_instrument_id}.json"
    )
    _atomic_write_text(mark_raw_path, mark_envelope.raw_body_utf8)

    # Primary live OHLCV clocks follow the public trades capture (open-candle source).
    captured_at = candle_captured_at
    effective_at = candle_effective_at

    doc = {
        "schema_name": OHLCV_SCHEMA,
        "schema_version": 1,
        "non_authorizing": True,
        "fixture_only": False,
        "venue": "okx",
        "market_type": "perpetual",
        "interval": "PT1H",
        "provider_bar": okx_bar,
        "candle_endpoint": OKX_CANDLES_PATH,
        "trades_endpoint": OKX_TRADES_PATH,
        "open_candle_live_source": OPEN_CANDLE_LIVE_SOURCE_V1,
        "open_candle_bootstrap_source": OKX_CANDLES_PATH,
        "instrument_id": selected_instrument,
        "provider_instrument_id": selected_provider_instrument_id,
        "selection_bundle_id": selection_bundle_id,
        "selection_path": str(selection_path.resolve()),
        "captured_at": captured_at,
        "effective_at": effective_at,
        "candle_captured_at": candle_captured_at,
        "candle_effective_at": candle_effective_at,
        "candles_captured_at": envelope.captured_at,
        "trades_captured_at": trades_envelope.captured_at,
        "ohlcv_revision_kind": revision_kind,
        "candle_revision_kind": candle_revision_kind,
        "trade_revision_kind": trade_revision_kind,
        "freshness_state": freshness_state,
        "is_stale": is_stale,
        "stale_reason": stale_reason,
        "gap_count": gap_count,
        "bar_count": len(bars),
        "closed_bar_count": len(closed),
        "first_timestamp": bars[0].ts,
        "last_timestamp": bars[-1].ts,
        "last_closed_timestamp": last_closed.ts if last_closed else None,
        "raw_capture_digest": envelope.raw_payload_digest,
        "raw_capture_path": str(raw_path.resolve()),
        "request_url": envelope.request_url,
        "trades_raw_capture_digest": trades_envelope.raw_payload_digest,
        "trades_raw_capture_path": str(trades_raw_path.resolve()),
        "trades_request_url": trades_envelope.request_url,
        "applied_trade_ids": applied_trade_ids,
        "trade_reduce_meta": trade_meta,
        "volume_semantic_model": "MODEL_A_CUMULATIVE_INTERVAL_VOLUME",
        "open_tip_cumulative_meta": cumulative_meta,
        "stale_overwrite_rejected": stale_overwrite_rejected,
        "volume_unit": TRADE_VOLUME_UNIT,
        "trade_volume_unit": TRADE_VOLUME_UNIT,
        "bars": [b.to_json_dict() for b in bars],
        "notes": [
            *notes,
            f"REVISION_KIND:{revision_kind}",
            f"CANDLE_REVISION_KIND:{candle_revision_kind}",
            f"TRADE_REVISION_KIND:{trade_revision_kind}",
            f"OPEN_CANDLE_LIVE_SOURCE:{OPEN_CANDLE_LIVE_SOURCE_V1}",
            "VOLUME_SEMANTIC_MODEL:MODEL_A_CUMULATIVE_INTERVAL_VOLUME",
            f"OPEN_TIP_VOLUME_PRESERVED:{bool(cumulative_meta.get('open_tip_volume_preserved'))}",
            f"STALE_OVERWRITE_REJECTED:{stale_overwrite_rejected}",
        ],
        # Additive live-mark projection (v1): authentic OKX public mark only.
        # Distinct fact from candle close — never rewrites OHLCV geometry.
        "live_mark_projection": LIVE_MARK_PROJECTION_V1,
        "live_mark_price": live_mark_price,
        "live_mark_provider_ts": live_mark_provider_ts,
        "live_mark_captured_at": mark_envelope.captured_at,
        "live_mark_request_url": live_mark_request_url,
        "live_mark_raw_digest": live_mark_raw_digest,
        "live_mark_raw_path": str(mark_raw_path.resolve()),
        "live_price_kind": "mark",
    }
    out_path = archive_root / OHLCV_RELATIVE_PATH
    _atomic_write_text(out_path, json.dumps(doc, indent=2) + "\n")
    # OHLCV lives under readmodels/; rewrite MANIFEST.sha256 so continuous
    # refresh does not fail-closed the universe_selection binding.
    readmodels_dir = out_path.parent
    if (readmodels_dir / "MANIFEST.sha256").is_file() or (
        readmodels_dir / "universe_selection_readmodel.v1.json"
    ).is_file():
        from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

        write_manifest_sha256(readmodels_dir)
    return {
        "ohlcv_path": str(out_path),
        "raw_ohlcv_path": str(raw_path),
        "bar_count": len(bars),
        "gap_count": gap_count,
        "freshness_state": freshness_state,
        "last_closed_timestamp": last_closed.ts if last_closed else None,
        "first_timestamp": bars[0].ts,
        "ohlcv_revision_kind": revision_kind,
        "digest": hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest(),
    }


def load_ohlcv_readmodel_v1(archive_root: Path) -> Mapping[str, Any] | None:
    path = archive_root / OHLCV_RELATIVE_PATH
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise OkxOhlcvReadmodelError("OHLCV_READMODEL_NOT_OBJECT")
    if data.get("schema_name") != OHLCV_SCHEMA:
        raise OkxOhlcvReadmodelError("OHLCV_SCHEMA_MISMATCH")
    return data


def _parse_aware_utc(raw: Any) -> datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        parsed = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def resolve_selected_instrument_for_ohlcv_refresh_v1(
    archive_root: Path,
) -> dict[str, Any]:
    """Resolve canonical selected OKX instrument from universe_selection_readmodel.v1."""
    selection_path = archive_root / UNIVERSE_SELECTION_RELATIVE_PATH
    if not selection_path.is_file():
        raise OkxOhlcvReadmodelError("MISSING_SOURCE:UNIVERSE_SELECTION")
    payload = json.loads(selection_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise OkxOhlcvReadmodelError("INVALID:UNIVERSE_SELECTION_NOT_OBJECT")
    selected = payload.get("selected_future")
    if not isinstance(selected, dict):
        raise OkxOhlcvReadmodelError("MISSING_SOURCE:SELECTED_INSTRUMENT")
    symbol = str(selected.get("symbol") or "").strip()
    if not symbol:
        raise OkxOhlcvReadmodelError("MISSING_SOURCE:SELECTED_INSTRUMENT")
    if "BTC" in symbol.upper().split("-"):
        raise OkxOhlcvReadmodelError("INVALID:BTC_EXCLUDED")
    venue = "okx"
    for row in payload.get("universe") or []:
        if isinstance(row, dict) and str(row.get("symbol") or "") == symbol and row.get("exchange"):
            venue = str(row["exchange"]).strip().lower() or "okx"
            break
    if venue not in {"okx", "okx_europe_eea"}:
        raise OkxOhlcvReadmodelError("INVALID:SELECTED_VENUE_NOT_OKX")
    bundle_id = str(
        payload.get("source_run_id")
        or (payload.get("evidence") or {}).get("source_run_id")
        or "universe_selection_readmodel.v1"
    )
    return {
        "selected_instrument": symbol,
        "selected_provider_instrument_id": symbol,
        "selected_venue": venue,
        "selection_bundle_id": bundle_id,
        "selection_path": selection_path,
    }


def refresh_selected_okx_ohlcv_readmodel_from_archive_v1(
    *,
    archive_root: Path,
    client: OkxPublicMarketDataClientV1 | None = None,
    bar: str = DEFAULT_BAR,
    min_interval_seconds: int = DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS,
    force: bool = False,
) -> dict[str, Any]:
    """Rate-limited public OHLCV rematerialization for the canonically selected instrument.

    Fail-closed: provider/network errors do not invent candles or rewrite the
    readmodel with fabricated bars. Concurrent refreshes are exclusive via flock.
    """
    root = archive_root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / REFRESH_LOCK_NAME
    lock_fh = lock_path.open("w", encoding="utf-8")
    try:
        try:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise OkxOhlcvReadmodelError("REFRESH_IN_PROGRESS") from exc

        selection = resolve_selected_instrument_for_ohlcv_refresh_v1(root)
        existing = load_ohlcv_readmodel_v1(root)
        if existing is not None:
            if str(existing.get("instrument_id") or "") != selection["selected_instrument"]:
                raise OkxOhlcvReadmodelError("INVALID:INSTRUMENT_MISMATCH")
            if str(existing.get("venue") or "").lower() not in {"okx", "okx_europe_eea"}:
                raise OkxOhlcvReadmodelError("INVALID:OHLCV_VENUE_NOT_OKX")
            captured_at = _parse_aware_utc(existing.get("captured_at"))
            if not force and captured_at is not None and min_interval_seconds > 0:
                age = (datetime.now(timezone.utc) - captured_at).total_seconds()
                if age < float(min_interval_seconds):
                    return {
                        "status": "SKIPPED_RECENT",
                        "refresh_attempted": False,
                        "selected_instrument": selection["selected_instrument"],
                        "selected_venue": selection["selected_venue"],
                        "captured_at": existing.get("captured_at"),
                        "last_timestamp": existing.get("last_timestamp"),
                        "digest": hashlib.sha256(
                            json.dumps(existing, sort_keys=True).encode()
                        ).hexdigest(),
                        "ohlcv": dict(existing),
                    }

        try:
            materialize = materialize_selected_okx_ohlcv_readmodel_v1(
                archive_root=root,
                selected_instrument=selection["selected_instrument"],
                selected_provider_instrument_id=selection["selected_provider_instrument_id"],
                selected_venue=selection["selected_venue"],
                selection_bundle_id=selection["selection_bundle_id"],
                selection_path=selection["selection_path"],
                bar=bar,
                client=client,
            )
        except Exception as exc:  # noqa: BLE001 — surface provider failures fail-closed
            retained = load_ohlcv_readmodel_v1(root)
            return {
                "status": "REFRESH_FAILED",
                "refresh_attempted": True,
                "refresh_error": f"{type(exc).__name__}:{exc}",
                "selected_instrument": selection["selected_instrument"],
                "selected_venue": selection["selected_venue"],
                "captured_at": None if retained is None else retained.get("captured_at"),
                "last_timestamp": None if retained is None else retained.get("last_timestamp"),
                "digest": None
                if retained is None
                else hashlib.sha256(json.dumps(retained, sort_keys=True).encode()).hexdigest(),
                "ohlcv": None if retained is None else dict(retained),
                "fabricated": False,
            }

        refreshed = load_ohlcv_readmodel_v1(root)
        return {
            "status": "OK",
            "refresh_attempted": True,
            "selected_instrument": selection["selected_instrument"],
            "selected_venue": selection["selected_venue"],
            "captured_at": None if refreshed is None else refreshed.get("captured_at"),
            "last_timestamp": None if refreshed is None else refreshed.get("last_timestamp"),
            "digest": materialize.get("digest"),
            "ohlcv": None if refreshed is None else dict(refreshed),
            "materialize": materialize,
        }
    finally:
        try:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
        except Exception:  # noqa: BLE001
            pass
        lock_fh.close()
