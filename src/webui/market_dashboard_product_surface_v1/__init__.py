"""Market Dashboard product surface v1 (PR-D).

Read-only presentation path: source loader → page aggregate → presenter → template.
"""

from __future__ import annotations

from src.webui.market_dashboard_product_surface_v1.presenter import (
    PRESENTER_OWNER,
    MarketDashboardPageContextV1,
    build_market_dashboard_page_context_v1,
)
from src.webui.market_dashboard_product_surface_v1.route_composition import (
    PRODUCT_SURFACE_OWNER,
    PRODUCT_TEMPLATE_NAME,
    build_market_dashboard_product_template_context_v1,
)
from src.webui.market_dashboard_product_surface_v1.source_loader import (
    LoadedMarketDashboardSourcesV1,
    load_market_dashboard_readonly_sources_v1,
)

__all__ = [
    "LoadedMarketDashboardSourcesV1",
    "MarketDashboardPageContextV1",
    "PRESENTER_OWNER",
    "PRODUCT_SURFACE_OWNER",
    "PRODUCT_TEMPLATE_NAME",
    "build_market_dashboard_page_context_v1",
    "build_market_dashboard_product_template_context_v1",
    "load_market_dashboard_readonly_sources_v1",
]
