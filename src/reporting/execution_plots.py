# src/reporting/execution_plots.py
"""
Peak_Trade: Execution Visualisierungen (Phase 16D)
===================================================

Optionale Visualisierungen fuer Execution-Daten aus Backtests.

Verwendet Matplotlib fuer leichtgewichtige Plots.
Alle Funktionen sind optional und scheitern graceful, wenn Matplotlib
nicht verfuegbar ist.

WICHTIG: Paper-only. Alle Daten stammen aus simulierten Backtests.
"""
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None  # type: ignore

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from src.orders.base import OrderExecutionResult

    from .execution_reports import ExecutionStats


def check_matplotlib() -> bool:
    """Prueft ob Matplotlib verfuegbar ist."""
    return MATPLOTLIB_AVAILABLE


def plot_slippage_histogram(
    slippages_bps: list[float],
    title: str = "Slippage Distribution",
    output_path: Path | None = None,
    bins: int = 20,
    figsize: tuple = (10, 6),
) -> Any | None:
    """
    Erstellt ein Histogramm der Slippage-Verteilung.

    Args:
        slippages_bps: Liste von Slippage-Werten in Basispunkten
        title: Plot-Titel
        output_path: Optionaler Pfad zum Speichern (PNG)
        bins: Anzahl Bins fuer das Histogramm
        figsize: Groesse der Figure

    Returns:
        Matplotlib Figure oder None bei Fehler
    """
    if not MATPLOTLIB_AVAILABLE:
        return None

    if not slippages_bps:
        return None

    fig, ax = plt.subplots(figsize=figsize)

    ax.hist(slippages_bps, bins=bins, edgecolor='black', alpha=0.7, color='steelblue')

    # Statistiken einzeichnen
    avg_slip = np.mean(slippages_bps)
    ax.axvline(avg_slip, color='red', linestyle='--', linewidth=2, label=f'Avg: {avg_slip:.2f} bps')

    ax.set_xlabel('Slippage (bps)')
    ax.set_ylabel('Frequency')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
        plt.close(fig)
    else:
        plt.close(fig)

    return fig


def plot_fee_histogram(
    fees: list[float],
    title: str = "Fee Distribution",
    output_path: Path | None = None,
    bins: int = 20,
    figsize: tuple = (10, 6),
) -> Any | None:
    """
    Erstellt ein Histogramm der Fee-Verteilung.

    Args:
        fees: Liste von Fee-Werten (EUR)
        title: Plot-Titel
        output_path: Optionaler Pfad zum Speichern (PNG)
        bins: Anzahl Bins
        figsize: Groesse der Figure

    Returns:
        Matplotlib Figure oder None bei Fehler
    """
    if not MATPLOTLIB_AVAILABLE:
        return None

    if not fees:
        return None

    fig, ax = plt.subplots(figsize=figsize)

    ax.hist(fees, bins=bins, edgecolor='black', alpha=0.7, color='green')

    avg_fee = np.mean(fees)
    ax.axvline(avg_fee, color='red', linestyle='--', linewidth=2, label=f'Avg: {avg_fee:.4f} EUR')

    ax.set_xlabel('Fee (EUR)')
    ax.set_ylabel('Frequency')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
        plt.close(fig)
    else:
        plt.close(fig)

    return fig


def plot_notional_histogram(
    notionals: list[float],
    title: str = "Trade Size Distribution",
    output_path: Path | None = None,
    bins: int = 20,
    figsize: tuple = (10, 6),
) -> Any | None:
    """
    Erstellt ein Histogramm der Trade-Groessen (Notional).

    Args:
        notionals: Liste von Notional-Werten (EUR)
        title: Plot-Titel
        output_path: Optionaler Pfad zum Speichern (PNG)
        bins: Anzahl Bins
        figsize: Groesse der Figure

    Returns:
        Matplotlib Figure oder None bei Fehler
    """
    if not MATPLOTLIB_AVAILABLE:
        return None

    if not notionals:
        return None

    fig, ax = plt.subplots(figsize=figsize)

    ax.hist(notionals, bins=bins, edgecolor='black', alpha=0.7, color='purple')

    avg_notional = np.mean(notionals)
    ax.axvline(avg_notional, color='red', linestyle='--', linewidth=2,
               label=f'Avg: {avg_notional:,.2f} EUR')

    ax.set_xlabel('Trade Size (EUR)')
    ax.set_ylabel('Frequency')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
        plt.close(fig)
    else:
        plt.close(fig)

    return fig


