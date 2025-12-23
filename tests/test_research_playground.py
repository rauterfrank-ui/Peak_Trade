# tests/test_research_playground.py
"""
Tests für Research Playground (Phase 41)
=========================================

Testet:
- StrategySweepConfig mit Constraints
- Predefined Sweeps Registry
- Parameter-Kombinations-Generierung
- Sweep-Batch-Execution (synthetisch)
"""

from __future__ import annotations

import pytest
import pandas as pd
import numpy as np
from typing import Any, Dict, List

from src.experiments.research_playground import (
    StrategySweepConfig,
    ParamConstraint,
    get_predefined_sweep,
    list_predefined_sweeps,
    get_all_predefined_sweeps,
    get_sweeps_for_strategy,
    get_sweeps_by_tag,
    create_custom_sweep,
    print_sweep_catalog,
)


# =============================================================================
# ParamConstraint Tests
# =============================================================================


class TestParamConstraint:
    """Tests für ParamConstraint."""

    def test_less_than_constraint(self):
        """Test für '<' Constraint."""
        c = ParamConstraint("fast", "<", "slow")

        # Valide: fast < slow
        assert c.evaluate({"fast": 5, "slow": 10}) is True
        assert c.evaluate({"fast": 1, "slow": 100}) is True

        # Invalide: fast >= slow
        assert c.evaluate({"fast": 10, "slow": 5}) is False
        assert c.evaluate({"fast": 10, "slow": 10}) is False

    def test_greater_than_constraint(self):
        """Test für '>' Constraint."""
        c = ParamConstraint("high", ">", "low")

        assert c.evaluate({"high": 80, "low": 20}) is True
        assert c.evaluate({"high": 20, "low": 80}) is False

    def test_less_equal_constraint(self):
        """Test für '<=' Constraint."""
        c = ParamConstraint("exit", "<=", "entry")

        assert c.evaluate({"exit": 10, "entry": 20}) is True
        assert c.evaluate({"exit": 20, "entry": 20}) is True
        assert c.evaluate({"exit": 30, "entry": 20}) is False

    def test_greater_equal_constraint(self):
        """Test für '>=' Constraint."""
        c = ParamConstraint("min_val", ">=", 5)

        assert c.evaluate({"min_val": 5}) is True
        assert c.evaluate({"min_val": 10}) is True
        assert c.evaluate({"min_val": 3}) is False

    def test_equal_constraint(self):
        """Test für '==' Constraint."""
        c = ParamConstraint("method", "==", "atr")

        assert c.evaluate({"method": "atr"}) is True
        assert c.evaluate({"method": "std"}) is False

    def test_not_equal_constraint(self):
        """Test für '!=' Constraint."""
        c = ParamConstraint("side", "!=", "short")

        assert c.evaluate({"side": "long"}) is True
        assert c.evaluate({"side": "both"}) is True
        assert c.evaluate({"side": "short"}) is False

    def test_constraint_with_literal_value(self):
        """Constraint mit literalem Wert statt Parameter-Referenz."""
        c = ParamConstraint("period", ">=", 5)

        assert c.evaluate({"period": 10}) is True
        assert c.evaluate({"period": 5}) is True
        assert c.evaluate({"period": 3}) is False

    def test_constraint_missing_param_returns_true(self):
        """Fehlender Parameter = keine Einschränkung."""
        c = ParamConstraint("missing", "<", 10)

        assert c.evaluate({"other": 5}) is True


# =============================================================================
# StrategySweepConfig Tests
# =============================================================================


