"""The exact instrument scopes of the existing I17 observation path."""

from collections.abc import Sequence
from dataclasses import dataclass, replace

from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
)


@dataclass(frozen=True)
class I17ShadowInstrumentV1:
    canonical_id: str
    native_id: str
    base: str
    lane_id: str | None = None
    instrument_type: str = "FUTURES"
    settlement_currency: str = "USD"
    contract_family: str = "xperp"


ETH_I17 = I17ShadowInstrumentV1(CANONICAL_INSTRUMENT_ID, CANONICAL_INSTRUMENT_ID, "ETH")
SOPH_I17 = I17ShadowInstrumentV1(
    "okx_eea:linear_dated_future:SOPH:USD:USD:soph-usd_um_xperp-310912",
    "SOPH-USD_UM_XPERP-310912",
    "SOPH",
    "LANE_2",
)
SOPH_I17_ARCHIVED_SLOT5 = replace(SOPH_I17, lane_id="LANE_5")


# Supported observation contracts. Actual occupancy is read separately from N5.
RANKED_SWAP_SCOPES = tuple(
    I17ShadowInstrumentV1(
        f"okx_eea:linear_perpetual:{base}:USDT:USDT:{base.lower()}-usdt-swap",
        f"{base}-USDT-SWAP",
        base,
        lane,
        "SWAP",
        "USDT",
        "linear_perpetual",
    )
    for base, lane in (
        ("UP", "LANE_1"),
        ("PIEVERSE", "LANE_4"),
        ("OL", "LANE_4"),
        ("CSOPSKHYNIX2L", "LANE_4"),
    )
)


def require_i17_shadow_instrument_v1(allowlist: Sequence[str]) -> I17ShadowInstrumentV1:
    for instrument in (ETH_I17, SOPH_I17, *RANKED_SWAP_SCOPES):
        if tuple(allowlist) == (instrument.native_id,):
            return instrument
    raise ValueError("I17_SHADOW_INSTRUMENT_SCOPE_MISMATCH")


def recorded_i17_shadow_instrument_v1(
    allowlist: Sequence[str], lane_id: str | None
) -> I17ShadowInstrumentV1:
    """Resolve the slot recorded in the original archive, including older sessions."""
    current = require_i17_shadow_instrument_v1(allowlist)
    if current == SOPH_I17 and lane_id == SOPH_I17_ARCHIVED_SLOT5.lane_id:
        return SOPH_I17_ARCHIVED_SLOT5
    if lane_id != current.lane_id:
        raise ValueError("I17_SHADOW_INSTRUMENT_SCOPE_MISMATCH")
    return current


def swap_queries_v1(native, underlying):
    exact = {"instId": native, "instType": "SWAP"}
    return {
        "index": ("/api/v5/market/index-tickers", {"instId": underlying}),
        "funding": ("/api/v5/public/funding-rate", {"instId": native}),
        "oi": ("/api/v5/public/open-interest", exact),
        "ticker": ("/api/v5/market/ticker", {"instId": native}),
        "book": ("/api/v5/market/books", {"instId": native, "sz": "5"}),
        "mark": ("/api/v5/public/mark-price", exact),
    }
