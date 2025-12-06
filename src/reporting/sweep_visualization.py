# src/reporting/sweep_visualization.py
"""
Peak_Trade Sweep Visualization (Phase 43)
=========================================

Visualisierungsfunktionen für Strategy-Sweep-Ergebnisse.

Komponenten:
- plot_metric_vs_single_param: 1D-Plot (Parameter vs. Metrik)
- plot_metric_heatmap_two_params: 2D-Heatmap (zwei Parameter vs. Metrik)
- generate_default_sweep_plots: Standardkollektion von Plots

Usage:
    from src.reporting.sweep_visualization import generate_default_sweep_plots

    plots = generate_default_sweep_plots(
        df=sweep_results_df,
        sweep_name="rsi_reversion_basic",
        output_dir=Path("reports/sweeps/images"),
    )
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import pandas as pd
import numpy as np

from .plots import save_heatmap, save_scatter_plot, MATPLOTLIB_AVAILABLE

logger = logging.getLogger(__name__)


# =============================================================================
# 1D PLOTS: PARAMETER VS METRIC
# =============================================================================


def plot_metric_vs_single_param(
    df: pd.DataFrame,
    param_name: str,
    metric_name: str,
    *,
    sweep_name: str,
    output_dir: Path,
) -> Optional[Path]:
    """
    Erzeugt einen Line/Scatter-Plot einer Metrik gegen einen Parameter.

    Args:
        df: DataFrame mit Sweep-Ergebnissen
        param_name: Name des Parameters (mit oder ohne "param_" Prefix)
        metric_name: Name der Metrik (mit oder ohne "metric_" Prefix)
        sweep_name: Name des Sweeps (für Dateinamen)
        output_dir: Ausgabe-Verzeichnis

    Returns:
        Pfad zur erzeugten PNG-Datei oder None bei Fehler

    Raises:
        ValueError: Wenn Parameter oder Metrik nicht im DataFrame gefunden werden
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("Matplotlib nicht verfügbar, überspringe Plot")
        return None

    # Normalisiere Spaltennamen
    param_col = param_name if param_name.startswith("param_") else f"param_{param_name}"
    metric_col = metric_name if metric_name.startswith("metric_") else f"metric_{metric_name}"

    # Validierung
    if param_col not in df.columns:
        raise ValueError(f"Parameter '{param_name}' nicht im DataFrame gefunden")
    if metric_col not in df.columns:
        raise ValueError(f"Metrik '{metric_name}' nicht im DataFrame gefunden")

    # Filtere NaN-Werte
    df_valid = df[[param_col, metric_col]].dropna()
    if len(df_valid) == 0:
        logger.warning(f"Keine gültigen Daten für {param_name} vs {metric_name}")
        return None

    # Erstelle Output-Verzeichnis
    output_dir.mkdir(parents=True, exist_ok=True)

    # Dateiname
    param_clean = param_name.replace("param_", "")
    metric_clean = metric_name.replace("metric_", "")
    filename = f"{sweep_name}_{param_clean}_vs_{metric_clean}.png"
    output_path = output_dir / filename

    try:
        # Sortiere nach Parameter für bessere Linie
        df_sorted = df_valid.sort_values(param_col)

        # Scatter-Plot mit Trendlinie
        save_scatter_plot(
            x_values=df_sorted[param_col].tolist(),
            y_values=df_sorted[metric_col].tolist(),
            output_path=output_path,
            title=f"{metric_clean.replace('_', ' ').title()} vs {param_clean.replace('_', ' ').title()}",
            xlabel=param_clean.replace("_", " ").title(),
            ylabel=metric_clean.replace("_", " ").title(),
            show_trend=True,
        )

        logger.info(f"Plot erstellt: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Plots: {e}")
        return None


# =============================================================================
# 2D HEATMAP: TWO PARAMS VS METRIC
# =============================================================================


