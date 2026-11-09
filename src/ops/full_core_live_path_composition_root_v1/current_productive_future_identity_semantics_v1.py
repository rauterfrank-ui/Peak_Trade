"""Resolve selected-future identity without silently treating dated futures as swaps."""

import re

from src.research.instrument_id_canonicalization_v1 import validate_instrument_id_format_v1
from trading.master_v2.double_play_futures_input import FuturesMarketType


def resolve_selected_future_market_type_v1(
    *, instrument_id: str, venue_native_id: str
) -> FuturesMarketType:
    native = str(venue_native_id or "").strip().upper()
    xperp = re.fullmatch(r"[A-Z0-9]+-USD_UM_XPERP-\d{6}", native) is not None
    if native.endswith("-SWAP"):
        market_type = FuturesMarketType.PERPETUAL
    elif xperp or re.fullmatch(r"[A-Z0-9]+-[A-Z0-9]+-\d{6}", native):
        market_type = FuturesMarketType.FUTURES
    else:
        raise ValueError("future_native_contract_identity_unknown")
    if ":" in instrument_id:
        if not validate_instrument_id_format_v1(instrument_id):
            raise ValueError("future_canonical_identity_invalid")
        _, contract, base, quote, _settlement, identity = instrument_id.split(":")
        if contract not in {"linear_perpetual", "linear_dated_future"}:
            raise ValueError("future_contract_type_unsupported")
        expected = (
            FuturesMarketType.PERPETUAL
            if contract == "linear_perpetual"
            else FuturesMarketType.FUTURES
        )
        if expected is not market_type:
            raise ValueError("future_contract_type_identity_mismatch")
        expected_prefix = f"{base}-{quote}_UM_XPERP-" if xperp else f"{base}-{quote}-"
        if not native.startswith(expected_prefix):
            raise ValueError("future_native_quote_identity_mismatch")
        if market_type is FuturesMarketType.PERPETUAL:
            if identity not in {"perp", native.lower()}:
                raise ValueError("future_native_contract_identity_mismatch")
        elif identity not in {native.lower(), f"20{native.rsplit('-', 1)[1]}"}:
            raise ValueError("future_expiry_identity_mismatch")
    return market_type
