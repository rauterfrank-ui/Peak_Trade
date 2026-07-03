"""Research-only instrument ID canonicalization for PIT futures universe manifests.

Non-authorizing: no trading, selection, risk, sizing, runtime, or execution authority.
No network access, no venue metadata queries, no heuristic runtime symbol resolution.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

PACKAGE_MARKER = "INSTRUMENT_ID_CANONICALIZATION_V1=true"
INSTRUMENT_ID_CANONICALIZATION_VERSION = "instrument_id_canonicalization.v1"

# Alias for manifest root field compatibility.
INSTRUMENT_ID_CANONICALIZATION_VERSION_TOKEN = INSTRUMENT_ID_CANONICALIZATION_VERSION

_FORBIDDEN_BASE_ASSETS = frozenset({"BTC", "XBT", "WBTC", "TBTC", "RBTC", "BTCB", "BITCOIN"})
_FORBIDDEN_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "wbtc", "tbtc", "rbtc", "btcb"})
_FUTURES_CONTRACT_TYPES = frozenset(
    {
        "linear_perpetual",
        "inverse_perpetual",
        "linear_dated_future",
        "inverse_dated_future",
    }
)
_PERPETUAL_CONTRACT_TYPES = frozenset({"linear_perpetual", "inverse_perpetual"})
_DATED_CONTRACT_TYPES = frozenset({"linear_dated_future", "inverse_dated_future"})
_VENUE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_ASSET_PATTERN = re.compile(r"^[A-Z0-9]{1,16}$")
_CONTRACT_EXPIRY_PATTERN = re.compile(r"^\d{8}$")
_NATIVE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_\-.]{0,127}$")


class InstrumentIdCanonicalizationErrorCode(str, Enum):
    INVALID_VENUE_ID = "INVALID_VENUE_ID"
    INVALID_MARKET_TYPE = "INVALID_MARKET_TYPE"
    NON_FUTURES_MARKET = "NON_FUTURES_MARKET"
    SPOT_MARKET = "SPOT_MARKET"
    SYNTHETIC_SPOT_MARKET = "SYNTHETIC_SPOT_MARKET"
    INVALID_CONTRACT_TYPE = "INVALID_CONTRACT_TYPE"
    INVALID_BASE_ASSET = "INVALID_BASE_ASSET"
    BITCOIN_DIRECTION_DISALLOWED = "BITCOIN_DIRECTION_DISALLOWED"
    INVALID_QUOTE_ASSET = "INVALID_QUOTE_ASSET"
    INVALID_SETTLEMENT_ASSET = "INVALID_SETTLEMENT_ASSET"
    MISSING_STABLE_INSTRUMENT_IDENTIFIER = "MISSING_STABLE_INSTRUMENT_IDENTIFIER"
    AMBIGUOUS_INSTRUMENT_ID = "AMBIGUOUS_INSTRUMENT_ID"
    UNSUPPORTED_CANONICALIZATION_VERSION = "UNSUPPORTED_CANONICALIZATION_VERSION"


@dataclass(frozen=True)
class InstrumentIdCanonicalizationInputV1:
    venue_id: str
    market_type: str
    contract_type: str
    base_asset: str
    quote_asset: str
    settlement_asset: str
    venue_symbol: str | None = None
    native_instrument_id: str | None = None
    contract_expiry: str | None = None
    canonicalization_version: str = INSTRUMENT_ID_CANONICALIZATION_VERSION


@dataclass(frozen=True)
class InstrumentIdCanonicalizationResultV1:
    success: bool
    instrument_id: str | None
    error_codes: tuple[str, ...]


def _bounded_token_match(text: str, token: str) -> bool:
    pattern = rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])"
    return re.search(pattern, text.lower()) is not None


def _scan_forbidden_substrings(*values: str | None) -> bool:
    for value in values:
        if not value:
            continue
        lowered = value.lower()
        for token in _FORBIDDEN_SUBSTRINGS:
            if _bounded_token_match(lowered, token):
                return True
    return False


def _normalize_asset(asset: str) -> str | None:
    if not isinstance(asset, str) or not asset.strip():
        return None
    normalized = asset.strip().upper()
    if not _ASSET_PATTERN.fullmatch(normalized):
        return None
    return normalized


def _resolve_contract_identity(
    *,
    contract_type: str,
    native_instrument_id: str | None,
    contract_expiry: str | None,
    venue_symbol: str | None,
) -> tuple[str | None, str | None]:
    if native_instrument_id is not None:
        native = native_instrument_id.strip()
        if not native or not _NATIVE_ID_PATTERN.fullmatch(native):
            return None, InstrumentIdCanonicalizationErrorCode.AMBIGUOUS_INSTRUMENT_ID.value
        return native, None

    if contract_type in _PERPETUAL_CONTRACT_TYPES:
        if venue_symbol is None or not venue_symbol.strip():
            return (
                None,
                InstrumentIdCanonicalizationErrorCode.MISSING_STABLE_INSTRUMENT_IDENTIFIER.value,
            )
        return "perp", None

    if contract_type in _DATED_CONTRACT_TYPES:
        if contract_expiry is not None:
            expiry = contract_expiry.strip()
            if not _CONTRACT_EXPIRY_PATTERN.fullmatch(expiry):
                return None, InstrumentIdCanonicalizationErrorCode.AMBIGUOUS_INSTRUMENT_ID.value
            return expiry, None
        return (
            None,
            InstrumentIdCanonicalizationErrorCode.MISSING_STABLE_INSTRUMENT_IDENTIFIER.value,
        )

    return None, InstrumentIdCanonicalizationErrorCode.INVALID_CONTRACT_TYPE.value


def canonicalize_instrument_id_v1(
    payload: InstrumentIdCanonicalizationInputV1 | Mapping[str, Any],
) -> InstrumentIdCanonicalizationResultV1:
    """Deterministically canonicalize a futures instrument identity."""
    if isinstance(payload, Mapping):
        data = dict(payload)
        inp = InstrumentIdCanonicalizationInputV1(
            venue_id=str(data.get("venue_id", "")),
            market_type=str(data.get("market_type", "")),
            contract_type=str(data.get("contract_type", "")),
            base_asset=str(data.get("base_asset", "")),
            quote_asset=str(data.get("quote_asset", "")),
            settlement_asset=str(data.get("settlement_asset", "")),
            venue_symbol=data.get("venue_symbol"),
            native_instrument_id=data.get("native_instrument_id"),
            contract_expiry=data.get("contract_expiry"),
            canonicalization_version=str(
                data.get("canonicalization_version", INSTRUMENT_ID_CANONICALIZATION_VERSION)
            ),
        )
    else:
        inp = payload

    errors: list[str] = []

    if inp.canonicalization_version != INSTRUMENT_ID_CANONICALIZATION_VERSION:
        errors.append(
            InstrumentIdCanonicalizationErrorCode.UNSUPPORTED_CANONICALIZATION_VERSION.value
        )
        return InstrumentIdCanonicalizationResultV1(False, None, tuple(errors))

    venue_id = inp.venue_id.strip().lower()
    if not venue_id or not _VENUE_ID_PATTERN.fullmatch(venue_id):
        errors.append(InstrumentIdCanonicalizationErrorCode.INVALID_VENUE_ID.value)

    market_type = inp.market_type.strip().lower()
    if not market_type:
        errors.append(InstrumentIdCanonicalizationErrorCode.INVALID_MARKET_TYPE.value)
    elif market_type == "spot":
        errors.append(InstrumentIdCanonicalizationErrorCode.SPOT_MARKET.value)
    elif market_type in {"synthetic_spot", "synthetic-spot"}:
        errors.append(InstrumentIdCanonicalizationErrorCode.SYNTHETIC_SPOT_MARKET.value)
    elif market_type not in {"futures", "futures_panel", "future", "perpetual"}:
        errors.append(InstrumentIdCanonicalizationErrorCode.NON_FUTURES_MARKET.value)

    contract_type = inp.contract_type.strip().lower()
    if contract_type not in _FUTURES_CONTRACT_TYPES:
        errors.append(InstrumentIdCanonicalizationErrorCode.INVALID_CONTRACT_TYPE.value)

    base_asset = _normalize_asset(inp.base_asset)
    if base_asset is None:
        errors.append(InstrumentIdCanonicalizationErrorCode.INVALID_BASE_ASSET.value)
    elif base_asset in _FORBIDDEN_BASE_ASSETS:
        errors.append(InstrumentIdCanonicalizationErrorCode.BITCOIN_DIRECTION_DISALLOWED.value)

    quote_asset = _normalize_asset(inp.quote_asset)
    if quote_asset is None:
        errors.append(InstrumentIdCanonicalizationErrorCode.INVALID_QUOTE_ASSET.value)

    settlement_asset = _normalize_asset(inp.settlement_asset)
    if settlement_asset is None:
        errors.append(InstrumentIdCanonicalizationErrorCode.INVALID_SETTLEMENT_ASSET.value)

    if _scan_forbidden_substrings(
        inp.venue_symbol,
        inp.native_instrument_id,
        base_asset,
    ):
        if InstrumentIdCanonicalizationErrorCode.BITCOIN_DIRECTION_DISALLOWED.value not in errors:
            errors.append(InstrumentIdCanonicalizationErrorCode.BITCOIN_DIRECTION_DISALLOWED.value)

    if errors:
        return InstrumentIdCanonicalizationResultV1(False, None, tuple(sorted(set(errors))))

    contract_identity, identity_error = _resolve_contract_identity(
        contract_type=contract_type,
        native_instrument_id=inp.native_instrument_id,
        contract_expiry=inp.contract_expiry,
        venue_symbol=inp.venue_symbol,
    )
    if identity_error is not None:
        return InstrumentIdCanonicalizationResultV1(False, None, (identity_error,))

    assert contract_identity is not None
    assert base_asset is not None
    assert quote_asset is not None
    assert settlement_asset is not None

    instrument_id = (
        f"{venue_id}:{contract_type}:{base_asset}:{quote_asset}:"
        f"{settlement_asset}:{contract_identity}"
    )
    return InstrumentIdCanonicalizationResultV1(True, instrument_id, ())


def validate_instrument_id_format_v1(instrument_id: str) -> bool:
    """Structural check for canonical instrument_id tokens."""
    parts = instrument_id.split(":")
    if len(parts) != 6:
        return False
    venue_id, contract_type, base_asset, quote_asset, settlement_asset, contract_identity = parts
    if not _VENUE_ID_PATTERN.fullmatch(venue_id):
        return False
    if contract_type not in _FUTURES_CONTRACT_TYPES:
        return False
    for asset in (base_asset, quote_asset, settlement_asset):
        if not _ASSET_PATTERN.fullmatch(asset):
            return False
    if base_asset in _FORBIDDEN_BASE_ASSETS:
        return False
    if _scan_forbidden_substrings(instrument_id):
        return False
    if contract_type in _PERPETUAL_CONTRACT_TYPES and contract_identity != "perp":
        if not _NATIVE_ID_PATTERN.fullmatch(contract_identity):
            return False
    elif contract_type in _DATED_CONTRACT_TYPES:
        if not (
            _CONTRACT_EXPIRY_PATTERN.fullmatch(contract_identity)
            or _NATIVE_ID_PATTERN.fullmatch(contract_identity)
        ):
            return False
    return True
