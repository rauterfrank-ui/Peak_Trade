"""Models for Cap 6.5 exit-policy producer binding (no decision authority)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_digest_v1(payload: Mapping[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256_hex(body.encode("utf-8"))


@dataclass(frozen=True)
class ExitPolicySignalEvidenceV1:
    """Evidence that a signal was productively evaluated (not an unbound stub)."""

    exit_class: str
    triggered: bool
    reason_code: str
    evaluation_bound: bool
    producer_owner: str
    inputs_digest: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CanonicalExitPolicyStateV1:
    """Minimal durable exit-policy state for restart continuity."""

    state_version: str
    instrument_id: str
    repository_sha: str
    config_digest: str
    has_open_position: bool
    existing_position_side: str
    entry_price: Optional[float]
    entry_event_time: Optional[float]
    entry_trading_epoch: Optional[int]
    time_exit_max_hold_seconds: float
    pending_exit_class: str
    pending_exit_reason: str
    pending_exit_identity: str
    last_exit_intent_identity: str
    last_observation_digest: str
    last_evaluated_event_time: Optional[float]
    commit_sequence: int
    owner: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "state_version": self.state_version,
            "instrument_id": self.instrument_id,
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "has_open_position": bool(self.has_open_position),
            "existing_position_side": self.existing_position_side,
            "entry_price": self.entry_price,
            "entry_event_time": self.entry_event_time,
            "entry_trading_epoch": self.entry_trading_epoch,
            "time_exit_max_hold_seconds": float(self.time_exit_max_hold_seconds),
            "pending_exit_class": self.pending_exit_class,
            "pending_exit_reason": self.pending_exit_reason,
            "pending_exit_identity": self.pending_exit_identity,
            "last_exit_intent_identity": self.last_exit_intent_identity,
            "last_observation_digest": self.last_observation_digest,
            "last_evaluated_event_time": self.last_evaluated_event_time,
            "commit_sequence": int(self.commit_sequence),
            "owner": self.owner,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CanonicalExitPolicyStateV1":
        return cls(
            state_version=str(payload["state_version"]),
            instrument_id=str(payload["instrument_id"]),
            repository_sha=str(payload["repository_sha"]),
            config_digest=str(payload["config_digest"]),
            has_open_position=bool(payload.get("has_open_position", False)),
            existing_position_side=str(payload.get("existing_position_side") or "none"),
            entry_price=(
                None if payload.get("entry_price") is None else float(payload["entry_price"])
            ),
            entry_event_time=(
                None
                if payload.get("entry_event_time") is None
                else float(payload["entry_event_time"])
            ),
            entry_trading_epoch=(
                None
                if payload.get("entry_trading_epoch") is None
                else int(payload["entry_trading_epoch"])
            ),
            time_exit_max_hold_seconds=float(payload["time_exit_max_hold_seconds"]),
            pending_exit_class=str(payload.get("pending_exit_class") or ""),
            pending_exit_reason=str(payload.get("pending_exit_reason") or ""),
            pending_exit_identity=str(payload.get("pending_exit_identity") or ""),
            last_exit_intent_identity=str(payload.get("last_exit_intent_identity") or ""),
            last_observation_digest=str(payload.get("last_observation_digest") or ""),
            last_evaluated_event_time=(
                None
                if payload.get("last_evaluated_event_time") is None
                else float(payload["last_evaluated_event_time"])
            ),
            commit_sequence=int(payload.get("commit_sequence") or 0),
            owner=str(payload["owner"]),
        )

    def digest(self) -> str:
        return canonical_digest_v1(self.to_dict())


@dataclass
class ExitPolicyProducerBundleV1:
    """Productively evaluated exit signals for one host cycle."""

    scope_adverse_exit: ExitPolicySignalEvidenceV1
    profit_protection: ExitPolicySignalEvidenceV1
    time_exit: ExitPolicySignalEvidenceV1
    strategy_invalidation: ExitPolicySignalEvidenceV1
    hard_risk_reduction: ExitPolicySignalEvidenceV1
    safety_exit: ExitPolicySignalEvidenceV1
    safety_mode: str
    trading_gate: str
    evaluation_bound: bool
    placeholder_false_signal_used_as_unbound_stub: bool
    producers_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope_adverse_exit": self.scope_adverse_exit.to_dict(),
            "profit_protection": self.profit_protection.to_dict(),
            "time_exit": self.time_exit.to_dict(),
            "strategy_invalidation": self.strategy_invalidation.to_dict(),
            "hard_risk_reduction": self.hard_risk_reduction.to_dict(),
            "safety_exit": self.safety_exit.to_dict(),
            "safety_mode": self.safety_mode,
            "trading_gate": self.trading_gate,
            "evaluation_bound": bool(self.evaluation_bound),
            "placeholder_false_signal_used_as_unbound_stub": bool(
                self.placeholder_false_signal_used_as_unbound_stub
            ),
            "producers_digest": self.producers_digest,
        }


@dataclass
class ExitPolicyProducerBindingEvidenceV1:
    ok: bool
    capability_id: str
    repository_sha: str
    config_digest: str
    claims: dict[str, Any]
    authority_matrix: list[dict[str, Any]]
    call_graph_before: list[str]
    call_graph_after: list[str]
    parity_results: dict[str, Any]
    restart_results: dict[str, Any]
    failure_injection_results: dict[str, Any]
    producer_results: dict[str, Any]
    evidence_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "ok": self.ok,
            "capability_id": self.capability_id,
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "claims": dict(self.claims),
            "authority_matrix": list(self.authority_matrix),
            "call_graph_before": list(self.call_graph_before),
            "call_graph_after": list(self.call_graph_after),
            "parity_results": dict(self.parity_results),
            "restart_results": dict(self.restart_results),
            "failure_injection_results": dict(self.failure_injection_results),
            "producer_results": dict(self.producer_results),
        }
        payload["evidence_digest"] = canonical_digest_v1(payload)
        return payload
