# tests/ops/test_parameter_schema_verification.py
"""
P0: Deterministic verification tests for parameter/schema contracts.

No network, no external tools. Asserts that:
- validate_schema() accepts empty list and valid schemas; rejects duplicate names.
- extract_defaults() returns dict name -> default from schema.
- Param kinds (int, float, choice, bool) enforce bounds/choices/defaults.
"""

from __future__ import annotations

import pytest

from src.strategies.parameters import (
    Param,
    validate_schema,
    extract_defaults,
)


class TestValidateSchemaContract:
    """validate_schema() contract: empty OK, valid OK, duplicate names raise."""

    def test_empty_schema_ok(self) -> None:
        """Empty list does not raise."""
        validate_schema([])

    def test_valid_schema_ok(self) -> None:
        """Valid schema (int + float) does not raise."""
        schema = [
            Param(name="window", kind="int", default=20, low=5, high=50),
            Param(name="threshold", kind="float", default=0.02, low=0.01, high=0.1),
        ]
        validate_schema(schema)

    def test_duplicate_names_raise(self) -> None:
        """Duplicate parameter names raise ValueError."""
        schema = [
            Param(name="x", kind="int", default=10, low=0, high=20),
            Param(name="x", kind="float", default=0.5, low=0.0, high=1.0),
        ]
        with pytest.raises(ValueError, match="Duplicate parameter name"):
            validate_schema(schema)


class TestExtractDefaultsContract:
    """extract_defaults() returns name -> default dict."""

    def test_empty_returns_empty_dict(self) -> None:
        """Empty schema yields {}."""
        assert extract_defaults([]) == {}

    def test_single_param(self) -> None:
        """Single param yields one entry."""
        schema = [Param(name="window", kind="int", default=20, low=5, high=50)]
        assert extract_defaults(schema) == {"window": 20}

    def test_multiple_params(self) -> None:
        """Multiple params yield all defaults."""
        schema = [
            Param(name="a", kind="int", default=1, low=0, high=10),
            Param(name="b", kind="float", default=0.5, low=0.0, high=1.0),
            Param(name="c", kind="choice", default="x", choices=["x", "y"]),
            Param(name="d", kind="bool", default=True),
        ]
        assert extract_defaults(schema) == {"a": 1, "b": 0.5, "c": "x", "d": True}


class TestParamKindContracts:
    """Param per-kind validation (int/float need bounds; choice needs choices; bool needs bool default)."""

    def test_int_missing_bounds_raises(self) -> None:
        """Int without low/high raises."""
        with pytest.raises(ValueError, match="low und high"):
            Param(name="w", kind="int", default=20)

    def test_choice_missing_choices_raises(self) -> None:
        """Choice without choices raises."""
        with pytest.raises(ValueError, match="choices"):
            Param(name="m", kind="choice", default="fast")

    def test_bool_non_bool_default_raises(self) -> None:
        """Bool with non-bool default raises."""
        with pytest.raises(ValueError, match="default muss bool"):
            Param(name="f", kind="bool", default="true")
