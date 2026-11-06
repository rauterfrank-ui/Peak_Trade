"""Typed models for prolonged natural-market wallclock binding."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
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
    min_session_duration_seconds: int
    planned_session_duration_seconds: int
    session_scope: str
    issued_at: float
    not_before: float
    expires_at: float
    activation_status: str
    owner_go_required: bool
    owner_session_go_required: bool
    single_use_authorization_required: bool
    confirm_token_required: bool
    network_session_execution_authorized_by_this_go: bool
    fixture_non_authoritative: bool
    session_go_digest: str
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["notes"] = list(self.notes)
        return payload


@dataclass
class BindingGateResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    prolonged_natural_market_path_bound: bool = False
    real_network_requires_bound_session_go: bool = True
    session_go_authority_satisfied: bool = False
    productive_session_execution_permitted: bool = False
    real_network_may_proceed: bool = False
    authorization_may_proceed: bool = False
    confirm_token_path_ok: bool = False
    network_session_started: bool = False
    fault_session_started: bool = False
    authority: Optional[SessionGoAuthorityV1] = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.authority is not None:
            payload["authority"] = self.authority.to_dict()
        return payload
