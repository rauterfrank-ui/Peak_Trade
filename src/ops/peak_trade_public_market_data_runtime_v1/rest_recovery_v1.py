"""Public REST bootstrap, history, and gap-fill recovery."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional

from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import (
    EEA_REST_HOST,
    MARK_HISTORY_CANDLES_PATH,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import (
    DataQualityStateV1,
    FinalizedPt1mMarkFactV1,
)


class PublicRestRecoveryError(RuntimeError):
    pass


RestGetJson = Callable[[str, Mapping[str, str]], Mapping[str, Any]]


@dataclass
class GapRecoveryResultV1:
    gaps_detected: int
    recovered_bars: tuple[FinalizedPt1mMarkFactV1, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)


def assert_eea_rest_host_v1(url_or_host: str) -> None:
    host = url_or_host.replace("https://", "").split("/")[0].lower()
    if host != EEA_REST_HOST and EEA_REST_HOST not in url_or_host:
        if host == "www.okx.com":
            raise PublicRestRecoveryError("GLOBAL_OKX_REST_NOT_EEA_PUBLIC_RUNTIME")


def parse_finalized_pt1m_mark_rows_v1(
    payload: Mapping[str, Any],
    *,
    instrument_ref_dict: Mapping[str, Any],
    captured_at: str,
    transport: str,
) -> list[FinalizedPt1mMarkFactV1]:
    from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import (
        DataQualityStateV1,
        InstrumentRefV1,
        MarketFactProvenanceV1,
        MarketTimestampV1,
    )

    data = payload.get("data")
    if not isinstance(data, list):
        raise PublicRestRecoveryError("MARK_ROWS_NOT_LIST")
    inst = InstrumentRefV1(**instrument_ref_dict)
    rows: list[FinalizedPt1mMarkFactV1] = []
    for item in data:
        if not isinstance(item, list) or len(item) < 6:
            continue
        confirm_idx = 5 if len(item) <= 6 else len(item) - 1
        confirm = str(item[confirm_idx])
        if confirm != "1":
            continue
        ts_ms = int(str(item[0]))
        mark_px = str(item[4])
        prov = MarketFactProvenanceV1(
            transport=transport,
            endpoint_or_channel=MARK_HISTORY_CANDLES_PATH,
            raw_payload_digest="",
            session_id="rest_recovery",
            eea_endpoint_family=EEA_REST_HOST,
        )
        quality = DataQualityStateV1(
            finalized=True,
            in_progress=False,
            missing=False,
            stale=False,
            corrected=False,
            duplicate=False,
            out_of_order=False,
            gap_detected=False,
        )
        rows.append(
            FinalizedPt1mMarkFactV1(
                instrument=inst,
                mark_px=mark_px,
                interval_start_ms=ts_ms,
                confirm=confirm,
                timestamps=MarketTimestampV1(
                    venue_event_time_ms=ts_ms,
                    captured_at=captured_at,
                    effective_at=captured_at,
                    source_clock_class="venue_event_ms",
                ),
                provenance=prov,
                quality=quality,
            )
        )
    return rows


def recover_pt1m_gaps_via_rest_v1(
    *,
    fetch_json: RestGetJson,
    venue_native_id: str,
    instrument_ref_dict: Mapping[str, Any],
    missing_interval_starts_ms: list[int],
    captured_at: str,
) -> GapRecoveryResultV1:
    if not missing_interval_starts_ms:
        return GapRecoveryResultV1(0, (), ("NO_GAPS",))
    params = {"instId": venue_native_id, "bar": "1m", "limit": "100"}
    payload = fetch_json(MARK_HISTORY_CANDLES_PATH, params)
    rows = parse_finalized_pt1m_mark_rows_v1(
        payload,
        instrument_ref_dict=instrument_ref_dict,
        captured_at=captured_at,
        transport="public_rest",
    )
    by_ts = {r.interval_start_ms: r for r in rows}
    recovered: list[FinalizedPt1mMarkFactV1] = []
    for ts in sorted(missing_interval_starts_ms):
        row = by_ts.get(ts)
        if row is None:
            raise PublicRestRecoveryError(f"GAP_NOT_RECOVERED:{ts}")
        q = row.quality
        recovered.append(
            FinalizedPt1mMarkFactV1(
                instrument=row.instrument,
                mark_px=row.mark_px,
                interval_start_ms=row.interval_start_ms,
                confirm=row.confirm,
                timestamps=row.timestamps,
                provenance=row.provenance,
                quality=DataQualityStateV1(
                    finalized=q.finalized,
                    in_progress=False,
                    missing=False,
                    stale=q.stale,
                    corrected=q.corrected,
                    duplicate=q.duplicate,
                    out_of_order=q.out_of_order,
                    gap_detected=False,
                ),
            )
        )
    return GapRecoveryResultV1(
        gaps_detected=len(missing_interval_starts_ms),
        recovered_bars=tuple(recovered),
        notes=("REST_GAP_RECOVERY",),
    )


def bootstrap_rest_snapshot_v1(fetch_json: RestGetJson, venue_native_id: str) -> dict[str, Any]:
    mark = fetch_json("/api/v5/public/mark-price", {"instType": "SWAP", "instId": venue_native_id})
    ticker = fetch_json("/api/v5/market/ticker", {"instId": venue_native_id})
    return {"mark": mark, "ticker": ticker, "host": EEA_REST_HOST}
