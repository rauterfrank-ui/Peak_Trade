# src/experiments/base.py
"""
Peak_Trade Experiments Base Types (Phase 29)
=============================================

Kern-Datenstrukturen und ExperimentRunner für Parameter-Sweeps.

Komponenten:
- ParamSweep: Definiert einen Parameter-Bereich
- ExperimentConfig: Konfiguration für einen Sweep
- SweepResultRow: Einzelnes Ergebnis
- ExperimentResult: Gesamtergebnis eines Sweeps
- ExperimentRunner: Führt Sweeps aus

Der ExperimentRunner generiert das kartesische Produkt aller
Parameter-Kombinationen und führt für jede einen Backtest durch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from itertools import product
from typing import Any, Callable, Dict, List, Optional, Union
import hashlib
import json
import logging
import time
import traceback

import pandas as pd

logger = logging.getLogger(__name__)


# ============================================================================
# PARAM SWEEP
# ============================================================================


@dataclass
class ParamSweep:
    """
    Definiert einen Parameter-Bereich für Sweeps.

    Attributes:
        name: Name des Parameters (z.B. "fast_period")
        values: Liste möglicher Werte oder Range-Definition
        description: Optionale Beschreibung

    Example:
        >>> # Explizite Werte
        >>> sweep = ParamSweep("fast_period", [5, 10, 20, 50])
        >>>
        >>> # Mit Beschreibung
        >>> sweep = ParamSweep(
        ...     name="adx_threshold",
        ...     values=[20, 25, 30],
        ...     description="ADX-Schwellwert für Trend-Erkennung"
        ... )
    """

    name: str
    values: List[Any]
    description: Optional[str] = None

    def __post_init__(self) -> None:
        """Validierung nach Initialisierung."""
        if not self.name:
            raise ValueError("ParamSweep.name darf nicht leer sein")
        if not self.values:
            raise ValueError(f"ParamSweep '{self.name}' muss mindestens einen Wert haben")

    @classmethod
    def from_range(
        cls,
        name: str,
        start: float,
        stop: float,
        step: float,
        description: Optional[str] = None,
    ) -> "ParamSweep":
        """
        Erstellt ParamSweep aus Range-Definition.

        Args:
            name: Parameter-Name
            start: Startwert (inklusive)
            stop: Endwert (inklusive)
            step: Schrittweite
            description: Optionale Beschreibung

        Returns:
            ParamSweep mit generierten Werten

        Example:
            >>> sweep = ParamSweep.from_range("fast_period", 5, 25, 5)
            >>> print(sweep.values)
            [5, 10, 15, 20, 25]
        """
        import numpy as np

        values = list(np.arange(start, stop + step / 2, step))
        # Konvertiere zu int wenn sinnvoll
        if all(v == int(v) for v in values):
            values = [int(v) for v in values]
        return cls(name=name, values=values, description=description)

    @classmethod
    def from_logspace(
        cls,
        name: str,
        start: float,
        stop: float,
        num: int,
        description: Optional[str] = None,
    ) -> "ParamSweep":
        """
        Erstellt ParamSweep mit logarithmisch verteilten Werten.

        Args:
            name: Parameter-Name
            start: Startwert
            stop: Endwert
            num: Anzahl der Werte
            description: Optionale Beschreibung

        Returns:
            ParamSweep mit logarithmisch verteilten Werten

        Example:
            >>> sweep = ParamSweep.from_logspace("window", 10, 1000, 4)
            >>> print(sweep.values)
            [10, 46, 215, 1000]
        """
        import numpy as np

        values = list(np.logspace(np.log10(start), np.log10(stop), num))
        # Runde auf sinnvolle Werte
        values = [round(v, 2) if v < 1 else int(round(v)) for v in values]
        return cls(name=name, values=values, description=description)

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "name": self.name,
            "values": self.values,
            "description": self.description,
            "num_values": len(self.values),
        }


# ============================================================================
# EXPERIMENT CONFIG
# ============================================================================


@dataclass
class ExperimentConfig:
    """
    Konfiguration für einen Experiment-Durchlauf.

    Attributes:
        name: Name des Experiments
        strategy_name: Name der Strategie (aus Registry)
        param_sweeps: Liste von ParamSweep-Objekten
        symbols: Liste der Symbole zum Testen
        timeframe: Zeitrahmen (z.B. "1h", "4h", "1d")
        start_date: Start-Datum für Backtest
        end_date: End-Datum für Backtest
        initial_capital: Startkapital
        regime_config: Optionale Regime-Detection-Konfiguration
        switching_config: Optionale Strategy-Switching-Konfiguration
        base_params: Basis-Parameter, die nicht gesweept werden
        metrics_to_collect: Welche Metriken gesammelt werden
        parallel: Ob parallel ausgeführt werden soll
        max_workers: Max. Anzahl paralleler Worker
        save_results: Ob Ergebnisse gespeichert werden sollen
        output_dir: Ausgabe-Verzeichnis
        tags: Optionale Tags für Kategorisierung

    Example:
        >>> config = ExperimentConfig(
        ...     name="MA Crossover Parameter Optimization",
        ...     strategy_name="ma_crossover",
        ...     param_sweeps=[
        ...         ParamSweep("fast_period", [5, 10, 20]),
        ...         ParamSweep("slow_period", [50, 100, 200]),
        ...     ],
        ...     symbols=["BTC/EUR", "ETH/EUR"],
        ...     timeframe="1h",
        ...     start_date="2024-01-01",
        ...     end_date="2024-06-01",
        ... )
    """

    name: str
    strategy_name: str
    param_sweeps: List[ParamSweep] = field(default_factory=list)
    symbols: List[str] = field(default_factory=lambda: ["BTC/EUR"])
    timeframe: str = "1h"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: float = 10000.0
    regime_config: Optional[Dict[str, Any]] = None
    switching_config: Optional[Dict[str, Any]] = None
    base_params: Dict[str, Any] = field(default_factory=dict)
    metrics_to_collect: List[str] = field(
        default_factory=lambda: [
            "total_return",
            "sharpe_ratio",
            "max_drawdown",
            "win_rate",
            "num_trades",
            "profit_factor",
            "ulcer_index",
            "recovery_factor",
        ]
    )
    parallel: bool = False
    max_workers: int = 4
    save_results: bool = True
    output_dir: str = "reports/experiments"
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validierung nach Initialisierung."""
        if not self.name:
            raise ValueError("ExperimentConfig.name darf nicht leer sein")
        if not self.strategy_name:
            raise ValueError("ExperimentConfig.strategy_name darf nicht leer sein")

    @property
    def num_combinations(self) -> int:
        """Berechnet die Anzahl aller Parameter-Kombinationen."""
        if not self.param_sweeps:
            return 1
        n = 1
        for sweep in self.param_sweeps:
            n *= len(sweep.values)
        return n * len(self.symbols)

    def generate_param_combinations(self) -> List[Dict[str, Any]]:
        """
        Generiert das kartesische Produkt aller Parameter-Kombinationen.

        Returns:
            Liste von Parameter-Dictionaries

        Example:
            >>> config = ExperimentConfig(
            ...     name="test",
            ...     strategy_name="ma_crossover",
            ...     param_sweeps=[
            ...         ParamSweep("fast", [5, 10]),
            ...         ParamSweep("slow", [50, 100]),
            ...     ],
            ... )
            >>> combos = config.generate_param_combinations()
            >>> print(len(combos))
            4
            >>> print(combos[0])
            {'fast': 5, 'slow': 50}
        """
        if not self.param_sweeps:
            return [{}]

        param_names = [s.name for s in self.param_sweeps]
        param_values = [s.values for s in self.param_sweeps]

        combinations = []
        for combo in product(*param_values):
            param_dict = dict(zip(param_names, combo))
            # Merge mit base_params (base_params werden überschrieben)
            full_params = {**self.base_params, **param_dict}
            combinations.append(full_params)

        return combinations

    def get_experiment_id(self) -> str:
        """
        Generiert eine eindeutige ID für dieses Experiment.

        Returns:
            Hex-String basierend auf Config-Hash
        """
        config_str = json.dumps(
            {
                "name": self.name,
                "strategy": self.strategy_name,
                "sweeps": [s.to_dict() for s in self.param_sweeps],
                "symbols": self.symbols,
                "timeframe": self.timeframe,
            },
            sort_keys=True,
        )
        return hashlib.md5(config_str.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "name": self.name,
            "strategy_name": self.strategy_name,
            "param_sweeps": [s.to_dict() for s in self.param_sweeps],
            "symbols": self.symbols,
            "timeframe": self.timeframe,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_capital": self.initial_capital,
            "regime_config": self.regime_config,
            "switching_config": self.switching_config,
            "base_params": self.base_params,
            "metrics_to_collect": self.metrics_to_collect,
            "num_combinations": self.num_combinations,
            "tags": self.tags,
        }


