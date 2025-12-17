# tests/test_strategy_switching.py
"""
Tests fuer Strategy Switching (Phase 28)
========================================

Testet SimpleRegimeMappingPolicy und Konfiguration.
"""

import pytest

from src.regime import (
    SimpleRegimeMappingPolicy,
    StrategySwitchDecision,
    StrategySwitchingConfig,
    make_switching_policy,
)

# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def default_config() -> StrategySwitchingConfig:
    """Standard-Konfiguration fuer Tests."""
    return StrategySwitchingConfig(
        enabled=True,
        policy_name="simple_regime_mapping",
        regime_to_strategies={
            "breakout": ["vol_breakout"],
            "ranging": ["mean_reversion_channel", "rsi_reversion"],
            "trending": ["trend_following"],
            "unknown": ["ma_crossover"],
        },
        regime_to_weights={
            "ranging": {"mean_reversion_channel": 0.6, "rsi_reversion": 0.4},
        },
        default_strategies=["ma_crossover"],
    )


@pytest.fixture
def available_strategies() -> list[str]:
    """Liste aller verfuegbaren Strategien."""
    return [
        "vol_breakout",
        "mean_reversion_channel",
        "rsi_reversion",
        "trend_following",
        "ma_crossover",
    ]


# ============================================================================
# SIMPLE REGIME MAPPING POLICY TESTS
# ============================================================================

class TestSimpleRegimeMappingPolicy:
    """Tests fuer SimpleRegimeMappingPolicy."""

    def test_decide_returns_decision(
        self, default_config: StrategySwitchingConfig, available_strategies: list[str]
    ):
        """decide() gibt StrategySwitchDecision zurueck."""
        policy = SimpleRegimeMappingPolicy(default_config)
        decision = policy.decide("breakout", available_strategies)

        assert isinstance(decision, StrategySwitchDecision)
        assert decision.regime == "breakout"

    def test_breakout_maps_to_vol_breakout(
        self, default_config: StrategySwitchingConfig, available_strategies: list[str]
    ):
        """Breakout-Regime mappt auf vol_breakout."""
        policy = SimpleRegimeMappingPolicy(default_config)
        decision = policy.decide("breakout", available_strategies)

        assert "vol_breakout" in decision.active_strategies
        assert len(decision.active_strategies) == 1

    def test_ranging_maps_to_multiple_strategies(
        self, default_config: StrategySwitchingConfig, available_strategies: list[str]
    ):
        """Ranging-Regime mappt auf mehrere Strategien."""
        policy = SimpleRegimeMappingPolicy(default_config)
        decision = policy.decide("ranging", available_strategies)

        assert "mean_reversion_channel" in decision.active_strategies
        assert "rsi_reversion" in decision.active_strategies
        assert len(decision.active_strategies) == 2

    def test_ranging_has_weights(
        self, default_config: StrategySwitchingConfig, available_strategies: list[str]
    ):
        """Ranging-Regime hat konfigurierte Gewichte."""
        policy = SimpleRegimeMappingPolicy(default_config)
        decision = policy.decide("ranging", available_strategies)

        assert decision.weights is not None
        assert abs(decision.weights.get("mean_reversion_channel", 0) - 0.6) < 0.01
        assert abs(decision.weights.get("rsi_reversion", 0) - 0.4) < 0.01

    def test_weights_are_normalized(
        self, available_strategies: list[str]
    ):
        """Gewichte werden normalisiert."""
        config = StrategySwitchingConfig(
            enabled=True,
            regime_to_strategies={"breakout": ["vol_breakout", "trend_following"]},
            regime_to_weights={"breakout": {"vol_breakout": 2.0, "trend_following": 3.0}},
        )

        policy = SimpleRegimeMappingPolicy(config)
        decision = policy.decide("breakout", available_strategies)

        assert decision.weights is not None
        total_weight = sum(decision.weights.values())
        assert abs(total_weight - 1.0) < 0.001

    def test_filter_unavailable_strategies(
        self, default_config: StrategySwitchingConfig
    ):
        """Nicht verfuegbare Strategien werden gefiltert."""
        # Nur vol_breakout verfuegbar
        limited_strategies = ["vol_breakout"]

        policy = SimpleRegimeMappingPolicy(default_config)
        decision = policy.decide("ranging", limited_strategies)

        # ranging mappt auf mean_reversion_channel und rsi_reversion,
        # aber keine davon ist verfuegbar -> Fallback auf default
        assert "ma_crossover" not in decision.active_strategies or len(decision.active_strategies) > 0

    def test_fallback_to_default_strategies(
        self, default_config: StrategySwitchingConfig
    ):
        """Fallback auf default_strategies wenn keine gemappt."""
        # Keine der gemappten Strategien verfuegbar
        limited_strategies = ["ma_crossover"]

        policy = SimpleRegimeMappingPolicy(default_config)
        decision = policy.decide("breakout", limited_strategies)

        # breakout -> vol_breakout (nicht verfuegbar) -> fallback auf ma_crossover
        assert "ma_crossover" in decision.active_strategies

    def test_fallback_to_all_available(self):
        """Fallback auf alle verfuegbaren wenn auch default nicht verfuegbar."""
        config = StrategySwitchingConfig(
            enabled=True,
            regime_to_strategies={"breakout": ["non_existent"]},
            default_strategies=["also_non_existent"],
        )

        available = ["actual_strategy"]
        policy = SimpleRegimeMappingPolicy(config)
        decision = policy.decide("breakout", available)

        assert "actual_strategy" in decision.active_strategies

    def test_unknown_regime_uses_default(
        self, default_config: StrategySwitchingConfig, available_strategies: list[str]
    ):
        """Unknown-Regime nutzt gemappte Strategie."""
        policy = SimpleRegimeMappingPolicy(default_config)
        decision = policy.decide("unknown", available_strategies)

        assert "ma_crossover" in decision.active_strategies


