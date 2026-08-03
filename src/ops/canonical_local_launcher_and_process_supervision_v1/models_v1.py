"""Durable session models for O2 launcher / supervision."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class LifecycleTransitionV1:
    timestamp_unix: float
    previous_state: str
    new_state: str
    reason_code: str
    session_id: str
    process_identity: dict[str, Any] = field(default_factory=dict)
    evidence_reference: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProcessIdentityV1:
    pid: int
    pgid: int
    process_start_identity: str
    cmdline_fingerprint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ProcessIdentityV1":
        return cls(
            pid=int(raw["pid"]),
            pgid=int(raw["pgid"]),
            process_start_identity=str(raw["process_start_identity"]),
            cmdline_fingerprint=str(raw.get("cmdline_fingerprint") or ""),
        )


@dataclass
class SessionRecordV1:
    schema_version: str
    capability_id: str
    session_id: str
    mode: str
    lifecycle_state: str
    repository_sha: str
    config_digest: str
    config_path: str
    supervisor_identity: str
    supervision_backend: str
    supervisor_instance_id: str
    process_identity: Optional[ProcessIdentityV1]
    log_root: str
    state_root: str
    evidence_root: str
    heartbeat_path: str
    created_at_unix: float
    updated_at_unix: float
    o1_environment_policy_id: str = ""
    o1_parent_environment_digest: str = ""
    o1_effective_environment_digest: str = ""
    safety_invariants: dict[str, bool] = field(default_factory=dict)
    last_reason_code: str = ""
    stop_escalated: bool = False
    recovered: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.process_identity is None:
            payload["process_identity"] = None
        return payload

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SessionRecordV1":
        identity_raw = raw.get("process_identity")
        identity = (
            ProcessIdentityV1.from_dict(identity_raw) if isinstance(identity_raw, dict) else None
        )
        return cls(
            schema_version=str(raw["schema_version"]),
            capability_id=str(raw["capability_id"]),
            session_id=str(raw["session_id"]),
            mode=str(raw["mode"]),
            lifecycle_state=str(raw["lifecycle_state"]),
            repository_sha=str(raw["repository_sha"]),
            config_digest=str(raw["config_digest"]),
            config_path=str(raw.get("config_path") or ""),
            supervisor_identity=str(raw["supervisor_identity"]),
            supervision_backend=str(raw["supervision_backend"]),
            supervisor_instance_id=str(raw["supervisor_instance_id"]),
            process_identity=identity,
            log_root=str(raw["log_root"]),
            state_root=str(raw["state_root"]),
            evidence_root=str(raw.get("evidence_root") or ""),
            heartbeat_path=str(raw["heartbeat_path"]),
            created_at_unix=float(raw["created_at_unix"]),
            updated_at_unix=float(raw["updated_at_unix"]),
            o1_environment_policy_id=str(raw.get("o1_environment_policy_id") or ""),
            o1_parent_environment_digest=str(raw.get("o1_parent_environment_digest") or ""),
            o1_effective_environment_digest=str(raw.get("o1_effective_environment_digest") or ""),
            safety_invariants=dict(raw.get("safety_invariants") or {}),
            last_reason_code=str(raw.get("last_reason_code") or ""),
            stop_escalated=bool(raw.get("stop_escalated") or False),
            recovered=bool(raw.get("recovered") or False),
        )
