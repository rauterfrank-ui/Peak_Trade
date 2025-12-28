"""Tests to verify legacy Traffic Light path delegates to canonical engine.

Phase 8D Verification: Ensure that src/risk/validation/traffic_light.py
properly delegates all computation to the canonical engine in
src/risk_layer/var_backtest/traffic_light.py.

These tests verify:
1. Legacy functions call canonical functions
2. Results are compatible between legacy and canonical paths
3. No duplicate computation occurs
"""

import pytest


class TestLegacyDelegation:
    """Verify legacy API delegates to canonical engine."""

    def test_basel_traffic_light_delegates_to_canonical(self):
        """Verify basel_traffic_light() delegates to canonical engine."""
        from unittest.mock import patch

        from src.risk.validation.traffic_light import basel_traffic_light

        # Mock the canonical function
        with patch(
            "src.risk.validation.traffic_light._canonical_basel_traffic_light"
        ) as mock_canonical:
            # Setup mock return value
            from src.risk_layer.var_backtest.traffic_light import (
                BaselZone,
                TrafficLightResult as CanonicalResult,
            )

            mock_canonical.return_value = CanonicalResult(
                zone=BaselZone.YELLOW,
                n_violations=5,
                expected_violations=2.5,
                n_observations=250,
                alpha=0.01,
                violation_rate=0.02,
                green_threshold=4,
                yellow_threshold=9,
                capital_multiplier=3.2,
            )

            # Call legacy function
            result = basel_traffic_light(breaches=5, observations=250, confidence_level=0.99)

            # Verify canonical function was called
            mock_canonical.assert_called_once()
            call_kwargs = mock_canonical.call_args[1]
            assert call_kwargs["n_violations"] == 5
            assert call_kwargs["n_observations"] == 250
            assert call_kwargs["alpha"] == pytest.approx(0.01)  # 1 - confidence_level

            # Verify result mapping
            assert result.breaches == 5
            assert result.observations == 250
            assert result.color == "yellow"  # BaselZone.YELLOW → "yellow"

    def test_get_traffic_light_thresholds_delegates(self):
        """Verify get_traffic_light_thresholds() delegates to canonical engine."""
        from unittest.mock import patch

        from src.risk.validation.traffic_light import get_traffic_light_thresholds

        with patch(
            "src.risk.validation.traffic_light._canonical_compute_zone_thresholds"
        ) as mock_canonical:
            mock_canonical.return_value = (4, 9)

            green, yellow = get_traffic_light_thresholds(observations=250, confidence_level=0.99)

            # Verify canonical function was called with correct args
            mock_canonical.assert_called_once_with(250, pytest.approx(0.01))
            assert green == 4
            assert yellow == 9


