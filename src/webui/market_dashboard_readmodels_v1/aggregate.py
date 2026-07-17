"""Market Dashboard ReadModel contracts v1 — page aggregate.

Immutable page snapshot with explicit available/unavailable unions per section.
Not bound to /market in PR-B.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Union

from src.webui.market_dashboard_readmodels_v1.contracts import (
    CanonicalDecisionSummaryV1,
    DashboardFreshnessSnapshotV1,
    DiagnosticsSummarySnapshotV1,
    DoublePlayDecisionSnapshotV1,
    EconomicSummarySnapshotV1,
    ExecutionStateSnapshotV1,
    MarketInstrumentSnapshotV1,
    MarketRankingSnapshotV1,
    SCHEMA_VERSION_V1,
    SafetyAuthoritySnapshotV1,
    UnavailableSnapshotV1,
)
from src.webui.market_dashboard_readmodels_v1.validation import (
    MarketDashboardReadModelContractError,
    require_aware_datetime,
    require_schema_id,
    require_schema_version,
)

PAGE_AGGREGATE_SCHEMA_ID = "peak_trade.market_dashboard.page_snapshot.v1"

MarketSectionV1 = Union[MarketInstrumentSnapshotV1, UnavailableSnapshotV1]
RankingSectionV1 = Union[MarketRankingSnapshotV1, UnavailableSnapshotV1]
DecisionSectionV1 = Union[CanonicalDecisionSummaryV1, UnavailableSnapshotV1]
DoublePlaySectionV1 = Union[DoublePlayDecisionSnapshotV1, UnavailableSnapshotV1]
SafetyAuthoritySectionV1 = Union[SafetyAuthoritySnapshotV1, UnavailableSnapshotV1]
ExecutionSectionV1 = Union[ExecutionStateSnapshotV1, UnavailableSnapshotV1]
EconomicSectionV1 = Union[EconomicSummarySnapshotV1, UnavailableSnapshotV1]
DiagnosticsSectionV1 = Union[DiagnosticsSummarySnapshotV1, UnavailableSnapshotV1]
FreshnessSectionV1 = Union[DashboardFreshnessSnapshotV1, UnavailableSnapshotV1]

_SECTION_TYPES: dict[str, tuple[type, ...]] = {
    "market": (MarketInstrumentSnapshotV1, UnavailableSnapshotV1),
    "ranking": (MarketRankingSnapshotV1, UnavailableSnapshotV1),
    "decision": (CanonicalDecisionSummaryV1, UnavailableSnapshotV1),
    "double_play": (DoublePlayDecisionSnapshotV1, UnavailableSnapshotV1),
    "safety_authority": (SafetyAuthoritySnapshotV1, UnavailableSnapshotV1),
    "execution": (ExecutionStateSnapshotV1, UnavailableSnapshotV1),
    "economic": (EconomicSummarySnapshotV1, UnavailableSnapshotV1),
    "diagnostics": (DiagnosticsSummarySnapshotV1, UnavailableSnapshotV1),
    "freshness": (DashboardFreshnessSnapshotV1, UnavailableSnapshotV1),
}


def _require_section(value: object, *, field: str) -> object:
    allowed = _SECTION_TYPES[field]
    if not isinstance(value, allowed):
        allowed_names = ", ".join(cls.__name__ for cls in allowed)
        raise MarketDashboardReadModelContractError(
            f"{field} must be one of ({allowed_names}), got {type(value).__name__}"
        )
    return value


@dataclass(frozen=True)
class MarketDashboardPageSnapshotV1:
    """Page-level aggregate. No presenter/HTML/CSS/Flask concerns."""

    schema_id: str
    schema_version: int
    generated_at: datetime
    market: MarketSectionV1
    ranking: RankingSectionV1
    decision: DecisionSectionV1
    double_play: DoublePlaySectionV1
    safety_authority: SafetyAuthoritySectionV1
    execution: ExecutionSectionV1
    economic: EconomicSectionV1
    diagnostics: DiagnosticsSectionV1
    freshness: FreshnessSectionV1

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", require_schema_id(self.schema_id))
        object.__setattr__(self, "schema_version", require_schema_version(self.schema_version))
        object.__setattr__(
            self,
            "generated_at",
            require_aware_datetime(self.generated_at, field="generated_at"),
        )
        for field_name in _SECTION_TYPES:
            object.__setattr__(
                self,
                field_name,
                _require_section(getattr(self, field_name), field=field_name),
            )


def new_market_dashboard_page_snapshot_v1(
    *,
    generated_at: datetime,
    market: MarketSectionV1,
    ranking: RankingSectionV1,
    decision: DecisionSectionV1,
    double_play: DoublePlaySectionV1,
    safety_authority: SafetyAuthoritySectionV1,
    execution: ExecutionSectionV1,
    economic: EconomicSectionV1,
    diagnostics: DiagnosticsSectionV1,
    freshness: FreshnessSectionV1,
) -> MarketDashboardPageSnapshotV1:
    return MarketDashboardPageSnapshotV1(
        schema_id=PAGE_AGGREGATE_SCHEMA_ID,
        schema_version=SCHEMA_VERSION_V1,
        generated_at=generated_at,
        market=market,
        ranking=ranking,
        decision=decision,
        double_play=double_play,
        safety_authority=safety_authority,
        execution=execution,
        economic=economic,
        diagnostics=diagnostics,
        freshness=freshness,
    )


__all__ = [
    "DecisionSectionV1",
    "DiagnosticsSectionV1",
    "DoublePlaySectionV1",
    "EconomicSectionV1",
    "ExecutionSectionV1",
    "FreshnessSectionV1",
    "MarketDashboardPageSnapshotV1",
    "MarketSectionV1",
    "PAGE_AGGREGATE_SCHEMA_ID",
    "RankingSectionV1",
    "SafetyAuthoritySectionV1",
    "new_market_dashboard_page_snapshot_v1",
]
