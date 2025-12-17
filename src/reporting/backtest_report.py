# src/reporting/backtest_report.py
"""
Peak_Trade Backtest Reporting (Phase 30)
========================================

Funktionen zum Erstellen von Markdown-Reports für einzelne Backtests.

Komponenten:
- build_backtest_summary_section: Metriken-Tabelle als Section
- build_equity_plot: Equity-Curve als PNG
- build_drawdown_plot: Drawdown als PNG
- build_backtest_report: Kompletter Backtest-Report

Usage:
    from src.reporting.backtest_report import build_backtest_report

    report = build_backtest_report(
        title="MA Crossover Backtest",
        metrics={"sharpe": 1.5, "total_return": 0.15},
        equity_curve=equity_series,
        drawdown_series=dd_series,
    )
    report_md = report.to_markdown()
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd

from .base import Report, ReportSection, df_to_markdown, format_metric
from .plots import (
    save_drawdown_plot,
    save_equity_plot,
    save_equity_with_regime_overlay,
    save_equity_with_regimes,
    save_regime_contribution_bars,
)
from .regime_reporting import build_regime_report_section, compute_regime_stats

# =============================================================================
# SECTION BUILDERS
# =============================================================================


def build_backtest_summary_section(
    metrics: dict[str, float],
    title: str = "Performance Summary",
) -> ReportSection:
    """
    Erstellt eine Section mit Backtest-Kennzahlen als Markdown-Tabelle.

    Args:
        metrics: Dictionary mit Metrik-Namen und Werten
        title: Section-Titel

    Returns:
        ReportSection mit formatierter Tabelle

    Example:
        >>> metrics = {"total_return": 0.15, "sharpe": 1.5, "max_drawdown": -0.10}
        >>> section = build_backtest_summary_section(metrics)
        >>> print(section.to_markdown())
    """
    # Formatiere Metriken mit passender Darstellung
    formatted_metrics: dict[str, str] = {}
    for key, value in metrics.items():
        formatted_metrics[key] = format_metric(value, key)

    # Erstelle Markdown-Tabelle
    rows: list[str] = []
    header = "| Metric | Value |"
    separator = "|--------|-------|"
    rows.append(header)
    rows.append(separator)

    for key, value_str in formatted_metrics.items():
        # Formatiere Metrik-Namen lesbarer
        display_name = key.replace("_", " ").title()
        rows.append(f"| {display_name} | {value_str} |")

    content = "\n".join(rows)

    return ReportSection(title=title, content_markdown=content)


def build_trade_stats_section(
    trades: list[dict[str, Any]],
    title: str = "Trade Statistics",
) -> ReportSection:
    """
    Erstellt eine Section mit Trade-Statistiken.

    Args:
        trades: Liste von Trade-Dicts (mit 'pnl', optional 'side', 'symbol', 'entry_time', 'exit_time')
        title: Section-Titel

    Returns:
        ReportSection mit Trade-Übersicht
    """
    if not trades:
        return ReportSection(title=title, content_markdown="*No trades executed*")

    # Berechne Statistiken
    pnls = [t.get("pnl", 0) for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]

    total_trades = len(trades)
    winning_trades = len(wins)
    losing_trades = len(losses)
    win_rate = winning_trades / total_trades if total_trades > 0 else 0

    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0

    total_pnl = sum(pnls)
    avg_pnl = total_pnl / total_trades if total_trades > 0 else 0

    # Profit Factor
    gross_profits = sum(wins) if wins else 0
    gross_losses = abs(sum(losses)) if losses else 0
    profit_factor = gross_profits / gross_losses if gross_losses > 0 else 0

    # Markdown-Tabelle
    rows = [
        "| Statistic | Value |",
        "|-----------|-------|",
        f"| Total Trades | {total_trades} |",
        f"| Winning Trades | {winning_trades} |",
        f"| Losing Trades | {losing_trades} |",
        f"| Win Rate | {win_rate:.1%} |",
        f"| Average Win | {avg_win:.2f} |",
        f"| Average Loss | {avg_loss:.2f} |",
        f"| Total PnL | {total_pnl:.2f} |",
        f"| Average PnL/Trade | {avg_pnl:.2f} |",
        f"| Profit Factor | {profit_factor:.2f} |",
    ]

    return ReportSection(title=title, content_markdown="\n".join(rows))


def build_parameters_section(
    params: dict[str, Any],
    title: str = "Strategy Parameters",
) -> ReportSection:
    """
    Erstellt eine Section mit Strategie-Parametern.

    Args:
        params: Dictionary mit Parameter-Namen und Werten
        title: Section-Titel

    Returns:
        ReportSection mit Parameter-Tabelle
    """
    if not params:
        return ReportSection(title=title, content_markdown="*No parameters specified*")

    rows = [
        "| Parameter | Value |",
        "|-----------|-------|",
    ]
    for key, value in params.items():
        display_name = key.replace("_", " ").title()
        rows.append(f"| {display_name} | {value} |")

    return ReportSection(title=title, content_markdown="\n".join(rows))


# =============================================================================
# PLOT BUILDERS
# =============================================================================


def build_equity_plot(
    equity_curve: pd.Series,
    output_path: str | Path,
    title: str | None = "Equity Curve",
) -> str:
    """
    Erstellt einen Equity-Curve-Plot und speichert ihn.

    Args:
        equity_curve: Equity-Series (Portfolio-Wert über Zeit)
        output_path: Pfad für die PNG-Datei
        title: Plot-Titel

    Returns:
        Pfad zur gespeicherten PNG-Datei (relativ)

    Example:
        >>> equity = pd.Series([10000, 10100, 10050, 10200])
        >>> path = build_equity_plot(equity, "reports/images/equity.png")
    """
    return save_equity_plot(equity_curve, output_path, title=title)


def build_drawdown_plot(
    drawdown_series: pd.Series,
    output_path: str | Path,
    title: str | None = "Drawdown",
) -> str:
    """
    Erstellt einen Drawdown-Plot und speichert ihn.

    Args:
        drawdown_series: Drawdown-Series (Werte <= 0)
        output_path: Pfad für die PNG-Datei
        title: Plot-Titel

    Returns:
        Pfad zur gespeicherten PNG-Datei

    Example:
        >>> dd = pd.Series([0.0, -0.01, -0.05, -0.02])
        >>> path = build_drawdown_plot(dd, "reports/images/drawdown.png")
    """
    return save_drawdown_plot(drawdown_series, output_path, title=title)


# =============================================================================
# FULL REPORT BUILDER
# =============================================================================


def build_backtest_report(
    title: str,
    metrics: dict[str, float],
    equity_curve: pd.Series | None = None,
    drawdown_series: pd.Series | None = None,
    trades: list[dict[str, Any]] | None = None,
    params: dict[str, Any] | None = None,
    extra_tables: dict[str, pd.DataFrame] | None = None,
    regimes: pd.Series | None = None,
    output_dir: str | Path | None = None,
    metadata: dict[str, Any] | None = None,
) -> Report:
    """
    Erstellt einen kompletten Backtest-Report.

    Args:
        title: Report-Titel
        metrics: Backtest-Metriken (total_return, sharpe, max_drawdown, etc.)
        equity_curve: Optionale Equity-Series für Plot
        drawdown_series: Optionale Drawdown-Series für Plot
        trades: Optionale Trade-Liste für Trade-Stats
        params: Optionale Strategie-Parameter
        extra_tables: Optionale zusätzliche DataFrames für Report
        regimes: Optionale Regime-Series für Regime-Plot
        output_dir: Verzeichnis für Plot-Dateien (default: reports/images)
        metadata: Optionale Metadaten für Report

    Returns:
        Report-Objekt mit allen Sections

    Example:
        >>> report = build_backtest_report(
        ...     title="MA Crossover BTC/EUR",
        ...     metrics={"sharpe": 1.5, "total_return": 0.15},
        ...     equity_curve=equity_series,
        ...     params={"fast_period": 10, "slow_period": 50},
        ... )
        >>> with open("report.md", "w") as f:
        ...     f.write(report.to_markdown())
    """
    output_dir = Path(output_dir or "reports/images")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Erstelle Report
    report = Report(
        title=title,
        metadata=metadata or {},
    )

    # 1. Summary-Section
    report.add_section(build_backtest_summary_section(metrics))

    # 2. Parameters-Section
    if params:
        report.add_section(build_parameters_section(params))

    # 3. Trade-Stats-Section
    if trades:
        report.add_section(build_trade_stats_section(trades))

    # 4. Charts-Section
    charts_content: list[str] = []

    if equity_curve is not None and len(equity_curve) > 0:
        if regimes is not None and len(regimes) > 0:
            # Equity mit Regime-Bändern (numerische Regime-Werte)
            equity_path = output_dir / "equity_with_regimes.png"
            try:
                # Versuche numerische Regime-Werte (1/0/-1)
                regime_numeric = regimes.astype(float)
                if regime_numeric.isin([1.0, 0.0, -1.0]).all() or regime_numeric.isin([1, 0, -1]).all():
                    save_equity_with_regime_overlay(equity_curve, regimes, equity_path)
                else:
                    # Fallback zu String-Labels
                    save_equity_with_regimes(equity_curve, regimes, equity_path)
            except (ValueError, TypeError):
                # Fallback zu String-Labels
                save_equity_with_regimes(equity_curve, regimes, equity_path)
            rel_path = os.path.relpath(equity_path, output_dir.parent)
            charts_content.append(f"### Equity Curve with Regimes\n\n![Equity with Regimes]({rel_path})")
        else:
            # Standard Equity Plot
            equity_path = output_dir / "equity_curve.png"
            build_equity_plot(equity_curve, equity_path)
            rel_path = os.path.relpath(equity_path, output_dir.parent)
            charts_content.append(f"### Equity Curve\n\n![Equity Curve]({rel_path})")

    if drawdown_series is not None and len(drawdown_series) > 0:
        dd_path = output_dir / "drawdown.png"
        build_drawdown_plot(drawdown_series, dd_path)
        rel_path = os.path.relpath(dd_path, output_dir.parent)
        charts_content.append(f"### Drawdown\n\n![Drawdown]({rel_path})")

    if charts_content:
        report.add_section(
            ReportSection(
                title="Charts",
                content_markdown="\n\n".join(charts_content),
            )
        )

    # 5. Regime-Analyse (wenn Regime-Daten vorhanden)
    regime_stats = None
    if regimes is not None and len(regimes) > 0 and equity_curve is not None and len(equity_curve) > 0:
        try:
            # Berechne Returns aus Equity
            returns_series = equity_curve.pct_change().fillna(0)

            # Prüfe ob Regime-Series numerische Werte hat (1/0/-1)
            regime_numeric = regimes.astype(float)
            if regime_numeric.isin([1.0, 0.0, -1.0]).all() or regime_numeric.isin([1, 0, -1]).all():
                # Berechne Regime-Stats
                regime_stats = compute_regime_stats(
                    equity_series=equity_curve,
                    returns_series=returns_series,
                    regime_series=regimes,
                    trades=trades if trades else None,
                )

                # Erstelle Contribution-Plot
                contribution_plot_path = output_dir / "regime_contribution.png"
                try:
                    save_regime_contribution_bars(
                        regime_stats=regime_stats,
                        output_path=contribution_plot_path,
                        title="Return Contribution by Regime",
                    )
                    rel_contribution_path = os.path.relpath(contribution_plot_path, output_dir.parent)
                    charts_content.append(f"### Return Contribution by Regime\n\n![Regime Contribution]({rel_contribution_path})")
                except Exception:
                    # Plot-Fehler nicht kritisch, nur loggen
                    pass

                # Füge Regime-Section hinzu
                report.add_section(build_regime_report_section(regime_stats))
        except Exception as e:
            # Bei Fehler: füge Hinweis hinzu, aber breche nicht ab
            report.add_section(
                ReportSection(
                    title="Regime-Analyse",
                    content_markdown=f"*Regime-Analyse konnte nicht erstellt werden: {e}*",
                )
            )

    # 6. Extra Tables
    if extra_tables:
        for table_name, df in extra_tables.items():
            table_content = df_to_markdown(df, max_rows=50)
            report.add_section(
                ReportSection(
                    title=table_name,
                    content_markdown=table_content,
                )
            )

    return report


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def save_backtest_report(
    report: Report,
    output_path: str | Path,
    format: str = "markdown",
) -> str:
    """
    Speichert einen Backtest-Report als Datei.

    Args:
        report: Report-Objekt
        output_path: Ausgabe-Pfad
        format: "markdown" oder "html"

    Returns:
        Pfad zur gespeicherten Datei
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format == "html":
        content = report.to_html()
    else:
        content = report.to_markdown()

    output_path.write_text(content, encoding="utf-8")
    return str(output_path)


