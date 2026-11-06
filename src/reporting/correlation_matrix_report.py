# src/reporting/correlation_matrix_report.py
"""
Peak_Trade Correlation Matrix Report (Parameter–Metrik)
========================================================

Berechnet die Korrelationsmatrix zwischen numerischen Sweep-Parametern und
ausgewählten Metriken (Spearman default, optional Pearson), schreibt CSV und
Heatmap. Für die Integration in den Sweep-Report-Schritt.

Usage:
    from src.reporting.correlation_matrix_report import (
        build_param_metric_corr,
        correlation_matrix_report,
    )

    matrix = build_param_metric_corr(df, metric_cols=None, method="spearman")
    paths = correlation_matrix_report(df, output_dir=Path("out/report"), sweep_name="rsi")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import pandas as pd

from .plots import save_heatmap, MATPLOTLIB_AVAILABLE

logger = logging.getLogger(__name__)

# Deterministische Dateinamen
CORR_CSV_SUFFIX = "param_metric_correlation.csv"
CORR_HEATMAP_SUFFIX = "param_metric_correlation_heatmap.png"


def _normalize_param_col(name: str) -> str:
    """Normalisiert Parametername zu param_*."""
    return name if name.startswith("param_") else f"param_{name}"


def _normalize_metric_col(name: str) -> str:
    """Normalisiert Metrikname zu metric_*."""
    return name if name.startswith("metric_") else f"metric_{name}"


def _numeric_param_columns(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """
    Ermittelt numerische Parameter-Spalten (param_*) und nicht-numerische (skipped).

    Returns:
        (numeric_param_cols, skipped_param_cols) – beide sortiert für Determinismus.
    """
    param_cols = sorted([c for c in df.columns if c.startswith("param_")])
    numeric: List[str] = []
    skipped: List[str] = []
    for col in param_cols:
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric.append(col)
        else:
            skipped.append(col)
    return numeric, skipped


def _metric_columns(df: pd.DataFrame, metric_cols: Optional[Sequence[str]]) -> List[str]:
    """Bestimmt die zu verwendenden Metrik-Spalten (sortiert)."""
    if metric_cols is not None:
        normalized = [_normalize_metric_col(c) for c in metric_cols]
        return sorted([c for c in normalized if c in df.columns])
    return sorted([c for c in df.columns if c.startswith("metric_")])


def build_param_metric_corr(
    df: pd.DataFrame,
    metric_cols: Optional[Sequence[str]] = None,
    method: str = "spearman",
) -> pd.DataFrame:
    """
    Berechnet die Korrelationsmatrix (Parameter × Metriken) mit pairwise-complete Beobachtungen.

    - Nur numerische Parameter werden verwendet; nicht-numerische werden übersprungen (geloggt).
    - Spalten/Zeilen deterministisch sortiert.
    - Fehlende Werte: pairwise complete (pandas .corr() Verhalten).

    Args:
        df: Sweep-Ergebnis-DataFrame mit param_* und metric_* Spalten.
        metric_cols: Optionale Liste von Metrik-Spalten (sonst alle metric_*).
        method: "spearman" (default) oder "pearson".

    Returns:
        DataFrame mit Index = Parametern (Zeilen), Spalten = Metriken; Werte = Korrelation.
        Leeres DataFrame wenn keine numerischen Parameter oder keine Metriken.
    """
    if method not in ("spearman", "pearson"):
        raise ValueError("method must be 'spearman' or 'pearson'")

    numeric_params, skipped_params = _numeric_param_columns(df)
    if skipped_params:
        logger.info(
            "Correlation matrix: skipping non-numeric param columns: %s",
            skipped_params,
        )
    if not numeric_params:
        logger.warning("Correlation matrix: no numeric param columns found")
        return pd.DataFrame()

    metrics = _metric_columns(df, metric_cols)
    if not metrics:
        logger.warning("Correlation matrix: no metric columns found")
        return pd.DataFrame()

    # Subset mit deterministischer Reihenfolge
    use = numeric_params + metrics
    sub = df[use].copy()

    # Pairwise complete correlation (pandas default)
    corr_full = sub.corr(method=method, min_periods=1)
    # Block: Zeilen = Parameter, Spalten = Metriken
    block = corr_full.loc[numeric_params, metrics]
    return block


def correlation_matrix_report(
    df: pd.DataFrame,
    output_dir: Path,
    sweep_name: str,
    metric_cols: Optional[Sequence[str]] = None,
    method: str = "spearman",
    with_heatmap: bool = True,
) -> dict:
    """
    Erzeugt Korrelationsmatrix-Report: CSV + optional Heatmap.

    - Deterministische Dateinamen: {sweep_name}_param_metric_correlation.csv,
      {sweep_name}_param_metric_correlation_heatmap.png
    - Loggt übersprungene nicht-numerische Parameter.

    Args:
        df: Sweep-Ergebnis-DataFrame.
        output_dir: Ausgabe-Verzeichnis für CSV und PNG.
        sweep_name: Sweep-Name für Dateinamen.
        metric_cols: Optionale Metrik-Spalten (sonst alle metric_*).
        method: "spearman" oder "pearson".
        with_heatmap: Ob Heatmap erzeugt werden soll.

    Returns:
        Dict mit "csv_path", "heatmap_path" (optional). Fehlende Pfade nicht im Dict.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    matrix = build_param_metric_corr(df, metric_cols=metric_cols, method=method)
    result: dict = {}

    if matrix.empty:
        logger.warning("Correlation matrix empty, skipping CSV and heatmap")
        return result

    # CSV – deterministischer Dateiname
    csv_path = output_dir / f"{sweep_name}_{CORR_CSV_SUFFIX}"
    matrix.to_csv(csv_path)
    result["csv_path"] = csv_path
    logger.info("Correlation matrix CSV written: %s", csv_path)

    # Heatmap
    if with_heatmap and MATPLOTLIB_AVAILABLE:
        heatmap_name = f"{sweep_name}_{CORR_HEATMAP_SUFFIX}"
        heatmap_path = output_dir / heatmap_name
        title = f"Parameter–Metric Correlation ({method})"
        try:
            save_heatmap(
                pivot_df=matrix,
                output_path=heatmap_path,
                title=title,
                xlabel="Metrics",
                ylabel="Parameters",
                cbar_label=f"Correlation ({method})",
                annotate=matrix.size <= 100,
                fmt=".2f",
                cmap="RdYlGn",
            )
            result["heatmap_path"] = heatmap_path
            logger.info("Correlation heatmap written: %s", heatmap_path)
        except Exception as e:
            logger.warning("Could not create correlation heatmap: %s", e)
    elif with_heatmap and not MATPLOTLIB_AVAILABLE:
        logger.warning("Matplotlib not available, skipping correlation heatmap")

    return result
