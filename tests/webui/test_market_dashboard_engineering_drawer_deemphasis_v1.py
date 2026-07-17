"""COMPOSITION_ENGINEERING_DRAWER_DEEMPHASIS_V1 — presentation contracts."""

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
DIAGNOSTICS_TMPL = (
    project_root
    / "templates"
    / "peak_trade_dashboard"
    / "partials"
    / "market_diagnostics_drawer_v1.html"
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
def client_engineering_deemphasis(
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


def test_engineering_deemphasis_tokens_and_layout_owner() -> None:
    tokens = TOKENS.read_text(encoding="utf-8")
    layout = LAYOUT.read_text(encoding="utf-8")
    assert "--pt-engineering-deemphasis-detail-gap: 2px;" in tokens
    assert "--pt-engineering-deemphasis-closed-padding-y: 4px;" in tokens
    assert "COMPOSITION_ENGINEERING_DRAWER_DEEMPHASIS_V1" in layout
    assert 'data-market-engineering-drawer-deemphasis-v1="true"' in layout
    assert "var(--pt-engineering-deemphasis-detail-gap)" in layout


def test_market_template_engineering_deemphasis_markers_and_landmark_order() -> None:
    html = MARKET_TMPL.read_text(encoding="utf-8")
    assert 'data-market-engineering-drawer-deemphasis-v1="true"' in html
    assert 'data-market-engineering-hierarchy-tier="tertiary"' in html
    assert 'data-market-engineering-hierarchy-tertiary-label-v1="true"' in html
    assert 'data-market-engineering-deemphasis-detail-v1="true"' in html

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

    assert html.find('data-market-observability-hierarchy-primary-v1="true"') < html.find(
        'data-market-observability-hierarchy-secondary-v1="true"'
    )
    assert html.find('data-landmark="OBSERVABILITY_SURFACE"') < html.find(
        'data-landmark="ENGINEERING_DRAWER"'
    )
    assert html.find('data-market-primary-page-share-dominance-v1="true"') >= 0 or (
        "primary-page-share-dominance" in html
    )


def test_diagnostics_drawer_deemphasis_markers() -> None:
    html = DIAGNOSTICS_TMPL.read_text(encoding="utf-8")
    assert 'data-market-engineering-deemphasis-detail-v1="true"' in html
    assert 'data-market-diagnostics-drawer-v1="true"' in html
    assert "text-sm font-semibold text-slate-400" not in html
    assert "text-[10px] font-medium text-slate-600" in html
    assert " open" not in html.split(">", 1)[0]


def test_ssr_engineering_deemphasis_readonly_closed_and_hierarchy(
    client_engineering_deemphasis: TestClient,
) -> None:
    response = client_engineering_deemphasis.get("/market?timeframe=1h")
    assert response.status_code == 200
    html = response.text

    assert 'data-market-engineering-drawer-deemphasis-v1="true"' in html
    assert 'data-market-engineering-hierarchy-tier="tertiary"' in html
    assert 'data-market-observability-hierarchy-primary-v1="true"' in html
    assert 'data-market-observability-hierarchy-secondary-v1="true"' in html
    assert 'data-market-observability-hierarchy-economic-v1="true"' in html
    assert 'data-market-observability-hierarchy-linear-v1="true"' in html
    assert 'data-market-readonly="true"' in html or 'data-market-read-only="true"' in html
    assert 'data-market-trading-authority-v1="false"' in html
    assert 'data-market-visual-operator-orders-allowed="false"' in html
    assert 'data-market-visual-operator-live-allowed="false"' in html
    assert "BTCUSDT" not in html
    assert "bitcoin" not in html.lower()

    for marker in (
        'data-market-system-governance-details-v1="true"',
        'data-market-diagnostics-drawer-v1="true"',
        'data-market-remodel-detail-anchors-v2="true"',
    ):
        m = re.search(rf"<details[^>]*{re.escape(marker)}[^>]*>", html)
        assert m is not None, marker
        assert " open" not in m.group(0)

    assert not re.search(
        r'data-landmark="ENGINEERING_DRAWER"[\s\S]{0,500}<details[^>]*\sopen',
        html,
    )
    assert html.find('data-landmark="PRIMARY_MARKET_SURFACE"') < html.find(
        'data-landmark="DECISION_SURFACE"'
    )
    assert html.find('data-market-observability-hierarchy-primary-v1="true"') < html.find(
        'data-market-observability-hierarchy-secondary-v1="true"'
    )
    assert html.find('data-landmark="OBSERVABILITY_SURFACE"') < html.find(
        'data-landmark="ENGINEERING_DRAWER"'
    )


def test_no_new_python_engineering_deemphasis_runtime_owner() -> None:
    webui = project_root / "src" / "webui"
    unexpected = list(webui.glob("*engineering*deemphasis*")) + list(
        webui.glob("*composition*engineering*")
    )
    assert unexpected == []
    assert LAYOUT.is_file()
    assert TOKENS.is_file()
    assert MARKET_TMPL.is_file()
