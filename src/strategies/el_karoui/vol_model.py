# src/strategies/el_karoui/vol_model.py
"""
El Karoui Volatilitäts-Modell – Research-Only
=============================================

Implementiert ein Volatilitäts-Regime-Modell inspiriert von Nicole El Karouis
Arbeiten zu stochastischen Volatilitätsmodellen.

⚠️ WICHTIG: RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

Konzepte:
- Realized-Volatility-Schätzung (rolling std / EWM)
- Vol-Regime-Klassifikation: LOW / MEDIUM / HIGH
- Vol-Target und Scaling-Faktoren für Position-Sizing

Die Mathematik in v1 ist pragmatisch (rolling std). Das Interface ist
so gestaltet, dass später komplexere El-Karoui-Ideen (stochastische Vol,
Forward-Vol, Volatilitäts-Surfaces) integriert werden können.

Warnung:
- Volatilitätsschätzung ist inhärent unsicher (Schätzfehler, Strukturbrüche)
- Regime-Wechsel können schnell erfolgen und schwer zu timen sein
- Nutze dieses Modell nur für explorative Analysen
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Union

import numpy as np
import pandas as pd


# =============================================================================
# VOL REGIME ENUM
# =============================================================================


class VolRegime(Enum):
    """
    Volatilitäts-Regime nach El Karoui Vol Model.

    Die Klassifikation basiert auf der Position der aktuellen Volatilität
    relativ zu historischen Perzentilen:
    - LOW: Volatilität im unteren Bereich (< low_threshold)
    - MEDIUM: Volatilität im mittleren Bereich
    - HIGH: Volatilität im oberen Bereich (> high_threshold)

    Attributes:
        value: Kurzbezeichnung des Regimes
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    def __str__(self) -> str:
        return self.value


# =============================================================================
# EL KAROUI VOL CONFIG
# =============================================================================


