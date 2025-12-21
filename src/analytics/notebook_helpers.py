# src/analytics/notebook_helpers.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import numpy as np
import pandas as pd

from src.core.experiments import EXPERIMENTS_CSV

# matplotlib ist optional: lazy import
HAS_MATPLOTLIB = False
plt = None  # type: ignore

try:
    import matplotlib.pyplot as _plt  # noqa: F401

    plt = _plt
    HAS_MATPLOTLIB = True
except Exception:
    # matplotlib ist optional: in CI nicht installiert → soll NICHT beim Import crashen
    HAS_MATPLOTLIB = False
    plt = None


def require_matplotlib() -> None:
    """Raise a friendly error if plotting is requested without matplotlib installed."""
    if not HAS_MATPLOTLIB:
        raise ImportError(
            "matplotlib ist nicht installiert. Installiere optional deps "
            "(z.B. `pip install matplotlib`) oder nutze Funktionen ohne Plotting."
        )


# =========================
#  Experiments / Registry
# =========================


def load_experiments(path: Path | str | None = None) -> pd.DataFrame:
    """
    Lädt die Experiment-Registry als DataFrame.

    Default: reports/experiments/experiments.csv
    """
    csv_path = Path(path) if path is not None else EXPERIMENTS_CSV
    if not csv_path.is_file():
        raise FileNotFoundError(f"Experiment-Registry nicht gefunden: {csv_path}")
    df = pd.read_csv(csv_path)
    return df


def filter_experiments(
    df: pd.DataFrame,
    run_type: str | None = None,
    strategy: str | None = None,
    symbol: str | None = None,
    portfolio: str | None = None,
    sweep_name: str | None = None,
    scan_name: str | None = None,
) -> pd.DataFrame:
    """
    Wendet die gleichen Filter wie scripts/list_experiments.py an,
    gibt aber ein DataFrame zurück (für Notebooks).
    """
    mask = pd.Series(True, index=df.index)

    if run_type is not None and "run_type" in df.columns:
        mask &= df["run_type"] == run_type

    if strategy is not None and "strategy_key" in df.columns:
        mask &= df["strategy_key"] == strategy

    if symbol is not None and "symbol" in df.columns:
        mask &= df["symbol"] == symbol

    if portfolio is not None and "portfolio_name" in df.columns:
        mask &= df["portfolio_name"] == portfolio

    if sweep_name is not None and "sweep_name" in df.columns:
        mask &= df["sweep_name"] == sweep_name

    if scan_name is not None and "scan_name" in df.columns:
        mask &= df["scan_name"] == scan_name

    return df[mask].copy()


def describe_metric_distribution(
    df: pd.DataFrame,
    metric: str = "sharpe",
    percentiles: Sequence[float] = (0.05, 0.25, 0.5, 0.75, 0.95),
) -> pd.Series:
    """
    Gibt eine grobe Verteilungsbeschreibung einer Kennzahl zurück
    (z.B. Sharpe, total_return, cagr, max_drawdown).
    """
    if metric not in df.columns:
        raise ValueError(f"Spalte {metric!r} nicht im DataFrame vorhanden.")
    s = pd.to_numeric(df[metric], errors="coerce").dropna()
    if s.empty:
        raise ValueError(f"Keine numerischen Werte für Metrik {metric!r} gefunden.")
    desc = s.describe(percentiles=list(percentiles))
    return desc


# =========================
#  Sweep-Analysis
# =========================


def load_sweep(csv_path: Path | str) -> pd.DataFrame:
    """
    Lädt eine Sweep-CSV (z.B. aus reports/sweeps/).
    """
    csv_path = Path(csv_path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"Sweep-CSV nicht gefunden: {csv_path}")
    return pd.read_csv(csv_path)


def sweep_scatter(
    df: pd.DataFrame,
    x_param: str,
    metric: str = "sharpe",
    title: str | None = None,
) -> None:
    """
    Simpler Scatterplot: Metrik vs. Parameter.
    """
    require_matplotlib()

    if x_param not in df.columns:
        raise ValueError(f"x-Parameter-Spalte {x_param!r} nicht in df.columns.")
    if metric not in df.columns:
        raise ValueError(f"Metrik-Spalte {metric!r} nicht in df.columns.")

    x = df[x_param]
    y = df[metric]

    plt.figure()
    plt.scatter(x, y)
    plt.xlabel(x_param)
    plt.ylabel(metric)
    plt.title(title or f"{metric} vs {x_param}")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def sweep_heatmap(
    df: pd.DataFrame,
    x_param: str,
    y_param: str,
    metric: str = "sharpe",
    aggfunc: str = "mean",
    title: str | None = None,
) -> None:
    """
    Heatmap über zwei Parameter (x,y) mit Metrik als Farbe.
    """
    require_matplotlib()

    for col in (x_param, y_param, metric):
        if col not in df.columns:
            raise ValueError(f"Spalte {col!r} nicht in df.columns.")

    pivot = df.pivot_table(
        index=y_param,
        columns=x_param,
        values=metric,
        aggfunc=aggfunc,
    )

    plt.figure()
    im = plt.imshow(pivot.values, aspect="auto", origin="lower")
    plt.colorbar(im, label=metric)
    plt.xticks(
        ticks=np.arange(len(pivot.columns)),
        labels=pivot.columns,
        rotation=45,
    )
    plt.yticks(
        ticks=np.arange(len(pivot.index)),
        labels=pivot.index,
    )
    plt.xlabel(x_param)
    plt.ylabel(y_param)
    plt.title(title or f"{metric} Heatmap – {y_param} vs {x_param}")
    plt.tight_layout()
    plt.show()


# =========================
#  Portfolio-Analysis
# =========================


def filter_portfolio_runs(
    df: pd.DataFrame,
    portfolio_name: str | None = None,
) -> pd.DataFrame:
    """
    Filtert run_type == 'portfolio', optional nach portfolio_name.
    """
    if "run_type" not in df.columns:
        raise ValueError("Spalte 'run_type' fehlt in Experiment-Registry.")
    mask = df["run_type"] == "portfolio"

    if portfolio_name is not None and "portfolio_name" in df.columns:
        mask &= df["portfolio_name"] == portfolio_name

    return df[mask].copy()


def top_portfolios(
    df: pd.DataFrame,
    metric: str = "sharpe",
    top_n: int = 10,
    ascending: bool = False,
) -> pd.DataFrame:
    """
    Gibt die Top-N Portfolios nach gewählter Kennzahl zurück.
    """
    df_port = filter_portfolio_runs(df)
    if metric not in df_port.columns:
        raise ValueError(f"Spalte {metric!r} nicht in Portfolio-Runs vorhanden.")
    df_port = df_port[df_port[metric].notna()]
    df_port = df_port.sort_values(by=metric, ascending=ascending)
    return df_port.head(top_n)


# =========================
#  Utility
# =========================


def print_headline(title: str) -> None:
    """
    Kleiner Helper für Notebook-Ausgaben.
    """
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80 + "\n")
