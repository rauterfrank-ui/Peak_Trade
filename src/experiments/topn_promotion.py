# src/experiments/topn_promotion.py
"""
Peak_Trade Top-N Promotion (Phase 42)
=====================================

Automatische Auswahl und Export der Top-N Konfigurationen aus Sweep-Ergebnissen.

Komponenten:
- TopNPromotionConfig: Konfiguration für Top-N Promotion
- load_sweep_results: Lädt Sweep-Ergebnisse
- select_top_n: Wählt Top-N Konfigurationen nach Metrik
- export_top_n: Exportiert Top-N in TOML-Format

Usage:
    from src.experiments.topn_promotion import (
        TopNPromotionConfig,
        load_sweep_results,
        select_top_n,
        export_top_n,
    )

    config = TopNPromotionConfig(
        sweep_name="rsi_reversion_basic",
        metric_primary="metric_sharpe_ratio",
        top_n=5,
    )
    df = load_sweep_results(config)
    df_top = select_top_n(df, config)
    output_path = export_top_n(df_top, config)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import toml

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class TopNPromotionConfig:
    """
    Konfiguration für Top-N Promotion.

    Attributes:
        sweep_name: Name des Sweeps (z.B. "rsi_reversion_basic")
        metric_primary: Primäre Metrik für Sortierung (default: "metric_sharpe_ratio")
        metric_fallback: Fallback-Metrik falls primary fehlt (default: "metric_total_return")
        top_n: Anzahl der Top-Konfigurationen (default: 5)
        output_path: Ausgabe-Verzeichnis (default: "reports/sweeps")
        experiments_dir: Verzeichnis mit Experiment-Ergebnissen (default: "reports/experiments")
    """

    sweep_name: str
    metric_primary: str = "metric_sharpe_ratio"
    metric_fallback: str = "metric_total_return"
    top_n: int = 5
    output_path: Path = field(default_factory=lambda: Path("reports/sweeps"))
    experiments_dir: Path = field(default_factory=lambda: Path("reports/experiments"))

    def __post_init__(self) -> None:
        """Normalisiert Pfade."""
        if isinstance(self.output_path, str):
            self.output_path = Path(self.output_path)
        if isinstance(self.experiments_dir, str):
            self.experiments_dir = Path(self.experiments_dir)


# =============================================================================
# LOAD RESULTS
# =============================================================================


def find_sweep_results(sweep_name: str, experiments_dir: Path) -> Optional[Path]:
    """
    Sucht nach der neuesten Ergebnis-Datei für einen Sweep.

    Args:
        sweep_name: Name des Sweeps
        experiments_dir: Verzeichnis mit Experiment-Ergebnissen

    Returns:
        Pfad zur Datei oder None
    """
    if not experiments_dir.exists():
        return None

    # Suche nach passenden CSV-Dateien (mit sweep_name im Dateinamen)
    pattern = f"*{sweep_name}*.csv"
    matches = sorted(experiments_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

    if matches:
        return matches[0]

    # Suche nach Parquet-Dateien
    pattern = f"*{sweep_name}*.parquet"
    matches = sorted(experiments_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

    if matches:
        return matches[0]

    # Fallback: Versuche strategy_name zu extrahieren
    parts = sweep_name.split("_")
    if len(parts) >= 2:
        strategy_name = "_".join(parts[:-1])
        pattern = f"*{strategy_name}*.csv"
        matches = sorted(experiments_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        if matches:
            return matches[0]

    return None


def load_sweep_results(config: TopNPromotionConfig) -> pd.DataFrame:
    """
    Lädt Sweep-Ergebnisse aus CSV oder Parquet.

    Args:
        config: TopNPromotionConfig

    Returns:
        DataFrame mit Sweep-Ergebnissen

    Raises:
        FileNotFoundError: Wenn keine Ergebnisse gefunden werden
        ValueError: Bei ungültigem Dateiformat
    """
    filepath = find_sweep_results(config.sweep_name, config.experiments_dir)

    if filepath is None:
        raise FileNotFoundError(
            f"Keine Ergebnisse gefunden für Sweep '{config.sweep_name}' in {config.experiments_dir}. "
            f"Führe zuerst einen Sweep aus: "
            f"python scripts/run_strategy_sweep.py --sweep-name {config.sweep_name}"
        )

    logger.info(f"Lade Sweep-Ergebnisse aus: {filepath}")

    # Lade Datei
    if filepath.suffix == ".parquet":
        df = pd.read_parquet(filepath)
    elif filepath.suffix == ".csv":
        df = pd.read_csv(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath.suffix}")

    logger.info(f"Geladen: {len(df)} Runs")
    return df


# =============================================================================
# SELECT TOP N
# =============================================================================


def select_top_n(
    df: pd.DataFrame, config: TopNPromotionConfig
) -> Tuple[pd.DataFrame, str]:
    """
    Wählt Top-N Konfigurationen nach Metrik aus.

    Args:
        df: DataFrame mit Sweep-Ergebnissen
        config: TopNPromotionConfig

    Returns:
        Tuple von (DataFrame mit Top-N Runs, verwendete Metrik)

    Raises:
        ValueError: Wenn keine gültige Metrik gefunden wird oder keine Daten übrig sind
    """
    # Bestimme Metrik (primary oder fallback)
    metric_used = config.metric_primary
    if metric_used not in df.columns:
        logger.warning(
            f"Metrik '{config.metric_primary}' nicht gefunden, verwende Fallback: {config.metric_fallback}"
        )
        metric_used = config.metric_fallback

    if metric_used not in df.columns:
        available = [c for c in df.columns if c.startswith("metric_")]
        raise ValueError(
            f"Weder '{config.metric_primary}' noch '{config.metric_fallback}' gefunden. "
            f"Verfügbare Metriken: {available}"
        )

    # Filtere NaN-Werte
    df_valid = df[df[metric_used].notna()].copy()

    if len(df_valid) == 0:
        raise ValueError(
            f"Keine gültigen Runs mit Metrik '{metric_used}' gefunden (alle NaN)"
        )

    logger.info(f"Verwende Metrik: {metric_used} ({len(df_valid)} gültige Runs)")

    # Sortiere absteigend und nimm Top-N
    df_top = df_valid.nlargest(config.top_n, metric_used).copy()

    # Füge Rank hinzu
    df_top.insert(0, "rank", range(1, len(df_top) + 1))

    logger.info(f"Top {len(df_top)} Konfigurationen ausgewählt")
    return df_top, metric_used


# =============================================================================
# EXPORT TOP N
# =============================================================================


def export_top_n(
    df_top: pd.DataFrame, config: TopNPromotionConfig
) -> Path:
    """
    Exportiert Top-N Konfigurationen in TOML-Format.

    Args:
        df_top: DataFrame mit Top-N Runs (muss "rank" Spalte enthalten)
        config: TopNPromotionConfig
        metric_used: Die verwendete Metrik (aus select_top_n)

    Returns:
        Pfad zur erzeugten TOML-Datei
    """
    # Erstelle Output-Verzeichnis
    config.output_path.mkdir(parents=True, exist_ok=True)

    # Bestimme verwendete Metrik (aus Config oder DataFrame)
    metric_used = config.metric_primary
    if metric_used not in df_top.columns:
        metric_used = config.metric_fallback

    # Baue TOML-Struktur
    toml_data: Dict[str, Any] = {
        "meta": {
            "sweep_name": config.sweep_name,
            "metric_used": metric_used,
            "top_n": len(df_top),
            "generated_at": datetime.now().isoformat(),
        },
        "candidates": [],
    }

    # Extrahiere Param- und Metrik-Spalten
    param_cols = [c for c in df_top.columns if c.startswith("param_")]
    metric_cols = [c for c in df_top.columns if c.startswith("metric_")]

    # Erstelle Einträge für jeden Kandidaten
    for _, row in df_top.iterrows():
        candidate: Dict[str, Any] = {
            "rank": int(row["rank"]),
        }

        # Experiment-ID falls vorhanden
        if "experiment_id" in row.index:
            candidate["experiment_id"] = str(row["experiment_id"])

        # Metriken
        for col in metric_cols:
            val = row[col]
            if pd.notna(val):
                # Entferne "metric_" Prefix für TOML
                key = col.replace("metric_", "")
                candidate[key] = float(val)

        # Parameter
        params: Dict[str, Any] = {}
        for col in param_cols:
            val = row[col]
            if pd.notna(val):
                # Entferne "param_" Prefix für TOML
                key = col.replace("param_", "")
                # Konvertiere zu Python-Typen
                if isinstance(val, (int, float)):
                    params[key] = float(val) if isinstance(val, float) else int(val)
                elif isinstance(val, bool):
                    params[key] = bool(val)
                elif isinstance(val, str):
                    params[key] = str(val)
                else:
                    params[key] = str(val)

        candidate["params"] = params

        toml_data["candidates"].append(candidate)

    # Schreibe TOML-Datei
    output_file = config.output_path / f"{config.sweep_name}_top_candidates.toml"
    with open(output_file, "w") as f:
        toml.dump(toml_data, f)

    logger.info(f"Top-N Kandidaten exportiert: {output_file}")
    return output_file

