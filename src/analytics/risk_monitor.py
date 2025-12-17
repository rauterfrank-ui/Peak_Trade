# src/analytics/risk_monitor.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Literal

import numpy as np
import pandas as pd

from src.core.experiments import EXPERIMENTS_CSV
from src.core.peak_config import PeakConfig

RiskStatus = Literal["OK", "WATCH", "BLOCKED", "UNKNOWN"]


@dataclass
class RiskPolicy:
    lookback_days: int = 365

    min_runs_per_strategy: int = 5
    min_runs_per_portfolio: int = 3

    max_drawdown_warn: float = 0.30
    max_drawdown_block: float = 0.50

    min_sharpe_ok: float = 0.5
    min_sharpe_good: float = 1.0

    min_total_return: float = -1.0  # z.B. -1.0 = -100%

    @classmethod
    def from_config(cls, cfg: PeakConfig) -> RiskPolicy:
        return cls(
            lookback_days=int(cfg.get("risk_monitor.lookback_days", 365)),
            min_runs_per_strategy=int(cfg.get("risk_monitor.min_runs_per_strategy", 5)),
            min_runs_per_portfolio=int(cfg.get("risk_monitor.min_runs_per_portfolio", 3)),
            max_drawdown_warn=float(cfg.get("risk_monitor.max_drawdown_warn", 0.30)),
            max_drawdown_block=float(cfg.get("risk_monitor.max_drawdown_block", 0.50)),
            min_sharpe_ok=float(cfg.get("risk_monitor.min_sharpe_ok", 0.5)),
            min_sharpe_good=float(cfg.get("risk_monitor.min_sharpe_good", 1.0)),
            min_total_return=float(cfg.get("risk_monitor.min_total_return", -1.0)),
        )


def load_experiments_df() -> pd.DataFrame:
    """
    Lädt die zentrale Experiment-Registry.
    """
    csv_path = EXPERIMENTS_CSV
    if not csv_path.is_file():
        raise FileNotFoundError(f"Experiment-Registry nicht gefunden: {csv_path}")

    df = pd.read_csv(csv_path)

    # Kernspalten sicherstellen
    for col in [
        "timestamp",
        "run_type",
        "run_name",
        "strategy_key",
        "symbol",
        "portfolio_name",
        "total_return",
        "max_drawdown",
        "sharpe",
    ]:
        if col not in df.columns:
            df[col] = np.nan

    # timestamp → Datetime
    if not np.issubdtype(df["timestamp"].dtype, np.datetime64):
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    return df


def filter_by_lookback(df: pd.DataFrame, policy: RiskPolicy) -> pd.DataFrame:
    """
    Filtert die Registry auf die letzten `lookback_days` (bezogen auf timestamp).
    """
    if "timestamp" not in df.columns or df["timestamp"].isna().all():
        # Kein Timestamp → kein Zeitfilter möglich
        return df

    max_ts = df["timestamp"].max()
    if pd.isna(max_ts):
        return df

    cutoff = max_ts - timedelta(days=policy.lookback_days)
    mask = df["timestamp"] >= cutoff
    return df[mask].copy()


def _classify_run(row: pd.Series, policy: RiskPolicy) -> tuple[RiskStatus, str]:
    """
    Klassifiziert einen einzelnen Run basierend auf MaxDD, Sharpe, TotalReturn.
    """
    dd = row.get("max_drawdown")
    sharpe = row.get("sharpe")
    total_return = row.get("total_return")

    reasons = []

    # Falls keine Kennzahlen vorhanden sind
    if pd.isna(dd) and pd.isna(sharpe) and pd.isna(total_return):
        return "UNKNOWN", "no_metrics"

    status: RiskStatus = "OK"

    # Drawdown-Rules
    if not pd.isna(dd):
        # max_drawdown typischerweise negativ (z.B. -0.35)
        dd_abs = abs(float(dd))
        if dd_abs >= policy.max_drawdown_block:
            status = "BLOCKED"
            reasons.append(f"max_drawdown>={policy.max_drawdown_block:.2f}")
        elif dd_abs >= policy.max_drawdown_warn and status != "BLOCKED":
            status = "WATCH"
            reasons.append(f"max_drawdown>={policy.max_drawdown_warn:.2f}")

    # Sharpe-Rules
    if not pd.isna(sharpe):
        s = float(sharpe)
        if s < 0:
            status = "BLOCKED"
            reasons.append("sharpe<0")
        elif s < policy.min_sharpe_ok and status != "BLOCKED":
            status = "WATCH"
            reasons.append(f"sharpe<{policy.min_sharpe_ok:.2f}")
        elif s >= policy.min_sharpe_good and status == "OK":
            reasons.append(f"sharpe>={policy.min_sharpe_good:.2f}")

    # Total-Return-Rules (optional)
    if total_return is not None and not pd.isna(total_return):
        tr = float(total_return)
        if tr < policy.min_total_return:
            status = "BLOCKED"
            reasons.append(f"total_return<{policy.min_total_return:.2f}")

    if not reasons:
        reasons.append("all_ok")

    return status, ";".join(reasons)


