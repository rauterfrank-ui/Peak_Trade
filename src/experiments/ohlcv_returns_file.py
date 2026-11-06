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

    return load_close_returns_from_ohlcv_frame(pd.read_parquet(p))


def load_close_returns_from_ohlcv_frame(frame: pd.DataFrame) -> pd.Series:
    """Original return calculation shared by admitted in-memory offline inputs."""
    df = frame.copy(deep=True).sort_index()
    if df.empty:
        raise ValueError("OHLCV frame empty")
    if "close" not in df.columns:
        raise ValueError("OHLCV frame missing 'close' column")

    if isinstance(df.index, pd.DatetimeIndex):
        ix = pd.DatetimeIndex(df.index)
    elif "timestamp" in df.columns:
        ix = pd.to_datetime(df["timestamp"], utc=True, errors="raise")
    else:
        raise ValueError("OHLCV frame must use DatetimeIndex or include 'timestamp' column")

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
        raise ValueError("Insufficient close observations after pct_change for OHLCV")

    rets.name = "returns"
    return rets
