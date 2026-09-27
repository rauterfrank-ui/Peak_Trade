"""Architecture guard helpers for Landscape V3 (AUTHORITY=NONE)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
V3_PKG = REPO_ROOT / "src" / "webui" / "market_dashboard_landscape_v3"
V3_ROUTER = REPO_ROOT / "src" / "webui" / "market_dashboard_landscape_shell_router_v3.py"
V3_TEMPLATE = REPO_ROOT / "templates" / "peak_trade_dashboard" / "market_landscape_v3.html"
V3_JS = REPO_ROOT / "static" / "js" / "market_dashboard_landscape_v3.js"

FORBIDDEN_IMPORT_PREFIXES = (
    "src.execution",
    "src.webui.market_dashboard_landscape_v2",
    "src.webui.market_dashboard_landscape_producer_binding_v2",
    "src.ops.okx_selected_instrument_ohlcv_readmodel_v1",
)

FORBIDDEN_SUBSTRINGS = (
    "www.okx.com",
    "market_dashboard_landscape_v2",
    "place_order",
    "Keychain",
    "wseeapap.okx.com",
)
