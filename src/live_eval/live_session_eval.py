"""Core evaluation logic for live session fills."""

import copy
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Mapping
from collections import defaultdict

from src.experiments.cross_lane_identity_join_v1 import CrossLaneIdentityJoinV1
from src.live_eval.i61_live_eval_named_lane_identity_join_v1 import (
    join_i61_named_lane_identity_v1,
)


@dataclass
class Fill:
    """Represents a single fill/trade execution."""

    ts: datetime
    symbol: str
    side: str  # 'buy' or 'sell'
    qty: float
    fill_price: float

    def __post_init__(self) -> None:
        """Validate fill data."""
        if self.side not in ("buy", "sell"):
            raise ValueError(f"Invalid side: {self.side}. Must be 'buy' or 'sell'.")
        if self.qty <= 0:
            raise ValueError(f"Quantity must be positive: {self.qty}")
        if self.fill_price <= 0:
            raise ValueError(f"Fill price must be positive: {self.fill_price}")


@dataclass
class Lot:
    """Represents an open position lot (for FIFO PnL calculation)."""

    qty: float
    price: float


def compute_metrics(fills: List[Fill], strict: bool = False) -> Dict[str, Any]:
    """
    Compute comprehensive metrics from a list of fills.

    Args:
        fills: List of Fill objects
        strict: If True, raise error on invalid FIFO matching (sell > available lots)
                If False, treat excess sells as short lots with PnL=0

    Returns:
        Dictionary containing metrics (JSON-serializable)
    """
    if not fills:
        return {
            "total_fills": 0,
            "symbols": [],
            "start_ts": None,
            "end_ts": None,
            "total_notional": 0.0,
            "total_qty": 0.0,
            "vwap_overall": None,
            "side_breakdown": {
                "buy": {"count": 0, "qty": 0.0, "notional": 0.0},
                "sell": {"count": 0, "qty": 0.0, "notional": 0.0},
            },
            "realized_pnl_total": 0.0,
            "realized_pnl_per_symbol": {},
        }

    # Sort fills by timestamp
    sorted_fills = sorted(fills, key=lambda f: f.ts)

    # Basic stats
    symbols = sorted(set(f.symbol for f in fills))
    start_ts = sorted_fills[0].ts.isoformat()
    end_ts = sorted_fills[-1].ts.isoformat()

    # Aggregations
    total_notional = sum(f.qty * f.fill_price for f in fills)
    total_qty = sum(f.qty for f in fills)
    vwap_overall = total_notional / total_qty if total_qty > 0 else None

    # Side breakdown
    side_stats = {
        "buy": {"count": 0, "qty": 0.0, "notional": 0.0},
        "sell": {"count": 0, "qty": 0.0, "notional": 0.0},
    }

    for fill in fills:
        side_stats[fill.side]["count"] += 1
        side_stats[fill.side]["qty"] += fill.qty
        side_stats[fill.side]["notional"] += fill.qty * fill.fill_price

    # FIFO PnL calculation per symbol
    lots_by_symbol: Dict[str, List[Lot]] = defaultdict(list)
    realized_pnl_per_symbol: Dict[str, float] = {}

    for fill in sorted_fills:
        symbol = fill.symbol

        if fill.side == "buy":
            # Open a new long lot
            lots_by_symbol[symbol].append(Lot(qty=fill.qty, price=fill.fill_price))

        else:  # sell
            remaining_sell_qty = fill.qty
            realized_pnl = 0.0

            # Match against available lots (FIFO)
            while remaining_sell_qty > 0 and lots_by_symbol[symbol]:
                oldest_lot = lots_by_symbol[symbol][0]

                if oldest_lot.qty <= remaining_sell_qty:
                    # Fully close this lot
                    matched_qty = oldest_lot.qty
                    realized_pnl += (fill.fill_price - oldest_lot.price) * matched_qty
                    remaining_sell_qty -= matched_qty
                    lots_by_symbol[symbol].pop(0)
                else:
                    # Partially close this lot
                    matched_qty = remaining_sell_qty
                    realized_pnl += (fill.fill_price - oldest_lot.price) * matched_qty
                    oldest_lot.qty -= matched_qty
                    remaining_sell_qty = 0

            # Handle excess sell quantity
            if remaining_sell_qty > 0:
                if strict:
                    raise ValueError(
                        f"Sell quantity exceeds available lots for {symbol} at {fill.ts}. "
                        f"Remaining unmatched: {remaining_sell_qty}"
                    )
                else:
                    # Best-effort: treat as short lot with entry price = sell price (PnL=0)
                    lots_by_symbol[symbol].insert(
                        0, Lot(qty=-remaining_sell_qty, price=fill.fill_price)
                    )

            # Accumulate realized PnL for this symbol
            realized_pnl_per_symbol[symbol] = (
                realized_pnl_per_symbol.get(symbol, 0.0) + realized_pnl
            )

    realized_pnl_total = sum(realized_pnl_per_symbol.values())

    # Per-symbol VWAP (optional detail)
    vwap_per_symbol = {}
    for symbol in symbols:
        symbol_fills = [f for f in fills if f.symbol == symbol]
        symbol_notional = sum(f.qty * f.fill_price for f in symbol_fills)
        symbol_qty = sum(f.qty for f in symbol_fills)
        vwap_per_symbol[symbol] = symbol_notional / symbol_qty if symbol_qty > 0 else None

    return {
        "total_fills": len(fills),
        "symbols": symbols,
        "start_ts": start_ts,
        "end_ts": end_ts,
        "total_notional": total_notional,
        "total_qty": total_qty,
        "vwap_overall": vwap_overall,
        "vwap_per_symbol": vwap_per_symbol,
        "side_breakdown": side_stats,
        "realized_pnl_total": realized_pnl_total,
        "realized_pnl_per_symbol": realized_pnl_per_symbol,
    }


