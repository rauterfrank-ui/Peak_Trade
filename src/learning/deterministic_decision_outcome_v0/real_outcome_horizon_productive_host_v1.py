"""Productive host producer for REAL N_BARS horizon observation (capture seam).

Consumes governed O4 snapshot + decision_event only. Does not create bars,
does not bypass supplier authority, and does not reach trading or execution.
"""

from __future__ import annotations

from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.capture_v0 import observe_after_producer_v0
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    validate_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
    run_offline_n_bars_horizon_pipeline_v1,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_contracts_v1 import (
    REAL_OUTCOME_HORIZON_ENGINE_WIRED,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_engine_v1 import (
    REAL_OUTCOME_HORIZON_ENGINE_ID,
)

PRODUCTIVE_HOST_ID: Final[str] = "peak_trade.learning.ddo.real_outcome_horizon_productive_host_v1"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False


def _require_wired_v1() -> None:
    if not REAL_OUTCOME_HORIZON_ENGINE_WIRED:
        raise DdoValidationError("REAL_OUTCOME_HORIZON_ENGINE_NOT_WIRED")


@observe_after_producer_v0(seam_id="real_outcome_horizon_engine")
def produce_real_outcome_horizon_evaluation_observation_v1(
    decision_event: Mapping[str, Any],
    o4_snapshot: Mapping[str, Any],
    *,
    outcome_scalar_kind: str = "LOG_RETURN",
    hit_target_value: float | None = None,
    hit_target_comparator: str | None = None,
    economic_score: str | None = None,
    producer_observed_at_unix: float | None = None,
) -> dict[str, Any]:
    """Single productive join: O4 snapshot → supplier → horizon observation."""
    _require_wired_v1()
    decision = validate_decision_event_v0(decision_event)
    pipeline = run_offline_n_bars_horizon_pipeline_v1(
        decision,
        o4_snapshot,
        outcome_scalar_kind=outcome_scalar_kind,
        hit_target_value=hit_target_value,
        hit_target_comparator=hit_target_comparator,  # type: ignore[arg-type]
        economic_score=economic_score,
    )
    observation = pipeline["evaluation_observation"]
    materialization = pipeline["materialization"]
    status = str(observation.get("horizon_observation_status") or UNKNOWN)
    ok = status == "OK" and str(observation.get("actual_outcome_ref") or "") not in {"", UNKNOWN}
    failure_codes: tuple[str, ...] = () if ok else (status,)
    return {
        "ok": ok,
        "hard_stop": False,
        "failure_codes": failure_codes,
        "horizon_observation_status": status,
        "evaluation_observation": dict(observation),
        "supplier_input_ref_present": "actual_outcome_ref" in materialization.supplier_input,
        "measurement_producer_id": materialization.measurement_evidence_artifact.get(
            "measurement_producer_id"
        ),
        "bridge_contract_id": materialization.evaluation_time_information_set_artifact.get(
            "bridge_contract_id"
        ),
        "producer_observed_at_unix": producer_observed_at_unix,
        "authority_owner": REAL_OUTCOME_HORIZON_ENGINE_ID,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
    }
