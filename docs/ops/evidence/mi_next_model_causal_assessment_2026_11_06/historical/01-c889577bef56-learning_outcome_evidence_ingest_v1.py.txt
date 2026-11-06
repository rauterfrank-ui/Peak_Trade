"""LEARNING_OUTCOME_EVIDENCE_INGEST_V1 — fail-closed evaluation bundle → learning state."""

from __future__ import annotations

import hashlib
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_ATTRIBUTION_RECORD,
    SCHEMA_NAME_COUNTERFACTUAL_RECORD,
    SCHEMA_NAME_LEARNING_STATE_RECORD,
    SCHEMA_NAME_OUTCOME_RECORD,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_records_v0 import (
    validate_attribution_record_v0,
    validate_counterfactual_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import (
    AppendOnlyDdoLedgerV0,
    AppendResultV0,
)
from src.learning.deterministic_decision_outcome_v0.learning_state_record_v0 import (
    build_learning_state_record_v0,
    validate_learning_state_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.outcome_v0 import validate_outcome_record_v0
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import canonical_json_dumps_v0

INGEST_ID: Final[str] = "peak_trade.learning.ddo.learning_outcome_evidence_ingest_v1"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False


def derive_learning_state_scope_id_v1(
    *, session_id: str, account_identity: str | None = None
) -> str:
    account = account_identity or UNKNOWN
    digest = hashlib.sha256(f"{session_id}|{account}".encode("utf-8")).hexdigest()
    return f"ddo.lscope.{digest[:40]}"


def compute_evaluation_bundle_fingerprint_v1(
    *,
    outcome_content_hash: str,
    attribution_content_hash: str,
    counterfactual_content_hash: str,
) -> str:
    payload = canonical_json_dumps_v0(
        {
            "outcome_content_hash": outcome_content_hash,
            "attribution_content_hash": attribution_content_hash,
            "counterfactual_content_hash": counterfactual_content_hash,
        }
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_evaluation_bundle_for_ingest_v1(
    outcome: Mapping[str, Any],
    attribution: Mapping[str, Any],
    counterfactual: Mapping[str, Any],
) -> dict[str, Any]:
    outcome_rec = validate_outcome_record_v0(outcome)
    attr_rec = validate_attribution_record_v0(attribution)
    cf_rec = validate_counterfactual_record_v0(counterfactual)
    if attr_rec["outcome_record_ref"] != outcome_rec["record_id"]:
        raise DdoValidationError("INGEST_ATTRIBUTION_OUTCOME_REF_MISMATCH")
    if cf_rec.get("outcome_record_ref") not in (None, outcome_rec["record_id"]):
        raise DdoValidationError("INGEST_COUNTERFACTUAL_OUTCOME_REF_MISMATCH")
    if outcome_rec["decision_event_ref"] != attr_rec.get("decision_event_ref"):
        if attr_rec.get("decision_event_ref") is not None:
            raise DdoValidationError("INGEST_DECISION_REF_DIVERGENCE")
    fingerprint = compute_evaluation_bundle_fingerprint_v1(
        outcome_content_hash=str(outcome_rec["content_hash"]),
        attribution_content_hash=str(attr_rec["content_hash"]),
        counterfactual_content_hash=str(cf_rec["content_hash"]),
    )
    return {
        "outcome": dict(outcome_rec),
        "attribution": dict(attr_rec),
        "counterfactual": dict(cf_rec),
        "evaluation_bundle_fingerprint": fingerprint,
    }


def latest_learning_state_for_scope_v1(
    ledger: AppendOnlyDdoLedgerV0,
    *,
    state_scope_id: str,
) -> Mapping[str, Any] | None:
    latest: Mapping[str, Any] | None = None
    latest_version = 0
    for row in ledger.read_all():
        if row.get("schema_name") != SCHEMA_NAME_LEARNING_STATE_RECORD:
            continue
        if str(row.get("state_scope_id")) != state_scope_id:
            continue
        version = int(row["state_version"])
        if version >= latest_version:
            latest_version = version
            latest = row
    return latest


def _derive_next_cycle_economic_score_label_v1(outcome: Mapping[str, Any]) -> str:
    token = outcome.get("economic_score")
    if token is None or token == "":
        return UNKNOWN
    return str(token)


def reduce_learning_state_transition_v1(
    *,
    state_scope_id: str,
    bundle: Mapping[str, Any],
    prior_state: Mapping[str, Any] | None,
    record_id: str,
    event_time_utc: str,
    correlation_id: str,
    cycle_id: str | None,
    code_sha: str = UNKNOWN,
    config_hash: str = UNKNOWN,
) -> dict[str, Any]:
    validated = validate_evaluation_bundle_for_ingest_v1(
        bundle["outcome"],
        bundle["attribution"],
        bundle["counterfactual"],
    )
    outcome = validated["outcome"]
    fingerprint = validated["evaluation_bundle_fingerprint"]
    outcome_time = str(outcome["event_time_utc"])

    if prior_state is not None:
        if str(prior_state.get("evaluation_bundle_fingerprint")) == fingerprint:
            return dict(prior_state)
        prior_time = str(prior_state["last_event_time_utc"])
        if outcome_time < prior_time:
            raise DdoValidationError("LEARNING_INGEST_OUT_OF_ORDER_EVENT_TIME")
        state_version = int(prior_state["state_version"]) + 1
        ingest_sequence = int(prior_state["ingest_sequence"]) + 1
        prior_ref = str(prior_state["record_id"])
    else:
        state_version = 1
        ingest_sequence = 1
        prior_ref = None

    label = _derive_next_cycle_economic_score_label_v1(outcome)
    payload = {
        "schema_name": SCHEMA_NAME_LEARNING_STATE_RECORD,
        "schema_version": "learning_state_record_v0",
        "record_id": record_id,
        "state_scope_id": state_scope_id,
        "state_version": state_version,
        "prior_state_record_ref": prior_ref,
        "evaluation_bundle_fingerprint": fingerprint,
        "outcome_record_ref": outcome["record_id"],
        "attribution_record_ref": validated["attribution"]["record_id"],
        "counterfactual_record_ref": validated["counterfactual"]["record_id"],
        "decision_event_ref": outcome["decision_event_ref"],
        "last_event_time_utc": outcome_time,
        "ingest_sequence": ingest_sequence,
        "next_cycle_economic_score_label": label,
        "last_evaluation_horizon": str(outcome["evaluation_horizon"]),
        "last_actual_outcome_ref": outcome.get("actual_outcome_ref") or UNKNOWN,
        "last_decision_score": outcome.get("decision_score"),
        "last_safety_score": outcome.get("safety_score"),
        "last_economic_score": outcome.get("economic_score"),
        "event_time_utc": event_time_utc,
        "correlation_id": correlation_id,
        "cycle_id": cycle_id,
        "causal_parent_ids": [
            outcome["record_id"],
            validated["attribution"]["record_id"],
            validated["counterfactual"]["record_id"],
            *([prior_ref] if prior_ref else []),
        ],
        "producer_id": INGEST_ID,
        "authority_owner": UNKNOWN,
        "code_sha": code_sha,
        "config_hash": config_hash,
        "evidence_hash": fingerprint,
        "evidence_source_refs": [
            outcome["record_id"],
            validated["attribution"]["record_id"],
            validated["counterfactual"]["record_id"],
        ],
        "productive_authority": "NONE",
        "runtime_reachability": False,
        "can_auto_promote": False,
        "can_mutate_core": False,
        "can_mutate_risk": False,
        "can_mutate_safety": False,
        "can_deploy": False,
    }
    return dict(build_learning_state_record_v0(payload))


def derive_learning_state_record_id_v1(*, state_scope_id: str, fingerprint: str) -> str:
    digest = hashlib.sha256(f"{state_scope_id}|{fingerprint}".encode("utf-8")).hexdigest()
    return f"ls.{digest[:48]}"


def ingest_evaluation_bundle_into_learning_state_v1(
    ledger: AppendOnlyDdoLedgerV0,
    *,
    state_scope_id: str,
    outcome: Mapping[str, Any],
    attribution: Mapping[str, Any],
    counterfactual: Mapping[str, Any],
    event_time_utc: str,
    correlation_id: str,
    cycle_id: str | None = None,
) -> dict[str, Any]:
    bundle = validate_evaluation_bundle_for_ingest_v1(outcome, attribution, counterfactual)
    fingerprint = bundle["evaluation_bundle_fingerprint"]
    prior = latest_learning_state_for_scope_v1(ledger, state_scope_id=state_scope_id)
    record_id = derive_learning_state_record_id_v1(
        state_scope_id=state_scope_id, fingerprint=fingerprint
    )
    if prior is not None and str(prior.get("record_id")) == record_id:
        return {
            "ok": True,
            "idempotent_replay": True,
            "learning_state_record": dict(prior),
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
            "ingest_id": INGEST_ID,
        }
    next_state = reduce_learning_state_transition_v1(
        state_scope_id=state_scope_id,
        bundle={
            "outcome": bundle["outcome"],
            "attribution": bundle["attribution"],
            "counterfactual": bundle["counterfactual"],
        },
        prior_state=prior,
        record_id=record_id,
        event_time_utc=event_time_utc,
        correlation_id=correlation_id,
        cycle_id=cycle_id,
    )
    append_result: AppendResultV0 = ledger.append(next_state)
    status = append_result.status
    stored = validate_learning_state_record_v0(next_state)
    return {
        "ok": True,
        "idempotent_replay": status == "IDEMPOTENT_REPLAY",
        "append_status": status,
        "learning_state_record": dict(stored),
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "ingest_id": INGEST_ID,
    }
