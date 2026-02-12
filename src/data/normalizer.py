"""
Data Normalizer: Konvertiert rohe Daten in Peak_Trade-Standard-Format.
"""

from typing import Dict, Optional

import pandas as pd

from . import REQUIRED_OHLCV_COLUMNS


# _PEAK_TRADE_FORCE_DT64NS_UTC
def _force_datetime_index_ns(idx, ensure_utc: bool):
    import pandas as pd

    di = pd.DatetimeIndex(idx)
    if ensure_utc:
        if di.tz is None:
            di = di.tz_localize("UTC")
        else:
            di = di.tz_convert("UTC")
        if hasattr(di, "as_unit"):
            return di.as_unit("ns")
        return pd.to_datetime(di, utc=True)
    else:
        if di.tz is not None:
            di = di.tz_convert("UTC").tz_localize(None)
        if hasattr(di, "as_unit"):
            return di.as_unit("ns")
        return pd.to_datetime(di)


class DataNormalizer:
    """
    Normalisiert rohe DataFrames in Peak_Trade-Standard-Format.

    Standard-Format:
    - DatetimeIndex (tz-aware UTC)
    - Spalten: ["open", "high", "low", "close", "volume"]
    - Sortiert nach Zeit (aufsteigend)
    - Keine Duplikate im Index
    """

    @staticmethod
    def normalize(
        df: pd.DataFrame,
        column_mapping: Optional[Dict[str, str]] = None,
        ensure_utc: bool = True,
        drop_extra_columns: bool = True,
    ) -> pd.DataFrame:
        """
        Normalisiert einen DataFrame in das Peak_Trade-OHLCV-Format.
        """
        df = df.copy()

        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError(f"Index muss DatetimeIndex sein, ist aber: {type(df.index).__name__}")

        if ensure_utc:
            if df.index.tz is None:
                df.index = df.index.tz_localize("UTC")
            else:
                df.index = df.index.tz_convert("UTC")

        if column_mapping:
            df = df.rename(columns=column_mapping)

        df.columns = df.columns.str.lower()

        missing_cols = set(REQUIRED_OHLCV_COLUMNS) - set(df.columns)
        if missing_cols:
            raise ValueError(
                f"Fehlende OHLCV-Spalten: {sorted(missing_cols)}. "
                f"Verfügbare Spalten: {sorted(df.columns)}"
            )

        if drop_extra_columns:
            df = df[REQUIRED_OHLCV_COLUMNS]

        df = df.sort_index()
        df = df[~df.index.duplicated(keep="last")]

        for col in REQUIRED_OHLCV_COLUMNS:
            df[col] = df[col].astype(float)

        # Normalize index to datetime64[ns] (UTC if ensure_utc=True, else naive)
        df.index = _force_datetime_index_ns(df.index, ensure_utc)
        return df


def resample_ohlcv(
    df: pd.DataFrame,
    freq: str,
    label: str = "right",
    closed: str = "right",
) -> pd.DataFrame:
    """
    Resampled OHLCV-Daten auf eine neue Frequenz.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError(
            f"Index muss DatetimeIndex sein für Resampling, ist aber: {type(df.index).__name__}"
        )

    missing_cols = set(REQUIRED_OHLCV_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"DataFrame muss OHLCV-Spalten enthalten. Fehlend: {sorted(missing_cols)}")

    resampler = df.resample(freq, label=label, closed=closed)

    df_resampled = pd.DataFrame(
        {
            "open": resampler["open"].first(),
            "high": resampler["high"].max(),
            "low": resampler["low"].min(),
            "close": resampler["close"].last(),
            "volume": resampler["volume"].sum(),
        }
    )

    df_resampled = df_resampled.dropna(how="all", subset=["open", "high", "low", "close"])
    return df_resampled
