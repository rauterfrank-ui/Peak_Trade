"""Selected-instrument OKX OHLCV readmodel materializer (public candles only)."""

from __future__ import annotations

import fcntl
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
UNIVERSE_SELECTION_RELATIVE_PATH = "readmodels/universe_selection_readmodel.v1.json"
REFRESH_LOCK_NAME = ".okx_selected_instrument_ohlcv_refresh.lock"
DEFAULT_BAR = "1H"
DEFAULT_LIMIT = 100
# Recent candles endpoint includes the incomplete open candle (confirm=0).
OKX_CANDLES_PATH = "/api/v5/market/candles"
OKX_MARK_PRICE_PATH = "/api/v5/public/mark-price"
LIVE_MARK_PROJECTION_V1 = "okx_ohlcv_live_mark_v1"
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
    mark_raw_path = (
        archive_root / "raw" / "okx_mark_price" / f"{selected_provider_instrument_id}.json"
    )
    _atomic_write_text(mark_raw_path, mark_envelope.raw_body_utf8)

    # Capture clocks: prefer the later of candles vs mark responses for honest freshness.
    captured_at = envelope.captured_at
    effective_at = envelope.effective_at or envelope.captured_at
    try:
        candle_cap = datetime.fromisoformat(str(envelope.captured_at).replace("Z", "+00:00"))
        mark_cap = datetime.fromisoformat(str(mark_envelope.captured_at).replace("Z", "+00:00"))
        if mark_cap > candle_cap:
            captured_at = mark_envelope.captured_at
            effective_at = mark_envelope.effective_at or mark_envelope.captured_at
    except ValueError:
        pass

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
        "instrument_id": selected_instrument,
        "provider_instrument_id": selected_provider_instrument_id,
        "selection_bundle_id": selection_bundle_id,
        "selection_path": str(selection_path.resolve()),
        "captured_at": captured_at,
        "effective_at": effective_at,
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
        # Additive live-mark projection (v1): authentic OKX public mark only.
        # Does not rewrite closed candle OHLC; browser may use mark for open-bar tip.
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
