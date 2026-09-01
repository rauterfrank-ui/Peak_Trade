"""Offline deterministic replay evaluator v0.

Replays stored DecisionEvent/IncidentRecord classification. Does not call the
trading core, does not invent labels, and does not consume evaluation-time
information.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_DECISION_EVENT,
    SCHEMA_NAME_INCIDENT_RECORD,
    freeze_record,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    validate_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.incident_record_v0 import (
    validate_incident_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import compute_content_hash_v0

REPLAY_EVALUATOR_ID: Final[str] = "peak_trade.learning.ddo.replay_evaluator_v0"
REPLAY_USES_DECISION_TIME_INFORMATION_SET: Final[bool] = True
REPLAY_HINDSIGHT_LEAKAGE_ALLOWED: Final[bool] = False
REPLAY_TRADING_CORE_REACHABLE: Final[bool] = False


def classify_decision_event_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    record = validate_decision_event_v0(payload)
    classification = {
        "evaluator_id": REPLAY_EVALUATOR_ID,
        "schema_name": SCHEMA_NAME_DECISION_EVENT,
        "record_id": record["record_id"],
        "decision_type": record["decision_type"],
        "decision_result": record["decision_result"],
        "reason_codes": list(record["reason_codes"]),
        "hard_block_reasons": list(record["hard_block_reasons"]),
        "content_hash": record["content_hash"],
        "uses_decision_time_information_set": True,
        "hindsight_leakage": False,
    }
    return freeze_record(classification)


def classify_incident_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    record = validate_incident_record_v0(payload)
    classification = {
        "evaluator_id": REPLAY_EVALUATOR_ID,
        "schema_name": SCHEMA_NAME_INCIDENT_RECORD,
        "record_id": record["record_id"],
        "incident_class": record["incident_class"],
        "reason_codes": list(record["reason_codes"]),
        "hard_block_reasons": list(record["hard_block_reasons"]),
        "content_hash": record["content_hash"],
        "uses_decision_time_information_set": True,
        "hindsight_leakage": False,
    }
    return freeze_record(classification)


def replay_same_inputs_same_classification_v0(
    first: Mapping[str, Any], second: Mapping[str, Any]
) -> MappingProxyType[str, Any]:
    left = classify_decision_event_v0(first)
    right = classify_decision_event_v0(second)
    if dict(left) != dict(right):
        raise DdoValidationError("REPLAY_CLASSIFICATION_DIVERGED")
    if compute_content_hash_v0(first) != compute_content_hash_v0(second):
        raise DdoValidationError("REPLAY_INPUT_HASH_DIVERGED")
    return left


def replay_same_incident_inputs_same_classification_v0(
    first: Mapping[str, Any], second: Mapping[str, Any]
) -> MappingProxyType[str, Any]:
    left = classify_incident_record_v0(first)
    right = classify_incident_record_v0(second)
    if dict(left) != dict(right):
        raise DdoValidationError("REPLAY_CLASSIFICATION_DIVERGED")
    if compute_content_hash_v0(first) != compute_content_hash_v0(second):
        raise DdoValidationError("REPLAY_INPUT_HASH_DIVERGED")
    return left


def replay_ledger_record_v0(
    ledger: AppendOnlyDdoLedgerV0, record_id: str
) -> MappingProxyType[str, Any]:
    record = ledger.get(record_id)
    schema_name = record["schema_name"]
    if schema_name == SCHEMA_NAME_DECISION_EVENT:
        return classify_decision_event_v0(record)
    if schema_name == SCHEMA_NAME_INCIDENT_RECORD:
        return classify_incident_record_v0(record)
    raise DdoValidationError(f"REPLAY_UNSUPPORTED_SCHEMA:{schema_name}")