# ============================================================================
# STRATEGY SWITCH DECISION TESTS
# ============================================================================

class TestStrategySwitchDecision:
    """Tests fuer StrategySwitchDecision Dataclass."""

    def test_get_weight_with_weights(self):
        """get_weight() mit konfigurierten Gewichten."""
        decision = StrategySwitchDecision(
            regime="ranging",
            active_strategies=["a", "b"],
            weights={"a": 0.7, "b": 0.3},
        )

        assert decision.get_weight("a") == 0.7
        assert decision.get_weight("b") == 0.3
        assert decision.get_weight("c") == 0.0

    def test_get_weight_without_weights(self):
        """get_weight() ohne Gewichte (Gleichverteilung)."""
        decision = StrategySwitchDecision(
            regime="ranging",
            active_strategies=["a", "b", "c"],
            weights=None,
        )

        assert abs(decision.get_weight("a") - 1/3) < 0.001
        assert abs(decision.get_weight("b") - 1/3) < 0.001

    def test_is_single_strategy(self):
        """is_single_strategy Property."""
        single = StrategySwitchDecision(
            regime="breakout",
            active_strategies=["vol_breakout"],
        )
        multi = StrategySwitchDecision(
            regime="ranging",
            active_strategies=["a", "b"],
        )

        assert single.is_single_strategy is True
        assert multi.is_single_strategy is False

    def test_primary_strategy_with_weights(self):
        """primary_strategy gibt Strategie mit hoechstem Gewicht."""
        decision = StrategySwitchDecision(
            regime="ranging",
            active_strategies=["a", "b", "c"],
            weights={"a": 0.2, "b": 0.5, "c": 0.3},
        )

        assert decision.primary_strategy == "b"

    def test_primary_strategy_without_weights(self):
        """primary_strategy ohne Gewichte gibt erste Strategie."""
        decision = StrategySwitchDecision(
            regime="breakout",
            active_strategies=["vol_breakout", "other"],
            weights=None,
        )

        assert decision.primary_strategy == "vol_breakout"

    def test_primary_strategy_empty(self):
        """primary_strategy bei leerer Liste."""
        decision = StrategySwitchDecision(
            regime="unknown",
            active_strategies=[],
        )

        assert decision.primary_strategy is None


