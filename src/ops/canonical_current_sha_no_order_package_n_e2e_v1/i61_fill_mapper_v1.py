"""Minimal Cap 7.1 fill-dict → I61 Fill mapper.

Does not change Fill, compute_metrics, or live-session semantics.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from src.live_eval.live_session_eval import Fill
from src.ops.canonical_current_sha_no_order_package_n_e2e_v1.constants_v1 import (
    PRODUCTION_INSTRUMENT_ID,
)

_SIDE_MAP = {
    "BUY": "buy",
    "SELL": "sell",
    "buy": "buy",
    "sell": "sell",
}


class I61FillMapperError(ValueError):
    """Fail-closed Cap 7.1 → I61 fill mapping error."""


def map_cap71_fills_to_i61_fills_v1(fills: Sequence[Mapping[str, Any]]) -> list[Fill]:
    """Map Cap 7.1 simulated fill dicts onto existing I61 Fill objects."""
    if not isinstance(fills, Sequence) or isinstance(fills, (str, bytes)):
        raise I61FillMapperError("Cap 7.1 fills must be a sequence of objects")
    mapped: list[Fill] = []
    for index, raw in enumerate(fills):
        if not isinstance(raw, Mapping):
            raise I61FillMapperError("Cap 7.1 fill entry must be an object")
        side_raw = str(raw.get("side") or "")
        side = _SIDE_MAP.get(side_raw)
        if side is None:
            continue
        try:
            qty = float(str(raw.get("quantity") or "0"))
            price = float(str(raw.get("fill_price") or "0"))
        except (TypeError, ValueError) as exc:
            raise I61FillMapperError("Cap 7.1 fill quantity/price is not numeric") from exc
        if qty <= 0 or price <= 0:
            continue
        ts_raw = raw.get("event_ts_unix")
        if ts_raw is None:
            ts = datetime.fromtimestamp(1_700_000_000 + index, tz=timezone.utc)
        else:
            ts = datetime.fromtimestamp(float(ts_raw), tz=timezone.utc)
        symbol = str(raw.get("instrument_id") or PRODUCTION_INSTRUMENT_ID)
        mapped.append(
            Fill(
                ts=ts,
                symbol=symbol,
                side=side,
                qty=qty,
                fill_price=price,
            )
        )
    return mapped
