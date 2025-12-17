# src/analytics/explorer.py
"""
Peak_Trade – Experiment & Metrics Explorer (Phase 22)
=====================================================
Zentrales Modul zum Durchsuchen, Filtern und Vergleichen von Experimenten/Runs.

Bietet:
- ExperimentFilter & ExperimentSummary Dataclasses
- ExperimentExplorer Klasse mit:
  - list_experiments: Filtern nach run_type, strategy, tags, sweep_name, Zeitraum
  - rank_experiments: Ranking nach beliebiger Metrik (sharpe, total_return, etc.)
  - get_experiment_details: Einzelnes Experiment abrufen
  - summarize_sweep: Sweep-Auswertung mit Top-N Parameterkombinationen
  - compare_sweeps: Mehrere Sweeps vergleichen

Usage:
    from src.analytics.explorer import (
        ExperimentFilter,
        ExperimentSummary,
        RankedExperiment,
        SweepOverview,
        ExperimentExplorer,
    )

    explorer = ExperimentExplorer()

    # Filtern & Listen
    flt = ExperimentFilter(run_types=["backtest"], strategies=["ma_crossover"])
    experiments = explorer.list_experiments(flt)

    # Ranking
    top_sharpe = explorer.rank_experiments(flt, metric="sharpe", top_n=10)

    # Sweep-Auswertung
    overview = explorer.summarize_sweep("my_strategy_opt_v1", metric="sharpe", top_n=10)
"""
from __future__ import annotations

import contextlib
import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.core.experiments import (
    EXPERIMENTS_CSV,
)

# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class ExperimentFilter:
    """
    Filter-Kriterien für Experimente.

    Attributes:
        run_types: Liste von run_type-Werten (z.B. ["backtest", "sweep"])
        strategies: Liste von strategy_key-Werten
        tags: Liste von Tags (aus metadata_json)
        sweep_names: Liste von sweep_name-Werten
        scan_names: Liste von scan_name-Werten
        portfolios: Liste von portfolio_name-Werten
        symbols: Liste von Symbolen
        created_from: Zeitstempel ab dem gefiltert wird (inklusiv)
        created_to: Zeitstempel bis zu dem gefiltert wird (inklusiv)
        limit: Maximale Anzahl Ergebnisse
    """

    run_types: list[str] | None = None
    strategies: list[str] | None = None
    tags: list[str] | None = None
    sweep_names: list[str] | None = None
    scan_names: list[str] | None = None
    portfolios: list[str] | None = None
    symbols: list[str] | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None
    limit: int | None = None


@dataclass
class ExperimentSummary:
    """
    Zusammenfassung eines einzelnen Experiments/Runs.

    Attributes:
        experiment_id: Eindeutige Run-ID (UUID)
        run_type: Typ des Runs (backtest, sweep, etc.)
        run_name: Name des Runs
        strategy_name: Name der Strategie (falls vorhanden)
        sweep_name: Name des Sweeps (falls run_type=sweep)
        scan_name: Name des Scans (falls run_type=market_scan)
        portfolio_name: Name des Portfolios (falls portfolio_backtest)
        symbol: Symbol/Market
        tags: Liste von Tags
        created_at: Erstellungszeitpunkt
        metrics: Dict mit Metriken (sharpe, total_return, max_drawdown, cagr, etc.)
        params: Dict mit Strategie-Parametern
    """

    experiment_id: str
    run_type: str
    run_name: str
    strategy_name: str | None = None
    sweep_name: str | None = None
    scan_name: str | None = None
    portfolio_name: str | None = None
    symbol: str | None = None
    tags: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class RankedExperiment:
    """
    Ein Experiment mit Ranking-Information.

    Attributes:
        summary: ExperimentSummary des Experiments
        rank: Position im Ranking (1-basiert)
        sort_key: Metrik, nach der sortiert wurde
        sort_value: Wert der Metrik
    """

    summary: ExperimentSummary
    rank: int
    sort_key: str
    sort_value: float


