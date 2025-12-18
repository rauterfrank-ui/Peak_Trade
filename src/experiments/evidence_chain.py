#!/usr/bin/env python3
"""
Evidence Chain Module (P1)
==========================

Erstellt standardisierte Artifacts für jeden Research/Backtest-Run:
- results/<run_id>/config_snapshot.json  (Meta + Params)
- results/<run_id>/stats.json           (Performance-Metriken)
- results/<run_id>/equity.csv           (Equity-Kurve)
- results/<run_id>/trades.parquet       (optional, wenn parquet engine verfügbar)
- results/<run_id>/report_snippet.md    (Markdown-Zusammenfassung)

Graceful degradation:
- Funktioniert ohne mlflow (Tracker = None)
- Funktioniert ohne quarto (Report-Rendering optional)
- trades.parquet ist optional (skip bei fehlender parquet engine)

Usage:
    from src.experiments.evidence_chain import (
        ensure_run_dir,
        write_config_snapshot,
        write_stats_json,
        write_equity_csv,
        write_trades_parquet_optional,
        write_report_snippet_md,
    )

    # In run_backtest.py oder research_cli.py:
    run_dir = ensure_run_dir(run_id)
    write_config_snapshot(run_dir, meta, params)
    write_stats_json(run_dir, stats)
    write_equity_csv(run_dir, equity_data)
    write_trades_parquet_optional(run_dir, trades_df)
    write_report_snippet_md(run_dir, summary)
"""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd


def ensure_run_dir(run_id: str, base_dir: Optional[Path] = None) -> Path:
    """
    Erstellt das Run-Verzeichnis results/<run_id>/ falls es nicht existiert.

    Args:
        run_id: Eindeutige Run-ID (z.B. UUID oder Timestamp)
        base_dir: Basis-Verzeichnis (default: ./results)

    Returns:
        Path zum Run-Verzeichnis
    """
    if base_dir is None:
        base_dir = Path("results")

    run_dir = base_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_config_snapshot(
    run_dir: Path,
    meta: Dict[str, Any],
    params: Dict[str, Any],
) -> Path:
    """
    Schreibt config_snapshot.json mit Meta-Informationen und Parametern.

    Args:
        run_dir: Run-Verzeichnis
        meta: Meta-Daten (z.B. run_id, strategy, git_sha, argv, timestamp)
        params: Strategy-Parameter

    Returns:
        Path zur geschriebenen Datei

    Example:
        meta = {
            "run_id": "abc123",
            "strategy": "ma_crossover",
            "git_sha": "abcdef123456",
            "argv": ["--strategy", "ma_crossover"],
            "stage": "backtest",
            "runner": "run_backtest.py",
            "timestamp": "2024-01-15T14:30:00Z",
        }
        params = {"fast": 10, "slow": 30}
        write_config_snapshot(run_dir, meta, params)
    """
    snapshot_path = run_dir / "config_snapshot.json"

    data = {
        "meta": meta,
        "params": params,
    }

    with open(snapshot_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    return snapshot_path


def write_stats_json(run_dir: Path, stats: Dict[str, Any]) -> Path:
    """
    Schreibt stats.json mit Performance-Metriken.

    Args:
        run_dir: Run-Verzeichnis
        stats: Stats-Dictionary (z.B. von BacktestResult.stats)

    Returns:
        Path zur geschriebenen Datei

    Example:
        stats = {
            "total_return": 0.25,
            "sharpe": 1.5,
            "max_drawdown": -0.15,
            "total_trades": 42,
            "win_rate": 0.55,
        }
        write_stats_json(run_dir, stats)
    """
    stats_path = run_dir / "stats.json"

    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2, default=str)

    return stats_path


