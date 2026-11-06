"""DTOs for Cap 5.2 public-MD no-order shadow evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.constants_v1 import (
    CANONICAL_DIGEST_EXCLUDED_KEYS,
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


def strip_volatile_for_canonical_digest(payload: Any) -> Any:
    if isinstance(payload, Mapping):
        out: dict[str, Any] = {}
        for key, value in payload.items():
            if str(key) in CANONICAL_DIGEST_EXCLUDED_KEYS:
                continue
            out[str(key)] = strip_volatile_for_canonical_digest(value)
        return out
    if isinstance(payload, (list, tuple)):
        return [strip_volatile_for_canonical_digest(x) for x in payload]
    return payload


def canonical_digest_v1(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return sha256_hex(canonical_json_dumps(strip_volatile_for_canonical_digest(payload)))


@dataclass(frozen=True)
class PublicMdShadowGateFlagsV1:
    flags: Mapping[str, bool]

    def all_true(self) -> bool:
        return all(bool(v) for v in self.flags.values())

    def false_flags(self) -> tuple[str, ...]:
        return tuple(sorted(k for k, v in self.flags.items() if not bool(v)))

    def to_dict(self) -> dict[str, Any]:
        return {k: bool(v) for k, v in sorted(self.flags.items())}


@dataclass(frozen=True)
class PublicMdSessionLockV1:
    identity: str
    session_id: str
    lock_path: str
    acquired: bool
    network_session: bool = True
    public_market_data_only: bool = True
    authorization_consumed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "session_id": self.session_id,
            "lock_path": self.lock_path,
            "acquired": self.acquired,
            "network_session": self.network_session,
            "public_market_data_only": self.public_market_data_only,
            "authorization_consumed": self.authorization_consumed,
        }


@dataclass
class MutableGateAccumulatorV1:
    flags: dict[str, bool] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    failure_codes: list[str] = field(default_factory=list)

    def set_flag(self, name: str, value: bool, *, failure_code: str) -> None:
        self.flags[name] = bool(value)
        if not value:
            self.blockers.append(name)
            self.failure_codes.append(failure_code)


@dataclass(frozen=True)
class PublicMdShadowEvidenceBundleV1:
    capability_id: str
    schema_version: str
    producer_version: str
    owner: str
    ok: bool
    repository_sha: str
    baseline_sha: str
    config_digest: str
    capture_digest: str
    call_graph_before: tuple[str, ...]
    call_graph_after: tuple[str, ...]
    productive_call_graph_proven: tuple[str, ...]
    gate_flags: Mapping[str, bool]
    telemetry: Mapping[str, Any]
    restart_recovery: Mapping[str, Any]
    failure_injection_results: Mapping[str, Any]
    activation_negative: Mapping[str, Any]
    network_order_negative: Mapping[str, Any]
    authorization_consumption: Mapping[str, Any]
    public_md_capture: Mapping[str, Any]
    legacy_authority_check: Mapping[str, Any]
    independent_run: Mapping[str, Any]
    verifier_result: Mapping[str, Any]
    canonical_outcome_digest: str
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id or CAPABILITY_ID,
            "schema_version": self.schema_version or SCHEMA_VERSION,
            "producer_version": self.producer_version or PRODUCER_VERSION,
            "owner": self.owner or OWNER,
            "ok": self.ok,
            "repository_sha": self.repository_sha,
            "baseline_sha": self.baseline_sha,
            "config_digest": self.config_digest,
            "capture_digest": self.capture_digest,
            "call_graph_before": list(self.call_graph_before),
            "call_graph_after": list(self.call_graph_after),
            "productive_call_graph_proven": list(self.productive_call_graph_proven),
            "gate_flags": dict(self.gate_flags),
            "telemetry": dict(self.telemetry),
            "restart_recovery": dict(self.restart_recovery),
            "failure_injection_results": dict(self.failure_injection_results),
            "activation_negative": dict(self.activation_negative),
            "network_order_negative": dict(self.network_order_negative),
            "authorization_consumption": dict(self.authorization_consumption),
            "public_md_capture": dict(self.public_md_capture),
            "legacy_authority_check": dict(self.legacy_authority_check),
            "independent_run": dict(self.independent_run),
            "verifier_result": dict(self.verifier_result),
            "canonical_outcome_digest": self.canonical_outcome_digest,
            "notes": list(self.notes),
            "CANONICAL_RUNTIME_ENTRYPOINT_STATUS": CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
            "RUNTIME_ACTIVATED": RUNTIME_ACTIVATED,
        }


@dataclass(frozen=True)
class PublicMdShadowGateResultV1:
    ok: bool
    ready_for_activation: bool
    runtime_activated: bool
    hard_stop: bool
    status: str
    gate_flags: PublicMdShadowGateFlagsV1
    evidence: PublicMdShadowEvidenceBundleV1
    blockers: tuple[str, ...]
    failure_codes: tuple[str, ...]
    shadow_end_to_end: Mapping[str, Any]
    bridge_cycles: tuple[Mapping[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "ready_for_activation": self.ready_for_activation,
            "runtime_activated": self.runtime_activated,
            "hard_stop": self.hard_stop,
            "status": self.status,
            "gate_flags": self.gate_flags.to_dict(),
            "evidence": self.evidence.to_dict(),
            "blockers": list(self.blockers),
            "failure_codes": list(self.failure_codes),
            "shadow_end_to_end": dict(self.shadow_end_to_end),
            "bridge_cycle_count": len(self.bridge_cycles),
        }
