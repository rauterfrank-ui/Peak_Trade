"""Load close-to-close returns from an OHLCV Parquet file (read-only, offline CLIs)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_close_returns_from_ohlcv_parquet(path: Path | str) -> pd.Series:
    """Build simple close-to-close return series from a Parquet OHLCV artifact.

    Expects column ``close``. Rows must carry a datetime index (`DatetimeIndex`) or a
    ``timestamp`` column. Index timezone is normalized to UTC when datetime-like.

    Raises:
        FileNotFoundError: path missing
        ValueError: empty frame, missing ``close``, or insufficient valid rows
    """
    p = Path(path).expanduser()
    if not p.is_file():
        raise FileNotFoundError(f"OHLCV parquet not found: {p}")

    df = pd.read_parquet(p).sort_index()
    if df.empty:
        raise ValueError(f"OHLCV parquet empty: {p}")
    if "close" not in df.columns:
        raise ValueError(f"OHLCV parquet missing 'close' column: {p}")

    if isinstance(df.index, pd.DatetimeIndex):
        ix = pd.DatetimeIndex(df.index)
    elif "timestamp" in df.columns:
        ix = pd.to_datetime(df["timestamp"], utc=True, errors="raise")
    else:
        raise ValueError(f"OHLCV parquet must use DatetimeIndex or include 'timestamp' column: {p}")

    s_close = pd.Series(pd.to_numeric(df["close"], errors="raise").to_numpy(dtype=float), index=ix)
    if s_close.index.duplicated().any():
        s_close = s_close[~s_close.index.duplicated(keep="last")]
    s_close = s_close.sort_index()

    if isinstance(s_close.index, pd.DatetimeIndex):
        if s_close.index.tz is None:
            s_close.index = s_close.index.tz_localize("UTC")
        else:
            s_close.index = s_close.index.tz_convert("UTC")

    rets = s_close.astype(float).pct_change().dropna()
    if len(rets) < 2:
        raise ValueError(f"Insufficient close observations after pct_change for OHLCV: {p}")

    rets.name = "returns"
    return rets
