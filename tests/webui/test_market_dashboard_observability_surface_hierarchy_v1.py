"""COMPOSITION_OBSERVABILITY_SURFACE_HIERARCHY_V1 — presentation contracts."""

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

TOKENS = project_root / "static" / "css" / "peak_trade_dashboard_design_tokens_v1.css"
LAYOUT = project_root / "static" / "css" / "peak_trade_dashboard_layout_v1.css"
MARKET_TMPL = project_root / "templates" / "peak_trade_dashboard" / "market_v0.html"
ECONOMIC_TMPL = (
    project_root
    / "templates"
    / "peak_trade_dashboard"
    / "partials"
    / "market_economic_observability_visual_v1.html"
)
LINEAR_TMPL = (
    project_root
    / "templates"
    / "peak_trade_dashboard"
    / "partials"
    / "market_ai_linear_diagnostics_visual_v1.html"
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
def client_observability_hierarchy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[TestClient]:
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
    monkeypatch.setattr(
        "src.data.kraken.fetch_ohlcv_df",
        MagicMock(side_effect=AssertionError("no kraken on futures-first /market")),
    )
    with TestClient(create_app()) as test_client:
        yield test_client


def test_observability_hierarchy_tokens_and_layout_owner() -> None:
    tokens = TOKENS.read_text(encoding="utf-8")
    layout = LAYOUT.read_text(encoding="utf-8")
    assert "--pt-observability-hierarchy-tier-gap: 6px;" in tokens
    assert "--pt-observability-hierarchy-linear-max-height: 72px;" in tokens
    assert "COMPOSITION_OBSERVABILITY_SURFACE_HIERARCHY_V1" in layout
    assert 'data-market-observability-surface-hierarchy-v1="true"' in layout
    assert "var(--pt-observability-hierarchy-linear-max-height)" in layout


def test_market_template_observability_hierarchy_markers_and_order() -> None:
    html = MARKET_TMPL.read_text(encoding="utf-8")
    assert 'data-market-observability-surface-hierarchy-v1="true"' in html
    assert 'data-market-observability-hierarchy-primary-v1="true"' in html
    assert 'data-market-observability-hierarchy-secondary-v1="true"' in html

    # Use HTML landmark sections (last occurrence) — CSS selectors mention landmarks earlier.
    landmarks = [
        "GLOBAL_HEADER",
        "PRIMARY_MARKET_SURFACE",
        "DECISION_SURFACE",
        "OBSERVABILITY_SURFACE",
        "ENGINEERING_DRAWER",
    ]
    positions = [html.rfind(f'data-landmark="{name}"') for name in landmarks]
    assert all(p >= 0 for p in positions)
    assert positions == sorted(positions)

    decision_pos = html.rfind('data-landmark="DECISION_SURFACE"')
    obs_pos = html.rfind('data-landmark="OBSERVABILITY_SURFACE"')
    eng_pos = html.rfind('data-landmark="ENGINEERING_DRAWER"')
    assert decision_pos < obs_pos < eng_pos

    primary_pos = html.find('data-market-observability-hierarchy-primary-v1="true"')
    secondary_pos = html.find('data-market-observability-hierarchy-secondary-v1="true"')
    economic_include = html.find("market_economic_observability_visual_v1.html")
    linear_include = html.find("market_ai_linear_diagnostics_visual_v1.html")
    assert obs_pos < primary_pos < economic_include < secondary_pos < linear_include < eng_pos


def test_observability_partial_markers_stable() -> None:
    economic = ECONOMIC_TMPL.read_text(encoding="utf-8")
    linear = LINEAR_TMPL.read_text(encoding="utf-8")
    assert 'data-market-observability-hierarchy-economic-v1="true"' in economic
    assert 'data-market-economic-observability-visual-v1="true"' in economic
    assert 'data-market-read-only="true"' in economic
    assert 'data-market-observability-hierarchy-linear-v1="true"' in linear
    assert 'data-market-ai-linear-diagnostics-visual-v1="true"' in linear
    assert 'data-market-read-only="true"' in linear


def test_ssr_observability_hierarchy_readonly_and_order(
    client_observability_hierarchy: TestClient,
) -> None:
    response = client_observability_hierarchy.get("/market?timeframe=1h")
    assert response.status_code == 200
    html = response.text
    assert 'data-market-observability-surface-hierarchy-v1="true"' in html
    assert 'data-market-observability-hierarchy-primary-v1="true"' in html
    assert 'data-market-observability-hierarchy-secondary-v1="true"' in html
    assert 'data-market-observability-hierarchy-economic-v1="true"' in html
    assert 'data-market-observability-hierarchy-linear-v1="true"' in html
    assert 'data-market-readonly="true"' in html or 'data-market-read-only="true"' in html
    assert 'data-market-trading-authority-v1="false"' in html
    assert 'data-market-non-authorizing="true"' in html or "non-authorizing" in html.lower()
    assert "BTCUSDT" not in html
    assert "bitcoin" not in html.lower()
    assert html.find('data-landmark="DECISION_SURFACE"') < html.find(
        'data-landmark="OBSERVABILITY_SURFACE"'
    )
    assert html.find('data-market-observability-hierarchy-primary-v1="true"') < html.find(
        'data-market-observability-hierarchy-secondary-v1="true"'
    )
    assert html.find('data-market-economic-observability-visual-v1="true"') < html.find(
        'data-market-ai-linear-diagnostics-visual-v1="true"'
    )
    assert not re.search(
        r'data-landmark="ENGINEERING_DRAWER"[\s\S]{0,400}<details[^>]*\sopen',
        html,
    )


def test_no_new_python_observability_runtime_owner() -> None:
    webui = project_root / "src" / "webui"
    unexpected = list(webui.glob("*observability*hierarchy*")) + list(
        webui.glob("*composition*observability*")
    )
    assert unexpected == []
    assert LAYOUT.is_file()
    assert TOKENS.is_file()
    assert MARKET_TMPL.is_file()
