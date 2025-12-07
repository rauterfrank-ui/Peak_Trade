# src/experiments/regime_aware_portfolio_sweeps.py
"""
Peak_Trade Regime-Aware Portfolio Sweeps
=========================================

Vordefinierte Parameter-Sweeps für Regime-Aware Portfolio-Strategien.

Verfügbare Funktionen:
- get_regime_aware_portfolio_sweeps(): Sweeps für Portfolio-Parameter (Scales, Mode, etc.)
- get_regime_aware_aggressive_sweeps(): Aggressives Preset
- get_regime_aware_conservative_sweeps(): Konservatives Preset
- get_regime_aware_volmetric_sweeps(): Vol-Metrik-Vergleich Preset

Example:
    >>> from src.experiments.regime_aware_portfolio_sweeps import get_regime_aware_aggressive_sweeps
    >>> sweeps = get_regime_aware_aggressive_sweeps("medium")
    >>> print([s.name for s in sweeps])
    ['risk_on_scale', 'neutral_scale', 'risk_off_scale']
"""
from __future__ import annotations

from typing import List, Literal

from .base import ParamSweep

Granularity = Literal["coarse", "medium", "fine"]


# ============================================================================
# REGIME-AWARE PORTFOLIO BASE SWEEPS
# ============================================================================

def get_regime_aware_portfolio_sweeps(
    granularity: Granularity = "medium",
    include_components: bool = False,
) -> List[ParamSweep]:
    """
    Gibt Parameter-Sweeps für Regime-Aware Portfolio-Strategie zurück.

    Args:
        granularity: Sweep-Granularität ("coarse", "medium", "fine")
        include_components: Ob Komponenten-Gewichte gesweept werden sollen

    Returns:
        Liste von ParamSweep-Objekten für Portfolio-Parameter

    Sweeps enthalten:
    - risk_on_scale: Skalierungsfaktor für Risk-On-Regime
    - neutral_scale: Skalierungsfaktor für Neutral-Regime
    - risk_off_scale: Skalierungsfaktor für Risk-Off-Regime
    - mode: Skalierungs-Modus ("scale" oder "filter")
    - (optional) component-weights Variationen
    """
    sweeps = []

    if granularity == "coarse":
        sweeps.append(ParamSweep("risk_on_scale", [1.0], "Risk-On Scale"))
        sweeps.append(ParamSweep("neutral_scale", [0.3, 0.5, 0.7], "Neutral Scale"))
        sweeps.append(ParamSweep("risk_off_scale", [0.0, 0.1, 0.2], "Risk-Off Scale"))
        sweeps.append(ParamSweep("mode", ["scale"], "Skalierungs-Modus"))
    elif granularity == "medium":
        sweeps.append(ParamSweep("risk_on_scale", [1.0], "Risk-On Scale"))
        sweeps.append(ParamSweep("neutral_scale", [0.3, 0.4, 0.5, 0.6, 0.7], "Neutral Scale"))
        sweeps.append(ParamSweep("risk_off_scale", [0.0, 0.1, 0.2, 0.3], "Risk-Off Scale"))
        sweeps.append(ParamSweep("mode", ["scale", "filter"], "Skalierungs-Modus"))
        sweeps.append(ParamSweep("signal_threshold", [0.2, 0.3, 0.4], "Signal Threshold"))
    else:  # fine
        sweeps.append(ParamSweep("risk_on_scale", [0.9, 1.0], "Risk-On Scale"))
        sweeps.append(ParamSweep.from_range("neutral_scale", 0.2, 0.8, 0.1, "Neutral Scale"))
        sweeps.append(ParamSweep.from_range("risk_off_scale", 0.0, 0.4, 0.1, "Risk-Off Scale"))
        sweeps.append(ParamSweep("mode", ["scale", "filter"], "Skalierungs-Modus"))
        sweeps.append(ParamSweep.from_range("signal_threshold", 0.15, 0.45, 0.05, "Signal Threshold"))

    if include_components:
        # Optional: Variiere Komponenten-Gewichte
        # Hinweis: Dies macht den Sweep sehr groß, daher standardmäßig deaktiviert
        if granularity == "coarse":
            sweeps.append(ParamSweep("breakout_weight", [0.5, 0.6, 0.7], "Breakout Base Weight"))
        elif granularity == "medium":
            sweeps.append(ParamSweep("breakout_weight", [0.4, 0.5, 0.6, 0.7], "Breakout Base Weight"))
        else:
            sweeps.append(ParamSweep.from_range("breakout_weight", 0.3, 0.8, 0.1, "Breakout Base Weight"))

    return sweeps


