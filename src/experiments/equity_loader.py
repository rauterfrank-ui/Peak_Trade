from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class EquityArtifactCandidate:
    kind: str
    path: Path


def _find_candidates(run_dir: Path) -> list[EquityArtifactCandidate]:
    cands: list[EquityArtifactCandidate] = []
    if not run_dir.exists():
        return cands

    p_events = run_dir / "events.parquet"
    if p_events.is_file():
        cands.append(EquityArtifactCandidate(kind="events_parquet", path=p_events))

    # Backtest exports: {run_name}_equity.csv (accept *equity.csv)
    for p in sorted(run_dir.glob("*equity.csv")):
        if p.is_file():
            cands.append(EquityArtifactCandidate(kind="equity_csv", path=p))

    return cands


def _require_datetime_index(s: pd.Series, *, source: Path) -> pd.Series:
    if not isinstance(s.index, pd.DatetimeIndex):
        raise ValueError(f"equity series index must be DatetimeIndex: {source}")
    if s.index.tz is None:
        # Enforce tz-aware UTC for downstream consistency.
        s.index = s.index.tz_localize("UTC")
    else:
        s.index = s.index.tz_convert("UTC")
    return s


def _load_from_events_parquet(p: Path) -> pd.Series:
    df = pd.read_parquet(p)
    if "equity" not in df.columns:
        raise ValueError(f"events.parquet missing required column 'equity': {p}")

    ts_col: Optional[str] = None
    for cand in ("ts_bar", "ts_event", "timestamp", "time"):
        if cand in df.columns:
            ts_col = cand
            break

    if ts_col is None:
        raise ValueError(
            f"events.parquet has no supported timestamp column (ts_bar/ts_event/timestamp/time): {p}"
        )

    idx = pd.to_datetime(df[ts_col], utc=True, errors="raise")
    s = pd.Series(df["equity"].to_numpy(), index=pd.DatetimeIndex(idx)).dropna()
    s = s[~s.index.duplicated(keep="last")].sort_index()
    s = _require_datetime_index(s, source=p)

    if len(s) < 3:
        raise ValueError(f"equity series too short after cleaning (need >=3): {p}")

    return s


def _load_from_equity_csv(p: Path) -> pd.Series:
    df = pd.read_csv(p)
    if "equity" not in df.columns:
        raise ValueError(f"equity csv missing required column 'equity': {p}")

    ts_col: Optional[str] = None
    for cand in ("date", "datetime", "timestamp", "time"):
        if cand in df.columns:
            ts_col = cand
            break

    if ts_col is None:
        # Assume first column is datetime-like (common for index-export CSVs)
        ts_col = df.columns[0]
        if ts_col == "equity":
            raise ValueError(
                f"equity csv has no timestamp column and first column is 'equity': {p}"
            )

    idx = pd.to_datetime(df[ts_col], utc=True, errors="raise")
    s = pd.Series(df["equity"].to_numpy(), index=pd.DatetimeIndex(idx)).dropna()
    s = s[~s.index.duplicated(keep="last")].sort_index()
    s = _require_datetime_index(s, source=p)

    if len(s) < 3:
        raise ValueError(f"equity series too short after cleaning (need >=3): {p}")

    return s


def load_equity_curves_from_run_dir(
    run_dir: Path,
    *,
    max_curves: Optional[int] = None,
) -> list[pd.Series]:
    """Load equity curves from a run directory.

    Supported artifacts (v1):
    - events.parquet (requires 'equity' + timestamp column)
    - *equity.csv (requires 'equity' + timestamp column, or datetime-like first column)

    Returns:
        List[pd.Series] (DatetimeIndex, tz-aware UTC), deterministic order.

    Failure-mode:
        No silent fallback. Raises FileNotFoundError/ValueError with a helpful message.
    """
    run_dir = Path(run_dir)
    cands = _find_candidates(run_dir)
    if not cands:
        raise FileNotFoundError(
            f"No supported equity artifacts found in run_dir={run_dir}. "
            f"Tried: events.parquet, *equity.csv"
        )

    curves: list[pd.Series] = []
    errors: list[str] = []

    for cand in cands:
        try:
            if cand.kind == "events_parquet":
                curves.append(_load_from_events_parquet(cand.path))
            elif cand.kind == "equity_csv":
                curves.append(_load_from_equity_csv(cand.path))
        except Exception as e:  # noqa: BLE001
            errors.append(f"{cand.kind}:{cand.path.name}: {type(e).__name__}: {e}")

    if max_curves is not None:
        curves = curves[:max_curves]

    if not curves:
        raise ValueError(
            f"Supported equity artifacts exist but none could be loaded for run_dir={run_dir}. "
            f"Errors: {errors}"
        )

    return curves


def equity_to_returns(equity: pd.Series) -> pd.Series:
    """Convert an equity curve to returns series using pct_change()."""
    equity = _require_datetime_index(equity.dropna(), source=Path("<equity_series>"))
    returns = equity.pct_change().dropna()
    if len(returns) < 2:
        raise ValueError("returns series too short after pct_change (need >=2)")
    return returns