class TestStrategySweepConfig:
    """Tests für StrategySweepConfig."""

    def test_basic_sweep_config(self):
        """Einfache Sweep-Konfiguration."""
        sweep = StrategySweepConfig(
            name="test_sweep",
            strategy_name="ma_crossover",
            param_grid={"fast": [5, 10], "slow": [50, 100]},
        )

        assert sweep.name == "test_sweep"
        assert sweep.strategy_name == "ma_crossover"
        assert sweep.num_raw_combinations == 4

    def test_sweep_with_constraints(self):
        """Sweep mit Constraints filtert ungültige Kombinationen."""
        sweep = StrategySweepConfig(
            name="constrained_sweep",
            strategy_name="ma_crossover",
            param_grid={
                "fast": [5, 10, 20, 50],
                "slow": [10, 20, 50, 100],
            },
            constraints=[("fast", "<", "slow")],
        )

        # Ohne Constraint: 4 * 4 = 16 Kombinationen
        assert sweep.num_raw_combinations == 16

        # Mit Constraint: nur Kombinationen wo fast < slow
        combos = sweep.generate_param_combinations()
        valid_count = sweep.num_combinations

        # Prüfe dass alle Kombinationen das Constraint erfüllen
        for combo in combos:
            assert combo["fast"] < combo["slow"]

        # Sollte weniger als 16 sein
        assert valid_count < sweep.num_raw_combinations

    def test_sweep_tuple_constraints(self):
        """Constraints können als Tupel übergeben werden."""
        sweep = StrategySweepConfig(
            name="tuple_constraint",
            strategy_name="rsi",
            param_grid={
                "oversold": [20, 30, 40],
                "overbought": [60, 70, 80],
            },
            constraints=[("oversold", "<", "overbought")],  # Tuple Format
        )

        combos = sweep.generate_param_combinations()
        for combo in combos:
            assert combo["oversold"] < combo["overbought"]

    def test_sweep_base_params(self):
        """Base params werden in alle Kombinationen gemerged."""
        sweep = StrategySweepConfig(
            name="with_base_params",
            strategy_name="breakout",
            param_grid={"lookback": [20, 50]},
            base_params={"side": "long", "stop_loss_pct": 0.02},
        )

        combos = sweep.generate_param_combinations()
        assert len(combos) == 2

        for combo in combos:
            assert combo["side"] == "long"
            assert combo["stop_loss_pct"] == 0.02
            assert combo["lookback"] in [20, 50]

    def test_sweep_empty_grid(self):
        """Leeres Grid = 1 Kombination mit nur base_params."""
        sweep = StrategySweepConfig(
            name="empty_grid",
            strategy_name="test",
            param_grid={},
            base_params={"fixed_param": 42},
        )

        combos = sweep.generate_param_combinations()
        assert len(combos) == 1
        assert combos[0] == {"fixed_param": 42}

    def test_sweep_to_dict(self):
        """to_dict() Serialisierung."""
        sweep = StrategySweepConfig(
            name="dict_test",
            strategy_name="ma_crossover",
            param_grid={"fast": [5, 10], "slow": [50, 100]},
            constraints=[("fast", "<", "slow")],
            description="Test sweep",
            tags=["test", "unit"],
        )

        d = sweep.to_dict()
        assert d["name"] == "dict_test"
        assert d["strategy_name"] == "ma_crossover"
        assert d["param_grid"] == {"fast": [5, 10], "slow": [50, 100]}
        assert d["description"] == "Test sweep"
        assert "test" in d["tags"]

    def test_sweep_validation_empty_name(self):
        """Leerer Name wirft ValueError."""
        with pytest.raises(ValueError, match="name darf nicht leer"):
            StrategySweepConfig(
                name="",
                strategy_name="test",
            )

    def test_sweep_validation_empty_strategy(self):
        """Leere Strategie wirft ValueError."""
        with pytest.raises(ValueError, match="strategy_name darf nicht leer"):
            StrategySweepConfig(
                name="test",
                strategy_name="",
            )

    def test_to_experiment_config(self):
        """Konvertierung zu ExperimentConfig."""
        sweep = StrategySweepConfig(
            name="exp_config_test",
            strategy_name="rsi_reversion",
            param_grid={"period": [7, 14]},
            symbols=["ETH/EUR"],
            timeframe="4h",
        )

        exp_config = sweep.to_experiment_config(
            start_date="2024-01-01",
            end_date="2024-06-01",
            initial_capital=5000.0,
        )

        assert exp_config.name == "exp_config_test"
        assert exp_config.strategy_name == "rsi_reversion"
        assert exp_config.symbols == ["ETH/EUR"]
        assert exp_config.timeframe == "4h"
        assert exp_config.start_date == "2024-01-01"
        assert exp_config.initial_capital == 5000.0