def build_quick_backtest_report(
    equity_curve: pd.Series,
    trades: list[dict[str, Any]] | None = None,
    strategy_name: str = "Strategy",
    symbol: str = "Unknown",
    params: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
) -> Report:
    """
    Schnelle Report-Generierung aus Equity-Curve.

    Berechnet automatisch Metriken aus der Equity-Curve.

    Args:
        equity_curve: Equity-Series
        trades: Optionale Trade-Liste
        strategy_name: Name der Strategie
        symbol: Gehandeltes Symbol
        params: Optionale Strategie-Parameter
        output_dir: Verzeichnis für Plot-Dateien

    Returns:
        Report-Objekt
    """
    from src.backtest.stats import compute_basic_stats, compute_drawdown

    # Berechne Metriken
    stats = compute_basic_stats(equity_curve)
    dd = compute_drawdown(equity_curve)

    # Trade-Stats wenn verfügbar
    if trades:
        from src.backtest.stats import compute_trade_stats

        trade_stats = compute_trade_stats(trades)
        stats["total_trades"] = trade_stats.total_trades
        stats["win_rate"] = trade_stats.win_rate
        stats["profit_factor"] = trade_stats.profit_factor

    return build_backtest_report(
        title=f"{strategy_name} Backtest - {symbol}",
        metrics=stats,
        equity_curve=equity_curve,
        drawdown_series=dd,
        trades=trades,
        params=params,
        output_dir=output_dir,
        metadata={
            "strategy": strategy_name,
            "symbol": symbol,
        },
    )
