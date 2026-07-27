"""Market Dashboard Landscape V2 — read-only projection contracts + page shell.

Consumer foundation, page aggregate/presenter, and Phase 4.1 binding via
market_dashboard_landscape_producer_binding_v2 (outside this package).
No runtime activation, orders, or domain recomputation.
"""

from __future__ import annotations

from .availability import AVAILABILITY_VALUES, Availability, parse_availability
from .contracts import (
    SCHEMA_FAMILY,
    SCHEMA_VERSION,
    AutonomyStageSnapshotV1,
    CanonicalDecisionSnapshotV1,
    DiagnosticsSummarySnapshotV1,
    DoublePlaySnapshotV1,
    DynamicScopeSnapshotV1,
    RegimeBullBearSwitchSnapshotV1,
    EconomicSummarySnapshotV1,
    ExecutionReconciliationSnapshotV1,
    MarketInstrumentSnapshotV1,
    RiskSizingCapitalSnapshotV1,
    SafetyAuthoritySnapshotV1,
    UniverseRankingSnapshotV1,
)
from .owner_registry import (
    CANONICAL_OWNER_REGISTRY_V1,
    REQUIRED_PROJECTION_SLOTS,
    owner_registry_by_slot,
)
from .page_aggregate import (
    PAGE_AGGREGATE_SCHEMA_ID,
    MarketDashboardPageSnapshotV1,
    MarketDashboardReadServiceV1,
)
from .presenter import present_market_landscape_v2
from .projections import (
    project_canonical_decision_snapshot_v1,
    project_double_play_snapshot_v1,
    project_economic_summary_snapshot_v1,
    project_market_instrument_snapshot_v1,
    project_universe_ranking_snapshot_v1,
)
from .provenance import FreshnessV1, SnapshotProvenanceV1
from .serialization import dumps_projection_canonical, serialize_projection
from .source_health import (
    SOURCE_HEALTH_SCHEMA_ID,
    DashboardSourceHealthSnapshotV1,
    build_source_health_from_snapshots,
)
from .unavailable import default_not_bound_bundle

PACKAGE_MARKER = "MARKET_DASHBOARD_LANDSCAPE_V2_READMODEL_CONTRACTS=true"
LAYER_VERSION = "v1"

__all__ = [
    "AVAILABILITY_VALUES",
    "Availability",
    "AutonomyStageSnapshotV1",
    "CANONICAL_OWNER_REGISTRY_V1",
    "CanonicalDecisionSnapshotV1",
    "DashboardSourceHealthSnapshotV1",
    "DiagnosticsSummarySnapshotV1",
    "DoublePlaySnapshotV1",
    "DynamicScopeSnapshotV1",
    "RegimeBullBearSwitchSnapshotV1",
    "EconomicSummarySnapshotV1",
    "ExecutionReconciliationSnapshotV1",
    "FreshnessV1",
    "LAYER_VERSION",
    "MarketDashboardPageSnapshotV1",
    "MarketDashboardReadServiceV1",
    "MarketInstrumentSnapshotV1",
    "PACKAGE_MARKER",
    "PAGE_AGGREGATE_SCHEMA_ID",
    "REQUIRED_PROJECTION_SLOTS",
    "RiskSizingCapitalSnapshotV1",
    "SCHEMA_FAMILY",
    "SCHEMA_VERSION",
    "SOURCE_HEALTH_SCHEMA_ID",
    "SafetyAuthoritySnapshotV1",
    "SnapshotProvenanceV1",
    "UniverseRankingSnapshotV1",
    "build_source_health_from_snapshots",
    "default_not_bound_bundle",
    "dumps_projection_canonical",
    "owner_registry_by_slot",
    "parse_availability",
    "present_market_landscape_v2",
    "project_canonical_decision_snapshot_v1",
    "project_double_play_snapshot_v1",
    "project_economic_summary_snapshot_v1",
    "project_market_instrument_snapshot_v1",
    "project_universe_ranking_snapshot_v1",
    "serialize_projection",
]
