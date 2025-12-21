"""
Peak_Trade Walk-Forward Backtesting
====================================

Walk-Forward-Analyse für Out-of-Sample-Validierung von Strategiekonfigurationen.

Komponenten:
- WalkForwardConfig: Konfiguration für Walk-Forward-Analyse
- WalkForwardWindowResult: Ergebnis eines einzelnen Train/Test-Fensters
- WalkForwardResult: Gesamtergebnis über alle Fenster
- run_walkforward_for_config: Hauptfunktion für Walk-Forward-Backtest
- split_train_test_windows: Hilfsfunktion für Fenster-Aufteilung

Usage:
    from src.backtest.walkforward import (
        WalkForwardConfig,
        run_walkforward_for_config,
    )

    config = WalkForwardConfig(
        train_window="180d",
        test_window="30d",
        top_n=3,
        sweep_name="rsi_reversion_basic",
    )
    result = run_walkforward_for_config("config_1", config)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from os import PathLike

import pandas as pd

from .engine import BacktestEngine
from .result import BacktestResult
from ..strategies import load_strategy
from ..core.config_registry import get_config

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class WalkForwardConfig:
    """
    Konfiguration für Walk-Forward-Backtesting.

    Attributes:
        train_window: Trainingsfenster-Dauer (z.B. "180d", "6M")
        test_window: Testfenster-Dauer (z.B. "30d", "1M")
        top_n: Anzahl der Top-Konfigurationen aus Sweep (default: 3)
        sweep_name: Name des Sweeps (z.B. "rsi_reversion_basic")
        symbol: Trading-Symbol (default: "BTC/EUR")
        config_path: Pfad zur Top-N-TOML-Datei (optional, wird aus sweep_name abgeleitet)
        start_date: Startdatum für Walk-Forward (optional, wird aus Daten abgeleitet)
        end_date: Enddatum für Walk-Forward (optional, wird aus Daten abgeleitet)
        step_size: Schrittgröße zwischen Fenstern (default: test_window, d.h. keine Überlappung)
        output_dir: Ausgabe-Verzeichnis für Walk-Forward-Ergebnisse (default: "results/walkforward")
    """

    train_window: str
    test_window: str
    top_n: int = 3
    sweep_name: str = ""
    symbol: str = "BTC/EUR"
    config_path: Optional[Path] = None
    start_date: Optional[pd.Timestamp] = None
    end_date: Optional[pd.Timestamp] = None
    step_size: Optional[str] = None  # None = anchored mode (lückenlos)
    output_dir: Path = field(default_factory=lambda: Path("results/walkforward"))

    def __post_init__(self) -> None:
        """Normalisiert Pfade und setzt Defaults."""
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        if isinstance(self.config_path, str):
            self.config_path = Path(self.config_path)
        # step_size bleibt None für anchored mode (lückenlos, ohne Überlappung)


# =============================================================================
# RESULT DATACLASSES
# =============================================================================


@dataclass
class WalkForwardWindowResult:
    """
    Ergebnis eines einzelnen Train/Test-Fensters.

    Attributes:
        window_index: Index des Fensters (0-basiert)
        train_start: Startdatum des Trainingsfensters
        train_end: Enddatum des Trainingsfensters
        test_start: Startdatum des Testfensters
        test_end: Enddatum des Testfensters
        train_result: BacktestResult für Trainingsfenster (optional)
        test_result: BacktestResult für Testfenster
        metrics: Aggregierte Metriken (z.B. Sharpe, Return, Drawdown)
        result_path: Pfad zur gespeicherten Ergebnis-Datei (optional)
    """

    window_index: int
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    train_result: Optional[BacktestResult] = None
    test_result: BacktestResult = field(default_factory=lambda: None)
    metrics: Dict[str, float] = field(default_factory=dict)
    result_path: Optional[Path] = None


@dataclass
class WalkForwardResult:
    """
    Gesamtergebnis einer Walk-Forward-Analyse.

    Attributes:
        config_id: ID der Strategiekonfiguration (z.B. "config_1" oder TOML-Pfad)
        strategy_name: Name der Strategie (z.B. "rsi_reversion")
        windows: Liste aller Fenster-Ergebnisse
        aggregate_metrics: Aggregierte Metriken über alle Fenster (z.B. avg_sharpe, avg_return)
        config_params: Strategie-Parameter (aus Top-N-TOML)
        output_dir: Ausgabe-Verzeichnis für alle Ergebnisse
    """

    config_id: str
    strategy_name: str
    windows: List[WalkForwardWindowResult] = field(default_factory=list)
    aggregate_metrics: Dict[str, float] = field(default_factory=dict)
    config_params: Dict[str, Any] = field(default_factory=dict)
    output_dir: Path = field(default_factory=lambda: Path("results/walkforward"))


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def split_train_test_windows(
    start: pd.Timestamp,
    end: pd.Timestamp,
    wf_config: WalkForwardConfig,
) -> List[Tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]]:
    """
    Teilt den Zeitraum in (train_start, train_end, test_start, test_end)-Fenster auf.

    Semantik von step_size:
        - Wenn step_size NICHT gesetzt (None): Fenster folgen lückenlos aufeinander.
          Das nächste train_start = aktuelles test_end. Keine Überlappung der Test-Fenster.
        - Wenn step_size gesetzt: Definiert den Abstand zwischen aufeinanderfolgenden
          train_start-Zeitpunkten. Bei step_size < train_window + test_window können
          sich aufeinanderfolgende Fenster überlappen.

    Args:
        start: Startdatum des Gesamtzeitraums
        end: Enddatum des Gesamtzeitraums
        wf_config: WalkForwardConfig mit train_window, test_window, step_size

    Returns:
        Liste von Tupeln (train_start, train_end, test_start, test_end)

    Raises:
        ValueError: Wenn keine vollständigen Fenster erstellt werden können
        ValueError: Wenn step_size <= 0

    Example:
        >>> start = pd.Timestamp("2024-01-01")
        >>> end = pd.Timestamp("2024-12-31")
        >>> config = WalkForwardConfig(train_window="180d", test_window="30d")
        >>> windows = split_train_test_windows(start, end, config)
        >>> print(f"{len(windows)} Fenster erstellt")
    """
    windows: List[Tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]] = []

    # Parse Fenster-Dauern
    try:
        train_delta = pd.Timedelta(wf_config.train_window)
        test_delta = pd.Timedelta(wf_config.test_window)
    except ValueError as e:
        raise ValueError(f"Ungültige Fenster-Dauer: {e}") from e

    # step_size: None bedeutet "anchored" (lückenlos), sonst expliziter Wert
    use_anchored_mode = wf_config.step_size is None
    if not use_anchored_mode:
        try:
            step_delta = pd.Timedelta(wf_config.step_size)
        except ValueError as e:
            raise ValueError(f"Ungültige Fenster-Dauer: {e}") from e
        if step_delta <= pd.Timedelta(0):
            raise ValueError(f"step_size muss positiv sein, ist aber: {step_delta}")

    # Validierung: Mindestlänge des Gesamtzeitraums
    min_required = train_delta + test_delta
    if (end - start) < min_required:
        raise ValueError(
            f"Gesamtzeitraum ({end - start}) ist zu kurz für Train ({train_delta}) + Test ({test_delta})"
        )

    # Start mit erstem Trainingsfenster
    current_start = start

    while current_start < end:
        train_end = current_start + train_delta
        test_start = train_end
        test_end = test_start + test_delta

        # Prüfe, ob Testfenster vollständig im Gesamtzeitraum liegt
        if test_end > end:
            break

        # Nur vollständige Fenster hinzufügen
        windows.append((current_start, train_end, test_start, test_end))

        # Nächstes Fenster berechnen
        if use_anchored_mode:
            # Anchored: nächstes Fenster startet direkt nach aktuellem Test-Ende
            current_start = test_end
        else:
            # Rolling: Schritt um step_delta nach vorne
            current_start = current_start + step_delta

    if len(windows) == 0:
        raise ValueError(
            f"Keine vollständigen Fenster erstellt. "
            f"Gesamtzeitraum: {start} bis {end} ({end - start}), "
            f"benötigt: Train ({train_delta}) + Test ({test_delta})"
        )

    return windows


# =============================================================================
# MAIN API
# =============================================================================


def run_walkforward_for_config(
    config_id: str,
    wf_config: WalkForwardConfig,
    *,
    df: Optional[pd.DataFrame] = None,
    strategy_name: Optional[str] = None,
    strategy_params: Optional[Dict[str, Any]] = None,
    strategy_signal_fn: Optional[Any] = None,
    logger: Optional[logging.Logger] = None,
) -> WalkForwardResult:
    """
    Führt einen Walk-Forward-Backtest für eine gegebene Strategiekonfiguration aus.

    Workflow:
    1. Lädt Strategie-Parameter (aus strategy_params oder config)
    2. Teilt Zeitraum in Train/Test-Fenster auf
    3. Für jedes Fenster:
       a. Trainingsfenster: Backtest auf Train-Daten (optional, für Parameter-Optimierung)
       b. Testfenster: Backtest auf Test-Daten mit optimierten Parametern
    4. Aggregiert Metriken über alle Fenster
    5. Speichert Ergebnisse (optional)

    Args:
        config_id: ID der Konfiguration (z.B. "config_1")
        wf_config: WalkForwardConfig mit Fenster-Einstellungen
        df: OHLCV-DataFrame (muss übergeben werden, wird nicht automatisch geladen)
        strategy_name: Name der Strategie (z.B. "rsi_reversion") - wird benötigt falls strategy_signal_fn None
        strategy_params: Strategie-Parameter-Dict (wird aus config geladen falls None)
        strategy_signal_fn: Signal-Generator-Funktion (wird aus strategy_name geladen falls None)
        logger: Optional Logger (default: Modul-Logger)

    Returns:
        WalkForwardResult mit allen Fenster-Ergebnissen und aggregierten Metriken

    Raises:
        ValueError: Bei ungültigen Fenster-Einstellungen, fehlenden Daten oder fehlenden Strategie-Parametern

    Example:
        >>> from src.backtest.walkforward import WalkForwardConfig, run_walkforward_for_config
        >>> from src.strategies.rsi_reversion import generate_signals
        >>>
        >>> config = WalkForwardConfig(
        ...     train_window="180d",
        ...     test_window="30d",
        ... )
        >>> result = run_walkforward_for_config(
        ...     "config_1",
        ...     config,
        ...     df=df,
        ...     strategy_name="rsi_reversion",
        ...     strategy_params={"rsi_period": 14, "oversold": 30, "overbought": 70},
        ... )
        >>> print(f"Durchschnitts-Sharpe: {result.aggregate_metrics.get('avg_sharpe', 0):.2f}")
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.info(f"Starte Walk-Forward-Analyse für Konfiguration: {config_id}")

    # 1. Validierung: DataFrame muss vorhanden sein
    if df is None or df.empty:
        raise ValueError("DataFrame muss übergeben werden und darf nicht leer sein")

    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame muss einen DatetimeIndex haben")

    # 2. Strategie-Parameter und Signal-Funktion laden
    if strategy_params is None:
        if strategy_name is None:
            raise ValueError("Entweder strategy_name oder strategy_params muss angegeben werden")
        try:
            from ..core.config_registry import get_strategy_cfg

            strategy_params = get_strategy_cfg(strategy_name)
            logger.info(f"Strategie-Parameter aus config geladen: {strategy_name}")
        except KeyError as e:
            raise ValueError(f"Strategie '{strategy_name}' nicht in config gefunden: {e}") from e
    else:
        if strategy_name is None:
            strategy_name = (
                wf_config.sweep_name.split("_")[0] if wf_config.sweep_name else "unknown"
            )
            logger.warning(f"strategy_name nicht angegeben, verwende: {strategy_name}")

    if strategy_signal_fn is None:
        if strategy_name is None:
            raise ValueError("Entweder strategy_signal_fn oder strategy_name muss angegeben werden")
        try:
            strategy_signal_fn = load_strategy(strategy_name)
            logger.info(f"Signal-Funktion geladen: {strategy_name}")
        except Exception as e:
            raise ValueError(f"Fehler beim Laden der Strategie '{strategy_name}': {e}") from e

    # 3. Zeitraum bestimmen
    if wf_config.start_date is not None and wf_config.end_date is not None:
        start = pd.Timestamp(wf_config.start_date)
        end = pd.Timestamp(wf_config.end_date)
        # Filtere DataFrame auf Zeitraum
        df = df.loc[start:end].copy()
        if df.empty:
            raise ValueError(f"Keine Daten im Zeitraum {start} bis {end}")
    else:
        # Verwende gesamten DataFrame-Zeitraum
        start = pd.Timestamp(df.index[0])
        end = pd.Timestamp(df.index[-1])
        logger.info(f"Verwende gesamten Datenzeitraum: {start} bis {end}")

    # 4. Fenster aufteilen
    try:
        windows = split_train_test_windows(start, end, wf_config)
        logger.info(f"{len(windows)} vollständige Fenster erstellt")
    except ValueError as e:
        logger.error(f"Fehler beim Aufteilen der Fenster: {e}")
        raise

    # 5. Backtest-Engine initialisieren
    engine = BacktestEngine()

    # 6. Für jedes Fenster: Backtest durchführen
    window_results: List[WalkForwardWindowResult] = []

    for window_idx, (train_start, train_end, test_start, test_end) in enumerate(windows):
        logger.info(
            f"Fenster {window_idx + 1}/{len(windows)}: "
            f"Train {train_start.date()} - {train_end.date()}, "
            f"Test {test_start.date()} - {test_end.date()}"
        )

        # Train-Daten extrahieren (optional, für spätere Parameter-Optimierung)
        train_df = df.loc[train_start:train_end].copy()
        if train_df.empty:
            logger.warning(f"Train-Daten leer für Fenster {window_idx}, überspringe")
            continue

        # Test-Daten extrahieren
        test_df = df.loc[test_start:test_end].copy()
        if test_df.empty:
            logger.warning(f"Test-Daten leer für Fenster {window_idx}, überspringe")
            continue

        # Train-Backtest (optional, aktuell nicht verwendet, aber für spätere Optimierung)
        train_result: Optional[BacktestResult] = None
        # NOTE: Siehe docs/TECH_DEBT_BACKLOG.md (Eintrag "Walk-Forward: Parameter-Optimierung")
        # train_result = engine.run_realistic(
        #     df=train_df,
        #     strategy_signal_fn=strategy_signal_fn,
        #     strategy_params=strategy_params,
        #     symbol=wf_config.symbol,
        # )

        # Test-Backtest (Haupt-Backtest für Out-of-Sample-Validierung)
        try:
            test_result = engine.run_realistic(
                df=test_df,
                strategy_signal_fn=strategy_signal_fn,
                strategy_params=strategy_params,
                symbol=wf_config.symbol,
            )
        except Exception as e:
            logger.error(f"Fehler beim Backtest für Fenster {window_idx}: {e}")
            continue

        # Metriken extrahieren
        metrics = test_result.stats.copy() if test_result.stats else {}

        # Window-Result erstellen
        window_result = WalkForwardWindowResult(
            window_index=window_idx,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
            train_result=train_result,
            test_result=test_result,
            metrics=metrics,
        )

        window_results.append(window_result)

        # Log Metriken
        sharpe = metrics.get("sharpe", 0.0)
        total_return = metrics.get("total_return", 0.0)
        max_drawdown = metrics.get("max_drawdown", 0.0)
        logger.info(
            f"  → Sharpe: {sharpe:.2f}, Return: {total_return:.2%}, "
            f"MaxDD: {max_drawdown:.2%}, Trades: {metrics.get('total_trades', 0)}"
        )

    if len(window_results) == 0:
        raise ValueError("Keine gültigen Fenster-Ergebnisse erzeugt")

    # 7. Aggregierte Metriken berechnen
    aggregate_metrics = _compute_aggregate_metrics(window_results)

    # 8. WalkForwardResult erstellen
    result = WalkForwardResult(
        config_id=config_id,
        strategy_name=strategy_name or "unknown",
        windows=window_results,
        aggregate_metrics=aggregate_metrics,
        config_params=strategy_params,
        output_dir=wf_config.output_dir,
    )

    logger.info(
        f"Walk-Forward-Analyse abgeschlossen: {len(window_results)} Fenster, "
        f"Avg Sharpe: {aggregate_metrics.get('avg_sharpe', 0):.2f}, "
        f"Avg Return: {aggregate_metrics.get('avg_return', 0):.2%}"
    )

    return result