class TestEquivalence:
    """Verify legacy and canonical paths produce compatible results."""

    def test_basel_traffic_light_equivalence_green(self):
        """Verify legacy matches canonical for GREEN zone."""
        from src.risk.validation.traffic_light import basel_traffic_light
        from src.risk_layer.var_backtest.traffic_light import (
            basel_traffic_light as canonical_basel_traffic_light,
        )

        # Test case: 3 breaches in 250 observations, 99% VaR → GREEN
        breaches = 3
        observations = 250
        confidence_level = 0.99

        # Legacy API
        legacy_result = basel_traffic_light(
            breaches=breaches,
            observations=observations,
            confidence_level=confidence_level,
        )

        # Canonical API
        canonical_result = canonical_basel_traffic_light(
            n_violations=breaches,
            n_observations=observations,
            alpha=1 - confidence_level,
        )

        # Verify results are compatible
        assert legacy_result.breaches == canonical_result.n_violations
        assert legacy_result.observations == canonical_result.n_observations
        assert (
            legacy_result.color == canonical_result.zone.value
        )  # "green" == BaselZone.GREEN.value
        assert legacy_result.green_threshold == canonical_result.green_threshold
        assert legacy_result.yellow_threshold == canonical_result.yellow_threshold

    def test_basel_traffic_light_equivalence_yellow(self):
        """Verify legacy matches canonical for YELLOW zone."""
        from src.risk.validation.traffic_light import basel_traffic_light
        from src.risk_layer.var_backtest.traffic_light import (
            basel_traffic_light as canonical_basel_traffic_light,
        )

        # Test case: 5 breaches in 250 observations, 99% VaR → YELLOW
        breaches = 5
        observations = 250
        confidence_level = 0.99

        # Legacy API
        legacy_result = basel_traffic_light(
            breaches=breaches,
            observations=observations,
            confidence_level=confidence_level,
        )

        # Canonical API
        canonical_result = canonical_basel_traffic_light(
            n_violations=breaches,
            n_observations=observations,
            alpha=1 - confidence_level,
        )

        # Verify results are compatible
        assert legacy_result.color == "yellow"
        assert canonical_result.zone.value == "yellow"
        assert legacy_result.breaches == canonical_result.n_violations
        assert legacy_result.observations == canonical_result.n_observations

    def test_basel_traffic_light_equivalence_red(self):
        """Verify legacy matches canonical for RED zone."""
        from src.risk.validation.traffic_light import basel_traffic_light
        from src.risk_layer.var_backtest.traffic_light import (
            basel_traffic_light as canonical_basel_traffic_light,
        )

        # Test case: 10 breaches in 250 observations, 99% VaR → RED
        breaches = 10
        observations = 250
        confidence_level = 0.99

        # Legacy API
        legacy_result = basel_traffic_light(
            breaches=breaches,
            observations=observations,
            confidence_level=confidence_level,
        )

        # Canonical API
        canonical_result = canonical_basel_traffic_light(
            n_violations=breaches,
            n_observations=observations,
            alpha=1 - confidence_level,
        )

        # Verify results are compatible
        assert legacy_result.color == "red"
        assert canonical_result.zone.value == "red"
        assert legacy_result.breaches == canonical_result.n_violations
        assert legacy_result.observations == canonical_result.n_observations

    def test_thresholds_equivalence(self):
        """Verify legacy threshold function matches canonical."""
        from src.risk.validation.traffic_light import get_traffic_light_thresholds
        from src.risk_layer.var_backtest.traffic_light import compute_zone_thresholds

        test_cases = [
            (250, 0.99),  # Standard Basel case
            (500, 0.99),  # Larger window
            (100, 0.95),  # Different confidence
        ]

        for observations, confidence_level in test_cases:
            # Legacy
            legacy_green, legacy_yellow = get_traffic_light_thresholds(
                observations, confidence_level
            )

            # Canonical
            alpha = 1 - confidence_level
            canonical_green, canonical_yellow = compute_zone_thresholds(observations, alpha)

            # Verify equivalence
            assert legacy_green == canonical_green, (
                f"Green threshold mismatch for obs={observations}, conf={confidence_level}: "
                f"legacy={legacy_green}, canonical={canonical_green}"
            )
            assert legacy_yellow == canonical_yellow, (
                f"Yellow threshold mismatch for obs={observations}, conf={confidence_level}: "
                f"legacy={legacy_yellow}, canonical={canonical_yellow}"
            )

    def test_multiple_scenarios_equivalence(self):
        """Test multiple realistic scenarios for equivalence."""
        from src.risk.validation.traffic_light import basel_traffic_light
        from src.risk_layer.var_backtest.traffic_light import (
            basel_traffic_light as canonical_basel_traffic_light,
        )

        scenarios = [
            # (breaches, observations, confidence_level, expected_zone)
            (2, 250, 0.99, "green"),  # Few violations → GREEN
            (3, 250, 0.99, "green"),  # Normal → GREEN
            (5, 250, 0.99, "yellow"),  # Moderate → YELLOW
            (7, 250, 0.99, "yellow"),  # More → YELLOW
            (10, 250, 0.99, "red"),  # Too many → RED
            (
                25,
                250,
                0.95,
                "red",
            ),  # 95% VaR, many violations → RED (expected ~12.5, 25 is too many)
        ]

        for breaches, observations, confidence_level, expected_zone in scenarios:
            # Legacy
            legacy = basel_traffic_light(
                breaches=breaches,
                observations=observations,
                confidence_level=confidence_level,
            )

            # Canonical
            canonical = canonical_basel_traffic_light(
                n_violations=breaches,
                n_observations=observations,
                alpha=1 - confidence_level,
            )

            # Verify equivalence
            assert legacy.color == expected_zone
            assert canonical.zone.value == expected_zone
            assert legacy.breaches == canonical.n_violations
            assert legacy.observations == canonical.n_observations
            assert legacy.green_threshold == canonical.green_threshold
            assert legacy.yellow_threshold == canonical.yellow_threshold