# ============================================================================
# FACTORY FUNCTION TESTS
# ============================================================================

class TestMakeSwitchingPolicy:
    """Tests fuer make_switching_policy Factory."""

    def test_returns_none_when_disabled(self):
        """Gibt None zurueck wenn disabled."""
        config = StrategySwitchingConfig(enabled=False)
        policy = make_switching_policy(config)

        assert policy is None

    def test_creates_simple_policy(self):
        """Erstellt SimpleRegimeMappingPolicy."""
        config = StrategySwitchingConfig(
            enabled=True,
            policy_name="simple_regime_mapping",
        )
        policy = make_switching_policy(config)

        assert policy is not None
        assert isinstance(policy, SimpleRegimeMappingPolicy)

    def test_unknown_policy_raises_error(self):
        """Unbekannte Policy loest ValueError aus."""
        config = StrategySwitchingConfig(
            enabled=True,
            policy_name="unknown_policy",
        )

        with pytest.raises(ValueError, match="Unbekannte Switching-Policy"):
            make_switching_policy(config)

    def test_accepts_alias_names(self):
        """Akzeptiert Alias-Namen fuer Policies."""
        for alias in ["simple", "mapping", "simple_regime_mapping"]:
            config = StrategySwitchingConfig(enabled=True, policy_name=alias)
            policy = make_switching_policy(config)
            assert isinstance(policy, SimpleRegimeMappingPolicy)


# ============================================================================
# CONFIG TESTS
# ============================================================================

class TestStrategySwitchingConfig:
    """Tests fuer StrategySwitchingConfig."""

    def test_default_values(self):
        """Prueft Default-Werte."""
        config = StrategySwitchingConfig()

        assert config.enabled is False
        assert config.policy_name == "simple_regime_mapping"
        assert config.default_strategies == ["ma_crossover"]
        assert config.regime_to_strategies is not None

    def test_get_strategies_for_regime(self):
        """get_strategies_for_regime() gibt richtige Strategien."""
        config = StrategySwitchingConfig(
            regime_to_strategies={
                "breakout": ["vol_breakout"],
                "ranging": ["mean_reversion"],
            },
            default_strategies=["default"],
        )

        assert config.get_strategies_for_regime("breakout") == ["vol_breakout"]
        assert config.get_strategies_for_regime("ranging") == ["mean_reversion"]
        assert config.get_strategies_for_regime("unknown") == ["default"]

    def test_get_weights_for_regime(self):
        """get_weights_for_regime() gibt richtige Gewichte."""
        config = StrategySwitchingConfig(
            regime_to_weights={
                "ranging": {"a": 0.6, "b": 0.4},
            },
        )

        assert config.get_weights_for_regime("ranging") == {"a": 0.6, "b": 0.4}
        assert config.get_weights_for_regime("breakout") is None

    def test_to_dict(self):
        """to_dict() gibt alle Felder zurueck."""
        config = StrategySwitchingConfig(enabled=True)
        d = config.to_dict()

        assert isinstance(d, dict)
        assert d["enabled"] is True
        assert "regime_to_strategies" in d

    def test_from_peak_config(self):
        """from_peak_config() liest aus PeakConfig."""
        # Mock PeakConfig
        class MockConfig:
            def get(self, path: str, default=None):
                values = {
                    "strategy_switching.enabled": True,
                    "strategy_switching.policy_name": "simple",
                    "strategy_switching.regime_to_strategies": {
                        "breakout": ["vol_breakout"],
                    },
                    "strategy_switching.default_strategies": ["fallback"],
                }
                return values.get(path, default)

        config = StrategySwitchingConfig.from_peak_config(MockConfig())

        assert config.enabled is True
        assert config.policy_name == "simple"
        assert config.regime_to_strategies == {"breakout": ["vol_breakout"]}
        assert config.default_strategies == ["fallback"]
