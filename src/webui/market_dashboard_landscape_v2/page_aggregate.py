"""Page aggregate for Market Dashboard Landscape V2.

Read-only composition of Phase 2 projection slots. Does not recompute
decision, direction, risk, sizing, scope, or Double Play. Phase 4.1 route
supplies market_instrument / universe_ranking overrides; other slots stay
explicit NOT_BOUND until later Phase 4 bindings.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .contracts import (
    AutonomyStageSnapshotV1,
    CanonicalDecisionSnapshotV1,
    DiagnosticsSummarySnapshotV1,
    DoublePlaySnapshotV1,
    DynamicScopeSnapshotV1,
    EconomicSummarySnapshotV1,
    ExecutionReconciliationSnapshotV1,
    MarketInstrumentSnapshotV1,
    RegimeBullBearSwitchSnapshotV1,
    RiskSizingCapitalSnapshotV1,
    SafetyAuthoritySnapshotV1,
    UniverseRankingSnapshotV1,
)
from .source_health import DashboardSourceHealthSnapshotV1, build_source_health_from_snapshots
from .unavailable import default_not_bound_bundle

PAGE_AGGREGATE_SCHEMA_ID = "market_dashboard_landscape_page_snapshot.v1"
SHELL_RUNTIME_BRIDGE_DISPLAY = "BOUND_NOT_ACTIVATED"
SHELL_AUTHORITY_CLASS = "product_shell_constant_non_authoritative"


@dataclass(frozen=True)
class MarketDashboardPageSnapshotV1:
    """Immutable one-page aggregate for GET /market Landscape shell."""

    schema_id: str
    market_instrument: MarketInstrumentSnapshotV1
    universe_ranking: UniverseRankingSnapshotV1
    dynamic_scope: DynamicScopeSnapshotV1
    regime_bull_bear_switch: RegimeBullBearSwitchSnapshotV1
    canonical_decision: CanonicalDecisionSnapshotV1
    double_play: DoublePlaySnapshotV1
    risk_sizing_capital: RiskSizingCapitalSnapshotV1
    safety_authority: SafetyAuthoritySnapshotV1
    execution_reconciliation: ExecutionReconciliationSnapshotV1
    economic_summary: EconomicSummarySnapshotV1
    autonomy_stage: AutonomyStageSnapshotV1
    diagnostics_summary: DiagnosticsSummarySnapshotV1
    source_health: DashboardSourceHealthSnapshotV1
    generated_at: datetime
    runtime_bridge_display: str
    shell_authority_class: str
    git_sha: str | None

    def __post_init__(self) -> None:
        if self.schema_id != PAGE_AGGREGATE_SCHEMA_ID:
            raise ValueError(f"schema_id must be {PAGE_AGGREGATE_SCHEMA_ID!r}")
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at must be timezone-aware")
        if self.runtime_bridge_display != SHELL_RUNTIME_BRIDGE_DISPLAY:
            raise ValueError("runtime_bridge_display is a fixed shell constant")
        if self.shell_authority_class != SHELL_AUTHORITY_CLASS:
            raise ValueError("shell_authority_class must remain non-authoritative")


def _slot_map_from_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    required = (
        "market_instrument",
        "universe_ranking",
        "dynamic_scope",
        "regime_bull_bear_switch",
        "canonical_decision",
        "double_play",
        "risk_sizing_capital",
        "safety_authority",
        "execution_reconciliation",
        "economic_summary",
        "autonomy_stage",
        "diagnostics_summary",
    )
    missing = [slot for slot in required if slot not in bundle]
    if missing:
        raise ValueError(f"MISSING_SOURCE: aggregate slots absent: {missing}")
    return {slot: bundle[slot] for slot in required}


class MarketDashboardReadServiceV1:
    """Sole page-aggregate owner for Landscape V2 shell.

    Accepts optional slot_overrides from the read-only producer-binding layer.
    No producer imports inside this package; no domain recomputation.
    """

    def load_page_snapshot(
        self,
        *,
        generated_at: datetime,
        git_sha: str | None = None,
        slot_overrides: Mapping[str, Any] | None = None,
    ) -> MarketDashboardPageSnapshotV1:
        if generated_at.tzinfo is None:
            raise ValueError("generated_at must be timezone-aware")
        stamp = generated_at.astimezone(timezone.utc)
        bundle = dict(default_not_bound_bundle(generated_at=stamp))
        if slot_overrides:
            for slot, snap in slot_overrides.items():
                if slot not in bundle:
                    raise ValueError(f"unknown override slot={slot!r}")
                # Fail-closed: do not silently replace INVALID with AVAILABLE
                # without an explicit override object that already carries
                # Availability.AVAILABLE from a projection helper.
                bundle[slot] = snap
        slots = _slot_map_from_bundle(bundle)
        health = build_source_health_from_snapshots(
            slots,
            generated_at=stamp,
            git_sha=git_sha,
        )
        return MarketDashboardPageSnapshotV1(
            schema_id=PAGE_AGGREGATE_SCHEMA_ID,
            market_instrument=slots["market_instrument"],
            universe_ranking=slots["universe_ranking"],
            dynamic_scope=slots["dynamic_scope"],
            regime_bull_bear_switch=slots["regime_bull_bear_switch"],
            canonical_decision=slots["canonical_decision"],
            double_play=slots["double_play"],
            risk_sizing_capital=slots["risk_sizing_capital"],
            safety_authority=slots["safety_authority"],
            execution_reconciliation=slots["execution_reconciliation"],
            economic_summary=slots["economic_summary"],
            autonomy_stage=slots["autonomy_stage"],
            diagnostics_summary=slots["diagnostics_summary"],
            source_health=health,
            generated_at=stamp,
            runtime_bridge_display=SHELL_RUNTIME_BRIDGE_DISPLAY,
            shell_authority_class=SHELL_AUTHORITY_CLASS,
            git_sha=git_sha,
        )
