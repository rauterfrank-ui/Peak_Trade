"""Explicit market-data price basis (no silent ticker fallback chain)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional

from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.constants_v2 import (
    BID_ASK_POLICY,
    FEATURE_PRICE_SOURCE,
    FILL_REFERENCE_PRICE_SOURCE,
    MARK_TO_MARKET_PRICE_SOURCE,
    PRICE_BASIS_CONTRACT_VERSION,
    REQUIRED_TICKER_PRICE_FIELD,
    SYNTHETIC_BID_ASK_FALLBACK_ACTIVE,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.provenance_v2 import (
    digest_mapping,
)


class PriceBasisErrorV2(ValueError):
    """Fail-closed price-basis error."""


@dataclass(frozen=True)
class ExplicitPriceBasisV2:
    mid_price: float
    price_field: str
    feature_price_source: str
    fill_reference_price_source: str
    mark_to_market_price_source: str
    bid_ask_policy: str
    price_basis_contract_version: str
    synthetic_bid_ask_fallback_active: bool
    best_bid: float
    best_ask: float
    spread: float
    exchange_timestamp_present: bool
    local_receive_timestamp_present: bool
    event_ts_unix: float
    receive_ts_unix: float
    market_data_reference: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def extract_explicit_ticker_price_v2(
    payload: Mapping[str, Any],
    *,
    required_field: str = REQUIRED_TICKER_PRICE_FIELD,
) -> float:
    """Require an explicit ticker field. No silent last→markPx→ask→bid chain."""
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise PriceBasisErrorV2("TICKER_DATA_MISSING")
    row = data[0]
    if not isinstance(row, dict):
        raise PriceBasisErrorV2("TICKER_ROW_INVALID")
    raw = row.get(required_field)
    if raw is None or raw == "":
        raise PriceBasisErrorV2(f"REQUIRED_PRICE_FIELD_MISSING:{required_field}")
    price = float(raw)
    if price <= 0 or price != price:  # noqa: PLR0124 — NaN check
        raise PriceBasisErrorV2(f"REQUIRED_PRICE_FIELD_INVALID:{required_field}")
    return price


def build_explicit_mid_price_basis_v2(
    *,
    mid_price: float,
    event_ts_unix: float,
    receive_ts_unix: float,
    price_field: str = REQUIRED_TICKER_PRICE_FIELD,
    bid_px: Optional[float] = None,
    ask_px: Optional[float] = None,
) -> ExplicitPriceBasisV2:
    if mid_price <= 0 or mid_price != mid_price:  # noqa: PLR0124
        raise PriceBasisErrorV2("MID_PRICE_INVALID")
    if bid_px is not None and ask_px is not None and bid_px > 0 and ask_px > 0:
        if ask_px < bid_px:
            raise PriceBasisErrorV2("BID_ASK_INVERTED")
        best_bid = float(bid_px)
        best_ask = float(ask_px)
        spread = best_ask - best_bid
        policy = "EXPLICIT_BID_ASK_FROM_TICKER"
        synthetic = False
    else:
        # Documented collapsed-mid contract (not silent 0.9999/1.0001 invention).
        best_bid = float(mid_price)
        best_ask = float(mid_price)
        spread = 0.0
        policy = BID_ASK_POLICY
        synthetic = SYNTHETIC_BID_ASK_FALLBACK_ACTIVE
    ref = digest_mapping(
        {
            "mid_price": mid_price,
            "price_field": price_field,
            "event_ts_unix": event_ts_unix,
            "receive_ts_unix": receive_ts_unix,
            "contract": PRICE_BASIS_CONTRACT_VERSION,
        }
    )
    return ExplicitPriceBasisV2(
        mid_price=float(mid_price),
        price_field=price_field,
        feature_price_source=FEATURE_PRICE_SOURCE,
        fill_reference_price_source=FILL_REFERENCE_PRICE_SOURCE,
        mark_to_market_price_source=MARK_TO_MARKET_PRICE_SOURCE,
        bid_ask_policy=policy,
        price_basis_contract_version=PRICE_BASIS_CONTRACT_VERSION,
        synthetic_bid_ask_fallback_active=synthetic,
        best_bid=best_bid,
        best_ask=best_ask,
        spread=spread,
        exchange_timestamp_present=True,
        local_receive_timestamp_present=True,
        event_ts_unix=float(event_ts_unix),
        receive_ts_unix=float(receive_ts_unix),
        market_data_reference=ref,
    )
