"""Phase 1B: design tokens, self-only assets, responsive grid, Phase 1A regression."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

from src.webui.app import create_app
from src.webui.futures_read_only_market_dashboard_runtime_v0 import (
    ENV_BUNDLE_ROOT as F5_ENV_BUNDLE_ROOT,
    ENV_ENABLED as F5_ENV_ENABLED,
)
from src.webui.market_futures_ohlcv_runtime_v0 import (
    ENV_BUNDLE_ROOT as OHLCV_ENV_BUNDLE_ROOT,
    ENV_ENABLED as OHLCV_ENV_ENABLED,
)
from src.webui.market_ranking_funnel_runtime_v0 import (
    ENV_BUNDLE_ROOT as RANKING_ENV_BUNDLE_ROOT,
    ENV_ENABLED as RANKING_ENV_ENABLED,
)
from src.webui.market_visual_operator_surface_v1 import (
    ENV_EVIDENCE_ROOT,
)

TOKEN_OWNER = (
    project_root / "static" / "css" / "peak_trade_dashboard_design_tokens_v1.css"
).resolve()
REQUIRED_TOKEN_VARS = (
    "--pt-content-max-width",
    "--pt-page-padding",
    "--pt-grid-gap",
    "--pt-card-padding",
    "--pt-card-radius",
    "--pt-card-border",
    "--pt-header-height",
    "--pt-safety-rail-max-height",
    "--pt-hero-min-height",
    "--pt-hero-max-height",
    "--pt-primary-chart-min-height",
    "--pt-font-family",
    "--pt-mono-font",
    "--pt-font-size-xs",
    "--pt-font-size-sm",
    "--pt-font-size-md",
    "--pt-font-size-lg",
    "--pt-font-size-xl",
    "--pt-line-height",
    "--pt-color-background",
    "--pt-color-surface-1",
    "--pt-color-surface-2",
    "--pt-color-border",
    "--pt-color-text-primary",
    "--pt-color-text-secondary",
    "--pt-color-positive",
    "--pt-color-negative",
    "--pt-color-warning",
    "--pt-color-info",
    "--pt-color-model",
    "--pt-color-muted",
)
FORBIDDEN_CDN_FRAGMENTS = (
    "cdn.tailwindcss.com",
    "cdn.jsdelivr.net",
    "unpkg.com",
    "cdnjs.cloudflare.com",
)
RANKING_FIXTURE = (
    project_root / "tests" / "fixtures" / "market_ranking_funnel_readmodel_v0" / "complete_minimal"
).resolve()
OHLCV_FIXTURE = (
    project_root / "tests" / "fixtures" / "market_futures_ohlcv_readmodel_v0" / "complete_minimal"
).resolve()
F5_FIXTURE = (
    project_root
    / "tests"
    / "fixtures"
    / "futures_read_only_market_dashboard_v0"
    / "complete_minimal"
).resolve()


@pytest.fixture()
def client_phase_1b(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[TestClient]:
    evidence = tmp_path / "economic_evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "compact_decision_funnel.json").write_text(
        '{"bar_count": 0, "trade_count": 0, "stages": {}}', encoding="utf-8"
    )
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2030-01-15T12:34:56.000000+00:00")
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    monkeypatch.setenv(OHLCV_ENV_ENABLED, "1")
    monkeypatch.setenv(OHLCV_ENV_BUNDLE_ROOT, str(OHLCV_FIXTURE))
    monkeypatch.setenv(F5_ENV_ENABLED, "1")
    monkeypatch.setenv(F5_ENV_BUNDLE_ROOT, str(F5_FIXTURE))
    monkeypatch.setenv(ENV_EVIDENCE_ROOT, str(evidence))
    kraken_mock = MagicMock(
        side_effect=AssertionError("fetch_ohlcv_df must not run on futures-first /market")
    )
    monkeypatch.setattr("src.data.kraken.fetch_ohlcv_df", kraken_mock)
    with TestClient(create_app()) as test_client:
        yield test_client


def _html(client: TestClient) -> str:
    resp = client.get("/market?timeframe=1h")
    assert resp.status_code == 200
    return resp.text


def test_canonical_design_token_owner_unique_v1() -> None:
    assert TOKEN_OWNER.is_file()
    text = TOKEN_OWNER.read_text(encoding="utf-8")
    assert "CANONICAL_OWNER" in text
    for var in REQUIRED_TOKEN_VARS:
        assert var in text
    css_root = project_root / "static" / "css"
    other_roots = []
    for path in css_root.glob("*.css"):
        if path.resolve() == TOKEN_OWNER:
            continue
        other = path.read_text(encoding="utf-8")
        if re.search(r":root\s*\{[^}]*--pt-content-max-width", other, re.S):
            other_roots.append(path.name)
    assert other_roots == [], f"duplicate token roots: {other_roots}"


def test_no_forbidden_cdn_in_market_render_path_v1(client_phase_1b: TestClient) -> None:
    html = _html(client_phase_1b)
    for frag in FORBIDDEN_CDN_FRAGMENTS:
        assert frag not in html
    assert 'data-market-design-token-owner-v1="true"' in html
    assert 'data-canonical-design-token-owner="true"' in html
    assert "/static/css/peak_trade_dashboard_design_tokens_v1.css" in html
    assert "/static/css/peak_trade_dashboard_utilities_v1.css" in html
    assert "/static/vendor/chartjs/4.4.1/chart.umd.min.js" in html
    assert 'data-market-network-allowlist-v1="self-only"' in html
    assert 'content="self-only"' in html


def test_self_only_asset_allowlist_from_html_v1(client_phase_1b: TestClient) -> None:
    html = _html(client_phase_1b)
    external = re.findall(
        r"""(?:src|href)=["'](https?://[^"']+)["']""",
        html,
        flags=re.I,
    )
    # Navigation companion link may point at local companion UI; page-load assets must be self.
    asset_like = [
        u
        for u in external
        if any(
            u.lower().endswith(ext) for ext in (".css", ".js", ".mjs", ".map", ".woff2", ".woff")
        )
        or "cdn." in u.lower()
        or "jsdelivr" in u.lower()
        or "tailwindcss" in u.lower()
    ]
    assert asset_like == [], f"unexpected external assets: {asset_like}"


def test_no_duplicate_core_tokens_in_dashboard_templates_v1() -> None:
    templates = project_root / "templates" / "peak_trade_dashboard"
    offenders: list[str] = []
    for path in templates.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        if "--pt-content-max-width" in text or "--pt-header-height" in text:
            offenders.append(str(path.relative_to(project_root)))
        if re.search(r":root\s*\{", text) and "--pt-" in text:
            offenders.append(str(path.relative_to(project_root)))
    assert offenders == []


def test_responsive_grid_contract_markers_v1(client_phase_1b: TestClient) -> None:
    html = _html(client_phase_1b)
    assert "pt-dashboard-shell" in html
    assert 'data-market-phase-1b-design-system-v1="true"' in html
    assert 'data-market-global-overflow-contained-v1="true"' in html
    assert "market-phase-1a-layout" in html
    layout_css = (project_root / "static" / "css" / "peak_trade_dashboard_layout_v1.css").read_text(
        encoding="utf-8"
    )
    assert "overflow-x: clip" in layout_css
    assert "var(--pt-content-max-width)" in layout_css
    assert "var(--pt-grid-gap)" in layout_css


def test_phase_1a_regression_single_safety_rail_and_chart_v1(client_phase_1b: TestClient) -> None:
    html = _html(client_phase_1b)
    assert html.count("market-phase-1a-safety-rail") >= 1
    assert "market-phase-1a-primary-chart" in html or "market-primary-close-chart" in html
    assert 'data-market-visual-operator-header-v1="true"' in html or (
        "market-visual-operator-header" in html
    )
    assert "LIVE_AUTHORIZED_NOW=true" not in html
    assert "ORDER_AUTHORIZED_NOW" not in html


def test_dashboard_remains_consumer_only_no_semantics_mutation_v1(
    client_phase_1b: TestClient,
) -> None:
    html = _html(client_phase_1b)
    for token in (
        "LIVE_AUTHORIZED_NOW=true",
        "ORDERS_ALLOWED=true",
        "TRUTH_GO_AUTHORIZED",
        "fetch_ohlcv_df must not run",
    ):
        assert token not in html
    assert 'method="POST"' not in html
    assert "method='POST'" not in html


def test_static_token_and_utility_assets_served_v1(client_phase_1b: TestClient) -> None:
    for path in (
        "/static/css/peak_trade_dashboard_design_tokens_v1.css",
        "/static/css/peak_trade_dashboard_layout_v1.css",
        "/static/css/peak_trade_dashboard_utilities_v1.css",
        "/static/vendor/chartjs/4.4.1/chart.umd.min.js",
    ):
        resp = client_phase_1b.get(path)
        assert resp.status_code == 200, path
        assert len(resp.content) > 100