# =============================================================================
# Predefined Sweeps Registry Tests
# =============================================================================


class TestPredefinedSweeps:
    """Tests für vordefinierte Sweeps."""

    def test_list_predefined_sweeps(self):
        """list_predefined_sweeps() gibt Namen zurück."""
        names = list_predefined_sweeps()

        assert isinstance(names, list)
        assert len(names) > 0
        assert all(isinstance(n, str) for n in names)

        # Bekannte Sweeps sollten existieren
        assert "ma_crossover_basic" in names
        assert "rsi_reversion_basic" in names
        assert "breakout_basic" in names

    def test_get_predefined_sweep(self):
        """get_predefined_sweep() lädt Sweep korrekt."""
        sweep = get_predefined_sweep("ma_crossover_basic")

        assert sweep.name == "ma_crossover_basic"
        assert sweep.strategy_name == "ma_crossover"
        assert "fast_period" in sweep.param_grid or "fast_period" in str(sweep.param_grid.keys())

    def test_get_predefined_sweep_not_found(self):
        """get_predefined_sweep() wirft KeyError für unbekannte Namen."""
        with pytest.raises(KeyError, match="nicht gefunden"):
            get_predefined_sweep("nonexistent_sweep")

    def test_get_all_predefined_sweeps(self):
        """get_all_predefined_sweeps() gibt Dict zurück."""
        all_sweeps = get_all_predefined_sweeps()

        assert isinstance(all_sweeps, dict)
        assert len(all_sweeps) > 0

        for name, sweep in all_sweeps.items():
            assert isinstance(name, str)
            assert isinstance(sweep, StrategySweepConfig)
            assert sweep.name == name

    def test_get_sweeps_for_strategy(self):
        """get_sweeps_for_strategy() filtert nach Strategie."""
        ma_sweeps = get_sweeps_for_strategy("ma_crossover")

        assert len(ma_sweeps) >= 2  # basic + fine
        for sweep in ma_sweeps:
            assert sweep.strategy_name == "ma_crossover"

    def test_get_sweeps_by_tag(self):
        """get_sweeps_by_tag() filtert nach Tag."""
        basic_sweeps = get_sweeps_by_tag("basic")

        assert len(basic_sweeps) > 0
        for sweep in basic_sweeps:
            assert "basic" in sweep.tags

    def test_predefined_sweep_constraints_work(self):
        """Vordefinierte Sweeps mit Constraints filtern korrekt."""
        # MA Crossover hat fast < slow Constraint
        sweep = get_predefined_sweep("ma_crossover_basic")
        combos = sweep.generate_param_combinations()

        # Alle Kombinationen müssen Constraint erfüllen
        for combo in combos:
            if "fast_period" in combo and "slow_period" in combo:
                assert combo["fast_period"] < combo["slow_period"]

    def test_all_predefined_sweeps_have_valid_combinations(self):
        """Alle vordefinierten Sweeps erzeugen mindestens 1 gültige Kombination."""
        all_sweeps = get_all_predefined_sweeps()

        for name, sweep in all_sweeps.items():
            combos = sweep.generate_param_combinations()
            assert len(combos) >= 1, f"Sweep '{name}' hat keine gültigen Kombinationen"


# =============================================================================
# Helper Functions Tests
# =============================================================================


