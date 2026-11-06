"""Append-only natural market-data GET capture for CURRENT productive read-only transport.

Observation-only side effect: delegate GET semantics and results are unchanged.
Does not authorize Live POST, replay, or trading-logic mutation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlparse

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    ENDPOINT_PUBLIC_MARK_PRICE,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FreshPretradeGetTransportResultV1,
    GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
    GET_PATH,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ENDPOINT_MARKET_INDEX_TICKERS,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)

OWNER = "full_core_live_path_composition_root_v1.productive_natural_market_data_capture_sink_v1"

NATURAL_MARKET_DATA_CAPTURE_SCHEMA_VERSION = "natural_market_data_get_capture.v1"
CAPTURE_LEDGER_FILENAME = "natural_market_data_get_capture_v1.jsonl"

GET_KIND_CANDLES = "CANDLES"
GET_KIND_MARK = "MARK"
GET_KIND_INDEX = "INDEX"
GET_KIND_OTHER = "OTHER"

UNAVAILABLE = "UNAVAILABLE"


class ProductiveNaturalMarketDataCaptureError(RuntimeError):
    """Fail-closed capture persistence violation (does not rewrite GET outcomes)."""


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def classify_natural_market_data_get_kind_v1(*, endpoint: str) -> str:
    path = str(endpoint or "").split("?", 1)[0]
    if path == GET_PATH:
        return GET_KIND_CANDLES
    if path == ENDPOINT_PUBLIC_MARK_PRICE:
        return GET_KIND_MARK
    if path == ENDPOINT_MARKET_INDEX_TICKERS:
        return GET_KIND_INDEX
    return GET_KIND_OTHER


def _split_endpoint_identity_v1(endpoint: str) -> tuple[str, str, dict[str, str]]:
    raw = str(endpoint or "")
    if raw.startswith("https://"):
        parsed = urlparse(raw)
        path = str(parsed.path or "")
        query_pairs = dict(parse_qsl(parsed.query, keep_blank_values=True))
        return path, parsed.query or UNAVAILABLE, query_pairs
    if "?" in raw:
        path, query = raw.split("?", 1)
        return path, query, dict(parse_qsl(query, keep_blank_values=True))
    return raw, UNAVAILABLE, {}


@dataclass
class ProductiveNaturalMarketDataCaptureSinkV1:
    evidence_root: Path
    run_id: str
    native_id: str
    _sequence: int = 0

    def append_successful_get_v1(
        self,
        *,
        result: FreshPretradeGetTransportResultV1,
        endpoint: str,
        auth_required: bool,
        pretrade_decision_id: str,
        get_cache_policy: str,
    ) -> dict[str, Any]:
        if not bool(result.get_performed):
            raise ProductiveNaturalMarketDataCaptureError("CAPTURE_SKIP_NON_SUCCESS_GET")
        request_path, request_query_raw, request_query = _split_endpoint_identity_v1(
            str(result.endpoint or endpoint)
        )
        record: dict[str, Any] = {
            "schema_version": NATURAL_MARKET_DATA_CAPTURE_SCHEMA_VERSION,
            "run_id": str(self.run_id),
            "capture_sequence": int(self._sequence),
            "captured_at_utc": _utc_now_iso_v1(),
            "native_id": str(self.native_id),
            "get_kind": classify_natural_market_data_get_kind_v1(endpoint=endpoint),
            "request_path": request_path,
            "request_query": request_query if request_query else UNAVAILABLE,
            "request_query_raw": request_query_raw,
            "endpoint_from_result": str(result.endpoint or UNAVAILABLE),
            "pretrade_decision_id": str(pretrade_decision_id or UNAVAILABLE),
            "auth_required": bool(auth_required),
            "get_cache_policy": str(get_cache_policy or UNAVAILABLE),
            "http_status": int(result.http_status),
            "get_performed": bool(result.get_performed),
            "transport_class": str(result.transport_class or UNAVAILABLE),
            "payload": result.payload,
            "body_sha256": str(result.body_sha256 or ""),
            "correlation_status": "PARTIAL",
            "complete_poll_bundle_proven": False,
            "bundle_reconstruction_in_this_wp": False,
        }
        root = Path(self.evidence_root)
        root.mkdir(parents=True, exist_ok=True)
        ledger = root / CAPTURE_LEDGER_FILENAME
        line = json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n"
        with ledger.open("a", encoding="utf-8") as handle:
            handle.write(line)
        self._sequence += 1
        return record


class ProductiveNaturalMarketDataCaptureTransportV1:
    """Delegating transport: one delegate GET per call; append-only capture on success."""

    def __init__(
        self,
        delegate: FullCoreProductiveReadOnlyGetTransportV1,
        *,
        sink: ProductiveNaturalMarketDataCaptureSinkV1,
    ) -> None:
        self._delegate = delegate
        self._sink = sink

    def get(
        self,
        *,
        endpoint: str,
        auth_required: bool,
        pretrade_decision_id: str,
        get_cache_policy: str = GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
    ) -> FreshPretradeGetTransportResultV1:
        result = self._delegate.get(
            endpoint=endpoint,
            auth_required=auth_required,
            pretrade_decision_id=pretrade_decision_id,
            get_cache_policy=get_cache_policy,
        )
        if bool(result.get_performed):
            self._sink.append_successful_get_v1(
                result=result,
                endpoint=endpoint,
                auth_required=auth_required,
                pretrade_decision_id=pretrade_decision_id,
                get_cache_policy=get_cache_policy,
            )
        return result

    def __getattr__(self, name: str) -> Any:
        return getattr(self._delegate, name)


def wrap_productive_transport_with_natural_market_data_capture_v1(
    transport: FullCoreProductiveReadOnlyGetTransportV1,
    *,
    evidence_root: Path,
    run_id: str,
    native_id: str,
) -> ProductiveNaturalMarketDataCaptureTransportV1:
    sink = ProductiveNaturalMarketDataCaptureSinkV1(
        evidence_root=Path(evidence_root),
        run_id=str(run_id),
        native_id=str(native_id),
    )
    return ProductiveNaturalMarketDataCaptureTransportV1(delegate=transport, sink=sink)


__all__ = [
    "CAPTURE_LEDGER_FILENAME",
    "GET_KIND_CANDLES",
    "GET_KIND_INDEX",
    "GET_KIND_MARK",
    "GET_KIND_OTHER",
    "NATURAL_MARKET_DATA_CAPTURE_SCHEMA_VERSION",
    "OWNER",
    "ProductiveNaturalMarketDataCaptureError",
    "ProductiveNaturalMarketDataCaptureSinkV1",
    "ProductiveNaturalMarketDataCaptureTransportV1",
    "classify_natural_market_data_get_kind_v1",
    "wrap_productive_transport_with_natural_market_data_capture_v1",
]
