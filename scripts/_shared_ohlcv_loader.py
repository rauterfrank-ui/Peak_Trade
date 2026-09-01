# -*- coding: utf-8 -*-
"""
Gemeinsamer OHLCV-Loader für Forward-/Paper-Skripte (J1).

Gleicher DataFrame-Vertrag für ``generate_forward_signals``, ``evaluate_forward_signals``,
``run_portfolio_backtest_v2``.

- ``DatetimeIndex`` (1h, **UTC**), Spalten open/high/low/close/volume (vgl. ``src.data.REQUIRED_OHLCV_COLUMNS``).
- Dummy: OHLC-Nachkorrektur zentral; vor Rückgabe ``validate_ohlcv(..., strict=True, require_tz=True)``.
- CSV/Fixture: ``source="csv"`` (Alias ``fixture``) — lokale Datei, kein Netzwerk; Pfad über ``ohlcv_csv_path`` (CLI: ``--ohlcv-csv``).
- Read-only: keine Orders, kein C1-Bezug.

``load_ohlcv_with_meta`` liefert dasselbe wie ``load_ohlcv`` plus ein Observability-Dict.
CLI-Defaults: ``scripts/_shared_forward_args.py``.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.data import REQUIRED_OHLCV_COLUMNS
from src.data.contracts import validate_ohlcv

# Dummy and local CSV only. Noncanonical venue sources are rejected.
OHLCV_SOURCE_DUMMY = "dummy"
OHLCV_SOURCE_CSV = "csv"
OHLCV_SOURCES = (OHLCV_SOURCE_DUMMY, OHLCV_SOURCE_CSV)


def _normalize_ohlcv_source(source: str) -> str:
    """
    Trim + lower case; ``dummy`` / ``csv`` (Alias ``fixture``).
    """
    if not isinstance(source, str):
        raise TypeError(f"OHLCV-Quelle muss str sein, nicht {type(source).__name__}.")
    key = source.strip().lower()
    if key == "fixture":
        key = OHLCV_SOURCE_CSV
    if key == "kraken":
        from src.exchange.operative_venue_boundary_v1 import reject_noncanonical_operative_surface

        reject_noncanonical_operative_surface(surface="load_ohlcv.source")
    if key not in OHLCV_SOURCES:
        raise ValueError(
            f"Unbekannte OHLCV-Quelle {source!r}; erlaubt: {list(OHLCV_SOURCES)} "
            "(Groß-/Kleinschreibung egal; fixture → csv)."
        )
    return key


def normalize_ohlcv_source(source: str) -> str:
    """Öffentlicher Alias für gemeinsame CLI (``argparse`` ``type=``); gleiche Semantik wie intern."""
    return _normalize_ohlcv_source(source)


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
        raise ValueError(f"Timeframe {timeframe!r} nicht unterstützt; erlaubt: {sorted(m.keys())}")
    return m[timeframe]


def _warn_csv_shortfall_if_needed(
    path: Path,
    n_bars_requested: int,
    bars_loaded: int,
) -> None:
    if bars_loaded >= n_bars_requested:
        return
    msg = (
        f"OHLCV-CSV {path}: nur {bars_loaded} von {n_bars_requested} angeforderten Bars "
        "(Datei zu kurz)."
    )
    warnings.warn(msg, UserWarning, stacklevel=2)


def _safe_symbol_token(symbol: str) -> str:
    return symbol.replace("/", "_").replace("\\", "_").replace(" ", "_")


def resolve_ohlcv_csv_path(path_arg: str | Path, symbol: str) -> Path:
    """
    Löst ``--ohlcv-csv`` auf. Optional ``{symbol}`` im Pfad (z. B. ``rows/BTC_EUR.csv``).
    """
    tpl = str(path_arg)
    if "{symbol}" in tpl:
        p = Path(tpl.format(symbol=_safe_symbol_token(symbol)))
    else:
        p = Path(tpl)
    return p.expanduser().resolve(strict=False)


def _column_lookup(raw: pd.DataFrame) -> dict[str, str]:
    return {str(c).strip().lower(): str(c) for c in raw.columns}


def _parse_ohlcv_csv(path: Path) -> pd.DataFrame:
    """
    Liest eine OHLCV-CSV (lokal), fail-closed: Spalten, Typen, monoton UTC-Index, keine Duplikate.

    Erwartet Spalten ``open``/``high``/``low``/``close``/``volume`` (Groß/Klein egal)
    und genau eine Zeit-Spalte: ``timestamp``, ``datetime``, ``date``, oder ``time``
    (numerisch → Unix-Sekunden UTC). Alternativ: erste Spalte ist parsierbares Datum,
    wenn keine der Zeit-Spalten genannt ist.
    """
    try:
        raw = pd.read_csv(path)
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise ValueError(f"OHLCV-CSV nicht lesbar ({path}): {exc}") from exc

    if raw.empty:
        raise ValueError(f"OHLCV-CSV leer: {path}")

    lookup = _column_lookup(raw)
    missing_ohlc = [c for c in REQUIRED_OHLCV_COLUMNS if c not in lookup]
    if missing_ohlc:
        raise ValueError(
            f"OHLCV-CSV {path}: fehlende Spalten {missing_ohlc}; vorhanden: {sorted(lookup.keys())}"
        )

    ts_col: str | None = None
    for key in ("timestamp", "datetime", "date"):
        if key in lookup:
            ts_col = lookup[key]
            break

    index: pd.DatetimeIndex | None = None
    drop_cols: set[str] = set()

    if ts_col is not None:
        series = raw[ts_col]
        if pd.api.types.is_numeric_dtype(series):
            index = pd.to_datetime(series, unit="s", utc=True)
        else:
            index = pd.to_datetime(series, utc=True)
        drop_cols.add(ts_col)
    else:
        if "time" in lookup:
            tcol = lookup["time"]
            series = raw[tcol]
            if pd.api.types.is_numeric_dtype(series):
                index = pd.to_datetime(series, unit="s", utc=True)
            else:
                index = pd.to_datetime(series, utc=True)
            drop_cols.add(tcol)
        else:
            first = raw.columns[0]
            try:
                index = pd.to_datetime(raw.iloc[:, 0], utc=True)
            except Exception as exc:
                raise ValueError(
                    f"OHLCV-CSV {path}: keine Zeit-Spalte (timestamp/datetime/date/time) "
                    f"und erste Spalte nicht als Datum parsierbar."
                ) from exc
            drop_cols.add(str(first))

    if index is None or len(index) != len(raw):
        raise ValueError(f"OHLCV-CSV {path}: Zeit-Index konnte nicht gebildet werden.")

    ohlcv = pd.DataFrame(index=index)
    for c in REQUIRED_OHLCV_COLUMNS:
        # Werte positional übernehmen (CSV-Zeilen == Index-Länge); kein Label-Align mit Default-Index.
        vals = pd.to_numeric(raw[lookup[c]], errors="coerce").to_numpy(dtype=np.float64, copy=True)
        ohlcv[c] = vals
    if ohlcv.index.duplicated().any():
        raise ValueError(f"OHLCV-CSV {path}: doppelte Zeitstempel.")
    if not ohlcv.index.is_monotonic_increasing:
        raise ValueError(f"OHLCV-CSV {path}: Zeitstempel sind nicht streng aufsteigend.")

    validate_ohlcv(ohlcv, strict=True, require_tz=True)
    return ohlcv


def load_csv_ohlcv(
    ohlcv_csv_path: str | Path,
    symbol: str,
    n_bars: int = 200,
) -> pd.DataFrame:
    """
    Lokale CSV-OHLCV (J1, NO-LIVE). Nutzt ``resolve_ohlcv_csv_path``; nimmt die letzten ``n_bars`` Zeilen.
    """
    if n_bars < 1:
        raise ValueError("n_bars muss >= 1 sein (CSV-OHLCV).")

    resolved = resolve_ohlcv_csv_path(ohlcv_csv_path, symbol)
    if not resolved.is_file():
        raise FileNotFoundError(f"OHLCV-CSV nicht gefunden: {resolved}")

    df = _parse_ohlcv_csv(resolved)
    if len(df) > n_bars:
        df = df.iloc[-n_bars:].copy()
    validate_ohlcv(df, strict=True, require_tz=True)
    _warn_csv_shortfall_if_needed(resolved, n_bars, len(df))
    return df


def load_dummy_ohlcv(symbol: str, n_bars: int = 200) -> pd.DataFrame:
    """
    Erzeugt Dummy-OHLCV für ein Symbol (symbol-spezifischer Seed).

    Args:
        symbol: Trading-Pair (z.B. "BTC/EUR")
        n_bars: Anzahl 1h-Bars

    Returns:
        DataFrame mit OHLCV-Spalten und DatetimeIndex (UTC, vertragstreu).
    """
    if n_bars < 1:
        raise ValueError("n_bars muss >= 1 sein (Dummy-OHLCV).")

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


def load_ohlcv(
    symbol: str,
    n_bars: int = 200,
    *,
    source: str = OHLCV_SOURCE_DUMMY,
    timeframe: str = "1h",
    use_cache: bool = True,
    ohlcv_csv_path: str | Path | None = None,
) -> pd.DataFrame:
    """
    Einheitlicher Einstieg: Dummy (Default) oder lokale CSV.

    Args:
        symbol: Trading-Paar (z.B. ``BTC/EUR``).
        n_bars: Gewünschte Bar-Anzahl.
        source: ``dummy`` | ``csv`` (Alias ``fixture``; Groß-/Kleinschreibung wird normalisiert).
        timeframe: Meta/CLI-Konsistenz (Dummy bleibt synthetisch).
        use_cache: Ungenutzt für Dummy/CSV.
        ohlcv_csv_path: Pfad zur CSV bei ``source=csv`` (Pfad kann ``{symbol}`` enthalten).
    """
    src = _normalize_ohlcv_source(source)
    if src == OHLCV_SOURCE_DUMMY:
        return load_dummy_ohlcv(symbol, n_bars=n_bars)
    if src == OHLCV_SOURCE_CSV:
        if not ohlcv_csv_path:
            raise ValueError("OHLCV-Quelle csv erfordert ohlcv_csv_path (CLI: --ohlcv-csv).")
        return load_csv_ohlcv(ohlcv_csv_path, symbol, n_bars=n_bars)
    raise AssertionError("unreachable")


def load_ohlcv_with_meta(
    symbol: str,
    n_bars: int = 200,
    *,
    source: str = OHLCV_SOURCE_DUMMY,
    timeframe: str = "1h",
    use_cache: bool = True,
    ohlcv_csv_path: str | Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Wie ``load_ohlcv``, zusätzlich deterministisches Observability-Dict:
    symbol, Quelle, Timeframe, angeforderte/effektive Bar-Anzahl,
    bei CSV: ``ohlcv_csv_resolved``, ``csv_bars_shortfall``.
    """
    src = _normalize_ohlcv_source(source)
    if src == OHLCV_SOURCE_DUMMY:
        df = load_dummy_ohlcv(symbol, n_bars=n_bars)
        meta: dict[str, Any] = {
            "symbol": symbol,
            "ohlcv_source": OHLCV_SOURCE_DUMMY,
            "timeframe": timeframe,
            "n_bars_requested": n_bars,
            "bars_loaded": int(len(df)),
            "pagination_used": None,
            "bars_shortfall": None,
            "ohlcv_csv_resolved": None,
            "csv_bars_shortfall": None,
        }
        return df, meta
    if src == OHLCV_SOURCE_CSV:
        if not ohlcv_csv_path:
            raise ValueError("OHLCV-Quelle csv erfordert ohlcv_csv_path (CLI: --ohlcv-csv).")
        resolved = resolve_ohlcv_csv_path(ohlcv_csv_path, symbol)
        df = load_csv_ohlcv(ohlcv_csv_path, symbol, n_bars=n_bars)
        loaded = int(len(df))
        shortfall = loaded < n_bars
        meta = {
            "symbol": symbol,
            "ohlcv_source": OHLCV_SOURCE_CSV,
            "timeframe": timeframe,
            "n_bars_requested": n_bars,
            "bars_loaded": loaded,
            "pagination_used": None,
            "bars_shortfall": None,
            "ohlcv_csv_resolved": str(resolved),
            "csv_bars_shortfall": shortfall,
        }
        return df, meta
    raise AssertionError("unreachable")