class TestHelperFunctions:
    """Tests für Helper-Funktionen."""

    def test_create_custom_sweep(self):
        """create_custom_sweep() Convenience-Funktion."""
        sweep = create_custom_sweep(
            name="custom_test",
            strategy_name="bollinger",
            param_grid={"period": [10, 20], "num_std": [1.5, 2.0, 2.5]},
            description="Custom Test Sweep",
        )

        assert sweep.name == "custom_test"
        assert sweep.strategy_name == "bollinger"
        assert sweep.num_combinations == 6
        assert sweep.description == "Custom Test Sweep"

    def test_create_custom_sweep_with_constraints(self):
        """create_custom_sweep() mit Constraints."""
        sweep = create_custom_sweep(
            name="constrained_custom",
            strategy_name="ma_crossover",
            param_grid={"fast": [5, 20], "slow": [10, 50]},
            constraints=[("fast", "<", "slow")],
        )

        # 2x2 = 4 raw, aber nur 3 valide (5<10, 5<50, 20<50, NOT 20<10)
        assert sweep.num_raw_combinations == 4
        assert sweep.num_combinations == 3

    def test_print_sweep_catalog(self):
        """print_sweep_catalog() gibt formatierten String zurück."""
        catalog = print_sweep_catalog()

        assert isinstance(catalog, str)
        assert "Strategy Sweep Catalog" in catalog
        assert "Phase 41" in catalog
        assert "ma_crossover" in catalog.lower()
        assert "rsi" in catalog.lower()


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integrations-Tests für komplexere Szenarien."""

    def test_rsi_sweep_constraint_validation(self):
        """RSI Sweep: oversold < overbought wird korrekt gefiltert."""
        sweep = get_predefined_sweep("rsi_reversion_basic")

        combos = sweep.generate_param_combinations()

        for combo in combos:
            if "oversold_level" in combo and "overbought_level" in combo:
                assert (
                    combo["oversold_level"] < combo["overbought_level"]
                ), f"Ungültige Kombination: {combo}"

    def test_breakout_sweep_has_sl_params(self):
        """Breakout Sweeps enthalten Stop-Loss Parameter."""
        sweep = get_predefined_sweep("breakout_basic")

        assert "lookback_breakout" in sweep.param_grid
        assert "stop_loss_pct" in sweep.param_grid

    def test_portfolio_sweep_exists(self):
        """Portfolio-Sweeps existieren."""
        names = list_predefined_sweeps()

        portfolio_sweeps = [n for n in names if "portfolio" in n.lower()]
        assert len(portfolio_sweeps) >= 1

        # Prüfe einen Portfolio-Sweep
        if portfolio_sweeps:
            sweep = get_predefined_sweep(portfolio_sweeps[0])
            assert sweep.strategy_name == "composite"
            assert sweep.portfolio_config is not None

    def test_constraint_chain(self):
        """Mehrere Constraints werden alle angewendet."""
        sweep = StrategySweepConfig(
            name="multi_constraint",
            strategy_name="test",
            param_grid={
                "a": [1, 5, 10],
                "b": [5, 10, 15],
                "c": [10, 15, 20],
            },
            constraints=[
                ("a", "<", "b"),
                ("b", "<", "c"),
            ],
        )

        combos = sweep.generate_param_combinations()

        # Alle Kombinationen müssen beide Constraints erfüllen
        for combo in combos:
            assert combo["a"] < combo["b"], f"a < b verletzt: {combo}"
            assert combo["b"] < combo["c"], f"b < c verletzt: {combo}"

        # Prüfe dass tatsächlich gefiltert wurde
        assert sweep.num_combinations < sweep.num_raw_combinations

    def test_sweep_symbols_and_timeframe(self):
        """Symbols und Timeframe werden korrekt gesetzt."""
        sweep = StrategySweepConfig(
            name="multi_symbol",
            strategy_name="ma_crossover",
            param_grid={"fast": [5, 10]},
            symbols=["BTC/EUR", "ETH/EUR", "SOL/EUR"],
            timeframe="4h",
        )

        assert sweep.symbols == ["BTC/EUR", "ETH/EUR", "SOL/EUR"]
        assert sweep.timeframe == "4h"

        exp_config = sweep.to_experiment_config()
        assert exp_config.symbols == ["BTC/EUR", "ETH/EUR", "SOL/EUR"]
        assert exp_config.timeframe == "4h"
