"""Learning consumers for CURRENT Double-Play decision bundle binding v1.

Resolves authoritative producer decision tokens for offline evaluation,
replay classification, and challenger comparison. Does not import trading,
ops, execution, or risk.

TRADING_AUTHORITY=NONE
RUNTIME_EFFECT=NONE
DECISION_EVENT_IS_ENVELOPE_ONLY=true
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import freeze_record
from src.learning.deterministic_decision_outcome_v0.current_decision_learning_binding_v1 import (
    RESOLVER_ID,
    CurrentDoublePlayDecisionBundleV1,
    resolve_current_double_play_decision_bundle_v1,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    validate_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.double_play_input_evidence_v1 import (
    PRODUCER_ID as DOUBLE_PLAY_PRODUCER_ID,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_observation_v0 import (
    EVALUATION_OBSERVATION_SCHEMA_NAME,
    EVALUATION_OBSERVATION_SCHEMA_VERSION,
)

CONSUMER_BINDING_ID: Final[str] = "peak_trade.learning.ddo.current_decision_consumer_v1"
CLASSIFIER_ID: Final[str] = "peak_trade.learning.ddo.classify_current_double_play_decision_v0"


def is_double_play_decision_event_v0(decision: Mapping[str, Any]) -> bool:
    producer_id = decision.get("producer_id")
    return isinstance(producer_id, str) and producer_id == DOUBLE_PLAY_PRODUCER_ID


def require_current_double_play_bundle_v1(
    *,
    records_by_id: Mapping[str, Mapping[str, Any]],
    decision_event_ref: str,
) -> CurrentDoublePlayDecisionBundleV1:
    """Fail-closed bundle join for Double-Play semantic consumers."""
    return resolve_current_double_play_decision_bundle_v1(
        records_by_id=records_by_id,
        decision_event_ref=decision_event_ref,
    )


def classify_current_double_play_decision_v0(
    bundle: CurrentDoublePlayDecisionBundleV1,
) -> MappingProxyType[str, Any]:
    """Authoritative producer decision classification (not DecisionEvent envelope)."""
    return freeze_record(
        {
            "evaluator_id": CLASSIFIER_ID,
            "resolver_id": RESOLVER_ID,
            "decision_event_ref": bundle.decision_event_ref,
            "observation_ref": bundle.observation_ref,
            "input_evidence_ref": bundle.input_evidence_ref,
            "authoritative_decision_outcome": bundle.authoritative_decision_outcome,
            "policy_decision_id": bundle.policy_decision_id,
            "instrument_id": bundle.instrument_id,
            "trading_epoch": bundle.trading_epoch,
            "semantic_digest": bundle.semantic_digest,
            "uses_decision_time_information_set": True,
            "hindsight_leakage": False,
            "decision_event_is_envelope_only": True,
        }
    )


def authoritative_decision_outcome_for_row_v1(
    row: Mapping[str, Any],
    *,
    records_by_id: Mapping[str, Mapping[str, Any]] | None,
) -> str | None:
    """Resolve producer outcome token when row is a DP semantic record."""
    schema_name = row.get("schema_name")
    if schema_name == "double_play_entry_exit_observation":
        payload = row.get("producer_canonical_payload")
        if isinstance(payload, Mapping):
            outcome = payload.get("decision_outcome")
            if isinstance(outcome, str) and outcome:
                return outcome
        return None
    if schema_name == "decision_event" and records_by_id is not None:
        decision = validate_decision_event_v0(row)
        if not is_double_play_decision_event_v0(decision):
            return None
        bundle = require_current_double_play_bundle_v1(
            records_by_id=records_by_id,
            decision_event_ref=str(decision["record_id"]),
        )
        return bundle.authoritative_decision_outcome
    return None


def build_decision_time_evaluation_observation_v1(
    *,
    decision_event_ref: str,
    evaluation_time_utc: str,
    evaluation_time_information_set_ref: str | None = None,
) -> dict[str, Any]:
    """Minimal evaluation observation at DECISION_TIME without invented economics."""
    return {
        "schema_name": EVALUATION_OBSERVATION_SCHEMA_NAME,
        "schema_version": EVALUATION_OBSERVATION_SCHEMA_VERSION,
        "decision_event_ref": decision_event_ref,
        "evaluation_horizon": "DECISION_TIME",
        "evaluation_time_utc": evaluation_time_utc,
        "evaluation_time_information_set_ref": evaluation_time_information_set_ref,
    }


def require_records_index_for_double_play_semantic_evaluation_v1(
    decision: Mapping[str, Any],
    records_by_id: Mapping[str, Mapping[str, Any]] | None,
) -> None:
    if is_double_play_decision_event_v0(decision) and records_by_id is None:
        raise DdoValidationError("DOUBLE_PLAY_SEMANTIC_EVAL_REQUIRES_RECORDS_INDEX")


def decision_score_from_current_bundle_v1(
    *,
    bundle: CurrentDoublePlayDecisionBundleV1,
    declared_decision_score: str | None,
) -> str:
    if declared_decision_score is not None:
        return str(declared_decision_score)
    token = bundle.authoritative_decision_outcome
    if not token:
        return UNKNOWN
    return token
