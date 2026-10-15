"""Shared GHOSV DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Tuple


class GhosvEvidenceKind(str, Enum):
    EXECUTION_ATTEMPT = "EXECUTION_ATTEMPT"
    ORDER_ENVELOPE = "ORDER_ENVELOPE"
    ORDER_ACK = "ORDER_ACK"
    ORDER_REJECT = "ORDER_REJECT"
    ORDER_STATUS = "ORDER_STATUS"
    PARTIAL_FILL = "PARTIAL_FILL"
    FULL_FILL = "FULL_FILL"
    FILL = "FILL"
    POSITION_SNAPSHOT = "POSITION_SNAPSHOT"
    RECONCILIATION_GATE = "RECONCILIATION_GATE"
    PRE_EXTERNAL_REPORT = "PRE_EXTERNAL_REPORT"
    RUNTIME_OBSERVATION = "RUNTIME_OBSERVATION"


class GhosvCompleteness(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class GhosvEvidenceRecordV1:
    """Read-only normalized evidence unit for GHOSV processing."""

    event_id: str
    kind: str
    source_module: str
    source_contract: str
    trade_id: str
    instrument_id: str
    client_order_id: str
    exchange_order_id: str
    fill_id: str
    observation_timestamp: str
    source_timestamp: str
    correlation_context: str
    completeness: str
    payload_ref: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    source_provenance: str = ""


@dataclass(frozen=True)
class GhosvCorrelationGroupV1:
    trade_id: str
    instrument_id: str
    client_order_id: str
    exchange_order_id: str
    status: str
    record_event_ids: Tuple[str, ...]
    reason_codes: Tuple[str, ...]


@dataclass(frozen=True)
class GhosvIntegrityFindingV1:
    check_id: str
    outcome: str
    traffic: str
    reason: str
    evidence_refs: Tuple[str, ...]


@dataclass(frozen=True)
class GhosvCriticalIncidentV1:
    incident_id: str
    incident_type: str
    severity: str
    trade_id: str
    instrument_id: str
    order_id: str
    evidence_refs: Tuple[str, ...]
    detected_at: str
    source_provenance: str
    semantic_reason: str
    correlation_status: str


@dataclass(frozen=True)
class GhosvSafetyAdapterDecisionV1:
    adapter_mode: str
    safety_escalation_enabled: bool
    incident_accepted: bool
    delivery_attempted: bool
    productive_side_effects: bool
    reason_codes: Tuple[str, ...]
    planned_handoff: str


@dataclass(frozen=True)
class GhosvSafetyResponseWitnessV1:
    incident_id: str
    incident_created: bool
    incident_delivery_attempted: bool
    incident_accepted: bool
    safety_state_persisted: bool
    admission_denied: bool
    venue_cancel_requested: bool
    venue_cancel_acknowledged: bool
    venue_order_closed: bool
    fill_already_executed: bool
    unknown: bool
    notes: Tuple[str, ...]


@dataclass(frozen=True)
class GhosvBoundedContextResultV1:
    package_id: str
    schema_version: str
    traffic_overall: str
    traffic_by_trade: Tuple[Tuple[str, str], ...]
    findings: Tuple[GhosvIntegrityFindingV1, ...]
    incidents: Tuple[GhosvCriticalIncidentV1, ...]
    correlation_groups: Tuple[GhosvCorrelationGroupV1, ...]
    adapter_decision: GhosvSafetyAdapterDecisionV1
    witness: Optional[GhosvSafetyResponseWitnessV1]
    dedupe_keys: Tuple[str, ...]