# ============================================================================
# SWEEP RESULT ROW
# ============================================================================


@dataclass
class SweepResultRow:
    """
    Ein einzelnes Ergebnis aus einem Parameter-Sweep.

    Attributes:
        experiment_id: ID des Experiments
        run_id: Eindeutige ID dieses Runs
        strategy_name: Name der Strategie
        symbol: Gehandeltes Symbol
        timeframe: Zeitrahmen
        params: Parameter-Dict für diesen Run
        metrics: Berechnete Metriken
        start_date: Backtest-Startdatum
        end_date: Backtest-Enddatum
        runtime_seconds: Laufzeit des Backtests
        success: Ob der Run erfolgreich war
        error_message: Fehlermeldung (falls nicht erfolgreich)
        timestamp: Zeitstempel der Ausführung
        regime_info: Optionale Regime-Informationen

    Example:
        >>> result = SweepResultRow(
        ...     experiment_id="abc123",
        ...     run_id="abc123_001",
        ...     strategy_name="ma_crossover",
        ...     symbol="BTC/EUR",
        ...     timeframe="1h",
        ...     params={"fast_period": 10, "slow_period": 50},
        ...     metrics={"total_return": 0.15, "sharpe_ratio": 1.2},
        ...     start_date="2024-01-01",
        ...     end_date="2024-06-01",
        ...     runtime_seconds=0.5,
        ...     success=True,
        ... )
    """

    experiment_id: str
    run_id: str
    strategy_name: str
    symbol: str
    timeframe: str
    params: Dict[str, Any]
    metrics: Dict[str, float]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    runtime_seconds: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    regime_info: Optional[Dict[str, Any]] = None

    def to_flat_dict(self) -> Dict[str, Any]:
        """
        Konvertiert zu flachem Dictionary für DataFrame-Erstellung.

        Parameter und Metriken werden mit Prefix versehen:
        - params -> param_*
        - metrics -> metric_*
        """
        flat = {
            "experiment_id": self.experiment_id,
            "run_id": self.run_id,
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "runtime_seconds": self.runtime_seconds,
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
        }

        # Parameter mit Prefix
        for k, v in self.params.items():
            flat[f"param_{k}"] = v

        # Metriken mit Prefix
        for k, v in self.metrics.items():
            flat[f"metric_{k}"] = v

        # Regime-Info falls vorhanden
        if self.regime_info:
            for k, v in self.regime_info.items():
                flat[f"regime_{k}"] = v

        return flat

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu nested Dictionary."""
        return {
            "experiment_id": self.experiment_id,
            "run_id": self.run_id,
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "params": self.params,
            "metrics": self.metrics,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "runtime_seconds": self.runtime_seconds,
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
            "regime_info": self.regime_info,
        }


# ============================================================================
# EXPERIMENT RESULT
# ============================================================================


@dataclass
class ExperimentResult:
    """
    Gesamtergebnis eines Experiments (alle Sweep-Runs).

    Attributes:
        experiment_id: ID des Experiments
        config: ExperimentConfig
        results: Liste aller SweepResultRow
        total_runtime_seconds: Gesamtlaufzeit
        start_time: Startzeitpunkt
        end_time: Endzeitpunkt
        success_rate: Anteil erfolgreicher Runs

    Example:
        >>> result = runner.run(config)
        >>> df = result.to_dataframe()
        >>> best = result.get_best_by_metric("sharpe_ratio")
    """

    experiment_id: str
    config: ExperimentConfig
    results: List[SweepResultRow] = field(default_factory=list)
    total_runtime_seconds: float = 0.0
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    @property
    def num_runs(self) -> int:
        """Anzahl der durchgeführten Runs."""
        return len(self.results)

    @property
    def num_successful(self) -> int:
        """Anzahl erfolgreicher Runs."""
        return sum(1 for r in self.results if r.success)

    @property
    def num_failed(self) -> int:
        """Anzahl fehlgeschlagener Runs."""
        return sum(1 for r in self.results if not r.success)

    @property
    def success_rate(self) -> float:
        """Erfolgsquote (0.0 bis 1.0)."""
        if not self.results:
            return 0.0
        return self.num_successful / len(self.results)

    def to_dataframe(self) -> pd.DataFrame:
        """
        Konvertiert alle Ergebnisse zu einem DataFrame.

        Returns:
            DataFrame mit einer Zeile pro Run
        """
        if not self.results:
            return pd.DataFrame()

        rows = [r.to_flat_dict() for r in self.results]
        df = pd.DataFrame(rows)

        # Sortiere Spalten
        cols = sorted(
            df.columns,
            key=lambda x: (
                0
                if x in ["experiment_id", "run_id", "strategy_name", "symbol", "timeframe"]
                else 1
                if x.startswith("param_")
                else 2
                if x.startswith("metric_")
                else 3
            ),
        )
        return df[cols]

    def get_best_by_metric(
        self,
        metric: str,
        ascending: bool = False,
        top_n: int = 1,
    ) -> List[SweepResultRow]:
        """
        Gibt die besten Runs nach einer Metrik zurück.

        Args:
            metric: Name der Metrik (ohne "metric_" Prefix)
            ascending: True für niedrigste Werte zuerst
            top_n: Anzahl der Top-Ergebnisse

        Returns:
            Liste der besten SweepResultRow-Objekte
        """
        successful = [r for r in self.results if r.success and metric in r.metrics]
        if not successful:
            return []

        sorted_results = sorted(
            successful,
            key=lambda r: r.metrics.get(metric, float("-inf" if not ascending else "inf")),
            reverse=not ascending,
        )

        return sorted_results[:top_n]

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Berechnet zusammenfassende Statistiken über alle Runs.

        Returns:
            Dict mit Statistiken pro Metrik
        """
        if not self.results:
            return {}

        df = self.to_dataframe()
        metric_cols = [c for c in df.columns if c.startswith("metric_")]

        summary = {
            "num_runs": self.num_runs,
            "num_successful": self.num_successful,
            "num_failed": self.num_failed,
            "success_rate": self.success_rate,
            "total_runtime_seconds": self.total_runtime_seconds,
        }

        for col in metric_cols:
            metric_name = col.replace("metric_", "")
            values = df[col].dropna()
            if len(values) > 0:
                summary[f"{metric_name}_mean"] = values.mean()
                summary[f"{metric_name}_std"] = values.std()
                summary[f"{metric_name}_min"] = values.min()
                summary[f"{metric_name}_max"] = values.max()
                summary[f"{metric_name}_median"] = values.median()

        return summary

    def save_csv(self, filepath: str) -> None:
        """Speichert Ergebnisse als CSV."""
        df = self.to_dataframe()
        df.to_csv(filepath, index=False)
        logger.info(f"Ergebnisse gespeichert: {filepath}")

    def save_parquet(self, filepath: str) -> None:
        """Speichert Ergebnisse als Parquet."""
        df = self.to_dataframe()
        df.to_parquet(filepath, index=False)
        logger.info(f"Ergebnisse gespeichert: {filepath}")

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "experiment_id": self.experiment_id,
            "config": self.config.to_dict(),
            "num_runs": self.num_runs,
            "num_successful": self.num_successful,
            "num_failed": self.num_failed,
            "success_rate": self.success_rate,
            "total_runtime_seconds": self.total_runtime_seconds,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "summary_stats": self.get_summary_stats(),
        }