def _compute_aggregate_metrics(
    window_results: List[WalkForwardWindowResult],
) -> Dict[str, float]:
    """
    Berechnet aggregierte Metriken über alle Fenster.

    Args:
        window_results: Liste von WalkForwardWindowResult

    Returns:
        Dict mit aggregierten Metriken:
        - avg_sharpe: Durchschnitts-Sharpe
        - avg_return: Durchschnitts-Return
        - avg_max_drawdown: Durchschnitts-Max-Drawdown
        - min_sharpe: Minimum-Sharpe
        - max_sharpe: Maximum-Sharpe
        - positive_windows: Anzahl Fenster mit positivem Return
        - total_windows: Gesamtanzahl Fenster
        - win_rate_windows: Anteil positiver Fenster
    """
    if not window_results:
        return {}

    # Extrahiere Metriken aus allen Test-Ergebnissen
    sharpe_values = []
    return_values = []
    drawdown_values = []
    positive_count = 0

    for window_result in window_results:
        metrics = window_result.metrics
        sharpe = metrics.get("sharpe", 0.0)
        total_return = metrics.get("total_return", 0.0)
        max_drawdown = metrics.get("max_drawdown", 0.0)

        sharpe_values.append(sharpe)
        return_values.append(total_return)
        drawdown_values.append(max_drawdown)

        if total_return > 0:
            positive_count += 1

    # Aggregationen
    n = len(window_results)
    aggregate = {
        "avg_sharpe": sum(sharpe_values) / n if n > 0 else 0.0,
        "avg_return": sum(return_values) / n if n > 0 else 0.0,
        "avg_max_drawdown": sum(drawdown_values) / n if n > 0 else 0.0,
        "min_sharpe": min(sharpe_values) if sharpe_values else 0.0,
        "max_sharpe": max(sharpe_values) if sharpe_values else 0.0,
        "min_return": min(return_values) if return_values else 0.0,
        "max_return": max(return_values) if return_values else 0.0,
        "positive_windows": positive_count,
        "total_windows": n,
        "win_rate_windows": positive_count / n if n > 0 else 0.0,
    }

    return aggregate


