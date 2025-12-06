# src/regime/switching.py
"""
Peak_Trade Strategy Switching (Phase 28)
========================================

Implementierung von Strategy-Switching-Policies.

Die Switching-Policy entscheidet, welche Strategien bei einem
gegebenen Regime aktiv sein sollen und mit welchen Gewichten.

Verfuegbare Policies:
- SimpleRegimeMappingPolicy: Einfaches Mapping Regime -> Strategien

Factory:
- make_switching_policy(): Erstellt Policy aus Config
"""
from __future__ import annotations

from typing import List, Optional, Dict
import logging

from .base import (
    RegimeLabel,
    StrategySwitchDecision,
    StrategySwitchingPolicy,
)
from .config import StrategySwitchingConfig

logger = logging.getLogger(__name__)


# ============================================================================
# SIMPLE REGIME MAPPING POLICY
# ============================================================================

class SimpleRegimeMappingPolicy:
    """
    Einfache Regime-zu-Strategie-Mapping-Policy.

    Mappt jedes Regime auf eine Liste von Strategien basierend auf
    der Konfiguration. Unterstuetzt optionale Gewichtung.

    Verhalten:
    1. Hole Strategien fuer das aktuelle Regime aus regime_to_strategies
    2. Filtere nur Strategien, die in available_strategies enthalten sind
    3. Falls keine uebrig -> Fallback auf default_strategies
    4. Hole optionale Gewichte und normalisiere sie

    Attributes:
        config: StrategySwitchingConfig

    Example:
        >>> config = StrategySwitchingConfig(
        ...     enabled=True,
        ...     regime_to_strategies={
        ...         "breakout": ["vol_breakout"],
        ...         "ranging": ["mean_reversion_channel", "rsi_reversion"],
        ...     },
        ... )
        >>> policy = SimpleRegimeMappingPolicy(config)
        >>> decision = policy.decide(
        ...     regime="ranging",
        ...     available_strategies=["mean_reversion_channel", "rsi_reversion"],
        ... )
        >>> print(decision.active_strategies)
        ['mean_reversion_channel', 'rsi_reversion']
    """

    def __init__(self, config: StrategySwitchingConfig) -> None:
        self.config = config

    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Normalisiert Gewichte auf Summe = 1.0.

        Args:
            weights: Dict {Strategy -> Weight}

        Returns:
            Normalisierte Gewichte
        """
        total = sum(weights.values())
        if total <= 0:
            # Gleichverteilung
            n = len(weights)
            return {k: 1.0 / n for k in weights} if n > 0 else {}

        return {k: v / total for k, v in weights.items()}

    def _filter_available_strategies(
        self,
        desired_strategies: List[str],
        available_strategies: List[str],
    ) -> List[str]:
        """
        Filtert gewuenschte Strategien auf verfuegbare.

        Args:
            desired_strategies: Gewuenschte Strategien aus Config
            available_strategies: Tatsaechlich verfuegbare Strategien

        Returns:
            Gefilterte Liste (nur verfuegbare Strategien)
        """
        available_set = set(available_strategies)
        filtered = [s for s in desired_strategies if s in available_set]

        if len(filtered) < len(desired_strategies):
            missing = set(desired_strategies) - available_set
            logger.debug(
                f"Einige gemappte Strategien sind nicht verfuegbar: {missing}"
            )

        return filtered

    def decide(
        self,
        regime: RegimeLabel,
        available_strategies: List[str],
    ) -> StrategySwitchDecision:
        """
        Entscheidet, welche Strategien fuer ein Regime aktiv sein sollen.

        Args:
            regime: Aktuelles Regime-Label
            available_strategies: Liste aller verfuegbaren Strategy-Namen

        Returns:
            StrategySwitchDecision mit aktiven Strategien und Gewichten
        """
        # 1. Hole gewuenschte Strategien fuer dieses Regime
        desired_strategies = self.config.get_strategies_for_regime(regime)

        # 2. Filtere nur verfuegbare Strategien
        active_strategies = self._filter_available_strategies(
            desired_strategies, available_strategies
        )

        # 3. Fallback wenn keine Strategie uebrig
        if not active_strategies:
            logger.debug(
                f"Keine Strategien fuer Regime '{regime}' verfuegbar, "
                f"nutze default_strategies"
            )
            default_strategies = self.config.default_strategies or []
            active_strategies = self._filter_available_strategies(
                default_strategies, available_strategies
            )

            # Letzter Fallback: Alle verfuegbaren Strategien
            if not active_strategies and available_strategies:
                logger.warning(
                    f"Auch default_strategies nicht verfuegbar, "
                    f"nutze alle verfuegbaren Strategien"
                )
                active_strategies = list(available_strategies)

        # 4. Hole und normalisiere Gewichte
        raw_weights = self.config.get_weights_for_regime(regime)
        weights: Optional[Dict[str, float]] = None

        if raw_weights:
            # Filtere Gewichte auf aktive Strategien
            filtered_weights = {
                s: raw_weights.get(s, 0.0)
                for s in active_strategies
                if s in raw_weights or raw_weights.get(s, 0.0) > 0
            }

            # Falls keine Gewichte fuer aktive Strategien, nutze Gleichverteilung
            if not filtered_weights:
                filtered_weights = {s: 1.0 for s in active_strategies}

            weights = self._normalize_weights(filtered_weights)

        # 5. Decision erstellen
        decision = StrategySwitchDecision(
            regime=regime,
            active_strategies=active_strategies,
            weights=weights,
            metadata={
                "policy": "simple_regime_mapping",
                "original_desired": desired_strategies,
                "fallback_used": len(active_strategies) < len(desired_strategies),
            },
        )

        logger.debug(
            f"Regime '{regime}' -> Strategien: {active_strategies}, "
            f"Gewichte: {weights}"
        )

        return decision


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def make_switching_policy(
    config: StrategySwitchingConfig,
) -> Optional[StrategySwitchingPolicy]:
    """
    Factory-Funktion: Erstellt eine StrategySwitchingPolicy aus Config.

    Args:
        config: StrategySwitchingConfig

    Returns:
        StrategySwitchingPolicy-Instanz oder None (wenn disabled)

    Raises:
        ValueError: Bei unbekanntem policy_name

    Example:
        >>> config = StrategySwitchingConfig(enabled=True)
        >>> policy = make_switching_policy(config)
        >>> if policy:
        ...     decision = policy.decide("breakout", ["vol_breakout"])
    """
    if not config.enabled:
        logger.debug("Strategy Switching ist deaktiviert (enabled=false)")
        return None

    policy_name = config.policy_name.lower()

    if policy_name in ("simple_regime_mapping", "simple", "mapping"):
        logger.info("Erstelle SimpleRegimeMappingPolicy")
        return SimpleRegimeMappingPolicy(config)

    else:
        raise ValueError(
            f"Unbekannte Switching-Policy: '{config.policy_name}'. "
            f"Verfuegbar: 'simple_regime_mapping'"
        )
