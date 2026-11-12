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
from src.learning.deterministic_decision_outcome_v0.errors_v0 import (
    DdoDuplicateConflictError,
    DdoValidationError,
)
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
    learning_event_time_key_v0,
    learning_state_head_v0,
)
from src.learning.deterministic_decision_outcome_v0.outcome_v0 import validate_outcome_record_v0
from src.learning.deterministic_decision_outcome_v0.self_learning_provenance_eligibility_v1 import (
    outcome_semantic_class_from_record_v1,
    require_self_learning_provenance_eligibility_v1,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import canonical_json_dumps_v0

INGEST_ID: Final[str] = "peak_trade.learning.ddo.learning_outcome_evidence_ingest_v1"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
_UNBOUND_PREDECESSOR = object()


def derive_learning_state_scope_id_v1(
    *,
    session_id: str,
    account_identity: str | None = None,
    config_hash: str | None = None,
    code_sha: str | None = None,
) -> str:
    account = account_identity or UNKNOWN
    identity = f"{session_id}|{account}"
    if config_hash is not None or code_sha is not None:
        # Explicit versioned pool, including an isolated UNKNOWN/legacy pool.
        identity = canonical_json_dumps_v0(
            {
                "contract": "learning_scope_configuration_v2",
                "session": session_id,
                "account": account,
                "config_hash": config_hash or UNKNOWN,
                "code_sha": code_sha or UNKNOWN,
            }
        )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
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
    require_self_learning_provenance_eligibility_v1(outcome_rec)
    attr_rec = validate_attribution_record_v0(attribution)
    cf_rec = validate_counterfactual_record_v0(counterfactual)
    if any(
        row[field] != outcome_rec[field]
        for row in (attr_rec, cf_rec)
        for field in ("code_sha", "config_hash")
    ):
        raise DdoValidationError("INGEST_BUNDLE_CONFIGURATION_MISMATCH")
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
    return learning_state_head_v0(ledger.read_all(), state_scope_id=state_scope_id)


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
    code_sha: str | None = None,
    config_hash: str | None = None,
) -> dict[str, Any]:
    validated = validate_evaluation_bundle_for_ingest_v1(
        bundle["outcome"],
        bundle["attribution"],
        bundle["counterfactual"],
    )
    outcome = validated["outcome"]
    source_code = str(outcome.get("code_sha") or UNKNOWN)
    source_config = str(outcome.get("config_hash") or UNKNOWN)
    if code_sha is not None and code_sha != source_code:
        raise DdoValidationError("LEARNING_INGEST_SOURCE_CODE_MISMATCH")
    if config_hash is not None and config_hash != source_config:
        raise DdoValidationError("LEARNING_INGEST_SOURCE_CONFIG_MISMATCH")
    code_sha, config_hash = source_code, source_config
    fingerprint = validated["evaluation_bundle_fingerprint"]
    outcome_time = str(outcome["event_time_utc"])
    outcome_time_key = learning_event_time_key_v0(outcome_time)
    prior_class = str(prior_state["outcome_semantic_class"]) if prior_state is not None else None
    eligibility = require_self_learning_provenance_eligibility_v1(
        outcome, prior_outcome_semantic_class=prior_class
    )
    prov_block = outcome.get("outcome_evidence_provenance") or {}
    outcome_scalar_kind = prov_block.get("outcome_scalar_kind")

    if prior_state is not None:
        if prior_state.get("config_hash") != config_hash or prior_state.get("code_sha") != code_sha:
            raise DdoValidationError("LEARNING_INGEST_CONFIGURATION_POOL_MISMATCH")
        if str(prior_state.get("evaluation_bundle_fingerprint")) == fingerprint:
            return dict(prior_state)
        prior_time = str(prior_state["last_event_time_utc"])
        if outcome_time_key < learning_event_time_key_v0(prior_time):
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
        "outcome_semantic_class": eligibility.outcome_semantic_class,
        "outcome_evidence_provenance_digest": eligibility.provenance_digest or UNKNOWN,
        "outcome_evidence_provenance": dict(prov_block) if prov_block else {},
        "outcome_scalar_kind": outcome_scalar_kind,
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


def _ingest_result(record: Mapping[str, Any], status: str) -> dict[str, Any]:
    return {
        "ok": True,
        "idempotent_replay": status == "IDEMPOTENT_REPLAY",
        "append_status": status,
        "learning_state_record": dict(record),
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "ingest_id": INGEST_ID,
    }


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
    expected_prior_state_record_ref: str | None | object = _UNBOUND_PREDECESSOR,
) -> dict[str, Any]:
    bundle = validate_evaluation_bundle_for_ingest_v1(outcome, attribution, counterfactual)
    fingerprint = bundle["evaluation_bundle_fingerprint"]
    record_id = derive_learning_state_record_id_v1(
        state_scope_id=state_scope_id, fingerprint=fingerprint
    )
    records = {row["record_id"]: row for row in ledger.read_all()}
    for role in ("outcome", "attribution", "counterfactual"):
        submitted = bundle[role]
        original = records.get(submitted["record_id"])
        if original is None or original["content_hash"] != submitted["content_hash"]:
            raise DdoValidationError(f"LEARNING_INGEST_ORIGINAL_EVIDENCE_MISMATCH:{role}")
    existing = records.get(record_id)
    if existing is not None:
        if (
            existing["schema_name"] != SCHEMA_NAME_LEARNING_STATE_RECORD
            or existing["state_scope_id"] != state_scope_id
            or existing["evaluation_bundle_fingerprint"] != fingerprint
        ):
            raise DdoDuplicateConflictError(f"DUPLICATE_RECORD_ID_CONFLICT:{record_id}")
        if any(
            existing[field] != bundle["outcome"][field] for field in ("code_sha", "config_hash")
        ):
            raise DdoValidationError("LEARNING_INGEST_CONFIGURATION_POOL_MISMATCH")
        if (
            expected_prior_state_record_ref is not _UNBOUND_PREDECESSOR
            and existing["prior_state_record_ref"] != expected_prior_state_record_ref
        ):
            raise DdoValidationError("LEARNING_STATE_PREDECESSOR_CHANGED")
        return _ingest_result(existing, "IDEMPOTENT_REPLAY")
    prior = learning_state_head_v0(records.values(), state_scope_id=state_scope_id)
    if (
        expected_prior_state_record_ref is not _UNBOUND_PREDECESSOR
        and (prior["record_id"] if prior is not None else None) != expected_prior_state_record_ref
    ):
        raise DdoValidationError("LEARNING_STATE_PREDECESSOR_CHANGED")
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
    return _ingest_result(next_state, append_result.status)