def plot_equity_with_trades(
    equity_curve: pd.Series,
    trades_df: pd.DataFrame | None = None,
    title: str = "Equity Curve with Trades",
    output_path: Path | None = None,
    figsize: tuple = (14, 8),
) -> Any | None:
    """
    Erstellt einen Equity-Kurven-Plot mit markierten Entry/Exit-Punkten.

    Args:
        equity_curve: Equity-Zeitreihe (pd.Series mit datetime Index)
        trades_df: Optionaler DataFrame mit Spalten:
                   - entry_time: Entry-Zeitpunkt
                   - exit_time: Exit-Zeitpunkt
                   - pnl: Profit/Loss des Trades
        title: Plot-Titel
        output_path: Optionaler Pfad zum Speichern (PNG)
        figsize: Groesse der Figure

    Returns:
        Matplotlib Figure oder None bei Fehler
    """
    if not MATPLOTLIB_AVAILABLE:
        return None

    if equity_curve is None or len(equity_curve) == 0:
        return None

    fig, ax = plt.subplots(figsize=figsize)

    # Equity-Kurve plotten
    ax.plot(equity_curve.index, equity_curve.values, color='blue', linewidth=1.5,
            label='Equity')

    # Trades markieren falls vorhanden
    if trades_df is not None and not trades_df.empty:
        for _, trade in trades_df.iterrows():
            entry_time = trade.get('entry_time')
            exit_time = trade.get('exit_time')
            pnl = trade.get('pnl', 0)

            # Entry markieren (gruen Dreieck nach oben)
            if entry_time and entry_time in equity_curve.index:
                entry_equity = equity_curve.loc[entry_time]
                ax.scatter([entry_time], [entry_equity], marker='^', color='green',
                          s=100, zorder=5)

            # Exit markieren (rot/gruen je nach PnL)
            if exit_time and exit_time in equity_curve.index:
                exit_equity = equity_curve.loc[exit_time]
                color = 'green' if pnl >= 0 else 'red'
                ax.scatter([exit_time], [exit_equity], marker='v', color=color,
                          s=100, zorder=5)

    ax.set_xlabel('Time')
    ax.set_ylabel('Equity (EUR)')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # X-Achse formatieren
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
        plt.close(fig)
    else:
        plt.close(fig)

    return fig


def plot_buy_sell_breakdown(
    stats: ExecutionStats,
    title: str = "Buy/Sell Breakdown",
    output_path: Path | None = None,
    figsize: tuple = (10, 6),
) -> Any | None:
    """
    Erstellt ein Balkendiagramm der Buy/Sell-Verteilung.

    Args:
        stats: ExecutionStats-Objekt
        title: Plot-Titel
        output_path: Optionaler Pfad zum Speichern (PNG)
        figsize: Groesse der Figure

    Returns:
        Matplotlib Figure oder None bei Fehler
    """
    if not MATPLOTLIB_AVAILABLE:
        return None

    if stats.n_buys == 0 and stats.n_sells == 0:
        return None

    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Linkes Diagramm: Anzahl Orders
    categories = ['Buys', 'Sells']
    counts = [stats.n_buys, stats.n_sells]
    colors = ['green', 'red']

    axes[0].bar(categories, counts, color=colors, alpha=0.7, edgecolor='black')
    axes[0].set_ylabel('Count')
    axes[0].set_title('Order Count')
    axes[0].grid(True, alpha=0.3, axis='y')

    for i, v in enumerate(counts):
        axes[0].text(i, v + 0.5, str(v), ha='center', fontweight='bold')

    # Rechtes Diagramm: Volumen
    volumes = [stats.buy_volume, stats.sell_volume]

    axes[1].bar(categories, volumes, color=colors, alpha=0.7, edgecolor='black')
    axes[1].set_ylabel('Volume (EUR)')
    axes[1].set_title('Volume')
    axes[1].grid(True, alpha=0.3, axis='y')

    for i, v in enumerate(volumes):
        axes[1].text(i, v + max(volumes) * 0.02, f'{v:,.0f}', ha='center', fontweight='bold')

    fig.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
        plt.close(fig)
    else:
        plt.close(fig)

    return fig


