"""Productive evaluation-runtime host for REAL N_BARS horizon observations.

Consumes only the in-process horizon producer result plus the same decision
event and explicit evaluation identity. Does not recompute supplier outcomes.
"""

from __future__ import annotations

import hashlib
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    validate_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    EVALUATION_ENGINE_ID,
    evaluate_offline_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_contracts_v1 import (
    EVALUATION_RUNTIME_WIRING,
)

PRODUCTIVE_EVALUATION_HOST_ID: Final[str] = (
    "peak_trade.learning.ddo.evaluation_runtime_productive_host_v1"
)
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False


def _require_runtime_wired_v1() -> None:
    if not EVALUATION_RUNTIME_WIRING:
        raise DdoValidationError("EVALUATION_RUNTIME_NOT_WIRED")


def ledger_records_index_v1(
    ledger: AppendOnlyDdoLedgerV0,
) -> dict[str, dict[str, Any]]:
    """Build a fail-closed records index for Double-Play semantic evaluation."""
    return {str(row["record_id"]): dict(row) for row in ledger.read_all()}


def derive_productive_n_bars_evaluation_identity_v1(
    *,
    decision_record_id: str,
    evaluation_time_utc: str,
    correlation_id: str,
) -> dict[str, Any]:
    """Deterministic evaluation record ids for productive N_BARS runtime joins."""
    base = f"{decision_record_id}|{evaluation_time_utc}|{correlation_id}"
    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()
    return {
        "outcome_record_id": f"out.nbars.{digest[:48]}",
        "attribution_record_id": f"attr.nbars.{digest[:48]}",
        "counterfactual_record_id": f"cf.nbars.{digest[:48]}",
        "correlation_id": correlation_id,
        "event_time_utc": evaluation_time_utc,
        "code_sha": UNKNOWN,
        "config_hash": UNKNOWN,
    }


def produce_n_bars_evaluation_runtime_bundle_v1(
    horizon_producer_result: Mapping[str, Any],
    decision_event: Mapping[str, Any],
    identity: Mapping[str, Any],
    *,
    ledger: AppendOnlyDdoLedgerV0 | None = None,
) -> dict[str, Any]:
    """Single evaluation consume of the authorized horizon observation payload."""
    _require_runtime_wired_v1()
    if not isinstance(horizon_producer_result, Mapping):
        raise DdoValidationError("EVALUATION_RUNTIME_HORIZON_RESULT_INVALID")
    observation = horizon_producer_result.get("evaluation_observation")
    if not isinstance(observation, Mapping):
        raise DdoValidationError("EVALUATION_RUNTIME_HORIZON_OBSERVATION_MISSING")
    decision = validate_decision_event_v0(decision_event)
    if str(observation.get("decision_event_ref")) != str(decision["record_id"]):
        raise DdoValidationError("EVALUATION_RUNTIME_DECISION_REF_MISMATCH")
    records_by_id = ledger_records_index_v1(ledger) if ledger is not None else None
    bundle = evaluate_offline_bundle_v0(
        decision,
        observation,
        identity=identity,
        ledger=ledger,
        records_by_id=records_by_id,
    )
    persist = bundle.get("persist")
    durable_persist = (
        dict(persist)
        if isinstance(persist, Mapping)
        else {"status": "SKIPPED_NO_LEDGER", "reason": "LEDGER_NOT_BOUND"}
    )
    return {
        "ok": True,
        "evaluator_id": EVALUATION_ENGINE_ID,
        "runtime_wiring": EVALUATION_RUNTIME_WIRING,
        "evaluation_horizon": bundle["outcome_record"]["evaluation_horizon"],
        "actual_outcome_ref": bundle["outcome_record"]["actual_outcome_ref"],
        "economic_score": bundle["outcome_record"]["economic_score"],
        "hindsight_leakage": bundle["hindsight_leakage"],
        "bundle": dict(bundle),
        "durable_persist": durable_persist,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "producer_host_id": PRODUCTIVE_EVALUATION_HOST_ID,
    }
