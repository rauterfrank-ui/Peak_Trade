"""Docs-charter contract for the Market Ranking Funnel Producer v0."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MARKET_SURFACE_DOC = PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md"


def test_market_surface_ranking_funnel_producer_charter_v0() -> None:
    """Market Ranking Funnel Producer v0 charter stays read-only and non-authorizing."""
    surface = MARKET_SURFACE_DOC.read_text(encoding="utf-8")

    required_tokens = [
        "### Market Ranking Funnel Producer v0 (read-only charter)",
        "market_ranking_funnel_readmodel.v0",
        "PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED=1",
        "GET &#47;market",
        "&#47;market&#47;double-play",
        "&#47;api&#47;market&#47;ranking",
        "endpoint in v0",
        "tests/ops/test_market_surface_ranking_funnel_producer_charter_v0.py",
        "tests/webui/test_market_dashboard_readonly_structure_contract_v0.py",
        "DASHBOARD_AUTHORITY_CHANGED=false",
        "RANKING_PRODUCER_AUTHORIZES_TRADES=false",
        "FuturesRankingSnapshot",
        "must not be directly wired",
        "non_authorizing=true",
        "universe",
        "shortlist",
        "selected",
    ]

    for token in required_tokens:
        assert token in surface

    forbidden_promotions = [
        "trade signal",
        "approval",
        "readiness",
        "live authorization",
        "strategy activation",
        "Master V2",
        "Double Play trading input",
    ]

    forbidden_section_start = surface.index("Forbidden promotions:")
    forbidden_section = surface[forbidden_section_start:]

    for token in forbidden_promotions:
        assert token in forbidden_section
