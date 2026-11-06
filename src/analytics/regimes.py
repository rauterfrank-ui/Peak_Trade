# src/analytics/regimes.py
"""
Peak_Trade – Regime-Analyse & Robustheits-Tools (Phase 19)
==========================================================
Modul zur Erkennung von Marktregimes und Analyse der Strategie-Performance
in unterschiedlichen Marktphasen.

Regime-Typen:
- Volatilität: low_vol / mid_vol / high_vol
- Trend: uptrend / sideways / downtrend

Funktionen:
- load_regime_config(): Lädt Konfiguration aus config/regimes.toml
- detect_regimes(): Erkennt Regimes in einer Preiszeitreihe
- analyze_regimes_from_equity(): Analysiert Performance pro Regime
- analyze_experiment_regimes(): High-Level-Analyse für Experimente

Hinweis:
    Dieses Modul ist rein analytisch (Phase 19 Scope).
    Es liest nur Daten und erzeugt Statistiken.
    Keine Änderungen an Order-/Execution-/Safety-Komponenten.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal, Union
import logging

import numpy as np
import pandas as pd

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

logger = logging.getLogger(__name__)


# =============================================================================
# KONSTANTEN
# =============================================================================

VolRegimeType = Literal["low_vol", "mid_vol", "high_vol"]
TrendRegimeType = Literal["uptrend", "sideways", "downtrend"]

DEFAULT_CONFIG_PATH = Path("config/regimes.toml")


# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class RegimeConfig:
    """
    Konfigurationsparameter für die Regime-Erkennung.

    Volatilität wird als annualisierte Rolling-StdDev der Log-Returns berechnet.
    Trend wird über relative MA-Differenzen bestimmt.

    Attributes:
        vol_lookback: Anzahl Bars für Rolling-Volatilität
        vol_low_threshold: Schwelle für low_vol (annualisiert)
        vol_high_threshold: Schwelle für high_vol (annualisiert)
        vol_annualization_factor: Faktor zur Annualisierung (z.B. 365 für täglich)
        trend_short_window: Fenster für kurzfristigen MA
        trend_long_window: Fenster für langfristigen MA
        trend_slope_threshold: Schwelle für Trend-Klassifikation (relativ)
    """

    vol_lookback: int = 20
    vol_low_threshold: float = 0.30
    vol_high_threshold: float = 0.60
    vol_annualization_factor: int = 365
    trend_short_window: int = 20
    trend_long_window: int = 50
    trend_slope_threshold: float = 0.02

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Config zu Dict."""
        return {
            "vol_lookback": self.vol_lookback,
            "vol_low_threshold": self.vol_low_threshold,
            "vol_high_threshold": self.vol_high_threshold,
            "vol_annualization_factor": self.vol_annualization_factor,
            "trend_short_window": self.trend_short_window,
            "trend_long_window": self.trend_long_window,
            "trend_slope_threshold": self.trend_slope_threshold,
        }


@dataclass
class RegimeLabel:
    """
    Regime-Label für einen einzelnen Zeitpunkt.

    Attributes:
        timestamp: Zeitstempel des Datenpunkts
        vol_regime: Volatilitäts-Regime (low_vol/mid_vol/high_vol)
        trend_regime: Trend-Regime (uptrend/sideways/downtrend)
    """

    timestamp: pd.Timestamp
    vol_regime: str  # "low_vol" | "mid_vol" | "high_vol"
    trend_regime: str  # "uptrend" | "sideways" | "downtrend"

    @property
    def combined(self) -> str:
        """Kombiniertes Regime-Label (z.B. 'low_vol_uptrend')."""
        return f"{self.vol_regime}_{self.trend_regime}"


