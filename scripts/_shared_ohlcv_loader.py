# -*- coding: utf-8 -*-
"""
Gemeinsamer Dummy-OHLCV-Loader für Forward-/Paper-Skripte (J1).

Gleicher DataFrame-Vertrag für ``generate_forward_signals``, ``evaluate_forward_signals``,
``run_portfolio_backtest_v2`` (Slice 1–3: alle drei Skripte nutzen diesen Loader).

- ``DatetimeIndex`` (1h, **UTC**), Spalten open/high/low/close/volume (vgl. ``src.data.REQUIRED_OHLCV_COLUMNS``).
- OHLC-Nachkorrektur zentral: ``high = max(open, close, high)``, ``low = min(open, close, low)``.
- Vor Rückgabe: ``validate_ohlcv(..., strict=True, require_tz=True)`` (Peak_Trade-Datenvertrag).
- Read-only: keine Orders, keine API-Keys, kein C1-Bezug; synthetische Daten.

TODO(J1): Optional echte Marktdaten (Kraken/CCXT).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.data.contracts import validate_ohlcv


def load_dummy_ohlcv(symbol: str, n_bars: int = 200) -> pd.DataFrame:
    """
    Erzeugt Dummy-OHLCV für ein Symbol (symbol-spezifischer Seed).

    Args:
        symbol: Trading-Pair (z.B. "BTC/EUR")
        n_bars: Anzahl 1h-Bars

    Returns:
        DataFrame mit OHLCV-Spalten und DatetimeIndex (UTC, vertragstreu).
    """
    seed = hash(symbol) % (2**32)
    np.random.seed(seed)

    start = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=n_bars)
    dates = pd.date_range(start=start, periods=n_bars, freq="1h", tz="UTC")

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

    # Strikt positiver OHLC (seltener Randfall: Random-Walk unter 0)
    floor = 1e-9
    for col in ("open", "high", "low", "close"):
        df[col] = df[col].clip(lower=floor)
    df["high"] = df[["open", "close", "high"]].max(axis=1)
    df["low"] = df[["open", "close", "low"]].min(axis=1)

    validate_ohlcv(df, strict=True, require_tz=True)
    return df
