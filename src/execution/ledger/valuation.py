from __future__ import annotations

from decimal import Decimal
from typing import Dict, Optional

from .engine_legacy import LegacyLedgerEngine
from .models import QuantizationPolicy, ValuationSnapshot


def snapshot_mark_to_market(
    engine: LegacyLedgerEngine,
    *,
    ts_sim: int,
    prices: Dict[str, Decimal],
    meta: Optional[dict] = None,
) -> ValuationSnapshot:
    """
    Convenience wrapper for mark-to-market valuation.

    Determinism:
    - prices are inputs (Decimal)
    - ts_sim is caller-provided ordering key
    """
    return engine.snapshot(ts_sim=ts_sim, mark_prices=prices, meta=meta)
