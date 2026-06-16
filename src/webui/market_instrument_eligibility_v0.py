"""Canonical instrument eligibility / exclusion for read-only market dashboard (SSR-only)."""

from __future__ import annotations

CANONICAL_EXCLUSION_OWNER = "src/webui/market_instrument_eligibility_v0.py"

BITCOIN_BASE_ALIASES: frozenset[str] = frozenset({"BTC", "XBT"})

BITCOIN_INSTRUMENT_IDS: frozenset[str] = frozenset(
    {
        "PF_XBTUSD",
        "PI_XBTUSD",
        "PF_XBTUSDT",
        "PI_XBTUSDT",
    }
)

BITCOIN_LITERAL_SYMBOLS: frozenset[str] = frozenset(
    {
        "BTC",
        "XBT",
        "BTCUSDT",
        "BTCUSD",
        "BTCEUR",
        "BTC/EUR",
        "BTC/USD",
        "BTC-USD",
        "BTC-USDT",
        "XBTUSD",
        "XBTUSDT",
        "XBT/EUR",
        "XBT/USD",
        "XBT-USD",
        "PF_XBTUSD",
        "PI_XBTUSD",
    }
)

_QUOTE_SUFFIXES: tuple[str, ...] = ("USDT", "USD", "EUR")


def _normalize_token(raw: str) -> str:
    return raw.strip().upper().replace(" ", "")


def extract_base_currency(
    symbol: str,
    *,
    base_currency: str | None = None,
    instrument_id: str | None = None,
) -> str | None:
    """Resolve a display/base currency token for eligibility checks (dashboard scope only)."""
    if base_currency is not None and str(base_currency).strip():
        return _normalize_token(str(base_currency))

    if instrument_id is not None and str(instrument_id).strip():
        inst = _normalize_token(str(instrument_id))
        if inst in BITCOIN_INSTRUMENT_IDS:
            return "XBT"
        if inst.startswith(("PF_", "PI_")) and len(inst) > 3:
            body = inst[3:]
            for quote in _QUOTE_SUFFIXES:
                if body.endswith(quote) and len(body) > len(quote):
                    return body[: -len(quote)]

    token = _normalize_token(symbol)
    if not token:
        return None
    if token in BITCOIN_LITERAL_SYMBOLS:
        if token in BITCOIN_BASE_ALIASES:
            return token
        if token.startswith(("PF_", "PI_")):
            body = token[3:]
            for quote in _QUOTE_SUFFIXES:
                if body.endswith(quote) and len(body) > len(quote):
                    return body[: -len(quote)]
    if "/" in token:
        return token.split("/", 1)[0]
    for quote in _QUOTE_SUFFIXES:
        if token.endswith(quote) and len(token) > len(quote):
            return token[: -len(quote)]
    return token


def is_bitcoin_underlying(
    symbol: str,
    *,
    base_currency: str | None = None,
    instrument_id: str | None = None,
) -> bool:
    """True when the instrument resolves to Bitcoin (BTC/XBT), including exchange aliases."""
    token = _normalize_token(symbol)
    if token in BITCOIN_LITERAL_SYMBOLS or token in BITCOIN_INSTRUMENT_IDS:
        return True
    base = extract_base_currency(
        symbol,
        base_currency=base_currency,
        instrument_id=instrument_id,
    )
    return base in BITCOIN_BASE_ALIASES if base else False


def is_eligible_market_dashboard_instrument(
    symbol: str,
    *,
    base_currency: str | None = None,
    instrument_id: str | None = None,
) -> bool:
    """Dashboard universe eligibility — Bitcoin instruments are always excluded."""
    if not str(symbol or "").strip() and not instrument_id and not base_currency:
        return False
    return not is_bitcoin_underlying(
        symbol,
        base_currency=base_currency,
        instrument_id=instrument_id,
    )
