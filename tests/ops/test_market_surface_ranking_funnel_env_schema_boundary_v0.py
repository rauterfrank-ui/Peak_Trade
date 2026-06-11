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


def test_market_surface_tape_operator_pointer_env_boundary_v0() -> None:
    """Tape readmodel SSR operator enablement tokens stay pinned in MARKET_SURFACE_V0."""
    surface = (PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")

    section_start = surface.index("### Market tape readmodel SSR (env-gated v0)")
    section_end = surface.index("## Safety banner and stable markers")
    tape = surface[section_start:section_end]

    assert "Operator enablement (tape readmodel SSR v0)" in tape
    assert "PEAK_TRADE_MARKET_TAPE_" in tape

    required_env_tokens = [
        "PEAK_TRADE_MARKET_TAPE_ENABLED=1",
        "PEAK_TRADE_MARKET_TAPE_BUNDLE_ROOT",
    ]

    for token in required_env_tokens:
        assert token in tape

    required_boundary_tokens = [
        "default off",
        "operator-gated",
        "fail-closed",
        "offline-only",
        "offline fixture",
        "diagnostic",
        "operator-context",
        "GET",
        "&#47;market",
        "no provider truth",
        "no dashboard truth",
        "trading readiness",
        "selected-future truth",
        "order/fill/position truth",
        "fills.json",
        "workflow-pipeline fills",
        "Market-Airport excluded",
        "Master V2 / Double Play protected",
        "no Double-Play authority",
        "no run",
        "testnet",
        "paper",
        "shadow",
        "network",
        "browser requirement",
        "test_market_tape_ssr_v0.py",
        "test_market_dashboard_readonly_structure_contract_v0.py",
        "test_market_tape_readmodel_v0.py",
        "test_market_surface_ranking_funnel_env_schema_boundary_v0.py",
    ]

    for token in required_boundary_tokens:
        assert token.lower() in tape.lower()


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
        "PEAK_TRADE_MARKET_DEPTH_CHART_ENABLED=1",
    ]

    for token in required_env_tokens:
        assert token in market_depth

    required_boundary_tokens = [
        "default off",
        "operator-gated",
        "fail-closed",
        "offline-only",
        "GET",
        "&#47;market",
        "no provider truth",
        "no dashboard truth",
        "liquidity",
        "slippage",
        "execution readiness",
        "no Chart.js",
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
        "test_market_depth_chart_ssr_v0.py",
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
        "data-chartjs-vendor-fallback-v0",
        "data-market-chart-status",
        "data-market-v11",
        "market-v0-chart-status",
        "CHARTJS_LOCAL_FALLBACK_PLANNING_CHARTER_V0",
        "peakTradeChartjsVendorFallbackV0",
    ]

    for token in required_diagnostic_tokens:
        assert token in chartjs_cdn

    required_boundary_tokens = [
        "diagnostic only",
        "fail-closed",
        "no authority",
        "template-wired",
        "onerror-only",
        "non-authorizing",
        "Chart.js vendor fallback template wiring v1",
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
        "test_chartjs_vendor_fallback_wiring_contract_v0.py",
    ]

    for token in required_boundary_tokens:
        assert token.lower() in chartjs_cdn.lower()

    forbidden_stale_tokens = [
        "vendor fallback stays deferred",
        "no active local Chart.js vendor fallback",
    ]

    for token in forbidden_stale_tokens:
        assert token.lower() not in chartjs_cdn.lower()


