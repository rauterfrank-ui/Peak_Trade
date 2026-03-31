# -*- coding: utf-8 -*-
"""
Gemeinsamer OHLCV-Loader für Forward-/Paper-Skripte (J1).

Gleicher DataFrame-Vertrag für ``generate_forward_signals``, ``evaluate_forward_signals``,
``run_portfolio_backtest_v2`` (Slice 1–3: Dummy; Slice 4: optional Kraken über ``load_ohlcv``).

- ``DatetimeIndex`` (1h, **UTC**), Spalten open/high/low/close/volume (vgl. ``src.data.REQUIRED_OHLCV_COLUMNS``).
- Dummy: OHLC-Nachkorrektur zentral; vor Rückgabe ``validate_ohlcv(..., strict=True, require_tz=True)``.
- Kraken: ``src.data.kraken.fetch_ohlcv_df`` (öffentliche OHLCV, kein Trading; Cache-Pfad via ConfigRegistry).
- Read-only: keine Orders, kein C1-Bezug.

J1 Slice 4: ``source="kraken"`` — bis zu 720 Bars pro **Request** (Kraken/ccxt-Limit), siehe ``KRAKEN_OHLCV_MAX_BARS``.

J1 Pagination: ``n_bars`` > 720 — wiederholte Abrufe (ältere Fenster über ``since_ms``); pro Paginations-Request ``use_cache=False`` (Cache-Datei in ``fetch_ohlcv_df`` ist pro Symbol/TF ein Voll-Snapshot).

CLI-Defaults für ``--n-bars``, ``--timeframe``, ``--ohlcv-source`` (Forward-/Portfolio-Skripte):
``scripts/_shared_forward_args.py`` — ``timeframe`` wirkt auf Kraken; Dummy bleibt 1h-synthetisch.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.data.contracts import validate_ohlcv

# Kraken Public-OHLCV: ccxt/Kraken begrenzt ``limit`` (hier konservativ wie ``fetch_ohlcv_df``).
KRAKEN_OHLCV_MAX_BARS = 720

OHLCV_SOURCE_DUMMY = "dummy"
OHLCV_SOURCE_KRAKEN = "kraken"
OHLCV_SOURCES = (OHLCV_SOURCE_DUMMY, OHLCV_SOURCE_KRAKEN)


def _timeframe_to_timedelta(timeframe: str) -> pd.Timedelta:
    """Pandas-Timedelta für bekannte Forward-CLI-Timeframes (siehe ``_shared_forward_args``)."""
    m = {
        "1m": pd.Timedelta(minutes=1),
        "5m": pd.Timedelta(minutes=5),
        "15m": pd.Timedelta(minutes=15),
        "1h": pd.Timedelta(hours=1),
        "4h": pd.Timedelta(hours=4),
        "1d": pd.Timedelta(days=1),
    }
    if timeframe not in m:
        raise ValueError(
            f"Timeframe {timeframe!r} für Kraken-Pagination nicht unterstützt; "
            f"erlaubt: {sorted(m.keys())}"
        )
    return m[timeframe]


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


def load_kraken_ohlcv(
    symbol: str,
    n_bars: int = 200,
    *,
    timeframe: str = "1h",
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Öffentliche Kraken-OHLCV über ``fetch_ohlcv_df`` (CCXT-Backend).

    Keine API-Keys für reine Kursabfragen nötig. Pro Request maximal
    ``KRAKEN_OHLCV_MAX_BARS`` Bars; bei ``n_bars`` darüber: Pagination vorwärts
    ab ``now - n_bars * bar_duration`` (``since_ms``), zusammenführen und
    ``tail(n_bars)``. Paginations-Requests nutzen ``use_cache=False``, weil der
    Parquet-Cache in ``fetch_ohlcv_df`` ein Voll-Snapshot ohne ``since``/``limit``
    ist.

    Cache/``data_dir``: wie ``src.data.kraken`` (ConfigRegistry / ``get_config()``)
    nur bei einzelnem Abruf ``n_bars <= KRAKEN_OHLCV_MAX_BARS``.
    """
    from src.data.kraken import fetch_ohlcv_df

    if n_bars < 1:
        raise ValueError("n_bars muss >= 1 sein.")

    if n_bars <= KRAKEN_OHLCV_MAX_BARS:
        limit = min(n_bars, KRAKEN_OHLCV_MAX_BARS)
        df = fetch_ohlcv_df(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            use_cache=use_cache,
        )
        if df.empty:
            raise ValueError(f"Kraken-OHLCV leer für {symbol!r} ({timeframe}, limit={limit}).")
        if len(df) > n_bars:
            df = df.iloc[-n_bars:].copy()
        validate_ohlcv(df, strict=True, require_tz=True)
        return df

    td = _timeframe_to_timedelta(timeframe)
    td_ms = int(td.total_seconds() * 1000)

    chunks: list[pd.DataFrame] = []
    since_ms: int | None = None
    max_loops = (n_bars // KRAKEN_OHLCV_MAX_BARS) + 5

    for _ in range(max_loops):
        if sum(len(c) for c in chunks) >= n_bars:
            break
        df = fetch_ohlcv_df(
            symbol=symbol,
            timeframe=timeframe,
            limit=KRAKEN_OHLCV_MAX_BARS,
            since_ms=since_ms,
            use_cache=False,
        )
        if df.empty:
            break
        chunks.insert(0, df)
        oldest_ms = int(df.index[0].timestamp() * 1000)
        since_ms = oldest_ms - KRAKEN_OHLCV_MAX_BARS * td_ms
        if since_ms < 0:
            since_ms = 0
        if len(df) < KRAKEN_OHLCV_MAX_BARS:
            break

    if not chunks:
        raise ValueError(f"Kraken-OHLCV leer für {symbol!r} ({timeframe}, Pagination).")

    out = pd.concat(chunks)
    out = out[~out.index.duplicated(keep="last")]
    out = out.sort_index()
    if len(out) > n_bars:
        out = out.iloc[-n_bars:].copy()
    validate_ohlcv(out, strict=True, require_tz=True)
    return out


def load_ohlcv(
    symbol: str,
    n_bars: int = 200,
    *,
    source: str = OHLCV_SOURCE_DUMMY,
    timeframe: str = "1h",
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Einheitlicher Einstieg: Dummy (Default) oder Kraken.

    Args:
        symbol: Trading-Paar (z.B. ``BTC/EUR``).
        n_bars: Gewünschte Bar-Anzahl (Kraken: mehrere Abrufe bei ``n_bars`` > ``KRAKEN_OHLCV_MAX_BARS``).
        source: ``dummy`` | ``kraken``.
        timeframe: Nur Kraken; Default ``1h`` (wie Forward-Pipeline).
        use_cache: Nur Kraken — Parquet-Cache in ``fetch_ohlcv_df``.
    """
    if source == OHLCV_SOURCE_DUMMY:
        return load_dummy_ohlcv(symbol, n_bars=n_bars)
    if source == OHLCV_SOURCE_KRAKEN:
        return load_kraken_ohlcv(symbol, n_bars=n_bars, timeframe=timeframe, use_cache=use_cache)
    raise ValueError(f"Unbekannte OHLCV-Quelle {source!r}; erlaubt: {list(OHLCV_SOURCES)}")
