"""Realized behavior may consume only the measurement referenced by its observation."""
from copy import deepcopy

import pytest

from src.learning.deterministic_decision_outcome_v0.o4_n_bars_bar_evidence_bridge_contracts_v1 import mint_ddo_content_ref_v1
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.realized_behavior_v1 import (
    RealizedBehaviorError, RealizedBehaviorJoinInputsV1, join_market_context_to_realized_behavior_v1,
)
from tests.learning.test_market_context_realized_behavior_join_v1 import _pipeline, _context_for_observation


@pytest.mark.parametrize("field,value", [
    ("log_return", 9.9), ("end_price", 999.0), ("actual_outcome_ref", "ddo.outcome.other"),
    ("instrument_ref", "other.instrument"), ("bar_spec_ref", "other.bar"),
])
def test_mutated_measurement_cannot_retain_a_trusted_outcome_ref(field, value):
    pipe = _pipeline()
    obs = pipe["evaluation_observation"]
    measurement = deepcopy(dict(pipe["materialization"].measurement_evidence_artifact))
    measurement[field] = value
    with pytest.raises(RealizedBehaviorError, match="MEASUREMENT_EVIDENCE_BINDING_INVALID"):
        join_market_context_to_realized_behavior_v1(RealizedBehaviorJoinInputsV1(
            market_context=_context_for_observation(obs), evaluation_observation=obs,
            measurement_evidence=measurement,
        ))


@pytest.mark.parametrize("field,value", [("instrument_ref", "other.instrument"), ("n_bars", 99),
    ("horizon_start_time_utc", "2026-09-01T11:00:00Z"), ("outcome_scalar_kind", "ABS_RETURN")])
def test_rehashed_measurement_must_still_match_observation_context(field, value):
    pipe = _pipeline()
    obs = deepcopy(dict(pipe["evaluation_observation"]))
    measurement = deepcopy(dict(pipe["materialization"].measurement_evidence_artifact))
    measurement[field] = value
    measurement.pop("actual_outcome_ref")
    new_ref = mint_ddo_content_ref_v1(prefix="ddo.outcome.measure.", payload=measurement)
    measurement["actual_outcome_ref"] = new_ref
    obs["actual_outcome_ref"] = new_ref
    with pytest.raises(RealizedBehaviorError, match="MEASUREMENT_EVIDENCE_BINDING_INVALID"):
        join_market_context_to_realized_behavior_v1(RealizedBehaviorJoinInputsV1(
            market_context=_context_for_observation(obs), evaluation_observation=obs,
            measurement_evidence=measurement,
        ))
