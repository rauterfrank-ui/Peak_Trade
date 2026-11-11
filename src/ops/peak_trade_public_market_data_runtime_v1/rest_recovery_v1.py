"""Public REST bootstrap, history, and gap-fill recovery."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import time
from typing import Any, Callable, Mapping, Optional

from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import (
    EEA_REST_HOST,
    MARK_HISTORY_CANDLES_PATH,
    MARK_PRICE_REST_PATH,
    PT1M_STEP_MS,
    TICKER_REST_PATH,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import (
    DataQualityStateV1,
    FinalizedPt1mMarkFactV1,
    InstrumentRefV1,
    fact_digest,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


class PublicRestRecoveryError(RuntimeError):
    pass


RestGetJson = Callable[[str, Mapping[str, str]], Mapping[str, Any]]


@dataclass
class GapRecoveryResultV1:
    gaps_detected: int
    recovered_bars: tuple[FinalizedPt1mMarkFactV1, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)


def collect_bound_rest_pt1m_mark_window_v1(
    fetch_json: RestGetJson,
    *,
    instrument_ref: InstrumentRefV1,
    session_id: str,
) -> tuple[tuple[FinalizedPt1mMarkFactV1, ...], float, float]:
    from src.ops.economic_md_input_producer_v1.constants_v1 import MARK_BAR, MARK_HISTORY_LIMIT
    from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
        parse_okx_mark_candles_v1,
    )
    from src.ops.economic_md_input_producer_v1.validation_v1 import (
        select_finalized_contiguous_pt1m_marks_v1,
    )

    started = time.time()
    payload = fetch_json(
        MARK_HISTORY_CANDLES_PATH,
        {"instId": instrument_ref.venue_native_id, "bar": MARK_BAR, "limit": MARK_HISTORY_LIMIT},
    )
    captured = time.time()
    data = payload.get("data") if isinstance(payload, Mapping) else None
    if (
        captured < started
        or not isinstance(data, list)
        or len(data) > int(MARK_HISTORY_LIMIT)
        or payload.get("code") != "0"
        or any(
            not isinstance(row, list)
            or len(row) != 6
            or row[5] not in ("0", "1")
            or not isinstance(row[0], str)
            or not row[0].isascii()
            or not row[0].isdigit()
            or not isinstance(row[4], str)
            for row in data
        )
    ):
        raise PublicRestRecoveryError("PUBLIC_PT1M_HISTORY_RESPONSE_UNPROVEN")
    captured_at = datetime.fromtimestamp(captured, timezone.utc).isoformat()
    raw = parse_okx_mark_candles_v1(
        payload,
        venue_native_id=instrument_ref.venue_native_id,
        receive_or_capture_timestamp=captured_at,
    )
    try:
        marks, failures = select_finalized_contiguous_pt1m_marks_v1(raw)
    except ValueError as exc:
        raise PublicRestRecoveryError("PUBLIC_PT1M_HISTORY_RESPONSE_UNPROVEN") from exc
    if failures:
        raise PublicRestRecoveryError("PUBLIC_PT1M_WINDOW_UNPROVEN:" + ",".join(failures))
    intervals = [int(mark.event_timestamp) for mark in marks]
    if any(ts % PT1M_STEP_MS or ts + PT1M_STEP_MS > int(captured * 1000) for ts in intervals):
        raise PublicRestRecoveryError("PUBLIC_PT1M_INTERVAL_UNPROVEN")
    normalized = parse_finalized_pt1m_mark_rows_v1(
        payload,
        instrument_ref_dict=instrument_ref.to_dict(),
        captured_at=captured_at,
        transport="public_rest",
    )
    by_interval = {fact.interval_start_ms: fact for fact in normalized}
    payload_digest = fact_digest(payload)
    return (
        tuple(
            replace(
                fact,
                provenance=replace(
                    fact.provenance, raw_payload_digest=payload_digest, session_id=session_id
                ),
            )
            for fact in (by_interval[ts] for ts in intervals)
        ),
        started,
        captured,
    )


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


def public_instrument_ref_for_binding_v1(bound: BoundInstrumentV1) -> InstrumentRefV1:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_future_identity_semantics_v1 import (
        resolve_selected_future_market_type_v1,
    )
    from trading.master_v2.double_play_futures_input import FuturesMarketType

    canonical = bound.instrument_id
    fields = canonical.split(":")
    if len(fields) != 6 or fields[0] != "okx_eea":
        raise PublicRestRecoveryError("PUBLIC_BOOTSTRAP_BOUND_INSTRUMENT_UNPROVEN")
    try:
        market_type = resolve_selected_future_market_type_v1(
            instrument_id=canonical, venue_native_id=bound.venue_native_id
        )
    except ValueError as exc:
        raise PublicRestRecoveryError("PUBLIC_BOOTSTRAP_BOUND_INSTRUMENT_UNPROVEN") from exc
    return InstrumentRefV1(
        canonical_instrument_id=canonical,
        venue_native_id=bound.venue_native_id,
        venue=fields[0],
        instrument_type="FUTURES" if market_type is FuturesMarketType.FUTURES else "SWAP",
        settlement_asset=fields[4],
        mapping_provenance_digest=fact_digest(
            {
                "instrument_id": canonical,
                "venue_native_id": bound.venue_native_id,
                "selection_integrity_digest": bound.selection_integrity_digest,
            }
        ),
    )


def _require_bound_public_row(
    payload: Mapping[str, Any], instrument_ref: InstrumentRefV1, reason: str
) -> Mapping[str, Any]:
    rows = payload.get("data") if isinstance(payload, Mapping) else None
    if (
        not isinstance(rows, list)
        or len(rows) != 1
        or not isinstance(rows[0], Mapping)
        or payload.get("code") != "0"
        or rows[0].get("instId") != instrument_ref.venue_native_id
        or rows[0].get("instType") != instrument_ref.instrument_type
    ):
        raise PublicRestRecoveryError(reason)
    return rows[0]


def bootstrap_rest_snapshot_v1(
    fetch_json: RestGetJson,
    venue_native_id: str,
    *,
    instrument_ref: InstrumentRefV1 | None = None,
) -> dict[str, Any]:
    inst_type = "SWAP"
    if instrument_ref is not None:
        if instrument_ref.venue_native_id != venue_native_id:
            raise PublicRestRecoveryError("PUBLIC_BOOTSTRAP_BOUND_INSTRUMENT_UNPROVEN")
        inst_type = instrument_ref.instrument_type
    mark = fetch_json(MARK_PRICE_REST_PATH, {"instType": inst_type, "instId": venue_native_id})
    if instrument_ref is not None:
        reason = "PUBLIC_MARK_BOOTSTRAP_UNPROVEN"
        row = _require_bound_public_row(mark, instrument_ref, reason)
        try:
            price = Decimal(str(row.get("markPx")))
        except InvalidOperation as exc:
            raise PublicRestRecoveryError(reason) from exc
        ts = str(row.get("ts"))
        if not price.is_finite() or price <= 0 or not ts.isascii() or not ts.isdecimal():
            raise PublicRestRecoveryError(reason)
        if not ts.lstrip("0"):
            raise PublicRestRecoveryError(reason)
    ticker = fetch_json(TICKER_REST_PATH, {"instId": venue_native_id})
    if instrument_ref is not None:
        _require_bound_public_row(ticker, instrument_ref, "PUBLIC_TICKER_BOOTSTRAP_UNPROVEN")
    return {"mark": mark, "ticker": ticker, "host": EEA_REST_HOST}
