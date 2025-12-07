# src/reporting/plots.py
"""
Peak_Trade Reporting Plots (Phase 30)
=====================================

Zentrale Plot-Helper für Backtest- und Experiment-Reports.

Alle Funktionen erzeugen PNG-Dateien und geben den Pfad zurück.
Nutzt nur Matplotlib (keine externen Abhängigkeiten).

Usage:
    from src.reporting.plots import save_line_plot, save_heatmap

    path = save_line_plot(equity_series, "reports/equity.png", title="Equity Curve")
    path = save_heatmap(pivot_df, "reports/heatmap.png", title="Sharpe by Parameters")
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import pandas as pd
import numpy as np

try:
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.colors import LinearSegmentedColormap

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None  # type: ignore


# =============================================================================
# PLOT CONFIGURATION
# =============================================================================

# Default figure size
DEFAULT_FIGSIZE = (12, 6)
DEFAULT_DPI = 150

# Color scheme
COLORS = {
    "primary": "#0d6efd",
    "success": "#198754",
    "danger": "#dc3545",
    "warning": "#ffc107",
    "secondary": "#6c757d",
    "light": "#f8f9fa",
    "dark": "#212529",
}


# =============================================================================
# LINE PLOTS
# =============================================================================


def save_line_plot(
    series: pd.Series,
    output_path: Union[str, Path],
    title: Optional[str] = None,
    ylabel: Optional[str] = None,
    xlabel: Optional[str] = None,
    figsize: Tuple[int, int] = DEFAULT_FIGSIZE,
    color: str = COLORS["primary"],
    fill: bool = True,
    reference_line: Optional[float] = None,
    dpi: int = DEFAULT_DPI,
) -> str:
    """
    Speichert einen einfachen Line-Plot als PNG.

    Args:
        series: Pandas Series mit Daten (Index wird für x-Achse verwendet)
        output_path: Pfad für die PNG-Datei
        title: Plot-Titel
        ylabel: Y-Achsen-Label
        xlabel: X-Achsen-Label
        figsize: Figure-Größe (width, height)
        color: Linienfarbe
        fill: Ob Fläche unter Linie gefüllt werden soll
        reference_line: Optionaler y-Wert für horizontale Referenzlinie
        dpi: Auflösung

    Returns:
        Pfad zur gespeicherten PNG-Datei

    Example:
        >>> equity = pd.Series([10000, 10100, 10050, 10200])
        >>> path = save_line_plot(equity, "reports/equity.png", title="Equity Curve")
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("Matplotlib is required for plotting")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(series.index, series.values, color=color, linewidth=1.5)

    if fill:
        ax.fill_between(series.index, series.values, alpha=0.1, color=color)

    if reference_line is not None:
        ax.axhline(
            reference_line,
            color=COLORS["secondary"],
            linestyle="--",
            linewidth=1,
            alpha=0.7,
            label=f"Reference: {reference_line}",
        )

    if title:
        ax.set_title(title)
    if ylabel:
        ax.set_ylabel(ylabel)
    if xlabel:
        ax.set_xlabel(xlabel)

    ax.grid(True, alpha=0.3)

    # Formatiere x-Achse für DatetimeIndex
    if isinstance(series.index, pd.DatetimeIndex):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return str(output_path)


def save_equity_plot(
    equity_curve: pd.Series,
    output_path: Union[str, Path],
    title: Optional[str] = "Equity Curve",
    show_start_line: bool = True,
    dpi: int = DEFAULT_DPI,
) -> str:
    """
    Speichert einen Equity-Curve-Plot.

    Args:
        equity_curve: Equity-Series (Portfolio-Wert über Zeit)
        output_path: Pfad für die PNG-Datei
        title: Plot-Titel
        show_start_line: Ob Startlinie angezeigt werden soll
        dpi: Auflösung

    Returns:
        Pfad zur gespeicherten PNG-Datei
    """
    reference = float(equity_curve.iloc[0]) if show_start_line else None
    return save_line_plot(
        series=equity_curve,
        output_path=output_path,
        title=title,
        ylabel="Equity",
        color=COLORS["primary"],
        fill=True,
        reference_line=reference,
        dpi=dpi,
    )


