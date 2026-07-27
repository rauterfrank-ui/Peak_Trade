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
class RegimeBullBearSwitchSnapshotV1(_ProjectionBase):
    """Read-only projection of Regime + Bull/Bear (SideState) + Switch evidence.

    Field-for-field consumer snapshot only. Does not own or recompute Regime,
    SideState, or transition_state authority.
    """

    regime_id: str | None
    regime_status: str | None
    side_state: str | None
    previous_side_state: str | None
    next_side_state: str | None
    scope_event_type: str | None
    transition_allowed: bool | None
    transition_reason_code: str | None
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))
        if self.availability is Availability.AVAILABLE:
            if (
                self.regime_id is None
                or self.regime_status is None
                or self.side_state is None
                or self.previous_side_state is None
                or self.next_side_state is None
                or self.scope_event_type is None
                or self.transition_allowed is None
                or self.transition_reason_code is None
            ):
                raise ValueError(
                    "regime/bull_bear/switch required fields must be present when AVAILABLE"
                )


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
    """Minimal direct projection of EconomicViabilityEvidenceV1 (Phase 4.6A).

    Ratified status field is ``economic_viability_status`` — the exact
    ``EconomicViabilityEvidenceV1.status`` enum value. Forbidden alias:
    ``economic_gate_status`` (must not represent EVI status or promotion gate).

    Metrics retain MetricFieldV1 dict shape (semantic/value/reason_code) with
    no recomputation. Lifecycle and promotion fields are intentionally absent.
    """

    economic_viability_status: str | None
    economic_validity_proven: bool | None
    profitability_claim_allowed: bool | None
    policy_threshold_status: str | None
    policy_version: str | None
    authority_effect: str | None
    runtime_effect: bool | None
    order_effect: bool | None
    reason_codes: tuple[str, ...]
    profit_factor: Mapping[str, Any] | None
    net_return: Mapping[str, Any] | None
    max_drawdown: Mapping[str, Any] | None
    sharpe: Mapping[str, Any] | None
    trade_count: Mapping[str, Any] | None
    funding_drag: Mapping[str, Any] | None
    evidence_ref: str | None
    contract_version: str | None
    owner: str | None
    strategy_id: str | None
    strategy_version: str | None
    config_digest: str | None
    implementation_digest: str | None
    data_digest: str | None
    manifest_digest: str | None
    wiring_chain_digest: str | None
    policy_digest: str | None

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))

        def _freeze_metric(value: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
            if value is None:
                return None
            return dict(value)

        object.__setattr__(self, "profit_factor", _freeze_metric(self.profit_factor))
        object.__setattr__(self, "net_return", _freeze_metric(self.net_return))
        object.__setattr__(self, "max_drawdown", _freeze_metric(self.max_drawdown))
        object.__setattr__(self, "sharpe", _freeze_metric(self.sharpe))
        object.__setattr__(self, "trade_count", _freeze_metric(self.trade_count))
        object.__setattr__(self, "funding_drag", _freeze_metric(self.funding_drag))


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
    RegimeBullBearSwitchSnapshotV1,
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