@dataclass
class ElKarouiVolConfig:
    """
    Konfiguration für das El Karoui Volatilitäts-Modell.

    Attributes:
        vol_window: Fensterlänge für Realized-Vol-Berechnung (Anzahl Perioden)
        lookback_window: Fenster für Perzentil-Berechnung (für Regime-Klassifikation)
        low_threshold: Perzentil-Schwelle für LOW-Regime (z.B. 0.30 = 30. Perzentil)
        high_threshold: Perzentil-Schwelle für HIGH-Regime (z.B. 0.70 = 70. Perzentil)
        use_ewm: Ob exponentiell gewichtete Volatilität verwendet wird
        annualization_factor: Faktor für Annualisierung (252 für täglich, 365*24 für stündlich)
        vol_target: Ziel-Volatilität p.a. für Scaling (z.B. 0.10 = 10%)
        smoothing_periods: Anzahl Perioden für Glättung der Vol-Schätzung (0 = keine)

    Example:
        >>> config = ElKarouiVolConfig(
        ...     vol_window=20,
        ...     low_threshold=0.30,
        ...     high_threshold=0.70,
        ... )
    """

    vol_window: int = 20
    lookback_window: int = 252  # 1 Jahr für Perzentil-Berechnung
    low_threshold: float = 0.30
    high_threshold: float = 0.70
    use_ewm: bool = True
    annualization_factor: float = 252.0
    vol_target: float = 0.10  # 10% p.a. Ziel-Volatilität
    smoothing_periods: int = 5

    # Risk-Multiplier pro Regime (für Position-Sizing)
    regime_multipliers: Dict[str, float] = field(
        default_factory=lambda: {
            "low": 1.0,      # Volles Exposure bei niedriger Vol
            "medium": 0.75,  # Reduziertes Exposure bei mittlerer Vol
            "high": 0.50,    # Stark reduziertes Exposure bei hoher Vol
        }
    )

    def __post_init__(self) -> None:
        """Validierung nach Initialisierung."""
        if self.vol_window < 2:
            raise ValueError(
                f"vol_window ({self.vol_window}) muss >= 2 sein"
            )
        if self.lookback_window < self.vol_window:
            raise ValueError(
                f"lookback_window ({self.lookback_window}) muss >= vol_window ({self.vol_window}) sein"
            )
        if not 0 < self.low_threshold < 1:
            raise ValueError(
                f"low_threshold ({self.low_threshold}) muss zwischen 0 und 1 sein"
            )
        if not 0 < self.high_threshold < 1:
            raise ValueError(
                f"high_threshold ({self.high_threshold}) muss zwischen 0 und 1 sein"
            )
        if self.low_threshold >= self.high_threshold:
            raise ValueError(
                f"low_threshold ({self.low_threshold}) muss < high_threshold ({self.high_threshold}) sein"
            )
        if self.vol_target <= 0:
            raise ValueError(
                f"vol_target ({self.vol_target}) muss > 0 sein"
            )

    @classmethod
    def default(cls) -> "ElKarouiVolConfig":
        """
        Erstellt eine Standardkonfiguration.

        Returns:
            ElKarouiVolConfig mit Default-Werten
        """
        return cls()

    @classmethod
    def conservative(cls) -> "ElKarouiVolConfig":
        """
        Erstellt eine konservative Konfiguration (engere Schwellen).

        Returns:
            ElKarouiVolConfig mit konservativen Werten
        """
        return cls(
            vol_window=20,
            low_threshold=0.25,
            high_threshold=0.60,
            vol_target=0.08,  # 8% p.a.
            regime_multipliers={
                "low": 1.0,
                "medium": 0.60,
                "high": 0.30,
            },
        )

    @classmethod
    def aggressive(cls) -> "ElKarouiVolConfig":
        """
        Erstellt eine aggressive Konfiguration (weitere Schwellen).

        Returns:
            ElKarouiVolConfig mit aggressiven Werten
        """
        return cls(
            vol_window=20,
            low_threshold=0.35,
            high_threshold=0.80,
            vol_target=0.15,  # 15% p.a.
            regime_multipliers={
                "low": 1.0,
                "medium": 0.85,
                "high": 0.65,
            },
        )

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "vol_window": self.vol_window,
            "lookback_window": self.lookback_window,
            "low_threshold": self.low_threshold,
            "high_threshold": self.high_threshold,
            "use_ewm": self.use_ewm,
            "annualization_factor": self.annualization_factor,
            "vol_target": self.vol_target,
            "smoothing_periods": self.smoothing_periods,
            "regime_multipliers": self.regime_multipliers,
        }


# =============================================================================
# EL KAROUI VOL MODEL
# =============================================================================