@dataclass
class SweepOverview:
    """
    Aggregierte Übersicht für einen Sweep.

    Attributes:
        sweep_name: Name des Sweeps
        strategy_key: Name der Strategie
        run_count: Anzahl der Runs im Sweep
        best_runs: Top-N Runs nach der gewählten Metrik
        metric_stats: Dict mit Statistiken zur Metrik (min, max, mean, std, median)
        param_ranges: Dict mit Wertebereichen für jeden Parameter
    """

    sweep_name: str
    strategy_key: str
    run_count: int
    best_runs: list[RankedExperiment] = field(default_factory=list)
    metric_stats: dict[str, float] = field(default_factory=dict)
    param_ranges: dict[str, dict[str, Any]] = field(default_factory=dict)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _parse_timestamp(ts_str: str) -> datetime | None:
    """Parst einen ISO-Timestamp-String zu datetime."""
    if not ts_str or pd.isna(ts_str):
        return None
    try:
        # Entferne 'Z' Suffix falls vorhanden
        ts_clean = ts_str.rstrip("Z")
        return datetime.fromisoformat(ts_clean)
    except (ValueError, TypeError):
        return None


def _extract_tag(metadata_json: str) -> str | None:
    """Extrahiert Tag aus metadata_json."""
    try:
        meta = json.loads(metadata_json)
        return meta.get("tag")
    except (json.JSONDecodeError, TypeError):
        return None


def _extract_tags_list(metadata_json: str) -> list[str]:
    """Extrahiert alle Tags als Liste aus metadata_json."""
    try:
        meta = json.loads(metadata_json)
        tag = meta.get("tag")
        if tag:
            return [tag]
        return []
    except (json.JSONDecodeError, TypeError):
        return []


def _parse_params(params_json: str) -> dict[str, Any]:
    """Parst params_json zu Dict."""
    try:
        return json.loads(params_json) if params_json else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _row_to_summary(row: pd.Series) -> ExperimentSummary:
    """Konvertiert eine DataFrame-Row zu ExperimentSummary."""
    # Metriken extrahieren
    metrics = {}
    for key in ["sharpe", "total_return", "max_drawdown", "cagr"]:
        val = row.get(key)
        if pd.notna(val):
            with contextlib.suppress(ValueError, TypeError):
                metrics[key] = float(val)

    # Zusätzliche Metriken aus stats_json
    try:
        stats = json.loads(row.get("stats_json", "{}"))
        for key in ["win_rate", "profit_factor", "sortino", "calmar", "total_trades"]:
            if key in stats and stats[key] is not None:
                with contextlib.suppress(ValueError, TypeError):
                    metrics[key] = float(stats[key])
    except (json.JSONDecodeError, TypeError):
        pass

    return ExperimentSummary(
        experiment_id=str(row.get("run_id", "")),
        run_type=str(row.get("run_type", "")),
        run_name=str(row.get("run_name", "")),
        strategy_name=row.get("strategy_key") if pd.notna(row.get("strategy_key")) else None,
        sweep_name=row.get("sweep_name") if pd.notna(row.get("sweep_name")) else None,
        scan_name=row.get("scan_name") if pd.notna(row.get("scan_name")) else None,
        portfolio_name=row.get("portfolio_name") if pd.notna(row.get("portfolio_name")) else None,
        symbol=row.get("symbol") if pd.notna(row.get("symbol")) else None,
        tags=_extract_tags_list(row.get("metadata_json", "{}")),
        created_at=_parse_timestamp(row.get("timestamp", "")),
        metrics=metrics,
        params=_parse_params(row.get("params_json", "{}")),
    )


# =============================================================================
# EXPERIMENT EXPLORER CLASS
# =============================================================================


