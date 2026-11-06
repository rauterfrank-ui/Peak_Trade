"""Typed canonical decision runtime config models for Cap 6.3."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonical_digest_v1(payload: Mapping[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256_hex(body)


@dataclass(frozen=True)
class CanonicalDecisionRuntimeConfigV1:
    """Single typed owner for in-scope decision runtime distances/epochs."""

    config_version: str
    schema_version: str
    confirmation_epochs: int
    up_distance: float
    adverse_exit_distance: float
    reversal_distance: float
    owner: str
    source_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "config_version": self.config_version,
            "schema_version": self.schema_version,
            "confirmation_epochs": int(self.confirmation_epochs),
            "up_distance": float(self.up_distance),
            "adverse_exit_distance": float(self.adverse_exit_distance),
            "reversal_distance": float(self.reversal_distance),
            "owner": self.owner,
            "source_path": self.source_path,
        }

    def values_payload(self) -> dict[str, Any]:
        return {
            "config_version": self.config_version,
            "schema_version": self.schema_version,
            "confirmation_epochs": int(self.confirmation_epochs),
            "up_distance": float(self.up_distance),
            "adverse_exit_distance": float(self.adverse_exit_distance),
            "reversal_distance": float(self.reversal_distance),
            "owner": self.owner,
        }

    def config_digest(self) -> str:
        return canonical_digest_v1(self.values_payload())


@dataclass
class DecisionConfigBindingStateV1:
    """Persisted Cap 6.3 config binding for restart / mismatch fail-closed."""

    state_version: str
    config_version: str
    schema_version: str
    config_digest: str
    confirmation_epochs: int
    up_distance: float
    adverse_exit_distance: float
    reversal_distance: float
    owner: str
    repository_sha: str
    predecessor_capability: str
    predecessor_config_digest_cap61: str
    predecessor_config_digest_cap62: str
    commit_sequence: int = 0
    source_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DecisionConfigBindingStateV1":
        return cls(
            state_version=str(payload["state_version"]),
            config_version=str(payload["config_version"]),
            schema_version=str(payload["schema_version"]),
            config_digest=str(payload["config_digest"]),
            confirmation_epochs=int(payload["confirmation_epochs"]),
            up_distance=float(payload["up_distance"]),
            adverse_exit_distance=float(payload["adverse_exit_distance"]),
            reversal_distance=float(payload["reversal_distance"]),
            owner=str(payload["owner"]),
            repository_sha=str(payload.get("repository_sha") or ""),
            predecessor_capability=str(payload.get("predecessor_capability") or ""),
            predecessor_config_digest_cap61=str(
                payload.get("predecessor_config_digest_cap61") or ""
            ),
            predecessor_config_digest_cap62=str(
                payload.get("predecessor_config_digest_cap62") or ""
            ),
            commit_sequence=int(payload.get("commit_sequence") or 0),
            source_path=str(payload.get("source_path") or ""),
        )

    def state_digest(self) -> str:
        return canonical_digest_v1(self.to_dict())


@dataclass
class DecisionConfigOwnershipEvidenceV1:
    ok: bool
    capability_id: str
    repository_sha: str
    config_version: str
    config_digest: str
    claims: dict[str, Any] = field(default_factory=dict)
    authority_matrix: list[dict[str, Any]] = field(default_factory=list)
    consumer_trace: list[dict[str, Any]] = field(default_factory=list)
    effective_values_before: dict[str, Any] = field(default_factory=dict)
    effective_values_after: dict[str, Any] = field(default_factory=dict)
    parity_results: dict[str, Any] = field(default_factory=dict)
    restart_results: dict[str, Any] = field(default_factory=dict)
    failure_injection_results: dict[str, Any] = field(default_factory=dict)
    call_graph_before: list[str] = field(default_factory=list)
    call_graph_after: list[str] = field(default_factory=list)
    ownership_graph_before: list[str] = field(default_factory=list)
    ownership_graph_after: list[str] = field(default_factory=list)
    predecessor_digests: dict[str, str] = field(default_factory=dict)
    evidence_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "ok": self.ok,
            "capability_id": self.capability_id,
            "repository_sha": self.repository_sha,
            "config_version": self.config_version,
            "config_digest": self.config_digest,
            "claims": dict(self.claims),
            "authority_matrix": list(self.authority_matrix),
            "consumer_trace": list(self.consumer_trace),
            "effective_values_before": dict(self.effective_values_before),
            "effective_values_after": dict(self.effective_values_after),
            "parity_results": dict(self.parity_results),
            "restart_results": dict(self.restart_results),
            "failure_injection_results": dict(self.failure_injection_results),
            "call_graph_before": list(self.call_graph_before),
            "call_graph_after": list(self.call_graph_after),
            "ownership_graph_before": list(self.ownership_graph_before),
            "ownership_graph_after": list(self.ownership_graph_after),
            "predecessor_digests": dict(self.predecessor_digests),
        }
        payload["evidence_digest"] = canonical_digest_v1(payload)
        self.evidence_digest = payload["evidence_digest"]
        return payload