def save_drawdown_plot(
    drawdown_series: pd.Series,
    output_path: Union[str, Path],
    title: Optional[str] = "Drawdown",
    dpi: int = DEFAULT_DPI,
) -> str:
    """
    Speichert einen Drawdown-Plot.

    Args:
        drawdown_series: Drawdown-Series (Werte <= 0)
        output_path: Pfad für die PNG-Datei
        title: Plot-Titel
        dpi: Auflösung

    Returns:
        Pfad zur gespeicherten PNG-Datei
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("Matplotlib is required for plotting")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 4))

    ax.fill_between(
        drawdown_series.index,
        drawdown_series.values,
        0,
        color=COLORS["danger"],
        alpha=0.3,
    )
    ax.plot(
        drawdown_series.index,
        drawdown_series.values,
        color=COLORS["danger"],
        linewidth=1,
    )

    if title:
        ax.set_title(title)
    ax.set_ylabel("Drawdown")
    ax.grid(True, alpha=0.3)

    # Y-Achse als Prozent
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))

    if isinstance(drawdown_series.index, pd.DatetimeIndex):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return str(output_path)


# =============================================================================
# HEATMAP
# =============================================================================


def save_heatmap(
    pivot_df: pd.DataFrame,
    output_path: Union[str, Path],
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    cbar_label: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 8),
    cmap: str = "RdYlGn",
    dpi: int = DEFAULT_DPI,
    annotate: bool = True,
    fmt: str = ".2f",
) -> str:
    """
    Speichert eine Heatmap als PNG.

    Args:
        pivot_df: Pivot-DataFrame (Index = y-Achse, Columns = x-Achse, Values = Farbe)
        output_path: Pfad für die PNG-Datei
        title: Plot-Titel
        xlabel: X-Achsen-Label
        ylabel: Y-Achsen-Label
        cbar_label: Colorbar-Label
        figsize: Figure-Größe
        cmap: Matplotlib Colormap Name
        dpi: Auflösung
        annotate: Ob Werte in Zellen geschrieben werden sollen
        fmt: Format-String für Annotationen

    Returns:
        Pfad zur gespeicherten PNG-Datei

    Example:
        >>> pivot = df.pivot(index="param_slow", columns="param_fast", values="sharpe")
        >>> path = save_heatmap(pivot, "reports/heatmap.png", title="Sharpe Heatmap")
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("Matplotlib is required for plotting")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=figsize)

    # Heatmap erstellen
    im = ax.imshow(pivot_df.values, aspect="auto", cmap=cmap)

    # Colorbar
    cbar = fig.colorbar(im, ax=ax)
    if cbar_label:
        cbar.set_label(cbar_label)

    # Achsen-Labels
    ax.set_xticks(np.arange(len(pivot_df.columns)))
    ax.set_yticks(np.arange(len(pivot_df.index)))
    ax.set_xticklabels(pivot_df.columns)
    ax.set_yticklabels(pivot_df.index)

    # Rotiere x-Labels wenn viele
    if len(pivot_df.columns) > 5:
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)

    # Annotationen
    if annotate and pivot_df.size <= 100:  # Nur bei kleinen Heatmaps
        for i in range(len(pivot_df.index)):
            for j in range(len(pivot_df.columns)):
                val = pivot_df.iloc[i, j]
                if pd.notna(val):
                    text = format(val, fmt)
                    # Textfarbe basierend auf Hintergrund
                    color = "white" if val < pivot_df.values.mean() else "black"
                    ax.text(j, i, text, ha="center", va="center", color=color, fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return str(output_path)


# =============================================================================
# SCATTER PLOTS
# =============================================================================


def save_scatter_plot(
    x_values: Sequence[float],
    y_values: Sequence[float],
    output_path: Union[str, Path],
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 6),
    color: str = COLORS["primary"],
    dpi: int = DEFAULT_DPI,
    show_trend: bool = False,
) -> str:
    """
    Speichert einen Scatter-Plot als PNG.

    Args:
        x_values: X-Werte
        y_values: Y-Werte
        output_path: Pfad für die PNG-Datei
        title: Plot-Titel
        xlabel: X-Achsen-Label
        ylabel: Y-Achsen-Label
        figsize: Figure-Größe
        color: Punktfarbe
        dpi: Auflösung
        show_trend: Ob Trendlinie angezeigt werden soll

    Returns:
        Pfad zur gespeicherten PNG-Datei
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("Matplotlib is required for plotting")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=figsize)

    ax.scatter(
        x_values,
        y_values,
        alpha=0.6,
        c=color,
        s=50,
        edgecolors="black",
        linewidth=0.5,
    )

    if show_trend and len(x_values) > 2:
        # Lineare Regression
        z = np.polyfit(x_values, y_values, 1)
        p = np.poly1d(z)
        x_line = np.linspace(min(x_values), max(x_values), 100)
        ax.plot(x_line, p(x_line), "--", color=COLORS["danger"], linewidth=1.5, label="Trend")
        ax.legend()

    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)

    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return str(output_path)


# =============================================================================
# HISTOGRAM / DISTRIBUTION
# =============================================================================


def save_histogram(
    values: Sequence[float],
    output_path: Union[str, Path],
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: str = "Frequency",
    bins: int = 20,
    figsize: Tuple[int, int] = (10, 5),
    color: str = COLORS["primary"],
    dpi: int = DEFAULT_DPI,
    show_mean: bool = True,
    show_median: bool = False,
) -> str:
    """
    Speichert ein Histogramm als PNG.

    Args:
        values: Werte für das Histogramm
        output_path: Pfad für die PNG-Datei
        title: Plot-Titel
        xlabel: X-Achsen-Label
        ylabel: Y-Achsen-Label
        bins: Anzahl Bins
        figsize: Figure-Größe
        color: Balkenfarbe
        dpi: Auflösung
        show_mean: Ob Mittelwert-Linie angezeigt werden soll
        show_median: Ob Median-Linie angezeigt werden soll

    Returns:
        Pfad zur gespeicherten PNG-Datei
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("Matplotlib is required for plotting")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=figsize)

    ax.hist(values, bins=bins, edgecolor="black", alpha=0.7, color=color)

    if show_mean:
        mean_val = np.mean(values)
        ax.axvline(
            mean_val,
            color=COLORS["danger"],
            linestyle="--",
            linewidth=2,
            label=f"Mean: {mean_val:.3f}",
        )

    if show_median:
        median_val = np.median(values)
        ax.axvline(
            median_val,
            color=COLORS["success"],
            linestyle="-.",
            linewidth=2,
            label=f"Median: {median_val:.3f}",
        )

    if show_mean or show_median:
        ax.legend()

    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return str(output_path)


