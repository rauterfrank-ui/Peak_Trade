"""Referential lineage and supersession/correction checks for DDO v0."""

from __future__ import annotations

from typing import Any, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_ATTRIBUTION_RECORD,
    SCHEMA_NAME_AUTONOMY_CYCLE,
    SCHEMA_NAME_CANDIDATE_ARTIFACT,
    SCHEMA_NAME_COUNTERFACTUAL_RECORD,
    SCHEMA_NAME_DECISION_EVENT,
    SCHEMA_NAME_DEPLOYMENT_RECORD,
    SCHEMA_NAME_DRIFT_OBSERVATION,
    SCHEMA_NAME_HEALTH_SNAPSHOT,
    SCHEMA_NAME_INCIDENT_RECORD,
    SCHEMA_NAME_KNOWN_GOOD_REFERENCE,
    SCHEMA_NAME_LEARNING_HYPOTHESIS,
    SCHEMA_NAME_OUTCOME_RECORD,
    SCHEMA_NAME_PROMOTION_ELIGIBILITY,
    SCHEMA_NAME_PROMOTION_POLICY,
    SCHEMA_NAME_RELEASE_ARTIFACT,
    SCHEMA_NAME_ROLLBACK_RECORD,
    SCHEMA_NAME_VALIDATION_EVIDENCE_PACK,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoLineageError

_MAX_LINEAGE_WALK = 1024

_OPTIONAL_TYPED_REFS: tuple[tuple[str, str], ...] = (
    ("decision_event_ref", SCHEMA_NAME_DECISION_EVENT),
    ("incident_record_ref", SCHEMA_NAME_INCIDENT_RECORD),
    ("outcome_record_ref", SCHEMA_NAME_OUTCOME_RECORD),
    ("hypothesis_ref", SCHEMA_NAME_LEARNING_HYPOTHESIS),
    ("candidate_artifact_ref", SCHEMA_NAME_CANDIDATE_ARTIFACT),
    ("incumbent_artifact_ref", SCHEMA_NAME_CANDIDATE_ARTIFACT),
    ("validation_evidence_pack_ref", SCHEMA_NAME_VALIDATION_EVIDENCE_PACK),
    ("promotion_policy_ref", SCHEMA_NAME_PROMOTION_POLICY),
    ("release_artifact_ref", SCHEMA_NAME_RELEASE_ARTIFACT),
    ("deployment_record_ref", SCHEMA_NAME_DEPLOYMENT_RECORD),
    ("previous_known_good_ref", SCHEMA_NAME_RELEASE_ARTIFACT),
    ("known_good_artifact_ref", SCHEMA_NAME_RELEASE_ARTIFACT),
    ("health_snapshot_ref", SCHEMA_NAME_HEALTH_SNAPSHOT),
    ("claimed_candidate_ref", SCHEMA_NAME_CANDIDATE_ARTIFACT),
    ("known_good_ref", SCHEMA_NAME_KNOWN_GOOD_REFERENCE),
)

_LIST_TYPED_REFS: tuple[tuple[str, str], ...] = (
    ("attribution_refs", SCHEMA_NAME_ATTRIBUTION_RECORD),
    ("counterfactual_refs", SCHEMA_NAME_COUNTERFACTUAL_RECORD),
    ("candidate_refs", SCHEMA_NAME_CANDIDATE_ARTIFACT),
    ("observation_refs", SCHEMA_NAME_DRIFT_OBSERVATION),
)

_REQUIRED_TYPED_REFS: dict[str, tuple[tuple[str, str], ...]] = {
    SCHEMA_NAME_OUTCOME_RECORD: (("decision_event_ref", SCHEMA_NAME_DECISION_EVENT),),
    SCHEMA_NAME_COUNTERFACTUAL_RECORD: (("decision_event_ref", SCHEMA_NAME_DECISION_EVENT),),
    SCHEMA_NAME_CANDIDATE_ARTIFACT: (("hypothesis_ref", SCHEMA_NAME_LEARNING_HYPOTHESIS),),
    SCHEMA_NAME_VALIDATION_EVIDENCE_PACK: (
        ("candidate_artifact_ref", SCHEMA_NAME_CANDIDATE_ARTIFACT),
    ),
    SCHEMA_NAME_PROMOTION_ELIGIBILITY: (
        ("candidate_artifact_ref", SCHEMA_NAME_CANDIDATE_ARTIFACT),
        ("validation_evidence_pack_ref", SCHEMA_NAME_VALIDATION_EVIDENCE_PACK),
        ("promotion_policy_ref", SCHEMA_NAME_PROMOTION_POLICY),
    ),
    SCHEMA_NAME_RELEASE_ARTIFACT: (
        ("candidate_artifact_ref", SCHEMA_NAME_CANDIDATE_ARTIFACT),
        ("validation_evidence_pack_ref", SCHEMA_NAME_VALIDATION_EVIDENCE_PACK),
    ),
    SCHEMA_NAME_DEPLOYMENT_RECORD: (
        ("release_artifact_ref", SCHEMA_NAME_RELEASE_ARTIFACT),
        ("previous_known_good_ref", SCHEMA_NAME_RELEASE_ARTIFACT),
    ),
    SCHEMA_NAME_ROLLBACK_RECORD: (
        ("deployment_record_ref", SCHEMA_NAME_DEPLOYMENT_RECORD),
        ("known_good_artifact_ref", SCHEMA_NAME_RELEASE_ARTIFACT),
    ),
}

