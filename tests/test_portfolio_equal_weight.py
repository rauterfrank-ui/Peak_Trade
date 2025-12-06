# tests/test_portfolio_equal_weight.py
"""
Tests für EqualWeightPortfolioStrategy (Phase 26)
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.portfolio import (
    EqualWeightPortfolioStrategy,
    PortfolioConfig,
    PortfolioContext,
)


@pytest.fixture
def basic_config():
    """Basis-Config für Equal-Weight."""
    return PortfolioConfig(
        enabled=True,
        name="equal_weight",
        max_single_weight=0.5,
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


class TestEqualWeightPortfolioStrategy:
    """Tests für Equal-Weight-Strategie."""

    def test_equal_weight_three_symbols(self, basic_config, basic_context):
        """Test: 3 Symbole → je ~33%."""
        strategy = EqualWeightPortfolioStrategy(basic_config)
        weights = strategy.generate_target_weights(basic_context)

        assert len(weights) == 3
        assert "BTC/EUR" in weights
        assert "ETH/EUR" in weights
        assert "LTC/EUR" in weights

        # Jedes Symbol sollte ~1/3 bekommen
        for symbol, weight in weights.items():
            assert abs(weight - 1/3) < 0.01, f"{symbol} weight {weight} != 1/3"

        # Summe sollte 1.0 sein
        assert abs(sum(weights.values()) - 1.0) < 0.001

    def test_equal_weight_two_symbols(self, basic_config):
        """Test: 2 Symbole → je 50%."""
        context = PortfolioContext(
            timestamp=pd.Timestamp("2024-01-01"),
            symbols=["BTC/EUR", "ETH/EUR"],
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
            current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0},
            equity=10000.0,
        )

        strategy = EqualWeightPortfolioStrategy(basic_config)
        weights = strategy.generate_target_weights(context)

        assert len(weights) == 2
        for weight in weights.values():
            assert abs(weight - 0.5) < 0.001

    def test_equal_weight_single_symbol(self, basic_config):
        """Test: 1 Symbol → 100%."""
        context = PortfolioContext(
            timestamp=pd.Timestamp("2024-01-01"),
            symbols=["BTC/EUR"],
            prices={"BTC/EUR": 50000.0},
            current_positions={"BTC/EUR": 0.0},
            equity=10000.0,
        )

        strategy = EqualWeightPortfolioStrategy(basic_config)
        weights = strategy.generate_target_weights(context)

        # Wird durch max_single_weight auf 0.5 gecappt
        assert len(weights) == 1
        assert weights["BTC/EUR"] == 1.0  # Nach Normalisierung

    def test_equal_weight_empty_universe(self, basic_config):
        """Test: Leeres Universe → leere Gewichte."""
        context = PortfolioContext(
            timestamp=pd.Timestamp("2024-01-01"),
            symbols=[],
            prices={},
            current_positions={},
            equity=10000.0,
        )

        strategy = EqualWeightPortfolioStrategy(basic_config)
        weights = strategy.generate_target_weights(context)

        assert weights == {}

    def test_equal_weight_with_config_universe(self, basic_context):
        """Test: Config-Universe hat Priorität."""
        config = PortfolioConfig(
            enabled=True,
            name="equal_weight",
            symbols=["BTC/EUR", "ETH/EUR"],  # Nur 2 von 3 Symbolen
        )

        strategy = EqualWeightPortfolioStrategy(config)
        weights = strategy.generate_target_weights(basic_context)

        # Nur die 2 Config-Symbole sollten Gewichte bekommen
        assert len(weights) == 2
        assert "LTC/EUR" not in weights

    def test_equal_weight_max_weight_constraint(self):
        """Test: max_single_weight Constraint wird angewendet."""
        config = PortfolioConfig(
            enabled=True,
            name="equal_weight",
            max_single_weight=0.25,  # Max 25% pro Symbol
        )

        context = PortfolioContext(
            timestamp=pd.Timestamp("2024-01-01"),
            symbols=["BTC/EUR", "ETH/EUR"],  # 2 Symbole = je 50%
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
            current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0},
            equity=10000.0,
        )

        strategy = EqualWeightPortfolioStrategy(config)
        weights = strategy.generate_target_weights(context)

        # Nach Normalisierung sollten beide wieder 50% haben
        # (da beide auf 25% gecappt und dann normalisiert werden)
        for weight in weights.values():
            assert abs(weight - 0.5) < 0.01

    def test_strategy_repr(self, basic_config):
        """Test: String-Repräsentation."""
        strategy = EqualWeightPortfolioStrategy(basic_config)
        repr_str = repr(strategy)

        assert "EqualWeightPortfolioStrategy" in repr_str
        assert "enabled=True" in repr_str