def test_market_surface_chartjs_cdn_blocking_evidence_criteria_env_boundary_v0() -> None:
    """CDN-blocking evidence criteria tokens stay pinned in MARKET_SURFACE_V0 charter."""
    surface = (PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")

    section_start = surface.index("#### CDN-blocking evidence criteria (v1)")
    section_end = surface.index("## Double-Play Market Dashboard v1 SSR")
    cdn_evidence = surface[section_start:section_end]

    assert "CDN-blocking evidence criteria (v1)" in cdn_evidence

    required_charter_tokens = [
        "CHARTJS_LOCAL_FALLBACK_PLANNING_CHARTER_V0",
        "CDN-blocking evidence",
        "vendor fallback",
        "Vendor-Decision-GO",
        "PR #4108",
        "onerror-only",
        "wiring absence",
        "keine Vendor-Datei",
        "no provider truth",
        "no dashboard truth",
        "trading readiness",
        "Market-Airport excluded",
        "Master V2 / Double Play protected",
    ]

    for token in required_charter_tokens:
        assert token.lower() in cdn_evidence.lower()

    required_negative_tokens = [
        "bloße CDN-Abhängigkeit",
        "hypothetisches Offline-Risiko",
        "Operator-Wunsch nach Fallback",
        "CSP-/Netzwerk-Paranoia ohne reproduzierbaren Blocking-Befund",
        "allgemeiner Browserfehler ohne Chart.js-CDN-Kausalität",
    ]

    for token in required_negative_tokens:
        assert token.lower() in cdn_evidence.lower()

    required_boundary_tokens = [
        "fail-closed",
        "no authority",
        "no vendor fallback authorization",
        "wiring absence",
        "browser-render",
        "netzwerkzugriff",
        "no run",
        "testnet",
        "paper",
        "shadow",
        "#4101",
        "#4097",
        "data-chartjs-cdn-load-error",
        "data-chartjs-cdn-monitored-v0",
        "data-chartjs-cdn-script-v0",
        "data-chartjs-vendor-fallback-v0",
        "data-market-chart-status",
    ]

    for token in required_boundary_tokens:
        assert token.lower() in cdn_evidence.lower()

    forbidden_stale_tokens = [
        "vendor fallback stays deferred",
        "no active local Chart.js vendor fallback",
        "Separater Implementierungs-PR (vendor asset + template path",
        "Vendor-Fallback-Implementation-GO",
    ]

    for token in forbidden_stale_tokens:
        assert token.lower() not in cdn_evidence.lower()

    forbidden_authority_tokens = [
        "vendor_fallback_authorized_now=true",
        "live_authorized=true",
        "preflight_lift_authorized=true",
        "execute_authorized=true",
        "order_authorized=true",
        "dashboard_truth_go_authorized=true",
    ]

    for token in forbidden_authority_tokens:
        assert token.lower() not in cdn_evidence.lower()


def test_market_surface_chartjs_cdn_blocking_evidence_capture_charter_env_boundary_v0() -> None:
    """CDN-blocking evidence capture charter tokens stay pinned in MARKET_SURFACE_V0 charter."""
    surface = (PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")

    section_start = surface.index("#### CDN-blocking evidence capture charter (v1)")
    section_end = surface.index("## Double-Play Market Dashboard v1 SSR")
    capture_charter = surface[section_start:section_end]

    assert "CDN-blocking evidence capture charter (v1)" in capture_charter

    required_phase_tokens = [
        "Prep",
        "Docs-Execute",
        "Capture",
        "Review",
        "Vendor-Decision",
        "Wiring verification",
    ]

    for token in required_phase_tokens:
        assert token in capture_charter

    required_artifact_tokens = [
        "Zeitpunkt/UTCSTAMP",
        "Umgebung",
        "Renderpfad",
        "erwartete Wirkung",
        "beobachtete Wirkung",
        "Chart.js-CDN-Kausalitätsabgrenzung",
        "Operator-Attestation",
        "MANIFEST.sha256",
        "MANIFEST_VERIFY.txt",
    ]

    for token in required_artifact_tokens:
        assert token.lower() in capture_charter.lower()

    required_boundary_tokens = [
        "capture-erhebung",
        "browser-render",
        "netzwerkzugriff",
        "vendor-datei",
        "no vendor fallback authorization",
        "wiring absence",
        "PR #4108",
        "onerror-only",
        "data-chartjs-vendor-fallback-v0",
        "no provider truth",
        "no dashboard truth",
        "trading readiness",
        "preflight-lift",
        "execution",
        "order",
        "cancel",
        "secrets/credentials/operator-env",
        "fail-closed",
        "no authority",
        "#4101",
        "#4104",
        "#4097",
        "Market-Airport excluded",
        "Master V2 / Double Play protected",
    ]

    for token in required_boundary_tokens:
        assert token.lower() in capture_charter.lower()

    forbidden_stale_tokens = [
        "vendor fallback stays deferred",
        "Vendor-Implementation",
        "Implementierungs-PR",
    ]

    for token in forbidden_stale_tokens:
        assert token.lower() not in capture_charter.lower()

    forbidden_authority_tokens = [
        "vendor_fallback_authorized_now=true",
        "live_authorized=true",
        "preflight_lift_authorized=true",
        "execute_authorized=true",
        "order_authorized=true",
        "dashboard_truth_go_authorized=true",
    ]

    for token in forbidden_authority_tokens:
        assert token.lower() not in capture_charter.lower()


def test_market_surface_chartjs_cdn_blocking_evidence_capture_browser_execute_prep_env_boundary_v0() -> (
    None
):
    """Browser-capture execute prep tokens stay pinned in MARKET_SURFACE_V0 charter."""
    surface = (PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")

    section_start = surface.index("#### Browser-capture execute prep (read-only v1)")
    section_end = surface.index("## Double-Play Market Dashboard v1 SSR")
    execute_prep = surface[section_start:section_end]

    assert "Browser-capture execute prep (read-only v1)" in execute_prep

    required_section_tokens = [
        "Browser-Capture-Preflight-Checkliste",
        "Browser-Capture-Readiness-Matrix",
        "Operator-Attestation-Template",
        "Durable-Capture-Bundle-Layout",
    ]

    for token in required_section_tokens:
        assert token in execute_prep

    required_attestation_tokens = [
        "Operator Frank Rauter",
        "Datum/UTCSTAMP",
        "Renderpfad",
        "beobachteter Blocking-Befund",
        "erwartete/observierte Auswirkung",
        "Chart.js CDN Kausalitätsabgrenzung",
        "MACHINE_SUMMARY.env",
        "CAPTURE_REPORT.md",
        "BROWSER_OBSERVATION.md",
        "OPERATOR_ATTESTATION.md",
        "CAUSALITY_REVIEW.md",
        "MANIFEST.sha256",
        "MANIFEST_VERIFY.txt",
    ]

    for token in required_attestation_tokens:
        assert token.lower() in execute_prep.lower()

    required_boundary_tokens = [
        "browser-capture-erhebung",
        "browser-render",
        "netzwerkzugriff",
        "vendor-datei",
        "no vendor fallback authorization",
        "wiring absence",
        "PR #4108",
        "onerror-only",
        "data-chartjs-vendor-fallback-v0",
        "no provider truth",
        "no dashboard truth",
        "trading readiness",
        "preflight-lift",
        "execution",
        "order",
        "cancel",
        "secrets/credentials/operator-env",
        "fail-closed",
        "no authority",
        "#4101",
        "#4104",
        "#4105",
        "#4097",
        "Market-Airport excluded",
        "Master V2 / Double Play protected",
    ]

    for token in required_boundary_tokens:
        assert token.lower() in execute_prep.lower()

    forbidden_stale_tokens = [
        "vendor fallback stays deferred",
        "Vendor-Implementation",
        "Implementierungs-PR",
    ]

    for token in forbidden_stale_tokens:
        assert token.lower() not in execute_prep.lower()

    forbidden_authority_tokens = [
        "vendor_fallback_authorized_now=true",
        "live_authorized=true",
        "preflight_lift_authorized=true",
        "execute_authorized=true",
        "order_authorized=true",
        "dashboard_truth_go_authorized=true",
    ]

    for token in forbidden_authority_tokens:
        assert token.lower() not in execute_prep.lower()


def test_market_surface_chartjs_browser_capture_criteria_post_4111_parity_v0() -> None:
    """Post-#4111 parity guards on #4104/#4105/#4106 charter cross-refs."""
    surface = (PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")
    truth_map = (PROJECT_ROOT / "docs/ops/registry/DOCS_TRUTH_MAP.md").read_text(encoding="utf-8")

    parity_start = surface.index("**Parity record:**")
    parity_end = surface.index(
        "#### Chart.js vendor fallback template wiring v1 (implemented)", parity_start
    )
    parity_record = surface[parity_start:parity_end]

    criteria_start = surface.index("#### CDN-blocking evidence criteria (v1)")
    criteria_end = surface.index("#### CDN-blocking evidence capture charter (v1)", criteria_start)
    criteria = surface[criteria_start:criteria_end]

    capture_start = surface.index("#### CDN-blocking evidence capture charter (v1)")
    capture_end = surface.index("#### Browser-capture execute prep (read-only v1)", capture_start)
    capture_charter = surface[capture_start:capture_end]

    execute_start = surface.index("#### Browser-capture execute prep (read-only v1)")
    execute_end = surface.index("## Double-Play Market Dashboard v1 SSR", execute_start)
    execute_prep = surface[execute_start:execute_end]

    section_required_tokens = {
        parity_record: (
            "#4108",
            "#4110",
            "#4111",
            "onerror-only",
            "separately authorized — not granted",
            "data-chartjs-vendor-fallback-v0",
            "non-authorizing",
        ),
        criteria: (
            "PR #4108",
            "onerror-only",
            "separater GO",
            "jetzt nicht erteilt",
            "data-chartjs-vendor-fallback-v0",
            "non-authorizing",
        ),
        capture_charter: (
            "PR #4108",
            "onerror-only",
            "separate GO",
            "data-chartjs-vendor-fallback-v0",
            "non-authorizing",
        ),
        execute_prep: (
            "PR #4108",
            "onerror-only",
            "separately authorized",
            "data-chartjs-vendor-fallback-v0",
            "non-authorizing",
        ),
    }

    for section, tokens in section_required_tokens.items():
        for token in tokens:
            assert token.lower() in section.lower()

    for token in ("PR #4110", "PR #4111"):
        assert token in parity_record

    assert "separately authorized — not granted" in parity_record.lower()
    assert "jsdelivr" in parity_record.lower()

    for stale in (
        "vendor fallback stays deferred",
        "planning-only",
        "future implementation preconditions",
        "kein vendor/static/templates",
        "chart.js cdn nur",
    ):
        assert stale.lower() not in parity_record.lower()
        assert stale.lower() not in criteria.lower()
        assert stale.lower() not in capture_charter.lower()
        assert stale.lower() not in execute_prep.lower()

    for forbidden in (
        "browser_capture_execute_authorized_now=true",
        "vendor_fallback_authorized_now=true",
        "dashboard_truth_go_authorized=true",
        "execute_authorized=true",
    ):
        for section in (parity_record, criteria, capture_charter, execute_prep):
            assert forbidden.lower() not in section.lower()

    assert "PR #4111" in truth_map
    chartjs_row_start = truth_map.index("Chart.js local fallback planning charter v0")
    chartjs_row_end = truth_map.index("\n", chartjs_row_start)
    chartjs_row = truth_map[chartjs_row_start:chartjs_row_end]
    assert "#4111" in chartjs_row
    assert "PR #4108/#4110/#4111" in chartjs_row
    assert "separately authorized" in chartjs_row.lower()


def test_market_surface_chartjs_browser_capture_criteria_post_4112_parity_v0() -> None:
    """Post-#4112 chronicle/cross-ref guards on parity record and DOCS_TRUTH_MAP (non-authorizing)."""
    surface = (PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")
    truth_map = (PROJECT_ROOT / "docs/ops/registry/DOCS_TRUTH_MAP.md").read_text(encoding="utf-8")

    parity_start = surface.index("**Parity record:**")
    parity_end = surface.index(
        "#### Chart.js vendor fallback template wiring v1 (implemented)", parity_start
    )
    parity_record = surface[parity_start:parity_end]

    for token in (
        "PR #4112",
        "browser-capture-criteria parity",
        "chronicle/cross-ref only",
        "separately authorized — not granted",
        "onerror-only",
        "jsdelivr",
        "data-chartjs-vendor-fallback-v0",
        "non-authorizing",
    ):
        assert token.lower() in parity_record.lower()

    for forbidden in (
        "browser_capture_execute_authorized_now=true",
        "vendor_fallback_authorized_now=true",
        "dashboard_truth_go_authorized=true",
        "execute_authorized=true",
        "live_authorized=true",
        "preflight_lift_authorized=true",
    ):
        assert forbidden.lower() not in parity_record.lower()

    assert "PR #4112" in truth_map
    chronicle_start = truth_map.index("## Änderungsnachweis (Slice A)")
    chronicle_end = truth_map.index("\n- 2026-06-03", chronicle_start)
    chronicle = truth_map[chronicle_start:chronicle_end]
    assert "PR #4112" in chronicle
    assert "browser-capture-criteria parity chronicle closeout" in chronicle.lower()
    assert "separately authorized — not granted" in chronicle.lower()
    assert "browser_capture_execute_authorized_now=false" in chronicle.lower()

    chartjs_row_start = truth_map.index("Chart.js local fallback planning charter v0")
    chartjs_row_end = truth_map.index("\n", chartjs_row_start)
    chartjs_row = truth_map[chartjs_row_start:chartjs_row_end]
    assert "#4112" in chartjs_row
    assert "PR #4108/#4110/#4111/#4112" in chartjs_row
    assert "separately authorized" in chartjs_row.lower()


def test_market_surface_chartjs_chain_closeout_handoff_post_4113_parity_v0() -> None:
    """Post-#4113 chain-closeout handoff guards on parity record and DOCS_TRUTH_MAP (non-authorizing)."""
    surface = (PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")
    truth_map = (PROJECT_ROOT / "docs/ops/registry/DOCS_TRUTH_MAP.md").read_text(encoding="utf-8")

    parity_start = surface.index("**Parity record:**")
    parity_end = surface.index(
        "#### Chart.js vendor fallback template wiring v1 (implemented)", parity_start
    )
    parity_record = surface[parity_start:parity_end]

    for token in (
        "PR #4113",
        "#4108→#4113",
        "CHARTJS_CHAIN_CLOSED_ON_MAIN=true",
        "chain-closeout handoff protocol",
        "no parallel handoff doc/SSOT",
        "separately authorized — not granted",
        "Browser-Capture-Execute-Readiness-Prep",
        "onerror-only",
        "jsdelivr",
        "data-chartjs-vendor-fallback-v0",
        "non-authorizing",
        "no Truth/Readiness/Execution/Runtime authority",
    ):
        assert token.lower() in parity_record.lower()

    for forbidden in (
        "browser_capture_execute_authorized_now=true",
        "vendor_fallback_authorized_now=true",
        "dashboard_truth_go_authorized=true",
        "execute_authorized=true",
        "live_authorized=true",
        "preflight_lift_authorized=true",
        "runtime_authorized=true",
        "truth_go_authorized=true",
    ):
        assert forbidden.lower() not in parity_record.lower()

    assert "PR #4113" in truth_map
    chronicle_start = truth_map.index("## Änderungsnachweis (Slice A)")
    chronicle_end = truth_map.index("\n- 2026-06-03", chronicle_start)
    chronicle = truth_map[chronicle_start:chronicle_end]
    assert "PR #4113" in chronicle or "PR #4114" in chronicle
    assert "chain closeout handoff protocol" in chronicle.lower()
    assert "no parallel handoff doc/SSOT".lower() in chronicle.lower()
    assert "separately authorized — not granted" in chronicle.lower()
    assert "browser_capture_execute_authorized_now=false" in chronicle.lower()
    assert "#4108→#4113" in chronicle or "4108→#4113" in chronicle

    chartjs_row_start = truth_map.index("Chart.js local fallback planning charter v0")
    chartjs_row_end = truth_map.index("\n", chartjs_row_start)
    chartjs_row = truth_map[chartjs_row_start:chartjs_row_end]
    assert "#4113" in chartjs_row
    assert "PR #4108/#4110/#4111/#4112/#4113" in chartjs_row
    assert "separately authorized" in chartjs_row.lower()


def test_market_surface_chartjs_local_fallback_planning_charter_post_merge_parity_v0() -> None:
    """Parent CHARTJS_LOCAL_FALLBACK charter block reflects PR #4108 wiring on main."""
    surface = (PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")

    section_start = surface.index("### Chart.js local fallback planning charter v0")
    section_end = surface.index(
        "#### Chart.js vendor fallback template wiring v1 (implemented)",
        section_start,
    )
    parent_charter = surface[section_start:section_end]

    required_parity_tokens = [
        "CHARTJS_VENDOR_ADDED_ON_MAIN=true",
        "CHARTJS_LOCAL_FALLBACK_WIRING_V1_ON_MAIN=true",
        "PR #4108",
        "onerror-only",
        "wiring absence",
        "jsdelivr",
    ]

    for token in required_parity_tokens:
        assert token.lower() in parent_charter.lower()

    forbidden_stale_tokens = [
        "CHARTJS_VENDOR_ADDED=false",
        "zukünftigen",
        "separaten",
        "Implementierungs-PR",
        "nicht ins Repo vendoren",
        "keine Template-Umstellung",
    ]

    for token in forbidden_stale_tokens:
        assert token.lower() not in parent_charter.lower()


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
        "vendor fallback template wiring v1",
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
        "vendor fallback template wiring v1",
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


TRUTH_MAP = PROJECT_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
CI_AUDIT = PROJECT_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
CROSSLINK_PACKAGE_MARKER = "MARKET_TAPE_SSR_DOCS_TRUTH_MAP_CI_AUDIT_STATIC_CROSSLINK_GUARD_V1=true"
TEST_PACKAGE_MARKER = "MARKET_TAPE_SSR_DOCS_TRUTH_MAP_CI_AUDIT_CROSSLINK_GUARD_TEST=true"
SURFACE_REL = "docs/webui/MARKET_SURFACE_V0.md"
TAPE_SSR_TEST_REL = "tests/webui/test_market_tape_ssr_v0.py"
BOUNDARY_TEST_REL = "tests/ops/test_market_surface_ranking_funnel_env_schema_boundary_v0.py"


def _docs_truth_map_chronicle_row(truth_map: str, needle: str) -> str:
    row_start = truth_map.index(needle)
    row_end = truth_map.index("\n", row_start)
    return truth_map[row_start:row_end]


def test_market_tape_ssr_crosslink_package_marker_v1() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER
    assert CROSSLINK_PACKAGE_MARKER in text


def test_docs_truth_map_market_tape_ssr_chronicle_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    row = _docs_truth_map_chronicle_row(
        truth_map, "Market tape readmodel SSR DOCS_TRUTH_MAP static crosslink guard v1"
    )
    for required in (
        SURFACE_REL,
        TAPE_SSR_TEST_REL,
        BOUNDARY_TEST_REL,
        "MARKET_TAPE_SSR_CROSSLINK_GUARD_IMPLEMENTED=true",
        "MARKET_TAPE_SSR_SURFACE_REFERENCED=true",
        "MARKET_TAPE_SSR_TESTS_REFERENCED=true",
        "MARKET_AIRPORT_CREATED_OR_REFERENCED=false",
        "ORDERFLOW_AUTHORIZATION_CREATED=false",
        "non-authorizing",
        "read-only",
    ):
        assert required.lower() in row.lower()


def test_ci_audit_market_tape_ssr_crosslink_v1() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    section_start = ci_audit.index(
        "## Market tape readmodel SSR DOCS_TRUTH_MAP static crosslink v1"
    )
    section_text = ci_audit[section_start : section_start + 3500]
    for required in (
        CROSSLINK_PACKAGE_MARKER,
        "MARKET_TAPE_SSR_CROSSLINK_GUARD_IMPLEMENTED=true",
        "MARKET_TAPE_SSR_SURFACE_REFERENCED=true",
        "MARKET_TAPE_SSR_TESTS_REFERENCED=true",
        "MARKET_AIRPORT_CREATED_OR_REFERENCED=false",
        SURFACE_REL,
        TAPE_SSR_TEST_REL,
        BOUNDARY_TEST_REL,
        "ORDERFLOW_AUTHORIZATION_CREATED=false",
        "READY_FOR_OPERATOR_ARMING_CHANGED=false",
        "non-authorizing",
        "default-off",
    ):
        assert required.lower() in section_text.lower()


def test_market_tape_ssr_surface_referenced_in_docs_v1() -> None:
    surface = PROJECT_ROOT / "docs" / "webui" / "MARKET_SURFACE_V0.md"
    assert surface.is_file()
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    assert SURFACE_REL in truth_map
    assert SURFACE_REL in ci_audit


def test_market_tape_ssr_tests_referenced_in_docs_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    for test_rel in (TAPE_SSR_TEST_REL, BOUNDARY_TEST_REL):
        assert test_rel in truth_map
        assert test_rel in ci_audit


OPERATOR_OVERVIEW_CROSSLINK_PACKAGE_MARKER = (
    "MARKET_OPERATOR_OVERVIEW_IA_V1_DOCS_TRUTH_MAP_CI_AUDIT_STATIC_CROSSLINK_GUARD_V1=true"
)
OPERATOR_OVERVIEW_TEST_PACKAGE_MARKER = (
    "MARKET_OPERATOR_OVERVIEW_IA_V1_DOCS_TRUTH_MAP_CI_AUDIT_CROSSLINK_GUARD_TEST=true"
)
OPERATOR_OVERVIEW_STRUCTURE_TEST_REL = (
    "tests/webui/test_market_dashboard_readonly_structure_contract_v0.py"
)


def test_market_operator_overview_ia_v1_crosslink_package_marker_v1() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert OPERATOR_OVERVIEW_TEST_PACKAGE_MARKER
    assert OPERATOR_OVERVIEW_CROSSLINK_PACKAGE_MARKER in text


def test_docs_truth_map_market_operator_overview_ia_v1_chronicle_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    row = _docs_truth_map_chronicle_row(
        truth_map,
        "Market Dashboard Operator Overview IA v1 DOCS_TRUTH_MAP static crosslink guard v1",
    )
    for required in (
        SURFACE_REL,
        OPERATOR_OVERVIEW_STRUCTURE_TEST_REL,
        BOUNDARY_TEST_REL,
        "MARKET_OPERATOR_OVERVIEW_IA_V1_CROSSLINK_GUARD_IMPLEMENTED=true",
        "MARKET_OPERATOR_OVERVIEW_IA_V1_SURFACE_REFERENCED=true",
        "MARKET_OPERATOR_OVERVIEW_IA_V1_TESTS_REFERENCED=true",
        "MARKET_OPERATOR_OVERVIEW_IA_V1_PR4145_ANCHOR_REFERENCED=true",
        "PR #4145",
        "MARKET_AIRPORT_CREATED_OR_REFERENCED=false",
        "ORDERFLOW_AUTHORIZATION_CREATED=false",
        "non-authorizing",
        "read-only",
        "display-only",
    ):
        assert required.lower() in row.lower()


def test_ci_audit_market_operator_overview_ia_v1_crosslink_v1() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    section_start = ci_audit.index(
        "## Market Dashboard Operator Overview IA v1 DOCS_TRUTH_MAP static crosslink v1"
    )
    section_text = ci_audit[section_start : section_start + 4000]
    for required in (
        OPERATOR_OVERVIEW_CROSSLINK_PACKAGE_MARKER,
        "MARKET_OPERATOR_OVERVIEW_IA_V1_CROSSLINK_GUARD_IMPLEMENTED=true",
        "MARKET_OPERATOR_OVERVIEW_IA_V1_SURFACE_REFERENCED=true",
        "MARKET_OPERATOR_OVERVIEW_IA_V1_TESTS_REFERENCED=true",
        "MARKET_OPERATOR_OVERVIEW_IA_V1_PR4145_ANCHOR_REFERENCED=true",
        "MARKET_AIRPORT_CREATED_OR_REFERENCED=false",
        SURFACE_REL,
        OPERATOR_OVERVIEW_STRUCTURE_TEST_REL,
        BOUNDARY_TEST_REL,
        "ORDERFLOW_AUTHORIZATION_CREATED=false",
        "READY_FOR_OPERATOR_ARMING_CHANGED=false",
        "PR #4145",
        "non-authorizing",
        "display-only",
        "/market",
        "/market/double-play",
    ):
        assert required.lower() in section_text.lower()


def test_market_operator_overview_ia_v1_surface_referenced_in_docs_v1() -> None:
    surface = PROJECT_ROOT / "docs" / "webui" / "MARKET_SURFACE_V0.md"
    assert surface.is_file()
    surface_text = surface.read_text(encoding="utf-8")
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    assert SURFACE_REL in truth_map
    assert SURFACE_REL in ci_audit
    assert "data-market-operator-overview-v1" in surface_text
    assert "Operator overview IA v1" in surface_text


def test_market_operator_overview_ia_v1_tests_referenced_in_docs_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    for test_rel in (OPERATOR_OVERVIEW_STRUCTURE_TEST_REL, BOUNDARY_TEST_REL):
        assert test_rel in truth_map
        assert test_rel in ci_audit


def test_market_kraken_like_operator_enablement_guide_v1_env_boundary_v0() -> None:
    """Kraken-like operator enablement guide tokens stay pinned in MARKET_SURFACE_V0."""
    surface = (PROJECT_ROOT / "docs/webui/MARKET_SURFACE_V0.md").read_text(encoding="utf-8")

    section_start = surface.index(
        "#### Operator enablement (Kraken-like operator overview IA v1 — post #4145–#4150 wave)"
    )
    section_end = surface.index(
        "### Lane taxonomy cross-reference (non-authorizing)", section_start
    )
    guide = surface[section_start:section_end]

    required_tokens = [
        "Observe → Rank → Select → Explain → Double-Play status",
        "display-only",
        "no-authority",
        "information architecture",
        "order placement",
        "no cancel",
        "no arming",
        "no leverage/margin controls",
        "#market-v0-instrument-header",
        "data-market-v0-futures-metrics-strip",
        "data-market-v0-observe-co-presence-v1",
        "data-market-v0-ranking-watchlist",
        "data-market-ai-decision-readout-v1",
        "trading authority=false",
        "data authority=false",
        "source-mode",
        "fixture_offline",
        "unavailable",
        "new route",
        "SPA",
        "new producer",
        "Master V2 / Double Play",
        "decision logic",
        "Market-Airport excluded",
        "tests/webui/test_market_dashboard_readonly_structure_contract_v0.py",
    ]

    for token in required_tokens:
        assert token.lower() in guide.lower(), f"missing enablement guide token: {token!r}"

    forbidden_tokens = [
        "execute_authorized=true",
        "preflight_lift_authorized=true",
        "live_authorized=true",
        "order_authorized=true",
    ]

    for token in forbidden_tokens:
        assert token.lower() not in guide.lower(), f"forbidden token in guide: {token!r}"
