# src/core/experiments.py
"""
Peak_Trade Experiment Registry
==============================
Zentrale Verwaltung aller Experiment-Runs (Backtests, Paper-Trades, Live-Risk-Checks, etc.).

Speicherformat: CSV in reports/experiments/experiments.csv
Jeder Run wird als ExperimentRecord mit eindeutiger run_id gespeichert.

Konventionen:
- run_type: Einer der definierten RUN_TYPE_* Konstanten
- run_name: Freier Name für den Run (z.B. "ma_crossover_dev_test")
- timestamp: ISO-Format UTC (z.B. "2024-01-15T14:30:00Z")
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import csv
import json
from datetime import datetime
import uuid

from src.backtest.result import BacktestResult

# =============================================================================
# RUN_TYPE KONSTANTEN
# =============================================================================
# Verwende diese Konstanten anstatt String-Literale für konsistentes Logging

RUN_TYPE_BACKTEST = "backtest"
"""Standard-Backtest einer einzelnen Strategie."""

RUN_TYPE_PORTFOLIO_BACKTEST = "portfolio_backtest"
"""Portfolio-Backtest mit mehreren Strategien."""

RUN_TYPE_LIVE_RISK_CHECK = "live_risk_check"
"""Live-Risk-Limits-Prüfung gegen Orders-CSV."""

RUN_TYPE_PAPER_TRADE = "paper_trade"
"""Paper-Trade-Simulation mit PaperBroker."""

RUN_TYPE_FORWARD_SIGNAL = "forward_signal"
"""Forward-Signal-Generierung (Out-of-Sample)."""

RUN_TYPE_SWEEP = "sweep"
"""Parameter-Sweep über mehrere Kombinationen."""

RUN_TYPE_MARKET_SCAN = "market_scan"
"""Scan über mehrere Märkte/Symbole."""

RUN_TYPE_SCHEDULER_JOB = "scheduler_job"
"""Scheduler-Job-Ausführung."""

RUN_TYPE_SHADOW_RUN = "shadow_run"
"""Shadow-/Dry-Run-Execution (Phase 24). Simuliert Orders ohne echte API-Calls."""

# Liste aller gültigen run_types
VALID_RUN_TYPES = [
    RUN_TYPE_BACKTEST,
    RUN_TYPE_PORTFOLIO_BACKTEST,
    RUN_TYPE_LIVE_RISK_CHECK,
    RUN_TYPE_PAPER_TRADE,
    RUN_TYPE_FORWARD_SIGNAL,
    RUN_TYPE_SWEEP,
    RUN_TYPE_MARKET_SCAN,
    RUN_TYPE_SCHEDULER_JOB,
    RUN_TYPE_SHADOW_RUN,
]

# =============================================================================
# PFADE
# =============================================================================

EXPERIMENTS_DIR = Path("reports") / "experiments"
EXPERIMENTS_CSV = EXPERIMENTS_DIR / "experiments.csv"


@dataclass
class ExperimentRecord:
    """
    Ein Eintrag in der Experiment-Registry.

    Idee:
    - Ein Record pro Run (z.B. einzelner Backtest, Sweep-Kombination, Scan-Symbol, Portfolio-Run).
    - Stats/Params/Metadata werden zusaetzlich als JSON gespeichert, um sie spaeter flexibel laden zu koennen.
    """

    run_id: str
    run_type: str           # z.B. "single_backtest", "market_scan", "sweep", "portfolio"
    run_name: str
    timestamp: str          # ISO-String in UTC

    strategy_key: Optional[str] = None
    symbol: Optional[str] = None
    portfolio_name: Optional[str] = None
    sweep_name: Optional[str] = None
    scan_name: Optional[str] = None

    total_return: Optional[float] = None
    cagr: Optional[float] = None
    max_drawdown: Optional[float] = None
    sharpe: Optional[float] = None

    report_dir: Optional[str] = None      # z.B. "reports" oder "reports/portfolio"
    report_prefix: Optional[str] = None   # z.B. "ma_crossover_run1", "portfolio_core_ma"

    params_json: str = ""     # JSON-String mit Strategy-Params
    stats_json: str = ""      # JSON-String mit allen Stats
    metadata_json: str = ""   # JSON-String mit vollstaendiger metadata

    def to_row(self) -> Dict[str, Any]:
        return asdict(self)


def _ensure_experiments_dir() -> None:
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)


def append_experiment_record(record: ExperimentRecord) -> None:
    """
    Haengt einen ExperimentRecord an die zentrale CSV an.
    Schreibt Header, falls die Datei noch nicht existiert.
    """
    _ensure_experiments_dir()
    row = record.to_row()
    file_exists = EXPERIMENTS_CSV.is_file()

    with EXPERIMENTS_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def build_record_from_result(
    result: BacktestResult,
    run_type: str,
    run_name: str,
    strategy_key: Optional[str] = None,
    symbol: Optional[str] = None,
    portfolio_name: Optional[str] = None,
    sweep_name: Optional[str] = None,
    scan_name: Optional[str] = None,
    report_dir: Optional[Path] = None,
    report_prefix: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> ExperimentRecord:
    """
    Baut einen ExperimentRecord aus einem BacktestResult und Zusatzinfos.
    """
    stats = result.stats or {}
    metadata = dict(result.metadata or {})
    if extra_metadata:
        metadata.update(extra_metadata)

    params = metadata.get("params", {})

    total_return = stats.get("total_return")
    cagr = stats.get("cagr")
    max_dd = stats.get("max_drawdown")
    sharpe = stats.get("sharpe")

    ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    if report_dir is not None:
        report_dir_str = str(report_dir)
    else:
        report_dir_str = None

    rec = ExperimentRecord(
        run_id=str(uuid.uuid4()),
        run_type=str(run_type),
        run_name=str(run_name),
        timestamp=ts,
        strategy_key=strategy_key or metadata.get("strategy_key"),
        symbol=symbol or metadata.get("symbol"),
        portfolio_name=portfolio_name or metadata.get("portfolio_name"),
        sweep_name=sweep_name,
        scan_name=scan_name,
        total_return=float(total_return) if total_return is not None else None,
        cagr=float(cagr) if cagr is not None else None,
        max_drawdown=float(max_dd) if max_dd is not None else None,
        sharpe=float(sharpe) if sharpe is not None else None,
        report_dir=report_dir_str,
        report_prefix=report_prefix,
        params_json=json.dumps(params, ensure_ascii=False),
        stats_json=json.dumps(stats, ensure_ascii=False),
        metadata_json=json.dumps(metadata, ensure_ascii=False),
    )
    return rec


def log_experiment_from_result(
    result: BacktestResult,
    run_type: str,
    run_name: str,
    strategy_key: Optional[str] = None,
    symbol: Optional[str] = None,
    portfolio_name: Optional[str] = None,
    sweep_name: Optional[str] = None,
    scan_name: Optional[str] = None,
    report_dir: Optional[Path] = None,
    report_prefix: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> ExperimentRecord:
    """
    Convenience-Funktion: Record aus Result bauen, in CSV schreiben, Record zurueckgeben.
    """
    record = build_record_from_result(
        result=result,
        run_type=run_type,
        run_name=run_name,
        strategy_key=strategy_key,
        symbol=symbol,
        portfolio_name=portfolio_name,
        sweep_name=sweep_name,
        scan_name=scan_name,
        report_dir=report_dir,
        report_prefix=report_prefix,
        extra_metadata=extra_metadata,
    )
    append_experiment_record(record)
    return record


def log_generic_experiment(
    run_type: str,
    run_name: str,
    strategy_key: Optional[str] = None,
    symbol: Optional[str] = None,
    portfolio_name: Optional[str] = None,
    sweep_name: Optional[str] = None,
    scan_name: Optional[str] = None,
    stats: Optional[Dict[str, Any]] = None,
    report_dir: Optional[Path] = None,
    report_prefix: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> ExperimentRecord:
    """
    Generic Logging für Experimente, die kein BacktestResult haben,
    z.B. Forward-Signal-Generierung oder externe Auswertungen.

    stats:
        Optionaler Dict mit Kennzahlen (z.B. total_return, cagr, sharpe, ...).
    extra_metadata:
        Zusätzliche Metadaten (wird in metadata_json gemerged).
    """
    stats = stats or {}
    metadata: Dict[str, Any] = {}
    if extra_metadata:
        metadata.update(extra_metadata)

    # Wenn stats Top-Level-Metriken enthalten, können wir sie direkt in die
    # entsprechenden Felder ziehen, sonst bleiben sie None.
    total_return = stats.get("total_return")
    cagr = stats.get("cagr")
    max_dd = stats.get("max_drawdown")
    sharpe = stats.get("sharpe")

    ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    report_dir_str = str(report_dir) if report_dir is not None else None

    record = ExperimentRecord(
        run_id=str(uuid.uuid4()),
        run_type=str(run_type),
        run_name=str(run_name),
        timestamp=ts,
        strategy_key=strategy_key,
        symbol=symbol,
        portfolio_name=portfolio_name,
        sweep_name=sweep_name,
        scan_name=scan_name,
        total_return=float(total_return) if total_return is not None else None,
        cagr=float(cagr) if cagr is not None else None,
        max_drawdown=float(max_dd) if max_dd is not None else None,
        sharpe=float(sharpe) if sharpe is not None else None,
        report_dir=report_dir_str,
        report_prefix=report_prefix,
        params_json=json.dumps({}, ensure_ascii=False),
        stats_json=json.dumps(stats, ensure_ascii=False),
        metadata_json=json.dumps(metadata, ensure_ascii=False),
    )

    append_experiment_record(record)
    return record


# =============================================================================
# CONVENIENCE HELPER FUNKTIONEN
# =============================================================================

def log_backtest_result(
    result: BacktestResult,
    *,
    strategy_name: str,
    tag: Optional[str] = None,
    config_path: Optional[str] = None,
    data_source: Optional[str] = None,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Loggt das Ergebnis eines Backtests in der Registry.

    Diese Funktion ist der empfohlene Weg, Backtest-Ergebnisse zu loggen.
    Sie verwendet intern log_experiment_from_result() mit run_type="backtest".

    Args:
        result: BacktestResult-Objekt mit equity_curve, trades, stats
        strategy_name: Name der Strategie (z.B. "ma_crossover")
        tag: Optionaler Tag für Filterung (z.B. "dev-test", "production")
        config_path: Pfad zur verwendeten Config
        data_source: Datenquelle (z.B. "kraken_csv", "binance_api")
        symbol: Symbol/Market (z.B. "BTC/EUR")
        timeframe: Timeframe (z.B. "1h", "4h", "1d")
        start_date: Startdatum des Backtests (ISO-Format)
        end_date: Enddatum des Backtests (ISO-Format)
        extra_metadata: Zusätzliche Metadaten

    Returns:
        run_id: Eindeutige ID des Runs

    Example:
        >>> from src.core.experiments import log_backtest_result
        >>> run_id = log_backtest_result(
        ...     result=backtest_result,
        ...     strategy_name="ma_crossover",
        ...     tag="dev-test",
        ...     config_path="config.toml",
        ... )
        >>> print(f"Logged with run_id: {run_id}")
    """
    ts_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_name = f"backtest_{strategy_name}_{ts_label}"
    if tag:
        run_name = f"backtest_{strategy_name}_{tag}_{ts_label}"

    metadata = {
        "tag": tag,
        "config_path": config_path,
        "data_source": data_source,
        "timeframe": timeframe,
        "start_date": start_date,
        "end_date": end_date,
        "runner": "run_backtest.py",
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    record = log_experiment_from_result(
        result=result,
        run_type=RUN_TYPE_BACKTEST,
        run_name=run_name,
        strategy_key=strategy_name,
        symbol=symbol,
        extra_metadata=metadata,
    )

    return record.run_id


def log_live_risk_check(
    metrics: Dict[str, Any],
    *,
    allowed: bool,
    reasons: List[str],
    orders_csv: Optional[str] = None,
    tag: Optional[str] = None,
    config_path: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Loggt einen Live-Risk-Check in der Registry.

    Args:
        metrics: Dict mit Risk-Metriken (n_orders, total_notional, etc.)
        allowed: Ob der Check bestanden wurde
        reasons: Liste von Verletzungen (leer wenn allowed=True)
        orders_csv: Pfad zur geprüften Orders-CSV
        tag: Optionaler Tag für Filterung
        config_path: Pfad zur verwendeten Config
        extra_metadata: Zusätzliche Metadaten

    Returns:
        run_id: Eindeutige ID des Runs
    """
    ts_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_name = f"live_risk_check_{ts_label}"
    if tag:
        run_name = f"live_risk_check_{tag}_{ts_label}"

    stats = {
        **metrics,
        "allowed": allowed,
        "n_violations": len(reasons),
    }

    metadata = {
        "tag": tag,
        "config_path": config_path,
        "orders_csv": orders_csv,
        "violations": reasons,
        "runner": "check_live_risk_limits.py",
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    record = log_generic_experiment(
        run_type=RUN_TYPE_LIVE_RISK_CHECK,
        run_name=run_name,
        stats=stats,
        extra_metadata=metadata,
    )

    return record.run_id


def log_forward_signal_run(
    *,
    strategy_key: str,
    symbol: str,
    timeframe: str,
    last_timestamp: "pd.Timestamp",
    last_signal: float,
    last_price: float,
    tag: Optional[str] = None,
    config_path: Optional[str] = None,
    exchange_name: Optional[str] = None,
    bars_fetched: Optional[int] = None,
    extra_stats: Optional[Dict[str, Any]] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Loggt einen Forward-Signal-Run in der Registry.

    Diese Funktion ist der empfohlene Weg, Forward-Signal-Runs zu loggen.
    Sie verwendet intern log_generic_experiment() mit run_type="forward_signal".

    Args:
        strategy_key: Name der Strategie (z.B. "ma_crossover")
        symbol: Trading-Pair (z.B. "BTC/EUR")
        timeframe: Timeframe (z.B. "1h", "4h")
        last_timestamp: Timestamp der letzten Bar
        last_signal: Signalwert der letzten Bar (-1, 0, +1)
        last_price: Schlusskurs der letzten Bar
        tag: Optionaler Tag für Filterung (z.B. "morning-scan")
        config_path: Pfad zur verwendeten Config
        exchange_name: Name des Exchange-Clients (z.B. "kraken")
        bars_fetched: Anzahl der abgerufenen Bars
        extra_stats: Zusätzliche Statistiken
        extra_metadata: Zusätzliche Metadaten

    Returns:
        run_id: Eindeutige ID des Runs

    Example:
        >>> run_id = log_forward_signal_run(
        ...     strategy_key="ma_crossover",
        ...     symbol="BTC/EUR",
        ...     timeframe="1h",
        ...     last_timestamp=pd.Timestamp("2025-12-05T10:00:00Z"),
        ...     last_signal=1.0,
        ...     last_price=43250.00,
        ...     tag="morning-scan",
        ... )
    """
    import pandas as pd  # Local import to avoid top-level dependency

    ts_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_name = f"forward_signal_{strategy_key}_{symbol.replace('/', '_')}_{ts_label}"
    if tag:
        run_name = f"forward_signal_{strategy_key}_{tag}_{ts_label}"

    # Stats
    stats: Dict[str, Any] = {
        "last_signal": float(last_signal),
        "last_price": float(last_price),
    }
    if extra_stats:
        stats.update(extra_stats)

    # Metadata
    metadata: Dict[str, Any] = {
        "symbol": symbol,
        "timeframe": timeframe,
        "strategy_key": strategy_key,
        "last_timestamp": (
            last_timestamp.isoformat()
            if isinstance(last_timestamp, pd.Timestamp)
            else str(last_timestamp)
        ),
        "config_path": config_path,
        "tag": tag,
        "exchange_name": exchange_name,
        "bars_fetched": bars_fetched,
        "runner": "run_forward_signals.py",
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    record = log_generic_experiment(
        run_type=RUN_TYPE_FORWARD_SIGNAL,
        run_name=run_name,
        strategy_key=strategy_key,
        symbol=symbol,
        stats=stats,
        extra_metadata=metadata,
    )

    return record.run_id


def log_portfolio_backtest_result(
    *,
    portfolio_name: str,
    equity_curve: "pd.Series",
    component_runs: List[Dict[str, Any]],
    portfolio_stats: Optional[Dict[str, Any]] = None,
    tag: Optional[str] = None,
    config_path: Optional[str] = None,
    allocation_method: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Loggt einen Portfolio-Backtest in der Registry.

    Diese Funktion ist der empfohlene Weg, Portfolio-Backtest-Ergebnisse zu loggen.
    Sie verwendet intern log_generic_experiment() mit run_type="portfolio_backtest".

    Args:
        portfolio_name: Name des Portfolios (z.B. "core_3-strat", "crypto_diversified")
        equity_curve: Aggregierte Portfolio-Equity-Curve (pd.Series)
        component_runs: Liste von Dicts mit Infos zu den Einzel-Runs:
            [
                {"run_id": "...", "strategy_key": "...", "symbol": "...",
                 "timeframe": "...", "weight": 0.33, "total_return": 0.05},
                ...
            ]
        portfolio_stats: Optional Dict mit Portfolio-Statistiken:
            {"total_return": 0.12, "max_drawdown": -0.08, "sharpe": 1.25, ...}
        tag: Optionaler Tag für Filterung (z.B. "weekend-research")
        config_path: Pfad zur verwendeten Config
        allocation_method: Allocation-Methode ("equal", "risk_parity", "sharpe_weighted", "manual")
        extra_metadata: Zusätzliche Metadaten

    Returns:
        run_id: Eindeutige ID des Portfolio-Runs

    Example:
        >>> run_id = log_portfolio_backtest_result(
        ...     portfolio_name="core_3-strat",
        ...     equity_curve=portfolio_equity,
        ...     component_runs=[
        ...         {"run_id": "abc", "strategy_key": "ma_crossover",
        ...          "symbol": "BTC/EUR", "weight": 0.33},
        ...         {"run_id": "def", "strategy_key": "rsi_reversion",
        ...          "symbol": "ETH/EUR", "weight": 0.33},
        ...     ],
        ...     portfolio_stats={"total_return": 0.12, "sharpe": 1.25},
        ...     tag="weekend-research",
        ... )
    """
    import pandas as pd  # Local import to avoid top-level dependency

    ts_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_name = f"portfolio_{portfolio_name}_{ts_label}"
    if tag:
        run_name = f"portfolio_{portfolio_name}_{tag}_{ts_label}"

    # Stats aus equity_curve berechnen (falls nicht übergeben)
    if portfolio_stats is None:
        portfolio_stats = {}

    # Basis-Stats aus equity_curve berechnen wenn nicht vorhanden
    if "total_return" not in portfolio_stats and len(equity_curve) > 0:
        initial = equity_curve.iloc[0]
        final = equity_curve.iloc[-1]
        portfolio_stats["total_return"] = (final / initial) - 1.0 if initial > 0 else 0.0

    if "max_drawdown" not in portfolio_stats and len(equity_curve) > 0:
        rolling_max = equity_curve.expanding().max()
        drawdown = (equity_curve - rolling_max) / rolling_max
        portfolio_stats["max_drawdown"] = float(drawdown.min())

    if "sharpe" not in portfolio_stats and len(equity_curve) > 1:
        returns = equity_curve.pct_change().dropna()
        if len(returns) > 0 and returns.std() > 0:
            # Annualisierter Sharpe (angenommen hourly data)
            portfolio_stats["sharpe"] = float(
                returns.mean() / returns.std() * (252 * 24) ** 0.5
            )
        else:
            portfolio_stats["sharpe"] = 0.0

    # Stats für Registry (Top-Level-Felder)
    stats = {
        "total_return": portfolio_stats.get("total_return"),
        "max_drawdown": portfolio_stats.get("max_drawdown"),
        "sharpe": portfolio_stats.get("sharpe"),
        "cagr": portfolio_stats.get("cagr"),
        "num_components": len(component_runs),
    }

    # Metadata
    metadata: Dict[str, Any] = {
        "portfolio_name": portfolio_name,
        "components": component_runs,
        "allocation_method": allocation_method,
        "tag": tag,
        "config_path": config_path,
        "runner": "run_portfolio_backtest.py",
        "equity_start": float(equity_curve.iloc[0]) if len(equity_curve) > 0 else None,
        "equity_end": float(equity_curve.iloc[-1]) if len(equity_curve) > 0 else None,
        "n_bars": len(equity_curve),
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    record = log_generic_experiment(
        run_type=RUN_TYPE_PORTFOLIO_BACKTEST,
        run_name=run_name,
        portfolio_name=portfolio_name,
        stats=stats,
        extra_metadata=metadata,
    )

    return record.run_id


def log_paper_trade_run(
    stats: Dict[str, Any],
    *,
    strategy_name: Optional[str] = None,
    orders_csv: Optional[str] = None,
    positions_csv: Optional[str] = None,
    trades_csv: Optional[str] = None,
    tag: Optional[str] = None,
    config_path: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Loggt einen Paper-Trade-Run in der Registry.

    Args:
        stats: Dict mit Paper-Trade-Metriken (starting_cash, equity, etc.)
        strategy_name: Name der Strategie (falls bekannt)
        orders_csv: Pfad zur Orders-CSV
        positions_csv: Pfad zur generierten Positions-CSV
        trades_csv: Pfad zur generierten Trades-CSV
        tag: Optionaler Tag für Filterung
        config_path: Pfad zur verwendeten Config
        extra_metadata: Zusätzliche Metadaten

    Returns:
        run_id: Eindeutige ID des Runs
    """
    ts_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_name = f"paper_trade_{ts_label}"
    if tag:
        run_name = f"paper_trade_{tag}_{ts_label}"

    metadata = {
        "tag": tag,
        "config_path": config_path,
        "orders_csv": orders_csv,
        "positions_csv": positions_csv,
        "trades_csv": trades_csv,
        "runner": "paper_trade_from_orders.py",
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    record = log_generic_experiment(
        run_type=RUN_TYPE_PAPER_TRADE,
        run_name=run_name,
        strategy_key=strategy_name,
        stats=stats,
        extra_metadata=metadata,
    )

    return record.run_id


def log_sweep_run(
    *,
    strategy_key: str,
    symbol: str,
    timeframe: str,
    params: Dict[str, Any],
    stats: Dict[str, Any],
    sweep_name: Optional[str] = None,
    backtest_run_id: Optional[str] = None,
    tag: Optional[str] = None,
    config_path: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Loggt einen einzelnen Sweep-Run (eine Parameterkombination) in der Registry.

    Diese Funktion ist für Parameter-Sweeps gedacht, bei denen viele
    Parameterkombinationen durchgetestet werden.

    Args:
        strategy_key: Name der Strategie (z.B. "ma_crossover")
        symbol: Trading-Pair (z.B. "BTC/EUR")
        timeframe: Timeframe (z.B. "1h", "4h")
        params: Die konkrete Parameterkombination (z.B. {"short_window": 10, "long_window": 50})
        stats: Backtest-Statistiken (z.B. {"total_return": 0.15, "sharpe": 1.2})
        sweep_name: Optionaler Name für den Sweep (z.B. "ma_grid_2025-01")
        backtest_run_id: Optionale Referenz auf den zugehörigen Backtest-Run
        tag: Optionaler Tag für Filterung (z.B. "grid-search", "optimization")
        config_path: Pfad zur verwendeten Config
        extra_metadata: Zusätzliche Metadaten

    Returns:
        run_id: Eindeutige ID des Sweep-Runs

    Example:
        >>> run_id = log_sweep_run(
        ...     strategy_key="ma_crossover",
        ...     symbol="BTC/EUR",
        ...     timeframe="1h",
        ...     params={"short_window": 10, "long_window": 50},
        ...     stats={"total_return": 0.15, "sharpe": 1.2, "max_drawdown": -0.08},
        ...     sweep_name="ma_grid_optimization",
        ...     tag="grid-search",
        ... )
    """
    ts_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    sweep_label = sweep_name or f"{strategy_key}_sweep"
    run_name = f"sweep_{sweep_label}_{ts_label}"
    if tag:
        run_name = f"sweep_{sweep_label}_{tag}_{ts_label}"

    # Metadata
    metadata: Dict[str, Any] = {
        "symbol": symbol,
        "timeframe": timeframe,
        "strategy_key": strategy_key,
        "params": params,
        "sweep_name": sweep_name,
        "backtest_run_id": backtest_run_id,
        "tag": tag,
        "config_path": config_path,
        "runner": "run_sweep.py",
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    record = ExperimentRecord(
        run_id=str(uuid.uuid4()),
        run_type=RUN_TYPE_SWEEP,
        run_name=run_name,
        timestamp=datetime.utcnow().isoformat(timespec="seconds") + "Z",
        strategy_key=strategy_key,
        symbol=symbol,
        sweep_name=sweep_name,
        total_return=float(stats.get("total_return")) if stats.get("total_return") is not None else None,
        cagr=float(stats.get("cagr")) if stats.get("cagr") is not None else None,
        max_drawdown=float(stats.get("max_drawdown")) if stats.get("max_drawdown") is not None else None,
        sharpe=float(stats.get("sharpe")) if stats.get("sharpe") is not None else None,
        params_json=json.dumps(params, ensure_ascii=False),
        stats_json=json.dumps(stats, ensure_ascii=False),
        metadata_json=json.dumps(metadata, ensure_ascii=False),
    )

    append_experiment_record(record)
    return record.run_id


def log_market_scan_result(
    *,
    strategy_key: str,
    symbol: str,
    timeframe: str,
    mode: str,
    signal: Optional[float] = None,
    stats: Optional[Dict[str, Any]] = None,
    scan_name: Optional[str] = None,
    tag: Optional[str] = None,
    config_path: Optional[str] = None,
    bars_fetched: Optional[int] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Loggt das Ergebnis eines Market-Scans für ein einzelnes Symbol.

    Market-Scans prüfen mehrere Symbole/Timeframes mit einer oder mehreren
    Strategien und loggen die Ergebnisse für spätere Analyse.

    Args:
        strategy_key: Name der Strategie (z.B. "ma_crossover")
        symbol: Trading-Pair (z.B. "BTC/EUR")
        timeframe: Timeframe (z.B. "1h", "4h")
        mode: Scan-Modus ("forward" oder "backtest-lite")
        signal: Letztes Signal bei mode="forward" (-1, 0, +1)
        stats: Backtest-Statistiken bei mode="backtest-lite"
        scan_name: Optionaler Name für den Scan (z.B. "daily_scan_2025-01")
        tag: Optionaler Tag für Filterung (z.B. "morning-scan", "daily")
        config_path: Pfad zur verwendeten Config
        bars_fetched: Anzahl der abgerufenen Bars
        extra_metadata: Zusätzliche Metadaten

    Returns:
        run_id: Eindeutige ID des Scan-Runs

    Example:
        >>> # Forward-Mode
        >>> run_id = log_market_scan_result(
        ...     strategy_key="ma_crossover",
        ...     symbol="BTC/EUR",
        ...     timeframe="1h",
        ...     mode="forward",
        ...     signal=1.0,
        ...     tag="morning-scan",
        ... )

        >>> # Backtest-Lite-Mode
        >>> run_id = log_market_scan_result(
        ...     strategy_key="rsi_reversion",
        ...     symbol="ETH/EUR",
        ...     timeframe="4h",
        ...     mode="backtest-lite",
        ...     stats={"total_return": 0.08, "sharpe": 0.9},
        ...     tag="weekly-scan",
        ... )
    """
    ts_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    scan_label = scan_name or f"{strategy_key}_scan"
    run_name = f"market_scan_{scan_label}_{symbol.replace('/', '_')}_{ts_label}"
    if tag:
        run_name = f"market_scan_{scan_label}_{tag}_{ts_label}"

    # Stats aufbauen
    result_stats: Dict[str, Any] = {}
    if signal is not None:
        result_stats["last_signal"] = float(signal)
    if stats:
        result_stats.update(stats)

    # Metadata
    metadata: Dict[str, Any] = {
        "symbol": symbol,
        "timeframe": timeframe,
        "strategy_key": strategy_key,
        "mode": mode,
        "scan_name": scan_name,
        "tag": tag,
        "config_path": config_path,
        "bars_fetched": bars_fetched,
        "runner": "run_market_scan.py",
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    record = ExperimentRecord(
        run_id=str(uuid.uuid4()),
        run_type=RUN_TYPE_MARKET_SCAN,
        run_name=run_name,
        timestamp=datetime.utcnow().isoformat(timespec="seconds") + "Z",
        strategy_key=strategy_key,
        symbol=symbol,
        scan_name=scan_name,
        total_return=float(result_stats.get("total_return")) if result_stats.get("total_return") is not None else None,
        cagr=float(result_stats.get("cagr")) if result_stats.get("cagr") is not None else None,
        max_drawdown=float(result_stats.get("max_drawdown")) if result_stats.get("max_drawdown") is not None else None,
        sharpe=float(result_stats.get("sharpe")) if result_stats.get("sharpe") is not None else None,
        params_json=json.dumps({}, ensure_ascii=False),
        stats_json=json.dumps(result_stats, ensure_ascii=False),
        metadata_json=json.dumps(metadata, ensure_ascii=False),
    )

    append_experiment_record(record)
    return record.run_id


def log_scheduler_job_run(
    *,
    job_name: str,
    command: str,
    args: Dict[str, Any],
    return_code: int,
    started_at: datetime,
    finished_at: datetime,
    tag: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Loggt einen Scheduler-Job-Run in der Registry.

    Diese Funktion wird vom Scheduler nach jeder Job-Ausführung aufgerufen.

    Args:
        job_name: Name des Jobs
        command: Ausgeführtes Kommando (z.B. "python")
        args: Job-Argumente (script, strategy, etc.)
        return_code: Exit-Code des Jobs
        started_at: Startzeitpunkt
        finished_at: Endzeitpunkt
        tag: Optionaler Tag
        extra_metadata: Zusätzliche Metadaten

    Returns:
        run_id: Eindeutige ID des Scheduler-Job-Runs

    Example:
        >>> run_id = log_scheduler_job_run(
        ...     job_name="daily_forward_signals",
        ...     command="python",
        ...     args={"script": "scripts/run_forward_signals.py", "strategy": "ma_crossover"},
        ...     return_code=0,
        ...     started_at=datetime.utcnow(),
        ...     finished_at=datetime.utcnow(),
        ...     tag="daily",
        ... )
    """
    ts_label = started_at.strftime("%Y%m%d_%H%M%S")
    run_name = f"scheduler_{job_name}_{ts_label}"

    duration_seconds = (finished_at - started_at).total_seconds()
    success = return_code == 0

    # Stats
    stats: Dict[str, Any] = {
        "return_code": return_code,
        "success": success,
        "duration_seconds": duration_seconds,
    }

    # Metadata
    metadata: Dict[str, Any] = {
        "job_name": job_name,
        "command": command,
        "args": args,
        "started_at": started_at.isoformat(timespec="seconds") + "Z",
        "finished_at": finished_at.isoformat(timespec="seconds") + "Z",
        "tag": tag,
        "runner": "run_scheduler.py",
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    record = ExperimentRecord(
        run_id=str(uuid.uuid4()),
        run_type=RUN_TYPE_SCHEDULER_JOB,
        run_name=run_name,
        timestamp=started_at.isoformat(timespec="seconds") + "Z",
        params_json=json.dumps(args, ensure_ascii=False),
        stats_json=json.dumps(stats, ensure_ascii=False),
        metadata_json=json.dumps(metadata, ensure_ascii=False),
    )

    append_experiment_record(record)
    return record.run_id


def log_shadow_run(
    *,
    strategy_key: str,
    symbol: str,
    timeframe: str,
    stats: Dict[str, Any],
    execution_summary: Optional[Dict[str, Any]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tag: Optional[str] = None,
    config_path: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Loggt einen Shadow-/Dry-Run in der Registry (Phase 24).

    Ein Shadow-Run simuliert die Execution-Pipeline ohne echte API-Calls.
    Orders werden nur simuliert und geloggt.

    Args:
        strategy_key: Name der Strategie (z.B. "ma_crossover")
        symbol: Trading-Pair (z.B. "BTC/EUR")
        timeframe: Timeframe (z.B. "1h", "4h")
        stats: Backtest-/Execution-Statistiken (z.B. total_return, sharpe, ...)
        execution_summary: Zusammenfassung der Shadow-Execution
            (z.B. total_orders, filled_orders, total_notional, ...)
        start_date: Startdatum des Shadow-Runs (ISO-Format)
        end_date: Enddatum des Shadow-Runs (ISO-Format)
        tag: Optionaler Tag für Filterung (z.B. "shadow_test_v1")
        config_path: Pfad zur verwendeten Config
        extra_metadata: Zusätzliche Metadaten

    Returns:
        run_id: Eindeutige ID des Shadow-Runs

    Example:
        >>> run_id = log_shadow_run(
        ...     strategy_key="ma_crossover",
        ...     symbol="BTC/EUR",
        ...     timeframe="1h",
        ...     stats={"total_return": 0.08, "sharpe": 1.1, "max_drawdown": -0.05},
        ...     execution_summary={
        ...         "total_orders": 42,
        ...         "filled_orders": 40,
        ...         "total_notional": 125000.0,
        ...         "total_fees": 62.50,
        ...     },
        ...     tag="shadow_test_v1",
        ... )
    """
    ts_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_name = f"shadow_{strategy_key}_{symbol.replace('/', '_')}_{ts_label}"
    if tag:
        run_name = f"shadow_{strategy_key}_{tag}_{ts_label}"

    # Stats für Registry (Top-Level-Felder)
    result_stats: Dict[str, Any] = dict(stats)

    # Execution-Summary in Stats mergen
    if execution_summary:
        result_stats["execution"] = execution_summary

    # Metadata
    metadata: Dict[str, Any] = {
        "symbol": symbol,
        "timeframe": timeframe,
        "strategy_key": strategy_key,
        "start_date": start_date,
        "end_date": end_date,
        "tag": tag,
        "config_path": config_path,
        "runner": "run_shadow_execution.py",
        "mode": "shadow_run",
    }
    if execution_summary:
        metadata["execution_summary"] = execution_summary
    if extra_metadata:
        metadata.update(extra_metadata)

    record = ExperimentRecord(
        run_id=str(uuid.uuid4()),
        run_type=RUN_TYPE_SHADOW_RUN,
        run_name=run_name,
        timestamp=datetime.utcnow().isoformat(timespec="seconds") + "Z",
        strategy_key=strategy_key,
        symbol=symbol,
        total_return=float(result_stats.get("total_return")) if result_stats.get("total_return") is not None else None,
        cagr=float(result_stats.get("cagr")) if result_stats.get("cagr") is not None else None,
        max_drawdown=float(result_stats.get("max_drawdown")) if result_stats.get("max_drawdown") is not None else None,
        sharpe=float(result_stats.get("sharpe")) if result_stats.get("sharpe") is not None else None,
        params_json=json.dumps({}, ensure_ascii=False),
        stats_json=json.dumps(result_stats, ensure_ascii=False),
        metadata_json=json.dumps(metadata, ensure_ascii=False),
    )

    append_experiment_record(record)
    return record.run_id


# =============================================================================
# ANALYSE-FUNKTIONEN (Lesen aus Registry)
# =============================================================================

def load_experiments_df() -> "pd.DataFrame":
    """
    Lädt alle Experiments aus der CSV als pandas DataFrame.

    Returns:
        DataFrame mit allen Experiment-Records

    Raises:
        FileNotFoundError: Wenn noch keine Experiments existieren
    """
    import pandas as pd

    if not EXPERIMENTS_CSV.exists():
        raise FileNotFoundError(
            f"Keine Experiments gefunden. Datei existiert nicht: {EXPERIMENTS_CSV}"
        )

    df = pd.read_csv(EXPERIMENTS_CSV)
    return df


def get_experiment_by_id(run_id: str) -> Optional[ExperimentRecord]:
    """
    Holt einen einzelnen Experiment-Record per run_id.

    Args:
        run_id: Eindeutige Run-ID (UUID)

    Returns:
        ExperimentRecord oder None wenn nicht gefunden
    """
    try:
        df = load_experiments_df()
    except FileNotFoundError:
        return None

    matches = df[df["run_id"] == run_id]
    if matches.empty:
        return None

    row = matches.iloc[0].to_dict()
    return ExperimentRecord(**row)


def list_experiments(
    run_type: Optional[str] = None,
    tag: Optional[str] = None,
    strategy_key: Optional[str] = None,
    limit: int = 20,
) -> List[ExperimentRecord]:
    """
    Listet Experiments mit optionalen Filtern.

    Args:
        run_type: Filter nach run_type (z.B. "backtest")
        tag: Filter nach tag im metadata_json
        strategy_key: Filter nach Strategie
        limit: Maximale Anzahl Ergebnisse

    Returns:
        Liste von ExperimentRecord-Objekten (neueste zuerst)
    """
    try:
        df = load_experiments_df()
    except FileNotFoundError:
        return []

    # Filter anwenden
    if run_type:
        df = df[df["run_type"] == run_type]

    if strategy_key:
        df = df[df["strategy_key"] == strategy_key]

    if tag:
        # Tag steht im metadata_json
        def has_tag(row):
            try:
                meta = json.loads(row.get("metadata_json", "{}"))
                return meta.get("tag") == tag
            except (json.JSONDecodeError, TypeError):
                return False

        df = df[df.apply(has_tag, axis=1)]

    # Nach Timestamp sortieren (neueste zuerst)
    if "timestamp" in df.columns:
        df = df.sort_values("timestamp", ascending=False)

    # Limit anwenden
    df = df.head(limit)

    # In Records umwandeln
    records = []
    for _, row in df.iterrows():
        try:
            records.append(ExperimentRecord(**row.to_dict()))
        except (TypeError, ValueError):
            continue

    return records


def get_experiment_stats(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Holt die Stats eines Experiments als Dict.

    Args:
        run_id: Eindeutige Run-ID

    Returns:
        Stats-Dict oder None wenn nicht gefunden
    """
    record = get_experiment_by_id(run_id)
    if record is None:
        return None

    try:
        return json.loads(record.stats_json)
    except (json.JSONDecodeError, TypeError):
        return {}


def get_experiment_metadata(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Holt die Metadata eines Experiments als Dict.

    Args:
        run_id: Eindeutige Run-ID

    Returns:
        Metadata-Dict oder None wenn nicht gefunden
    """
    record = get_experiment_by_id(run_id)
    if record is None:
        return None

    try:
        return json.loads(record.metadata_json)
    except (json.JSONDecodeError, TypeError):
        return {}
