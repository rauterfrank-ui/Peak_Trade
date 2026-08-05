"""Typed models for real Public-MD restart wallclock binding."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class BindingGateResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    real_public_md_network_path_bound: bool = False
    real_network_requires_bound_session_go: bool = True
    session_go_authority_satisfied: bool = False
    productive_session_execution_permitted: bool = False
    real_network_may_proceed: bool = False
    authorization_may_proceed: bool = False
    confirm_token_path_ok: bool = False
    network_session_started: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SegmentBindingResultV1:
    ok: bool
    segment_role: str
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    exit_code: Optional[int] = None
    exit_code_classification: Optional[str] = None
    alpha_blocked: bool = True
    reconciliation_before_alpha: bool = False
    authorization_consumed: bool = False
    network_session_started: bool = False
    real_network_used: bool = False
    fake_md_used: bool = False
    real_session_claim_satisfied: bool = False
    wallclock_runner_referenced: bool = True
    wallclock_runner_invoked: bool = False
    distinct_observation_count: int = 0
    duplicate_confirmation_advance_prevented: bool = True
    duplicate_fill_prevented: bool = True
    process_pid: Optional[int] = None
    claims: dict[str, Any] = field(default_factory=dict)
    harness_result: Optional[dict[str, Any]] = None
    gate: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
