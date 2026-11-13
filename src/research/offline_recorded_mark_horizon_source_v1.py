"""Bounded offline source adapter, not a productive O4 producer or horizon policy.

An explicit request selects N hourly aggregates from original finalized minute
mark candles. N has no default. This adapter does not select a learning target.
Archive hashes bind local evidence, not independent exchange attestation.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.economic_md_input_producer_v1.constants_v1 import PUBLIC_HTTP_HOST
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.error_classes_v1 import (
    MarketDataBindingErrorV1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.venue_instrument_mapping_v1 import (
    resolve_okx_venue_instrument_mapping_v1,
)
from src.research.offline_n_bars_semantic_repair_v1 import RECORDED, canonical, digest_bytes

ENDPOINT = "/api/v5/market/history-mark-price-candles"
LEGACY_NATIVE_INSTRUMENT = "ETH-USDT-SWAP"


def utc_seconds(value: str) -> float:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset().total_seconds() != 0:
        raise ValueError("EXPLICIT_UTC_REQUIRED")
    return dt.timestamp()


def utc_text(value: float) -> str:
    return datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")


def read_bound_json(path: Path, expected_sha256: str) -> Any:
    raw = path.read_bytes()
    if digest_bytes(raw) != expected_sha256:
        raise ValueError("SOURCE_SHA256_MISMATCH")
    return json.loads(raw)


def recorded_mark_price_unit_v1(
    *,
    instrument_binding: Mapping[str, Any],
    canonical_instrument_id: str,
    native_instrument_id: str,
) -> str:
    """Validate the exact archived market before capture or offline replay."""
    binding = instrument_binding
    metadata = binding.get("instrument_metadata")
    mismatch = "PILOT_INSTRUMENT_BINDING_MISMATCH"
    if (
        not isinstance(canonical_instrument_id, str)
        or not canonical_instrument_id
        or binding.get("canonical_instrument_id") != canonical_instrument_id
        or binding.get("native_instrument_id") != native_instrument_id
        or binding.get("venue") != "OKX"
        or not isinstance(metadata, Mapping)
        or metadata.get("instId") != native_instrument_id
    ):
        raise ValueError(mismatch)
    if native_instrument_id == LEGACY_NATIVE_INSTRUMENT:
        if (
            metadata.get("instType") != "SWAP"
            or metadata.get("settleCcy") != "USDT"
            or metadata.get("uly") != "ETH-USDT"
        ):
            raise ValueError(mismatch)
        return "USDT per ETH"
    if (
        canonical_instrument_id != native_instrument_id
        or metadata.get("instType") != "FUTURES"
        or metadata.get("ctType") != "linear"
        or metadata.get("settleCcy") != "USD"
        or metadata.get("uly") != "ETH-USD"
    ):
        raise ValueError(mismatch)
    try:
        mapping = resolve_okx_venue_instrument_mapping_v1(
            canonical_instrument_id=canonical_instrument_id,
            instruments_inventory=[metadata],
        )
    except MarketDataBindingErrorV1 as exc:
        raise ValueError(mismatch) from exc
    if (
        mapping.venue_instrument_id != native_instrument_id
        or mapping.instrument_type != metadata["instType"]
        or mapping.contract_family != "xperp"
        or mapping.settlement_currency != metadata["settleCcy"]
        or mapping.mapping_digest != binding.get("mapping_digest")
    ):
        raise ValueError(mismatch)
    return "USD per ETH"


def aggregate_recorded_mark_minutes(
    *,
    pages: Sequence[Mapping[str, Any]],
    instrument_binding: Mapping[str, Any],
    canonical_instrument_id: str,
    native_instrument_id: str,
    horizon_start_utc: str,
    n_bars: int,
    repository_sha: str,
) -> dict[str, Any]:
    """Require every original finalized minute before constructing hourly bars.

    Each page contains the raw payload, its exact bytes' SHA256 and matching
    archived request record. Files must be hash-checked by load_archive_source.
    Source timestamps are minute opens. They are never renamed as tick times.
    available_at is the archived response receipt, never a guessed live arrival.
    """
    if isinstance(n_bars, bool) or not isinstance(n_bars, int) or not 1 <= n_bars <= 24:
        raise ValueError("EXPLICIT_BOUNDED_BAR_COUNT_REQUIRED")
    start = utc_seconds(horizon_start_utc)
    if start % 3600:
        raise ValueError("EXPLICIT_HOURLY_GRID_REQUIRED")
    price_unit = recorded_mark_price_unit_v1(
        instrument_binding=instrument_binding,
        canonical_instrument_id=canonical_instrument_id,
        native_instrument_id=native_instrument_id,
    )
    end = start + n_bars * 3600
    selected: dict[int, dict[str, Any]] = {}
    page_proofs = []
    for page in pages:
        record, payload = page["request_record"], page["payload"]
        query = record.get("query_params") or {}
        if record.get("raw_response_sha256") != page["raw_sha256"]:
            raise ValueError("RAW_REQUEST_HASH_MISMATCH")
        if (
            record.get("endpoint") != ENDPOINT
            or query.get("instId") != native_instrument_id
            or query.get("bar") != "1m"
            or record.get("http_status") != 200
            or record.get("okx_code") != "0"
            or payload.get("code") != "0"
            or (
                native_instrument_id != LEGACY_NATIVE_INSTRUMENT
                and record.get("request_host") != PUBLIC_HTTP_HOST
            )
        ):
            raise ValueError("ORIGINAL_REQUEST_CONTRACT_MISMATCH")
        received = utc_seconds(record["response_time_utc"])
        if utc_seconds(record["request_time_utc"]) > received:
            raise ValueError("RESPONSE_PRECEDES_REQUEST")
        page_proofs.append(dict(record))
        for index, row in enumerate(payload["data"]):
            if not isinstance(row, list) or len(row) != 6:
                raise ValueError("ORIGINAL_MARK_CANDLE_SHAPE_REQUIRED")
            opened_ms = int(row[0])
            if opened_ms % 60000:
                raise ValueError("ORIGINAL_MINUTE_GRID_REQUIRED")
            opened = opened_ms // 1000
            if not start <= opened < end:
                continue
            if row[5] != "1":
                raise ValueError("UNFINALIZED_SOURCE_MINUTE")
            prices = [float(x) for x in row[1:5]]
            o, h, low, close = prices
            if (
                not all(math.isfinite(p) and p > 0 for p in prices)
                or not low <= min(o, close) <= max(o, close) <= h
            ):
                raise ValueError("INVALID_ORIGINAL_PRICE")
            if received < opened + 60:
                raise ValueError("SOURCE_RECEIVED_BEFORE_MINUTE_CLOSE")
            if opened in selected:
                raise ValueError("DUPLICATE_OR_CONFLICTING_SOURCE_MINUTE")
            selected[opened] = {
                "original_row": row,
                "original_index": index,
                "raw_sha256": page["raw_sha256"],
                "received": received,
            }
    expected = [int(start) + i * 60 for i in range(n_bars * 60)]
    if set(selected) != set(expected):
        raise ValueError("INCOMPLETE_ORIGINAL_MINUTE_COVERAGE")
    contract = {
        "source_kind": RECORDED,
        "clock_domain": "CAPTURE_UTC",
        "source_epoch": "archived-okx-mark-minute-replay-v1",
        "canonical_instrument_id": canonical_instrument_id,
        "venue_instrument_id": native_instrument_id,
        "venue": "OKX",
        "price_unit": price_unit,
        "price_basis": "EXPLICIT_BAR_CLOSE",
        "price_family": "MARK_PRICE",
        "input_interval": "PT1M",
        "aggregation": "60 gapless finalized original minute candles per PT1H",
        "horizon_policy": "EXPLICIT_OFFLINE_REQUEST_ONLY_NOT_SYSTEM_DEFAULT",
        "request_records": page_proofs,
        "original_minute_rows": [selected[t] for t in expected],
        "source_time_semantics": "Original timestamp is minute open; no last tick time attested.",
        "independent_exchange_attestation": False,
    }
    config_digest = digest_bytes(canonical(contract))
    receipts = []
    for i in range(n_bars):
        opened = int(start) + i * 3600
        minute_rows = [selected[opened + j * 60] for j in range(60)]
        last = minute_rows[-1]
        close = float(last["original_row"][4])
        available = max(r["received"] for r in minute_rows)
        receipts.append(
            {
                "source_kind": RECORDED,
                "available_at_utc": utc_text(available),
                "bar": {
                    "canonical_instrument_id": canonical_instrument_id,
                    "venue_instrument_id": native_instrument_id,
                    "venue": "OKX",
                    "interval": "PT1H",
                    "bar_open_time": float(opened),
                    "bar_close_time": float(opened + 3600),
                    "finalization_state": "FINALIZED_BAR",
                    "quality_state": "FINALIZED_BAR",
                    "close": close,
                    "revision": 0,
                    "session_id": "offline-archived-mark-aggregation-v1",
                    "repository_sha": repository_sha,
                    "config_digest": config_digest,
                    "last_observation_identity": {
                        "canonical_instrument_id": canonical_instrument_id,
                        "venue_instrument_id": native_instrument_id,
                        "venue": "OKX",
                        "venue_event_time": float(opened + 3540),
                        "mark_price": close,
                    },
                },
            }
        )
    return {**contract, "bar_receipts": receipts}


def load_archive_source(
    *,
    raw_path: Path,
    raw_sha256: str,
    request_log_path: Path,
    request_log_sha256: str,
    binding_path: Path,
    binding_sha256: str,
    canonical_instrument_id: str,
    native_instrument_id: str,
    horizon_start_utc: str,
    n_bars: int,
    repository_sha: str,
) -> dict[str, Any]:
    """Read-only, exact named files only. No network/import of ingestion runner."""
    payload = read_bound_json(raw_path, raw_sha256)
    log = read_bound_json(request_log_path, request_log_sha256)
    binding = read_bound_json(binding_path, binding_sha256)
    matching = [r for r in log if r.get("raw_response_sha256") == raw_sha256]
    if len(matching) != 1:
        raise ValueError("EXACT_UNIQUE_ARCHIVED_REQUEST_REQUIRED")
    result = aggregate_recorded_mark_minutes(
        pages=[{"payload": payload, "raw_sha256": raw_sha256, "request_record": matching[0]}],
        instrument_binding=binding,
        canonical_instrument_id=canonical_instrument_id,
        native_instrument_id=native_instrument_id,
        horizon_start_utc=horizon_start_utc,
        n_bars=n_bars,
        repository_sha=repository_sha,
    )
    result["archive_file_bindings"] = {
        "raw": {"path": str(raw_path), "sha256": raw_sha256},
        "request_log": {"path": str(request_log_path), "sha256": request_log_sha256},
        "instrument_binding": {"path": str(binding_path), "sha256": binding_sha256},
    }
    return result
