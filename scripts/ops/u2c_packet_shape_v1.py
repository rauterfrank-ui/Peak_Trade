"""U2C → U2B packet shape alignment: flat Kraken rows → nested FuturesProducerPacket JSON."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional


def normalize_market_type(raw: str) -> str:
    """Map U5D contract labels to U2b FuturesMarketType string values."""
    value = (raw or "").strip().lower()
    if value in {"future", "futures", "futures_inverse", "dated_future"}:
        return "futures"
    if value in {"perpetual", "flexible_futures", "swap"}:
        return "perpetual"
    return value or "perpetual"


def flat_row_to_nested_packet(
    row: Mapping[str, Any],
    *,
    candidate_id: str,
    source_universe_size: int,
    rank: Optional[int] = None,
    selected_top_n: int = 20,
) -> Dict[str, Any]:
    """Convert a flat U5D packet_candidate row to nested FuturesProducerPacket JSON."""
    symbol = str(row.get("symbol") or row.get("instrument_id") or "")
    market_type = normalize_market_type(
        str(row.get("market_type") or row.get("contract_type") or "perpetual")
    )
    missing = list(row.get("missing_fields") or [])

    tick_known = row.get("tick_size") is not None
    contract_known = row.get("contract_size") is not None
    min_qty_known = row.get("min_qty") is not None
    min_notional_known = row.get("min_notional") is not None
    margin_known = row.get("margin_asset") is not None
    settlement_known = row.get("settlement_asset") is not None
    leverage_known = row.get("max_leverage") is not None
    known_flags = (
        tick_known,
        contract_known,
        min_qty_known,
        min_notional_known,
        margin_known,
        settlement_known,
        leverage_known,
    )
    instrument_complete = all(known_flags) and not missing

    last_available = row.get("last_price") is not None
    mark_available = row.get("mark_price") is not None
    index_available = row.get("index_price") is not None
    funding_available = row.get("funding_rate") is not None
    oi_available = row.get("open_interest") is not None
    fetched_at = str(row.get("fetched_at") or "")
    provenance_missing: List[str] = []
    if not fetched_at:
        provenance_missing.append("fetched_at")
    if not last_available and not mark_available:
        provenance_missing.append("price")
    provenance_complete = not provenance_missing and bool(fetched_at)

    vol = row.get("vol24h")
    spread = row.get("spread")
    spread_bps: Optional[float] = None
    if isinstance(spread, (int, float)) and row.get("display_price"):
        try:
            spread_bps = (float(spread) / float(row["display_price"])) * 10000.0
        except (TypeError, ValueError, ZeroDivisionError):
            spread_bps = None

    return {
        "candidate": {
            "candidate_id": candidate_id,
            "instrument_id": str(row.get("instrument_id") or symbol),
            "symbol": symbol,
            "market_type": market_type,
            "exchange": str(row.get("exchange") or row.get("provider") or "kraken_futures"),
            "base_currency": str(row.get("base_currency") or ""),
            "quote_currency": str(row.get("quote_currency") or ""),
            "live_authorization": False,
        },
        "ranking": {
            "source_universe_size": source_universe_size,
            "selected_top_n": selected_top_n,
            "rank": rank,
            "score": None,
            "score_components_complete": False,
            "is_top_n_member": rank is not None and rank <= selected_top_n,
        },
        "instrument": {
            "complete": instrument_complete,
            "contract_size_known": contract_known,
            "tick_size_known": tick_known,
            "step_size_known": contract_known,
            "min_qty_known": min_qty_known,
            "min_notional_known": min_notional_known,
            "margin_asset_known": margin_known,
            "settlement_asset_known": settlement_known,
            "leverage_bounds_known": leverage_known,
            "missing_fields": missing,
        },
        "provenance": {
            "complete": provenance_complete,
            "freshness_state": "fresh" if fetched_at else "unknown",
            "dataset_id": f"u2c-{symbol}",
            "source": "governed_metadata_snapshot",
            "mark_available": mark_available,
            "index_available": index_available,
            "last_available": last_available,
            "ohlcv_available": False,
            "funding_available": funding_available,
            "open_interest_available": oi_available,
            "missing_fields": provenance_missing,
        },
        "volatility": {
            "realized_volatility": None,
            "atr_or_rolling_range": None,
            "volatility_regime": None,
            "dynamic_scope_usable": False,
        },
        "liquidity": {
            "spread_bps": spread_bps,
            "average_spread_bps": spread_bps,
            "volume": vol if isinstance(vol, (int, float)) else None,
            "quote_volume": None,
            "liquidity_regime": None,
            "spread_quality": None,
        },
        "derivatives": {
            "funding_available": funding_available,
            "funding_rate": row.get("funding_rate"),
            "funding_regime": None,
            "open_interest_available": oi_available,
            "open_interest": row.get("open_interest"),
            "open_interest_regime": None,
        },
        "opportunity": {
            "opportunity_score": None,
            "inactivity_score": None,
            "movement_above_fee_slippage_breakeven": None,
            "chop_risk": None,
            "candidate_is_inactive": not bool(row.get("active", True)),
        },
    }
