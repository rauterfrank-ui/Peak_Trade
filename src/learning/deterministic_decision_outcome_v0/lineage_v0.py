"""Referential lineage and supersession/correction checks for DDO v0."""

from __future__ import annotations

from typing import Any, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_DECISION_EVENT,
    SCHEMA_NAME_INCIDENT_RECORD,
    SCHEMA_NAME_OUTCOME_RECORD,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoLineageError

_MAX_LINEAGE_WALK = 1024


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
    if schema_name == SCHEMA_NAME_OUTCOME_RECORD:
        decision_id = record.get("decision_event_ref")
        if decision_id not in existing_by_id:
            raise DdoLineageError(f"OUTCOME_DECISION_REF_MISSING:{decision_id}")
        if existing_by_id[decision_id].get("schema_name") != SCHEMA_NAME_DECISION_EVENT:
            raise DdoLineageError("OUTCOME_DECISION_REF_NOT_DECISION_EVENT")
        incident_id = record.get("incident_record_ref")
        if incident_id is not None:
            if incident_id not in existing_by_id:
                raise DdoLineageError(f"OUTCOME_INCIDENT_REF_MISSING:{incident_id}")
            if existing_by_id[incident_id].get("schema_name") != SCHEMA_NAME_INCIDENT_RECORD:
                raise DdoLineageError("OUTCOME_INCIDENT_REF_NOT_INCIDENT_RECORD")
    if schema_name == SCHEMA_NAME_INCIDENT_RECORD:
        decision_id = record.get("decision_event_ref")
        if decision_id is not None:
            if decision_id not in existing_by_id:
                raise DdoLineageError(f"INCIDENT_DECISION_REF_MISSING:{decision_id}")
            if existing_by_id[decision_id].get("schema_name") != SCHEMA_NAME_DECISION_EVENT:
                raise DdoLineageError("INCIDENT_DECISION_REF_NOT_DECISION_EVENT")
    expected = record.get("expected_outcome_ref")
    if isinstance(expected, Mapping) and expected.get("link_status") == "PRESENT":
        outcome_id = expected.get("outcome_record_id")
        if outcome_id not in existing_by_id:
            raise DdoLineageError(f"EXPECTED_OUTCOME_REF_MISSING:{outcome_id}")
        if existing_by_id[outcome_id].get("schema_name") != SCHEMA_NAME_OUTCOME_RECORD:
            raise DdoLineageError("EXPECTED_OUTCOME_REF_NOT_OUTCOME_RECORD")
