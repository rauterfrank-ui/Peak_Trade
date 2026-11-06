"""Typed models for Phase 9.2 restart/recovery session contract harness."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class RestartSessionContractV1:
    schema_version: str
    capability_id: str
    restart_campaign_id: str
    durable_state_lineage_id: str
    segment_id: str
    segment_role: str
    predecessor_segment_id: str | None
    predecessor_terminal_manifest_digest: str | None
    expected_repository_sha: str
    expected_config_digest: str
    expected_instrument_identity: str
    expected_confirmation_session_id: str
    expected_runtime_state_digest: str
    expected_portfolio_digest: str
    expected_scope_digest: str
    expected_accounting_digest: str
    expected_evidence_cursor: str
    authorization_id: str
    authorization_digest: str
    runtime_session_id: str
    controlled_restart_reason: str
    minimum_pre_restart_distinct_observations: int
    required_reconciliation_before_alpha: bool
    no_order_boundary_assertions: tuple[str, ...]
    contract_digest: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["no_order_boundary_assertions"] = list(self.no_order_boundary_assertions)
        return payload


@dataclass
class StateRootBindingV1:
    field_name: str
    owner_capability: str
    classification: str
    reason: str
    digest: str
    value: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RestartCheckpointV1:
    restart_campaign_id: str
    durable_state_lineage_id: str
    confirmation_session_id: str
    observation_epoch: int
    observation_identity: str
    runtime_state_digest: str
    portfolio_digest: str
    scope_digest: str
    accounting_digest: str
    evidence_cursor: str
    atomic_commit_position: str
    selected_instrument_reference: str
    typed_volatility_reference: str
    reconciliation_reference: str
    open_position_present: bool
    open_position_quantity: float
    distinct_observation_count: int
    applied_fill_ids: list[str] = field(default_factory=list)
    applied_confirmation_ids: list[str] = field(default_factory=list)
    state_roots: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SegmentTelemetryV1:
    restart_campaign_id: str
    durable_state_lineage_id: str
    segment_id: str
    segment_role: str
    predecessor_segment_id: str | None
    pre_restart_terminal_manifest_digest: str | None
    state_root_digest_before_segment: str
    state_root_digest_after_segment: str
    confirmation_session_id_before: str
    confirmation_session_id_after: str
    observation_epoch_before: int
    observation_epoch_after: int
    reconciliation_completed_before_alpha: bool
    duplicate_confirmation_prevented_count: int
    duplicate_fill_prevented_count: int
    evidence_cursor_before: str
    evidence_cursor_after: str
    portfolio_digest_before: str
    portfolio_digest_after: str
    scope_digest_before: str
    scope_digest_after: str
    accounting_digest_before: str
    accounting_digest_after: str
    controlled_restart_requested: bool
    controlled_restart_completed: bool
    open_position_present_at_restart: bool
    open_position_recovered: bool
    open_position_recovery_claim: str
    authorization_reused: bool
    live_testnet_order_boundary_preserved: bool
    alpha_blocked: bool = False
    runtime_session_started: bool = False
    network_side_effect_before_validation: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SegmentRunResultV1:
    ok: bool
    segment_role: str
    segment_id: str
    runtime_session_id: str
    authorization_id: str
    authorization_consumed_once: bool
    lock_acquired: bool
    lock_released_by_owner: bool
    alpha_blocked: bool
    runtime_session_started: bool
    controlled_restart_exit_code: int | None
    terminal_manifest_digest: str | None
    telemetry: dict[str, Any]
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RestartBundleVerificationResultV1:
    result: str
    verified: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
