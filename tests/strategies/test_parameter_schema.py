"""
Tests für Parameter Schema
===========================
Testet Param dataclass + Validation.
"""

import pytest

from src.strategies.parameters import Param, validate_schema, extract_defaults


class TestParamBasics:
    """Tests für Param dataclass."""

    def test_param_int(self):
        """Param (int): Validierung funktioniert."""
        param = Param(name="window", kind="int", default=20, low=5, high=50)

        assert param.name == "window"
        assert param.kind == "int"
        assert param.default == 20
        assert param.low == 5
        assert param.high == 50

    def test_param_float(self):
        """Param (float): Validierung funktioniert."""
        param = Param(name="threshold", kind="float", default=0.02, low=0.01, high=0.1)

        assert param.validate_value(0.05) is True
        assert param.validate_value(0.001) is False  # Zu klein
        assert param.validate_value(0.2) is False  # Zu groß

    def test_param_choice(self):
        """Param (choice): Validierung funktioniert."""
        param = Param(name="mode", kind="choice", default="fast", choices=["fast", "slow"])

        assert param.validate_value("fast") is True
        assert param.validate_value("slow") is True
        assert param.validate_value("medium") is False  # Nicht in choices

    def test_param_bool(self):
        """Param (bool): Validierung funktioniert."""
        param = Param(name="use_filter", kind="bool", default=True)

        assert param.validate_value(True) is True
        assert param.validate_value(False) is True
        assert param.validate_value("true") is False  # Nicht bool


class TestParamValidation:
    """Tests für Param-Validierung."""

    def test_int_missing_bounds(self):
        """Int-Param ohne low/high: ValueError."""
        with pytest.raises(ValueError, match="low und high müssen gesetzt sein"):
            Param(name="window", kind="int", default=20)

    def test_int_invalid_bounds(self):
        """Int-Param mit low >= high: ValueError."""
        with pytest.raises(ValueError, match="low .* muss < high"):
            Param(name="window", kind="int", default=20, low=50, high=10)

    def test_choice_missing_choices(self):
        """Choice-Param ohne choices: ValueError."""
        with pytest.raises(ValueError, match="choices müssen gesetzt sein"):
            Param(name="mode", kind="choice", default="fast")

    def test_choice_default_not_in_choices(self):
        """Choice-Param mit ungültigem default: ValueError."""
        with pytest.raises(ValueError, match="default .* nicht in choices"):
            Param(name="mode", kind="choice", default="medium", choices=["fast", "slow"])

    def test_bool_invalid_default(self):
        """Bool-Param mit nicht-bool default: ValueError."""
        with pytest.raises(ValueError, match="default muss bool sein"):
            Param(name="use_filter", kind="bool", default="true")


class TestValidateSchema:
    """Tests für validate_schema()."""

    def test_empty_schema(self):
        """Leeres Schema ist OK."""
        validate_schema([])  # Sollte nicht werfen

    def test_valid_schema(self):
        """Valides Schema."""
        schema = [
            Param(name="window", kind="int", default=20, low=5, high=50),
            Param(name="threshold", kind="float", default=0.02, low=0.01, high=0.1),
        ]
        validate_schema(schema)  # Sollte nicht werfen

    def test_duplicate_names(self):
        """Doppelte Namen: ValueError."""
        schema = [
            Param(name="window", kind="int", default=20, low=5, high=50),
            Param(name="window", kind="int", default=30, low=10, high=60),  # Duplikat
        ]
        with pytest.raises(ValueError, match="Duplicate parameter name"):
            validate_schema(schema)


class TestExtractDefaults:
    """Tests für extract_defaults()."""

    def test_extract_defaults(self):
        """extract_defaults(): Extrahiert Default-Werte."""
        schema = [
            Param(name="window", kind="int", default=20, low=5, high=50),
            Param(name="threshold", kind="float", default=0.02, low=0.01, high=0.1),
            Param(name="mode", kind="choice", default="fast", choices=["fast", "slow"]),
        ]

        defaults = extract_defaults(schema)

        assert defaults == {"window": 20, "threshold": 0.02, "mode": "fast"}

    def test_extract_defaults_empty(self):
        """extract_defaults(): Leeres Schema → leerer Dict."""
        assert extract_defaults([]) == {}


@pytest.mark.skip(reason="Strategies don't have parameter_schema yet - deferred to Phase 2")
class TestStrategiesWithSchema:
    """Tests für Strategien mit parameter_schema (TODO: Phase 2)."""

    def test_ma_crossover_has_schema(self):
        """MA Crossover: Hat parameter_schema."""
        from src.strategies.ma_crossover import MACrossoverStrategy

        strategy = MACrossoverStrategy()
        schema = getattr(strategy, "parameter_schema", None)

        assert schema is not None, "Strategy should have parameter_schema"
        assert len(schema) > 0
        assert any(p.name == "fast_window" for p in schema)
        assert any(p.name == "slow_window" for p in schema)

    def test_rsi_reversion_has_schema(self):
        """RSI Reversion: Hat parameter_schema."""
        from src.strategies.rsi_reversion import RsiReversionStrategy

        strategy = RsiReversionStrategy()
        schema = getattr(strategy, "parameter_schema", None)

        assert schema is not None, "Strategy should have parameter_schema"
        assert len(schema) > 0
        assert any(p.name == "rsi_window" for p in schema)

    def test_donchian_breakout_has_schema(self):
        """Donchian Breakout: Hat parameter_schema."""
        from src.strategies.breakout_donchian import DonchianBreakoutStrategy

        strategy = DonchianBreakoutStrategy()
        schema = getattr(strategy, "parameter_schema", None)

        assert schema is not None, "Strategy should have parameter_schema"
        assert len(schema) > 0
        assert any(p.name == "lookback" for p in schema)
