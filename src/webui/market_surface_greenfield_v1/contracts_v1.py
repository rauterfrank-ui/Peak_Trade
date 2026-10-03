"""Presentation boundary contracts for market surface greenfield v1."""

from __future__ import annotations

IMPLEMENTATION_ROOT = "src/webui/market_surface_greenfield_v1"
SURFACE_HTML_ROUTE = "/operator-trading-surface"
STATE_API_PATH = "/api/operator-trading-surface/v1/state"
STATE_SCHEMA = "operator_trading_surface_canonical_state.v1"

POLL_INTERVAL_SECONDS = 1

# Instrument slots with no canonical CURRENT productive HTTP source (fail-closed).
UNKNOWN_SOURCE_SLOTS: tuple[tuple[str, str], ...] = (
    ("top20", "SOURCE UNAVAILABLE"),
    ("top5", "SOURCE UNAVAILABLE"),
    ("feature_slots", "SOURCE UNAVAILABLE"),
    ("confirmation", "NO CANONICAL SOURCE"),
    ("risk_size_anatomy", "NO CURRENT HTTP SOURCE"),
    ("learning", "NO CURRENT INSTRUMENT"),
)

PROVENANCE_CLASS_NEW_GREENFIELD = "NEW_GREENFIELD"
PROVENANCE_CLASS_PROVEN_CURRENT = "PROVEN_CURRENT_INDEPENDENT"
PROVENANCE_CLASS_EXTERNAL = "EXTERNAL_LIBRARY"