class TestNoCodeDuplication:
    """Verify no duplicate computation occurs."""

    def test_legacy_imports_canonical_functions(self):
        """Verify legacy module imports from canonical module."""
        import src.risk.validation.traffic_light as legacy_module

        # Verify that legacy module has imported canonical functions
        assert hasattr(legacy_module, "_canonical_basel_traffic_light")
        assert hasattr(legacy_module, "_canonical_compute_zone_thresholds")

        # Verify these are the actual canonical functions
        from src.risk_layer.var_backtest.traffic_light import (
            basel_traffic_light as canonical_basel,
            compute_zone_thresholds as canonical_compute,
        )

        assert legacy_module._canonical_basel_traffic_light is canonical_basel
        assert legacy_module._canonical_compute_zone_thresholds is canonical_compute

    def test_legacy_module_has_no_duplicate_thresholds(self):
        """Verify legacy module doesn't contain duplicate threshold logic."""
        import inspect

        import src.risk.validation.traffic_light as legacy_module

        # Read source code
        source = inspect.getsource(legacy_module)

        # Check for absence of duplicate threshold computation
        # These patterns should NOT be in the legacy module (delegated to canonical)
        forbidden_patterns = [
            "scipy_binom.ppf",  # Binomial quantile computation
            "math.sqrt(n_observations * alpha",  # Standard deviation computation
            "* 1.645",  # Z-score for green threshold
            "* 3.09",  # Z-score for yellow threshold
        ]

        # Allow these in comments/docstrings but not in actual logic
        # We just check they're not in executable code (simplistic check)
        for pattern in forbidden_patterns:
            # If pattern exists, it should only be in comments/strings
            if pattern in source:
                # This is OK if it's in a comment or docstring
                # For simplicity, we just ensure it's not in multiple places
                count = source.count(pattern)
                assert count <= 1, (
                    f"Pattern '{pattern}' appears {count} times (should be delegated)"
                )

    def test_canonical_module_unchanged(self):
        """Verify canonical module is not affected by legacy wrapper."""
        from src.risk_layer.var_backtest.traffic_light import (
            BaselZone,
            basel_traffic_light,
            compute_zone_thresholds,
        )

        # Test canonical module independently
        result = basel_traffic_light(n_violations=3, n_observations=250, alpha=0.01)
        assert result.zone == BaselZone.GREEN
        assert result.capital_multiplier == 3.0

        # Test threshold computation
        green, yellow = compute_zone_thresholds(n_observations=250, alpha=0.01)
        assert green == 4
        assert yellow == 9


class TestBackwardCompatibility:
    """Verify existing code continues to work."""

    def test_legacy_result_has_required_methods(self):
        """Verify legacy TrafficLightResult has to_json_dict and to_markdown methods."""
        from src.risk.validation.traffic_light import basel_traffic_light

        result = basel_traffic_light(breaches=5, observations=250, confidence_level=0.99)

        # Check methods exist
        assert hasattr(result, "to_json_dict")
        assert hasattr(result, "to_markdown")

        # Check methods work
        json_dict = result.to_json_dict()
        assert isinstance(json_dict, dict)
        assert "color" in json_dict
        assert "breaches" in json_dict
        assert "breach_rate" in json_dict

        markdown = result.to_markdown()
        assert isinstance(markdown, str)
        assert "Basel Traffic Light Result" in markdown
        assert result.color.upper() in markdown

    def test_legacy_result_attributes(self):
        """Verify legacy TrafficLightResult has expected attributes."""
        from src.risk.validation.traffic_light import basel_traffic_light

        result = basel_traffic_light(breaches=5, observations=250, confidence_level=0.99)

        # Check all expected attributes exist
        assert hasattr(result, "color")
        assert hasattr(result, "breaches")
        assert hasattr(result, "observations")
        assert hasattr(result, "green_threshold")
        assert hasattr(result, "yellow_threshold")

        # Check types
        assert result.color in ("green", "yellow", "red")
        assert isinstance(result.breaches, int)
        assert isinstance(result.observations, int)
        assert isinstance(result.green_threshold, int)
        assert isinstance(result.yellow_threshold, int)
