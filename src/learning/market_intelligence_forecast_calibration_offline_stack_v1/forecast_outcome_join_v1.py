"""Join ForecastEvidence to CURRENT N_BARS realized outcome (reference-only; no mutation)."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import require_mapping
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_observation_v0 import (
    validate_evaluation_observation_v0,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_contracts_v1 import (
    require_positive_int,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import compute_content_hash_v0
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    NO_DUPLICATE_OUTCOME_TRUTH,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    validate_forecast_evidence_v1,
)

JOIN_SCHEMA_VERSION: Final[str] = "forecast_outcome_join_v1"


class ForecastOutcomeJoinError(ValueError):
    """Fail-closed forecast/outcome join error."""


def join_forecast_to_n_bars_outcome_v1(
    *,
    forecast_evidence: Mapping[str, Any],
    evaluation_observation: Mapping[str, Any] | None,
) -> MappingProxyType[str, Any]:
    forecast = validate_forecast_evidence_v1(forecast_evidence)
    if evaluation_observation is None:
        return MappingProxyType(
            {
                "schema_version": JOIN_SCHEMA_VERSION,
                "join_status": "OUTCOME_MISSING",
                "forecast_evidence_id": forecast["forecast_evidence_id"],
                "actual_outcome_ref": None,
                "n_bars_outcome_owner": "peak_trade.learning.ddo.real_outcome_horizon_engine_v1",
                "outcome_fields_mutated": False,
                "no_duplicate_outcome_truth": NO_DUPLICATE_OUTCOME_TRUTH,
            }
        )

    observation = validate_evaluation_observation_v0(evaluation_observation)
    obs_n = require_positive_int(observation.get("n_bars"), "n_bars")
    if obs_n != int(forecast["n_bars"]):
        raise ForecastOutcomeJoinError("FORECAST_N_BARS_MISMATCH")
    if str(observation.get("bar_spec_ref")) != str(forecast["bar_spec_ref"]):
        raise ForecastOutcomeJoinError("FORECAST_BAR_SPEC_MISMATCH")

    actual_outcome_ref = observation.get("actual_outcome_ref")
    if actual_outcome_ref is None:
        raise ForecastOutcomeJoinError("N_BARS_ACTUAL_OUTCOME_REF_MISSING")

    join_body = {
        "schema_version": JOIN_SCHEMA_VERSION,
        "join_status": "JOINED",
        "forecast_evidence_id": forecast["forecast_evidence_id"],
        "actual_outcome_ref": str(actual_outcome_ref),
        "evaluation_observation_ref": str(observation.get("record_id", actual_outcome_ref)),
        "n_bars": obs_n,
        "bar_spec_ref": str(observation.get("bar_spec_ref")),
        "outcome_fields_mutated": False,
        "no_duplicate_outcome_truth": NO_DUPLICATE_OUTCOME_TRUTH,
    }
    join_body["join_digest"] = compute_content_hash_v0(join_body)
    return MappingProxyType(join_body)


def assert_n_bars_observation_unmodified_v1(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> None:
    if dict(before) != dict(after):
        raise DdoValidationError("N_BARS_OBSERVATION_MUTATED_BY_MI_JOIN")
