# src/analytics/leaderboard.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from src.core.experiments import EXPERIMENTS_CSV


@dataclass
class Leaderboards:
    """
    Container fuer verschiedene Standard-Leaderboards.
    """
    df_all: pd.DataFrame
    df_global_top: pd.DataFrame
    df_per_symbol: pd.DataFrame
    df_per_strategy: pd.DataFrame
    df_per_run_type: pd.DataFrame


def load_experiments_df() -> pd.DataFrame:
    """
    Laedt die zentrale Experiment-Registry als DataFrame.

    Erwartet: reports/experiments/experiments.csv
    """
    csv_path = EXPERIMENTS_CSV
    if not csv_path.is_file():
        raise FileNotFoundError(f"Experiment-Registry nicht gefunden: {csv_path}")

    df = pd.read_csv(csv_path)

    # Sicherstellen, dass einige Kernspalten existieren (ansonsten leere anlegen)
    for col in [
        "run_type",
        "run_name",
        "strategy_key",
        "symbol",
        "portfolio_name",
        "sweep_name",
        "scan_name",
        "total_return",
        "cagr",
        "max_drawdown",
        "sharpe",
        "timestamp",
    ]:
        if col not in df.columns:
            df[col] = None

    return df


def _filter_for_metric(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    if metric not in df.columns:
        # leeres DF ohne Zeilen zurueckgeben
        return df.iloc[0:0].copy()
    return df[df[metric].notna()].copy()


def _compute_global_top(
    df: pd.DataFrame,
    metric: str,
    top_n: int = 50,
    ascending: bool = False,
) -> pd.DataFrame:
    dfm = _filter_for_metric(df, metric)
    if dfm.empty:
        return dfm

    dfm = dfm.sort_values(by=metric, ascending=ascending)
    return dfm.head(top_n)


def _compute_group_top(
    df: pd.DataFrame,
    group_col: str,
    metric: str,
    per_group_top_n: int = 5,
    ascending: bool = False,
    min_runs_per_group: int = 1,
) -> pd.DataFrame:
    """
    Berechnet pro Gruppe (z.B. Symbol oder Strategie) die Top-N-Runs nach `metric`.
    """
    dfm = _filter_for_metric(df, metric)
    if dfm.empty or group_col not in dfm.columns:
        return dfm.iloc[0:0].copy()

    # Nur Gruppen mit ausreichend vielen Runs
    grp_counts = dfm[group_col].value_counts()
    valid_groups = grp_counts[grp_counts >= min_runs_per_group].index

    dfm = dfm[dfm[group_col].isin(valid_groups)]
    if dfm.empty:
        return dfm

    dfm = dfm.sort_values(by=metric, ascending=ascending)
    top = dfm.groupby(group_col, as_index=False, sort=False).head(per_group_top_n)
    return top


def build_standard_leaderboards(
    metric: str = "sharpe",
    global_top_n: int = 50,
    per_symbol_top_n: int = 5,
    per_strategy_top_n: int = 5,
    per_run_type_top_n: int = 5,
    min_runs_per_symbol: int = 1,
    min_runs_per_strategy: int = 1,
    min_runs_per_run_type: int = 1,
    ascending: bool = False,
) -> Leaderboards:
    """
    Baut Standard-Leaderboards auf Basis der Experiment-Registry.

    metric:
        z.B. "sharpe", "total_return", "cagr"
    ascending:
        False fuer "hoeher ist besser" (Sharpe, Return, CAGR),
        True falls man z.B. nach max_drawdown sortieren moechte (kleiner ist besser).
    """
    df_all = load_experiments_df()

    df_global_top = _compute_global_top(
        df_all, metric=metric, top_n=global_top_n, ascending=ascending
    )

    df_per_symbol = _compute_group_top(
        df_all,
        group_col="symbol",
        metric=metric,
        per_group_top_n=per_symbol_top_n,
        ascending=ascending,
        min_runs_per_group=min_runs_per_symbol,
    )

    df_per_strategy = _compute_group_top(
        df_all,
        group_col="strategy_key",
        metric=metric,
        per_group_top_n=per_strategy_top_n,
        ascending=ascending,
        min_runs_per_group=min_runs_per_strategy,
    )

    df_per_run_type = _compute_group_top(
        df_all,
        group_col="run_type",
        metric=metric,
        per_group_top_n=per_run_type_top_n,
        ascending=ascending,
        min_runs_per_group=min_runs_per_run_type,
    )

    return Leaderboards(
        df_all=df_all,
        df_global_top=df_global_top,
        df_per_symbol=df_per_symbol,
        df_per_strategy=df_per_strategy,
        df_per_run_type=df_per_run_type,
    )