class ElKarouiVolModel:
    """
    El Karoui Volatilitäts-Modell.

    ⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

    Dieses Modell schätzt die realisierte Volatilität und klassifiziert
    das aktuelle Vol-Regime (LOW / MEDIUM / HIGH).

    Features:
    - Realized-Vol-Schätzung (rolling std oder EWM)
    - Regime-Klassifikation basierend auf Perzentilen
    - Vol-Target-Scaling für Position-Sizing
    - Risk-Multiplier pro Regime

    Attributes:
        config: ElKarouiVolConfig mit Modell-Parametern

    Example:
        >>> model = ElKarouiVolModel.from_default()
        >>> # Returns als Input (log oder simple returns)
        >>> returns = prices.pct_change().dropna()
        >>> regime = model.regime_for_returns(returns)
        >>> print(f"Aktuelles Regime: {regime}")
        Aktuelles Regime: medium

        >>> multiplier = model.scaling_factor_for_returns(returns)
        >>> print(f"Scaling-Faktor: {multiplier:.2f}")
        Scaling-Faktor: 0.85
    """

    def __init__(self, config: ElKarouiVolConfig) -> None:
        """
        Initialisiert das Volatilitäts-Modell.

        Args:
            config: Konfiguration für das Modell
        """
        self.config = config

    @classmethod
    def from_default(cls) -> "ElKarouiVolModel":
        """
        Erstellt ein Modell mit Standardkonfiguration.

        Returns:
            ElKarouiVolModel mit Default-Config
        """
        return cls(ElKarouiVolConfig.default())

    @classmethod
    def from_config_dict(cls, config_dict: Dict[str, Any]) -> "ElKarouiVolModel":
        """
        Erstellt ein Modell aus einem Config-Dictionary.

        Args:
            config_dict: Dictionary mit Konfiguration

        Returns:
            ElKarouiVolModel-Instanz
        """
        config = ElKarouiVolConfig(
            vol_window=config_dict.get("vol_window", 20),
            lookback_window=config_dict.get("lookback_window", 252),
            low_threshold=config_dict.get("low_threshold", 0.30),
            high_threshold=config_dict.get("high_threshold", 0.70),
            use_ewm=config_dict.get("use_ewm", True),
            annualization_factor=config_dict.get("annualization_factor", 252.0),
            vol_target=config_dict.get("vol_target", 0.10),
            smoothing_periods=config_dict.get("smoothing_periods", 5),
        )

        if "regime_multipliers" in config_dict:
            config.regime_multipliers = config_dict["regime_multipliers"]

        return cls(config)

    def calculate_realized_vol(
        self,
        returns: pd.Series,
        annualize: bool = True,
    ) -> pd.Series:
        """
        Berechnet die realisierte Volatilität.

        Args:
            returns: Series mit Returns (log oder simple)
            annualize: Ob die Volatilität annualisiert werden soll

        Returns:
            Series mit realisierter Volatilität

        Example:
            >>> model = ElKarouiVolModel.from_default()
            >>> vol = model.calculate_realized_vol(returns)
        """
        window = self.config.vol_window
        smoothing = self.config.smoothing_periods

        # Volatilität schätzen
        if self.config.use_ewm:
            vol = returns.ewm(span=window, min_periods=window).std()
        else:
            vol = returns.rolling(window=window, min_periods=window).std()

        # Optional: Glättung
        if smoothing > 1:
            vol = vol.rolling(window=smoothing, min_periods=1).mean()

        # Annualisierung
        if annualize:
            vol = vol * np.sqrt(self.config.annualization_factor)

        return vol

    def calculate_vol_percentile(
        self,
        vol_series: pd.Series,
    ) -> pd.Series:
        """
        Berechnet die Perzentil-Position der Volatilität.

        Args:
            vol_series: Series mit Volatilitätswerten

        Returns:
            Series mit Perzentil-Werten (0.0 - 1.0)

        Example:
            >>> percentiles = model.calculate_vol_percentile(vol_series)
        """
        lookback = self.config.lookback_window

        def percentile_rank(x: pd.Series) -> float:
            """Berechnet den Perzentil-Rang des letzten Werts."""
            if len(x) < 2 or pd.isna(x.iloc[-1]):
                return np.nan
            current = x.iloc[-1]
            return (x < current).mean()

        percentiles = vol_series.rolling(
            window=lookback,
            min_periods=self.config.vol_window,
        ).apply(percentile_rank, raw=False)

        return percentiles

    def regime_for_percentile(self, percentile: float) -> VolRegime:
        """
        Bestimmt das Regime für einen gegebenen Perzentil-Wert.

        Args:
            percentile: Perzentil-Wert (0.0 - 1.0)

        Returns:
            VolRegime (LOW, MEDIUM, HIGH)

        Example:
            >>> regime = model.regime_for_percentile(0.25)
            >>> print(regime)
            low
        """
        if pd.isna(percentile):
            return VolRegime.MEDIUM  # Default bei fehlenden Daten

        if percentile < self.config.low_threshold:
            return VolRegime.LOW
        elif percentile > self.config.high_threshold:
            return VolRegime.HIGH
        else:
            return VolRegime.MEDIUM

    def regime_for_returns(
        self,
        returns: pd.Series,
    ) -> VolRegime:
        """
        Bestimmt das aktuelle Vol-Regime für eine Return-Serie.

        Args:
            returns: Series mit Returns

        Returns:
            Aktuelles VolRegime (LOW, MEDIUM, HIGH)

        Example:
            >>> regime = model.regime_for_returns(returns)
            >>> print(f"Aktuelles Regime: {regime}")
        """
        if len(returns) < self.config.vol_window:
            return VolRegime.MEDIUM  # Default bei zu wenig Daten

        vol = self.calculate_realized_vol(returns)
        percentiles = self.calculate_vol_percentile(vol)

        current_percentile = percentiles.iloc[-1]
        return self.regime_for_percentile(current_percentile)

    def regime_series(
        self,
        returns: pd.Series,
    ) -> pd.Series:
        """
        Berechnet das Vol-Regime für jeden Zeitpunkt.

        Args:
            returns: Series mit Returns

        Returns:
            Series mit VolRegime-Werten

        Example:
            >>> regimes = model.regime_series(returns)
            >>> print(regimes.value_counts())
        """
        vol = self.calculate_realized_vol(returns)
        percentiles = self.calculate_vol_percentile(vol)

        regimes = percentiles.apply(
            lambda x: self.regime_for_percentile(x).value
        )

        return regimes

    def multiplier_for_regime(self, regime: VolRegime) -> float:
        """
        Gibt den Risk-Multiplier für ein Regime zurück.

        Args:
            regime: VolRegime

        Returns:
            Risk-Multiplier (0.0 - 1.0)

        Example:
            >>> mult = model.multiplier_for_regime(VolRegime.HIGH)
            >>> print(f"Multiplier: {mult}")
            Multiplier: 0.5
        """
        return self.config.regime_multipliers.get(regime.value, 0.75)

    def scaling_factor_for_returns(
        self,
        returns: pd.Series,
    ) -> float:
        """
        Berechnet den Scaling-Faktor für Position-Sizing.

        Der Scaling-Faktor kombiniert:
        1. Regime-Multiplier (basierend auf Vol-Regime)
        2. Vol-Target-Scaling (aktuelle Vol vs. Ziel-Vol)

        Args:
            returns: Series mit Returns

        Returns:
            Scaling-Faktor für Position-Sizing

        Example:
            >>> factor = model.scaling_factor_for_returns(returns)
            >>> position_size = base_position * factor
        """
        if len(returns) < self.config.vol_window:
            return 0.5  # Konservativer Default

        # Aktuelles Regime und Multiplier
        regime = self.regime_for_returns(returns)
        regime_mult = self.multiplier_for_regime(regime)

        # Vol-Target-Scaling: vol_target / current_vol (gecapped)
        vol = self.calculate_realized_vol(returns)
        current_vol = vol.iloc[-1]

        if pd.isna(current_vol) or current_vol <= 0:
            vol_scale = 1.0
        else:
            vol_scale = self.config.vol_target / current_vol
            # Cap bei 0.2 bis 2.0 um extreme Werte zu vermeiden
            vol_scale = max(0.2, min(2.0, vol_scale))

        # Kombinierter Faktor
        return regime_mult * vol_scale

    def scaling_factor_series(
        self,
        returns: pd.Series,
    ) -> pd.Series:
        """
        Berechnet den Scaling-Faktor für jeden Zeitpunkt.

        Args:
            returns: Series mit Returns

        Returns:
            Series mit Scaling-Faktoren

        Example:
            >>> factors = model.scaling_factor_series(returns)
        """
        vol = self.calculate_realized_vol(returns)
        percentiles = self.calculate_vol_percentile(vol)

        def calc_scaling(row_idx: int) -> float:
            """Berechnet Scaling für einen Zeitpunkt."""
            if row_idx < self.config.vol_window:
                return 0.5

            pct = percentiles.iloc[row_idx]
            regime = self.regime_for_percentile(pct)
            regime_mult = self.multiplier_for_regime(regime)

            current_vol = vol.iloc[row_idx]
            if pd.isna(current_vol) or current_vol <= 0:
                vol_scale = 1.0
            else:
                vol_scale = self.config.vol_target / current_vol
                vol_scale = max(0.2, min(2.0, vol_scale))

            return regime_mult * vol_scale

        scaling = pd.Series(
            [calc_scaling(i) for i in range(len(returns))],
            index=returns.index,
        )

        return scaling

    def get_vol_analysis(
        self,
        returns: pd.Series,
    ) -> Dict[str, Any]:
        """
        Gibt eine umfassende Volatilitätsanalyse zurück.

        Args:
            returns: Series mit Returns

        Returns:
            Dict mit:
            - current_vol: Aktuelle annualisierte Volatilität
            - vol_percentile: Perzentil der aktuellen Volatilität
            - regime: Aktuelles Vol-Regime
            - regime_multiplier: Multiplier für das Regime
            - scaling_factor: Kombinierter Scaling-Faktor
            - vol_target: Konfigurierte Ziel-Volatilität
            - vol_history: Historische Volatilität (Series)

        Example:
            >>> analysis = model.get_vol_analysis(returns)
            >>> print(f"Regime: {analysis['regime']}, Vol: {analysis['current_vol']:.1%}")
        """
        if len(returns) < self.config.vol_window:
            return {
                "current_vol": None,
                "vol_percentile": None,
                "regime": VolRegime.MEDIUM,
                "regime_multiplier": self.multiplier_for_regime(VolRegime.MEDIUM),
                "scaling_factor": 0.5,
                "vol_target": self.config.vol_target,
                "vol_history": None,
            }

        vol = self.calculate_realized_vol(returns)
        percentiles = self.calculate_vol_percentile(vol)

        current_vol = vol.iloc[-1]
        current_pct = percentiles.iloc[-1]
        regime = self.regime_for_percentile(current_pct)
        regime_mult = self.multiplier_for_regime(regime)
        scaling = self.scaling_factor_for_returns(returns)

        return {
            "current_vol": current_vol,
            "vol_percentile": current_pct,
            "regime": regime,
            "regime_multiplier": regime_mult,
            "scaling_factor": scaling,
            "vol_target": self.config.vol_target,
            "vol_history": vol,
        }

    def __repr__(self) -> str:
        return (
            f"<ElKarouiVolModel("
            f"window={self.config.vol_window}, "
            f"thresholds=[{self.config.low_threshold:.2f}, {self.config.high_threshold:.2f}], "
            f"target={self.config.vol_target:.0%}) "
            f"[RESEARCH-ONLY]>"
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def get_vol_regime(
    returns: pd.Series,
    vol_window: int = 20,
    low_threshold: float = 0.30,
    high_threshold: float = 0.70,
) -> VolRegime:
    """
    Convenience-Funktion: Bestimmt das Vol-Regime für Returns.

    Args:
        returns: Series mit Returns
        vol_window: Fenster für Vol-Berechnung
        low_threshold: Schwelle für LOW-Regime
        high_threshold: Schwelle für HIGH-Regime

    Returns:
        VolRegime

    Example:
        >>> regime = get_vol_regime(returns)
        >>> print(regime)
        medium
    """
    config = ElKarouiVolConfig(
        vol_window=vol_window,
        low_threshold=low_threshold,
        high_threshold=high_threshold,
    )
    model = ElKarouiVolModel(config)
    return model.regime_for_returns(returns)


def get_vol_scaling_factor(
    returns: pd.Series,
    vol_window: int = 20,
    vol_target: float = 0.10,
) -> float:
    """
    Convenience-Funktion: Berechnet den Vol-Scaling-Faktor.

    Args:
        returns: Series mit Returns
        vol_window: Fenster für Vol-Berechnung
        vol_target: Ziel-Volatilität p.a.

    Returns:
        Scaling-Faktor für Position-Sizing

    Example:
        >>> factor = get_vol_scaling_factor(returns)
        >>> position = base_position * factor
    """
    config = ElKarouiVolConfig(
        vol_window=vol_window,
        vol_target=vol_target,
    )
    model = ElKarouiVolModel(config)
    return model.scaling_factor_for_returns(returns)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enum
    "VolRegime",
    # Config
    "ElKarouiVolConfig",
    # Model
    "ElKarouiVolModel",
    # Convenience Functions
    "get_vol_regime",
    "get_vol_scaling_factor",
]



