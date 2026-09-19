"""Offline REAL N_BARS observation supplier (DDO Real Outcome Horizon S1/S2).

Pure library: no trading, execution, risk, venue, network, capture, or runtime wiring.
Does not mint ``actual_outcome_ref`` or compute ``economic_score``.
"""

from __future__ import annotations

from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    validate_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_observation_v0 import (
    EVALUATION_OBSERVATION_SCHEMA_NAME,
    EVALUATION_OBSERVATION_SCHEMA_VERSION,
    validate_evaluation_observation_v0,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_contracts_v1 import (
    REAL_OUTCOME_HORIZON_ENGINE_WIRED,
    SUPPLIER_COMPUTES_ECONOMIC_SCORE,
    SUPPLIER_MINTS_ACTUAL_OUTCOME_REF,
    validate_n_bars_observation_for_decision_v1,
    validate_real_outcome_horizon_supplier_input_v1,
)

REAL_OUTCOME_HORIZON_ENGINE_ID: Final[str] = (
    "peak_trade.learning.ddo.real_outcome_horizon_engine_v1"
)
REAL_OUTCOME_HORIZON_ENGINE_CAPTURE_SEAM: Final[str] = "real_outcome_horizon_engine"
REAL_OUTCOME_HORIZON_ENGINE_ROLE: Final[str] = "OFFLINE_OBSERVATION_SUPPLIER_ONLY"
TRADING_CORE_REACHABLE: Final[bool] = False
RUNTIME_EFFECT: Final[str] = "NONE"


def supply_n_bars_evaluation_observation_v1(
    decision_event: Mapping[str, Any],
    supplier_input: Mapping[str, Any],
    *,
    decision_event_ref: str | None = None,
    evaluation_time_utc: str | None = None,
) -> dict[str, Any]:
    """Deterministic offline supplier: validated supplier input -> evaluation_observation_v0."""
    decision = validate_decision_event_v0(decision_event)
    bundle = validate_real_outcome_horizon_supplier_input_v1(supplier_input)
    ref = decision_event_ref or str(decision["record_id"])
    eval_time = evaluation_time_utc
    if eval_time is None:
        closes = bundle.get("bar_close_times_utc")
        if closes:
            eval_time = closes[-1]
        else:
            eval_time = str(decision["event_time_utc"])

    payload: dict[str, Any] = {
        "schema_name": EVALUATION_OBSERVATION_SCHEMA_NAME,
        "schema_version": EVALUATION_OBSERVATION_SCHEMA_VERSION,
        "decision_event_ref": ref,
        "evaluation_horizon": "N_BARS",
        "evaluation_time_utc": eval_time,
        "evaluation_time_information_set_ref": bundle["evaluation_time_information_set_ref"],
        "horizon_start_time_utc": bundle["horizon_start_time_utc"],
        "instrument_ref": bundle["instrument_ref"],
        "bar_spec_ref": bundle["bar_spec_ref"],
        "n_bars": bundle["n_bars"],
        "horizon_observation_status": bundle["horizon_observation_status"],
        "horizon_observation_reason": bundle.get("horizon_observation_reason"),
        "outcome_scalar_kind": bundle["outcome_scalar_kind"],
        "bar_close_times_utc": bundle.get("bar_close_times_utc"),
        "bar_identity_refs": bundle.get("bar_identity_refs"),
        "actual_outcome_ref": bundle["actual_outcome_ref"],
        "economic_score": bundle.get("economic_score"),
    }
    observation = validate_evaluation_observation_v0(payload)
    validate_n_bars_observation_for_decision_v1(decision, observation)
    return dict(observation)


def real_outcome_horizon_engine_authority_snapshot_v1() -> dict[str, Any]:
    return {
        "engine_id": REAL_OUTCOME_HORIZON_ENGINE_ID,
        "role": REAL_OUTCOME_HORIZON_ENGINE_ROLE,
        "capture_seam": REAL_OUTCOME_HORIZON_ENGINE_CAPTURE_SEAM,
        "real_outcome_horizon_engine_wired": REAL_OUTCOME_HORIZON_ENGINE_WIRED,
        "supplier_mints_actual_outcome_ref": SUPPLIER_MINTS_ACTUAL_OUTCOME_REF,
        "supplier_computes_economic_score": SUPPLIER_COMPUTES_ECONOMIC_SCORE,
        "trading_core_reachable": TRADING_CORE_REACHABLE,
        "runtime_effect": RUNTIME_EFFECT,
    }