@dataclass
class RegimeStats:
    """
    Performance-Statistiken für ein einzelnes Regime.

    Attributes:
        regime: Regime-Bezeichnung (z.B. "low_vol_uptrend" oder "low_vol")
        weight: Anteil an der Gesamtzeit (0..1)
        bar_count: Anzahl Bars in diesem Regime
        return_sum: Summe der Returns
        return_mean: Durchschnittlicher Return pro Bar
        return_std: Standardabweichung der Returns
        sharpe: Annualisierter Sharpe Ratio (kann None sein bei zu wenig Daten)
        max_drawdown: Maximaler Drawdown innerhalb dieses Regimes (kann None sein)
        total_return: Kumulierter Return in diesem Regime
    """

    regime: str
    weight: float
    bar_count: int
    return_sum: float
    return_mean: float
    return_std: float
    sharpe: Optional[float] = None
    max_drawdown: Optional[float] = None
    total_return: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dict."""
        return {
            "regime": self.regime,
            "weight": self.weight,
            "bar_count": self.bar_count,
            "return_sum": self.return_sum,
            "return_mean": self.return_mean,
            "return_std": self.return_std,
            "sharpe": self.sharpe,
            "max_drawdown": self.max_drawdown,
            "total_return": self.total_return,
        }


@dataclass
class RegimeAnalysisResult:
    """
    Vollständiges Ergebnis einer Regime-Analyse.

    Attributes:
        experiment_id: ID des analysierten Experiments (optional)
        strategy_name: Name der Strategie (optional)
        regimes: Liste von RegimeStats für jedes Regime
        overall_return: Gesamtreturn über alle Regimes
        overall_sharpe: Gesamter Sharpe Ratio
        regime_distribution: Dict mit Regime -> Anteil
        config_used: Die verwendete RegimeConfig
    """

    experiment_id: Optional[str] = None
    strategy_name: Optional[str] = None
    regimes: List[RegimeStats] = field(default_factory=list)
    overall_return: float = 0.0
    overall_sharpe: Optional[float] = None
    regime_distribution: Dict[str, float] = field(default_factory=dict)
    config_used: Optional[RegimeConfig] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dict für Serialisierung."""
        return {
            "experiment_id": self.experiment_id,
            "strategy_name": self.strategy_name,
            "regimes": [r.to_dict() for r in self.regimes],
            "overall_return": self.overall_return,
            "overall_sharpe": self.overall_sharpe,
            "regime_distribution": self.regime_distribution,
            "config_used": self.config_used.to_dict() if self.config_used else None,
        }

    def get_best_regime(self) -> Optional[RegimeStats]:
        """Gibt das Regime mit dem besten Sharpe zurück."""
        valid = [r for r in self.regimes if r.sharpe is not None]
        if not valid:
            return None
        return max(valid, key=lambda r: r.sharpe or float("-inf"))

    def get_worst_regime(self) -> Optional[RegimeStats]:
        """Gibt das Regime mit dem schlechtesten Sharpe zurück."""
        valid = [r for r in self.regimes if r.sharpe is not None]
        if not valid:
            return None
        return min(valid, key=lambda r: r.sharpe or float("inf"))


# =============================================================================
# KONFIGURATION LADEN
# =============================================================================


def load_regime_config(path: Optional[Path] = None) -> RegimeConfig:
    """
    Lädt Regime-Konfiguration aus TOML-Datei.

    Args:
        path: Pfad zur Konfigurationsdatei.
              Default: config/regimes.toml

    Returns:
        RegimeConfig mit geladenen Werten

    Raises:
        FileNotFoundError: Wenn Config-Datei nicht existiert
        ValueError: Bei ungültigen Werten

    Example:
        >>> cfg = load_regime_config()
        >>> print(f"Vol-Lookback: {cfg.vol_lookback}")
    """
    config_path = path or DEFAULT_CONFIG_PATH

    if not config_path.exists():
        logger.warning(f"Regime-Config nicht gefunden: {config_path}. Verwende Default-Werte.")
        return RegimeConfig()

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    vol_section = data.get("volatility", {})
    trend_section = data.get("trend", {})

    return RegimeConfig(
        vol_lookback=int(vol_section.get("lookback", 20)),
        vol_low_threshold=float(vol_section.get("low_threshold", 0.30)),
        vol_high_threshold=float(vol_section.get("high_threshold", 0.60)),
        vol_annualization_factor=int(vol_section.get("annualization_factor", 365)),
        trend_short_window=int(trend_section.get("short_window", 20)),
        trend_long_window=int(trend_section.get("long_window", 50)),
        trend_slope_threshold=float(trend_section.get("slope_threshold", 0.02)),
    )


# =============================================================================
# REGIME-ERKENNUNG
# =============================================================================


def _compute_log_returns(prices: pd.Series) -> pd.Series:
    """Berechnet Log-Returns aus einer Preisreihe."""
    return np.log(prices / prices.shift(1))