# ============================================================================
# EXPERIMENT RUNNER
# ============================================================================

# Type alias für Backtest-Funktion
BacktestFunction = Callable[
    [str, Dict[str, Any], str, str, Optional[str], Optional[str], float],
    Dict[str, Any],
]


class ExperimentRunner:
    """
    Führt Parameter-Sweeps aus und sammelt Ergebnisse.

    Der Runner generiert das kartesische Produkt aller Parameter-Kombinationen
    und führt für jede Kombination einen Backtest durch.

    Attributes:
        backtest_fn: Backtest-Funktion (Default: _default_backtest)
        progress_callback: Optionaler Callback für Fortschrittsanzeige

    Example:
        >>> runner = ExperimentRunner()
        >>> config = ExperimentConfig(
        ...     name="MA Sweep",
        ...     strategy_name="ma_crossover",
        ...     param_sweeps=[ParamSweep("fast_period", [5, 10, 20])],
        ... )
        >>> result = runner.run(config)
        >>> print(result.to_dataframe())
    """

    def __init__(
        self,
        backtest_fn: Optional[BacktestFunction] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> None:
        """
        Initialisiert den ExperimentRunner.

        Args:
            backtest_fn: Custom Backtest-Funktion (optional)
            progress_callback: Callback(current, total, message) für Progress
        """
        self.backtest_fn = backtest_fn or self._default_backtest
        self.progress_callback = progress_callback

    def _default_backtest(
        self,
        strategy_name: str,
        params: Dict[str, Any],
        symbol: str,
        timeframe: str,
        start_date: Optional[str],
        end_date: Optional[str],
        initial_capital: float,
    ) -> Dict[str, Any]:
        """
        Default-Backtest-Funktion, die BacktestEngine verwendet.

        Args:
            strategy_name: Name der Strategie
            params: Parameter-Dict
            symbol: Symbol
            timeframe: Zeitrahmen
            start_date: Startdatum
            end_date: Enddatum
            initial_capital: Startkapital

        Returns:
            Dict mit Metriken
        """
        try:
            from src.backtest.engine import run_single_strategy_from_registry
            from src.data.kraken import fetch_ohlcv_df
            from src.core.config_registry import get_config
            import pandas as pd

            # Setze initial_capital in der Config
            cfg = get_config()
            original_initial_cash = cfg["backtest"]["initial_cash"]
            cfg["backtest"]["initial_cash"] = initial_capital

            try:
                # Lade OHLCV-Daten
                # Konvertiere Symbol-Format falls nötig (z.B. "BTC/EUR" -> "BTC/EUR")
                # Kraken verwendet "/" als Separator
                kraken_symbol = symbol.replace("-", "/")

                # Berechne limit basierend auf start_date/end_date oder verwende Default
                limit = 720  # Default für Kraken API

                # Wenn start_date gegeben, berechne since_ms
                since_ms = None
                if start_date:
                    try:
                        start_dt = pd.to_datetime(start_date)
                        since_ms = int(start_dt.timestamp() * 1000)
                    except Exception:
                        logger.warning(
                            f"Konnte start_date nicht parsen: {start_date}, verwende Default"
                        )

                # Lade Daten
                df = fetch_ohlcv_df(
                    symbol=kraken_symbol,
                    timeframe=timeframe,
                    limit=limit,
                    since_ms=since_ms,
                    use_cache=True,
                )

                # Filtere nach end_date falls gegeben
                if end_date:
                    try:
                        end_dt = pd.to_datetime(end_date)
                        df = df[df.index <= end_dt]
                    except Exception:
                        logger.warning(
                            f"Konnte end_date nicht parsen: {end_date}, ignoriere Filter"
                        )

                if df.empty:
                    raise ValueError(f"Keine Daten für {symbol} {timeframe} gefunden")

                # Führe Backtest aus
                # run_single_strategy_from_registry ist eine Standalone-Funktion, keine Methode
                result = run_single_strategy_from_registry(
                    df=df,
                    strategy_name=strategy_name,
                    custom_params=params,
                )
            finally:
                # Stelle original initial_cash wieder her
                cfg["backtest"]["initial_cash"] = original_initial_cash

            # Extrahiere Metriken aus dem Result
            if result and hasattr(result, "stats"):
                return result.stats
            elif isinstance(result, dict):
                return result.get("stats", result)
            else:
                return {}

        except Exception as e:
            logger.error(f"Backtest-Fehler: {e}")
            raise

    def _run_single(
        self,
        experiment_id: str,
        run_index: int,
        config: ExperimentConfig,
        params: Dict[str, Any],
        symbol: str,
    ) -> SweepResultRow:
        """
        Führt einen einzelnen Backtest durch.

        Args:
            experiment_id: ID des Experiments
            run_index: Index des Runs
            config: Experiment-Konfiguration
            params: Parameter für diesen Run
            symbol: Symbol für diesen Run

        Returns:
            SweepResultRow mit Ergebnissen
        """
        run_id = f"{experiment_id}_{run_index:04d}"
        start_time = time.time()

        try:
            metrics = self.backtest_fn(
                strategy_name=config.strategy_name,
                params=params,
                symbol=symbol,
                timeframe=config.timeframe,
                start_date=config.start_date,
                end_date=config.end_date,
                initial_capital=config.initial_capital,
            )

            runtime = time.time() - start_time

            # Filtere auf gewünschte Metriken
            filtered_metrics = {}
            for m in config.metrics_to_collect:
                if m in metrics:
                    filtered_metrics[m] = metrics[m]
                elif m.replace("_", "") in metrics:
                    filtered_metrics[m] = metrics[m.replace("_", "")]

            return SweepResultRow(
                experiment_id=experiment_id,
                run_id=run_id,
                strategy_name=config.strategy_name,
                symbol=symbol,
                timeframe=config.timeframe,
                params=params,
                metrics=filtered_metrics,
                start_date=config.start_date,
                end_date=config.end_date,
                runtime_seconds=runtime,
                success=True,
            )

        except Exception as e:
            runtime = time.time() - start_time
            logger.warning(f"Run {run_id} fehlgeschlagen: {e}")

            return SweepResultRow(
                experiment_id=experiment_id,
                run_id=run_id,
                strategy_name=config.strategy_name,
                symbol=symbol,
                timeframe=config.timeframe,
                params=params,
                metrics={},
                start_date=config.start_date,
                end_date=config.end_date,
                runtime_seconds=runtime,
                success=False,
                error_message=str(e),
            )

    def run(
        self,
        config: ExperimentConfig,
        dry_run: bool = False,
    ) -> ExperimentResult:
        """
        Führt das Experiment aus.

        Args:
            config: Experiment-Konfiguration
            dry_run: Wenn True, nur Parameter generieren ohne Backtest

        Returns:
            ExperimentResult mit allen Ergebnissen

        Example:
            >>> runner = ExperimentRunner()
            >>> config = ExperimentConfig(
            ...     name="Test",
            ...     strategy_name="ma_crossover",
            ...     param_sweeps=[ParamSweep("fast_period", [5, 10])],
            ... )
            >>> result = runner.run(config)
        """
        experiment_id = config.get_experiment_id()
        start_time = datetime.now()

        logger.info(
            f"Starte Experiment '{config.name}' (ID: {experiment_id})\n"
            f"  Strategie: {config.strategy_name}\n"
            f"  Symbole: {config.symbols}\n"
            f"  Kombinationen: {config.num_combinations}"
        )

        # Generiere alle Parameter-Kombinationen
        param_combinations = config.generate_param_combinations()

        if dry_run:
            logger.info(f"Dry-Run: {len(param_combinations)} Kombinationen generiert")
            return ExperimentResult(
                experiment_id=experiment_id,
                config=config,
                results=[],
                start_time=start_time.isoformat(),
            )

        # Führe Backtests aus
        results: List[SweepResultRow] = []
        total_runs = len(param_combinations) * len(config.symbols)
        run_index = 0

        for symbol in config.symbols:
            for params in param_combinations:
                run_index += 1

                if self.progress_callback:
                    self.progress_callback(
                        run_index,
                        total_runs,
                        f"{symbol} | {params}",
                    )

                logger.debug(f"Run {run_index}/{total_runs}: {symbol} | {params}")

                result = self._run_single(
                    experiment_id=experiment_id,
                    run_index=run_index,
                    config=config,
                    params=params,
                    symbol=symbol,
                )
                results.append(result)

        end_time = datetime.now()
        total_runtime = (end_time - start_time).total_seconds()

        experiment_result = ExperimentResult(
            experiment_id=experiment_id,
            config=config,
            results=results,
            total_runtime_seconds=total_runtime,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
        )

        logger.info(
            f"Experiment abgeschlossen:\n"
            f"  Runs: {experiment_result.num_runs}\n"
            f"  Erfolgreich: {experiment_result.num_successful}\n"
            f"  Fehlgeschlagen: {experiment_result.num_failed}\n"
            f"  Laufzeit: {total_runtime:.1f}s"
        )

        # Speichere Ergebnisse falls gewünscht
        if config.save_results:
            self._save_results(experiment_result, config)

        return experiment_result

    def _save_results(
        self,
        result: ExperimentResult,
        config: ExperimentConfig,
    ) -> None:
        """Speichert Ergebnisse in Dateien."""
        import os

        os.makedirs(config.output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Verwende config.name (Sweep-Name) statt nur strategy_name für bessere Auffindbarkeit
        base_name = f"{config.name}_{result.experiment_id}_{timestamp}"

        # CSV
        csv_path = os.path.join(config.output_dir, f"{base_name}.csv")
        result.save_csv(csv_path)

        # Parquet
        try:
            parquet_path = os.path.join(config.output_dir, f"{base_name}.parquet")
            result.save_parquet(parquet_path)
        except ImportError:
            logger.debug("pyarrow nicht verfügbar, überspringe Parquet-Export")

        # Summary JSON
        try:
            summary_path = os.path.join(config.output_dir, f"{base_name}_summary.json")
            with open(summary_path, "w") as f:
                json.dump(result.to_dict(), f, indent=2, default=str)
            logger.info(f"Summary gespeichert: {summary_path}")
        except Exception as e:
            logger.warning(f"Konnte Summary nicht speichern: {e}")

    def run_parallel(
        self,
        config: ExperimentConfig,
    ) -> ExperimentResult:
        """
        Führt das Experiment parallel aus.

        Args:
            config: Experiment-Konfiguration

        Returns:
            ExperimentResult mit allen Ergebnissen

        Note:
            Verwendet concurrent.futures für Parallelisierung.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        experiment_id = config.get_experiment_id()
        start_time = datetime.now()

        logger.info(
            f"Starte Parallel-Experiment '{config.name}' (ID: {experiment_id})\n"
            f"  Workers: {config.max_workers}"
        )

        param_combinations = config.generate_param_combinations()
        results: List[SweepResultRow] = []

        # Erstelle alle Run-Definitionen
        runs = []
        run_index = 0
        for symbol in config.symbols:
            for params in param_combinations:
                run_index += 1
                runs.append((run_index, params, symbol))

        # Parallel ausführen
        with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
            futures = {
                executor.submit(
                    self._run_single,
                    experiment_id,
                    run_idx,
                    config,
                    params,
                    symbol,
                ): (run_idx, params, symbol)
                for run_idx, params, symbol in runs
            }

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                if self.progress_callback:
                    self.progress_callback(
                        len(results),
                        len(runs),
                        f"Completed: {result.run_id}",
                    )

        end_time = datetime.now()
        total_runtime = (end_time - start_time).total_seconds()

        experiment_result = ExperimentResult(
            experiment_id=experiment_id,
            config=config,
            results=sorted(results, key=lambda r: r.run_id),
            total_runtime_seconds=total_runtime,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
        )

        if config.save_results:
            self._save_results(experiment_result, config)

        return experiment_result