class ExperimentExplorer:
    """
    Zentraler Explorer für Experimente/Runs.

    Ermöglicht:
    - Filtern nach diversen Kriterien
    - Ranking nach Metriken
    - Sweep-Auswertungen
    - Strategie-Vergleiche

    Example:
        >>> explorer = ExperimentExplorer()
        >>> flt = ExperimentFilter(run_types=["backtest"], strategies=["ma_crossover"])
        >>> experiments = explorer.list_experiments(flt)
        >>> top_sharpe = explorer.rank_experiments(flt, metric="sharpe", top_n=10)
    """

    def __init__(self, experiments_csv: Path | None = None):
        """
        Initialisiert den Explorer.

        Args:
            experiments_csv: Optionaler Pfad zur Experiments-CSV.
                            Default: EXPERIMENTS_CSV aus src.core.experiments
        """
        self._csv_path = experiments_csv or EXPERIMENTS_CSV

    def _load_df(self) -> pd.DataFrame:
        """Lädt die Experiments-CSV als DataFrame."""
        if not self._csv_path.exists():
            return pd.DataFrame()
        return pd.read_csv(self._csv_path)

    def _apply_filter(self, df: pd.DataFrame, flt: ExperimentFilter) -> pd.DataFrame:
        """Wendet einen ExperimentFilter auf das DataFrame an."""
        if df.empty:
            return df

        # Run-Type-Filter
        if flt.run_types and "run_type" in df.columns:
            df = df[df["run_type"].isin(flt.run_types)]

        # Strategy-Filter
        if flt.strategies and "strategy_key" in df.columns:
            df = df[df["strategy_key"].isin(flt.strategies)]

        # Symbol-Filter
        if flt.symbols and "symbol" in df.columns:
            df = df[df["symbol"].isin(flt.symbols)]

        # Portfolio-Filter
        if flt.portfolios and "portfolio_name" in df.columns:
            df = df[df["portfolio_name"].isin(flt.portfolios)]

        # Sweep-Name-Filter
        if flt.sweep_names and "sweep_name" in df.columns:
            df = df[df["sweep_name"].isin(flt.sweep_names)]

        # Scan-Name-Filter
        if flt.scan_names and "scan_name" in df.columns:
            df = df[df["scan_name"].isin(flt.scan_names)]

        # Tag-Filter (aus metadata_json)
        if flt.tags and "metadata_json" in df.columns:
            df = df.copy()
            df["_tag"] = df["metadata_json"].apply(_extract_tag)
            df = df[df["_tag"].isin(flt.tags)]
            df = df.drop(columns=["_tag"])

        # Zeitraum-Filter
        if (flt.created_from or flt.created_to) and "timestamp" in df.columns:
            df = df.copy()
            df["_ts"] = df["timestamp"].apply(_parse_timestamp)

            if flt.created_from:
                df = df[df["_ts"] >= flt.created_from]
            if flt.created_to:
                df = df[df["_ts"] <= flt.created_to]

            df = df.drop(columns=["_ts"])

        return df

    def list_experiments(
        self,
        flt: ExperimentFilter | None = None,
        sort_by: str = "timestamp",
        ascending: bool = False,
    ) -> list[ExperimentSummary]:
        """
        Listet Experimente mit optionalen Filtern.

        Args:
            flt: ExperimentFilter mit Filterkriterien
            sort_by: Spalte für Sortierung (default: timestamp)
            ascending: Sortierreihenfolge (default: False = neueste zuerst)

        Returns:
            Liste von ExperimentSummary-Objekten
        """
        df = self._load_df()
        if df.empty:
            return []

        if flt:
            df = self._apply_filter(df, flt)

        if df.empty:
            return []

        # Sortierung
        if sort_by in df.columns:
            df = df.sort_values(by=sort_by, ascending=ascending)

        # Limit
        if flt and flt.limit:
            df = df.head(flt.limit)

        # Zu Summaries konvertieren
        return [_row_to_summary(row) for _, row in df.iterrows()]

    def rank_experiments(
        self,
        flt: ExperimentFilter | None = None,
        metric: str = "sharpe",
        top_n: int | None = None,
        descending: bool = True,
    ) -> list[RankedExperiment]:
        """
        Rankt Experimente nach einer Metrik.

        Args:
            flt: ExperimentFilter mit Filterkriterien
            metric: Metrik für Ranking (z.B. "sharpe", "total_return", "max_drawdown")
            top_n: Anzahl Top-Ergebnisse (None = alle)
            descending: True für höher=besser, False für niedriger=besser

        Returns:
            Liste von RankedExperiment-Objekten mit Ranking-Info
        """
        df = self._load_df()
        if df.empty:
            return []

        if flt:
            df = self._apply_filter(df, flt)

        if df.empty or metric not in df.columns:
            return []

        # Nur Rows mit numerischen Werten für die Metrik
        df = df.copy()
        df[metric] = pd.to_numeric(df[metric], errors="coerce")
        df = df[df[metric].notna()]

        if df.empty:
            return []

        # Sortierung
        df = df.sort_values(by=metric, ascending=not descending)

        # Limit
        if top_n:
            df = df.head(top_n)

        # Zu RankedExperiments konvertieren
        ranked = []
        for rank, (_, row) in enumerate(df.iterrows(), 1):
            summary = _row_to_summary(row)
            ranked.append(
                RankedExperiment(
                    summary=summary,
                    rank=rank,
                    sort_key=metric,
                    sort_value=float(row[metric]),
                )
            )

        return ranked

    def get_experiment_details(self, experiment_id: str) -> ExperimentSummary | None:
        """
        Holt Details zu einem einzelnen Experiment.

        Args:
            experiment_id: Run-ID (UUID)

        Returns:
            ExperimentSummary oder None wenn nicht gefunden
        """
        df = self._load_df()
        if df.empty:
            return None

        matches = df[df["run_id"] == experiment_id]
        if matches.empty:
            return None

        return _row_to_summary(matches.iloc[0])

    def summarize_sweep(
        self,
        sweep_name: str,
        metric: str = "sharpe",
        top_n: int = 10,
    ) -> SweepOverview | None:
        """
        Erstellt eine Übersicht für einen Sweep.

        Args:
            sweep_name: Name des Sweeps
            metric: Metrik für Ranking der besten Runs
            top_n: Anzahl Top-Runs in der Übersicht

        Returns:
            SweepOverview mit aggregierten Informationen oder None
        """
        df = self._load_df()
        if df.empty:
            return None

        # Nur Sweep-Runs mit passendem sweep_name
        sweep_df = df[
            (df["run_type"] == "sweep") & (df["sweep_name"] == sweep_name)
        ].copy()

        if sweep_df.empty:
            return None

        # Strategie-Key (erster nicht-None Wert)
        strategy_key = ""
        if "strategy_key" in sweep_df.columns:
            non_null = sweep_df["strategy_key"].dropna()
            if len(non_null) > 0:
                strategy_key = str(non_null.iloc[0])

        run_count = len(sweep_df)

        # Metrik-Statistiken
        metric_stats = {}
        if metric in sweep_df.columns:
            metric_values = pd.to_numeric(sweep_df[metric], errors="coerce").dropna()
            if len(metric_values) > 0:
                metric_stats = {
                    "min": float(metric_values.min()),
                    "max": float(metric_values.max()),
                    "mean": float(metric_values.mean()),
                    "std": float(metric_values.std()) if len(metric_values) > 1 else 0.0,
                    "median": float(metric_values.median()),
                }

        # Parameter-Ranges aus params_json extrahieren
        param_ranges: dict[str, dict[str, Any]] = {}
        if "params_json" in sweep_df.columns:
            all_params: dict[str, list[Any]] = {}
            for _, row in sweep_df.iterrows():
                params = _parse_params(row.get("params_json", "{}"))
                for key, val in params.items():
                    if key not in all_params:
                        all_params[key] = []
                    all_params[key].append(val)

            for key, values in all_params.items():
                unique_values = list(set(str(v) for v in values))
                param_ranges[key] = {
                    "values": unique_values,
                    "count": len(unique_values),
                }

        # Top-N Runs nach Metrik
        flt = ExperimentFilter(run_types=["sweep"], sweep_names=[sweep_name])
        best_runs = self.rank_experiments(flt, metric=metric, top_n=top_n, descending=True)

        return SweepOverview(
            sweep_name=sweep_name,
            strategy_key=strategy_key,
            run_count=run_count,
            best_runs=best_runs,
            metric_stats=metric_stats,
            param_ranges=param_ranges,
        )

    def list_sweeps(self) -> list[str]:
        """
        Listet alle verfügbaren Sweep-Namen.

        Returns:
            Liste von sweep_name-Werten
        """
        df = self._load_df()
        if df.empty or "sweep_name" not in df.columns:
            return []

        sweep_df = df[df["run_type"] == "sweep"]
        if sweep_df.empty:
            return []

        return sorted(sweep_df["sweep_name"].dropna().unique().tolist())

    def compare_sweeps(
        self,
        sweep_names: Sequence[str],
        metric: str = "sharpe",
    ) -> list[SweepOverview]:
        """
        Vergleicht mehrere Sweeps.

        Args:
            sweep_names: Liste von Sweep-Namen zum Vergleich
            metric: Metrik für Ranking

        Returns:
            Liste von SweepOverview-Objekten, sortiert nach bestem Wert
        """
        overviews = []
        for name in sweep_names:
            overview = self.summarize_sweep(name, metric=metric)
            if overview:
                overviews.append(overview)

        # Sortieren nach bestem Metrik-Wert (max)
        overviews.sort(
            key=lambda o: o.metric_stats.get("max", 0.0),
            reverse=True,
        )

        return overviews

    def get_unique_strategies(self) -> list[str]:
        """
        Listet alle einzigartigen Strategie-Keys.

        Returns:
            Sortierte Liste von strategy_key-Werten
        """
        df = self._load_df()
        if df.empty or "strategy_key" not in df.columns:
            return []

        return sorted(df["strategy_key"].dropna().unique().tolist())

    def get_unique_run_types(self) -> list[str]:
        """
        Listet alle einzigartigen Run-Types.

        Returns:
            Sortierte Liste von run_type-Werten
        """
        df = self._load_df()
        if df.empty or "run_type" not in df.columns:
            return []

        return sorted(df["run_type"].dropna().unique().tolist())

    def count_experiments(self, flt: ExperimentFilter | None = None) -> int:
        """
        Zählt Experimente (mit optionalem Filter).

        Args:
            flt: ExperimentFilter mit Filterkriterien

        Returns:
            Anzahl der Experimente
        """
        df = self._load_df()
        if df.empty:
            return 0

        if flt:
            df = self._apply_filter(df, flt)

        return len(df)

    def export_to_csv(
        self,
        flt: ExperimentFilter | None = None,
        output_path: Path = Path("experiments_export.csv"),
        columns: list[str] | None = None,
    ) -> Path:
        """
        Exportiert gefilterte Experimente in eine CSV-Datei.

        Args:
            flt: ExperimentFilter mit Filterkriterien
            output_path: Pfad zur Ausgabe-CSV
            columns: Liste der zu exportierenden Spalten (None = alle)

        Returns:
            Pfad zur erstellten CSV-Datei
        """
        df = self._load_df()
        if flt:
            df = self._apply_filter(df, flt)

        if columns:
            available_cols = [c for c in columns if c in df.columns]
            df = df[available_cols]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

        return output_path

    def export_to_markdown(
        self,
        flt: ExperimentFilter | None = None,
        output_path: Path = Path("experiments_export.md"),
        metric: str = "sharpe",
        top_n: int = 20,
    ) -> Path:
        """
        Exportiert gefilterte Experimente als Markdown-Tabelle.

        Args:
            flt: ExperimentFilter mit Filterkriterien
            output_path: Pfad zur Ausgabe-Markdown-Datei
            metric: Metrik für Sortierung
            top_n: Anzahl Experimente in der Tabelle

        Returns:
            Pfad zur erstellten Markdown-Datei
        """
        ranked = self.rank_experiments(flt, metric=metric, top_n=top_n)

        lines = []
        lines.append("# Peak_Trade Experiment Export")
        lines.append("")
        lines.append(f"Generiert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Sortiert nach: `{metric}`")
        lines.append(f"Anzahl: {len(ranked)}")
        lines.append("")
        lines.append("## Experimente")
        lines.append("")

        if ranked:
            lines.append("| Rank | Run ID | Type | Strategy | Return | Sharpe | Max DD |")
            lines.append("|------|--------|------|----------|--------|--------|--------|")

            for r in ranked:
                s = r.summary
                ret = f"{s.metrics.get('total_return', 0)*100:.1f}%" if s.metrics.get("total_return") else "-"
                sharpe = f"{s.metrics.get('sharpe', 0):.2f}" if s.metrics.get("sharpe") else "-"
                dd = f"{s.metrics.get('max_drawdown', 0)*100:.1f}%" if s.metrics.get("max_drawdown") else "-"
                run_id = s.experiment_id[:12]
                strategy = s.strategy_name or "-"

                lines.append(f"| {r.rank} | {run_id} | {s.run_type} | {strategy} | {ret} | {sharpe} | {dd} |")

        else:
            lines.append("*Keine Experimente gefunden.*")

        lines.append("")
        lines.append("---")
        lines.append("*Report erstellt mit Peak_Trade Experiment Explorer*")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")

        return output_path


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def get_explorer(experiments_csv: Path | None = None) -> ExperimentExplorer:
    """
    Factory-Funktion für ExperimentExplorer.

    Args:
        experiments_csv: Optionaler Pfad zur Experiments-CSV

    Returns:
        Initialisierter ExperimentExplorer
    """
    return ExperimentExplorer(experiments_csv)