def _compute_rolling_volatility(
    prices: pd.Series,
    lookback: int,
    annualization_factor: int = 365,
) -> pd.Series:
    """
    Berechnet annualisierte Rolling-Volatilität.

    Args:
        prices: Preisreihe
        lookback: Fenster für Rolling-StdDev
        annualization_factor: Faktor zur Annualisierung

    Returns:
        Series mit annualisierter Volatilität
    """
    log_returns = _compute_log_returns(prices)
    rolling_std = log_returns.rolling(window=lookback, min_periods=1).std()
    # Annualisieren
    annualized = rolling_std * np.sqrt(annualization_factor)
    return annualized


def _classify_volatility(
    vol: pd.Series,
    low_threshold: float,
    high_threshold: float,
) -> pd.Series:
    """
    Klassifiziert Volatilität in low_vol/mid_vol/high_vol.

    Args:
        vol: Volatilitäts-Series
        low_threshold: Schwelle für low_vol
        high_threshold: Schwelle für high_vol

    Returns:
        Series mit Regime-Labels
    """
    labels = pd.Series("mid_vol", index=vol.index, dtype="object")
    labels = labels.mask(vol < low_threshold, "low_vol")
    labels = labels.mask(vol > high_threshold, "high_vol")
    return labels


def _compute_ma_delta(
    prices: pd.Series,
    short_window: int,
    long_window: int,
) -> pd.Series:
    """
    Berechnet relative Differenz zwischen kurzem und langem MA.

    Args:
        prices: Preisreihe
        short_window: Fenster für kurzen MA
        long_window: Fenster für langen MA

    Returns:
        Series mit (MA_short - MA_long) / MA_long
    """
    ma_short = prices.rolling(window=short_window, min_periods=1).mean()
    ma_long = prices.rolling(window=long_window, min_periods=1).mean()
    # Relative Differenz (vermeidet Division durch 0)
    delta = (ma_short - ma_long) / ma_long.replace(0, np.nan)
    return delta.fillna(0)


def _classify_trend(
    ma_delta: pd.Series,
    slope_threshold: float,
) -> pd.Series:
    """
    Klassifiziert Trend in uptrend/sideways/downtrend.

    Args:
        ma_delta: MA-Differenz-Series
        slope_threshold: Schwelle für Trend-Erkennung

    Returns:
        Series mit Regime-Labels
    """
    labels = pd.Series("sideways", index=ma_delta.index, dtype="object")
    labels = labels.mask(ma_delta > slope_threshold, "uptrend")
    labels = labels.mask(ma_delta < -slope_threshold, "downtrend")
    return labels


def detect_regimes(
    prices: pd.DataFrame,
    cfg: RegimeConfig,
    price_col: str = "close",
) -> pd.DataFrame:
    """
    Erkennt Marktregimes in einer Preiszeitreihe.

    Berechnet für jeden Zeitpunkt:
    - Volatilitäts-Regime (low_vol / mid_vol / high_vol)
    - Trend-Regime (uptrend / sideways / downtrend)
    - Kombiniertes Regime (z.B. "low_vol_uptrend")

    Args:
        prices: DataFrame mit DatetimeIndex und Preis-Spalte
        cfg: RegimeConfig mit Parametern
        price_col: Name der Preis-Spalte (default: 'close')

    Returns:
        DataFrame mit zusätzlichen Spalten:
        - 'vol_regime': Volatilitäts-Regime
        - 'trend_regime': Trend-Regime
        - 'regime': Kombiniertes Regime
        - 'volatility': Berechnete annualisierte Volatilität
        - 'ma_delta': MA-Differenz

    Raises:
        KeyError: Wenn price_col nicht existiert

    Example:
        >>> cfg = load_regime_config()
        >>> df = detect_regimes(prices_df, cfg)
        >>> print(df['regime'].value_counts())
    """
    if price_col not in prices.columns:
        raise KeyError(
            f"Spalte '{price_col}' nicht im DataFrame. Verfügbare Spalten: {list(prices.columns)}"
        )

    result = prices.copy()
    price_series = prices[price_col].astype(float)

    # Volatilität berechnen und klassifizieren
    volatility = _compute_rolling_volatility(
        price_series,
        lookback=cfg.vol_lookback,
        annualization_factor=cfg.vol_annualization_factor,
    )
    vol_regime = _classify_volatility(
        volatility,
        low_threshold=cfg.vol_low_threshold,
        high_threshold=cfg.vol_high_threshold,
    )

    # Trend berechnen und klassifizieren
    ma_delta = _compute_ma_delta(
        price_series,
        short_window=cfg.trend_short_window,
        long_window=cfg.trend_long_window,
    )
    trend_regime = _classify_trend(ma_delta, slope_threshold=cfg.trend_slope_threshold)

    # Ergebnisse hinzufügen
    result["volatility"] = volatility
    result["ma_delta"] = ma_delta
    result["vol_regime"] = vol_regime
    result["trend_regime"] = trend_regime
    result["regime"] = vol_regime + "_" + trend_regime

    return result


