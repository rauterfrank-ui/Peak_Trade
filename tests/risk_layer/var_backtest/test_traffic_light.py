"""Co-located unit tests for src/risk_layer/var_backtest/traffic_light.py.

The canonical engine uses *alpha* (e.g. 0.01 for 99% VaR), not 0.99 confidence.
Wrappers in src.risk/validation/ delegate here; this file pins package behavior.
"""

from __future__ import annotations

import re

import pytest

from src.risk_layer.var_backtest.traffic_light import (
    BaselZone,
    TrafficLightMonitor,
    TrafficLightResult,
    basel_traffic_light,
    compute_zone_thresholds,
    traffic_light_recommendation,
)

ALPHA_99 = 0.01
N_250 = 250


def test_module_exports_expected_public_api() -> None:
    assert BaselZone.GREEN.value == "green"
    assert "zone" in TrafficLightResult.__dataclass_fields__


@pytest.mark.parametrize(
    ("n_violations", "expected_zone"),
    [
        (0, BaselZone.GREEN),
        (4, BaselZone.GREEN),
        (5, BaselZone.YELLOW),
        (9, BaselZone.YELLOW),
        (10, BaselZone.RED),
        (50, BaselZone.RED),
    ],
)
def test_basel_zones_250_observations_99_var(n_violations: int, expected_zone: BaselZone) -> None:
    result = basel_traffic_light(n_violations, N_250, ALPHA_99)
    assert result.zone == expected_zone
    assert result.n_violations == n_violations
    assert result.n_observations == N_250
    assert result.alpha == ALPHA_99
    assert result.green_threshold == 4
    assert result.yellow_threshold == 9
    assert pytest.approx(result.expected_violations) == N_250 * ALPHA_99
    assert pytest.approx(result.violation_rate) == n_violations / N_250


def test_traffic_light_result_fields_are_stable() -> None:
    result = basel_traffic_light(3, N_250, ALPHA_99)
    assert isinstance(result, TrafficLightResult)
    assert isinstance(result.zone, BaselZone)
    assert 3.0 <= result.capital_multiplier <= 4.0


def test_invalid_inputs_raise_value_error() -> None:
    with pytest.raises(ValueError, match="n_violations"):
        basel_traffic_light(-1, N_250, ALPHA_99)
    with pytest.raises(ValueError, match="n_observations"):
        basel_traffic_light(0, 0, ALPHA_99)
    with pytest.raises(ValueError, match="alpha"):
        basel_traffic_light(0, N_250, 0.0)
    with pytest.raises(ValueError, match="alpha"):
        basel_traffic_light(0, N_250, 1.0)


def test_violations_can_exceed_observations_still_classifies() -> None:
    """Model allows breach count above window size (edge stress); rate can exceed 1."""
    result = basel_traffic_light(300, N_250, ALPHA_99)
    assert result.zone == BaselZone.RED
    assert result.n_violations == 300
    assert result.violation_rate > 1.0


def test_compute_zone_thresholds_basel_window() -> None:
    g, y = compute_zone_thresholds(250, ALPHA_99)
    assert (g, y) == (4, 9)


def test_traffic_light_recommendation_is_non_empty_and_avoids_live_authority_claims() -> None:
    result = basel_traffic_light(5, N_250, ALPHA_99)
    text = traffic_light_recommendation(result)
    assert isinstance(text, str)
    assert len(text) > 20
    # Editorial strings are regulatory; must not look like a flat "go live" permit.
    lowered = text.lower()
    for bad in [
        "live authorization granted",
        "signoff complete",
        "you are approved for live",
        "strategy-ready",
    ]:
        assert bad not in lowered


def test_traffic_light_monitor_update_matches_basel_traffic_light() -> None:
    monitor = TrafficLightMonitor(alpha=ALPHA_99, window=5)
    r1 = monitor.update(realized_loss=1.0, var_estimate=0.5)  # violation
    assert r1.n_observations == 1
    assert r1.n_violations == 1
    direct = basel_traffic_light(1, 1, ALPHA_99)
    assert r1.zone == direct.zone


def test_result_repr_does_not_embed_authority_phrases() -> None:
    r = basel_traffic_light(0, N_250, ALPHA_99)
    s = repr(r).lower()
    for bad in [
        "live authorization granted",
        "signoff complete",
        "externally authorized",
    ]:
        assert bad not in s


def test_recommendation_red_zone_mentions_suspension_not_live_enablement() -> None:
    r = basel_traffic_light(20, N_250, ALPHA_99)
    assert r.zone == BaselZone.RED
    text = traffic_light_recommendation(r).lower()
    # Regulatory wording: suspend model, not a trading enablement claim.
    assert "suspend" in text or "red" in text
    assert re.search(r"live authorization granted|ready for live", text) is None
