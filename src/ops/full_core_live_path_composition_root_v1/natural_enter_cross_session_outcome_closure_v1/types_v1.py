"""Typed records for pending Natural-Enter outcomes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class NaturalEnterPendingOutcomeRecordV1:
    schema_version: str
    pending_outcome_id: str
    decision_event_ref: str
    dpo_ref: str
    decision_id: str
    correlation_id: str
    cycle_id: str
    source_run_id: str
    source_session_id: str
    source_evidence_root: str
    canonical_instrument_id: str
    native_id: str
    side: str
    decision_timestamp_unix: float
    decision_reference_price: float
    market_context_ref: str
    n_bars_required: int
    bars_observed: int
    finalized_bar_identities: tuple[str, ...]
    status: str
    created_at_utc: str
    updated_at_utc: str
    closure_refs: Mapping[str, str] = field(default_factory=dict)
    failure_reason: str = ""

    def to_index_dict_v1(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "pending_outcome_id": self.pending_outcome_id,
            "decision_event_ref": self.decision_event_ref,
            "dpo_ref": self.dpo_ref,
            "decision_id": self.decision_id,
            "correlation_id": self.correlation_id,
            "cycle_id": self.cycle_id,
            "source_run_id": self.source_run_id,
            "source_session_id": self.source_session_id,
            "source_evidence_root": self.source_evidence_root,
            "canonical_instrument_id": self.canonical_instrument_id,
            "native_id": self.native_id,
            "side": self.side,
            "decision_timestamp_unix": self.decision_timestamp_unix,
            "decision_reference_price": self.decision_reference_price,
            "market_context_ref": self.market_context_ref,
            "n_bars_required": self.n_bars_required,
            "bars_observed": self.bars_observed,
            "finalized_bar_identities": list(self.finalized_bar_identities),
            "status": self.status,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
            "closure_refs": dict(self.closure_refs),
            "failure_reason": self.failure_reason,
        }

    @classmethod
    def from_index_dict_v1(cls, raw: Mapping[str, Any]) -> NaturalEnterPendingOutcomeRecordV1:
        identities = raw.get("finalized_bar_identities") or []
        closure = raw.get("closure_refs") or {}
        return cls(
            schema_version=str(raw.get("schema_version") or ""),
            pending_outcome_id=str(raw.get("pending_outcome_id") or ""),
            decision_event_ref=str(raw.get("decision_event_ref") or ""),
            dpo_ref=str(raw.get("dpo_ref") or ""),
            decision_id=str(raw.get("decision_id") or ""),
            correlation_id=str(raw.get("correlation_id") or ""),
            cycle_id=str(raw.get("cycle_id") or ""),
            source_run_id=str(raw.get("source_run_id") or ""),
            source_session_id=str(raw.get("source_session_id") or ""),
            source_evidence_root=str(raw.get("source_evidence_root") or ""),
            canonical_instrument_id=str(raw.get("canonical_instrument_id") or ""),
            native_id=str(raw.get("native_id") or ""),
            side=str(raw.get("side") or ""),
            decision_timestamp_unix=float(raw.get("decision_timestamp_unix") or 0.0),
            decision_reference_price=float(raw.get("decision_reference_price") or 0.0),
            market_context_ref=str(raw.get("market_context_ref") or ""),
            n_bars_required=int(raw.get("n_bars_required") or 2),
            bars_observed=int(raw.get("bars_observed") or 0),
            finalized_bar_identities=tuple(str(x) for x in identities),
            status=str(raw.get("status") or ""),
            created_at_utc=str(raw.get("created_at_utc") or ""),
            updated_at_utc=str(raw.get("updated_at_utc") or ""),
            closure_refs={str(k): str(v) for k, v in dict(closure).items()},
            failure_reason=str(raw.get("failure_reason") or ""),
        )
