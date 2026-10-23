"""Bounded public OKX GET snapshot for one instrument.

Reads candles, ticker volume, open interest, funding rate, and mark price.
Checks instrument identity, timestamps, and freshness. Does not POST, does not
use credentials, and does not fill a missing field.
RUNTIME_AUTHORIZATION_EFFECT=NONE.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlencode

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    ENDPOINT_PUBLIC_MARK_PRICE,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_golden_happy_vector_current_input_observation_adapter_v1 import (
    DEFAULT_FRESH_MARK_MAX_AGE_SECONDS,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ENDPOINT_MARKET_CANDLES,
    ENDPOINT_MARKET_TICKER,
    ENDPOINT_PUBLIC_FUNDING_RATE,
    ENDPOINT_PUBLIC_OPEN_INTEREST,
    extract_finalized_candle_closes_v1,
    extract_funding_rate_v1,
    extract_mark_and_index_from_payload_v1,
    extract_open_interest_v1,
    extract_ticker_fields_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_stored_market_evidence_bind_v1 import (
    CANDLE_BODY_NAME,
    CANDLE_PROVENANCE_NAME,
)

CANDLE_BAR_SECONDS = 60.0
PUBLIC_GET_MAX_REQUEST_COUNT = 5


class PublicMarketSnapshotError(RuntimeError):
    """Fail-closed public market snapshot violation."""


@dataclass(frozen=True)
class PublicMarketSnapshotV1:
    native_id: str
    evidence_dir: str
    observed_unix: float
    finalized_close_count: int
    last_finalized_event_ts_unix: float
    volume: float
    open_interest: float
    funding_rate: float
    mark_px: float
    index_px: float
    post_count: int
    request_count: int


def _assert_read_only_pins_v1() -> None:
    if POST_ALLOWED is True or REAL_VENUE_POST_ALLOWED is True:
        raise PublicMarketSnapshotError("POST_STANDING_MUST_REMAIN_FALSE")
    if EXTERNAL_EFFECT_AUTHORIZED is True:
        raise PublicMarketSnapshotError("EXTERNAL_EFFECT_MUST_REMAIN_FALSE")


def open_public_read_only_market_transport_v1() -> FullCoreProductiveReadOnlyGetTransportV1:
    """Public GET transport. No credential handle and no POST authority."""

    _assert_read_only_pins_v1()
    return FullCoreProductiveReadOnlyGetTransportV1(
        handle=None,
        max_request_count=PUBLIC_GET_MAX_REQUEST_COUNT,
    )


def _endpoint_v1(path: str, query: Mapping[str, str]) -> str:
    return f"{path}?{urlencode(dict(query))}"


def _rows_v1(payload: Any) -> list[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, Mapping)]


def _field_ts_unix_v1(payload: Any, *, native_id: str) -> float | None:
    wanted = str(native_id or "").strip()
    for row in _rows_v1(payload):
        inst = str(row.get("instId") or "").strip()
        if inst not in {"", wanted}:
            continue
        raw = row.get("ts")
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return None
        if value > 1_000_000_000_000:
            value = value / 1000.0
        return value
    return None


def _fresh_v1(*, observed_unix: float, event_unix: float, max_age_seconds: float) -> bool:
    age = float(observed_unix) - float(event_unix)
    return -5.0 <= age <= float(max_age_seconds)


def _require_get_v1(transport: Any, *, endpoint: str, native_id: str) -> Any:
    result = transport.get(
        endpoint=endpoint,
        auth_required=False,
        pretrade_decision_id=f"public-market-snapshot:{native_id}",
    )
    if getattr(result, "method", "GET") != "GET":
        raise PublicMarketSnapshotError("NON_GET_FORBIDDEN")
    if getattr(result, "auth_header_sent", False) is True:
        raise PublicMarketSnapshotError("PUBLIC_GET_AUTH_HEADER_FORBIDDEN")
    if (
        getattr(result, "get_performed", False) is not True
        or getattr(result, "payload", None) is None
    ):
        raise PublicMarketSnapshotError(
            "MARKET_GET_NOT_PERFORMED:" + str(getattr(result, "error_class", "") or endpoint)
        )
    return result.payload


def acquire_public_okx_market_snapshot_v1(
    *,
    transport: Any,
    native_id: str,
    evidence_dir: Path,
    observed_unix: float,
) -> PublicMarketSnapshotV1:
    """GET the five public fields and persist a binder-readable directory."""

    _assert_read_only_pins_v1()
    wanted = str(native_id or "").strip()
    if not wanted:
        raise PublicMarketSnapshotError("NATIVE_ID_REQUIRED")
    root = Path(evidence_dir)
    root.mkdir(parents=True, exist_ok=True)

    candle_endpoint = _endpoint_v1(
        ENDPOINT_MARKET_CANDLES,
        {"instId": wanted, "bar": "1m", "limit": "100"},
    )
    ticker_endpoint = _endpoint_v1(ENDPOINT_MARKET_TICKER, {"instId": wanted})
    oi_endpoint = _endpoint_v1(ENDPOINT_PUBLIC_OPEN_INTEREST, {"instId": wanted})
    funding_endpoint = _endpoint_v1(ENDPOINT_PUBLIC_FUNDING_RATE, {"instId": wanted})
    mark_endpoint = _endpoint_v1(ENDPOINT_PUBLIC_MARK_PRICE, {"instId": wanted})

    candles = _require_get_v1(transport, endpoint=candle_endpoint, native_id=wanted)
    ticker = _require_get_v1(transport, endpoint=ticker_endpoint, native_id=wanted)
    open_interest_payload = _require_get_v1(transport, endpoint=oi_endpoint, native_id=wanted)
    funding_payload = _require_get_v1(transport, endpoint=funding_endpoint, native_id=wanted)
    mark_payload = _require_get_v1(transport, endpoint=mark_endpoint, native_id=wanted)

    closes, last_ts = extract_finalized_candle_closes_v1(candles)
    bid, ask, volume, _ticker_index = extract_ticker_fields_v1(ticker, native_id=wanted)
    open_interest = extract_open_interest_v1(open_interest_payload, native_id=wanted)
    funding_rate = extract_funding_rate_v1(funding_payload, native_id=wanted)
    mark_px, index_px = extract_mark_and_index_from_payload_v1(mark_payload, native_id=wanted)

    missing: list[str] = []
    if not closes or last_ts is None:
        missing.append("finalized_closes")
    elif not _fresh_v1(
        observed_unix=observed_unix,
        event_unix=last_ts,
        max_age_seconds=CANDLE_BAR_SECONDS + DEFAULT_FRESH_MARK_MAX_AGE_SECONDS,
    ):
        missing.append("candle_freshness")
    if volume is None or bid is None or ask is None:
        missing.append("vol24h")
    if open_interest is None:
        missing.append("open_interest")
    if funding_rate is None:
        missing.append("funding_rate")
    if mark_px is None or index_px is None:
        missing.append("mark_px")
    for name, payload in (
        ("ticker_ts", ticker),
        ("open_interest_ts", open_interest_payload),
        ("funding_ts", funding_payload),
        ("mark_ts", mark_payload),
    ):
        event_unix = _field_ts_unix_v1(payload, native_id=wanted)
        if event_unix is None or not _fresh_v1(
            observed_unix=observed_unix,
            event_unix=event_unix,
            max_age_seconds=DEFAULT_FRESH_MARK_MAX_AGE_SECONDS,
        ):
            missing.append(name)
    if missing:
        raise PublicMarketSnapshotError("PUBLIC_MARKET_SNAPSHOT_INCOMPLETE:" + ",".join(missing))

    body_bytes = json.dumps(candles, separators=(",", ":"), sort_keys=True).encode("utf-8")
    body_sha = hashlib.sha256(body_bytes).hexdigest()
    (root / CANDLE_BODY_NAME).write_bytes(body_bytes)
    provenance = {
        "BODY_SHA256": body_sha,
        "C1_GATE_NATIVE_ID": wanted,
        "ENDPOINT": candle_endpoint,
        "OBSERVED_AT_UNIX": str(observed_unix),
        "POST_COUNT": "0",
        "VENUE_MUTATION_PERFORMED": "false",
        "AUTH_REQUIRED": "false",
    }
    (root / CANDLE_PROVENANCE_NAME).write_text(
        json.dumps(provenance, sort_keys=True),
        encoding="utf-8",
    )
    for name, payload in (
        ("ticker.json", ticker),
        ("oi.json", open_interest_payload),
        ("funding.json", funding_payload),
        ("mark.json", mark_payload),
    ):
        (root / name).write_text(
            json.dumps(payload, separators=(",", ":"), sort_keys=True),
            encoding="utf-8",
        )
    return PublicMarketSnapshotV1(
        native_id=wanted,
        evidence_dir=str(root),
        observed_unix=float(observed_unix),
        finalized_close_count=len(closes),
        last_finalized_event_ts_unix=float(last_ts),
        volume=float(volume),
        open_interest=float(open_interest),
        funding_rate=float(funding_rate),
        mark_px=float(mark_px),
        index_px=float(index_px),
        post_count=0,
        request_count=5,
    )
