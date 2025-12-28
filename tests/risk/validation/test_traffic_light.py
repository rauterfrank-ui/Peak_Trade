"""Tests for Basel Traffic Light System."""

import pytest

from src.risk.validation.traffic_light import (
    TrafficLightResult,
    basel_traffic_light,
    get_traffic_light_thresholds,
)


class TestTrafficLightClassification:
    """Test traffic light classification."""

    def test_green_zone_boundary(self):
        """Test boundary of green zone (0-4 breaches for 250 obs)."""
        # 4 breaches -> green
        result = basel_traffic_light(4, 250, 0.99)
        assert result.color == 'green'

        # 5 breaches -> yellow
        result = basel_traffic_light(5, 250, 0.99)
        assert result.color == 'yellow'

    def test_yellow_zone_boundary(self):
        """Test boundary of yellow zone (5-9 breaches for 250 obs)."""
        # 9 breaches -> yellow
        result = basel_traffic_light(9, 250, 0.99)
        assert result.color == 'yellow'

        # 10 breaches -> red
        result = basel_traffic_light(10, 250, 0.99)
        assert result.color == 'red'

    def test_red_zone(self):
        """Test red zone (>=10 breaches for 250 obs)."""
        result = basel_traffic_light(15, 250, 0.99)
        assert result.color == 'red'

        result = basel_traffic_light(50, 250, 0.99)
        assert result.color == 'red'

    def test_zero_breaches(self):
        """Test with zero breaches (should be green)."""
        result = basel_traffic_light(0, 250, 0.99)
        assert result.color == 'green'


class TestTrafficLightThresholds:
    """Test threshold computation."""

    def test_basel_standard_thresholds(self):
        """Test Basel standard thresholds (250 obs, 99% VaR)."""
        green, yellow = get_traffic_light_thresholds(250, 0.99)

        assert green == 4
        assert yellow == 9

    def test_scaled_thresholds(self):
        """Test threshold scaling for different observation counts."""
        # 500 observations -> scale by 2x
        green, yellow = get_traffic_light_thresholds(500, 0.99)

        assert green == 8  # 4 * 2
        assert yellow == 18  # 9 * 2

        # Ensure yellow > green
        assert yellow > green

    def test_small_sample_thresholds(self):
        """Test thresholds for small samples."""
        green, yellow = get_traffic_light_thresholds(50, 0.99)

        # Scale by 0.2
        assert green >= 0
        assert yellow > green


class TestTrafficLightEdgeCases:
    """Test edge cases."""

    def test_zero_observations(self):
        """Test with zero observations."""
        green, yellow = get_traffic_light_thresholds(0, 0.99)
        assert green == 0
        assert yellow == 0

    def test_all_breaches(self):
        """Test when all observations are breaches (should be red)."""
        result = basel_traffic_light(250, 250, 0.99)
        assert result.color == 'red'


class TestTrafficLightSerialization:
    """Test result serialization."""

    def test_to_json_dict(self):
        """Test JSON serialization."""
        result = basel_traffic_light(5, 250, 0.99)
        json_dict = result.to_json_dict()

        assert isinstance(json_dict, dict)
        assert "color" in json_dict
        assert "breaches" in json_dict
        assert "observations" in json_dict
        assert "breach_rate" in json_dict
        assert json_dict["color"] == "yellow"

    def test_to_markdown(self):
        """Test markdown report generation."""
        result = basel_traffic_light(5, 250, 0.99)
        markdown = result.to_markdown()

        assert isinstance(markdown, str)
        assert "Basel Traffic Light" in markdown
        assert "YELLOW" in markdown
        assert str(result.breaches) in markdown