def annotate_runs_with_risk(df: pd.DataFrame, policy: RiskPolicy) -> pd.DataFrame:
    """
    Fügt pro Run Spalten:
        - risk_status_run
        - risk_reasons_run
    hinzu.
    """
    df = df.copy()
    statuses: list[str] = []
    reasons_list: list[str] = []

    for _, row in df.iterrows():
        status, reasons = _classify_run(row, policy)
        statuses.append(status)
        reasons_list.append(reasons)

    df["risk_status_run"] = statuses
    df["risk_reasons_run"] = reasons_list
    return df


def _aggregate_group_risk(
    df_runs: pd.DataFrame,
    group_col: str,
    min_runs: int,
) -> pd.DataFrame:
    """
    Aggregiert Risiko pro Gruppe (strategy_key oder portfolio_name).
    """
    if group_col not in df_runs.columns:
        return pd.DataFrame(
            columns=[
                group_col,
                "n_runs",
                "n_blocked",
                "n_watch",
                "n_ok",
                "n_unknown",
                "risk_status_group",
                "total_return_mean",
                "sharpe_mean",
                "max_drawdown_mean",
            ]
        )

    grouped = df_runs.groupby(group_col, dropna=True)

    records = []
    for key, grp in grouped:
        if pd.isna(key):
            continue

        n_runs = len(grp)
        n_blocked = int((grp["risk_status_run"] == "BLOCKED").sum())
        n_watch = int((grp["risk_status_run"] == "WATCH").sum())
        n_ok = int((grp["risk_status_run"] == "OK").sum())
        n_unknown = int((grp["risk_status_run"] == "UNKNOWN").sum())

        if n_runs < min_runs:
            status_group: RiskStatus = "UNKNOWN"
        elif n_blocked > 0:
            status_group = "BLOCKED"
        elif n_watch > 0:
            status_group = "WATCH"
        elif n_ok > 0:
            status_group = "OK"
        else:
            status_group = "UNKNOWN"

        records.append(
            {
                group_col: key,
                "n_runs": n_runs,
                "n_blocked": n_blocked,
                "n_watch": n_watch,
                "n_ok": n_ok,
                "n_unknown": n_unknown,
                "risk_status_group": status_group,
                "total_return_mean": float(grp["total_return"].mean())
                if "total_return" in grp.columns
                else np.nan,
                "sharpe_mean": float(grp["sharpe"].mean())
                if "sharpe" in grp.columns
                else np.nan,
                "max_drawdown_mean": float(grp["max_drawdown"].mean())
                if "max_drawdown" in grp.columns
                else np.nan,
            }
        )

    if not records:
        return pd.DataFrame(
            columns=[
                group_col,
                "n_runs",
                "n_blocked",
                "n_watch",
                "n_ok",
                "n_unknown",
                "risk_status_group",
                "total_return_mean",
                "sharpe_mean",
                "max_drawdown_mean",
            ]
        )

    return pd.DataFrame(records)


def aggregate_strategy_risk(df_runs: pd.DataFrame, policy: RiskPolicy) -> pd.DataFrame:
    """
    Aggregiert Risiko pro strategy_key.
    """
    return _aggregate_group_risk(
        df_runs=df_runs,
        group_col="strategy_key",
        min_runs=policy.min_runs_per_strategy,
    )


def aggregate_portfolio_risk(df_runs: pd.DataFrame, policy: RiskPolicy) -> pd.DataFrame:
    """
    Aggregiert Risiko pro portfolio_name (nur run_type == 'portfolio').
    """
    df_port = df_runs[df_runs["run_type"] == "portfolio"].copy()
    return _aggregate_group_risk(
        df_runs=df_port,
        group_col="portfolio_name",
        min_runs=policy.min_runs_per_portfolio,
    )
