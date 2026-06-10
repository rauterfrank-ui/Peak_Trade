"""Docs contract for Market Ranking Funnel Producer v0 env/schema boundary."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_market_surface_ranking_funnel_env_schema_boundary_v0() -> None:
    """Ranking funnel env/schema boundary stays pinned before implementation."""
    surface = (PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")

    required_tokens = [
        "PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED=1",
        "PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT",
        "market_ranking_funnel_readmodel.v0",
        "tests&#47;fixtures&#47;market_ranking_funnel_readmodel_v0&#47;",
        "readmodel_id",
        "generated_at_iso",
        "source",
        "stale",
        "stale_reason",
        "non_authorizing=true",
        "stages.universe[]",
        "stages.shortlist[]",
        "stages.selected[]",
        "row_id",
        "symbol",
        "rank",
        "display_score",
        "notes",
        "&#47;api&#47;market&#47;ranking",
    ]

    for token in required_tokens:
        assert token in surface

    charter_start = surface.index("### Market Ranking Funnel Producer v0")
    marker_start = surface.index("### Marker / IA crosswalk policy v0")
    charter = surface[charter_start:marker_start]

    forbidden_payload_tokens = [
        "order_id",
        "side",
        "quantity",
        "leverage",
        "approval=true",
        "live_authorized=true",
        "strategy_activation=true",
    ]

    for token in forbidden_payload_tokens:
        assert token not in charter


def test_market_surface_single_page_consolidation_operator_pointer_env_boundary_v0() -> None:
    """Single-page consolidation operator enablement tokens stay pinned in MARKET_SURFACE_V0."""
    surface = (PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")

    section_start = surface.index("### Single-page consolidation (env-gated SSR v1)")
    section_end = surface.index("## Ranking funnel empty state (dynamic labels)")
    consolidation = surface[section_start:section_end]

    required_env_tokens = [
        "PEAK_TRADE_MARKET_SINGLE_PAGE_CONSOLIDATION_V1_ENABLED=1",
        "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED=1",
        "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT",
        "PEAK_TRADE_LAST_PAPER_RUN_PANEL_ENABLED=1",
        "PEAK_TRADE_LAST_PAPER_RUN_BUNDLE_ROOT",
    ]

    for token in required_env_tokens:
        assert token in consolidation

    required_boundary_tokens = [
        "default off",
        "operator-gated",
        "fail-closed",
        "no dashboard truth",
        "no provider truth",
        "Market-Airport excluded",
        "Master V2 / Double Play protected",
        "test_market_single_page_consolidation_structure_contract_v1.py",
        "observability/OBSERVABILITY_HUB_V0.md",
    ]

    for token in required_boundary_tokens:
        assert token.lower() in consolidation.lower()


def test_market_surface_run_projection_operator_pointer_env_boundary_v0() -> None:
    """Run projection operator enablement tokens stay pinned in MARKET_SURFACE_V0."""
    surface = (PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")

    section_start = surface.index("### Post-Closeout Registry run projection (env-gated SSR v0)")
    section_end = surface.index("## Safety banner and stable markers")
    run_projection = surface[section_start:section_end]

    assert "Operator enablement (run projection v1)" in run_projection
    assert "PEAK_TRADE_MARKET_RUN_PROJECTION_" in run_projection

    required_env_tokens = [
        "PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED=1",
        "PEAK_TRADE_MARKET_RUN_PROJECTION_PAYLOAD_JSON",
    ]

    for token in required_env_tokens:
        assert token in run_projection

    required_boundary_tokens = [
        "default off",
        "operator-gated",
        "fail-closed",
        "&#47;market",
        "no provider truth",
        "no dashboard truth",
        "Market-Airport excluded",
        "Master V2 / Double Play protected",
        "test_market_registry_projection_overlay_v0.py",
        "test_market_dashboard_readonly_structure_contract_v0.py",
        "test_market_dashboard_readonly_run_projection_spec_v0.py",
    ]

    for token in required_boundary_tokens:
        assert token.lower() in run_projection.lower()


def test_market_surface_ranking_funnel_operator_pointer_env_boundary_v0() -> None:
    """Ranking funnel operator enablement tokens stay pinned in MARKET_SURFACE_V0."""
    surface = (PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")

    section_start = surface.index("### Market Ranking Funnel SSR v0 landed")
    section_end = surface.index("### Marker / IA crosswalk policy v0")
    ranking_funnel = surface[section_start:section_end]

    assert "Operator enablement (ranking funnel v1)" in ranking_funnel

    required_env_tokens = [
        "PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED=1",
        "PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT",
    ]

    for token in required_env_tokens:
        assert token in ranking_funnel

    required_boundary_tokens = [
        "default off",
        "operator-gated",
        "fail-closed",
        "GET",
        "&#47;market",
        "no provider truth",
        "no dashboard truth",
        "Market-Airport excluded",
        "Master V2 / Double Play protected",
        "no run",
        "testnet",
        "paper",
        "shadow",
        "test_market_dashboard_readonly_structure_contract_v0.py",
        "test_market_ranking_funnel_readmodel_v0.py",
    ]

    for token in required_boundary_tokens:
        assert token.lower() in ranking_funnel.lower()


def test_market_surface_market_depth_operator_pointer_env_boundary_v0() -> None:
    """Market depth operator enablement tokens stay pinned in MARKET_SURFACE_V0."""
    surface = (PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")

    section_start = surface.index("### Market Depth display on GET /market (SSR v0 implemented)")
    section_end = surface.index(
        "## Double-Play Market Dashboard konsumiert strukturierte Metadaten v2"
    )
    market_depth = surface[section_start:section_end]

    assert "Operator enablement (market depth v1)" in market_depth
    assert "PEAK_TRADE_MARKET_DEPTH_" in market_depth

    required_env_tokens = [
        "PEAK_TRADE_MARKET_DEPTH_ENABLED=1",
        "PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT",
    ]

    for token in required_env_tokens:
        assert token in market_depth

    required_boundary_tokens = [
        "default off",
        "operator-gated",
        "fail-closed",
        "GET",
        "&#47;market",
        "no provider truth",
        "no dashboard truth",
        "Market-Airport excluded",
        "Master V2 / Double Play protected",
        "no run",
        "testnet",
        "paper",
        "shadow",
        "test_market_dashboard_readonly_structure_contract_v0.py",
        "test_market_depth_readmodel_v0.py",
        "test_market_depth_api_v0.py",
        "test_market_surface_api.py",
    ]

    for token in required_boundary_tokens:
        assert token.lower() in market_depth.lower()


def test_market_surface_chartjs_cdn_diagnostics_operator_pointer_env_boundary_v0() -> None:
    """Chart.js CDN diagnostics operator enablement tokens stay pinned in MARKET_SURFACE_V0."""
    surface = (PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")

    section_start = surface.index("#### Operator enablement (chart.js CDN diagnostics v1)")
    section_end = surface.index("### Chart.js local fallback planning charter v0")
    chartjs_cdn = surface[section_start:section_end]

    assert "Operator enablement (chart.js CDN diagnostics v1)" in chartjs_cdn

    required_diagnostic_tokens = [
        "data-chartjs-cdn-load-error",
        "data-chartjs-cdn-monitored-v0",
        "data-chartjs-cdn-script-v0",
        "data-market-chart-status",
        "data-market-v11",
        "market-v0-chart-status",
        "CHARTJS_LOCAL_FALLBACK_PLANNING_CHARTER_V0",
    ]

    for token in required_diagnostic_tokens:
        assert token in chartjs_cdn

    required_boundary_tokens = [
        "diagnostic only",
        "fail-closed",
        "no authority",
        "vendor fallback stays deferred until CDN-blocking evidence",
        "no provider truth",
        "no dashboard truth",
        "Market-Airport excluded",
        "Master V2 / Double Play protected",
        "no run",
        "testnet",
        "paper",
        "shadow",
        "test_market_dashboard_readonly_structure_contract_v0.py",
        "tests/test_market_surface_api.py",
    ]

    for token in required_boundary_tokens:
        assert token.lower() in chartjs_cdn.lower()


def test_market_surface_ssr_provenance_snapshot_operator_pointer_env_boundary_v0() -> None:
    """SSR provenance / snapshot triage operator enablement tokens stay pinned in MARKET_SURFACE_V0."""
    surface = (PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")

    section_start = surface.index("#### Operator enablement (SSR provenance / snapshot triage v1)")
    section_end = surface.index("### Single-page consolidation (env-gated SSR v1)")
    ssr_provenance = surface[section_start:section_end]

    assert "Operator enablement (SSR provenance / snapshot triage v1)" in ssr_provenance

    required_provenance_tokens = [
        "data-market-v0-embedded-snapshot-generated-at-v0",
        "data-market-v0-depth-bundle-provenance-v0",
        "data-market-v0-depth-bundle-stale",
        "data-market-v0-payload-meta-note-v0",
        "data-market-v0-depth-tile-freshness-mirror-v0",
        "generated_at_utc",
        "Snapshot bei Seitenladen",
        "meta.note",
        "depth_generated_at_iso",
        "depth_stale",
        "depth_stale_reason",
    ]

    for token in required_provenance_tokens:
        assert token in ssr_provenance

    required_boundary_tokens = [
        "display-only",
        "fail-closed",
        "no authority",
        "no provider truth",
        "no dashboard truth",
        "trading readiness",
        "vendor fallback stays deferred",
        "Market-Airport excluded",
        "Master V2 / Double Play protected",
        "no run",
        "testnet",
        "paper",
        "shadow",
        "chart.js CDN diagnostics v1",
        "test_market_dashboard_readonly_structure_contract_v0.py",
        "tests/test_market_surface_api.py",
    ]

    for token in required_boundary_tokens:
        assert token.lower() in ssr_provenance.lower()

    forbidden_authority_tokens = [
        "live_authorized=true",
        "testnet_authorized=true",
        "execute_authorized=true",
        "order_authorized=true",
    ]

    for token in forbidden_authority_tokens:
        assert token.lower() not in ssr_provenance.lower()


def test_market_surface_active_paper_run_operator_pointer_env_boundary_v0() -> None:
    """Active paper run operator enablement tokens stay pinned in MARKET_SURFACE_V0."""
    surface = (PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")

    section_start = surface.index("### Active Paper Run SSR (env-gated v1)")
    section_end = surface.index("### Single-page consolidation (env-gated SSR v1)")
    active_paper_run = surface[section_start:section_end]

    assert "Operator enablement (active paper run v1)" in active_paper_run

    required_env_tokens = [
        "PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_ENABLED=1",
        "PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_BRIDGE_ROOT",
        "PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_DETAIL_URL",
    ]

    for token in required_env_tokens:
        assert token in active_paper_run

    required_marker_tokens = [
        "data-market-v0-active-paper-run",
        "data-market-v0-active-paper-run-readonly",
        'data-market-v0-active-paper-run-authority="false"',
        "data-market-v0-active-paper-run-enabled",
        "data-market-v0-active-paper-run-active",
        "LIVE_AUTHORIZED",
        "PREFLIGHT_LIFT",
        "is_active",
    ]

    for token in required_marker_tokens:
        assert token in active_paper_run

    required_boundary_tokens = [
        "default off",
        "operator-gated",
        "fail-closed",
        "Observability/Operator Context",
        "no authority",
        "no provider truth",
        "no dashboard truth",
        "trading readiness",
        "exchange-freshness",
        "vendor fallback stays deferred",
        "Market-Airport excluded",
        "Master V2 / Double Play protected",
        "no run",
        "testnet",
        "paper",
        "shadow",
        "Last Paper Run",
        "SSR provenance / snapshot triage",
        "test_market_active_paper_run_runtime_v0.py",
    ]

    for token in required_boundary_tokens:
        assert token.lower() in active_paper_run.lower()

    forbidden_authority_tokens = [
        "live_authorized=true",
        "preflight_lift_authorized=true",
        "testnet_authorized=true",
        "execute_authorized=true",
        "order_authorized=true",
    ]

    for token in forbidden_authority_tokens:
        assert token.lower() not in active_paper_run.lower()
