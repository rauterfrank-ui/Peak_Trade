"""Deterministic JSON serialization for Landscape V2 projections."""

from __future__ import annotations

import json
from typing import Any

from .contracts import (
    AutonomyStageSnapshotV1,
    CanonicalDecisionSnapshotV1,
    DiagnosticsSummarySnapshotV1,
    DoublePlaySnapshotV1,
    DynamicScopeSnapshotV1,
    EconomicSummarySnapshotV1,
    ExecutionReconciliationSnapshotV1,
    MarketInstrumentSnapshotV1,
    RiskSizingCapitalSnapshotV1,
    SafetyAuthoritySnapshotV1,
    UniverseRankingSnapshotV1,
    projection_envelope_dict,
)
from .source_health import DashboardSourceHealthSnapshotV1


def _base(snapshot: Any) -> dict[str, Any]:
    return projection_envelope_dict(snapshot)


def serialize_projection(snapshot: Any) -> dict[str, Any]:
    if isinstance(snapshot, MarketInstrumentSnapshotV1):
        payload = _base(snapshot)
        payload.update(
            {
                "instrument_id": snapshot.instrument_id,
                "venue": snapshot.venue,
                "market_type": snapshot.market_type,
                "mark_price": snapshot.mark_price,
                "reason_codes": list(snapshot.reason_codes),
            }
        )
        return payload
    if isinstance(snapshot, UniverseRankingSnapshotV1):
        payload = _base(snapshot)
        payload.update(
            {
                "ranking": [dict(row) for row in snapshot.ranking],
                "selected_instrument_id": snapshot.selected_instrument_id,
                "reason_codes": list(snapshot.reason_codes),
            }
        )
        return payload
    if isinstance(snapshot, DynamicScopeSnapshotV1):
        payload = _base(snapshot)
        payload.update(
            {
                "scope_state": snapshot.scope_state,
                "current_scope_ref": snapshot.current_scope_ref,
                "next_scope_ref": snapshot.next_scope_ref,
                "reason_codes": list(snapshot.reason_codes),
            }
        )
        return payload
    if isinstance(snapshot, CanonicalDecisionSnapshotV1):
        payload = _base(snapshot)
        payload.update(
            {
                "instrument_id": snapshot.instrument_id,
                "decision": snapshot.decision,
                "direction": snapshot.direction,
                "reason_codes": list(snapshot.reason_codes),
                "blockers": list(snapshot.blockers),
                "decision_id": snapshot.decision_id,
                "evidence_schema_version": snapshot.evidence_schema_version,
            }
        )
        return payload
    if isinstance(snapshot, DoublePlaySnapshotV1):
        payload = _base(snapshot)
        payload.update(
            {
                "overall_status": snapshot.overall_status,
                "panel_summaries": [dict(row) for row in snapshot.panel_summaries],
                "blockers": list(snapshot.blockers),
                "display_only": snapshot.display_only,
                "live_authorization": snapshot.live_authorization,
            }
        )
        return payload
    if isinstance(snapshot, RiskSizingCapitalSnapshotV1):
        payload = _base(snapshot)
        payload.update(
            {
                "risk_status": snapshot.risk_status,
                "sizing_status": snapshot.sizing_status,
                "capital_status": snapshot.capital_status,
                "reason_codes": list(snapshot.reason_codes),
                "quantity": snapshot.quantity,
            }
        )
        return payload
    if isinstance(snapshot, SafetyAuthoritySnapshotV1):
        payload = _base(snapshot)
        payload.update(
            {
                "kill_switch_state": snapshot.kill_switch_state,
                "veto_active": snapshot.veto_active,
                "reason_codes": list(snapshot.reason_codes),
            }
        )
        return payload
    if isinstance(snapshot, ExecutionReconciliationSnapshotV1):
        payload = _base(snapshot)
        payload.update(
            {
                "execution_status": snapshot.execution_status,
                "reconciliation_status": snapshot.reconciliation_status,
                "order_intent_ref": snapshot.order_intent_ref,
                "reason_codes": list(snapshot.reason_codes),
            }
        )
        return payload
    if isinstance(snapshot, EconomicSummarySnapshotV1):
        payload = _base(snapshot)
        payload.update(
            {
                "economic_gate_status": snapshot.economic_gate_status,
                "evidence_ref": snapshot.evidence_ref,
                "reason_codes": list(snapshot.reason_codes),
            }
        )
        return payload
    if isinstance(snapshot, AutonomyStageSnapshotV1):
        payload = _base(snapshot)
        payload.update(
            {
                "autonomy_stage": snapshot.autonomy_stage,
                "runtime_bridge_status": snapshot.runtime_bridge_status,
                "reason_codes": list(snapshot.reason_codes),
            }
        )
        return payload
    if isinstance(snapshot, DiagnosticsSummarySnapshotV1):
        payload = _base(snapshot)
        payload.update(
            {
                "diagnostic_codes": list(snapshot.diagnostic_codes),
                "summary": snapshot.summary,
                "reason_codes": list(snapshot.reason_codes),
            }
        )
        return payload
    if isinstance(snapshot, DashboardSourceHealthSnapshotV1):
        return snapshot.to_json_dict()
    raise TypeError(f"unsupported snapshot type: {type(snapshot)!r}")


def dumps_projection_canonical(snapshot: Any) -> str:
    """Stable canonical JSON (sorted keys, compact separators)."""
    return json.dumps(
        serialize_projection(snapshot),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
