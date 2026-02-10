# src/reporting/sweep_visualization.py
"""
Peak_Trade Sweep Visualization (Phase 43)
=========================================

Visualisierungsfunktionen für Strategy-Sweep-Ergebnisse.

Komponenten:
- plot_metric_vs_single_param: 1D-Plot (Parameter vs. Metrik)
- plot_metric_heatmap_two_params: 2D-Heatmap (zwei Parameter vs. Metrik)
- create_drawdown_heatmap: 2D-Heatmap speziell für Drawdown-Metriken
- create_standard_2x2_heatmap: Standard-Template mit 2 Parametern × 2 Metriken (zwei Heatmaps)
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
# DRAWDOWN HEATMAP
# =============================================================================


def create_drawdown_heatmap(
    df: pd.DataFrame,
    param_x: str,
    param_y: str,
    metric_col: str = "metric_max_drawdown",
    *,
    title: Optional[str] = None,
    output_path: Optional[Path] = None,
    sweep_name: Optional[str] = None,
    output_dir: Optional[Path] = None,
) -> Optional[Path]:
    """
    Erzeugt eine 2D-Heatmap für eine Drawdown-Metrik (z. B. Max-Drawdown) über zwei Parameterachsen.

    Args:
        df: DataFrame mit Sweep-Ergebnissen. Muss Spalten für param_x, param_y
            und die Metrikspalte (default: 'metric_max_drawdown') enthalten.
        param_x: Name der Spalte für die X-Parameterachse (mit oder ohne "param_" Prefix).
        param_y: Name der Spalte für die Y-Parameterachse (mit oder ohne "param_" Prefix).
        metric_col: Name der Spalte mit der Drawdown-Metrik (default: 'metric_max_drawdown').
        title: Optionaler Plot-Titel. Falls None, wird automatisch generiert.
        output_path: Optionaler Pfad für die Ausgabe. Falls None, wird der Pfad
            anhand von param_x, param_y und metric_col konstruiert.
        sweep_name: Name des Sweeps (für Dateinamen, falls output_path None ist).
        output_dir: Ausgabe-Verzeichnis (für Dateinamen, falls output_path None ist).

    Returns:
        Pfad zur erzeugten Plot-Datei oder None bei Fehler.

    Raises:
        ValueError: Wenn Parameter oder Metrik nicht im DataFrame gefunden werden
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("Matplotlib nicht verfügbar, überspringe Drawdown-Heatmap")
        return None

    # Normalisiere Spaltennamen
    param_x_col = param_x if param_x.startswith("param_") else f"param_{param_x}"
    param_y_col = param_y if param_y.startswith("param_") else f"param_{param_y}"
    metric_col_normalized = (
        metric_col if metric_col.startswith("metric_") else f"metric_{metric_col}"
    )

    # Validierung
    if param_x_col not in df.columns:
        raise ValueError(f"Parameter '{param_x}' nicht im DataFrame gefunden")
    if param_y_col not in df.columns:
        raise ValueError(f"Parameter '{param_y}' nicht im DataFrame gefunden")
    if metric_col_normalized not in df.columns:
        raise ValueError(f"Drawdown-Metrik '{metric_col}' nicht im DataFrame gefunden")

    # Filtere NaN-Werte
    df_valid = df[[param_x_col, param_y_col, metric_col_normalized]].dropna()
    if len(df_valid) == 0:
        logger.warning(f"Keine gültigen Daten für Drawdown-Heatmap {param_x} x {param_y}")
        return None

    # Bestimme Output-Pfad
    if output_path is None:
        if output_dir is None or sweep_name is None:
            raise ValueError("output_path oder (output_dir + sweep_name) muss angegeben werden")
        output_dir.mkdir(parents=True, exist_ok=True)
        param_x_clean = param_x.replace("param_", "")
        param_y_clean = param_y.replace("param_", "")
        filename = f"heatmap_drawdown_{param_x_clean}_vs_{param_y_clean}.png"
        output_path = output_dir / filename
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Erstelle Pivot-Table
        pivot = df_valid.pivot_table(
            values=metric_col_normalized,
            index=param_y_col,
            columns=param_x_col,
            aggfunc="mean",
        )

        # Sortiere Index und Spalten für bessere Darstellung
        pivot = pivot.sort_index(axis=0).sort_index(axis=1)

        # Titel generieren falls nicht angegeben
        if title is None:
            param_x_display = param_x.replace("param_", "").replace("_", " ").title()
            param_y_display = param_y.replace("param_", "").replace("_", " ").title()
            metric_display = metric_col_normalized.replace("metric_", "").replace("_", " ").title()
            title = f"Drawdown-Heatmap: {param_x_display} × {param_y_display} ({metric_display})"

        # Heatmap erstellen (für Drawdown verwenden wir eine invertierte Colormap)
        # Drawdown ist negativ, daher sollte "Reds" oder "YlOrRd" verwendet werden
        param_x_display = param_x.replace("param_", "").replace("_", " ").title()
        param_y_display = param_y.replace("param_", "").replace("_", " ").title()
        metric_display = metric_col_normalized.replace("metric_", "").replace("_", " ").title()

        save_heatmap(
            pivot_df=pivot,
            output_path=output_path,
            title=title,
            xlabel=param_x_display,
            ylabel=param_y_display,
            cbar_label=metric_display,
            annotate=pivot.size <= 100,  # Nur bei kleinen Heatmaps
            cmap="Reds",  # Rot für Drawdown (höhere Werte = schlechter)
        )

        logger.info(f"Drawdown-Heatmap erstellt: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Drawdown-Heatmap: {e}")
        return None


