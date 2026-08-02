"""Durable coordinator models for Cap 6.4 — no parallel decision authority."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonical_digest_v1(payload: Mapping[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256_hex(body)


@dataclass(frozen=True)
class MemberRootRefV1:
    member_id: str
    state_root: str
    owner: str
    state_digest: str
    commit_identity: str = ""
    commit_sequence: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "MemberRootRefV1":
        return cls(
            member_id=str(payload["member_id"]),
            state_root=str(payload["state_root"]),
            owner=str(payload["owner"]),
            state_digest=str(payload["state_digest"]),
            commit_identity=str(payload.get("commit_identity") or ""),
            commit_sequence=int(payload.get("commit_sequence") or 0),
        )


@dataclass
class DecisionPathWalJournalV1:
    """Write-ahead journal for a single versioned multi-record transaction."""

    state_version: str
    transaction_id: str
    idempotency_key: str
    commit_sequence: int
    repository_sha: str
    config_digest: str
    instrument_id: str
    confirmation_session_id: str
    scope_session_id: str
    members: list[MemberRootRefV1]
    confirmation_payload: dict[str, Any]
    dynamic_scope_payload: dict[str, Any]
    decision_config_payload: dict[str, Any]
    accounting_payload: dict[str, Any]
    portfolio_digest: str
    fill_idempotency_key: str
    observation_epoch: int
    phase: str = "PREPARED"
    previous_commit_identity: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "state_version": self.state_version,
            "transaction_id": self.transaction_id,
            "idempotency_key": self.idempotency_key,
            "commit_sequence": int(self.commit_sequence),
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "instrument_id": self.instrument_id,
            "confirmation_session_id": self.confirmation_session_id,
            "scope_session_id": self.scope_session_id,
            "members": [m.to_dict() for m in self.members],
            "confirmation_payload": dict(self.confirmation_payload),
            "dynamic_scope_payload": dict(self.dynamic_scope_payload),
            "decision_config_payload": dict(self.decision_config_payload),
            "accounting_payload": dict(self.accounting_payload),
            "portfolio_digest": self.portfolio_digest,
            "fill_idempotency_key": self.fill_idempotency_key,
            "observation_epoch": int(self.observation_epoch),
            "phase": self.phase,
            "previous_commit_identity": self.previous_commit_identity,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DecisionPathWalJournalV1":
        return cls(
            state_version=str(payload["state_version"]),
            transaction_id=str(payload["transaction_id"]),
            idempotency_key=str(payload["idempotency_key"]),
            commit_sequence=int(payload["commit_sequence"]),
            repository_sha=str(payload["repository_sha"]),
            config_digest=str(payload["config_digest"]),
            instrument_id=str(payload["instrument_id"]),
            confirmation_session_id=str(payload["confirmation_session_id"]),
            scope_session_id=str(payload["scope_session_id"]),
            members=[MemberRootRefV1.from_dict(m) for m in payload.get("members") or []],
            confirmation_payload=dict(payload.get("confirmation_payload") or {}),
            dynamic_scope_payload=dict(payload.get("dynamic_scope_payload") or {}),
            decision_config_payload=dict(payload.get("decision_config_payload") or {}),
            accounting_payload=dict(payload.get("accounting_payload") or {}),
            portfolio_digest=str(payload.get("portfolio_digest") or ""),
            fill_idempotency_key=str(payload.get("fill_idempotency_key") or ""),
            observation_epoch=int(payload.get("observation_epoch") or 0),
            phase=str(payload.get("phase") or "PREPARED"),
            previous_commit_identity=str(payload.get("previous_commit_identity") or ""),
        )

    def journal_digest(self) -> str:
        return canonical_digest_v1(self.to_dict())


@dataclass
class DecisionPathCommitMarkerV1:
    state_version: str
    commit_identity: str
    commit_sequence: int
    transaction_id: str
    idempotency_key: str
    repository_sha: str
    config_digest: str
    instrument_id: str
    member_digests: dict[str, str]
    confirmation_session_id: str
    scope_session_id: str
    observation_epoch: int
    portfolio_digest: str
    fill_idempotency_key: str
    previous_commit_identity: str = ""
    evidence_status: str = "PENDING"

    def to_dict(self) -> dict[str, Any]:
        return {
            "state_version": self.state_version,
            "commit_identity": self.commit_identity,
            "commit_sequence": int(self.commit_sequence),
            "transaction_id": self.transaction_id,
            "idempotency_key": self.idempotency_key,
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "instrument_id": self.instrument_id,
            "member_digests": dict(self.member_digests),
            "confirmation_session_id": self.confirmation_session_id,
            "scope_session_id": self.scope_session_id,
            "observation_epoch": int(self.observation_epoch),
            "portfolio_digest": self.portfolio_digest,
            "fill_idempotency_key": self.fill_idempotency_key,
            "previous_commit_identity": self.previous_commit_identity,
            "evidence_status": self.evidence_status,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DecisionPathCommitMarkerV1":
        return cls(
            state_version=str(payload["state_version"]),
            commit_identity=str(payload["commit_identity"]),
            commit_sequence=int(payload["commit_sequence"]),
            transaction_id=str(payload["transaction_id"]),
            idempotency_key=str(payload["idempotency_key"]),
            repository_sha=str(payload["repository_sha"]),
            config_digest=str(payload["config_digest"]),
            instrument_id=str(payload["instrument_id"]),
            member_digests={
                str(k): str(v) for k, v in dict(payload.get("member_digests") or {}).items()
            },
            confirmation_session_id=str(payload["confirmation_session_id"]),
            scope_session_id=str(payload["scope_session_id"]),
            observation_epoch=int(payload.get("observation_epoch") or 0),
            portfolio_digest=str(payload.get("portfolio_digest") or ""),
            fill_idempotency_key=str(payload.get("fill_idempotency_key") or ""),
            previous_commit_identity=str(payload.get("previous_commit_identity") or ""),
            evidence_status=str(payload.get("evidence_status") or "PENDING"),
        )

    def marker_digest(self) -> str:
        return canonical_digest_v1(self.to_dict())


@dataclass
class PendingEvidenceCursorV1:
    state_version: str
    commit_identity: str
    commit_sequence: int
    idempotency_key: str
    evidence_path: str
    attempts: int = 0
    last_error: str = ""
    status: str = "PENDING"
    materialized_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PendingEvidenceCursorV1":
        return cls(
            state_version=str(payload["state_version"]),
            commit_identity=str(payload["commit_identity"]),
            commit_sequence=int(payload["commit_sequence"]),
            idempotency_key=str(payload["idempotency_key"]),
            evidence_path=str(payload.get("evidence_path") or ""),
            attempts=int(payload.get("attempts") or 0),
            last_error=str(payload.get("last_error") or ""),
            status=str(payload.get("status") or "PENDING"),
            materialized_digest=str(payload.get("materialized_digest") or ""),
        )


@dataclass
class DecisionPathAtomicEvidenceV1:
    ok: bool
    capability_id: str
    repository_sha: str
    atomicity_model: str
    config_digest: str
    claims: dict[str, Any] = field(default_factory=dict)
    state_root_matrix: list[dict[str, Any]] = field(default_factory=list)
    parity_results: dict[str, Any] = field(default_factory=dict)
    restart_results: dict[str, Any] = field(default_factory=dict)
    failure_injection_results: dict[str, Any] = field(default_factory=dict)
    call_graph_before: list[str] = field(default_factory=list)
    call_graph_after: list[str] = field(default_factory=list)
    predecessor_digests: dict[str, str] = field(default_factory=dict)
    transaction_boundary: str = ""
    commit_marker_semantics: str = ""
    recovery_cursor_semantics: str = ""
    writer_fencing_model: str = ""
    idempotency_model: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "ok": self.ok,
            "capability_id": self.capability_id,
            "repository_sha": self.repository_sha,
            "atomicity_model": self.atomicity_model,
            "config_digest": self.config_digest,
            "claims": dict(self.claims),
            "state_root_matrix": list(self.state_root_matrix),
            "parity_results": dict(self.parity_results),
            "restart_results": dict(self.restart_results),
            "failure_injection_results": dict(self.failure_injection_results),
            "call_graph_before": list(self.call_graph_before),
            "call_graph_after": list(self.call_graph_after),
            "predecessor_digests": dict(self.predecessor_digests),
            "transaction_boundary": self.transaction_boundary,
            "commit_marker_semantics": self.commit_marker_semantics,
            "recovery_cursor_semantics": self.recovery_cursor_semantics,
            "writer_fencing_model": self.writer_fencing_model,
            "idempotency_model": self.idempotency_model,
        }
        payload["evidence_digest"] = canonical_digest_v1(payload)
        return payload
