"""U2C → U2B packet shape alignment: flat Kraken rows → nested FuturesProducerPacket JSON."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

MARKET_DATA_MISSING_FIELD_NAMES = frozenset(
    {
        "vol24h",
        "bid_ask",
        "funding_rate",
        "open_interest",
        "last_price",
        "mark_price",
        "index_price",
    }
)

MISSING_PROVIDER_METADATA_NOT_IN_PUBLIC_VIEW = frozenset({"min_notional"})

CANDIDATE_VALIDATION_ALLOWED_MISSING_PROVIDER_METADATA = frozenset({"min_notional"})


def normalize_market_type(raw: str) -> str:
    """Map U5D contract labels to U2b FuturesMarketType string values."""
    value = (raw or "").strip().lower()
    if value in {"future", "futures", "futures_inverse", "dated_future"}:
        return "futures"
    if value in {"perpetual", "flexible_futures", "swap"}:
        return "perpetual"
    return value or "perpetual"


def _parse_positive_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed


def extract_kraken_provider_instrument_fields(inst: Mapping[str, Any]) -> Dict[str, Any]:
    """Map real Kraken instruments payload fields — no invented sizing or margin values."""
    out: Dict[str, Any] = {}
    missing_provider: List[str] = []

    impact = inst.get("impactMidSize")
    min_qty = _parse_positive_float(impact)
    if min_qty is not None:
        out["min_qty"] = min_qty
        out["min_qty_source"] = "kraken_instruments.impactMidSize"

    quote = inst.get("quote")
    if isinstance(quote, str) and quote.strip():
        quote_value = quote.strip()
        out["margin_asset"] = quote_value
        out["settlement_asset"] = quote_value
        out["margin_asset_source"] = "kraken_instruments.quote"
        out["settlement_asset_source"] = "kraken_instruments.quote"

    levels = inst.get("retailMarginLevels") or inst.get("marginLevels")
    if isinstance(levels, list) and levels:
        first = levels[0]
        if isinstance(first, dict):
            initial = first.get("initialMargin")
            maintenance = first.get("maintenanceMargin")
            initial_rate = _parse_positive_float(initial)
            if initial_rate is not None:
                out["max_leverage"] = round(1.0 / initial_rate, 6)
                out["initial_margin_rate"] = initial_rate
                out["leverage_bounds_source"] = (
                    "kraken_instruments.retailMarginLevels[0].initialMargin"
                )
            maintenance_rate = _parse_positive_float(maintenance)
            if maintenance_rate is not None:
                out["maintenance_margin_rate"] = maintenance_rate

    if inst.get("min_notional") is None:
        missing_provider.append("min_notional")
    out["missing_provider_metadata"] = sorted(set(missing_provider))
    return out


def _instrument_missing_fields_from_row(row: Mapping[str, Any]) -> List[str]:
    explicit = row.get("instrument_missing_fields")
    if explicit is not None:
        return sorted({str(item) for item in explicit if str(item)})
    legacy = list(row.get("missing_fields") or [])
    return sorted(
        {
            str(item)
            for item in legacy
            if str(item) and str(item) not in MARKET_DATA_MISSING_FIELD_NAMES
        }
    )


def assess_instrument_completeness(row: Mapping[str, Any]) -> Dict[str, Any]:
    """Classify strict vs candidate-validation instrument completeness from flat row data."""
    instrument_missing = _instrument_missing_fields_from_row(row)
    missing_provider = sorted(
        {str(item) for item in (row.get("missing_provider_metadata") or []) if str(item)}
    )
    if row.get("min_notional") is None and "min_notional" not in missing_provider:
        missing_provider.append("min_notional")
        missing_provider = sorted(set(missing_provider))

    tick_known = row.get("tick_size") is not None
    contract_known = row.get("contract_size") is not None
    min_qty_known = row.get("min_qty") is not None
    min_notional_known = row.get("min_notional") is not None
    margin_known = row.get("margin_asset") is not None
    settlement_known = row.get("settlement_asset") is not None
    leverage_known = row.get("max_leverage") is not None

    provider_flags: Tuple[bool, ...] = (
        tick_known,
        contract_known,
        min_qty_known,
        margin_known,
        settlement_known,
        leverage_known,
    )
    provider_complete = all(provider_flags) and not instrument_missing
    strict_complete = provider_complete and min_notional_known

    allowed_missing = set(missing_provider).issubset(
        CANDIDATE_VALIDATION_ALLOWED_MISSING_PROVIDER_METADATA
    )
    candidate_validation_complete = provider_complete and allowed_missing

    reasons: List[str] = []
    if instrument_missing:
        reasons.append(f"instrument_missing:{','.join(instrument_missing)}")
    unknown_provider_fields: List[str] = []
    if not tick_known:
        unknown_provider_fields.append("tick_size")
    if not contract_known:
        unknown_provider_fields.append("contract_size")
    if not min_qty_known:
        unknown_provider_fields.append("min_qty")
    if not margin_known:
        unknown_provider_fields.append("margin_asset")
    if not settlement_known:
        unknown_provider_fields.append("settlement_asset")
    if not leverage_known:
        unknown_provider_fields.append("max_leverage")
    if unknown_provider_fields:
        reasons.append(f"provider_fields_missing:{','.join(unknown_provider_fields)}")
    if not min_notional_known:
        reasons.append("missing_provider_metadata:min_notional")

    return {
        "instrument_missing_fields": instrument_missing,
        "missing_provider_metadata": missing_provider,
        "provider_instrument_complete": provider_complete,
        "strict_instrument_complete": strict_complete,
        "candidate_validation_complete": candidate_validation_complete,
        "completeness_reason": "; ".join(reasons) if reasons else "all_provider_fields_present",
        "tick_size_known": tick_known,
        "contract_size_known": contract_known,
        "min_qty_known": min_qty_known,
        "min_notional_known": min_notional_known,
        "margin_asset_known": margin_known,
        "settlement_asset_known": settlement_known,
        "leverage_bounds_known": leverage_known,
    }


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
    assessment = assess_instrument_completeness(row)
    instrument_missing = assessment["instrument_missing_fields"]

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

    market_data_missing = sorted(
        {
            str(item)
            for item in (row.get("market_data_missing_fields") or row.get("missing_fields") or [])
            if str(item)
        }
    )

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
            "complete": assessment["strict_instrument_complete"],
            "candidate_validation_complete": assessment["candidate_validation_complete"],
            "contract_size_known": assessment["contract_size_known"],
            "tick_size_known": assessment["tick_size_known"],
            "step_size_known": assessment["contract_size_known"],
            "min_qty_known": assessment["min_qty_known"],
            "min_notional_known": assessment["min_notional_known"],
            "margin_asset_known": assessment["margin_asset_known"],
            "settlement_asset_known": assessment["settlement_asset_known"],
            "leverage_bounds_known": assessment["leverage_bounds_known"],
            "missing_fields": instrument_missing,
            "missing_provider_metadata": assessment["missing_provider_metadata"],
            "completeness_reason": assessment["completeness_reason"],
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
            "market_data_missing_fields": market_data_missing,
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


def summarize_instrument_completeness(
    packets: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Aggregate completeness stats for governed candidate bundle metadata."""
    strict_complete = 0
    candidate_validation_complete = 0
    missing_provider_counts: Dict[str, int] = {}
    for packet in packets:
        instrument = packet.get("instrument") or {}
        if instrument.get("complete"):
            strict_complete += 1
        if instrument.get("candidate_validation_complete"):
            candidate_validation_complete += 1
        for field in instrument.get("missing_provider_metadata") or []:
            key = str(field)
            missing_provider_counts[key] = missing_provider_counts.get(key, 0) + 1
    total = len(packets)
    return {
        "packet_count": total,
        "strict_instrument_complete_count": strict_complete,
        "candidate_validation_complete_count": candidate_validation_complete,
        "missing_provider_metadata_counts": missing_provider_counts,
    }
