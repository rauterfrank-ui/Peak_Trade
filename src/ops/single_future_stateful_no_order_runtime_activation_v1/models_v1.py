"""Typed activation / runtime-mode models for Cap 7.2."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_digest_v1(payload: Mapping[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256_hex(body.encode("utf-8"))


class RuntimeModeV1(str, Enum):
    """Sole canonical runtime-mode source for Cap 7.2 no-order activation."""

    INTERNAL_SIMULATED_EXECUTION_PUBLIC_MD_CAPABLE_NO_ORDER = (
        "INTERNAL_SIMULATED_EXECUTION_PUBLIC_MD_CAPABLE_NO_ORDER"
    )


class ActivationStatusV1(str, Enum):
    INACTIVE = "INACTIVE"
    READY_FOR_ACTIVATION = "READY_FOR_ACTIVATION"
    ACTIVE = "ACTIVE"
    ROLLBACK_INACTIVE = "ROLLBACK_INACTIVE"


@dataclass(frozen=True)
class ActivationConfigV1:
    schema_version: str
    capability_id: str
    runtime_mode: RuntimeModeV1
    repository_sha_bound: str
    config_digest: str
    stateful_runtime_ready_for_activation: bool
    full_canonical_stateful_runtime_active: bool
    simulated_execution_active: bool
    public_md_runtime_capable: bool
    public_md_network_session_observed: bool
    live_orders: bool
    testnet_orders: bool
    paper_exchange_orders: bool
    exchange_credential_use: bool
    real_capital_movement: bool
    multi_future_runtime_authorized: bool
    network_allowlist: str
    http_method_allowlist: str
    predecessor_capability_id: str
    predecessor_merge_sha: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "capability_id": self.capability_id,
            "runtime_mode": self.runtime_mode.value,
            "repository_sha_bound": self.repository_sha_bound,
            "config_digest": self.config_digest,
            "STATEFUL_RUNTIME_READY_FOR_ACTIVATION": self.stateful_runtime_ready_for_activation,
            "FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE": self.full_canonical_stateful_runtime_active,
            "SIMULATED_EXECUTION_ACTIVE": self.simulated_execution_active,
            "PUBLIC_MD_RUNTIME_CAPABLE": self.public_md_runtime_capable,
            "PUBLIC_MD_NETWORK_SESSION_OBSERVED": self.public_md_network_session_observed,
            "LIVE_ORDERS": self.live_orders,
            "TESTNET_ORDERS": self.testnet_orders,
            "PAPER_EXCHANGE_ORDERS": self.paper_exchange_orders,
            "EXCHANGE_CREDENTIAL_USE": self.exchange_credential_use,
            "REAL_CAPITAL_MOVEMENT": self.real_capital_movement,
            "MULTI_FUTURE_RUNTIME_AUTHORIZED": self.multi_future_runtime_authorized,
            "NETWORK_ALLOWLIST": self.network_allowlist,
            "HTTP_METHOD_ALLOWLIST": self.http_method_allowlist,
            "predecessor_capability_id": self.predecessor_capability_id,
            "predecessor_merge_sha": self.predecessor_merge_sha,
        }


@dataclass
class CanonicalActivationStateV1:
    state_version: str
    status: ActivationStatusV1
    runtime_mode: RuntimeModeV1
    repository_sha: str
    config_digest: str
    instrument_id: str
    writer_identity: str
    commit_sequence: int
    stateful_runtime_ready_for_activation: bool
    full_canonical_stateful_runtime_active: bool
    simulated_execution_active: bool
    public_md_runtime_capable: bool
    public_md_network_session_observed: bool
    alpha_blocked: bool
    alpha_block_reason: str
    exit_risk_safety_state_preserved: bool
    live_orders: bool = False
    testnet_orders: bool = False
    paper_exchange_orders: bool = False
    exchange_credential_use: bool = False
    real_capital_movement: bool = False
    multi_future_runtime_authorized: bool = False
    network_session_started: bool = False
    authorization_consumed: bool = False
    rollback_applied: bool = False
    last_failure_code: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "state_version": self.state_version,
            "status": self.status.value,
            "runtime_mode": self.runtime_mode.value,
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "instrument_id": self.instrument_id,
            "writer_identity": self.writer_identity,
            "commit_sequence": int(self.commit_sequence),
            "STATEFUL_RUNTIME_READY_FOR_ACTIVATION": bool(
                self.stateful_runtime_ready_for_activation
            ),
            "FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE": bool(
                self.full_canonical_stateful_runtime_active
            ),
            "SIMULATED_EXECUTION_ACTIVE": bool(self.simulated_execution_active),
            "PUBLIC_MD_RUNTIME_CAPABLE": bool(self.public_md_runtime_capable),
            "PUBLIC_MD_NETWORK_SESSION_OBSERVED": bool(self.public_md_network_session_observed),
            "ALPHA_BLOCKED": bool(self.alpha_blocked),
            "alpha_block_reason": self.alpha_block_reason,
            "EXIT_RISK_SAFETY_STATE_PRESERVED": bool(self.exit_risk_safety_state_preserved),
            "LIVE_ORDERS": bool(self.live_orders),
            "TESTNET_ORDERS": bool(self.testnet_orders),
            "PAPER_EXCHANGE_ORDERS": bool(self.paper_exchange_orders),
            "EXCHANGE_CREDENTIAL_USE": bool(self.exchange_credential_use),
            "REAL_CAPITAL_MOVEMENT": bool(self.real_capital_movement),
            "MULTI_FUTURE_RUNTIME_AUTHORIZED": bool(self.multi_future_runtime_authorized),
            "NETWORK_SESSION_STARTED": bool(self.network_session_started),
            "AUTHORIZATION_CONSUMED": bool(self.authorization_consumed),
            "rollback_applied": bool(self.rollback_applied),
            "last_failure_code": self.last_failure_code,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> CanonicalActivationStateV1:
        return cls(
            state_version=str(payload["state_version"]),
            status=ActivationStatusV1(str(payload["status"])),
            runtime_mode=RuntimeModeV1(str(payload["runtime_mode"])),
            repository_sha=str(payload["repository_sha"]),
            config_digest=str(payload["config_digest"]),
            instrument_id=str(payload.get("instrument_id") or ""),
            writer_identity=str(payload.get("writer_identity") or ""),
            commit_sequence=int(payload.get("commit_sequence") or 0),
            stateful_runtime_ready_for_activation=bool(
                payload.get("STATEFUL_RUNTIME_READY_FOR_ACTIVATION")
            ),
            full_canonical_stateful_runtime_active=bool(
                payload.get("FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE")
            ),
            simulated_execution_active=bool(payload.get("SIMULATED_EXECUTION_ACTIVE")),
            public_md_runtime_capable=bool(payload.get("PUBLIC_MD_RUNTIME_CAPABLE")),
            public_md_network_session_observed=bool(
                payload.get("PUBLIC_MD_NETWORK_SESSION_OBSERVED")
            ),
            alpha_blocked=bool(payload.get("ALPHA_BLOCKED")),
            alpha_block_reason=str(payload.get("alpha_block_reason") or ""),
            exit_risk_safety_state_preserved=bool(
                payload.get("EXIT_RISK_SAFETY_STATE_PRESERVED", True)
            ),
            live_orders=bool(payload.get("LIVE_ORDERS", False)),
            testnet_orders=bool(payload.get("TESTNET_ORDERS", False)),
            paper_exchange_orders=bool(payload.get("PAPER_EXCHANGE_ORDERS", False)),
            exchange_credential_use=bool(payload.get("EXCHANGE_CREDENTIAL_USE", False)),
            real_capital_movement=bool(payload.get("REAL_CAPITAL_MOVEMENT", False)),
            multi_future_runtime_authorized=bool(
                payload.get("MULTI_FUTURE_RUNTIME_AUTHORIZED", False)
            ),
            network_session_started=bool(payload.get("NETWORK_SESSION_STARTED", False)),
            authorization_consumed=bool(payload.get("AUTHORIZATION_CONSUMED", False)),
            rollback_applied=bool(payload.get("rollback_applied", False)),
            last_failure_code=str(payload.get("last_failure_code") or ""),
        )


@dataclass
class ActivationEvidenceV1:
    ok: bool
    capability_id: str
    repository_sha: str
    config_digest: str
    predecessor_capability_id: str
    predecessor_merge_sha: str
    claims: dict[str, Any]
    precondition_matrix: dict[str, Any]
    authority_matrix: list[dict[str, Any]]
    call_graph_before: list[str]
    call_graph_after: list[str]
    execution_port_proof: dict[str, Any]
    network_credential_proof: dict[str, Any]
    startup_restart_proof: dict[str, Any]
    rollback_proof: dict[str, Any]
    parity_results: dict[str, Any]
    failure_injection_results: dict[str, Any]
    activation_status: dict[str, Any]
    evidence_digest: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "ok": bool(self.ok),
            "capability_id": self.capability_id,
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "predecessor_capability_id": self.predecessor_capability_id,
            "predecessor_merge_sha": self.predecessor_merge_sha,
            "claims": dict(self.claims),
            "precondition_matrix": dict(self.precondition_matrix),
            "authority_matrix": list(self.authority_matrix),
            "call_graph_before": list(self.call_graph_before),
            "call_graph_after": list(self.call_graph_after),
            "execution_port_proof": dict(self.execution_port_proof),
            "network_credential_proof": dict(self.network_credential_proof),
            "startup_restart_proof": dict(self.startup_restart_proof),
            "rollback_proof": dict(self.rollback_proof),
            "parity_results": dict(self.parity_results),
            "failure_injection_results": dict(self.failure_injection_results),
            "activation_status": dict(self.activation_status),
            "notes": list(self.notes),
        }
        payload["evidence_digest"] = canonical_digest_v1(payload)
        self.evidence_digest = payload["evidence_digest"]
        return payload
