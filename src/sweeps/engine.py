# src/sweeps/engine.py
"""
Peak_Trade – Sweep Engine Core (Phase 20)
==========================================

Generische Sweep-Engine für Hyperparameter-Optimierung.

Diese Engine orchestriert:
- Parametergrid-Generierung (Grid-Search)
- Backtest-Läufe für jede Kombination
- Registry-Integration für Reproduzierbarkeit
- Ergebnis-Aggregation und Ranking

Safety:
- Nur Backtest- und Portfolio-Backtest-Runs
- Keine Live- oder Testnet-Orders
- SafetyGuard und TradingEnvironment bleiben unverändert
"""
from __future__ import annotations

import itertools
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import pandas as pd

from src.core.experiments import log_sweep_run, RUN_TYPE_SWEEP
from src.core.peak_config import PeakConfig, load_config
from src.core.position_sizing import build_position_sizer_from_config
from src.core.risk import build_risk_manager_from_config
from src.backtest.engine import BacktestEngine
from src.strategies.registry import (
    create_strategy_from_config,
    get_available_strategy_keys,
    get_strategy_spec,
)


# =============================================================================
# DATA STRUCTURES
# =============================================================================


@dataclass
class SweepConfig:
    """
    Konfiguration für einen Hyperparameter-Sweep.

    Attributes:
        strategy_key: Name der Strategie aus der Registry (z.B. "ma_crossover")
        param_grid: Parameter-Grid als Dict {param_name: [values]}
        symbol: Trading-Pair (z.B. "BTC/EUR")
        timeframe: Timeframe für OHLCV-Daten (z.B. "1h")
        sweep_name: Optionaler Name für Gruppierung (auto-generiert wenn None)
        tag: Optionaler Tag für Registry-Filterung
        max_runs: Maximale Anzahl Runs (None = alle Kombinationen)
        sort_by: Metrik für Ergebnis-Sortierung (default: "sharpe")
        sort_ascending: Sortierrichtung (default: False = beste zuerst)
        config_path: Pfad zur Basis-Config (default: "config.toml")
        extra_metadata: Zusätzliche Metadaten für Registry

    Example:
        >>> config = SweepConfig(
        ...     strategy_key="ma_crossover",
        ...     param_grid={"fast_window": [10, 20], "slow_window": [50, 100]},
        ...     symbol="BTC/EUR",
        ...     timeframe="1h",
        ...     tag="optimization",
        ... )
    """

    strategy_key: str
    param_grid: Dict[str, List[Any]]
    symbol: str = "BTC/EUR"
    timeframe: str = "1h"
    sweep_name: Optional[str] = None
    tag: Optional[str] = None
    max_runs: Optional[int] = None
    sort_by: str = "sharpe"
    sort_ascending: bool = False
    config_path: str = "config.toml"
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validierung nach Initialisierung."""
        if not self.strategy_key:
            raise ValueError("strategy_key darf nicht leer sein")
        if not self.param_grid:
            raise ValueError("param_grid darf nicht leer sein")

        available = get_available_strategy_keys()
        if self.strategy_key not in available:
            raise ValueError(
                f"Unbekannte Strategie '{self.strategy_key}'. "
                f"Verfügbar: {', '.join(available)}"
            )

    @property
    def total_combinations(self) -> int:
        """Gibt die Gesamtzahl der Parameterkombinationen zurück."""
        if not self.param_grid:
            return 0
        total = 1
        for values in self.param_grid.values():
            total *= len(values)
        return total

    @property
    def effective_runs(self) -> int:
        """Gibt die effektive Anzahl der Runs zurück (mit max_runs Limit)."""
        total = self.total_combinations
        if self.max_runs is not None:
            return min(total, self.max_runs)
        return total


@dataclass
class SweepResult:
    """
    Ergebnis eines einzelnen Sweep-Runs.

    Attributes:
        params: Die getestete Parameterkombination
        stats: Backtest-Statistiken (total_return, sharpe, max_drawdown, etc.)
        run_id: Eindeutige ID aus der Registry
        success: True wenn Backtest erfolgreich war
        error: Fehlermeldung bei Misserfolg (None wenn erfolgreich)
    """

    params: Dict[str, Any]
    stats: Dict[str, Any]
    run_id: str
    success: bool = True
    error: Optional[str] = None

    @property
    def total_return(self) -> float:
        """Shortcut für total_return aus stats."""
        return float(self.stats.get("total_return", 0.0))

    @property
    def sharpe(self) -> float:
        """Shortcut für Sharpe Ratio aus stats."""
        return float(self.stats.get("sharpe", 0.0))

    @property
    def max_drawdown(self) -> float:
        """Shortcut für Max Drawdown aus stats."""
        return float(self.stats.get("max_drawdown", 0.0))

    @property
    def total_trades(self) -> int:
        """Shortcut für Anzahl Trades aus stats."""
        return int(self.stats.get("total_trades", 0))


@dataclass
class SweepSummary:
    """
    Zusammenfassung eines kompletten Sweeps.

    Attributes:
        sweep_id: Eindeutige ID des Sweeps
        sweep_name: Name des Sweeps
        strategy_key: Getestete Strategie
        symbol: Trading-Pair
        timeframe: Timeframe
        total_combinations: Anzahl aller möglichen Kombinationen
        runs_executed: Anzahl tatsächlich ausgeführter Runs
        successful_runs: Anzahl erfolgreicher Runs
        failed_runs: Anzahl fehlgeschlagener Runs
        results: Liste aller SweepResult-Objekte
        best_result: Bestes Ergebnis nach sort_by Metrik
        duration_seconds: Gesamtdauer des Sweeps
        started_at: Startzeitpunkt
        completed_at: Endzeitpunkt
    """

    sweep_id: str
    sweep_name: str
    strategy_key: str
    symbol: str
    timeframe: str
    total_combinations: int
    runs_executed: int
    successful_runs: int
    failed_runs: int
    results: List[SweepResult]
    best_result: Optional[SweepResult]
    duration_seconds: float
    started_at: str
    completed_at: str

    def get_top_results(
        self,
        n: int = 10,
        sort_by: str = "sharpe",
        ascending: bool = False,
    ) -> List[SweepResult]:
        """
        Gibt die Top-N Ergebnisse zurück.

        Args:
            n: Anzahl der Top-Ergebnisse
            sort_by: Metrik für Sortierung
            ascending: Sortierrichtung

        Returns:
            Liste der Top-N SweepResult-Objekte
        """
        successful = [r for r in self.results if r.success]
        if not successful:
            return []

        # Sortieren nach Metrik
        def get_metric(result: SweepResult) -> float:
            return float(result.stats.get(sort_by, 0.0))

        sorted_results = sorted(
            successful,
            key=get_metric,
            reverse=not ascending,
        )
        return sorted_results[:n]

    def to_dataframe(self) -> pd.DataFrame:
        """Konvertiert Ergebnisse zu pandas DataFrame für Analyse."""
        rows = []
        for r in self.results:
            row = {**r.params, **r.stats, "run_id": r.run_id, "success": r.success}
            if r.error:
                row["error"] = r.error
            rows.append(row)
        return pd.DataFrame(rows)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def generate_sweep_id() -> str:
    """Generiert eine eindeutige Sweep-ID."""
    return str(uuid.uuid4())[:8]


def expand_parameter_grid(grid: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    """
    Erzeugt das kartesische Produkt aller Parameterwerte (Grid-Search).

    Args:
        grid: Dict mit Parameternamen als Keys und Listen von Werten als Values

    Returns:
        Liste von Dicts, jedes Dict ist eine Parameterkombination

    Example:
        >>> grid = {"fast_window": [10, 20], "slow_window": [50, 100]}
        >>> expand_parameter_grid(grid)
        [
            {"fast_window": 10, "slow_window": 50},
            {"fast_window": 10, "slow_window": 100},
            {"fast_window": 20, "slow_window": 50},
            {"fast_window": 20, "slow_window": 100},
        ]
    """
    if not grid:
        return [{}]

    keys = list(grid.keys())
    values = list(grid.values())

    combinations = []
    for combo in itertools.product(*values):
        param_dict = dict(zip(keys, combo))
        combinations.append(param_dict)

    return combinations


def validate_param_grid(grid: Dict[str, List[Any]]) -> None:
    """
    Validiert ein Parameter-Grid.

    Raises:
        ValueError: Bei ungültigem Grid
    """
    if not isinstance(grid, dict):
        raise ValueError("param_grid muss ein Dict sein")

    for key, values in grid.items():
        if not isinstance(key, str):
            raise ValueError(f"Parameter-Key muss string sein, nicht {type(key)}")
        if not isinstance(values, (list, tuple)):
            raise ValueError(
                f"Parameter-Werte für '{key}' müssen Liste sein, nicht {type(values)}"
            )
        if len(values) == 0:
            raise ValueError(f"Parameter '{key}' hat keine Werte")


# =============================================================================
# SWEEP ENGINE
# =============================================================================


class SweepEngine:
    """
    Orchestriert Hyperparameter-Sweeps für Strategien.

    Die Engine führt systematisch alle Parameterkombinationen aus,
    loggt Ergebnisse in der Registry und bietet Ranking-Funktionen.

    Safety:
    - Nur Backtest-Runs, keine Live- oder Testnet-Orders
    - SafetyGuard und TradingEnvironment werden nicht verändert

    Example:
        >>> engine = SweepEngine()
        >>> config = SweepConfig(
        ...     strategy_key="ma_crossover",
        ...     param_grid={"fast_window": [10, 20], "slow_window": [50, 100]},
        ... )
        >>> summary = engine.run_sweep(config, data=df)
        >>> print(summary.best_result)
    """

    def __init__(
        self,
        verbose: bool = False,
        progress_callback: Optional[Callable[[int, int, Dict], None]] = None,
    ) -> None:
        """
        Initialisiert die Sweep-Engine.

        Args:
            verbose: Wenn True, ausführliche Ausgabe
            progress_callback: Optionaler Callback für Fortschritt
                Signatur: callback(current_run, total_runs, current_params)
        """
        self.verbose = verbose
        self.progress_callback = progress_callback

    def run_sweep(
        self,
        config: SweepConfig,
        data: pd.DataFrame,
        skip_registry: bool = False,
    ) -> SweepSummary:
        """
        Führt einen kompletten Hyperparameter-Sweep aus.

        Args:
            config: Sweep-Konfiguration
            data: OHLCV-DataFrame für Backtests
            skip_registry: Wenn True, kein Registry-Logging (für Tests)

        Returns:
            SweepSummary mit allen Ergebnissen

        Raises:
            ValueError: Bei ungültiger Konfiguration
        """
        # Validierung
        validate_param_grid(config.param_grid)

        # Sweep-ID und Name generieren
        sweep_id = generate_sweep_id()
        sweep_name = config.sweep_name or f"{config.strategy_key}_sweep_{sweep_id}"

        # Parameterkombinationen generieren
        combinations = expand_parameter_grid(config.param_grid)
        if config.max_runs is not None:
            combinations = combinations[: config.max_runs]

        # Basis-Config laden
        cfg = load_config(Path(config.config_path))

        # Tracking
        start_time = datetime.utcnow()
        started_at = start_time.isoformat(timespec="seconds") + "Z"
        results: List[SweepResult] = []

        if self.verbose:
            print(f"\n[Sweep] Starte {len(combinations)} Runs für {config.strategy_key}")
            print(f"        Sweep-ID: {sweep_id}")
            print(f"        Symbol: {config.symbol}, Timeframe: {config.timeframe}")

        # Runs ausführen
        for i, params in enumerate(combinations, 1):
            if self.progress_callback:
                self.progress_callback(i, len(combinations), params)
            elif self.verbose:
                print(f"  [{i}/{len(combinations)}] {params}")

            try:
                stats = self._run_single_backtest(
                    data=data,
                    strategy_key=config.strategy_key,
                    params=params,
                    cfg=cfg,
                )

                # Registry-Logging
                run_id = ""
                if not skip_registry:
                    run_id = log_sweep_run(
                        strategy_key=config.strategy_key,
                        symbol=config.symbol,
                        timeframe=config.timeframe,
                        params=params,
                        stats=stats,
                        sweep_name=sweep_name,
                        tag=config.tag,
                        config_path=config.config_path,
                        extra_metadata={
                            "sweep_id": sweep_id,
                            "run_index": i,
                            "total_runs": len(combinations),
                            **config.extra_metadata,
                        },
                    )
                else:
                    run_id = f"test_{uuid.uuid4().hex[:8]}"

                results.append(
                    SweepResult(
                        params=params,
                        stats=stats,
                        run_id=run_id,
                        success=True,
                    )
                )

            except Exception as e:
                if self.verbose:
                    print(f"    FEHLER: {e}")

                results.append(
                    SweepResult(
                        params=params,
                        stats={},
                        run_id="",
                        success=False,
                        error=str(e),
                    )
                )

        # Abschluss
        end_time = datetime.utcnow()
        completed_at = end_time.isoformat(timespec="seconds") + "Z"
        duration = (end_time - start_time).total_seconds()

        # Bestes Ergebnis finden
        successful_results = [r for r in results if r.success]
        best_result = None
        if successful_results:
            best_result = self._find_best_result(
                successful_results,
                sort_by=config.sort_by,
                ascending=config.sort_ascending,
            )

        summary = SweepSummary(
            sweep_id=sweep_id,
            sweep_name=sweep_name,
            strategy_key=config.strategy_key,
            symbol=config.symbol,
            timeframe=config.timeframe,
            total_combinations=config.total_combinations,
            runs_executed=len(results),
            successful_runs=len(successful_results),
            failed_runs=len(results) - len(successful_results),
            results=results,
            best_result=best_result,
            duration_seconds=duration,
            started_at=started_at,
            completed_at=completed_at,
        )

        if self.verbose:
            print(f"\n[Sweep] Abgeschlossen in {duration:.1f}s")
            print(f"        Erfolgreich: {summary.successful_runs}/{summary.runs_executed}")
            if best_result:
                print(f"        Bestes Ergebnis: {best_result.params}")
                print(f"        Sharpe: {best_result.sharpe:.2f}, Return: {best_result.total_return:.2%}")

        return summary

    def _run_single_backtest(
        self,
        data: pd.DataFrame,
        strategy_key: str,
        params: Dict[str, Any],
        cfg: PeakConfig,
    ) -> Dict[str, Any]:
        """
        Führt einen einzelnen Backtest mit spezifischen Parametern aus.

        Args:
            data: OHLCV-DataFrame
            strategy_key: Strategie-Key
            params: Parameter für diese Kombination
            cfg: Peak-Config

        Returns:
            Stats-Dict mit Backtest-Ergebnissen
        """
        # Position-Sizer und Risk-Manager aus Config
        position_sizer = build_position_sizer_from_config(cfg)
        risk_manager = build_risk_manager_from_config(cfg, section="risk_management")

        # Strategie erstellen
        strategy = create_strategy_from_config(strategy_key, cfg)

        # Parameter auf Strategie anwenden
        for key, value in params.items():
            if hasattr(strategy, key):
                setattr(strategy, key, value)
            # Auch in config aktualisieren für Strategien die config nutzen
            if hasattr(strategy, "config") and isinstance(strategy.config, dict):
                strategy.config[key] = value

        # Backtest-Engine
        engine = BacktestEngine(
            core_position_sizer=position_sizer,
            risk_manager=risk_manager,
        )

        def strategy_signal_fn(df: pd.DataFrame, _params: Dict) -> pd.Series:
            return strategy.generate_signals(df)

        result = engine.run_realistic(
            df=data,
            strategy_signal_fn=strategy_signal_fn,
            strategy_params=params,
        )

        return result.stats or {}

    def _find_best_result(
        self,
        results: List[SweepResult],
        sort_by: str,
        ascending: bool,
    ) -> Optional[SweepResult]:
        """Findet das beste Ergebnis nach der angegebenen Metrik."""
        if not results:
            return None

        def get_metric(r: SweepResult) -> float:
            val = r.stats.get(sort_by, 0.0)
            # Handle None values
            if val is None:
                return float("-inf") if not ascending else float("inf")
            return float(val)

        return (
            min(results, key=get_metric)
            if ascending
            else max(results, key=get_metric)
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def run_strategy_sweep(
    strategy_key: str,
    param_grid: Dict[str, List[Any]],
    data: pd.DataFrame,
    symbol: str = "BTC/EUR",
    timeframe: str = "1h",
    sweep_name: Optional[str] = None,
    tag: Optional[str] = None,
    max_runs: Optional[int] = None,
    sort_by: str = "sharpe",
    config_path: str = "config.toml",
    verbose: bool = False,
    skip_registry: bool = False,
) -> SweepSummary:
    """
    Convenience-Funktion für einen einfachen Strategy-Sweep.

    Args:
        strategy_key: Name der Strategie
        param_grid: Parameter-Grid
        data: OHLCV-DataFrame
        symbol: Trading-Pair
        timeframe: Timeframe
        sweep_name: Optionaler Sweep-Name
        tag: Optionaler Tag
        max_runs: Max. Anzahl Runs
        sort_by: Sortier-Metrik
        config_path: Config-Pfad
        verbose: Ausführliche Ausgabe
        skip_registry: Registry-Logging überspringen

    Returns:
        SweepSummary mit Ergebnissen

    Example:
        >>> summary = run_strategy_sweep(
        ...     strategy_key="my_strategy",
        ...     param_grid={"lookback_window": [15, 20, 25], "entry_multiplier": [1.2, 1.5, 2.0]},
        ...     data=df,
        ...     tag="optimization",
        ... )
        >>> print(f"Best Sharpe: {summary.best_result.sharpe:.2f}")
    """
    config = SweepConfig(
        strategy_key=strategy_key,
        param_grid=param_grid,
        symbol=symbol,
        timeframe=timeframe,
        sweep_name=sweep_name,
        tag=tag,
        max_runs=max_runs,
        sort_by=sort_by,
        config_path=config_path,
    )

    engine = SweepEngine(verbose=verbose)
    return engine.run_sweep(config, data=data, skip_registry=skip_registry)
