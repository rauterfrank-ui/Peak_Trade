"""DTOs for Cap 4.1 single-future canonical runtime pre-activation closure."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.constants_v1 import (
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    CAPABILITY_ID,
    OWNER,
    PRODUCER_VERSION,
    RUNTIME_ACTIVATED,
    SCHEMA_VERSION,
)


def canonical_json_dumps(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class PreActivationGateFlagsV1:
    flags: Mapping[str, bool]

    def all_true(self) -> bool:
        return all(bool(v) for v in self.flags.values())

    def false_flags(self) -> tuple[str, ...]:
        return tuple(sorted(k for k, v in self.flags.items() if not bool(v)))

    def to_dict(self) -> dict[str, Any]:
        return {k: bool(v) for k, v in sorted(self.flags.items())}


@dataclass(frozen=True)
class PreActivationEvidenceV1:
    capability_id: str
    schema_version: str
    producer_version: str
    owner: str
    ok: bool
    repository_sha: str
    baseline_sha: str
    config_digest: str
    call_graph_before: tuple[str, ...]
    call_graph_after: tuple[str, ...]
    productive_call_graph_proven: tuple[str, ...]
    gate_flags: Mapping[str, bool]
    effective_config: Mapping[str, Any]
    authority_map: Mapping[str, Any]
    restart_recovery: Mapping[str, Any]
    exit_risk_safety_independence: Mapping[str, Any]
    failure_injection_results: Mapping[str, Any]
    legacy_authority_check: Mapping[str, Any]
    activation_negative: Mapping[str, Any]
    network_order_negative: Mapping[str, Any]
    verification_result: Mapping[str, Any]
    canonical_runtime_entrypoint_status: str = CANONICAL_RUNTIME_ENTRYPOINT_STATUS
    runtime_activated: bool = RUNTIME_ACTIVATED
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "schema_version": self.schema_version,
            "producer_version": self.producer_version,
            "owner": self.owner,
            "ok": self.ok,
            "repository_sha": self.repository_sha,
            "baseline_sha": self.baseline_sha,
            "config_digest": self.config_digest,
            "call_graph_before": list(self.call_graph_before),
            "call_graph_after": list(self.call_graph_after),
            "productive_call_graph_proven": list(self.productive_call_graph_proven),
            "gate_flags": dict(sorted(self.gate_flags.items())),
            "effective_config": dict(self.effective_config),
            "authority_map": dict(self.authority_map),
            "restart_recovery": dict(self.restart_recovery),
            "exit_risk_safety_independence": dict(self.exit_risk_safety_independence),
            "failure_injection_results": dict(self.failure_injection_results),
            "legacy_authority_check": dict(self.legacy_authority_check),
            "activation_negative": dict(self.activation_negative),
            "network_order_negative": dict(self.network_order_negative),
            "verification_result": dict(self.verification_result),
            "CANONICAL_RUNTIME_ENTRYPOINT_STATUS": self.canonical_runtime_entrypoint_status,
            "RUNTIME_ACTIVATED": bool(self.runtime_activated),
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class PreActivationGateResultV1:
    ok: bool
    ready_for_activation: bool
    runtime_activated: bool
    hard_stop: bool
    status: str
    gate_flags: PreActivationGateFlagsV1
    evidence: PreActivationEvidenceV1
    blockers: tuple[str, ...] = ()
    failure_codes: tuple[str, ...] = ()
    offline_end_to_end: Optional[Mapping[str, Any]] = None
    bridge_cycles: tuple[Mapping[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "ready_for_activation": self.ready_for_activation,
            "runtime_activated": self.runtime_activated,
            "hard_stop": self.hard_stop,
            "CANONICAL_RUNTIME_ENTRYPOINT_STATUS": self.status,
            "gate_flags": self.gate_flags.to_dict(),
            "evidence": self.evidence.to_dict(),
            "blockers": list(self.blockers),
            "failure_codes": list(self.failure_codes),
            "offline_end_to_end": (
                None if self.offline_end_to_end is None else dict(self.offline_end_to_end)
            ),
            "bridge_cycles": [dict(c) for c in self.bridge_cycles],
        }


@dataclass(frozen=True)
class AnalyticalSessionLockV1:
    identity: str
    session_id: str
    lock_path: str
    acquired: bool
    network_session: bool = False
    authorization_consumed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "session_id": self.session_id,
            "lock_path": self.lock_path,
            "acquired": self.acquired,
            "network_session": self.network_session,
            "authorization_consumed": self.authorization_consumed,
        }


@dataclass
class MutableGateAccumulatorV1:
    """Mutable helper while assembling gate flags (not part of durable schema)."""

    flags: dict[str, bool] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    failure_codes: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def set_flag(self, name: str, value: bool, *, failure_code: str | None = None) -> None:
        self.flags[name] = bool(value)
        if not value:
            self.blockers.append(name)
            if failure_code:
                self.failure_codes.append(failure_code)


def default_evidence_shell(
    *,
    repository_sha: str,
    baseline_sha: str,
    config_digest: str,
    call_graph_before: tuple[str, ...],
    call_graph_after: tuple[str, ...],
) -> PreActivationEvidenceV1:
    return PreActivationEvidenceV1(
        capability_id=CAPABILITY_ID,
        schema_version=SCHEMA_VERSION,
        producer_version=PRODUCER_VERSION,
        owner=OWNER,
        ok=False,
        repository_sha=repository_sha,
        baseline_sha=baseline_sha,
        config_digest=config_digest,
        call_graph_before=call_graph_before,
        call_graph_after=call_graph_after,
        productive_call_graph_proven=(),
        gate_flags={},
        effective_config={},
        authority_map={},
        restart_recovery={},
        exit_risk_safety_independence={},
        failure_injection_results={},
        legacy_authority_check={},
        activation_negative={},
        network_order_negative={},
        verification_result={"ok": False},
    )