# =============================================================================
# REGIME BAND PLOT (optional)
# =============================================================================


def save_equity_with_regimes(
    equity_curve: pd.Series,
    regimes: pd.Series,
    output_path: Union[str, Path],
    title: Optional[str] = "Equity Curve with Regimes",
    regime_colors: Optional[Dict[str, str]] = None,
    dpi: int = DEFAULT_DPI,
) -> str:
    """
    Speichert Equity-Curve mit farblich markierten Regime-Perioden.

    Args:
        equity_curve: Equity-Series
        regimes: Series mit Regime-Labels (gleicher Index wie equity)
        output_path: Pfad für die PNG-Datei
        title: Plot-Titel
        regime_colors: Dict mit Regime-Name -> Farbe
        dpi: Auflösung

    Returns:
        Pfad zur gespeicherten PNG-Datei
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("Matplotlib is required for plotting")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Default-Farben für Regimes
    default_colors = {
        "bull": "#c8e6c9",  # light green
        "bear": "#ffcdd2",  # light red
        "sideways": "#e0e0e0",  # light gray
        "volatile": "#fff3e0",  # light orange
        "trending": "#bbdefb",  # light blue
    }
    colors = {**default_colors, **(regime_colors or {})}

    fig, ax = plt.subplots(figsize=(12, 6))

    # Equity-Kurve
    ax.plot(
        equity_curve.index,
        equity_curve.values,
        color=COLORS["primary"],
        linewidth=1.5,
        zorder=10,
    )

    # Regime-Bänder im Hintergrund
    unique_regimes = regimes.unique()
    for regime in unique_regimes:
        mask = regimes == regime
        regime_starts = mask.astype(int).diff().fillna(0) == 1
        regime_ends = mask.astype(int).diff().fillna(0) == -1

        starts = regimes.index[regime_starts].tolist()
        ends = regimes.index[regime_ends].tolist()

        # Falls am Anfang aktiv, füge Start hinzu
        if mask.iloc[0]:
            starts = [regimes.index[0]] + starts
        # Falls am Ende aktiv, füge Ende hinzu
        if mask.iloc[-1]:
            ends = ends + [regimes.index[-1]]

        color = colors.get(str(regime).lower(), "#e0e0e0")
        for start, end in zip(starts, ends):
            ax.axvspan(start, end, alpha=0.3, color=color, label=regime)

    # Legend (nur einzigartige Labels)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc="upper left")

    if title:
        ax.set_title(title)
    ax.set_ylabel("Equity")
    ax.grid(True, alpha=0.3)

    if isinstance(equity_curve.index, pd.DatetimeIndex):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return str(output_path)


def save_equity_with_regime_overlay(
    equity_curve: pd.Series,
    regime_series: pd.Series,
    output_path: Union[str, Path],
    title: Optional[str] = "Equity Curve with Regime Overlay",
    dpi: int = DEFAULT_DPI,
) -> str:
    """
    Speichert Equity-Curve mit farbigen Hintergrund-Bändern für Regime-Perioden.

    Optimiert für numerische Regime-Werte:
    - 1 = Risk-On (grün)
    - 0 = Neutral (grau)
    - -1 = Risk-Off (rot)

    Args:
        equity_curve: Equity-Series
        regime_series: Series mit numerischen Regime-Werten (1/0/-1)
        output_path: Pfad für die PNG-Datei
        title: Plot-Titel
        dpi: Auflösung

    Returns:
        Pfad zur gespeicherten PNG-Datei

    Example:
        >>> equity = pd.Series([10000, 10100, 10050, 10200])
        >>> regimes = pd.Series([1, 1, 0, -1])  # Risk-On, Risk-On, Neutral, Risk-Off
        >>> path = save_equity_with_regime_overlay(equity, regimes, "reports/equity_regime.png")
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("Matplotlib is required for plotting")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Regime-Farben für numerische Werte
    regime_colors = {
        1: "#c8e6c9",   # light green (Risk-On)
        0: "#e0e0e0",   # light gray (Neutral)
        -1: "#ffcdd2",  # light red (Risk-Off)
    }
    regime_labels = {
        1: "Risk-On",
        0: "Neutral",
        -1: "Risk-Off",
    }

    fig, ax = plt.subplots(figsize=(12, 6))

    # Equity-Kurve
    ax.plot(
        equity_curve.index,
        equity_curve.values,
        color=COLORS["primary"],
        linewidth=1.5,
        zorder=10,
        label="Equity",
    )

    # Aligniere Regime-Series mit Equity-Index
    regime_aligned = regime_series.reindex(equity_curve.index, method="ffill").fillna(0).astype(int)

    # Regime-Bänder im Hintergrund
    unique_regimes = sorted(regime_aligned.unique())
    legend_handles = []

    for regime_val in unique_regimes:
        mask = regime_aligned == regime_val
        if not mask.any():
            continue

        # Finde Regime-Perioden (Start/Ende)
        regime_changes = mask.astype(int).diff().fillna(0)
        starts = equity_curve.index[regime_changes == 1].tolist()
        ends = equity_curve.index[regime_changes == -1].tolist()

        # Falls am Anfang aktiv, füge Start hinzu
        if mask.iloc[0]:
            starts = [equity_curve.index[0]] + starts
        # Falls am Ende aktiv, füge Ende hinzu
        if mask.iloc[-1]:
            ends = ends + [equity_curve.index[-1]]

        # Zeichne Bänder
        color = regime_colors.get(regime_val, "#e0e0e0")
        label = regime_labels.get(regime_val, f"Regime {regime_val}")

        # Paare Start/Ende
        for i, start in enumerate(starts):
            if i < len(ends):
                end = ends[i]
            else:
                end = equity_curve.index[-1]

            # Nur zeichnen wenn Start < End
            if start <= end:
                ax.axvspan(start, end, alpha=0.2, color=color, zorder=0)

        # Legend-Eintrag (nur einmal)
        if starts:
            legend_handles.append(plt.Rectangle((0, 0), 1, 1, alpha=0.2, color=color, label=label))

    # Legend
    if legend_handles:
        ax.legend(handles=legend_handles, loc="upper left")

    if title:
        ax.set_title(title)
    ax.set_ylabel("Equity")
    ax.grid(True, alpha=0.3)

    if isinstance(equity_curve.index, pd.DatetimeIndex):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return str(output_path)


