"""Models for Cap 7.1 actionability evidence (no decision authority)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_digest_v1(payload: Mapping[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256_hex(body.encode("utf-8"))


@dataclass
class ActionabilityEvidenceV1:
    ok: bool
    capability_id: str
    repository_sha: str
    config_digest: str
    claims: dict[str, Any]
    authority_matrix: list[dict[str, Any]]
    call_graph: list[str]
    parity_results: dict[str, Any]
    lifecycle_results: dict[str, Any]
    restart_results: dict[str, Any]
    failure_injection_results: dict[str, Any]
    metrics: dict[str, Any]
    evidence_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "ok": bool(self.ok),
            "capability_id": self.capability_id,
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "claims": dict(self.claims),
            "authority_matrix": list(self.authority_matrix),
            "call_graph": list(self.call_graph),
            "parity_results": dict(self.parity_results),
            "lifecycle_results": dict(self.lifecycle_results),
            "restart_results": dict(self.restart_results),
            "failure_injection_results": dict(self.failure_injection_results),
            "metrics": dict(self.metrics),
        }
        payload["evidence_digest"] = canonical_digest_v1(payload)
        self.evidence_digest = payload["evidence_digest"]
        return payload


@dataclass
class CycleTraceRowV1:
    cycle_index: int
    mid_price: float
    event_ts_unix: float
    decision_outcome: str
    intended_side: str
    intended_quantity: str
    intent_action: str
    reason_codes: list[str]
    fill_id: str | None
    fill_side: str | None
    fill_quantity: str | None
    fee: str | None
    slippage_cost: str | None
    position_side: str
    venue_flat: bool
    confirmation_phase: str
    observation_classification: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_index": self.cycle_index,
            "mid_price": self.mid_price,
            "event_ts_unix": self.event_ts_unix,
            "decision_outcome": self.decision_outcome,
            "intended_side": self.intended_side,
            "intended_quantity": self.intended_quantity,
            "intent_action": self.intent_action,
            "reason_codes": list(self.reason_codes),
            "fill_id": self.fill_id,
            "fill_side": self.fill_side,
            "fill_quantity": self.fill_quantity,
            "fee": self.fee,
            "slippage_cost": self.slippage_cost,
            "position_side": self.position_side,
            "venue_flat": self.venue_flat,
            "confirmation_phase": self.confirmation_phase,
            "observation_classification": self.observation_classification,
        }


@dataclass
class LifecycleRunResultV1:
    name: str
    ok: bool
    rows: list[CycleTraceRowV1] = field(default_factory=list)
    fills: list[dict[str, Any]] = field(default_factory=list)
    intents: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    claims: dict[str, Any] = field(default_factory=dict)
    portfolio_snapshot: dict[str, Any] = field(default_factory=dict)
    accounting_snapshot: dict[str, Any] = field(default_factory=dict)
    digests: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ok": bool(self.ok),
            "rows": [r.to_dict() for r in self.rows],
            "fills": list(self.fills),
            "intents": list(self.intents),
            "metrics": dict(self.metrics),
            "claims": dict(self.claims),
            "portfolio_snapshot": dict(self.portfolio_snapshot),
            "accounting_snapshot": dict(self.accounting_snapshot),
            "digests": dict(self.digests),
        }