def write_equity_csv(
    run_dir: Path,
    equity_data: Union[pd.DataFrame, List[Dict[str, Any]], List[List[Any]]],
) -> Path:
    """
    Schreibt equity.csv mit Equity-Kurve.

    Args:
        run_dir: Run-Verzeichnis
        equity_data: Equity-Daten in einem der Formate:
            - pd.DataFrame mit Spalten timestamp, equity
            - list[dict] mit keys timestamp, equity
            - list[list] mit Header in erster Zeile

    Returns:
        Path zur geschriebenen Datei

    Example:
        # DataFrame
        df_equity = pd.DataFrame({
            "timestamp": ["2024-01-01T00:00:00", "2024-01-01T01:00:00"],
            "equity": [10000.0, 10100.0],
        })
        write_equity_csv(run_dir, df_equity)

        # list[dict]
        equity_data = [
            {"timestamp": "2024-01-01T00:00:00", "equity": 10000.0},
            {"timestamp": "2024-01-01T01:00:00", "equity": 10100.0},
        ]
        write_equity_csv(run_dir, equity_data)
    """
    equity_path = run_dir / "equity.csv"

    # Konvertiere zu DataFrame falls nötig
    if isinstance(equity_data, pd.DataFrame):
        df = equity_data
    elif isinstance(equity_data, list):
        if len(equity_data) == 0:
            # Leere Liste -> leeres DataFrame
            df = pd.DataFrame(columns=["timestamp", "equity"])
        elif isinstance(equity_data[0], dict):
            # list[dict]
            df = pd.DataFrame(equity_data)
        elif isinstance(equity_data[0], list):
            # list[list] mit Header in erster Zeile
            header = equity_data[0]
            rows = equity_data[1:]
            df = pd.DataFrame(rows, columns=header)
        else:
            raise ValueError(f"Unbekanntes Format für equity_data: {type(equity_data[0])}")
    else:
        raise ValueError(f"Unbekanntes Format für equity_data: {type(equity_data)}")

    # Schreibe CSV
    df.to_csv(equity_path, index=False)

    return equity_path


def write_trades_parquet_optional(
    run_dir: Path,
    trades_data: Optional[pd.DataFrame],
) -> Optional[Path]:
    """
    Schreibt trades.parquet falls trades_data vorhanden und parquet engine verfügbar.

    Graceful degradation: Gibt None zurück wenn:
    - trades_data ist None/leer
    - parquet engine nicht verfügbar (ImportError)

    Args:
        run_dir: Run-Verzeichnis
        trades_data: Trades-DataFrame (optional)

    Returns:
        Path zur geschriebenen Datei oder None falls nicht möglich

    Example:
        trades_df = pd.DataFrame({
            "timestamp": ["2024-01-01T00:00:00"],
            "symbol": ["BTC/EUR"],
            "side": ["buy"],
            "quantity": [0.1],
        })
        write_trades_parquet_optional(run_dir, trades_df)
    """
    if trades_data is None or len(trades_data) == 0:
        return None

    parquet_path = run_dir / "trades.parquet"

    try:
        trades_data.to_parquet(parquet_path, index=False)
        return parquet_path
    except ImportError:
        # parquet engine (pyarrow/fastparquet) nicht verfügbar
        return None
    except Exception:
        # Andere Fehler (z.B. I/O-Fehler) ebenfalls silent ignorieren
        return None


