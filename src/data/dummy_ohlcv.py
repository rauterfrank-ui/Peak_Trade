# -*- coding: utf-8 -*-
"""
Reproduzierbare Dummy-OHLCV für Forward-/Paper-Skripte (J1).

J1 Slice 1 (Branch ``feat/j1-shared-ohlcv-loader-slice1``) — fester Scope:

1. Nur ``scripts/generate_forward_signals.py`` wird auf diesen gemeinsamen Loader
   umgestellt; ``evaluate_forward_signals`` / ``run_portfolio_backtest_v2`` bleiben
   in Slice 1 unverändert (Folge-Slices separat).

2. DataFrame-Vertrag: ``DatetimeIndex`` (1h) und Spalten
   ``open``, ``high``, ``low``, ``close``, ``volume`` (analog ``REQUIRED_OHLCV_COLUMNS``).

3. OHLC-Konsistenz wie bisher: nach der Rohgenerierung
   ``high = max(open, close, high)``, ``low = min(open, close, low)``.

4. Read-only Datenpfad: keine Orders, keine API-Keys, kein C1-Bezug; nur synthetische
   lokale Daten.

TODO(J1): Optional durch echte Marktdaten (Kraken/CCXT) ersetzen.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def load_dummy_ohlcv_bars(symbol: str, n_bars: int = 200) -> pd.DataFrame:
    """
    Erzeugt Dummy-OHLCV für ein Symbol (symbol-spezifischer Seed).

    Args:
        symbol: Trading-Pair (z.B. "BTC/EUR")
        n_bars: Anzahl 1h-Bars

    Returns:
        DataFrame mit REQUIRED_OHLCV-Spalten und DatetimeIndex.
    """
    seed = hash(symbol) % (2**32)
    np.random.seed(seed)

    start = datetime.now() - timedelta(hours=n_bars)
    dates = pd.date_range(start, periods=n_bars, freq="1h")

    if "BTC" in symbol:
        base_price = 50000
        volatility = 0.003
    elif "ETH" in symbol:
        base_price = 3000
        volatility = 0.004
    elif "LTC" in symbol:
        base_price = 100
        volatility = 0.005
    else:
        base_price = 1000
        volatility = 0.003

    trend = np.linspace(0, base_price * 0.06, n_bars)
    cycle = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * base_price * 0.04
    noise = np.random.randn(n_bars).cumsum() * base_price * volatility
    close_prices = base_price + trend + cycle + noise

    df = pd.DataFrame(
        {
            "open": close_prices * (1 + np.random.randn(n_bars) * volatility),
            "high": close_prices * (1 + abs(np.random.randn(n_bars)) * volatility * 1.5),
            "low": close_prices * (1 - abs(np.random.randn(n_bars)) * volatility * 1.5),
            "close": close_prices,
            "volume": np.random.randint(10, 100, n_bars),
        },
        index=dates,
    )

    df["high"] = df[["open", "close", "high"]].max(axis=1)
    df["low"] = df[["open", "close", "low"]].min(axis=1)

    return df