def get_regime_distribution(regimes: pd.DataFrame) -> Dict[str, float]:
    """
    Berechnet die Verteilung der Regimes.

    Args:
        regimes: DataFrame mit 'regime'-Spalte

    Returns:
        Dict mit Regime -> Anteil (0..1)
    """
    if "regime" not in regimes.columns or regimes.empty:
        return {}

    counts = regimes["regime"].value_counts(normalize=True)
    return counts.to_dict()


# =============================================================================
# REGIME-PERFORMANCE-ANALYSE
# =============================================================================


def _compute_drawdown(equity: pd.Series) -> pd.Series:
    """Berechnet Drawdown aus Equity-Curve."""
    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max.replace(0, np.nan)
    return drawdown.fillna(0)


def analyze_regimes_from_equity(
    equity: pd.Series,
    regimes: pd.DataFrame,
    annualization_factor: int = 365,
    combine_regimes: bool = True,
) -> List[RegimeStats]:
    """
    Analysiert Performance pro Regime basierend auf Equity-Curve.

    Berechnet für jedes Regime:
    - Anteil an Gesamtzeit (weight)
    - Return-Statistiken (mean, std, sum)
    - Sharpe Ratio (annualisiert)
    - Max Drawdown (lokal innerhalb des Regimes)

    Args:
        equity: Equity-Curve (Series mit DatetimeIndex)
        regimes: DataFrame mit 'regime' oder 'vol_regime'/'trend_regime' Spalten
        annualization_factor: Faktor für Sharpe-Annualisierung
        combine_regimes: Wenn True, kombinierte Regimes analysieren.
                         Wenn False, nur Vol- und Trend-Regimes separat.

    Returns:
        Liste von RegimeStats für jedes Regime

    Example:
        >>> stats = analyze_regimes_from_equity(equity_curve, regime_df)
        >>> for s in stats:
        ...     print(f"{s.regime}: Sharpe={s.sharpe:.2f}")
    """
    if equity.empty or regimes.empty:
        return []

    # Indices angleichen (nur gemeinsame Zeitpunkte)
    common_idx = equity.index.intersection(regimes.index)
    if len(common_idx) == 0:
        logger.warning("Keine gemeinsamen Zeitpunkte zwischen Equity und Regimes.")
        return []

    equity = equity.loc[common_idx]
    regimes = regimes.loc[common_idx]

    # Returns berechnen
    returns = equity.pct_change().fillna(0)

    # Regime-Spalte bestimmen
    if combine_regimes and "regime" in regimes.columns:
        regime_col = "regime"
    elif "vol_regime" in regimes.columns:
        regime_col = "vol_regime"
    elif "trend_regime" in regimes.columns:
        regime_col = "trend_regime"
    else:
        logger.warning("Keine Regime-Spalte im DataFrame gefunden.")
        return []

    # Eindeutige Regimes
    unique_regimes = regimes[regime_col].unique()
    total_bars = len(regimes)

    stats_list = []
    for regime_name in unique_regimes:
        mask = regimes[regime_col] == regime_name
        regime_returns = returns[mask]
        regime_equity = equity[mask]

        bar_count = int(mask.sum())
        weight = bar_count / total_bars if total_bars > 0 else 0.0

        # Return-Statistiken
        return_sum = float(regime_returns.sum())
        return_mean = float(regime_returns.mean()) if len(regime_returns) > 0 else 0.0
        return_std = float(regime_returns.std(ddof=1)) if len(regime_returns) > 1 else 0.0

        # Sharpe Ratio
        sharpe = None
        if return_std > 0 and len(regime_returns) > 1:
            sharpe = float(return_mean / return_std * np.sqrt(annualization_factor))

        # Lokaler Max Drawdown
        max_dd = None
        if len(regime_equity) > 1:
            dd = _compute_drawdown(regime_equity)
            max_dd = float(dd.min()) if not dd.empty else None

        # Total Return für dieses Regime
        total_return = None
        if len(regime_equity) > 1:
            start_val = regime_equity.iloc[0]
            end_val = regime_equity.iloc[-1]
            if start_val > 0:
                total_return = float((end_val - start_val) / start_val)

        stats_list.append(
            RegimeStats(
                regime=str(regime_name),
                weight=weight,
                bar_count=bar_count,
                return_sum=return_sum,
                return_mean=return_mean,
                return_std=return_std,
                sharpe=sharpe,
                max_drawdown=max_dd,
                total_return=total_return,
            )
        )

    # Nach Weight sortieren (absteigend)
    stats_list.sort(key=lambda s: s.weight, reverse=True)

    return stats_list