def quick_list(
    run_type: str | None = None,
    strategy: str | None = None,
    limit: int = 20,
) -> list[ExperimentSummary]:
    """
    Schnelle Auflistung von Experimenten.

    Args:
        run_type: Filter nach run_type
        strategy: Filter nach strategy_key
        limit: Maximale Anzahl

    Returns:
        Liste von ExperimentSummary-Objekten
    """
    flt = ExperimentFilter(
        run_types=[run_type] if run_type else None,
        strategies=[strategy] if strategy else None,
        limit=limit,
    )
    return ExperimentExplorer().list_experiments(flt)


def quick_rank(
    metric: str = "sharpe",
    run_type: str | None = None,
    strategy: str | None = None,
    top_n: int = 10,
) -> list[RankedExperiment]:
    """
    Schnelles Ranking von Experimenten.

    Args:
        metric: Metrik für Ranking
        run_type: Filter nach run_type
        strategy: Filter nach strategy_key
        top_n: Anzahl Top-Ergebnisse

    Returns:
        Liste von RankedExperiment-Objekten
    """
    flt = ExperimentFilter(
        run_types=[run_type] if run_type else None,
        strategies=[strategy] if strategy else None,
    )
    return ExperimentExplorer().rank_experiments(flt, metric=metric, top_n=top_n)


def quick_sweep_summary(
    sweep_name: str,
    metric: str = "sharpe",
    top_n: int = 10,
) -> SweepOverview | None:
    """
    Schnelle Sweep-Zusammenfassung.

    Args:
        sweep_name: Name des Sweeps
        metric: Metrik für Ranking
        top_n: Anzahl Top-Runs

    Returns:
        SweepOverview oder None
    """
    return ExperimentExplorer().summarize_sweep(sweep_name, metric=metric, top_n=top_n)