# ============================================================================
# PRESET A - AGGRESSIVE RISK-ON FOCUS
# ============================================================================

def get_regime_aware_aggressive_sweeps(
    granularity: Granularity = "medium",
) -> List[ParamSweep]:
    """
    Aggressives Preset: Starke Reduktion in Risk-Off, moderate Reduktion in Neutral.

    Portfolio-Komponenten: breakout_basic + rsi_reversion
    Fokus: Maximale Aktivität in Risk-On, reduzierte Aktivität in anderen Regimes.

    Args:
        granularity: Sweep-Granularität

    Returns:
        Liste von ParamSweep-Objekten
    """
    sweeps = []

    if granularity == "coarse":
        # Risk-On: Volle Gewichte
        sweeps.append(ParamSweep("risk_on_scale", [1.0], "Risk-On Scale"))
        # Neutral: Moderate Reduktion
        sweeps.append(ParamSweep("neutral_scale", [0.5, 0.6, 0.7], "Neutral Scale"))
        # Risk-Off: Minimale Aktivität
        sweeps.append(ParamSweep("risk_off_scale", [0.0, 0.1], "Risk-Off Scale"))
        sweeps.append(ParamSweep("mode", ["scale"], "Skalierungs-Modus"))
    elif granularity == "medium":
        sweeps.append(ParamSweep("risk_on_scale", [1.0], "Risk-On Scale"))
        sweeps.append(ParamSweep("neutral_scale", [0.4, 0.5, 0.6, 0.7, 0.8], "Neutral Scale"))
        sweeps.append(ParamSweep("risk_off_scale", [0.0, 0.05, 0.1, 0.15, 0.2], "Risk-Off Scale"))
        sweeps.append(ParamSweep("mode", ["scale"], "Skalierungs-Modus"))
        sweeps.append(ParamSweep("signal_threshold", [0.25, 0.3, 0.35], "Signal Threshold"))
    else:  # fine
        sweeps.append(ParamSweep("risk_on_scale", [1.0], "Risk-On Scale"))
        sweeps.append(ParamSweep.from_range("neutral_scale", 0.4, 0.8, 0.05, "Neutral Scale"))
        sweeps.append(ParamSweep.from_range("risk_off_scale", 0.0, 0.25, 0.05, "Risk-Off Scale"))
        sweeps.append(ParamSweep("mode", ["scale"], "Skalierungs-Modus"))
        sweeps.append(ParamSweep.from_range("signal_threshold", 0.2, 0.4, 0.05, "Signal Threshold"))

    return sweeps


# ============================================================================
# PRESET B - CONSERVATIVE / CAPITAL PRESERVATION
# ============================================================================

