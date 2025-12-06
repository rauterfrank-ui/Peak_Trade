# src/analytics/filter_flow.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Literal, Sequence, Tuple

import numpy as np
import pandas as pd

from src.core.peak_config import PeakConfig


SelectionStatus = Literal["APPROVED", "WATCH", "BLOCKED", "UNKNOWN"]


@dataclass
class SelectionPolicy:
    """
    Policy für den Live-/Filter-Flow.

    Diese Policy arbeitet auf:
    - Risk-Aggregation (risk_status_group)
    - Forward-Eval-Runs (run_type = 'forward_eval')
    - Gesamtzahl von Runs pro Strategie
    """

    allowed_risk_statuses: Tuple[str, ...] = ("OK",)

    min_total_runs: int = 10
    min_forward_eval_runs: int = 3

    min_forward_sharpe: float = 0.0
    min_forward_total_return: float = -0.5

    @classmethod
    def from_config(cls, cfg: PeakConfig) -> "SelectionPolicy":
        raw_allowed = cfg.get("filter_flow.allowed_risk_statuses", ["OK"])
        if isinstance(raw_allowed, str):
            allowed = tuple(s.strip() for s in raw_allowed.split(",") if s.strip())
        else:
            try:
                allowed = tuple(str(x) for x in raw_allowed)
            except TypeError:
                allowed = ("OK",)

        return cls(
            allowed_risk_statuses=allowed,
            min_total_runs=int(cfg.get("filter_flow.min_total_runs", 10)),
            min_forward_eval_runs=int(cfg.get("filter_flow.min_forward_eval_runs", 3)),
            min_forward_sharpe=float(cfg.get("filter_flow.min_forward_sharpe", 0.0)),
            min_forward_total_return=float(
                cfg.get("filter_flow.min_forward_total_return", -0.5)
            ),
        )


def _safe_mean(series: pd.Series) -> float:
    if series is None or series.empty:
        return float("nan")
    return float(series.mean())


def _classify_selection(row: pd.Series, policy: SelectionPolicy) -> Tuple[SelectionStatus, str]:
    """
    Klassifiziert eine Strategie basierend auf:
    - risk_status_group
    - n_total_runs, n_forward_eval_runs
    - forward_total_return_mean, forward_sharpe_mean
    """
    risk_status = row.get("risk_status_group", np.nan)
    n_total_runs = row.get("n_total_runs", 0) or 0
    n_fwd = row.get("n_forward_eval_runs", 0) or 0
    fwd_tr = row.get("forward_total_return_mean", np.nan)
    fwd_sh = row.get("forward_sharpe_mean", np.nan)

    reasons: list[str] = []
    status: SelectionStatus = "APPROVED"

    # 1) Risk hart blockend?
    if isinstance(risk_status, str) and risk_status == "BLOCKED":
        status = "BLOCKED"
        reasons.append("risk_blocked")

    # 2) Risk-Status nicht erlaubt?
    if isinstance(risk_status, str) and risk_status not in policy.allowed_risk_statuses:
        if status != "BLOCKED":
            status = "WATCH"
        reasons.append(f"risk_status_not_allowed({risk_status})")

    # 3) Ausreichend Daten?
    if n_total_runs < policy.min_total_runs or n_fwd < policy.min_forward_eval_runs:
        # zu wenig Daten → UNKNOWN dominiert alles
        status = "UNKNOWN"
        reasons.append("insufficient_runs")

    # 4) Forward-Qualität (nur wenn nicht BLOCKED/UNKNOWN)
    if status not in ("BLOCKED", "UNKNOWN"):
        if not (fwd_sh is None or np.isnan(fwd_sh)):
            if fwd_sh < policy.min_forward_sharpe:
                if status == "APPROVED":
                    status = "WATCH"
                reasons.append(f"forward_sharpe<{policy.min_forward_sharpe:.3f}")

        if not (fwd_tr is None or np.isnan(fwd_tr)):
            if fwd_tr < policy.min_forward_total_return:
                if status == "APPROVED":
                    status = "WATCH"
                reasons.append(
                    f"forward_total_return<{policy.min_forward_total_return:.3f}"
                )

    if not reasons:
        reasons.append("all_criteria_passed")

    return status, ";".join(reasons)


