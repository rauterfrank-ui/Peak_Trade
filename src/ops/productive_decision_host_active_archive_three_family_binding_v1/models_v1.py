"""Models for productive decision-host ↔ active-archive three-family binding."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional

from src.ops.productive_decision_host_active_archive_three_family_binding_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    CAPABILITY_ID,
    DASHBOARD_AUTHORITY_EFFECT,
    HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH,
    OWNER,
    PACKAGE_MARKER,
    RUNTIME_MODE,
    SCHEMA_VERSION,
)


@dataclass(frozen=True)
class StateRootBindingV1:
    """Durable runtime state roots (decision authority) — never the dashboard archive."""

    layout_version: str
    runtime_root: str
    dynamic_scope_state_root: str
    confirmation_state_root: str
    activation_state_root: str
    accounting_state_root: str
    canonical_decision_source_dir: str
    evidence_session_root: str
    writer_lock_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArchiveBindingV1:
    """Dashboard archive is projection/readmodel target only — not decision authority."""

    archive_root: str
    resolution_precedence: str
    readmodels_dir: str
    dynamic_scope_sibling_path: str
    canonical_decision_sibling_path: str
    double_play_sibling_path: str
    writable: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SessionContractV1:
    """Explicit Owner-authorized no-order session contract."""

    capability_id: str
    schema_version: str
    owner: str
    package_marker: str
    runtime_mode: str
    repository_sha: str
    expected_repository_sha: str
    config_digest: str
    runtime_session_id: str
    instrument_id: str
    instrument_source: str
    archive_root: str
    owner_go: bool
    activation_enabled: bool
    public_md_only: bool
    orders_authorized: bool
    live_authorized: bool
    testnet_authorized: bool
    paper_exchange_orders: bool
    exchange_credential_use: bool
    real_capital_movement: bool
    network_session_allowed: bool
    long_running_phase_9_2_proven: bool
    hard_stop_double_play_canonical_input_contract_mismatch: bool
    authority_effect: str = AUTHORITY_EFFECT
    dashboard_authority_effect: str = DASHBOARD_AUTHORITY_EFFECT

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FamilyExportResultV1:
    family_id: str
    exportable: bool
    exported: bool
    materialized: bool
    loader_ok: bool
    source_digest: str = ""
    target_path: str = ""
    projection_path: str = ""
    error_code: str = ""
    detail: str = ""
    cycle_id: str = ""
    skipped_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CycleCommitTraceV1:
    cycle_id: str
    cycle_index: int
    instrument_id: str
    repository_sha: str
    config_digest: str
    runtime_session_id: str
    mid_price: float
    event_ts_unix: float
    decision_outcome: str
    decision_id: str
    dynamic_scope_advanced: bool
    dynamic_scope_persisted: bool
    canonical_decision_persisted: bool
    runtime_commit_ok: bool
    families: dict[str, Any] = field(default_factory=dict)
    blockers: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["blockers"] = list(self.blockers)
        return payload


@dataclass
class SmokeSessionResultV1:
    ok: bool
    capability_id: str = CAPABILITY_ID
    owner: str = OWNER
    package_marker: str = PACKAGE_MARKER
    schema_version: str = SCHEMA_VERSION
    runtime_mode: str = RUNTIME_MODE
    host_started: bool = False
    archive_bound: bool = False
    public_md_cycle_observed: bool = False
    canonical_cycle_committed: bool = False
    cycles_attempted: int = 0
    cycles_committed: int = 0
    dynamic_scope: Optional[FamilyExportResultV1] = None
    canonical_decision: Optional[FamilyExportResultV1] = None
    double_play: Optional[FamilyExportResultV1] = None
    hard_stop_double_play: bool = HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH
    long_running_phase_9_2_proven: bool = False
    order_path_reachable: bool = False
    credential_path_reachable: bool = False
    session: Optional[Mapping[str, Any]] = None
    state_roots: Optional[Mapping[str, Any]] = None
    archive_binding: Optional[Mapping[str, Any]] = None
    errors: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "capability_id": self.capability_id,
            "owner": self.owner,
            "package_marker": self.package_marker,
            "schema_version": self.schema_version,
            "runtime_mode": self.runtime_mode,
            "host_started": self.host_started,
            "archive_bound": self.archive_bound,
            "public_md_cycle_observed": self.public_md_cycle_observed,
            "canonical_cycle_committed": self.canonical_cycle_committed,
            "cycles_attempted": self.cycles_attempted,
            "cycles_committed": self.cycles_committed,
            "dynamic_scope": None if self.dynamic_scope is None else self.dynamic_scope.to_dict(),
            "canonical_decision": (
                None if self.canonical_decision is None else self.canonical_decision.to_dict()
            ),
            "double_play": None if self.double_play is None else self.double_play.to_dict(),
            "hard_stop_double_play": self.hard_stop_double_play,
            "long_running_phase_9_2_proven": self.long_running_phase_9_2_proven,
            "order_path_reachable": self.order_path_reachable,
            "credential_path_reachable": self.credential_path_reachable,
            "session": None if self.session is None else dict(self.session),
            "state_roots": None if self.state_roots is None else dict(self.state_roots),
            "archive_binding": (
                None if self.archive_binding is None else dict(self.archive_binding)
            ),
            "errors": list(self.errors),
            "notes": list(self.notes),
            "authority_effect": AUTHORITY_EFFECT,
            "dashboard_authority_effect": DASHBOARD_AUTHORITY_EFFECT,
        }
