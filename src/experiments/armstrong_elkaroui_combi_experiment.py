# src/experiments/armstrong_elkaroui_combi_experiment.py
"""
Armstrong-El Karoui Kombi-Experiment (R&D Phase)
================================================

Dieses Modul kombiniert Armstrong-Zyklen und El-Karoui-Volatilitätsregime
für denselben Markt/Zeitraum und berechnet aggregierte Kennzahlen.

⚠️ WICHTIG: RESEARCH-ONLY – NICHT FÜR LIVE-TRADING ⚠️

Konzept:
- Armstrong-Event-State: Markiert Event-Fenster um ECM-Turning-Points
- El-Karoui-Regime: Klassifiziert Volatilitäts-Regime (LOW/MEDIUM/HIGH)
- Kombi-State: Kartesisches Produkt beider Label-Dimensionen
- Aggregierte Kennzahlen pro Kombi-State (Returns, Counts, etc.)

Usage:
    from src.experiments.armstrong_elkaroui_combi_experiment import (
        ArmstrongElKarouiCombiConfig,
        run_armstrong_elkaroui_combi_experiment,
        CombiExperimentResult,
    )

    config = ArmstrongElKarouiCombiConfig(
        symbol="BTC/EUR",
        timeframe="1h",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 6, 1),
    )

    result = run_armstrong_elkaroui_combi_experiment(config)
    print(result.combo_stats)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# =============================================================================
# RUN TYPE KONSTANTEN
# =============================================================================

RUN_TYPE_ARMSTRONG_ELKAROUI_COMBI = "armstrong_elkaroui_combi"

# Erlaubte Environments für dieses R&D-Experiment
ALLOWED_ENVIRONMENTS = ["offline_backtest", "research"]


# =============================================================================
# ENUMS / LABEL-TYPEN
# =============================================================================


class ArmstrongEventState:
    """Armstrong Event-States für Label-Klassifikation."""

    NONE = "NONE"
    PRE_EVENT = "PRE_EVENT"
    EVENT = "EVENT"
    POST_EVENT = "POST_EVENT"


class ElKarouiRegime:
    """El-Karoui Volatilitäts-Regime."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# =============================================================================
# CONFIG DATACLASS
# =============================================================================


@dataclass
class ArmstrongElKarouiCombiConfig:
    """
    Konfiguration für das Armstrong-El-Karoui Kombi-Experiment.

    Attributes:
        symbol: Trading-Symbol (z.B. "BTC/EUR")
        timeframe: Zeitrahmen (z.B. "1h", "4h", "1d")
        start_date: Startdatum für das Experiment
        end_date: Enddatum für das Experiment
        armstrong_params: Parameter für Armstrong-Cycle-Strategie
        elkaroui_params: Parameter für El-Karoui-Vol-Model-Strategie
        environment: Umgebung (nur offline_backtest/research erlaubt)
        run_type: Run-Type für Registry
        tier: Tier-Level (immer r_and_d)
        experiment_category: Kategorie des Experiments
        forward_return_windows: Windows für Forward-Returns in Bars
        output_dir: Verzeichnis für Ergebnisse
    """

    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    armstrong_params: Dict[str, Any] = field(
        default_factory=lambda: {
            "cycle_length_days": 3141,
            "event_window_days": 90,
            "reference_date": "2015-10-01",
        }
    )
    elkaroui_params: Dict[str, Any] = field(
        default_factory=lambda: {
            "vol_window": 20,
            "vol_threshold_low": 0.3,
            "vol_threshold_high": 0.7,
            "use_ewm": True,
            "annualization_factor": 252.0,
        }
    )
    environment: str = "offline_backtest"
    run_type: str = RUN_TYPE_ARMSTRONG_ELKAROUI_COMBI
    tier: str = "r_and_d"
    experiment_category: str = "label_analysis"
    forward_return_windows: List[int] = field(default_factory=lambda: [1, 3, 7])
    output_dir: str = "reports/r_and_d/armstrong_elkaroui_combi"

    def __post_init__(self) -> None:
        """Validierung nach Initialisierung."""
        if self.environment not in ALLOWED_ENVIRONMENTS:
            raise ValueError(
                f"Environment '{self.environment}' nicht erlaubt für R&D-Experiment. "
                f"Erlaubt: {ALLOWED_ENVIRONMENTS}"
            )
        if self.tier != "r_and_d":
            raise ValueError(f"Tier muss 'r_and_d' sein für dieses Experiment, nicht '{self.tier}'")

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "armstrong_params": self.armstrong_params,
            "elkaroui_params": self.elkaroui_params,
            "environment": self.environment,
            "run_type": self.run_type,
            "tier": self.tier,
            "experiment_category": self.experiment_category,
            "forward_return_windows": self.forward_return_windows,
        }