def get_regime_aware_conservative_sweeps(
    granularity: Granularity = "medium",
) -> List[ParamSweep]:
    """
    Konservatives Preset: Deutlich reduzierte Allokation in Neutral & Risk-Off.

    Portfolio-Komponenten: breakout_basic + ma_crossover
    Fokus: Kapitalerhalt, strenge Regime-Filterung.

    Args:
        granularity: Sweep-Granularität

    Returns:
        Liste von ParamSweep-Objekten
    """
    sweeps = []

    if granularity == "coarse":
        sweeps.append(ParamSweep("risk_on_scale", [1.0], "Risk-On Scale"))
        # Neutral: Stark reduziert
        sweeps.append(ParamSweep("neutral_scale", [0.2, 0.3, 0.4], "Neutral Scale"))
        # Risk-Off: Komplett aus
        sweeps.append(ParamSweep("risk_off_scale", [0.0], "Risk-Off Scale"))
        sweeps.append(ParamSweep("mode", ["filter"], "Skalierungs-Modus"))
    elif granularity == "medium":
        sweeps.append(ParamSweep("risk_on_scale", [1.0], "Risk-On Scale"))
        sweeps.append(ParamSweep("neutral_scale", [0.2, 0.25, 0.3, 0.35, 0.4], "Neutral Scale"))
        sweeps.append(ParamSweep("risk_off_scale", [0.0], "Risk-Off Scale"))
        sweeps.append(ParamSweep("mode", ["filter"], "Skalierungs-Modus"))
        sweeps.append(ParamSweep("signal_threshold", [0.2, 0.25, 0.3], "Signal Threshold"))
    else:  # fine
        sweeps.append(ParamSweep("risk_on_scale", [1.0], "Risk-On Scale"))
        sweeps.append(ParamSweep.from_range("neutral_scale", 0.1, 0.5, 0.05, "Neutral Scale"))
        sweeps.append(ParamSweep("risk_off_scale", [0.0], "Risk-Off Scale"))
        sweeps.append(ParamSweep("mode", ["filter"], "Skalierungs-Modus"))
        sweeps.append(ParamSweep.from_range("signal_threshold", 0.15, 0.35, 0.05, "Signal Threshold"))

    return sweeps


# ============================================================================
# PRESET C - VOL-METRIC COMPARISON
# ============================================================================

def get_regime_aware_volmetric_sweeps(
    granularity: Granularity = "medium",
) -> List[ParamSweep]:
    """
    Vol-Metrik-Vergleich Preset: Fixes Portfolio, variierende Vol-Metriken.

    Portfolio: breakout_basic + rsi_reversion (fix)
    Fokus: Vergleich verschiedener Vol-Metriken (ATR, STD, REALIZED, RANGE).

    Args:
        granularity: Sweep-Granularität

    Returns:
        Liste von ParamSweep-Objekten
    """
    sweeps = []

    # Portfolio-Parameter fix
    # (könnten auch gesweept werden, aber dann wird es zu groß)

    # Vol-Regime-Parameter
    if granularity == "coarse":
        sweeps.append(ParamSweep("vol_metric", ["atr", "std"], "Volatilitäts-Metrik"))
        sweeps.append(ParamSweep("low_vol_threshold", [0.5], "Low-Vol Threshold"))
        sweeps.append(ParamSweep("high_vol_threshold", [2.0], "High-Vol Threshold"))
    elif granularity == "medium":
        sweeps.append(ParamSweep("vol_metric", ["atr", "std", "realized", "range"], "Volatilitäts-Metrik"))
        sweeps.append(ParamSweep("low_vol_threshold", [0.4, 0.5, 0.6], "Low-Vol Threshold"))
        sweeps.append(ParamSweep("high_vol_threshold", [1.5, 2.0, 2.5], "High-Vol Threshold"))
        sweeps.append(ParamSweep("vol_lookback", [14, 20], "Vol Lookback"))
    else:  # fine
        sweeps.append(ParamSweep("vol_metric", ["atr", "std", "realized", "range"], "Volatilitäts-Metrik"))
        sweeps.append(ParamSweep.from_range("low_vol_threshold", 0.3, 0.7, 0.1, "Low-Vol Threshold"))
        sweeps.append(ParamSweep.from_range("high_vol_threshold", 1.5, 3.0, 0.5, "High-Vol Threshold"))
        sweeps.append(ParamSweep("vol_lookback", [10, 14, 20, 30], "Vol Lookback"))

    return sweeps


# ============================================================================
# COMBINED SWEEPS (Portfolio + Vol-Regime)
# ============================================================================

