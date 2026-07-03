"""Canonical trade-record schema adapter for cross-sectional backtest wiring v0.

Single owner for Execution-v2 → compute_backtest_stats trade-record contract.
Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_TRADE_RECORD_SCHEMA_V0=true"
SCHEMA_VERSION = "cross_sectional_trade_record_schema.v0"

CANONICAL_PNL_FIELD = "pnl"
PNL_UNIT = "absolute_quote_currency"

REQUIRED_STATS_FIELDS = (
    "entry_time",
    "exit_time",
    "instrument_id",
    "side",
    "entry_price",
    "exit_price",
    CANONICAL_PNL_FIELD,
    "gross_pnl",
    "entry_cost",
    "exit_cost",
    "gross_pnl_frac",
    "pnl_unit",
)


class TradeRecordContractError(KeyError):
    """Fail-closed when a trade record lacks the canonical PnL field."""


def validate_trade_record_for_stats_v0(record: Mapping[str, Any], *, index: int = 0) -> None:
    """Raise TradeRecordContractError when canonical pnl is missing."""
    if CANONICAL_PNL_FIELD not in record:
        keys = sorted(str(key) for key in record.keys())
        raise TradeRecordContractError(
            f"trade_record_missing_canonical_pnl_field index={index} keys={keys}"
        )
    pnl = record[CANONICAL_PNL_FIELD]
    if pnl is None:
        raise TradeRecordContractError(f"trade_record_null_canonical_pnl_field index={index}")


def normalize_trades_for_stats_v0(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Validate and return trade dicts for compute_backtest_stats (fail-closed)."""
    normalized: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        validate_trade_record_for_stats_v0(record, index=index)
        normalized.append(dict(record))
    return normalized


def compute_roundtrip_net_pnl_v0(
    *,
    equity_at_entry: float,
    equity_before_exit: float,
    gross_pnl_frac: float,
    exit_cost: float,
) -> tuple[float, float]:
    """Return (gross_pnl_abs, net_pnl_abs) with costs applied exactly once."""
    gross_pnl_abs = equity_before_exit * gross_pnl_frac
    equity_after = equity_before_exit * (1.0 + gross_pnl_frac) - exit_cost
    net_pnl_abs = equity_after - equity_at_entry
    return gross_pnl_abs, net_pnl_abs
