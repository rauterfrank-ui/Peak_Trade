"""Route composition for GET /market product surface (PR-D).

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
        # Explicitly unbound until consolidated / evidence producers are wired.
        canonical_decision_source=None,
        double_play_composition=None,
        safety_authority_source=None,
        execution_source=None,
        economic_source=None,
        diagnostics_source=None,
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
