"""S05 — critical incident contract."""

from __future__ import annotations

import hashlib
import json
from typing import Sequence

from src.ops.ghosv_bounded_context_v1.constants_v1 import (
    INCIDENT_SEVERITY_CRITICAL,
    INCIDENT_SEVERITY_NONE,
)
from src.ops.ghosv_bounded_context_v1.types_v1 import (
    GhosvCorrelationGroupV1,
    GhosvCriticalIncidentV1,
    GhosvIntegrityFindingV1,
)

INCIDENT_CONTRACT = "ghosv_critical_incident.v1"

_CHECK_TO_INCIDENT = {
    "ORDER_IDENTITY_INTEGRITY": "ORDER_IDENTITY_CONFLICT",
    "DUPLICATE_FILL_INTEGRITY": "CONFIRMED_DUPLICATE_FILL_PROCESSING",
    "FILL_QUANTITY_INTEGRITY": "CONFIRMED_FILL_QUANTITY_VIOLATION",
    "RECONCILIATION_CONSISTENCY": "CONFIRMED_RECONCILIATION_MISMATCH",
    "EXECUTION_STATE_CONSISTENCY": "UNRESOLVED_EXCHANGE_EXECUTION_STATE",
}


def _incident_id(
    incident_type: str, trade_id: str, order_id: str, evidence_refs: tuple[str, ...]
) -> str:
    blob = json.dumps(
        {"type": incident_type, "trade_id": trade_id, "order_id": order_id, "refs": evidence_refs},
        sort_keys=True,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def build_critical_incidents_v1(
    *,
    findings: Sequence[GhosvIntegrityFindingV1],
    groups: Sequence[GhosvCorrelationGroupV1],
    detected_at: str,
) -> tuple[GhosvCriticalIncidentV1, ...]:
    incidents: list[GhosvCriticalIncidentV1] = []
    group_by_trade = {g.trade_id: g for g in groups}
    seen_ids: set[str] = set()
    seen_logical: set[tuple[str, str, str]] = set()

    for finding in findings:
        if finding.traffic != "RED" or finding.outcome != "FAIL":
            continue
        incident_type = _CHECK_TO_INCIDENT.get(finding.check_id, finding.check_id)
        trade_id = ""
        order_id = ""
        correlation_status = "UNKNOWN"
        for g in groups:
            if g.record_event_ids == finding.evidence_refs or any(
                ref in g.record_event_ids for ref in finding.evidence_refs
            ):
                trade_id = g.trade_id
                order_id = g.client_order_id or g.exchange_order_id
                correlation_status = g.status
                break
        if not trade_id and groups:
            trade_id = groups[0].trade_id
            order_id = groups[0].client_order_id or groups[0].exchange_order_id
            correlation_status = groups[0].status
        logical = (incident_type, trade_id, order_id)
        if logical in seen_logical:
            continue
        seen_logical.add(logical)
        iid = _incident_id(incident_type, trade_id, order_id, finding.evidence_refs)
        if iid in seen_ids:
            continue
        seen_ids.add(iid)
        inst = ""
        if trade_id in group_by_trade:
            inst = group_by_trade[trade_id].instrument_id
        elif groups:
            inst = groups[0].instrument_id
        incidents.append(
            GhosvCriticalIncidentV1(
                incident_id=iid,
                incident_type=incident_type,
                severity=INCIDENT_SEVERITY_CRITICAL,
                trade_id=trade_id,
                instrument_id=inst,
                order_id=order_id,
                evidence_refs=finding.evidence_refs,
                detected_at=detected_at,
                source_provenance="ghosv_bounded_context_v1.s05_critical_incident_v1",
                semantic_reason=finding.reason,
                correlation_status=correlation_status,
            )
        )
    return tuple(incidents)


def dedupe_incident_keys_v1(incidents: Sequence[GhosvCriticalIncidentV1]) -> tuple[str, ...]:
    return tuple(i.incident_id for i in incidents)