def write_report_snippet_md(
    run_dir: Path,
    summary: Dict[str, Any],
) -> Path:
    """
    Schreibt report_snippet.md mit Markdown-Zusammenfassung.

    Dieses Snippet kann in Quarto-Reports inkludiert werden.

    Args:
        run_dir: Run-Verzeichnis
        summary: Summary-Dictionary mit Key-Stats

    Returns:
        Path zur geschriebenen Datei

    Example:
        summary = {
            "run_id": "abc123",
            "strategy": "ma_crossover",
            "symbol": "BTC/EUR",
            "total_return": 0.25,
            "sharpe": 1.5,
            "max_drawdown": -0.15,
            "total_trades": 42,
        }
        write_report_snippet_md(run_dir, summary)
    """
    snippet_path = run_dir / "report_snippet.md"

    # Baue Markdown
    lines = []
    lines.append("# Backtest Summary\n")

    # Run-Meta
    if "run_id" in summary:
        lines.append(f"**Run ID:** `{summary['run_id']}`\n")
    if "strategy" in summary:
        lines.append(f"**Strategy:** `{summary['strategy']}`\n")
    if "symbol" in summary:
        lines.append(f"**Symbol:** `{summary['symbol']}`\n")
    if "timestamp" in summary:
        lines.append(f"**Timestamp:** `{summary['timestamp']}`\n")

    lines.append("\n## Performance Metrics\n")

    # Key-Metriken
    metrics = [
        ("Total Return", "total_return", ".2%"),
        ("Sharpe Ratio", "sharpe", ".2f"),
        ("Max Drawdown", "max_drawdown", ".2%"),
        ("Total Trades", "total_trades", "d"),
        ("Win Rate", "win_rate", ".2%"),
        ("Profit Factor", "profit_factor", ".2f"),
    ]

    for label, key, fmt in metrics:
        if key in summary:
            value = summary[key]
            if value is not None:
                formatted = f"{value:{fmt}}" if isinstance(value, (int, float)) else str(value)
                lines.append(f"- **{label}:** {formatted}\n")

    # Zusätzliche Keys (falls vorhanden)
    extra_keys = set(summary.keys()) - {k for _, k, _ in metrics} - {"run_id", "strategy", "symbol", "timestamp"}
    if extra_keys:
        lines.append("\n## Additional Info\n")
        for key in sorted(extra_keys):
            lines.append(f"- **{key}:** {summary[key]}\n")

    # Schreibe Datei
    with open(snippet_path, "w") as f:
        f.writelines(lines)

    return snippet_path


# =============================================================================
# HELPER: Optional MLflow Tracker (Graceful Degradation)
# =============================================================================


class NullTracker:
    """
    Null-Object-Pattern für MLflow-Tracker.

    Wird verwendet wenn mlflow nicht verfügbar ist.
    """

    def log_params(self, params: Dict[str, Any]) -> None:
        """No-op."""
        pass

    def log_metrics(self, metrics: Dict[str, float]) -> None:
        """No-op."""
        pass

    def log_artifact(self, artifact_path: Path) -> None:
        """No-op."""
        pass

    def set_tag(self, key: str, value: str) -> None:
        """No-op."""
        pass


def get_optional_tracker() -> Union[Any, NullTracker]:
    """
    Versucht einen MLflow-Tracker zu erstellen, fällt zurück auf NullTracker.

    Returns:
        MLflow-Tracker oder NullTracker
    """
    try:
        import mlflow
        # Wenn mlflow verfügbar ist, gebe einen einfachen Wrapper zurück
        # der die wichtigsten Methoden exponiert
        class MLflowTrackerWrapper:
            def log_params(self, params: Dict[str, Any]) -> None:
                mlflow.log_params(params)

            def log_metrics(self, metrics: Dict[str, float]) -> None:
                mlflow.log_metrics(metrics)

            def log_artifact(self, artifact_path: Path) -> None:
                mlflow.log_artifact(str(artifact_path))

            def set_tag(self, key: str, value: str) -> None:
                mlflow.set_tag(key, value)

        return MLflowTrackerWrapper()
    except ImportError:
        return NullTracker()


# =============================================================================
# HELPER: Quick Evidence Chain for Minimal Runners
# =============================================================================


def write_minimal_evidence_chain(
    run_dir: Path,
    meta: Dict[str, Any],
    stats: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Schreibt minimale Evidence Chain (config + stats + snippet).

    Für Runner die keine vollständige Evidence Chain brauchen (z.B. research_cli, live_ops).

    Args:
        run_dir: Run-Verzeichnis
        meta: Meta-Daten
        stats: Optional stats (wenn nicht vorhanden, wird ein leeres dict verwendet)
    """
    # 1. Config-Snapshot (ohne params)
    write_config_snapshot(run_dir, meta, params={})

    # 2. Stats (falls vorhanden)
    if stats:
        write_stats_json(run_dir, stats)

    # 3. Report-Snippet
    summary = {**meta}
    if stats:
        summary.update(stats)
    write_report_snippet_md(run_dir, summary)
