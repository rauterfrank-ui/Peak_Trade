"""Typed models for Phase 9.2 productive restart/recovery Session-GO authority."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class SessionGoAuthorityV1:
    schema_version: str
    capability_id: str
    session_go_id: str
    session_id: str
    expected_repository_sha: str
    expected_config_digest: str
    entrypoint_id: str
    entrypoint_path: str
    public_md_only: bool
    http_get_only: bool
    max_session_duration_seconds: int
    restart_recovery_scope: str
    issued_at: float
    not_before: float
    expires_at: float
    activation_status: str
    owner_go_required: bool
    owner_session_go_required: bool
    single_use_authorization_required: bool
    confirm_token_required: bool
    network_session_execution_authorized_by_this_go: bool
    fixture_non_authoritative: bool = False
    session_go_digest: str = ""
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["notes"] = list(self.notes)
        return payload


@dataclass
class SessionGoGateResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    authority: Optional[SessionGoAuthorityV1] = None
    session_go_authority_satisfied: bool = False
    productive_session_execution_permitted: bool = False
    authorization_may_proceed: bool = False
    lock_may_proceed: bool = False
    network_may_proceed: bool = False
    session_start_may_proceed: bool = False
    authorization_consumed: bool = False
    session_lock_acquired: bool = False
    session_started: bool = False
    network_request_count: int = 0
    side_effects_occurred: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "authority": None if self.authority is None else self.authority.to_dict(),
            "session_go_authority_satisfied": self.session_go_authority_satisfied,
            "productive_session_execution_permitted": self.productive_session_execution_permitted,
            "authorization_may_proceed": self.authorization_may_proceed,
            "lock_may_proceed": self.lock_may_proceed,
            "network_may_proceed": self.network_may_proceed,
            "session_start_may_proceed": self.session_start_may_proceed,
            "authorization_consumed": self.authorization_consumed,
            "session_lock_acquired": self.session_lock_acquired,
            "session_started": self.session_started,
            "network_request_count": self.network_request_count,
            "side_effects_occurred": self.side_effects_occurred,
        }
