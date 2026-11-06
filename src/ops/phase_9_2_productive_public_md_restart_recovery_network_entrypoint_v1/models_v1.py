"""Typed models for the productive public-MD restart/recovery network entrypoint."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SegmentAuthorizationEnvelopeV1:
    schema_version: str
    capability_id: str
    session_id: str
    segment_id: str
    segment_role: str
    segment_purpose: str
    repository_sha: str
    config_digest: str
    runtime_mode: str
    instrument_identity: str
    network_allowlist: str
    http_method_allowlist: str
    allowed_side_effects: tuple[str, ...]
    forbidden_side_effects: tuple[str, ...]
    max_segment_duration_seconds: int
    predecessor_checkpoint_digest: str | None
    expected_successor_state: str
    authorization_id: str
    authorization_digest: str
    single_use: bool
    expires_at: float
    revocation_status: str
    productive: bool
    fixture: bool
    envelope_digest: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["allowed_side_effects"] = list(self.allowed_side_effects)
        payload["forbidden_side_effects"] = list(self.forbidden_side_effects)
        return payload


@dataclass
class OrchestrationSegmentResultV1:
    ok: bool
    segment_role: str
    segment_id: str
    authorization_id: str
    authorization_digest: str
    authorization_consumed: bool
    wallclock_started: bool
    wallclock_network_opened: bool
    harness_ok: bool
    controlled_restart_exit_code: int | None
    checkpoint_digest: str | None
    terminal_manifest_digest: str | None
    reconciliation_before_alpha: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    telemetry: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OrchestrationCampaignResultV1:
    ok: bool
    session_id: str
    segment_plan: tuple[str, ...]
    pre: OrchestrationSegmentResultV1 | None
    post: OrchestrationSegmentResultV1 | None
    verifier: dict[str, Any] | None
    controlled_restart_exit_code: int | None
    network_session_started: bool
    real_authorization_issued: bool
    real_authorization_consumed: bool
    runtime_started: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "session_id": self.session_id,
            "segment_plan": list(self.segment_plan),
            "pre": None if self.pre is None else self.pre.to_dict(),
            "post": None if self.post is None else self.post.to_dict(),
            "verifier": self.verifier,
            "controlled_restart_exit_code": self.controlled_restart_exit_code,
            "network_session_started": self.network_session_started,
            "real_authorization_issued": self.real_authorization_issued,
            "real_authorization_consumed": self.real_authorization_consumed,
            "runtime_started": self.runtime_started,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "claims": dict(self.claims),
        }
