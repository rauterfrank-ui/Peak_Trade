"""Landscape V3 presentation constants — AUTHORITY=NONE."""

from __future__ import annotations

CAPABILITY_ID = "MARKET_DASHBOARD_LANDSCAPE_V3_FRESH_V1"
SCHEMA_VERSION = "market_dashboard_landscape_v3.v1"
STREAM_SCHEMA_VERSION = "market_dashboard_landscape_v3_stream.v1"
SNAPSHOT_SCHEMA_VERSION = "market_dashboard_landscape_v3_snapshot.v1"

AUTHORITY = "NONE"
READ_ONLY = True
PRODUCTIVE_BACKFLOW = False
SELECTION_AUTHORITY = "NONE"
RISK_AUTHORITY = "NONE"
EXECUTION_AUTHORITY = "NONE"

DEFAULT_VENUE_NATIVE_ID = "ETH-USDT-SWAP"
EEA_PUBLIC_MD_SOURCE_FAMILY = "PEAK_TRADE_PUBLIC_MARKET_DATA_RUNTIME_V1"

V3_HTML_ROUTE = "/market/v3"
V3_SNAPSHOT_API_ROUTE = "/api/market/v3/snapshot"
V3_STREAM_WS_ROUTE = "/api/market/v3/stream"

FORBIDDEN_V2_ASSET_PREFIXES = (
    "static/js/market_dashboard_landscape_v2",
    "static/css/market_dashboard_landscape_v2",
    "market_landscape_v2.html",
)