# =============================================================================
# STANDARD 2×2 HEATMAP TEMPLATE (Block B)
# =============================================================================


def create_standard_2x2_heatmap(
    df: pd.DataFrame,
    x_param: str,
    y_param: str,
    metric_a: str,
    metric_b: str,
    *,
    sweep_name: str,
    output_dir: Path,
    fill_missing: Optional[float] = None,
) -> Dict[str, Path]:
    """
    Standard 2×2 heatmap template: two heatmaps (metric_a, metric_b) over the same
    (x_param, y_param) grid with consistent labeling and deterministic output paths.

    Use case: e.g. Sharpe + Max-Drawdown on the same parameter grid for quick
    side-by-side comparison. Missing grid points are left as NaN in the pivot
    (or filled with fill_missing if provided); plotting does not require a full grid.

    Args:
        df: DataFrame with sweep results (param_* and metric_* columns).
        x_param: Column name for the x-axis (with or without "param_" prefix).
        y_param: Column name for the y-axis (with or without "param_" prefix).
        metric_a: Column name for the first heatmap (with or without "metric_" prefix).
        metric_b: Column name for the second heatmap (with or without "metric_" prefix).
        sweep_name: Sweep identifier for filenames and logging.
        output_dir: Directory for output PNGs.
        fill_missing: Optional value to fill missing (x, y) cells before plotting.

    Returns:
        Dict with keys "metric_a" and "metric_b" mapping to the created PNG paths.
        Keys are omitted for metrics that could not be plotted (missing column or no data).

    Raises:
        ValueError: If any of the required columns are missing from df.
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("Matplotlib nicht verfügbar, überspringe 2×2 Heatmap-Template")
        return {}

    # Normalize column names
    x_col = x_param if x_param.startswith("param_") else f"param_{x_param}"
    y_col = y_param if y_param.startswith("param_") else f"param_{y_param}"
    ma_col = metric_a if metric_a.startswith("metric_") else f"metric_{metric_a}"
    mb_col = metric_b if metric_b.startswith("metric_") else f"metric_{metric_b}"

    for name, col in [("x_param", x_col), ("y_param", y_col), ("metric_a", ma_col), ("metric_b", mb_col)]:
        if col not in df.columns:
            raise ValueError(f"Spalte für {name} nicht gefunden: {col}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Deterministic filenames: same axis order and metric suffix
    x_clean = x_param.replace("param_", "")
    y_clean = y_param.replace("param_", "")
    ma_clean = metric_a.replace("metric_", "")
    mb_clean = metric_b.replace("metric_", "")

    base = f"{sweep_name}_heatmap_2x2_{x_clean}_x_{y_clean}"
    path_a = output_dir / f"{base}_{ma_clean}.png"
    path_b = output_dir / f"{base}_{mb_clean}.png"

    logger.info(
        "2×2 Heatmap-Template: x_param=%s, y_param=%s, metric_a=%s, metric_b=%s -> %s",
        x_clean, y_clean, ma_clean, mb_clean, output_dir,
    )

    result: Dict[str, Path] = {}

    # Build pivot once per metric; reuse shared logic for consistent layout
    for label, metric_col, out_path in [
        ("metric_a", ma_col, path_a),
        ("metric_b", mb_col, path_b),
    ]:
        df_sub = df[[x_col, y_col, metric_col]].dropna()
        if len(df_sub) == 0:
            logger.warning("Keine gültigen Daten für 2×2 Heatmap %s", label)
            continue

        pivot = df_sub.pivot_table(
            values=metric_col,
            index=y_col,
            columns=x_col,
            aggfunc="mean",
        )
        pivot = pivot.sort_index(axis=0).sort_index(axis=1)
        if fill_missing is not None:
            pivot = pivot.fillna(fill_missing)

        title = f"{metric_col.replace('metric_', '').replace('_', ' ').title()}: {x_clean} × {y_clean}"
        xlabel = x_clean.replace("_", " ").title()
        ylabel = y_clean.replace("_", " ").title()
        cbar_label = metric_col.replace("metric_", "").replace("_", " ").title()

        try:
            save_heatmap(
                pivot_df=pivot,
                output_path=out_path,
                title=title,
                xlabel=xlabel,
                ylabel=ylabel,
                cbar_label=cbar_label,
                annotate=pivot.size <= 100,
            )
            result[label] = out_path
            logger.info("2×2 Heatmap erstellt: %s -> %s", label, out_path)
        except Exception as e:
            logger.error("Fehler beim Erstellen der 2×2 Heatmap %s: %s", label, e)

    return result


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
            logger.warning(
                f"Weder {metric_primary} noch {metric_fallback} gefunden, verwende erste verfügbare Metrik: {metric_cols[0]}"
            )
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

    # Drawdown-Heatmaps: Automatisch erzeugen wenn max_drawdown vorhanden
    drawdown_metric_cols = [c for c in metric_cols if "drawdown" in c.lower()]
    if drawdown_metric_cols and len(param_candidates) >= 2:
        # Verwende erste gefundene Drawdown-Metrik
        drawdown_metric = drawdown_metric_cols[0]
        param_x = param_candidates[0]
        param_y = param_candidates[1]

        # Normalisiere
        if not param_x.startswith("param_"):
            param_x = f"param_{param_x}"
        if not param_y.startswith("param_"):
            param_y = f"param_{param_y}"

        if param_x in df.columns and param_y in df.columns:
            try:
                drawdown_heatmap_path = create_drawdown_heatmap(
                    df=df,
                    param_x=param_x,
                    param_y=param_y,
                    metric_col=drawdown_metric,
                    sweep_name=sweep_name,
                    output_dir=output_dir,
                )
                if drawdown_heatmap_path:
                    param_x_clean = param_x.replace("param_", "")
                    param_y_clean = param_y.replace("param_", "")
                    plots[f"drawdown_heatmap_{param_x_clean}_vs_{param_y_clean}"] = (
                        drawdown_heatmap_path
                    )
            except Exception as e:
                logger.warning(f"Fehler beim Erstellen der Drawdown-Heatmap: {e}")

    logger.info(f"Erstellt: {len(plots)} Plots für Sweep '{sweep_name}'")
    return plots