def get_regime_aware_combined_sweeps(
    granularity: Granularity = "medium",
    preset: str = "aggressive",
) -> List[ParamSweep]:
    """
    Kombiniert Portfolio-Sweeps mit Vol-Regime-Sweeps.

    Args:
        granularity: Sweep-Granularität
        preset: Preset-Name ("aggressive", "conservative", "volmetric")

    Returns:
        Kombinierte Liste von ParamSweep-Objekten
    """
    from .regime_sweeps import get_volatility_detector_sweeps

    # Portfolio-Sweeps basierend auf Preset
    if preset == "aggressive":
        portfolio_sweeps = get_regime_aware_aggressive_sweeps(granularity)
    elif preset == "conservative":
        portfolio_sweeps = get_regime_aware_conservative_sweeps(granularity)
    elif preset == "volmetric":
        portfolio_sweeps = get_regime_aware_volmetric_sweeps(granularity)
    else:
        portfolio_sweeps = get_regime_aware_portfolio_sweeps(granularity)

    # Vol-Regime-Sweeps (nur wenn nicht volmetric preset, da sonst doppelt)
    if preset != "volmetric":
        # Für Vol-Regime nutzen wir Threshold-basierte Sweeps
        vol_sweeps = []
        if granularity == "coarse":
            vol_sweeps.append(ParamSweep("low_vol_threshold", [0.5, 0.8], "Low-Vol Threshold"))
            vol_sweeps.append(ParamSweep("high_vol_threshold", [1.5, 2.0], "High-Vol Threshold"))
        elif granularity == "medium":
            vol_sweeps.append(ParamSweep("low_vol_threshold", [0.4, 0.5, 0.6, 0.8], "Low-Vol Threshold"))
            vol_sweeps.append(ParamSweep("high_vol_threshold", [1.5, 2.0, 2.5], "High-Vol Threshold"))
            vol_sweeps.append(ParamSweep("vol_metric", ["atr", "std"], "Volatilitäts-Metrik"))
        else:
            vol_sweeps.append(ParamSweep.from_range("low_vol_threshold", 0.3, 0.9, 0.1, "Low-Vol Threshold"))
            vol_sweeps.append(ParamSweep.from_range("high_vol_threshold", 1.5, 3.0, 0.5, "High-Vol Threshold"))
            vol_sweeps.append(ParamSweep("vol_metric", ["atr", "std", "realized"], "Volatilitäts-Metrik"))

        return portfolio_sweeps + vol_sweeps

    return portfolio_sweeps


# ============================================================================
# REGISTRY
# ============================================================================

REGIME_AWARE_PORTFOLIO_SWEEP_REGISTRY = {
    "regime_aware_portfolio": get_regime_aware_portfolio_sweeps,
    "regime_aware_aggressive": get_regime_aware_aggressive_sweeps,
    "regime_aware_conservative": get_regime_aware_conservative_sweeps,
    "regime_aware_volmetric": get_regime_aware_volmetric_sweeps,
}


def list_available_regime_aware_sweeps() -> List[str]:
    """
    Gibt Liste aller verfügbaren Regime-Aware Portfolio-Sweeps zurück.

    Returns:
        Sortierte Liste der Sweep-Namen
    """
    return sorted(REGIME_AWARE_PORTFOLIO_SWEEP_REGISTRY.keys())


def get_regime_aware_sweep(
    name: str,
    granularity: Granularity = "medium",
) -> List[ParamSweep]:
    """
    Gibt Sweeps für einen gegebenen Namen zurück.

    Args:
        name: Sweep-Name (aus Registry)
        granularity: Sweep-Granularität

    Returns:
        Liste von ParamSweep-Objekten

    Raises:
        ValueError: Bei unbekanntem Namen
    """
    name_lower = name.lower().replace("-", "_")

    if name_lower in REGIME_AWARE_PORTFOLIO_SWEEP_REGISTRY:
        return REGIME_AWARE_PORTFOLIO_SWEEP_REGISTRY[name_lower](granularity)

    available = ", ".join(sorted(REGIME_AWARE_PORTFOLIO_SWEEP_REGISTRY.keys()))
    raise ValueError(
        f"Unbekannter Regime-Aware Portfolio-Sweep: '{name}'. "
        f"Verfügbar: {available}"
    )


