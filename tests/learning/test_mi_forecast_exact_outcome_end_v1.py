"""An explicit forecast end cannot join an outcome from another time window."""
from copy import deepcopy

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_outcome_join_v1 import (
    ForecastOutcomeJoinError, join_forecast_to_n_bars_outcome_v1,
)
from tests.learning.test_market_intelligence_forecast_calibration_offline_stack_v1 import (
    _mint_forecast, _observation_for_n,
)


@pytest.mark.parametrize("end", ["2026-09-01T13:00:00Z", "2026-09-01T15:00:00Z", "2026-09-02T14:00:00Z"])
def test_same_n_and_bar_spec_cannot_join_a_different_target_end(end):
    forecast = _mint_forecast(n_bars=2, created="2026-09-01T12:00:00Z", horizon_end=end, info_set="info.end.test")
    observation = _observation_for_n(n_bars=2)
    before = deepcopy(dict(observation))
    with pytest.raises(ForecastOutcomeJoinError, match="FORECAST_OUTCOME_HORIZON_END_MISMATCH"):
        join_forecast_to_n_bars_outcome_v1(forecast_evidence=forecast, evaluation_observation=observation)
    assert dict(observation) == before


def test_outcome_end_is_last_bar_close_not_later_evaluation_knowledge():
    forecast = _mint_forecast(n_bars=2, created="2026-09-01T12:00:00Z", horizon_end="2026-09-01T14:00:00Z", info_set="info.end.later")
    observation = dict(_observation_for_n(n_bars=2))
    observation["evaluation_time_utc"] = "2026-09-01T16:00:00Z"
    joined = join_forecast_to_n_bars_outcome_v1(forecast_evidence=forecast, evaluation_observation=observation)
    assert joined["join_status"] == "JOINED"


def test_equal_utc_instants_with_different_precision_join():
    forecast = _mint_forecast(n_bars=2, created="2026-09-01T12:00:00Z", horizon_end="2026-09-01T14:00:00.000Z", info_set="info.end.precision")
    joined = join_forecast_to_n_bars_outcome_v1(forecast_evidence=forecast, evaluation_observation=_observation_for_n(n_bars=2))
    assert joined["join_status"] == "JOINED"