def build_strategy_selection(
    df_runs: pd.DataFrame,
    df_strat_risk: pd.DataFrame,
    policy: SelectionPolicy,
) -> pd.DataFrame:
    """
    Baut eine Strategy-Selection-Tabelle.

    Erwartet:
    - df_runs: alle Runs im Lookback, inkl. Spalten:
        strategy_key, run_type, total_return, sharpe, ...
    - df_strat_risk: Aggregation aus risk_monitor.aggregate_strategy_risk(...)
        mit Spalten: strategy_key, risk_status_group, n_runs, ...

    Rückgabe:
    DataFrame mit Spalten u.a.:
        strategy_key
        n_total_runs
        n_forward_eval_runs
        forward_total_return_mean
        forward_sharpe_mean
        risk_status_group
        selection_status
        selection_reasons
    """
    # Alle Strategie-Keys einsammeln
    keys_runs = (
        set(df_runs["strategy_key"].dropna()) if "strategy_key" in df_runs.columns else set()
    )
    keys_risk = (
        set(df_strat_risk["strategy_key"].dropna())
        if "strategy_key" in df_strat_risk.columns
        else set()
    )
    all_keys = sorted(keys_runs | keys_risk)

    if not all_keys:
        return pd.DataFrame(
            columns=[
                "strategy_key",
                "n_total_runs",
                "n_forward_eval_runs",
                "forward_total_return_mean",
                "forward_sharpe_mean",
                "risk_status_group",
                "selection_status",
                "selection_reasons",
            ]
        )

    df_sel = pd.DataFrame({"strategy_key": all_keys})

    # n_total_runs
    if "strategy_key" in df_runs.columns:
        total_counts = df_runs.groupby("strategy_key").size().rename("n_total_runs")
        df_sel = df_sel.merge(
            total_counts.to_frame(), on="strategy_key", how="left"
        )
    else:
        df_sel["n_total_runs"] = 0

    # Forward-Eval-Stats
    if "run_type" in df_runs.columns:
        df_fwd = df_runs[df_runs["run_type"] == "forward_eval"].copy()
    else:
        df_fwd = df_runs.iloc[0:0].copy()

    if not df_fwd.empty:
        fwd_counts = df_fwd.groupby("strategy_key").size().rename("n_forward_eval_runs")
        fwd_tr_mean = (
            df_fwd.groupby("strategy_key")["total_return"]
            .mean()
            .rename("forward_total_return_mean")
        )
        if "sharpe" in df_fwd.columns:
            fwd_sh_mean = (
                df_fwd.groupby("strategy_key")["sharpe"]
                .mean()
                .rename("forward_sharpe_mean")
            )
        else:
            fwd_sh_mean = pd.Series(dtype=float, name="forward_sharpe_mean")

        df_sel = df_sel.merge(
            fwd_counts.to_frame(), on="strategy_key", how="left"
        ).merge(
            fwd_tr_mean.to_frame(), on="strategy_key", how="left"
        )
        if not fwd_sh_mean.empty:
            df_sel = df_sel.merge(
                fwd_sh_mean.to_frame(), on="strategy_key", how="left"
            )
        else:
            df_sel["forward_sharpe_mean"] = np.nan
    else:
        df_sel["n_forward_eval_runs"] = 0
        df_sel["forward_total_return_mean"] = np.nan
        df_sel["forward_sharpe_mean"] = np.nan

    # Risk-Status joinen
    if not df_strat_risk.empty:
        df_sel = df_sel.merge(
            df_strat_risk[["strategy_key", "risk_status_group", "n_runs"]],
            on="strategy_key",
            how="left",
            suffixes=("", "_risk"),
        )
    else:
        df_sel["risk_status_group"] = np.nan
        df_sel["n_runs"] = np.nan

    # NaNs sinnvoll füllen
    df_sel["n_total_runs"] = df_sel["n_total_runs"].fillna(0).astype(int)
    df_sel["n_forward_eval_runs"] = df_sel["n_forward_eval_runs"].fillna(0).astype(int)

    # Auswahl klassifizieren
    statuses: list[str] = []
    reasons: list[str] = []
    for _, row in df_sel.iterrows():
        status, reason = _classify_selection(row, policy)
        statuses.append(status)
        reasons.append(reason)

    df_sel["selection_status"] = statuses
    df_sel["selection_reasons"] = reasons

    return df_sel
