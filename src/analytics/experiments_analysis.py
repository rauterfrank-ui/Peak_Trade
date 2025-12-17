# src/analytics/experiments_analysis.py
"""
Peak_Trade – Experiment-Analyse-Funktionen
==========================================
Aggregations- und Analysefunktionen für die Experiment-Registry.

Bietet:
- StrategySummary Dataclass für Strategie-Übersichten
- Funktionen zum Filtern, Aggregieren und Vergleichen von Runs
- Report-Generierung (Markdown)

Usage:
    from src.analytics.experiments_analysis import (
        load_experiments_df_filtered,
        summarize_strategies,
        top_runs_by_metric,
        write_markdown_report,
    )
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.core.experiments import load_experiments_df


@dataclass
class StrategySummary:
    """
    Aggregierte Zusammenfassung für eine Strategie.

    Attributes:
        strategy_key: Name der Strategie
        run_count: Anzahl der Runs
        avg_total_return: Durchschnittliche Rendite
        avg_sharpe: Durchschnittlicher Sharpe Ratio
        avg_max_drawdown: Durchschnittlicher Max Drawdown
        best_run_id: Run-ID mit bestem total_return
        worst_run_id: Run-ID mit schlechtestem total_return
        best_sharpe_run_id: Run-ID mit bestem Sharpe
    """

    strategy_key: str
    run_count: int = 0
    avg_total_return: float = 0.0
    avg_sharpe: float = 0.0
    avg_max_drawdown: float = 0.0
    best_run_id: str | None = None
    worst_run_id: str | None = None
    best_sharpe_run_id: str | None = None


@dataclass
class PortfolioSummary:
    """
    Aggregierte Zusammenfassung für ein Portfolio.

    Attributes:
        portfolio_name: Name des Portfolios
        run_count: Anzahl der Runs
        avg_total_return: Durchschnittliche Rendite
        avg_sharpe: Durchschnittlicher Sharpe Ratio
        avg_max_drawdown: Durchschnittlicher Max Drawdown
        best_run_id: Run-ID mit bestem total_return
    """

    portfolio_name: str
    run_count: int = 0
    avg_total_return: float = 0.0
    avg_sharpe: float = 0.0
    avg_max_drawdown: float = 0.0
    best_run_id: str | None = None


# =============================================================================
# LADEN & FILTERN
# =============================================================================


def load_experiments_df_filtered(
    *,
    run_types: Sequence[str] | None = None,
    strategy_keys: Sequence[str] | None = None,
    symbols: Sequence[str] | None = None,
    portfolios: Sequence[str] | None = None,
    tags: Sequence[str] | None = None,
) -> pd.DataFrame:
    """
    Lädt alle Experiments und filtert nach verschiedenen Kriterien.

    Args:
        run_types: Liste von run_type-Werten (z.B. ["backtest", "portfolio_backtest"])
        strategy_keys: Liste von Strategie-Keys (z.B. ["ma_crossover", "rsi_reversion"])
        symbols: Liste von Symbolen (z.B. ["BTC/EUR", "ETH/EUR"])
        portfolios: Liste von Portfolio-Namen
        tags: Liste von Tags (aus metadata_json)

    Returns:
        Gefiltertes DataFrame mit Experiments

    Raises:
        FileNotFoundError: Wenn keine Registry existiert
    """
    import json

    df = load_experiments_df()

    # Run-Type-Filter
    if run_types is not None and "run_type" in df.columns:
        df = df[df["run_type"].isin(run_types)]

    # Strategy-Filter
    if strategy_keys is not None and "strategy_key" in df.columns:
        df = df[df["strategy_key"].isin(strategy_keys)]

    # Symbol-Filter
    if symbols is not None and "symbol" in df.columns:
        df = df[df["symbol"].isin(symbols)]

    # Portfolio-Filter
    if portfolios is not None and "portfolio_name" in df.columns:
        df = df[df["portfolio_name"].isin(portfolios)]

    # Tag-Filter (aus metadata_json)
    if tags is not None and "metadata_json" in df.columns:

        def get_tag(meta_json: str) -> str | None:
            try:
                meta = json.loads(meta_json)
                return meta.get("tag")
            except (json.JSONDecodeError, TypeError):
                return None

        df["_tag"] = df["metadata_json"].apply(get_tag)
        df = df[df["_tag"].isin(tags)]
        df = df.drop(columns=["_tag"])

    return df.copy()


def filter_backtest_runs(df: pd.DataFrame) -> pd.DataFrame:
    """Filtert nur Backtest-Runs."""
    if "run_type" not in df.columns:
        return df
    return df[df["run_type"] == "backtest"].copy()


def filter_portfolio_backtest_runs(df: pd.DataFrame) -> pd.DataFrame:
    """Filtert nur Portfolio-Backtest-Runs."""
    if "run_type" not in df.columns:
        return df
    return df[df["run_type"] == "portfolio_backtest"].copy()


# =============================================================================
# AGGREGATION & ANALYSE
# =============================================================================


def summarize_strategies(df: pd.DataFrame) -> list[StrategySummary]:
    """
    Aggregiert Backtests pro strategy_key.

    Args:
        df: DataFrame mit Experiment-Daten
            Erwartet Spalten: strategy_key, total_return, sharpe, max_drawdown, run_id

    Returns:
        Liste von StrategySummary-Objekten, sortiert nach avg_sharpe (desc)
    """
    if df.empty or "strategy_key" not in df.columns:
        return []

    # Nur Rows mit strategy_key
    df_with_strat = df[df["strategy_key"].notna()].copy()
    if df_with_strat.empty:
        return []

    summaries = []

    for strat_key, group in df_with_strat.groupby("strategy_key"):
        run_count = len(group)

        # Durchschnitte berechnen
        avg_return = (
            group["total_return"].astype(float).mean()
            if "total_return" in group.columns
            else 0.0
        )
        avg_sharpe = (
            group["sharpe"].astype(float).mean()
            if "sharpe" in group.columns
            else 0.0
        )
        avg_dd = (
            group["max_drawdown"].astype(float).mean()
            if "max_drawdown" in group.columns
            else 0.0
        )

        # Best/Worst Run
        best_run_id = None
        worst_run_id = None
        best_sharpe_run_id = None

        if "total_return" in group.columns and "run_id" in group.columns:
            tr_numeric = pd.to_numeric(group["total_return"], errors="coerce")
            valid_tr = group[tr_numeric.notna()]
            if not valid_tr.empty:
                best_idx = tr_numeric[tr_numeric.notna()].idxmax()
                worst_idx = tr_numeric[tr_numeric.notna()].idxmin()
                best_run_id = group.loc[best_idx, "run_id"]
                worst_run_id = group.loc[worst_idx, "run_id"]

        if "sharpe" in group.columns and "run_id" in group.columns:
            sh_numeric = pd.to_numeric(group["sharpe"], errors="coerce")
            valid_sh = group[sh_numeric.notna()]
            if not valid_sh.empty:
                best_sh_idx = sh_numeric[sh_numeric.notna()].idxmax()
                best_sharpe_run_id = group.loc[best_sh_idx, "run_id"]

        summaries.append(
            StrategySummary(
                strategy_key=str(strat_key),
                run_count=run_count,
                avg_total_return=float(avg_return) if pd.notna(avg_return) else 0.0,
                avg_sharpe=float(avg_sharpe) if pd.notna(avg_sharpe) else 0.0,
                avg_max_drawdown=float(avg_dd) if pd.notna(avg_dd) else 0.0,
                best_run_id=best_run_id,
                worst_run_id=worst_run_id,
                best_sharpe_run_id=best_sharpe_run_id,
            )
        )

    # Sortieren nach avg_sharpe (absteigend)
    summaries.sort(key=lambda s: s.avg_sharpe, reverse=True)
    return summaries


def summarize_portfolios(df: pd.DataFrame) -> list[PortfolioSummary]:
    """
    Aggregiert Portfolio-Backtests pro portfolio_name.

    Args:
        df: DataFrame mit Experiment-Daten
            Erwartet Spalten: portfolio_name, total_return, sharpe, max_drawdown, run_id

    Returns:
        Liste von PortfolioSummary-Objekten, sortiert nach avg_sharpe (desc)
    """
    if df.empty or "portfolio_name" not in df.columns:
        return []

    # Nur Rows mit portfolio_name
    df_with_port = df[df["portfolio_name"].notna()].copy()
    if df_with_port.empty:
        return []

    summaries = []

    for port_name, group in df_with_port.groupby("portfolio_name"):
        run_count = len(group)

        avg_return = (
            group["total_return"].astype(float).mean()
            if "total_return" in group.columns
            else 0.0
        )
        avg_sharpe = (
            group["sharpe"].astype(float).mean()
            if "sharpe" in group.columns
            else 0.0
        )
        avg_dd = (
            group["max_drawdown"].astype(float).mean()
            if "max_drawdown" in group.columns
            else 0.0
        )

        best_run_id = None
        if "total_return" in group.columns and "run_id" in group.columns:
            tr_numeric = pd.to_numeric(group["total_return"], errors="coerce")
            valid_tr = group[tr_numeric.notna()]
            if not valid_tr.empty:
                best_idx = tr_numeric[tr_numeric.notna()].idxmax()
                best_run_id = group.loc[best_idx, "run_id"]

        summaries.append(
            PortfolioSummary(
                portfolio_name=str(port_name),
                run_count=run_count,
                avg_total_return=float(avg_return) if pd.notna(avg_return) else 0.0,
                avg_sharpe=float(avg_sharpe) if pd.notna(avg_sharpe) else 0.0,
                avg_max_drawdown=float(avg_dd) if pd.notna(avg_dd) else 0.0,
                best_run_id=best_run_id,
            )
        )

    summaries.sort(key=lambda s: s.avg_sharpe, reverse=True)
    return summaries


def top_runs_by_metric(
    df: pd.DataFrame,
    metric: str = "total_return",
    n: int = 20,
    ascending: bool = False,
) -> pd.DataFrame:
    """
    Gibt die Top-N Runs nach einer bestimmten Metrik zurück.

    Args:
        df: DataFrame mit Experiment-Daten
        metric: Spaltenname für Sortierung (z.B. "total_return", "sharpe", "max_drawdown")
        n: Anzahl der Top-Runs
        ascending: False für "höher ist besser", True für "niedriger ist besser"

    Returns:
        DataFrame mit Top-N Runs
    """
    if df.empty or metric not in df.columns:
        return df.head(0)

    # Nur Rows mit numerischen Werten für die Metrik
    df_numeric = df.copy()
    df_numeric[metric] = pd.to_numeric(df_numeric[metric], errors="coerce")
    df_numeric = df_numeric[df_numeric[metric].notna()]

    if df_numeric.empty:
        return df.head(0)

    df_sorted = df_numeric.sort_values(by=metric, ascending=ascending)
    return df_sorted.head(n)


def compare_strategies(
    df: pd.DataFrame,
    strategies: Sequence[str],
    metrics: Sequence[str] = ("total_return", "sharpe", "max_drawdown"),
) -> pd.DataFrame:
    """
    Vergleicht mehrere Strategien anhand ausgewählter Metriken.

    Args:
        df: DataFrame mit Experiment-Daten
        strategies: Liste von strategy_key-Werten zum Vergleich
        metrics: Tuple von Metriken für den Vergleich

    Returns:
        DataFrame mit Vergleich (Index: strategy_key, Columns: metrics)
    """
    if df.empty or "strategy_key" not in df.columns:
        return pd.DataFrame()

    df_filtered = df[df["strategy_key"].isin(strategies)].copy()
    if df_filtered.empty:
        return pd.DataFrame()

    result = []
    for strat in strategies:
        strat_df = df_filtered[df_filtered["strategy_key"] == strat]
        row = {"strategy_key": strat, "run_count": len(strat_df)}

        for metric in metrics:
            if metric in strat_df.columns:
                values = pd.to_numeric(strat_df[metric], errors="coerce")
                row[f"avg_{metric}"] = values.mean()
                row[f"std_{metric}"] = values.std()
                row[f"min_{metric}"] = values.min()
                row[f"max_{metric}"] = values.max()

        result.append(row)

    return pd.DataFrame(result)


# =============================================================================
# REPORT-GENERIERUNG
# =============================================================================


def write_markdown_report(
    summaries: list[StrategySummary],
    path: Path,
    *,
    title: str = "Peak_Trade Strategy Report",
    run_type: str | None = None,
) -> None:
    """
    Schreibt eine Markdown-Übersicht der StrategySummary-Liste.

    Args:
        summaries: Liste von StrategySummary-Objekten
        path: Pfad zur Markdown-Datei
        title: Titel des Reports
        run_type: Optional: Run-Type für Untertitel
    """
    from datetime import datetime

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"Generiert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    if run_type:
        lines.append(f"Run-Type: `{run_type}`")
        lines.append("")

    lines.append("## Strategie-Übersicht")
    lines.append("")

    if not summaries:
        lines.append("*Keine Strategien gefunden.*")
    else:
        # Tabellen-Header
        lines.append(
            "| Strategy Key | Runs | Avg Return | Avg Sharpe | Avg MaxDD | Best Run |"
        )
        lines.append(
            "|--------------|------|------------|------------|-----------|----------|"
        )

        for s in summaries:
            avg_ret = f"{s.avg_total_return:.2%}" if s.avg_total_return else "-"
            avg_sh = f"{s.avg_sharpe:.2f}" if s.avg_sharpe else "-"
            avg_dd = f"{s.avg_max_drawdown:.2%}" if s.avg_max_drawdown else "-"
            best_id = s.best_run_id[:8] + "..." if s.best_run_id else "-"

            lines.append(
                f"| {s.strategy_key} | {s.run_count} | {avg_ret} | {avg_sh} | {avg_dd} | {best_id} |"
            )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Report erstellt mit Peak_Trade Analytics*")

    path.write_text("\n".join(lines), encoding="utf-8")


def write_portfolio_markdown_report(
    summaries: list[PortfolioSummary],
    path: Path,
    *,
    title: str = "Peak_Trade Portfolio Report",
) -> None:
    """
    Schreibt eine Markdown-Übersicht der PortfolioSummary-Liste.

    Args:
        summaries: Liste von PortfolioSummary-Objekten
        path: Pfad zur Markdown-Datei
        title: Titel des Reports
    """
    from datetime import datetime

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"Generiert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## Portfolio-Übersicht")
    lines.append("")

    if not summaries:
        lines.append("*Keine Portfolios gefunden.*")
    else:
        lines.append(
            "| Portfolio Name | Runs | Avg Return | Avg Sharpe | Avg MaxDD | Best Run |"
        )
        lines.append(
            "|----------------|------|------------|------------|-----------|----------|"
        )

        for s in summaries:
            avg_ret = f"{s.avg_total_return:.2%}" if s.avg_total_return else "-"
            avg_sh = f"{s.avg_sharpe:.2f}" if s.avg_sharpe else "-"
            avg_dd = f"{s.avg_max_drawdown:.2%}" if s.avg_max_drawdown else "-"
            best_id = s.best_run_id[:8] + "..." if s.best_run_id else "-"

            lines.append(
                f"| {s.portfolio_name} | {s.run_count} | {avg_ret} | {avg_sh} | {avg_dd} | {best_id} |"
            )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Report erstellt mit Peak_Trade Analytics*")

    path.write_text("\n".join(lines), encoding="utf-8")


# =============================================================================
# SWEEP & MARKET-SCAN ANALYSE
# =============================================================================


def filter_sweeps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtert nur Sweep-Runs aus dem DataFrame.

    Args:
        df: DataFrame mit Experiment-Daten

    Returns:
        DataFrame nur mit run_type="sweep"
    """
    if "run_type" not in df.columns:
        return df.head(0)
    return df[df["run_type"] == "sweep"].copy()