def plot_metric_heatmap_two_params(
    df: pd.DataFrame,
    param_x: str,
    param_y: str,
    metric_name: str,
    *,
    sweep_name: str,
    output_dir: Path,
) -> Optional[Path]:
    """
    Erzeugt eine 2D-Heatmap einer Metrik über zwei Parameter.

    Args:
        df: DataFrame mit Sweep-Ergebnissen
        param_x: X-Achsen-Parameter (mit oder ohne "param_" Prefix)
        param_y: Y-Achsen-Parameter (mit oder ohne "param_" Prefix)
        metric_name: Name der Metrik (mit oder ohne "metric_" Prefix)
        sweep_name: Name des Sweeps (für Dateinamen)
        output_dir: Ausgabe-Verzeichnis

    Returns:
        Pfad zur erzeugten PNG-Datei oder None bei Fehler

    Raises:
        ValueError: Wenn Parameter oder Metrik nicht im DataFrame gefunden werden
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("Matplotlib nicht verfügbar, überspringe Plot")
        return None

    # Normalisiere Spaltennamen
    param_x_col = param_x if param_x.startswith("param_") else f"param_{param_x}"
    param_y_col = param_y if param_y.startswith("param_") else f"param_{param_y}"
    metric_col = metric_name if metric_name.startswith("metric_") else f"metric_{metric_name}"

    # Validierung
    if param_x_col not in df.columns:
        raise ValueError(f"Parameter '{param_x}' nicht im DataFrame gefunden")
    if param_y_col not in df.columns:
        raise ValueError(f"Parameter '{param_y}' nicht im DataFrame gefunden")
    if metric_col not in df.columns:
        raise ValueError(f"Metrik '{metric_name}' nicht im DataFrame gefunden")

    # Filtere NaN-Werte
    df_valid = df[[param_x_col, param_y_col, metric_col]].dropna()
    if len(df_valid) == 0:
        logger.warning(f"Keine gültigen Daten für Heatmap {param_x} x {param_y} vs {metric_name}")
        return None

    # Erstelle Output-Verzeichnis
    output_dir.mkdir(parents=True, exist_ok=True)

    # Dateiname
    param_x_clean = param_x.replace("param_", "")
    param_y_clean = param_y.replace("param_", "")
    metric_clean = metric_name.replace("metric_", "")
    filename = f"{sweep_name}_heatmap_{param_x_clean}_x_{param_y_clean}_{metric_clean}.png"
    output_path = output_dir / filename

    try:
        # Erstelle Pivot-Table
        pivot = df_valid.pivot_table(
            values=metric_col,
            index=param_y_col,
            columns=param_x_col,
            aggfunc="mean",
        )

        # Sortiere Index und Spalten für bessere Darstellung
        pivot = pivot.sort_index(axis=0).sort_index(axis=1)

        # Heatmap erstellen
        metric_clean_display = metric_clean.replace("_", " ").title()
        param_x_display = param_x_clean.replace("_", " ").title()
        param_y_display = param_y_clean.replace("_", " ").title()

        save_heatmap(
            pivot_df=pivot,
            output_path=output_path,
            title=f"{metric_clean_display} Heatmap: {param_x_display} × {param_y_display}",
            xlabel=param_x_display,
            ylabel=param_y_display,
            cbar_label=metric_clean_display,
            annotate=pivot.size <= 100,  # Nur bei kleinen Heatmaps
        )

        logger.info(f"Heatmap erstellt: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Heatmap: {e}")
        return None


# =============================================================================
# DEFAULT PLOT COLLECTION
# =============================================================================


def generate_default_sweep_plots(
    df: pd.DataFrame,
    sweep_name: str,
    output_dir: Path,
    param_candidates: Optional[Sequence[str]] = None,
    metric_primary: str = "metric_sharpe_ratio",
    metric_fallback: str = "metric_total_return",
) -> Dict[str, Path]:
    """
    Erzeugt eine Standardkollektion von Plots für Sweep-Ergebnisse.

    Args:
        df: DataFrame mit Sweep-Ergebnissen
        sweep_name: Name des Sweeps
        output_dir: Ausgabe-Verzeichnis
        param_candidates: Liste von Parametern für Plots (optional, wird automatisch erkannt)
        metric_primary: Primäre Metrik für Plots
        metric_fallback: Fallback-Metrik falls primary fehlt

    Returns:
        Dictionary mit Plot-Namen -> Pfad (z.B. {"param_vs_metric": Path(...), "heatmap": Path(...)})
    """
    plots: Dict[str, Path] = {}

    # Extrahiere Param- und Metrik-Spalten
    param_cols = [c for c in df.columns if c.startswith("param_")]
    metric_cols = [c for c in df.columns if c.startswith("metric_")]

    if not param_cols:
        logger.warning("Keine Parameter-Spalten gefunden, keine Plots möglich")
        return plots

    if not metric_cols:
        logger.warning("Keine Metrik-Spalten gefunden, keine Plots möglich")
        return plots

    # Bestimme verwendete Metrik
    metric_used = metric_primary if metric_primary in df.columns else metric_fallback
    if metric_used not in df.columns:
        if metric_cols:
            logger.warning(f"Weder {metric_primary} noch {metric_fallback} gefunden, verwende erste verfügbare Metrik: {metric_cols[0]}")
            metric_used = metric_cols[0]
        else:
            logger.warning("Keine Metrik-Spalten gefunden")
            return plots

    if metric_used is None:
        return plots

    # Parameter-Kandidaten
    if param_candidates is None:
        # Automatisch: Nimm die ersten 3 Parameter
        param_candidates = param_cols[:3]

    # 1D-Plots: Parameter vs. Metrik
    for param_col in param_candidates:
        if param_col not in df.columns:
            param_col = f"param_{param_col}" if not param_col.startswith("param_") else param_col

        if param_col in df.columns:
            plot_path = plot_metric_vs_single_param(
                df=df,
                param_name=param_col,
                metric_name=metric_used,
                sweep_name=sweep_name,
                output_dir=output_dir,
            )
            if plot_path:
                param_clean = param_col.replace("param_", "")
                plots[f"param_{param_clean}_vs_metric"] = plot_path

    # 2D-Heatmap: Zwei Parameter vs. Metrik (nur wenn mindestens 2 Parameter vorhanden)
    if len(param_candidates) >= 2:
        param_x = param_candidates[0]
        param_y = param_candidates[1]

        # Normalisiere
        if not param_x.startswith("param_"):
            param_x = f"param_{param_x}"
        if not param_y.startswith("param_"):
            param_y = f"param_{param_y}"

        if param_x in df.columns and param_y in df.columns:
            heatmap_path = plot_metric_heatmap_two_params(
                df=df,
                param_x=param_x,
                param_y=param_y,
                metric_name=metric_used,
                sweep_name=sweep_name,
                output_dir=output_dir,
            )
            if heatmap_path:
                plots["heatmap_2d"] = heatmap_path

    logger.info(f"Erstellt: {len(plots)} Plots für Sweep '{sweep_name}'")
    return plots

