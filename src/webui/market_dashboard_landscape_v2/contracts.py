"""Immutable dashboard-facing projection contracts (Landscape V2).

These are consumer snapshots only. They do not recompute decision, risk,
sizing, scope, or Double Play authority. Unbound slots use explicit
Availability states — never silent defaults.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence, Union

from .availability import Availability
from .provenance import FreshnessV1, SnapshotProvenanceV1

SCHEMA_FAMILY = "market_dashboard_landscape_projection"
SCHEMA_VERSION = "v1"


def _require_provenance(provenance: SnapshotProvenanceV1) -> SnapshotProvenanceV1:
    if not isinstance(provenance, SnapshotProvenanceV1):
        raise TypeError("provenance must be SnapshotProvenanceV1")
    return provenance


def _require_freshness(freshness: FreshnessV1) -> FreshnessV1:
    if not isinstance(freshness, FreshnessV1):
        raise TypeError("freshness must be FreshnessV1")
    return freshness


@dataclass(frozen=True)
class _ProjectionBase:
    """Shared envelope fields for all Landscape projections."""

    schema_id: str
    schema_version: str
    provenance: SnapshotProvenanceV1
    freshness: FreshnessV1
    availability: Availability

    def __post_init__(self) -> None:
        if not self.schema_id or not isinstance(self.schema_id, str):
            raise ValueError("schema_id required")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"schema_version must be {SCHEMA_VERSION!r}, got {self.schema_version!r}"
            )
        _require_provenance(self.provenance)
        _require_freshness(self.freshness)
        if not isinstance(self.availability, Availability):
            raise TypeError("availability must be Availability")
        if self.availability != self.provenance.availability:
            raise ValueError("availability must match provenance.availability")
        if self.freshness.is_stale and self.availability is Availability.AVAILABLE:
            raise ValueError("stale freshness cannot pair with AVAILABLE")


@dataclass(frozen=True)
class MarketInstrumentSnapshotV1(_ProjectionBase):
    instrument_id: str | None
    venue: str | None
    market_type: str | None
    mark_price: float | None
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))
        if self.availability is Availability.AVAILABLE:
            if not self.instrument_id:
                raise ValueError("instrument_id required when AVAILABLE")


@dataclass(frozen=True)
class UniverseRankingSnapshotV1(_ProjectionBase):
    ranking: tuple[Mapping[str, Any], ...]
    selected_instrument_id: str | None
    reason_codes: tuple[str, ...]
    universe: tuple[Mapping[str, Any], ...] = ()

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "ranking", tuple(dict(row) for row in self.ranking))
        object.__setattr__(self, "universe", tuple(dict(row) for row in self.universe))
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))


@dataclass(frozen=True)
class DynamicScopeSnapshotV1(_ProjectionBase):
    scope_state: str | None
    current_scope_ref: str | None
    next_scope_ref: str | None
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))


@dataclass(frozen=True)
class CanonicalDecisionSnapshotV1(_ProjectionBase):
    instrument_id: str | None
    decision: str | None
    direction: str | None
    reason_codes: tuple[str, ...]
    blockers: tuple[str, ...]
    decision_id: str | None
    evidence_schema_version: str | None

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))
        object.__setattr__(self, "blockers", tuple(self.blockers))
        if self.availability is Availability.AVAILABLE:
            if self.decision is None or self.direction is None:
                raise ValueError("decision and direction required when AVAILABLE")


@dataclass(frozen=True)
class DoublePlaySnapshotV1(_ProjectionBase):
    overall_status: str | None
    panel_summaries: tuple[Mapping[str, Any], ...]
    blockers: tuple[str, ...]
    display_only: bool
    live_authorization: bool

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(
            self, "panel_summaries", tuple(dict(row) for row in self.panel_summaries)
        )
        object.__setattr__(self, "blockers", tuple(self.blockers))
        if self.live_authorization is not False:
            raise ValueError("live_authorization must remain False on Landscape projection")
        if self.availability is Availability.AVAILABLE and not self.display_only:
            raise ValueError("AVAILABLE DoublePlaySnapshot must be display_only=True")


@dataclass(frozen=True)
class RiskSizingCapitalSnapshotV1(_ProjectionBase):
    risk_status: str | None
    sizing_status: str | None
    capital_status: str | None
    reason_codes: tuple[str, ...]
    quantity: float | None

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))
        # Landscape must never invent sizing quantities.
        if self.availability is not Availability.AVAILABLE and self.quantity is not None:
            raise ValueError("quantity forbidden unless AVAILABLE from canonical producer")


@dataclass(frozen=True)
class SafetyAuthoritySnapshotV1(_ProjectionBase):
    kill_switch_state: str | None
    veto_active: bool | None
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))


@dataclass(frozen=True)
class ExecutionReconciliationSnapshotV1(_ProjectionBase):
    execution_status: str | None
    reconciliation_status: str | None
    order_intent_ref: str | None
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))


@dataclass(frozen=True)
class EconomicSummarySnapshotV1(_ProjectionBase):
    economic_gate_status: str | None
    evidence_ref: str | None
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))


@dataclass(frozen=True)
class AutonomyStageSnapshotV1(_ProjectionBase):
    autonomy_stage: str | None
    runtime_bridge_status: str | None
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))


@dataclass(frozen=True)
class DiagnosticsSummarySnapshotV1(_ProjectionBase):
    diagnostic_codes: tuple[str, ...]
    summary: str | None
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "diagnostic_codes", tuple(self.diagnostic_codes))
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))


ProjectionSnapshot = Union[
    MarketInstrumentSnapshotV1,
    UniverseRankingSnapshotV1,
    DynamicScopeSnapshotV1,
    CanonicalDecisionSnapshotV1,
    DoublePlaySnapshotV1,
    RiskSizingCapitalSnapshotV1,
    SafetyAuthoritySnapshotV1,
    ExecutionReconciliationSnapshotV1,
    EconomicSummarySnapshotV1,
    AutonomyStageSnapshotV1,
    DiagnosticsSummarySnapshotV1,
]


def projection_envelope_dict(snapshot: _ProjectionBase) -> dict[str, Any]:
    return {
        "schema_id": snapshot.schema_id,
        "schema_version": snapshot.schema_version,
        "availability": snapshot.availability.value,
        "provenance": snapshot.provenance.to_json_dict(),
        "freshness": snapshot.freshness.to_json_dict(),
    }


def require_sequence(name: str, value: Sequence[str]) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise TypeError(f"{name} must be a sequence of strings")
    out = tuple(str(item) for item in value)
    return out
