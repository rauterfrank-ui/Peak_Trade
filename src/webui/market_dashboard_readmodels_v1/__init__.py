"""Market Dashboard ReadModel contracts v1.

Typed, immutable, versioned, fail-closed consumer contracts for the Market
Dashboard architecture reset. Producer binding is PR-C; UI/page binding is PR-D.

Package documentation: docs/webui/MARKET_DASHBOARD_READMODELS_V1.md
"""

from __future__ import annotations

from src.webui.market_dashboard_readmodels_v1.aggregate import (
    MarketDashboardPageSnapshotV1,
    PAGE_AGGREGATE_SCHEMA_ID,
    new_market_dashboard_page_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.contracts import (
    AuthorityClassificationV1,
    CanonicalDecisionStatusV1,
    CanonicalDecisionSummaryV1,
    DashboardAvailabilityStateV1,
    DashboardFreshnessSnapshotV1,
    DecisionDirectionV1,
    DiagnosticsSummarySnapshotV1,
    DoublePlayDecisionSnapshotV1,
    EconomicGateStatusV1,
    EconomicSummarySnapshotV1,
    EligibilityStatusV1,
    ExecutionStateSnapshotV1,
    MarketInstrumentSnapshotV1,
    MarketRankingItemV1,
    MarketRankingSnapshotV1,
    OhlcvBarV1,
    OperatingModeV1,
    PACKAGE_ID,
    SafetyAuthoritySnapshotV1,
    SideAssessmentV1,
    SourceFreshnessEntryV1,
    TriStateV1,
    UnavailableSnapshotV1,
    new_canonical_decision_summary_v1,
    new_dashboard_freshness_snapshot_v1,
    new_diagnostics_summary_snapshot_v1,
    new_double_play_decision_snapshot_v1,
    new_economic_summary_snapshot_v1,
    new_execution_state_snapshot_v1,
    new_market_instrument_snapshot_v1,
    new_market_ranking_snapshot_v1,
    new_safety_authority_snapshot_v1,
    new_unavailable_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.provenance import (
    DashboardFreshnessStateV1,
    DashboardSnapshotProvenanceV1,
    DashboardSourceKindV1,
    PROVENANCE_SCHEMA_ID,
    new_dashboard_snapshot_provenance_v1,
)
from src.webui.market_dashboard_readmodels_v1.serialization import (
    dumps_json,
    loads_page_snapshot_json,
    page_snapshot_from_json_dict,
    page_snapshot_to_json_dict,
    to_json_dict,
)
from src.webui.market_dashboard_readmodels_v1.validation import (
    MarketDashboardReadModelContractError,
)

__all__ = [
    "AuthorityClassificationV1",
    "CanonicalDecisionStatusV1",
    "CanonicalDecisionSummaryV1",
    "DashboardAvailabilityStateV1",
    "DashboardFreshnessSnapshotV1",
    "DashboardFreshnessStateV1",
    "DashboardSnapshotProvenanceV1",
    "DashboardSourceKindV1",
    "DecisionDirectionV1",
    "DiagnosticsSummarySnapshotV1",
    "DoublePlayDecisionSnapshotV1",
    "EconomicGateStatusV1",
    "EconomicSummarySnapshotV1",
    "EligibilityStatusV1",
    "ExecutionStateSnapshotV1",
    "MarketDashboardPageSnapshotV1",
    "MarketDashboardReadModelContractError",
    "MarketInstrumentSnapshotV1",
    "MarketRankingItemV1",
    "MarketRankingSnapshotV1",
    "OhlcvBarV1",
    "OperatingModeV1",
    "PACKAGE_ID",
    "PAGE_AGGREGATE_SCHEMA_ID",
    "PROVENANCE_SCHEMA_ID",
    "SafetyAuthoritySnapshotV1",
    "SideAssessmentV1",
    "SourceFreshnessEntryV1",
    "TriStateV1",
    "UnavailableSnapshotV1",
    "dumps_json",
    "loads_page_snapshot_json",
    "new_canonical_decision_summary_v1",
    "new_dashboard_freshness_snapshot_v1",
    "new_dashboard_snapshot_provenance_v1",
    "new_diagnostics_summary_snapshot_v1",
    "new_double_play_decision_snapshot_v1",
    "new_economic_summary_snapshot_v1",
    "new_execution_state_snapshot_v1",
    "new_market_dashboard_page_snapshot_v1",
    "new_market_instrument_snapshot_v1",
    "new_market_ranking_snapshot_v1",
    "new_safety_authority_snapshot_v1",
    "new_unavailable_snapshot_v1",
    "page_snapshot_from_json_dict",
    "page_snapshot_to_json_dict",
    "to_json_dict",
]