# =============================================================================
# SWEEP INTEGRATION
# =============================================================================


def run_walkforward_for_top_n_from_sweep(
    sweep_name: str,
    wf_config: WalkForwardConfig,
    *,
    top_n: int = 3,
    df: Optional[pd.DataFrame] = None,
    metric_primary: str = "metric_sharpe_ratio",
    metric_fallback: str = "metric_total_return",
    logger: Optional[logging.Logger] = None,
) -> List[WalkForwardResult]:
    """
    Lädt die Top-N-Konfigurationen eines Sweeps aus der Registry
    und führt für jede Konfiguration einen Walk-Forward-Backtest aus.

    Workflow:
    1. Lädt Top-N-Konfigurationen aus Sweep-Ergebnissen (via topn_promotion)
    2. Für jede Konfiguration:
       a. Extrahiert Strategiename und Parameter
       b. Führt Walk-Forward-Backtest aus
    3. Gibt Liste aller WalkForwardResult zurück

    Args:
        sweep_name: Name des Sweeps (z.B. "rsi_reversion_basic")
        wf_config: WalkForwardConfig mit Fenster-Einstellungen
        top_n: Anzahl der Top-Konfigurationen (default: 3)
        df: OHLCV-DataFrame (muss übergeben werden)
        metric_primary: Primäre Metrik für Top-N-Auswahl (default: "metric_sharpe_ratio")
        metric_fallback: Fallback-Metrik (default: "metric_total_return")
        logger: Optional Logger (default: Modul-Logger)

    Returns:
        Liste von WalkForwardResult, eine pro Top-N-Konfiguration

    Raises:
        FileNotFoundError: Wenn keine Sweep-Ergebnisse gefunden werden
        ValueError: Bei ungültigen Konfigurationen oder fehlenden Daten

    Example:
        >>> from src.backtest.walkforward import (
        ...     WalkForwardConfig,
        ...     run_walkforward_for_top_n_from_sweep,
        ... )
        >>>
        >>> config = WalkForwardConfig(
        ...     train_window="180d",
        ...     test_window="30d",
        ... )
        >>> results = run_walkforward_for_top_n_from_sweep(
        ...     "rsi_reversion_basic",
        ...     config,
        ...     top_n=3,
        ...     df=df,
        ... )
        >>> for result in results:
        ...     print(f"{result.config_id}: Avg Sharpe = {result.aggregate_metrics.get('avg_sharpe', 0):.2f}")
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.info(
        f"Starte Walk-Forward-Analyse für Top-{top_n} Konfigurationen aus Sweep: {sweep_name}"
    )

    # 1. Validierung: DataFrame muss vorhanden sein
    if df is None or df.empty:
        raise ValueError("DataFrame muss übergeben werden und darf nicht leer sein")

    # 2. Lade Top-N-Konfigurationen aus Sweep
    try:
        from ..experiments.topn_promotion import load_top_n_configs_for_sweep

        configs = load_top_n_configs_for_sweep(
            sweep_name=sweep_name,
            n=top_n,
            metric_primary=metric_primary,
            metric_fallback=metric_fallback,
        )
        logger.info(f"{len(configs)} Top-N-Konfigurationen geladen")
    except Exception as e:
        logger.error(f"Fehler beim Laden der Top-N-Konfigurationen: {e}")
        raise

    if len(configs) == 0:
        raise ValueError(f"Keine Konfigurationen für Sweep '{sweep_name}' gefunden")

    # 3. Führe Walk-Forward für jede Konfiguration aus
    results: List[WalkForwardResult] = []

    for i, config_dict in enumerate(configs, 1):
        config_id = config_dict.get("config_id", f"config_{i}")
        strategy_name = config_dict.get("strategy_name", "unknown")
        strategy_params = config_dict.get("params", {})

        logger.info(
            f"Konfiguration {i}/{len(configs)}: {config_id} "
            f"(Rank {config_dict.get('rank', i)}, Strategy: {strategy_name})"
        )

        try:
            # Führe Walk-Forward aus
            result = run_walkforward_for_config(
                config_id=config_id,
                wf_config=wf_config,
                df=df,
                strategy_name=strategy_name,
                strategy_params=strategy_params,
                logger=logger,
            )

            results.append(result)

            # Log Summary
            avg_sharpe = result.aggregate_metrics.get("avg_sharpe", 0.0)
            avg_return = result.aggregate_metrics.get("avg_return", 0.0)
            win_rate = result.aggregate_metrics.get("win_rate_windows", 0.0)
            logger.info(
                f"  → Avg Sharpe: {avg_sharpe:.2f}, Avg Return: {avg_return:.2%}, "
                f"Win Rate: {win_rate:.1%}"
            )

        except Exception as e:
            logger.error(f"Fehler bei Walk-Forward für {config_id}: {e}")
            # Weiter mit nächster Konfiguration (nicht komplett abbrechen)
            continue

    if len(results) == 0:
        raise ValueError("Keine erfolgreichen Walk-Forward-Ergebnisse erzeugt")

    logger.info(
        f"Walk-Forward-Analyse abgeschlossen: {len(results)}/{len(configs)} Konfigurationen erfolgreich"
    )

    return results