def save_regime_contribution_bars(
    regime_stats: Any,
    output_path: Union[str, Path],
    title: Optional[str] = "Return Contribution by Regime",
    dpi: int = DEFAULT_DPI,
) -> str:
    """
    Speichert einen Balken-Plot der Return-Contribution pro Regime.

    Args:
        regime_stats: RegimeStatsSummary mit Buckets (aus regime_reporting)
        output_path: Pfad für die PNG-Datei
        title: Plot-Titel
        dpi: Auflösung

    Returns:
        Pfad zur gespeicherten PNG-Datei

    Example:
        >>> from src.reporting.regime_reporting import RegimeStatsSummary, RegimeBucketMetrics
        >>> stats = RegimeStatsSummary(
        ...     buckets=[
        ...         RegimeBucketMetrics(..., return_contribution_pct=60.0, name="Risk-On"),
        ...         RegimeBucketMetrics(..., return_contribution_pct=30.0, name="Neutral"),
        ...         RegimeBucketMetrics(..., return_contribution_pct=10.0, name="Risk-Off"),
        ...     ],
        ...     overall_return=0.15,
        ...     overall_sharpe=1.5,
        ... )
        >>> path = save_regime_contribution_bars(stats, "reports/contribution.png")
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("Matplotlib is required for plotting")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Extrahiere Labels und Werte
    labels: List[str] = []
    values: List[float] = []

    for bucket in regime_stats.buckets:
        contrib = bucket.return_contribution_pct
        if contrib is None:
            continue
        labels.append(bucket.name)
        values.append(float(contrib))

    if not labels:
        # Wenn nichts sinnvoll geplottet werden kann, erstelle leeren Plot mit Hinweis
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No contribution data available", ha="center", va="center", transform=ax.transAxes)
        ax.set_title(title or "Return Contribution by Regime")
        plt.tight_layout()
        plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        return str(output_path)

    fig, ax = plt.subplots(figsize=(10, 5))

    # Farben basierend auf Regime-Namen
    colors = []
    for label in labels:
        if "Risk-On" in label or "risk_on" in label.lower():
            colors.append(COLORS["success"])  # Grün
        elif "Risk-Off" in label or "risk_off" in label.lower():
            colors.append(COLORS["danger"])  # Rot
        elif "Neutral" in label or "neutral" in label.lower():
            colors.append(COLORS["secondary"])  # Grau
        else:
            colors.append(COLORS["primary"])  # Blau

    bars = ax.bar(labels, values, color=colors, alpha=0.7, edgecolor="black", linewidth=1)

    # Werte auf Balken anzeigen
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + (1 if height >= 0 else -3),
            f"{value:.1f}%",
            ha="center",
            va="bottom" if height >= 0 else "top",
            fontsize=10,
            fontweight="bold",
        )

    ax.set_ylabel("Return Contribution [%]")
    ax.set_xlabel("Regime")
    if title:
        ax.set_title(title)

    # Nulllinie
    ax.axhline(0.0, color="black", linestyle="--", linewidth=0.8, alpha=0.5)

    ax.grid(True, alpha=0.3, axis="y")
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return str(output_path)