def plot_execution_summary(
    stats: ExecutionStats,
    title: str = "Execution Summary",
    output_path: Path | None = None,
    figsize: tuple = (12, 8),
) -> Any | None:
    """
    Erstellt eine zusammenfassende Visualisierung der Execution-Stats.

    Kombiniert mehrere Metriken in einem Figure:
    - Fill-Rate (Pie)
    - Fee-Breakdown (Bar)
    - Key Metrics (Text)

    Args:
        stats: ExecutionStats-Objekt
        title: Plot-Titel
        output_path: Optionaler Pfad zum Speichern (PNG)
        figsize: Groesse der Figure

    Returns:
        Matplotlib Figure oder None bei Fehler
    """
    if not MATPLOTLIB_AVAILABLE:
        return None

    fig = plt.figure(figsize=figsize)

    # Layout: 2x2 Grid
    # Top-left: Fill-Rate Pie
    ax1 = fig.add_subplot(2, 2, 1)
    if stats.n_orders > 0:
        sizes = [stats.n_fills, stats.n_rejected]
        labels = [f'Filled ({stats.n_fills})', f'Rejected ({stats.n_rejected})']
        colors = ['green', 'red']
        ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Fill Rate')
    else:
        ax1.text(0.5, 0.5, 'No Orders', ha='center', va='center', fontsize=14)
        ax1.set_title('Fill Rate')

    # Top-right: Fees & Slippage Bar
    ax2 = fig.add_subplot(2, 2, 2)
    metrics = ['Total Fees', 'Total Slippage']
    values = [stats.total_fees, stats.total_slippage]
    bars = ax2.bar(metrics, values, color=['orange', 'purple'], alpha=0.7, edgecolor='black')
    ax2.set_ylabel('EUR')
    ax2.set_title('Costs')
    ax2.grid(True, alpha=0.3, axis='y')

    for bar, v in zip(bars, values, strict=False):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.02,
                f'{v:.2f}', ha='center', fontsize=10)

    # Bottom-left: Key Metrics Text
    ax3 = fig.add_subplot(2, 2, 3)
    ax3.axis('off')

    metrics_text = [
        f"Total Orders: {stats.n_orders}",
        f"Total Fills: {stats.n_fills}",
        f"Fill Rate: {stats.fill_rate:.1%}",
        "",
        f"Total Notional: {stats.total_notional:,.2f} EUR",
        f"Avg Trade Size: {stats.avg_trade_notional:,.2f} EUR",
        "",
        f"Total Fees: {stats.total_fees:.2f} EUR",
        f"Fee Rate: {stats.fee_rate_bps:.2f} bps",
        "",
        f"Avg Slippage: {stats.avg_slippage_bps:.2f} bps",
        f"Hit Rate: {stats.hit_rate:.1%}",
    ]

    ax3.text(0.1, 0.9, '\n'.join(metrics_text), transform=ax3.transAxes,
             fontsize=11, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.3))
    ax3.set_title('Key Metrics')

    # Bottom-right: Buy/Sell Volumes
    ax4 = fig.add_subplot(2, 2, 4)
    if stats.n_buys > 0 or stats.n_sells > 0:
        categories = ['Buy Volume', 'Sell Volume']
        volumes = [stats.buy_volume, stats.sell_volume]
        colors = ['green', 'red']
        bars = ax4.bar(categories, volumes, color=colors, alpha=0.7, edgecolor='black')
        ax4.set_ylabel('EUR')
        ax4.set_title('Volume Split')
        ax4.grid(True, alpha=0.3, axis='y')

        for bar, v in zip(bars, volumes, strict=False):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(volumes)*0.02,
                    f'{v:,.0f}', ha='center', fontsize=10)
    else:
        ax4.text(0.5, 0.5, 'No Trades', ha='center', va='center', fontsize=14)
        ax4.set_title('Volume Split')

    fig.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
        plt.close(fig)
    else:
        plt.close(fig)

    return fig


def extract_slippages_from_results(
    results: Sequence[OrderExecutionResult],
    reference_prices: dict[str, float] | None = None,
) -> list[float]:
    """
    Extrahiert Slippage-Werte aus OrderExecutionResults.

    Args:
        results: Liste von OrderExecutionResult
        reference_prices: Optionale Referenzpreise

    Returns:
        Liste von Slippage-Werten in bps
    """
    slippages: list[float] = []

    for result in results:
        if not result.is_filled or not result.fill:
            continue

        req = result.request
        fill = result.fill

        # Referenzpreis ermitteln
        ref_price: float | None = None
        if reference_prices and req.symbol in reference_prices:
            ref_price = reference_prices[req.symbol]
        if ref_price is None:
            ref_price = req.metadata.get("signal_price")
        if ref_price is None:
            ref_price = result.metadata.get("reference_price")

        if ref_price and ref_price > 0:
            if fill.side == "buy":
                slip_bps = (fill.price - ref_price) / ref_price * 10_000
            else:
                slip_bps = (ref_price - fill.price) / ref_price * 10_000
            slippages.append(slip_bps)

    return slippages


def extract_fees_from_results(results: Sequence[OrderExecutionResult]) -> list[float]:
    """
    Extrahiert Fee-Werte aus OrderExecutionResults.

    Args:
        results: Liste von OrderExecutionResult

    Returns:
        Liste von Fee-Werten (EUR)
    """
    fees: list[float] = []

    for result in results:
        if result.is_filled and result.fill and result.fill.fee:
            fees.append(result.fill.fee)

    return fees


def extract_notionals_from_results(results: Sequence[OrderExecutionResult]) -> list[float]:
    """
    Extrahiert Notional-Werte aus OrderExecutionResults.

    Args:
        results: Liste von OrderExecutionResult

    Returns:
        Liste von Notional-Werten (EUR)
    """
    notionals: list[float] = []

    for result in results:
        if result.is_filled and result.fill:
            notional = result.fill.quantity * result.fill.price
            notionals.append(notional)

    return notionals
