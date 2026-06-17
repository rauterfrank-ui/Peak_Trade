"""Dedicated contract tests for canonical market instrument eligibility gate (v0)."""

from __future__ import annotations

import inspect
from types import ModuleType

import pytest

from src.webui import market_instrument_eligibility_v0 as eligibility_module
from src.webui.market_instrument_eligibility_v0 import (
    BITCOIN_BASE_ALIASES,
    BITCOIN_INSTRUMENT_IDS,
    BITCOIN_LITERAL_SYMBOLS,
    CANONICAL_EXCLUSION_OWNER,
    extract_base_currency,
    is_bitcoin_underlying,
    is_eligible_market_dashboard_instrument,
)

_FORBIDDEN_PUBLIC_NAMES = frozenset(
    {
        "order",
        "orders",
        "order_id",
        "create_order",
        "submit_order",
        "execute",
        "execution",
        "execution_authorized",
        "live_authorized",
        "ready_for_operator_arming",
        "armed",
        "enabled",
        "credentials",
        "credential",
        "api_key",
        "api_secret",
        "private_key",
        "authority_lift",
        "promotion",
        "approve",
        "approved",
        "side_recommendation",
        "trade_recommendation",
    }
)

_NON_BITCOIN_FUTURES_POSITIVE: tuple[tuple[str, dict[str, str | None]], ...] = (
    ("ETHUSDT", {}),
    ("SOLUSDT", {}),
    ("PF_ETHUSD", {"instrument_id": "PF_ETHUSD"}),
    ("PI_SOLUSD", {"instrument_id": "PI_SOLUSD"}),
)

_BITCOIN_EXCLUSION_SYMBOLS: tuple[str, ...] = (
    "BTCUSDT",
    "XBTUSD",
    "PF_XBTUSD",
    "PI_XBTUSD",
    "BTC/EUR",
)


def test_canonical_exclusion_owner_constant() -> None:
    assert CANONICAL_EXCLUSION_OWNER == "src/webui/market_instrument_eligibility_v0.py"


def test_public_entrypoints_return_expected_types() -> None:
    assert is_bitcoin_underlying("ETHUSDT") is False
    assert is_eligible_market_dashboard_instrument("ETHUSDT") is True
    assert extract_base_currency("ETHUSDT") == "ETH"
    assert extract_base_currency("") is None


def test_eligibility_public_api_has_no_market_type_parameter() -> None:
    for fn in (
        extract_base_currency,
        is_bitcoin_underlying,
        is_eligible_market_dashboard_instrument,
    ):
        params = set(inspect.signature(fn).parameters)
        assert "market_type" not in params
        assert "spot" not in params
        assert "synthetic" not in params


@pytest.mark.parametrize(("symbol", "kwargs"), _NON_BITCOIN_FUTURES_POSITIVE)
def test_non_bitcoin_futures_symbols_are_eligible(
    symbol: str, kwargs: dict[str, str | None]
) -> None:
    assert is_bitcoin_underlying(symbol, **kwargs) is False
    assert is_eligible_market_dashboard_instrument(symbol, **kwargs) is True


@pytest.mark.parametrize("symbol", _BITCOIN_EXCLUSION_SYMBOLS)
def test_bitcoin_underlying_symbols_are_ineligible(symbol: str) -> None:
    assert is_bitcoin_underlying(symbol) is True
    assert is_eligible_market_dashboard_instrument(symbol) is False


@pytest.mark.parametrize(
    ("symbol", "base_currency", "instrument_id", "expected_base"),
    [
        ("ETHUSDT", None, None, "ETH"),
        ("SOLUSDT", None, None, "SOL"),
        ("ETH/EUR", None, None, "ETH"),
        ("PF_ETHUSD", None, "PF_ETHUSD", "ETH"),
        ("", "ADA", None, "ADA"),
    ],
)
def test_extract_base_currency_non_bitcoin_futures(
    symbol: str,
    base_currency: str | None,
    instrument_id: str | None,
    expected_base: str,
) -> None:
    assert (
        extract_base_currency(symbol, base_currency=base_currency, instrument_id=instrument_id)
        == expected_base
    )


@pytest.mark.parametrize(
    "symbol,base_currency,instrument_id",
    [
        ("", None, None),
        ("   ", None, None),
        ("", None, ""),
        ("", "", ""),
    ],
)
def test_empty_or_blank_inputs_fail_closed(
    symbol: str,
    base_currency: str | None,
    instrument_id: str | None,
) -> None:
    assert (
        is_eligible_market_dashboard_instrument(
            symbol,
            base_currency=base_currency,
            instrument_id=instrument_id,
        )
        is False
    )


def test_batch_eligibility_preserves_input_order() -> None:
    symbols = ["ETHUSDT", "SOLUSDT", "ADAUSDT"]
    before = list(symbols)
    results = [is_eligible_market_dashboard_instrument(item) for item in symbols]
    assert results == [True, True, True]
    assert symbols == before


def test_eligibility_decisions_are_deterministic_for_identical_input() -> None:
    cases = [
        ("ETHUSDT", {}),
        ("PF_ETHUSD", {"instrument_id": "PF_ETHUSD"}),
        ("BTCUSDT", {}),
    ]
    first = [
        (
            is_bitcoin_underlying(symbol, **kwargs),
            is_eligible_market_dashboard_instrument(symbol, **kwargs),
            extract_base_currency(symbol, **kwargs),
        )
        for symbol, kwargs in cases
    ]
    second = [
        (
            is_bitcoin_underlying(symbol, **kwargs),
            is_eligible_market_dashboard_instrument(symbol, **kwargs),
            extract_base_currency(symbol, **kwargs),
        )
        for symbol, kwargs in cases
    ]
    assert first == second


def test_eligibility_functions_do_not_mutate_symbol_input() -> None:
    symbol = "ETHUSDT"
    before = symbol
    is_bitcoin_underlying(symbol)
    is_eligible_market_dashboard_instrument(symbol)
    extract_base_currency(symbol)
    assert symbol == before


def test_only_non_bitcoin_symbols_can_be_eligible() -> None:
    for symbol in _BITCOIN_EXCLUSION_SYMBOLS:
        assert is_eligible_market_dashboard_instrument(symbol) is False
    for symbol, kwargs in _NON_BITCOIN_FUTURES_POSITIVE:
        assert is_eligible_market_dashboard_instrument(symbol, **kwargs) is True


def test_bitcoin_alias_sets_are_stable_canonical_constants() -> None:
    assert BITCOIN_BASE_ALIASES == frozenset({"BTC", "XBT"})
    assert "PF_XBTUSD" in BITCOIN_INSTRUMENT_IDS
    assert "BTCUSDT" in BITCOIN_LITERAL_SYMBOLS


def test_eligibility_module_has_no_forbidden_execution_or_authority_surface() -> None:
    public_names = {
        name
        for name, value in inspect.getmembers(eligibility_module)
        if not name.startswith("_") and not inspect.ismodule(value)
    }
    assert public_names.isdisjoint(_FORBIDDEN_PUBLIC_NAMES)

    for fn in (
        extract_base_currency,
        is_bitcoin_underlying,
        is_eligible_market_dashboard_instrument,
    ):
        assert inspect.isfunction(fn)
        assert fn.__module__ == eligibility_module.__name__


def test_eligibility_module_exports_no_nested_authority_modules() -> None:
    for _name, value in inspect.getmembers(eligibility_module):
        if isinstance(value, ModuleType):
            pytest.fail("eligibility module must not expose nested runtime modules")