def filter_market_scans(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtert nur Market-Scan-Runs aus dem DataFrame.

    Args:
        df: DataFrame mit Experiment-Daten

    Returns:
        DataFrame nur mit run_type="market_scan"
    """
    if "run_type" not in df.columns:
        return df.head(0)
    return df[df["run_type"] == "market_scan"].copy()


@dataclass
class SweepSummary:
    """
    Aggregierte Zusammenfassung für einen Sweep.

    Attributes:
        sweep_name: Name des Sweeps
        strategy_key: Name der Strategie
        run_count: Anzahl der Runs
        best_sharpe: Bester Sharpe Ratio
        best_return: Beste Rendite
        best_params: Parameter der besten Kombination (nach Sharpe)
        best_run_id: Run-ID der besten Kombination
    """

    sweep_name: str
    strategy_key: str
    run_count: int = 0
    best_sharpe: float = 0.0
    best_return: float = 0.0
    best_params: dict[str, Any] | None = None
    best_run_id: str | None = None


def summarize_sweeps(df: pd.DataFrame) -> list[SweepSummary]:
    """
    Aggregiert Sweep-Ergebnisse pro sweep_name.

    Args:
        df: DataFrame mit Sweep-Daten (gefiltert auf run_type="sweep")

    Returns:
        Liste von SweepSummary-Objekten, sortiert nach best_sharpe (desc)
    """
    import json

    df_sweeps = filter_sweeps(df)
    if df_sweeps.empty or "sweep_name" not in df_sweeps.columns:
        return []

    df_with_sweep = df_sweeps[df_sweeps["sweep_name"].notna()].copy()
    if df_with_sweep.empty:
        return []

    summaries = []

    for sweep_name, group in df_with_sweep.groupby("sweep_name"):
        run_count = len(group)

        # Beste Kombination nach Sharpe finden
        sharpe_col = pd.to_numeric(group["sharpe"], errors="coerce")
        best_idx = sharpe_col.idxmax() if sharpe_col.notna().any() else None

        best_sharpe = 0.0
        best_return = 0.0
        best_params = None
        best_run_id = None
        strategy_key = str(group["strategy_key"].iloc[0]) if "strategy_key" in group.columns else ""

        if best_idx is not None:
            best_row = group.loc[best_idx]
            best_sharpe = float(best_row.get("sharpe", 0) or 0)
            best_return = float(best_row.get("total_return", 0) or 0)
            best_run_id = str(best_row.get("run_id", ""))

            # Parameter aus params_json extrahieren
            try:
                params_json = best_row.get("params_json", "{}")
                best_params = json.loads(params_json) if params_json else {}
            except (json.JSONDecodeError, TypeError):
                best_params = {}

        summaries.append(
            SweepSummary(
                sweep_name=str(sweep_name),
                strategy_key=strategy_key,
                run_count=run_count,
                best_sharpe=best_sharpe,
                best_return=best_return,
                best_params=best_params,
                best_run_id=best_run_id,
            )
        )

    summaries.sort(key=lambda s: s.best_sharpe, reverse=True)
    return summaries


@dataclass
class MarketScanSummary:
    """
    Aggregierte Zusammenfassung für einen Market-Scan.

    Attributes:
        scan_name: Name des Scans
        strategy_key: Name der Strategie
        run_count: Anzahl der gescannten Symbole
        long_signals: Anzahl der LONG-Signale
        short_signals: Anzahl der SHORT-Signale
        flat_signals: Anzahl der FLAT-Signale
        top_symbol: Symbol mit stärkstem Signal
        top_signal: Wert des stärksten Signals
    """

    scan_name: str
    strategy_key: str
    run_count: int = 0
    long_signals: int = 0
    short_signals: int = 0
    flat_signals: int = 0
    top_symbol: str | None = None
    top_signal: float = 0.0


def summarize_market_scans(df: pd.DataFrame) -> list[MarketScanSummary]:
    """
    Aggregiert Market-Scan-Ergebnisse pro scan_name.

    Args:
        df: DataFrame mit Market-Scan-Daten

    Returns:
        Liste von MarketScanSummary-Objekten
    """
    import json

    df_scans = filter_market_scans(df)
    if df_scans.empty or "scan_name" not in df_scans.columns:
        return []

    df_with_scan = df_scans[df_scans["scan_name"].notna()].copy()
    if df_with_scan.empty:
        return []

    summaries = []

    for scan_name, group in df_with_scan.groupby("scan_name"):
        run_count = len(group)
        strategy_key = str(group["strategy_key"].iloc[0]) if "strategy_key" in group.columns else ""

        # Signale aus stats_json extrahieren
        long_signals = 0
        short_signals = 0
        flat_signals = 0
        top_symbol = None
        top_signal = 0.0

        for _, row in group.iterrows():
            try:
                stats_json = row.get("stats_json", "{}")
                stats = json.loads(stats_json) if stats_json else {}
                signal = stats.get("last_signal", 0)

                if signal > 0:
                    long_signals += 1
                elif signal < 0:
                    short_signals += 1
                else:
                    flat_signals += 1

                if abs(signal) > abs(top_signal):
                    top_signal = signal
                    top_symbol = row.get("symbol")

            except (json.JSONDecodeError, TypeError):
                flat_signals += 1

        summaries.append(
            MarketScanSummary(
                scan_name=str(scan_name),
                strategy_key=strategy_key,
                run_count=run_count,
                long_signals=long_signals,
                short_signals=short_signals,
                flat_signals=flat_signals,
                top_symbol=top_symbol,
                top_signal=top_signal,
            )
        )

    return summaries


def write_top_runs_markdown_report(
    df: pd.DataFrame,
    path: Path,
    *,
    title: str = "Peak_Trade Top Runs",
    metric: str = "total_return",
) -> None:
    """
    Schreibt eine Markdown-Übersicht der Top-Runs.

    Args:
        df: DataFrame mit Top-Runs
        path: Pfad zur Markdown-Datei
        title: Titel des Reports
        metric: Metrik für Sortierung
    """
    from datetime import datetime

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"Generiert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Sortiert nach: `{metric}`")
    lines.append("")
    lines.append("## Top Runs")
    lines.append("")

    if df.empty:
        lines.append("*Keine Runs gefunden.*")
    else:
        lines.append(
            "| Rank | Run ID | Type | Strategy | Return | Sharpe | MaxDD |"
        )
        lines.append(
            "|------|--------|------|----------|--------|--------|-------|"
        )

        for rank, (_, row) in enumerate(df.iterrows(), 1):
            run_id = str(row.get("run_id", "-"))[:12]
            run_type = str(row.get("run_type", "-"))[:10]
            strategy = str(row.get("strategy_key", "-"))[:15]
            total_ret = (
                f"{float(row['total_return']):.2%}"
                if pd.notna(row.get("total_return"))
                else "-"
            )
            sharpe = (
                f"{float(row['sharpe']):.2f}"
                if pd.notna(row.get("sharpe"))
                else "-"
            )
            max_dd = (
                f"{float(row['max_drawdown']):.2%}"
                if pd.notna(row.get("max_drawdown"))
                else "-"
            )

            lines.append(
                f"| {rank} | {run_id} | {run_type} | {strategy} | {total_ret} | {sharpe} | {max_dd} |"
            )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Report erstellt mit Peak_Trade Analytics*")

    path.write_text("\n".join(lines), encoding="utf-8")