def analyze_experiment_regimes(
    prices: pd.DataFrame,
    equity: pd.Series,
    cfg: Optional[RegimeConfig] = None,
    experiment_id: Optional[str] = None,
    strategy_name: Optional[str] = None,
    price_col: str = "close",
) -> RegimeAnalysisResult:
    """
    High-Level Regime-Analyse für ein Experiment.

    Kombiniert detect_regimes() und analyze_regimes_from_equity()
    zu einem vollständigen Analyse-Ergebnis.

    Args:
        prices: DataFrame mit OHLCV-Daten (DatetimeIndex)
        equity: Equity-Curve des Backtests
        cfg: RegimeConfig (default: lädt aus config/regimes.toml)
        experiment_id: Optionale Experiment-ID für Zuordnung
        strategy_name: Optionaler Strategie-Name
        price_col: Name der Preis-Spalte

    Returns:
        RegimeAnalysisResult mit vollständiger Analyse

    Example:
        >>> result = analyze_experiment_regimes(prices, equity, strategy_name="ma_crossover")
        >>> print(f"Best Regime: {result.get_best_regime().regime}")
    """
    if cfg is None:
        cfg = load_regime_config()

    # Regimes erkennen
    regimes_df = detect_regimes(prices, cfg, price_col=price_col)

    # Regime-Statistiken berechnen
    regime_stats = analyze_regimes_from_equity(
        equity,
        regimes_df,
        annualization_factor=cfg.vol_annualization_factor,
    )

    # Gesamtstatistiken
    overall_return = 0.0
    if len(equity) > 1:
        start_val = float(equity.iloc[0])
        end_val = float(equity.iloc[-1])
        if start_val > 0:
            overall_return = (end_val - start_val) / start_val

    overall_sharpe = None
    if len(equity) > 1:
        returns = equity.pct_change().dropna()
        if len(returns) > 0 and returns.std() > 0:
            overall_sharpe = float(
                returns.mean() / returns.std() * np.sqrt(cfg.vol_annualization_factor)
            )

    # Regime-Verteilung
    regime_dist = get_regime_distribution(regimes_df)

    return RegimeAnalysisResult(
        experiment_id=experiment_id,
        strategy_name=strategy_name,
        regimes=regime_stats,
        overall_return=overall_return,
        overall_sharpe=overall_sharpe,
        regime_distribution=regime_dist,
        config_used=cfg,
    )


# =============================================================================
# ROBUSTHEITS-ANALYSE FÜR SWEEPS
# =============================================================================