# =============================================================================
# RESULT DATACLASS
# =============================================================================


@dataclass
class CombiExperimentResult:
    """
    Ergebnis des Armstrong-El-Karoui Kombi-Experiments.

    Attributes:
        run_id: Eindeutige ID des Experiment-Runs
        config: Experiment-Konfiguration
        combo_stats: Aggregierte Statistiken pro Kombi-State
        label_series: DataFrame mit allen Labels pro Bar
        metadata: Zusätzliche Metadaten
        success: Ob das Experiment erfolgreich war
        error_message: Fehlermeldung falls nicht erfolgreich
        report_paths: Pfade zu generierten Reports
    """

    run_id: str
    config: ArmstrongElKarouiCombiConfig
    combo_stats: Dict[str, Dict[str, Any]]
    label_series: Optional[pd.DataFrame] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None
    report_paths: List[str] = field(default_factory=list)

    @property
    def run_type(self) -> str:
        """Run-Type aus Config."""
        return self.config.run_type

    @property
    def tier(self) -> str:
        """Tier aus Config."""
        return self.config.tier

    @property
    def environment(self) -> str:
        """Environment aus Config."""
        return self.config.environment

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary (für JSON-Export)."""
        return {
            "run_id": self.run_id,
            "run_type": self.run_type,
            "tier": self.tier,
            "environment": self.environment,
            "experiment_category": self.config.experiment_category,
            "config": self.config.to_dict(),
            "combo_stats": self.combo_stats,
            "metadata": self.metadata,
            "success": self.success,
            "error_message": self.error_message,
            "report_paths": self.report_paths,
        }

    def save_json(self, filepath: Optional[str] = None) -> str:
        """
        Speichert Ergebnis als JSON.

        Args:
            filepath: Optionaler Pfad (sonst wird aus run_id generiert)

        Returns:
            Pfad zur gespeicherten Datei
        """
        if filepath is None:
            output_dir = Path(self.config.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            filepath = str(output_dir / f"{self.run_id}.json")

        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

        logger.info(f"Ergebnis gespeichert: {filepath}")
        return filepath


# =============================================================================
# HELPER FUNKTIONEN FÜR LABEL-GENERIERUNG
# =============================================================================


def compute_armstrong_event_labels(
    data: pd.DataFrame,
    armstrong_params: Dict[str, Any],
) -> pd.Series:
    """
    Berechnet Armstrong Event-State Labels für jeden Bar.

    Args:
        data: OHLCV-DataFrame mit DatetimeIndex
        armstrong_params: Parameter für Armstrong-Cycle

    Returns:
        Series mit Event-State Labels (NONE, PRE_EVENT, EVENT, POST_EVENT)
    """
    cycle_length_days = armstrong_params.get("cycle_length_days", 3141)
    event_window_days = armstrong_params.get("event_window_days", 90)
    reference_date = pd.Timestamp(armstrong_params.get("reference_date", "2015-10-01"))

    # Pre-/Post-Event Fenster (je 1/3 des Event-Fensters)
    pre_event_days = event_window_days // 3
    post_event_days = event_window_days // 3

    labels = pd.Series(ArmstrongEventState.NONE, index=data.index)

    # Handle timezone-aware vs naive datetime
    index_for_calc = data.index
    ref_date = reference_date
    if hasattr(index_for_calc, "tz") and index_for_calc.tz is not None:
        index_for_calc = index_for_calc.tz_localize(None)
    if hasattr(ref_date, "tz") and ref_date.tz is not None:
        ref_date = ref_date.tz_localize(None)

    # Berechne Tage seit Referenz-Datum
    days_since_ref = (index_for_calc - ref_date).days

    # Berechne Position im Zyklus (0 = am Turning-Point)
    cycle_position = days_since_ref % cycle_length_days

    # Tage bis zum nächsten Turning-Point
    days_to_next = cycle_length_days - cycle_position

    # Tage seit dem letzten Turning-Point
    days_since_last = cycle_position

    # Klassifiziere Events
    for i, idx in enumerate(data.index):
        d_to_next = days_to_next.iloc[i] if hasattr(days_to_next, "iloc") else days_to_next[i]
        d_since_last = (
            days_since_last.iloc[i] if hasattr(days_since_last, "iloc") else days_since_last[i]
        )

        # PRE_EVENT: Kurz vor dem Turning-Point
        if d_to_next <= pre_event_days:
            labels.iloc[i] = ArmstrongEventState.PRE_EVENT
        # POST_EVENT: Kurz nach dem Turning-Point
        elif d_since_last <= post_event_days:
            labels.iloc[i] = ArmstrongEventState.POST_EVENT
        # EVENT: Im Event-Fenster (nahe am Turning-Point)
        elif d_to_next <= event_window_days or d_since_last <= event_window_days:
            labels.iloc[i] = ArmstrongEventState.EVENT
        else:
            labels.iloc[i] = ArmstrongEventState.NONE

    return labels


def compute_elkaroui_regime_labels(
    data: pd.DataFrame,
    elkaroui_params: Dict[str, Any],
) -> pd.Series:
    """
    Berechnet El-Karoui Volatilitäts-Regime Labels für jeden Bar.

    Args:
        data: OHLCV-DataFrame mit 'close' Spalte
        elkaroui_params: Parameter für El-Karoui-Vol-Model

    Returns:
        Series mit Regime Labels (LOW, MEDIUM, HIGH)
    """
    vol_window = elkaroui_params.get("vol_window", 20)
    vol_threshold_low = elkaroui_params.get("vol_threshold_low", 0.3)
    vol_threshold_high = elkaroui_params.get("vol_threshold_high", 0.7)
    use_ewm = elkaroui_params.get("use_ewm", True)
    annualization_factor = elkaroui_params.get("annualization_factor", 252.0)

    if "close" not in data.columns:
        raise ValueError("DataFrame muss 'close' Spalte enthalten")

    # Berechne Returns
    returns = data["close"].pct_change()

    # Berechne realisierte Volatilität
    if use_ewm:
        vol = returns.ewm(span=vol_window, min_periods=vol_window).std()
    else:
        vol = returns.rolling(window=vol_window, min_periods=vol_window).std()

    # Annualisierte Volatilität
    vol_annualized = vol * np.sqrt(annualization_factor)

    # Berechne rollende Quantile für Regime-Klassifikation
    lookback_window = min(252, len(data) // 2)
    if lookback_window < vol_window:
        lookback_window = vol_window

    vol_quantiles = vol_annualized.rolling(window=lookback_window, min_periods=vol_window).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=False
    )

    # Klassifiziere Regime
    labels = pd.Series(ElKarouiRegime.MEDIUM, index=data.index)
    labels[vol_quantiles <= vol_threshold_low] = ElKarouiRegime.LOW
    labels[vol_quantiles >= vol_threshold_high] = ElKarouiRegime.HIGH

    return labels


def compute_forward_returns(
    data: pd.DataFrame,
    windows: List[int],
) -> pd.DataFrame:
    """
    Berechnet Forward-Returns für verschiedene Fenstergrößen.

    Args:
        data: OHLCV-DataFrame mit 'close' Spalte
        windows: Liste von Fenstergrößen in Bars

    Returns:
        DataFrame mit Forward-Return-Spalten
    """
    if "close" not in data.columns:
        raise ValueError("DataFrame muss 'close' Spalte enthalten")

    result = pd.DataFrame(index=data.index)

    for window in windows:
        # Forward-Return: (Close[t+window] - Close[t]) / Close[t]
        result[f"ret_{window}d_fwd"] = data["close"].pct_change(window).shift(-window)

    return result


def create_combo_state_labels(
    armstrong_labels: pd.Series,
    elkaroui_labels: pd.Series,
) -> pd.Series:
    """
    Kombiniert Armstrong- und El-Karoui-Labels zu Kombi-States.

    Args:
        armstrong_labels: Armstrong Event-State Labels
        elkaroui_labels: El-Karoui Regime Labels

    Returns:
        Series mit Kombi-State Labels (z.B. "EVENT_HIGH", "NONE_LOW")
    """
    combo_labels = armstrong_labels.astype(str) + "_" + elkaroui_labels.astype(str)
    return combo_labels


# =============================================================================
# AGGREGATION FUNKTIONEN
# =============================================================================


def compute_combo_stats(
    labels_df: pd.DataFrame,
    combo_col: str = "combo_state",
    return_cols: Optional[List[str]] = None,
    big_move_threshold: float = 0.02,
) -> Dict[str, Dict[str, Any]]:
    """
    Berechnet aggregierte Statistiken pro Kombi-State.

    Args:
        labels_df: DataFrame mit Labels und Returns
        combo_col: Name der Kombi-State-Spalte
        return_cols: Liste der Return-Spalten
        big_move_threshold: Schwelle für "große Bewegungen"

    Returns:
        Dict mit Stats pro Kombi-State
    """
    if return_cols is None:
        return_cols = [col for col in labels_df.columns if col.startswith("ret_")]

    stats = {}

    for combo_state in labels_df[combo_col].dropna().unique():
        mask = labels_df[combo_col] == combo_state
        subset = labels_df[mask]

        state_stats: Dict[str, Any] = {
            "count_bars": int(len(subset)),
        }

        # Return-Statistiken
        for ret_col in return_cols:
            if ret_col not in subset.columns:
                continue

            valid_returns = subset[ret_col].dropna()
            if len(valid_returns) == 0:
                continue

            # Basis-Statistiken
            state_stats[f"avg_{ret_col}"] = float(valid_returns.mean())
            state_stats[f"std_{ret_col}"] = float(valid_returns.std())
            state_stats[f"median_{ret_col}"] = float(valid_returns.median())

            # Große Bewegungen
            big_moves = (valid_returns.abs() > big_move_threshold).sum()
            state_stats[f"p_big_move_{ret_col.replace('ret_', '').replace('_fwd', '')}"] = (
                float(big_moves / len(valid_returns)) if len(valid_returns) > 0 else 0.0
            )

        stats[combo_state] = state_stats

    return stats


# =============================================================================
# HAUPTFUNKTION
# =============================================================================


def run_armstrong_elkaroui_combi_experiment(
    config: ArmstrongElKarouiCombiConfig,
    data: Optional[pd.DataFrame] = None,
) -> CombiExperimentResult:
    """
    Führt das Armstrong-El-Karoui Kombi-Experiment aus.

    Args:
        config: Experiment-Konfiguration
        data: Optional OHLCV-DataFrame (falls None, wird geladen)

    Returns:
        CombiExperimentResult mit allen Ergebnissen

    Raises:
        ValueError: Bei ungültiger Konfiguration
    """
    import hashlib
    from datetime import datetime as dt

    # Run-ID generieren
    run_id = f"rnd_combi_{dt.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(config.to_dict()).encode()).hexdigest()[:8]}"

    logger.info(f"Starte Armstrong-El-Karoui Kombi-Experiment: {run_id}")
    logger.info(f"  Symbol: {config.symbol}")
    logger.info(f"  Timeframe: {config.timeframe}")
    logger.info(f"  Zeitraum: {config.start_date} - {config.end_date}")

    try:
        # 1. Daten laden falls nicht übergeben
        if data is None:
            data = _load_data(config)

        if data.empty:
            raise ValueError(f"Keine Daten für {config.symbol} gefunden")

        logger.info(f"  Bars geladen: {len(data)}")

        # 2. Armstrong-Labels berechnen
        logger.info("  Berechne Armstrong Event-States...")
        armstrong_labels = compute_armstrong_event_labels(data, config.armstrong_params)

        # 3. El-Karoui-Regime berechnen
        logger.info("  Berechne El-Karoui Regime-Labels...")
        elkaroui_labels = compute_elkaroui_regime_labels(data, config.elkaroui_params)

        # 4. Kombi-States bilden
        logger.info("  Erstelle Kombi-States...")
        combo_labels = create_combo_state_labels(armstrong_labels, elkaroui_labels)

        # 5. Forward-Returns berechnen
        logger.info("  Berechne Forward-Returns...")
        forward_returns = compute_forward_returns(data, config.forward_return_windows)

        # 6. Labels-DataFrame zusammenstellen
        labels_df = pd.DataFrame(
            {
                "armstrong_state": armstrong_labels,
                "elkaroui_regime": elkaroui_labels,
                "combo_state": combo_labels,
            }
        )
        labels_df = pd.concat([labels_df, forward_returns], axis=1)

        # 7. Aggregierte Statistiken berechnen
        logger.info("  Berechne aggregierte Statistiken...")
        combo_stats = compute_combo_stats(labels_df, combo_col="combo_state")

        # 8. Metadata sammeln
        metadata = {
            "num_bars": len(data),
            "start_date": data.index[0].isoformat() if len(data) > 0 else None,
            "end_date": data.index[-1].isoformat() if len(data) > 0 else None,
            "num_combo_states": len(combo_stats),
            "armstrong_state_distribution": armstrong_labels.value_counts().to_dict(),
            "elkaroui_regime_distribution": elkaroui_labels.value_counts().to_dict(),
        }

        logger.info(f"  Kombi-States gefunden: {len(combo_stats)}")
        for state, stats in sorted(combo_stats.items()):
            logger.info(f"    {state}: {stats.get('count_bars', 0)} Bars")

        result = CombiExperimentResult(
            run_id=run_id,
            config=config,
            combo_stats=combo_stats,
            label_series=labels_df,
            metadata=metadata,
            success=True,
        )

        # 9. Ergebnis speichern
        result.save_json()

        logger.info(f"✅ Experiment erfolgreich: {run_id}")

        return result

    except Exception as e:
        logger.error(f"❌ Experiment fehlgeschlagen: {e}")
        return CombiExperimentResult(
            run_id=run_id,
            config=config,
            combo_stats={},
            success=False,
            error_message=str(e),
        )


def _load_data(config: ArmstrongElKarouiCombiConfig) -> pd.DataFrame:
    """
    Lädt OHLCV-Daten für das Experiment.

    Args:
        config: Experiment-Konfiguration

    Returns:
        DataFrame mit OHLCV-Daten
    """
    try:
        from src.data.kraken import fetch_ohlcv_df
    except ImportError:
        logger.warning("Kraken-Data-Loader nicht verfügbar, verwende Dummy-Daten")
        return _generate_dummy_data(config)

    try:
        # Versuche echte Daten zu laden
        df = fetch_ohlcv_df(
            symbol=config.symbol,
            timeframe=config.timeframe,
            limit=2000,
            use_cache=True,
        )

        if df.empty:
            logger.warning("Keine Marktdaten gefunden, verwende Dummy-Daten")
            return _generate_dummy_data(config)

        # Datums-Filter anwenden
        if config.start_date:
            start_dt = pd.to_datetime(config.start_date)
            if start_dt.tz is None and df.index.tz is not None:
                start_dt = start_dt.tz_localize(df.index.tz)
            df = df[df.index >= start_dt]

        if config.end_date:
            end_dt = pd.to_datetime(config.end_date)
            if end_dt.tz is None and df.index.tz is not None:
                end_dt = end_dt.tz_localize(df.index.tz)
            df = df[df.index <= end_dt]

        return df

    except Exception as e:
        logger.warning(f"Konnte Marktdaten nicht laden: {e}")
        return _generate_dummy_data(config)


def _generate_dummy_data(config: ArmstrongElKarouiCombiConfig) -> pd.DataFrame:
    """
    Generiert Dummy-OHLCV-Daten für Tests.

    Args:
        config: Experiment-Konfiguration

    Returns:
        DataFrame mit Dummy-OHLCV-Daten
    """
    # Berechne Anzahl Bars basierend auf Timeframe
    tf_hours = {"1h": 1, "4h": 4, "1d": 24, "1w": 168}.get(config.timeframe, 1)
    hours_total = (config.end_date - config.start_date).total_seconds() / 3600
    n_bars = int(hours_total / tf_hours)
    n_bars = max(100, min(n_bars, 10000))  # Zwischen 100 und 10000 Bars

    # Generiere Index
    freq = {"1h": "1h", "4h": "4h", "1d": "1D", "1w": "1W"}.get(config.timeframe, "1h")
    index = pd.date_range(start=config.start_date, periods=n_bars, freq=freq, tz="UTC")

    # Random Walk für Close
    np.random.seed(42)
    base_price = 50000.0
    volatility = 0.015
    returns = np.random.normal(0, volatility, n_bars)
    trend = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * 0.001
    returns = returns + trend
    close_prices = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame(index=index)
    df["close"] = close_prices
    df["open"] = df["close"].shift(1).fillna(base_price)
    high_bump = np.random.uniform(0, 0.005, n_bars)
    df["high"] = np.maximum(df["open"], df["close"]) * (1 + high_bump)
    low_dip = np.random.uniform(0, 0.005, n_bars)
    df["low"] = np.minimum(df["open"], df["close"]) * (1 - low_dip)
    df["volume"] = np.random.uniform(100, 1000, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


# =============================================================================
# REPORT GENERATOR
# =============================================================================


def generate_armstrong_elkaroui_combi_report(
    result: CombiExperimentResult,
    output_dir: Optional[str] = None,
) -> str:
    """
    Generiert einen Markdown-Report für das Kombi-Experiment.

    Args:
        result: Experiment-Ergebnis
        output_dir: Optionales Output-Verzeichnis

    Returns:
        Pfad zur generierten Report-Datei
    """
    if output_dir is None:
        output_dir = result.config.output_dir

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    report_file = output_path / f"{result.run_id}_report.md"

    lines = [
        "# Armstrong × El-Karoui Kombi-Experiment Report",
        "",
        f"**Run-ID:** `{result.run_id}`",
        f"**Datum:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Status:** {'✅ Erfolgreich' if result.success else '❌ Fehlgeschlagen'}",
        "",
        "---",
        "",
        "## 1. Setup",
        "",
        f"- **Symbol:** {result.config.symbol}",
        f"- **Timeframe:** {result.config.timeframe}",
        f"- **Zeitraum:** {result.config.start_date} bis {result.config.end_date}",
        f"- **Run-Type:** {result.run_type}",
        f"- **Tier:** {result.tier}",
        f"- **Environment:** {result.environment}",
        "",
        "### Armstrong-Parameter",
        "",
        "| Parameter | Wert |",
        "|-----------|------|",
    ]

    for k, v in result.config.armstrong_params.items():
        lines.append(f"| {k} | {v} |")

    lines.extend(
        [
            "",
            "### El-Karoui-Parameter",
            "",
            "| Parameter | Wert |",
            "|-----------|------|",
        ]
    )

    for k, v in result.config.elkaroui_params.items():
        lines.append(f"| {k} | {v} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 2. Kombi-State-Statistiken",
            "",
        ]
    )

    if result.combo_stats:
        # Tabelle der Kombi-States
        lines.extend(
            [
                "| Kombi-State | Anzahl Bars | Avg Ret 1d | Avg Ret 3d | Avg Ret 7d | P(Big Move) |",
                "|-------------|-------------|------------|------------|------------|-------------|",
            ]
        )

        # Sortiere nach avg_ret_3d_fwd
        sorted_states = sorted(
            result.combo_stats.items(),
            key=lambda x: x[1].get("avg_ret_3d_fwd", 0),
            reverse=True,
        )

        for state, stats in sorted_states:
            count = stats.get("count_bars", 0)
            avg_1d = stats.get("avg_ret_1d_fwd", 0) * 100
            avg_3d = stats.get("avg_ret_3d_fwd", 0) * 100
            avg_7d = stats.get("avg_ret_7d_fwd", 0) * 100
            p_big = stats.get("p_big_move_3d", 0) * 100
            lines.append(
                f"| {state} | {count} | {avg_1d:+.2f}% | {avg_3d:+.2f}% | {avg_7d:+.2f}% | {p_big:.1f}% |"
            )

        lines.extend(
            [
                "",
                "---",
                "",
                "## 3. Label-Verteilung",
                "",
            ]
        )

        # Armstrong-Verteilung
        if "armstrong_state_distribution" in result.metadata:
            lines.extend(
                [
                    "### Armstrong Event-States",
                    "",
                    "| State | Anzahl |",
                    "|-------|--------|",
                ]
            )
            for state, count in result.metadata["armstrong_state_distribution"].items():
                lines.append(f"| {state} | {count} |")

        # El-Karoui-Verteilung
        if "elkaroui_regime_distribution" in result.metadata:
            lines.extend(
                [
                    "",
                    "### El-Karoui Regime",
                    "",
                    "| Regime | Anzahl |",
                    "|--------|--------|",
                ]
            )
            for regime, count in result.metadata["elkaroui_regime_distribution"].items():
                lines.append(f"| {regime} | {count} |")

    else:
        lines.append("*Keine Statistiken verfügbar.*")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 4. Metadaten",
            "",
            f"- **Anzahl Bars:** {result.metadata.get('num_bars', 'N/A')}",
            f"- **Datenstart:** {result.metadata.get('start_date', 'N/A')}",
            f"- **Datenende:** {result.metadata.get('end_date', 'N/A')}",
            f"- **Anzahl Kombi-States:** {result.metadata.get('num_combo_states', 'N/A')}",
            "",
        ]
    )

    if result.error_message:
        lines.extend(
            [
                "---",
                "",
                "## ⚠️ Fehler",
                "",
                f"```\n{result.error_message}\n```",
                "",
            ]
        )

    # Report schreiben
    with open(report_file, "w") as f:
        f.write("\n".join(lines))

    logger.info(f"Report generiert: {report_file}")

    return str(report_file)

