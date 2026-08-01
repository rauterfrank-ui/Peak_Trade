"""Typed models and errors for S03 productive session execution owner v1."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional


class AdditionalEvidenceS03SessionExecutionOwnerError(RuntimeError):
    """Fail-closed S03 execution-owner error (never embeds confirm-token plaintext)."""


def sha256_hex_canonical(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass
class SideEffectProbeV1:
    events: list[str] = field(default_factory=list)

    def record(self, event: str) -> None:
        self.events.append(str(event))

    def to_dict(self) -> dict[str, Any]:
        return {"events": list(self.events)}


@dataclass(frozen=True)
class S03ScopeBindingsV1:
    campaign_id: str
    session_label: str
    session_id: str
    preregistration_id: str
    preregistration_digest: str
    contract_digest: str
    runbook_digest: str
    authorization_id: str
    authorization_digest: str
    repository_sha: str
    venue: str
    instrument: str
    network_scope: str
    session_scope: str
    duration_seconds: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "session_label": self.session_label,
            "session_id": self.session_id,
            "preregistration_id": self.preregistration_id,
            "preregistration_digest": self.preregistration_digest,
            "contract_digest": self.contract_digest,
            "runbook_digest": self.runbook_digest,
            "authorization_id": self.authorization_id,
            "authorization_digest": self.authorization_digest,
            "repository_sha": self.repository_sha,
            "venue": self.venue,
            "instrument": self.instrument,
            "network_scope": self.network_scope,
            "session_scope": self.session_scope,
            "duration_seconds": self.duration_seconds,
        }


@dataclass(frozen=True)
class MarketSampleV1:
    sample_identity: str
    mark_price: float
    event_time_unix_seconds: float
    receive_time_unix_seconds: float
    monotonic_elapsed_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_identity": self.sample_identity,
            "mark_price": self.mark_price,
            "event_time_unix_seconds": self.event_time_unix_seconds,
            "receive_time_unix_seconds": self.receive_time_unix_seconds,
            "monotonic_elapsed_seconds": self.monotonic_elapsed_seconds,
        }


@dataclass(frozen=True)
class SessionLockRecordV1:
    campaign_id: str
    session_id: str
    preregistration_id: str
    preregistration_digest: str
    authorization_id: str
    authorization_digest: str
    repository_sha: str
    process_id: int
    owner_identity: str
    created_at_utc: str
    monotonic_start_reference: float
    session_scope: str
    venue: str
    instrument: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "session_id": self.session_id,
            "preregistration_id": self.preregistration_id,
            "preregistration_digest": self.preregistration_digest,
            "authorization_id": self.authorization_id,
            "authorization_digest": self.authorization_digest,
            "repository_sha": self.repository_sha,
            "process_id": self.process_id,
            "owner_identity": self.owner_identity,
            "created_at_utc": self.created_at_utc,
            "monotonic_start_reference": self.monotonic_start_reference,
            "session_scope": self.session_scope,
            "venue": self.venue,
            "instrument": self.instrument,
        }


@dataclass(frozen=True)
class OrchestratorResultV1:
    status: str
    terminal_verdict: str
    authorization_consumed: bool
    session_lock_created: bool
    session_lock_removed: bool
    network_activity_occurred: bool
    evidence_mutation_occurred: bool
    real_session_started: bool
    requested_duration_seconds: int
    actual_monotonic_duration_seconds: float
    evidence_root: str
    integrity_manifest_path: str
    terminal_verdict_path: str
    side_effect_probe: Mapping[str, Any]
    blocker: str = ""
    sufficient_s03_evidence: bool = False
    counterfactual_runtime_authority_occurred: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "terminal_verdict": self.terminal_verdict,
            "authorization_consumed": self.authorization_consumed,
            "session_lock_created": self.session_lock_created,
            "session_lock_removed": self.session_lock_removed,
            "network_activity_occurred": self.network_activity_occurred,
            "evidence_mutation_occurred": self.evidence_mutation_occurred,
            "real_session_started": self.real_session_started,
            "requested_duration_seconds": self.requested_duration_seconds,
            "actual_monotonic_duration_seconds": self.actual_monotonic_duration_seconds,
            "evidence_root": self.evidence_root,
            "integrity_manifest_path": self.integrity_manifest_path,
            "terminal_verdict_path": self.terminal_verdict_path,
            "side_effect_probe": dict(self.side_effect_probe),
            "blocker": self.blocker,
            "sufficient_s03_evidence": self.sufficient_s03_evidence,
            "counterfactual_runtime_authority_occurred": (
                self.counterfactual_runtime_authority_occurred
            ),
        }


@dataclass(frozen=True)
class OfflineProbeFixturesV1:
    confirm_token: str
    authorization_path: Any  # Path
    evidence_root: Any  # Path
    repository_sha: str
    market_samples: tuple[MarketSampleV1, ...]
    monotonic_clock: Any
    wall_clock_utc: Any
    sleep: Any = None
    previously_seen_fingerprints: Optional[frozenset[str]] = None
