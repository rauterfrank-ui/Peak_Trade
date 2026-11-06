"""Normative Double-Play current decision learning bundle join v1.

Learning-only. Resolves typed producer decision semantics from persisted DDO
records. Does not import trading, ops, execution, or risk producers.

TRADING_AUTHORITY=NONE
RUNTIME_EFFECT=NONE
DECISION_EVENT_IS_ENVELOPE_ONLY=true
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_DECISION_EVENT,
    SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION,
    SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE,
    SCHEMA_VERSION_DECISION_EVENT_V0,
    SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_V1,
    SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE_V1,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    validate_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.double_play_input_evidence_v1 import (
    TYPED_PROJECTION_STATUS as INPUT_TYPED_STATUS,
    UNAVAILABLE_PROJECTION_STATUS as INPUT_UNAVAILABLE_STATUS,
    compute_producer_input_digest_from_canonical_payload_v1,
    validate_double_play_entry_exit_policy_input_evidence_v1,
)
from src.learning.deterministic_decision_outcome_v0.double_play_observation_projection_v1 import (
    PRODUCER_CANONICAL_KEYS,
    TYPED_PROJECTION_STATUS,
    UNAVAILABLE_PROJECTION_STATUS,
    validate_double_play_entry_exit_observation_v1,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoLineageError

BINDING_ID: Final[str] = "peak_trade.learning.ddo.current_decision_learning_binding_v1"
RESOLVER_ID: Final[str] = "peak_trade.learning.ddo.resolve_current_double_play_decision_bundle_v1"

ROLE_DECISION_EVENT_V0: Final[str] = "GENERIC_OBSERVATION_LINEAGE_ENVELOPE"
ROLE_DOUBLE_PLAY_OBSERVATION_V1: Final[str] = "CURRENT_TYPED_PRODUCER_DECISION_PROJECTION"
ROLE_DOUBLE_PLAY_INPUT_EVIDENCE_V1: Final[str] = "PRE_DECISION_INPUT_EVIDENCE"

CURRENT_DECISION_LEARNING_ROLES_V1: Final[Mapping[str, Any]] = MappingProxyType(
    {
        "binding_id": BINDING_ID,
        "resolver_id": RESOLVER_ID,
        "producer_semantics_authoritative": True,
        "decision_event_is_envelope_only": True,
        "no_decision_event_enum_expansion": True,
        "authoritative_decision_outcome_field": (
            "double_play_entry_exit_observation_v1.producer_canonical_payload.decision_outcome"
        ),
        "records": MappingProxyType(
            {
                SCHEMA_NAME_DECISION_EVENT: MappingProxyType(
                    {
                        "schema_version": SCHEMA_VERSION_DECISION_EVENT_V0,
                        "role": ROLE_DECISION_EVENT_V0,
                        "carries_producer_decision_semantics": False,
                    }
                ),
                SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION: MappingProxyType(
                    {
                        "schema_version": SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_V1,
                        "role": ROLE_DOUBLE_PLAY_OBSERVATION_V1,
                        "carries_producer_decision_semantics": True,
                    }
                ),
                SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE: MappingProxyType(
                    {
                        "schema_version": (
                            SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE_V1
                        ),
                        "role": ROLE_DOUBLE_PLAY_INPUT_EVIDENCE_V1,
                        "carries_producer_decision_semantics": False,
                    }
                ),
            }
        ),
    }
)


class CurrentDecisionLearningBindingError(DdoLineageError):
    """Fail-closed join resolver error. Not trading authority."""

    def __init__(self, failure_code: str, detail: str = "") -> None:
        message = f"{failure_code}:{detail}" if detail else failure_code
        super().__init__(message)
        self.failure_code = failure_code


@dataclass(frozen=True)
class CurrentDoublePlayDecisionBundleV1:
    """Resolved current Double-Play decision learning bundle."""

    decision_event_ref: str
    observation_ref: str
    input_evidence_ref: str | None
    authoritative_decision_outcome: str
    producer_canonical_payload: Mapping[str, Any]
    instrument_id: str
    trading_epoch: int
    policy_decision_id: str
    semantic_digest: str
    input_digest: str
    composition_result_ref: str
    policy_version: str


def records_index_from_sequence_v1(
    records: Mapping[str, Mapping[str, Any]] | tuple[Mapping[str, Any], ...],
) -> dict[str, dict[str, Any]]:
    if isinstance(records, Mapping):
        return {str(k): dict(v) for k, v in records.items()}
    out: dict[str, dict[str, Any]] = {}
    for row in records:
        record_id = row.get("record_id")
        if not isinstance(record_id, str) or not record_id:
            raise CurrentDecisionLearningBindingError("RECORD_ID_MISSING")
        if record_id in out:
            raise CurrentDecisionLearningBindingError("DUPLICATE_RECORD_ID", detail=record_id)
        out[record_id] = dict(row)
    return out


def _semantic_digest_from_canonical_payload(payload: Mapping[str, Any]) -> str:
    canonical = {key: payload[key] for key in PRODUCER_CANONICAL_KEYS}
    raw = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _require_canonical_payload(observation: Mapping[str, Any]) -> dict[str, Any]:
    status = observation.get("projection_status")
    if status == UNAVAILABLE_PROJECTION_STATUS:
        raise CurrentDecisionLearningBindingError("SIBLING_OBSERVATION_UNAVAILABLE")
    if status != TYPED_PROJECTION_STATUS:
        raise CurrentDecisionLearningBindingError(
            "SIBLING_OBSERVATION_PROJECTION_STATUS_INVALID", detail=str(status)
        )
    payload_raw = observation.get("producer_canonical_payload")
    if not isinstance(payload_raw, dict):
        raise CurrentDecisionLearningBindingError("PRODUCER_CANONICAL_PAYLOAD_MISSING")
    payload = dict(payload_raw)
    missing = [key for key in PRODUCER_CANONICAL_KEYS if key not in payload]
    if missing:
        raise CurrentDecisionLearningBindingError(
            "PRODUCER_CANONICAL_KEYS_MISSING", detail=",".join(missing)
        )
    return payload


def _verify_observation_integrity(
    observation: Mapping[str, Any], payload: Mapping[str, Any]
) -> None:
    digest = observation.get("semantic_digest")
    if not isinstance(digest, str) or not digest:
        raise CurrentDecisionLearningBindingError("SEMANTIC_DIGEST_MISSING")
    expected = _semantic_digest_from_canonical_payload(payload)
    if digest != expected:
        raise CurrentDecisionLearningBindingError("SEMANTIC_DIGEST_MISMATCH")
    input_digest = payload.get("input_digest")
    if not isinstance(input_digest, str) or not input_digest:
        raise CurrentDecisionLearningBindingError("INPUT_DIGEST_MISSING_IN_PAYLOAD")


def _select_input_evidence(
    *,
    candidates: list[dict[str, Any]],
    observation_ref: str,
) -> dict[str, Any] | None:
    if not candidates:
        return None
    linked = [
        row for row in candidates if row.get("typed_output_observation_ref") == observation_ref
    ]
    if len(linked) > 1:
        raise CurrentDecisionLearningBindingError("SIBLING_INPUT_EVIDENCE_AMBIGUOUS")
    if len(linked) == 1:
        return linked[0]
    if len(candidates) == 1:
        only = candidates[0]
        ref = only.get("typed_output_observation_ref")
        if ref is not None and ref != observation_ref:
            raise CurrentDecisionLearningBindingError("INPUT_OBSERVATION_REF_MISMATCH")
        return only
    raise CurrentDecisionLearningBindingError("SIBLING_INPUT_EVIDENCE_AMBIGUOUS")


def _verify_input_integrity(
    *,
    input_evidence: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> None:
    status = input_evidence.get("projection_status")
    if status == INPUT_UNAVAILABLE_STATUS:
        raise CurrentDecisionLearningBindingError("SIBLING_INPUT_EVIDENCE_UNAVAILABLE")
    if status != INPUT_TYPED_STATUS:
        raise CurrentDecisionLearningBindingError(
            "SIBLING_INPUT_EVIDENCE_PROJECTION_STATUS_INVALID", detail=str(status)
        )
    digest_payload = input_evidence.get("producer_digest_canonical_payload")
    if not isinstance(digest_payload, dict):
        raise CurrentDecisionLearningBindingError("PRODUCER_DIGEST_CANONICAL_PAYLOAD_MISSING")
    reproduced = compute_producer_input_digest_from_canonical_payload_v1(digest_payload)
    stored = input_evidence.get("producer_input_digest")
    if not isinstance(stored, str) or not stored:
        raise CurrentDecisionLearningBindingError("PRODUCER_INPUT_DIGEST_MISSING")
    if reproduced != stored:
        raise CurrentDecisionLearningBindingError("PRODUCER_INPUT_DIGEST_MISMATCH")
    if str(payload.get("input_digest")) != stored:
        raise CurrentDecisionLearningBindingError("INPUT_DIGEST_CROSS_RECORD_MISMATCH")
    comp_ref = str(digest_payload.get("composition_result_ref", ""))
    comp_digest = str(digest_payload.get("composition_semantic_digest", ""))
    if comp_ref and str(payload.get("composition_result_ref")) != comp_ref:
        raise CurrentDecisionLearningBindingError("COMPOSITION_RESULT_REF_MISMATCH")
    if comp_digest and comp_ref:
        # composition_semantic_digest is validated at capture time on input evidence;
        # cross-check ref alignment only (digest scope is pre-decision).
        pass


def resolve_current_double_play_decision_bundle_v1(
    *,
    records_by_id: Mapping[str, Mapping[str, Any]],
    decision_event_ref: str,
) -> CurrentDoublePlayDecisionBundleV1:
    """Fail-closed join of DecisionEvent + typed DP observation (+ optional input)."""
    if decision_event_ref not in records_by_id:
        raise CurrentDecisionLearningBindingError("DECISION_EVENT_NOT_FOUND", decision_event_ref)
    decision_raw = records_by_id[decision_event_ref]
    decision = validate_decision_event_v0(decision_raw)
    if decision["schema_name"] != SCHEMA_NAME_DECISION_EVENT:
        raise CurrentDecisionLearningBindingError("DECISION_EVENT_SCHEMA_REQUIRED")

    observations = [
        dict(row)
        for row in records_by_id.values()
        if row.get("schema_name") == SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION
        and row.get("decision_event_ref") == decision_event_ref
    ]
    if not observations:
        raise CurrentDecisionLearningBindingError("SIBLING_OBSERVATION_ABSENT")
    if len(observations) > 1:
        raise CurrentDecisionLearningBindingError("SIBLING_OBSERVATION_AMBIGUOUS")

    observation = validate_double_play_entry_exit_observation_v1(observations[0])
    payload = _require_canonical_payload(observation)
    _verify_observation_integrity(observation, payload)

    decision_outcome = payload.get("decision_outcome")
    if not isinstance(decision_outcome, str) or not decision_outcome:
        raise CurrentDecisionLearningBindingError("AUTHORITATIVE_DECISION_OUTCOME_MISSING")

    input_candidates = [
        dict(row)
        for row in records_by_id.values()
        if row.get("schema_name") == SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE
        and row.get("decision_event_ref") == decision_event_ref
    ]
    input_row = _select_input_evidence(
        candidates=input_candidates,
        observation_ref=str(observation["record_id"]),
    )
    input_ref: str | None = None
    if input_row is not None:
        input_evidence = validate_double_play_entry_exit_policy_input_evidence_v1(input_row)
        input_ref = str(input_evidence["record_id"])
        _verify_input_integrity(input_evidence=input_evidence, payload=payload)

    return CurrentDoublePlayDecisionBundleV1(
        decision_event_ref=decision_event_ref,
        observation_ref=str(observation["record_id"]),
        input_evidence_ref=input_ref,
        authoritative_decision_outcome=str(decision_outcome),
        producer_canonical_payload=dict(payload),
        instrument_id=str(payload["instrument_id"]),
        trading_epoch=int(payload["trading_epoch"]),
        policy_decision_id=str(payload["policy_decision_id"]),
        semantic_digest=str(observation["semantic_digest"]),
        input_digest=str(payload["input_digest"]),
        composition_result_ref=str(payload["composition_result_ref"]),
        policy_version=str(payload["policy_version"]),
    )
