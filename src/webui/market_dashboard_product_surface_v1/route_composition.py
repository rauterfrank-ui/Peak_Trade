"""Route composition for GET /market product surface (PR-F).

Path: optional read-only sources → PR-C adapters via page builder → presenter → template.
"""

from __future__ import annotations

from typing import Any

from src.webui.market_dashboard_product_surface_v1.presenter import (
    PRESENTER_OWNER,
    build_market_dashboard_page_context_v1,
)
from src.webui.market_dashboard_product_surface_v1.source_loader import (
    load_market_dashboard_readonly_sources_v1,
)
from src.webui.market_dashboard_readmodels_v1.page_builder import (
    PAGE_AGGREGATE_OWNER,
    MarketDashboardPageSourceInputsV1,
    build_market_dashboard_page_snapshot_v1,
)

PRODUCT_TEMPLATE_NAME = "market_dashboard_product_v1.html"
PRODUCT_SURFACE_OWNER = (
    "src.webui.market_dashboard_product_surface_v1.route_composition."
    "build_market_dashboard_product_template_context_v1"
)


def build_market_dashboard_product_template_context_v1() -> dict[str, Any]:
    """Compose page aggregate + presenter context for the active /market template."""

    loaded = load_market_dashboard_readonly_sources_v1()
    inputs = MarketDashboardPageSourceInputsV1(
        generated_at=loaded.generated_at,
        market_ohlcv_source=loaded.market_ohlcv_source,
        instrument_id=loaded.instrument_id,
        venue=loaded.venue,
        ranking_source=loaded.ranking_source,
        ranking_stage=loaded.ranking_stage,
        canonical_decision_source=loaded.canonical_decision_source,
        decision_effective_at=loaded.decision_effective_at,
        decision_evidence_reference=loaded.decision_evidence_reference,
        decision_evidence_status=loaded.decision_evidence_status,
        double_play_composition=loaded.double_play_composition,
        double_play_bull_assessment=loaded.double_play_bull_assessment,
        double_play_bear_assessment=loaded.double_play_bear_assessment,
        double_play_effective_at=loaded.double_play_effective_at,
        double_play_evidence_reference=loaded.double_play_evidence_reference,
        # Honest residual: no consolidated Safety/Authority producer.
        safety_authority_source=loaded.safety_authority_source,
        execution_source=loaded.execution_source,
        execution_effective_at=loaded.execution_effective_at,
        execution_operating_mode=loaded.execution_operating_mode,
        execution_evidence_reference=loaded.execution_evidence_reference,
        economic_source=loaded.economic_source,
        economic_effective_at=loaded.economic_effective_at,
        economic_evidence_reference=loaded.economic_evidence_reference,
        diagnostics_source=loaded.diagnostics_source,
        diagnostics_effective_at=loaded.diagnostics_effective_at,
        diagnostics_bundle_reference=loaded.diagnostics_bundle_reference,
        market_source_reference=loaded.market_source_reference,
        ranking_source_reference=loaded.ranking_source_reference,
    )
    snapshot = build_market_dashboard_page_snapshot_v1(inputs)
    context = build_market_dashboard_page_context_v1(
        snapshot,
        chart_bars=loaded.chart_bars,
    )
    payload = context.to_template_dict()
    payload["page_aggregate_owner"] = PAGE_AGGREGATE_OWNER
    payload["presenter_owner"] = PRESENTER_OWNER
    payload["product_surface_owner"] = PRODUCT_SURFACE_OWNER
    payload["loader_notes"] = list(loaded.loader_notes)
    payload["product_gate_pass"] = False
    return payload


__all__ = [
    "PRODUCT_SURFACE_OWNER",
    "PRODUCT_TEMPLATE_NAME",
    "build_market_dashboard_product_template_context_v1",
]
