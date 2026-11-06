"""Typed models for post-unlock canonical runtime invocation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class PostUnlockInvocationResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    session_go_authority_satisfied: bool = False
    productive_session_execution_permitted: bool = False
    authorization_validated: bool = False
    authorization_consumed: bool = False
    authorization_consumed_exactly_once: bool = False
    session_lock_acquired: bool = False
    session_lock_released: bool = False
    canonical_runner_invoked: bool = False
    canonical_runner_invocation_count: int = 0
    runtime_started: bool = False
    network_session_started: bool = False
    network_request_count: int = 0
    restart_recovery_completed: bool = False
    reconciliation_before_alpha: bool = False
    session_id: str = ""
    session_go_id: str = ""
    session_go_digest: str = ""
    campaign: Optional[dict[str, Any]] = None
    claims: dict[str, Any] = field(default_factory=dict)
    terminal_state: str = "HARD_STOP"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "session_go_authority_satisfied": self.session_go_authority_satisfied,
            "productive_session_execution_permitted": self.productive_session_execution_permitted,
            "authorization_validated": self.authorization_validated,
            "authorization_consumed": self.authorization_consumed,
            "authorization_consumed_exactly_once": self.authorization_consumed_exactly_once,
            "session_lock_acquired": self.session_lock_acquired,
            "session_lock_released": self.session_lock_released,
            "canonical_runner_invoked": self.canonical_runner_invoked,
            "canonical_runner_invocation_count": self.canonical_runner_invocation_count,
            "runtime_started": self.runtime_started,
            "network_session_started": self.network_session_started,
            "network_request_count": self.network_request_count,
            "restart_recovery_completed": self.restart_recovery_completed,
            "reconciliation_before_alpha": self.reconciliation_before_alpha,
            "session_id": self.session_id,
            "session_go_id": self.session_go_id,
            "session_go_digest": self.session_go_digest,
            "campaign": self.campaign,
            "claims": dict(self.claims),
            "terminal_state": self.terminal_state,
        }
