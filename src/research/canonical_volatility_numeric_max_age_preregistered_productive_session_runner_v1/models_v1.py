"""Typed models and errors for preregistered productive session runner v1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional


class PreregisteredSessionRunnerError(RuntimeError):
    """Fail-closed preregistered productive session runner error."""


@dataclass(frozen=True)
class GitBaselineSnapshotV1:
    branch: str
    head_sha: str
    origin_main_sha: str
    worktree_allowed_delta_only: bool


@dataclass(frozen=True)
class SideEffectProbeV1:
    """Ordered probe of irreversible side effects for consume-before tests."""

    events: list[str] = field(default_factory=list)

    def record(self, event: str) -> None:
        self.events.append(str(event))

    def to_dict(self) -> dict[str, Any]:
        return {"events": list(self.events)}


@dataclass(frozen=True)
class PreflightResultV1:
    ok: bool
    campaign_id: str
    session_id: str
    preregistration_id: str
    preregistration_digest: str
    authorization_id: str
    authorization_digest: str
    repository_sha: str
    venue: str
    instrument_id: str
    market_data_scope: str
    evidence_scope: str
    max_cycles: int
    productive_ledger_path: str
    join_ledger_path: str
    quarantine_ledger_path: str
    typed_volatility_persistence_path: str
    session_manifest_path: str
    session_02_id: str
    blockers: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "campaign_id": self.campaign_id,
            "session_id": self.session_id,
            "preregistration_id": self.preregistration_id,
            "preregistration_digest": self.preregistration_digest,
            "authorization_id": self.authorization_id,
            "authorization_digest": self.authorization_digest,
            "repository_sha": self.repository_sha,
            "venue": self.venue,
            "instrument_id": self.instrument_id,
            "market_data_scope": self.market_data_scope,
            "evidence_scope": self.evidence_scope,
            "max_cycles": self.max_cycles,
            "productive_ledger_path": self.productive_ledger_path,
            "join_ledger_path": self.join_ledger_path,
            "quarantine_ledger_path": self.quarantine_ledger_path,
            "typed_volatility_persistence_path": self.typed_volatility_persistence_path,
            "session_manifest_path": self.session_manifest_path,
            "session_02_id": self.session_02_id,
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True)
class RunnerResultV1:
    status: str
    terminal_state: str
    terminal_verdict: str
    session_id: str
    campaign_id: str
    authorization_consumed: bool
    authorization_consumed_at: Optional[str]
    authorization_consumption_count: int
    session_started: bool
    market_data_request_occurred: bool
    session_01_evidence_mutation_occurred: bool
    productive_ledger_mutation_occurred: bool
    session_02_mutation_occurred: bool
    cycles_executed: int
    records_appended: int
    public_endpoints_only: bool
    private_endpoint_request_occurred: bool
    order_request_occurred: bool
    credential_access_occurred: bool
    integrity: Mapping[str, Any]
    side_effect_probe: Mapping[str, Any]
    blocker: str = ""
    accumulation_report: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "terminal_state": self.terminal_state,
            "terminal_verdict": self.terminal_verdict,
            "session_id": self.session_id,
            "campaign_id": self.campaign_id,
            "authorization_consumed": self.authorization_consumed,
            "authorization_consumed_at": self.authorization_consumed_at,
            "authorization_consumption_count": self.authorization_consumption_count,
            "session_started": self.session_started,
            "market_data_request_occurred": self.market_data_request_occurred,
            "session_01_evidence_mutation_occurred": self.session_01_evidence_mutation_occurred,
            "productive_ledger_mutation_occurred": self.productive_ledger_mutation_occurred,
            "session_02_mutation_occurred": self.session_02_mutation_occurred,
            "cycles_executed": self.cycles_executed,
            "records_appended": self.records_appended,
            "public_endpoints_only": self.public_endpoints_only,
            "private_endpoint_request_occurred": self.private_endpoint_request_occurred,
            "order_request_occurred": self.order_request_occurred,
            "credential_access_occurred": self.credential_access_occurred,
            "integrity": dict(self.integrity),
            "side_effect_probe": dict(self.side_effect_probe),
            "blocker": self.blocker,
            "accumulation_report": dict(self.accumulation_report),
            "economic_validity_claimed": False,
            "promotion_authorized": False,
        }