_MISSING_CODES: dict[tuple[str, str], str] = {
    (SCHEMA_NAME_OUTCOME_RECORD, "decision_event_ref"): "OUTCOME_DECISION_REF_MISSING",
    (SCHEMA_NAME_OUTCOME_RECORD, "incident_record_ref"): "OUTCOME_INCIDENT_REF_MISSING",
    (SCHEMA_NAME_INCIDENT_RECORD, "decision_event_ref"): "INCIDENT_DECISION_REF_MISSING",
}

_TYPE_CODES: dict[tuple[str, str], str] = {
    (SCHEMA_NAME_OUTCOME_RECORD, "decision_event_ref"): "OUTCOME_DECISION_REF_NOT_DECISION_EVENT",
    (SCHEMA_NAME_OUTCOME_RECORD, "incident_record_ref"): "OUTCOME_INCIDENT_REF_NOT_INCIDENT_RECORD",
    (SCHEMA_NAME_INCIDENT_RECORD, "decision_event_ref"): "INCIDENT_DECISION_REF_NOT_DECISION_EVENT",
}


def _walk_chain(
    start_id: str,
    *,
    field: str,
    records: Mapping[str, Mapping[str, Any]],
) -> None:
    seen: set[str] = set()
    current = start_id
    steps = 0
    while current:
        if current in seen:
            raise DdoLineageError(f"LINEAGE_CYCLE:{field}:{current}")
        seen.add(current)
        steps += 1
        if steps > _MAX_LINEAGE_WALK:
            raise DdoLineageError(f"LINEAGE_WALK_EXCEEDED:{field}")
        record = records.get(current)
        if record is None:
            return
        nxt = record.get(field)
        if not nxt:
            return
        current = str(nxt)


def _require_typed_ref(
    *,
    field: str,
    target: str,
    expected_schema: str,
    existing_by_id: Mapping[str, Mapping[str, Any]],
    missing_code: str,
    type_code: str,
) -> None:
    if target not in existing_by_id:
        raise DdoLineageError(f"{missing_code}:{target}")
    if existing_by_id[target].get("schema_name") != expected_schema:
        raise DdoLineageError(f"{type_code}:{field}:{target}")


def _codes_for(schema_name: str, field: str) -> tuple[str, str]:
    missing = _MISSING_CODES.get((schema_name, field), f"{field.upper()}_MISSING")
    type_code = _TYPE_CODES.get((schema_name, field), f"{field.upper()}_TYPE_MISMATCH")
    return missing, type_code


def validate_record_lineage_v0(
    record: Mapping[str, Any],
    *,
    existing_by_id: Mapping[str, Mapping[str, Any]],
) -> None:
    record_id = str(record["record_id"])
    schema_name = str(record["schema_name"])
    if record_id in existing_by_id:
        return
    for field in ("supersedes_id", "corrects_id"):
        target = record.get(field)
        if target is None:
            continue
        if target == record_id:
            raise DdoLineageError(f"SELF_LINEAGE_FORBIDDEN:{field}")
        if target not in existing_by_id:
            raise DdoLineageError(f"LINEAGE_TARGET_MISSING:{field}:{target}")
        parent = existing_by_id[target]
        if parent.get("schema_name") != schema_name:
            raise DdoLineageError(f"LINEAGE_SCHEMA_MISMATCH:{field}:{target}")
        probe = dict(existing_by_id)
        probe[record_id] = record
        _walk_chain(record_id, field=field, records=probe)
    for parent_id in record.get("causal_parent_ids") or []:
        if parent_id not in existing_by_id:
            raise DdoLineageError(f"CAUSAL_PARENT_MISSING:{parent_id}")
    required_fields = {item[0] for item in _REQUIRED_TYPED_REFS.get(schema_name, ())}
    for field, expected in _REQUIRED_TYPED_REFS.get(schema_name, ()):
        target = record.get(field)
        missing_code, type_code = _codes_for(schema_name, field)
        _require_typed_ref(
            field=field,
            target=str(target),
            expected_schema=expected,
            existing_by_id=existing_by_id,
            missing_code=missing_code,
            type_code=type_code,
        )
    if schema_name == SCHEMA_NAME_ATTRIBUTION_RECORD:
        if record.get("decision_event_ref") is None and record.get("incident_record_ref") is None:
            raise DdoLineageError("ATTRIBUTION_REQUIRES_DECISION_OR_INCIDENT_REF")
    if schema_name == SCHEMA_NAME_AUTONOMY_CYCLE and not record.get("cycle_id"):
        raise DdoLineageError("AUTONOMY_CYCLE_REQUIRES_CYCLE_ID")
    for field, expected in _OPTIONAL_TYPED_REFS:
        if field in required_fields:
            continue
        target = record.get(field)
        if target is None:
            continue
        missing_code, type_code = _codes_for(schema_name, field)
        _require_typed_ref(
            field=field,
            target=str(target),
            expected_schema=expected,
            existing_by_id=existing_by_id,
            missing_code=missing_code,
            type_code=type_code,
        )
    for field, expected in _LIST_TYPED_REFS:
        for target in record.get(field) or []:
            _require_typed_ref(
                field=field,
                target=str(target),
                expected_schema=expected,
                existing_by_id=existing_by_id,
                missing_code=f"{field.upper()}_MISSING",
                type_code=f"{field.upper()}_TYPE_MISMATCH",
            )
    expected = record.get("expected_outcome_ref")
    if isinstance(expected, Mapping) and expected.get("link_status") == "PRESENT":
        outcome_id = expected.get("outcome_record_id")
        _require_typed_ref(
            field="expected_outcome_ref",
            target=str(outcome_id),
            expected_schema=SCHEMA_NAME_OUTCOME_RECORD,
            existing_by_id=existing_by_id,
            missing_code="EXPECTED_OUTCOME_REF_MISSING",
            type_code="EXPECTED_OUTCOME_REF_NOT_OUTCOME_RECORD",
        )
