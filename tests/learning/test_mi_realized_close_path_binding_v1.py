"""Close-path observations must not silently replace bound measurement endpoints."""
from copy import deepcopy

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.realized_behavior_v1 import (
    RealizedBehaviorError, RealizedBehaviorJoinInputsV1, join_market_context_to_realized_behavior_v1,
)
from tests.learning.test_market_context_realized_behavior_join_v1 import _pipeline, _context_for_observation, _snapshot


def _join(bars):
    pipe = _pipeline()
    obs = pipe["evaluation_observation"]
    return join_market_context_to_realized_behavior_v1(RealizedBehaviorJoinInputsV1(
        market_context=_context_for_observation(obs), evaluation_observation=obs,
        measurement_evidence=pipe["materialization"].measurement_evidence_artifact,
        o4_bars_for_path=bars,
    ))


@pytest.mark.parametrize("index", [0, -1])
def test_same_bar_identity_with_different_endpoint_price_is_rejected(index):
    bars = deepcopy(_snapshot()["o4_bars"])
    bars[index]["close"] = 999.0
    with pytest.raises(RealizedBehaviorError, match="O4_MEASUREMENT_ENDPOINT_PRICE_MISMATCH"):
        _join(bars)


@pytest.mark.parametrize("different_price", [False, True])
def test_duplicate_bar_identity_is_ambiguous(different_price):
    bars = deepcopy(_snapshot()["o4_bars"])
    duplicate = deepcopy(bars[-1])
    if different_price:
        duplicate["close"] = 999.0
    bars.append(duplicate)
    with pytest.raises(RealizedBehaviorError, match="O4_BAR_IDENTITY_DUPLICATE"):
        _join(bars)


def test_supplied_order_is_not_the_identity_order():
    bars = deepcopy(_snapshot()["o4_bars"])
    expected = _join(bars)
    assert _join(list(reversed(bars))) == expected