@dataclass(frozen=True)
class LiveSessionMetricsNamedLaneIdentityJoinResultV1:
    contract: Dict[str, Any]
    join: CrossLaneIdentityJoinV1


@dataclass(frozen=True)
class LiveSessionDirNamedLaneIdentityJoinResultV1:
    contract: Dict[str, Any]
    join: CrossLaneIdentityJoinV1


def parse_live_session_metrics_with_identity_join_v1(
    raw: Mapping[str, Any],
    **sidecars: Any,
) -> LiveSessionMetricsNamedLaneIdentityJoinResultV1:
    """Parse live I61 metrics and fail-closed join Package-N IDENTITY sidecar."""
    snapshot = copy.deepcopy(dict(raw)) if isinstance(raw, Mapping) else None
    join = join_i61_named_lane_identity_v1(raw, surface="metrics", **sidecars)
    if not isinstance(raw, Mapping) or snapshot is None:
        raise ValueError("malformed plane data rejected: I61 metrics is not an object")
    contract = copy.deepcopy(dict(raw))
    if dict(raw) != snapshot:
        raise ValueError("I61 metrics input was mutated")
    return LiveSessionMetricsNamedLaneIdentityJoinResultV1(contract=contract, join=join)


def parse_live_session_dir_with_identity_join_v1(
    raw: Mapping[str, Any],
    **sidecars: Any,
) -> LiveSessionDirNamedLaneIdentityJoinResultV1:
    """Parse a live I61 session-dir hint and fail-closed join Package-N IDENTITY sidecar."""
    snapshot = copy.deepcopy(dict(raw)) if isinstance(raw, Mapping) else None
    join = join_i61_named_lane_identity_v1(raw, surface="session", **sidecars)
    if not isinstance(raw, Mapping) or snapshot is None:
        raise ValueError("malformed plane data rejected: I61 session is not an object")
    contract = {"session_dir": str(raw["session_dir"])}
    if dict(raw) != snapshot:
        raise ValueError("I61 session input was mutated")
    return LiveSessionDirNamedLaneIdentityJoinResultV1(contract=contract, join=join)
