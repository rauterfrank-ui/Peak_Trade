"""Market Dashboard page aggregate builder (PR-D).

Exactly one page-level composition owner: projects explicit adapter inputs into
``MarketDashboardPageSnapshotV1``. Performs no domain decisions, no implicit
source discovery, and no silent defaults beyond calling PR-C adapters.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from src.webui.market_dashboard_readmodels_v1.adapters import (
    adapt_canonical_decision_summary_v1,
    adapt_dashboard_freshness_snapshot_v1,
    adapt_diagnostics_summary_snapshot_v1,
    adapt_double_play_decision_snapshot_v1,
    adapt_economic_summary_snapshot_v1,
    adapt_execution_state_snapshot_v1,
    adapt_market_instrument_snapshot_v1,
    adapt_market_ranking_snapshot_v1,
    adapt_safety_authority_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.aggregate import (
    MarketDashboardPageSnapshotV1,
    new_market_dashboard_page_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.contracts import OperatingModeV1

PAGE_AGGREGATE_OWNER = (
    "src.webui.market_dashboard_readmodels_v1.page_builder.build_market_dashboard_page_snapshot_v1"
)


@dataclass(frozen=True)
class MarketDashboardPageSourceInputsV1:
    """Explicit, already-produced sources for one page aggregate build.

    Absent optional sources remain ``None`` and become typed unavailable
    sections via adapters. ``safety_authority_source`` must stay ``None`` until
    a consolidated canonical producer exists (NOT_BOUND).
    """

    generated_at: datetime
    market_ohlcv_source: Mapping[str, Any] | None = None
    instrument_id: str = ""
    venue: str = ""
    ranking_source: Mapping[str, Any] | None = None
    ranking_stage: str = "universe"
    canonical_decision_source: Any | None = None
    decision_effective_at: datetime | None = None
    decision_evidence_reference: str | None = None
    decision_evidence_status: str | None = None
    double_play_composition: Any | None = None
    double_play_bull_assessment: Any | None = None
    double_play_bear_assessment: Any | None = None
    double_play_effective_at: datetime | None = None
    double_play_evidence_reference: str | None = None
    safety_authority_source: Mapping[str, Any] | None = None
    execution_source: Any | None = None
    execution_effective_at: datetime | None = None
    execution_operating_mode: OperatingModeV1 | str = OperatingModeV1.OFFLINE
    execution_evidence_reference: str | None = None
    economic_source: Any | None = None
    economic_effective_at: datetime | None = None
    economic_evidence_reference: str | None = None
    diagnostics_source: Mapping[str, Any] | None = None
    diagnostics_effective_at: datetime | None = None
    diagnostics_bundle_reference: str | None = None
    market_source_reference: str | None = None
    ranking_source_reference: str | None = None


def build_market_dashboard_page_snapshot_v1(
    inputs: MarketDashboardPageSourceInputsV1,
) -> MarketDashboardPageSnapshotV1:
    """Build the immutable page aggregate from explicit adapter inputs only."""

    generated_at = inputs.generated_at
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=timezone.utc)

    market = adapt_market_instrument_snapshot_v1(
        inputs.market_ohlcv_source,
        instrument_id=inputs.instrument_id,
        venue=inputs.venue,
        generated_at=generated_at,
        source_reference=inputs.market_source_reference,
    )
    ranking = adapt_market_ranking_snapshot_v1(
        inputs.ranking_source,
        generated_at=generated_at,
        stage=inputs.ranking_stage,
        source_reference=inputs.ranking_source_reference,
    )
    decision_effective = inputs.decision_effective_at or generated_at
    decision = adapt_canonical_decision_summary_v1(
        inputs.canonical_decision_source,
        generated_at=generated_at,
        effective_at=decision_effective,
        evidence_reference=inputs.decision_evidence_reference,
        evidence_status=inputs.decision_evidence_status,
    )
    dp_effective = inputs.double_play_effective_at or generated_at
    double_play = adapt_double_play_decision_snapshot_v1(
        inputs.double_play_composition,
        generated_at=generated_at,
        effective_at=dp_effective,
        bull_assessment=inputs.double_play_bull_assessment,
        bear_assessment=inputs.double_play_bear_assessment,
        evidence_reference=inputs.double_play_evidence_reference,
    )
    safety_authority = adapt_safety_authority_snapshot_v1(
        inputs.safety_authority_source,
        generated_at=generated_at,
    )
    execution_effective = inputs.execution_effective_at or generated_at
    execution = adapt_execution_state_snapshot_v1(
        inputs.execution_source,
        generated_at=generated_at,
        effective_at=execution_effective,
        operating_mode=inputs.execution_operating_mode,
        evidence_reference=inputs.execution_evidence_reference,
    )
    economic_effective = inputs.economic_effective_at or generated_at
    economic = adapt_economic_summary_snapshot_v1(
        inputs.economic_source,
        generated_at=generated_at,
        effective_at=economic_effective,
        evidence_reference=inputs.economic_evidence_reference,
    )
    diagnostics_effective = inputs.diagnostics_effective_at or generated_at
    diagnostics = adapt_diagnostics_summary_snapshot_v1(
        inputs.diagnostics_source,
        generated_at=generated_at,
        effective_at=diagnostics_effective,
        bundle_reference=inputs.diagnostics_bundle_reference,
    )
    freshness = adapt_dashboard_freshness_snapshot_v1(
        page_generated_at=generated_at,
        sources={
            "market": market,
            "ranking": ranking,
            "decision": decision,
            "double_play": double_play,
            "safety_authority": safety_authority,
            "execution": execution,
            "economic": economic,
            "diagnostics": diagnostics,
        },
    )
    return new_market_dashboard_page_snapshot_v1(
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
    "MarketDashboardPageSourceInputsV1",
    "PAGE_AGGREGATE_OWNER",
    "build_market_dashboard_page_snapshot_v1",
]