@dataclass
class SweepRobustnessResult:
    """
    Robustheits-Analyse für einen Sweep.

    Attributes:
        sweep_name: Name des Sweeps
        run_count: Anzahl analysierter Runs
        regime_consistency: Dict[Regime -> Anzahl Runs mit positivem Sharpe]
        best_regime: Regime mit konsistent bester Performance
        worst_regime: Regime mit konsistent schlechtester Performance
        robustness_score: Score für Gesamt-Robustheit (0..1)
        per_run_results: Liste von RegimeAnalysisResult pro Run
    """

    sweep_name: str
    run_count: int
    regime_consistency: Dict[str, int] = field(default_factory=dict)
    best_regime: Optional[str] = None
    worst_regime: Optional[str] = None
    robustness_score: float = 0.0
    per_run_results: List[RegimeAnalysisResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dict."""
        return {
            "sweep_name": self.sweep_name,
            "run_count": self.run_count,
            "regime_consistency": self.regime_consistency,
            "best_regime": self.best_regime,
            "worst_regime": self.worst_regime,
            "robustness_score": self.robustness_score,
        }


def compute_sweep_robustness(
    regime_results: List[RegimeAnalysisResult],
    sweep_name: str = "unknown",
) -> SweepRobustnessResult:
    """
    Berechnet Robustheits-Metriken für einen Sweep.

    Analysiert, wie konsistent die Strategie über verschiedene
    Parameter-Kombinationen in verschiedenen Regimes performt.

    Args:
        regime_results: Liste von RegimeAnalysisResult für jeden Run
        sweep_name: Name des Sweeps

    Returns:
        SweepRobustnessResult mit Robustheits-Metriken
    """
    if not regime_results:
        return SweepRobustnessResult(sweep_name=sweep_name, run_count=0)

    run_count = len(regime_results)

    # Regime-Konsistenz: Wie oft ist Sharpe > 0 pro Regime?
    regime_positive_count: Dict[str, int] = {}
    regime_sharpe_sum: Dict[str, float] = {}
    regime_count: Dict[str, int] = {}

    for result in regime_results:
        for rs in result.regimes:
            regime = rs.regime
            regime_count[regime] = regime_count.get(regime, 0) + 1
            if rs.sharpe is not None:
                regime_sharpe_sum[regime] = regime_sharpe_sum.get(regime, 0) + rs.sharpe
                if rs.sharpe > 0:
                    regime_positive_count[regime] = regime_positive_count.get(regime, 0) + 1

    # Bestes und schlechtestes Regime (nach durchschnittlichem Sharpe)
    regime_avg_sharpe = {}
    for regime, total in regime_sharpe_sum.items():
        count = regime_count.get(regime, 1)
        regime_avg_sharpe[regime] = total / count

    best_regime = None
    worst_regime = None
    if regime_avg_sharpe:
        best_regime = max(regime_avg_sharpe, key=lambda r: regime_avg_sharpe[r])
        worst_regime = min(regime_avg_sharpe, key=lambda r: regime_avg_sharpe[r])

    # Robustness Score: Anteil der Runs mit positivem Sharpe in allen Regimes
    total_positives = sum(regime_positive_count.values())
    total_possible = sum(regime_count.values())
    robustness_score = total_positives / total_possible if total_possible > 0 else 0.0

    return SweepRobustnessResult(
        sweep_name=sweep_name,
        run_count=run_count,
        regime_consistency=regime_positive_count,
        best_regime=best_regime,
        worst_regime=worst_regime,
        robustness_score=robustness_score,
        per_run_results=regime_results,
    )


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def format_regime_stats_table(stats: List[RegimeStats]) -> str:
    """
    Formatiert RegimeStats als ASCII-Tabelle.

    Args:
        stats: Liste von RegimeStats

    Returns:
        Formatierter String für Terminal-Ausgabe
    """
    if not stats:
        return "Keine Regime-Statistiken verfügbar."

    lines = []
    header = (
        f"{'Regime':<25} {'Weight':>8} {'Bars':>6} {'Return_mean':>12} {'Sharpe':>8} {'MaxDD':>8}"
    )
    lines.append(header)
    lines.append("-" * len(header))

    for s in stats:
        weight_str = f"{s.weight:.1%}"
        mean_str = f"{s.return_mean:.4f}" if s.return_mean else "-"
        sharpe_str = f"{s.sharpe:.2f}" if s.sharpe is not None else "-"
        dd_str = f"{s.max_drawdown:.1%}" if s.max_drawdown is not None else "-"

        lines.append(
            f"{s.regime:<25} "
            f"{weight_str:>8} "
            f"{s.bar_count:>6} "
            f"{mean_str:>12} "
            f"{sharpe_str:>8} "
            f"{dd_str:>8}"
        )

    return "\n".join(lines)


def create_regime_summary_df(results: List[RegimeAnalysisResult]) -> pd.DataFrame:
    """
    Erstellt einen DataFrame mit Regime-Summaries für mehrere Experimente.

    Args:
        results: Liste von RegimeAnalysisResult

    Returns:
        DataFrame mit einer Zeile pro Experiment und Regime-Metriken als Spalten
    """
    rows = []
    for result in results:
        row = {
            "experiment_id": result.experiment_id,
            "strategy_name": result.strategy_name,
            "overall_return": result.overall_return,
            "overall_sharpe": result.overall_sharpe,
        }

        # Regime-spezifische Spalten
        for rs in result.regimes:
            row[f"{rs.regime}_weight"] = rs.weight
            row[f"{rs.regime}_sharpe"] = rs.sharpe
            row[f"{rs.regime}_return"] = rs.return_mean

        rows.append(row)

    return pd.DataFrame(rows)
