#!/usr/bin/env python3
"""
Validate Futures Dataset (Offline-First)
======================================

Minimaler Validator für OHLCV Futures Datasets (Parquet/CSV).

Checks (MVP):
- Peak_Trade OHLCV data contract (strict=True, require_tz=True)
- Optional: Maintenance break check (CME Equity Index Session Spec, simplified)

NO-LIVE: Keine Live-Calls.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.data.contracts import validate_ohlcv
from src.markets.cme.calendar import CmeEquityIndexSessionSpec


def _read_any(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
        # Heuristic: if an 'timestamp' or 'time' column exists, set index
        for col in ("timestamp", "time", "datetime", "date"):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], utc=True)
                df = df.set_index(col)
                break
        return df
    raise ValueError(f"Unsupported file type: {path.suffix} (use .parquet or .csv)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Input OHLCV file (.parquet or .csv)")
    ap.add_argument("--allow-partial-volume-nans", action="store_true")
    ap.add_argument(
        "--check-maintenance", action="store_true", help="Fail if bars fall in daily maintenance"
    )
    args = ap.parse_args()

    path = Path(args.input)
    df = _read_any(path)

    validate_ohlcv(
        df,
        strict=True,
        require_tz=True,
        allow_partial_nans=bool(args.allow_partial_volume_nans),
    )

    if args.check_maintenance:
        sess = CmeEquityIndexSessionSpec()
        bad = []
        for ts in df.index:
            ts_utc = pd.Timestamp(ts).to_pydatetime()
            if sess.is_in_maintenance_break_utc(ts_utc):
                bad.append(ts)
                if len(bad) >= 5:
                    break
        if bad:
            print(f"FAIL: found bars in maintenance window (first {len(bad)}): {bad}")
            return 2

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
