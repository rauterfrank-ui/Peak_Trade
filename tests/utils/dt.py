import pandas as pd


def normalize_dt_index(df: pd.DataFrame, *, ensure_utc: bool) -> pd.DataFrame:
    out = df.copy()
    di = pd.DatetimeIndex(out.index)
    if ensure_utc:
        if di.tz is None:
            di = di.tz_localize("UTC")
        else:
            di = di.tz_convert("UTC")
        if hasattr(di, "as_unit"):
            out.index = di.as_unit("ns")
        else:
            out.index = pd.to_datetime(di, utc=True)
    else:
        if di.tz is not None:
            di = di.tz_convert("UTC").tz_localize(None)
        if hasattr(di, "as_unit"):
            out.index = di.as_unit("ns")
        else:
            out.index = pd.to_datetime(di)
    return out
