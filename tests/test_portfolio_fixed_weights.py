# tests/test_portfolio_fixed_weights.py
"""
Tests für FixedWeightsPortfolioStrategy (Phase 26)
"""

import pytest
import pandas as pd
import numpy as np

from src.portfolio import (
    FixedWeightsPortfolioStrategy,
    PortfolioConfig,
    PortfolioContext,
)


@pytest.fixture
def fixed_weights_config():
    """Config mit festen Gewichten."""
    return PortfolioConfig(
        enabled=True,
        name="fixed_weights",
        fixed_weights={
            "BTC/EUR": 0.5,
            "ETH/EUR": 0.3,
            "LTC/EUR": 0.2,
        },
        max_single_weight=0.6,
        min_weight=0.01,
        normalize_weights=True,
    )


@pytest.fixture
def basic_context():
    """Basis-Context mit 3 Symbolen."""
    return PortfolioContext(
        timestamp=pd.Timestamp("2024-01-01"),
        symbols=["BTC/EUR", "ETH/EUR", "LTC/EUR"],
        prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0, "LTC/EUR": 100.0},
        current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0, "LTC/EUR": 0.0},
        equity=10000.0,
    )


class TestFixedWeightsPortfolioStrategy:
    """Tests für Fixed-Weights-Strategie."""

    def test_fixed_weights_basic(self, fixed_weights_config, basic_context):
        """Test: Feste Gewichte werden korrekt angewendet."""
        strategy = FixedWeightsPortfolioStrategy(fixed_weights_config)
        weights = strategy.generate_target_weights(basic_context)

        assert len(weights) == 3
        assert abs(weights["BTC/EUR"] - 0.5) < 0.01
        assert abs(weights["ETH/EUR"] - 0.3) < 0.01
        assert abs(weights["LTC/EUR"] - 0.2) < 0.01

        # Summe sollte 1.0 sein
        assert abs(sum(weights.values()) - 1.0) < 0.001

    def test_fixed_weights_partial_universe(self, fixed_weights_config):
        """Test: Nur Symbole im Context bekommen Gewichte."""
        context = PortfolioContext(
            timestamp=pd.Timestamp("2024-01-01"),
            symbols=["BTC/EUR", "ETH/EUR"],  # Ohne LTC/EUR
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
            current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0},
            equity=10000.0,
        )

        strategy = FixedWeightsPortfolioStrategy(fixed_weights_config)
        weights = strategy.generate_target_weights(context)

        # Nur 2 Symbole, normalisiert
        assert len(weights) == 2
        assert "LTC/EUR" not in weights

        # Original: BTC=0.5, ETH=0.3 → Sum=0.8 → normalisiert
        expected_btc = 0.5 / 0.8  # ~0.625
        expected_eth = 0.3 / 0.8  # ~0.375

        assert abs(weights["BTC/EUR"] - expected_btc) < 0.01
        assert abs(weights["ETH/EUR"] - expected_eth) < 0.01

    def test_fixed_weights_symbol_not_in_config(self):
        """Test: Symbol im Context aber nicht in Config → ignoriert."""
        config = PortfolioConfig(
            enabled=True,
            name="fixed_weights",
            fixed_weights={
                "BTC/EUR": 0.6,
                "ETH/EUR": 0.4,
            },
        )

        context = PortfolioContext(
            timestamp=pd.Timestamp("2024-01-01"),
            symbols=["BTC/EUR", "ETH/EUR", "LTC/EUR"],  # LTC nicht in Config
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0, "LTC/EUR": 100.0},
            current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0, "LTC/EUR": 0.0},
            equity=10000.0,
        )

        strategy = FixedWeightsPortfolioStrategy(config)
        weights = strategy.generate_target_weights(context)

        assert len(weights) == 2
        assert "LTC/EUR" not in weights

    def test_fixed_weights_normalization(self):
        """Test: Gewichte werden auf Summe 1.0 normalisiert."""
        config = PortfolioConfig(
            enabled=True,
            name="fixed_weights",
            fixed_weights={
                "BTC/EUR": 0.3,  # Summe = 0.6 (nicht 1.0)
                "ETH/EUR": 0.3,
            },
            normalize_weights=True,
        )

        context = PortfolioContext(
            timestamp=pd.Timestamp("2024-01-01"),
            symbols=["BTC/EUR", "ETH/EUR"],
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
            current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0},
            equity=10000.0,
        )

        strategy = FixedWeightsPortfolioStrategy(config)
        weights = strategy.generate_target_weights(context)

        # Nach Normalisierung: je 50%
        assert abs(weights["BTC/EUR"] - 0.5) < 0.01
        assert abs(weights["ETH/EUR"] - 0.5) < 0.01

    def test_fixed_weights_empty_config_fallback(self):
        """Test: Leere fixed_weights → Fallback auf Equal-Weight."""
        config = PortfolioConfig(
            enabled=True,
            name="fixed_weights",
            fixed_weights=None,  # Keine Gewichte definiert
        )

        context = PortfolioContext(
            timestamp=pd.Timestamp("2024-01-01"),
            symbols=["BTC/EUR", "ETH/EUR"],
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
            current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0},
            equity=10000.0,
        )

        strategy = FixedWeightsPortfolioStrategy(config)
        weights = strategy.generate_target_weights(context)

        # Fallback auf Equal-Weight → je 50%
        assert len(weights) == 2
        for weight in weights.values():
            assert abs(weight - 0.5) < 0.01

    def test_fixed_weights_max_constraint(self):
        """Test: max_single_weight wird angewendet."""
        config = PortfolioConfig(
            enabled=True,
            name="fixed_weights",
            fixed_weights={
                "BTC/EUR": 0.8,  # > max_single_weight
                "ETH/EUR": 0.2,
            },
            max_single_weight=0.6,  # Max 60%
        )

        context = PortfolioContext(
            timestamp=pd.Timestamp("2024-01-01"),
            symbols=["BTC/EUR", "ETH/EUR"],
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
            current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0},
            equity=10000.0,
        )

        strategy = FixedWeightsPortfolioStrategy(config)
        weights = strategy.generate_target_weights(context)

        # BTC wird auf 0.6 gecappt, dann normalisiert
        # Original nach Cap: BTC=0.6, ETH=0.2 → Sum=0.8
        # Nach Normalisierung: BTC=0.6/0.8=0.75, ETH=0.2/0.8=0.25
        assert weights["BTC/EUR"] <= 1.0
        assert weights["ETH/EUR"] <= 1.0
