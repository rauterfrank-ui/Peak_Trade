"""Selected-instrument OKX OHLCV readmodel materializer (public candles only)."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
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
DEFAULT_BAR = "1H"
DEFAULT_LIMIT = 100


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
        "/api/v5/market/history-candles",
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
    bars, notes = parse_okx_history_candles(data)
    if not bars:
        raise OkxOhlcvReadmodelError("OHLCV_PARSE_EMPTY")

    closed = [b for b in bars if b.confirm]
    last_closed = closed[-1] if closed else None
    as_of = utc_now_iso()
    policy = load_freshness_policy_v1()
    freshness_state, is_stale, stale_reason = classify_freshness_v1(
        reference_at=(last_closed.ts if last_closed else envelope.captured_at),
        as_of=as_of,
        source_type="ohlcv_latest_candle",
        policy=policy,
    )
    gap_count = 0
    for note in notes:
        if note.startswith("GAP_COUNT:"):
            gap_count = int(note.split(":", 1)[1])

    raw_path = archive_root / "raw" / "okx_ohlcv" / f"{selected_provider_instrument_id}_{okx_bar}.json"
    _atomic_write_text(raw_path, envelope.raw_body_utf8)

    doc = {
        "schema_name": OHLCV_SCHEMA,
        "schema_version": 1,
        "non_authorizing": True,
        "fixture_only": False,
        "venue": "okx",
        "market_type": "perpetual",
        "interval": "PT1H",
        "provider_bar": okx_bar,
        "instrument_id": selected_instrument,
        "provider_instrument_id": selected_provider_instrument_id,
        "selection_bundle_id": selection_bundle_id,
        "selection_path": str(selection_path.resolve()),
        "captured_at": envelope.captured_at,
        "effective_at": envelope.effective_at or envelope.captured_at,
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
        "volume_unit": "contracts",
        "bars": [b.to_json_dict() for b in bars],
        "notes": notes,
    }
    out_path = archive_root / OHLCV_RELATIVE_PATH
    _atomic_write_text(out_path, json.dumps(doc, indent=2) + "\n")
    return {
        "ohlcv_path": str(out_path),
        "raw_ohlcv_path": str(raw_path),
        "bar_count": len(bars),
        "gap_count": gap_count,
        "freshness_state": freshness_state,
        "last_closed_timestamp": last_closed.ts if last_closed else None,
        "first_timestamp": bars[0].ts,
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
