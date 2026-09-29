"""Controlled external market observation builders for productive sessions.

Builds transport-level candle/mark payloads from deterministic close schedules.
No MV2 state, no ARM/ENTER semantics — observation data only.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
    prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    PREVIOUS_C1_VENUE_EVENT_TIME,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

NATURAL_ENTER_MARK_INCREMENT_V1 = 5.0


def governed_productive_c1_event_ts_unix_v1(*, offset_seconds: float = 120.0) -> float:
    return float(PREVIOUS_C1_VENUE_EVENT_TIME) + float(offset_seconds)


def strong_uptrend_closes_v1(
    *, count: int = 64, base: float = 1000.0, step: float = 10.0
) -> tuple[float, ...]:
    return tuple(base + float(index) * step for index in range(count))


def natural_enter_long_closes_v1(
    uptrend: tuple[float, ...] | None = None,
    *,
    mark_increment: float = NATURAL_ENTER_MARK_INCREMENT_V1,
) -> tuple[float, ...]:
    path = uptrend if uptrend is not None else strong_uptrend_closes_v1()
    return tuple(list(path) + [float(path[-1]) + float(mark_increment)])


def governed_c1_candles_payload_from_closes_v1(
    *,
    closes: Sequence[float],
    last_event_ts_unix: float,
) -> dict[str, object]:
    last_ms = int(float(last_event_ts_unix) * 1000)
    rows: list[list[str]] = []
    for index, close_px in enumerate(closes):
        ts = str(last_ms - (len(closes) - 1 - index) * 60_000)
        px = f"{float(close_px):.4f}"
        rows.append([ts, px, px, px, px, "10", "100", "USDT", "1"])
    return {"code": "0", "data": rows}


def governed_c1_aligned_g17_dk_producer_v1(
    *,
    bound: BoundInstrumentV1,
    anchor_event_ts_unix: float,
    evidence_store_root: Path,
    mark_closes: Sequence[float] | None = None,
) -> object:
    last_ms = int(float(anchor_event_ts_unix) * 1000)
    if mark_closes is not None and len(mark_closes) > 0:
        raw = tuple(float(x) for x in mark_closes)
        if len(raw) >= 61:
            price_series = raw[-61:]
        else:
            pad = [raw[0]] * (61 - len(raw))
            price_series = tuple(pad + list(raw))
    else:
        price_series = tuple(100.0 + float(index) for index in range(61))
    rows: list[list[str]] = []
    for index in range(61):
        ts = str(last_ms - (60 - index) * 60_000)
        px = str(price_series[index])
        rows.append([ts, px, px, px, px, "1"])
    payload = {"code": "0", "msg": "", "data": list(reversed(rows))}
    join = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
        evidence_store_root=Path(evidence_store_root),
        bound_instrument=bound,
        mark_candles_payload=payload,
        receive_or_capture_timestamp=str(last_ms),
    )
    if join.fail_closed or join.producer is None:
        raise RuntimeError(join.reason_code or "G17_DK_ALIGNED_PRODUCER_FAIL_CLOSED")
    return join.producer
