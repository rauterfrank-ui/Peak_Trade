"""COMPOSITION_DECISION_SURFACE_HIERARCHY_V1 — presentation contracts."""

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
FUNNEL_TMPL = (
    project_root
    / "templates"
    / "peak_trade_dashboard"
    / "partials"
    / "market_decision_funnel_visual_v1.html"
)
TOP20_TMPL = (
    project_root
    / "templates"
    / "peak_trade_dashboard"
    / "partials"
    / "market_governed_top20_primary_v1.html"
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
def client_decision_hierarchy(
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


def test_decision_hierarchy_tokens_and_layout_owner() -> None:
    tokens = TOKENS.read_text(encoding="utf-8")
    layout = LAYOUT.read_text(encoding="utf-8")
    assert "--pt-decision-hierarchy-primary-matrix-max-height: 220px;" in tokens
    assert "--pt-decision-hierarchy-funnel-stages-max-height: 64px;" in tokens
    assert "--pt-decision-hierarchy-secondary-matrix-max-height: 48px;" in tokens
    assert "--pt-decision-hierarchy-tertiary-module-max-height: 152px;" in tokens
    assert "COMPOSITION_DECISION_SURFACE_HIERARCHY_V1" in layout
    assert 'data-market-decision-surface-hierarchy-v1="true"' in layout
    assert "var(--pt-decision-hierarchy-primary-matrix-max-height)" in layout
    # Prior landmark rhythm tokens remain distinct.
    assert "--pt-landmark-gap-primary-to-decision: 20px;" in tokens


def test_market_template_decision_hierarchy_markers_and_order() -> None:
    html = MARKET_TMPL.read_text(encoding="utf-8")
    assert 'data-market-decision-surface-hierarchy-v1="true"' in html
    assert 'data-market-decision-hierarchy-primary-v1="true"' in html
    assert 'data-market-decision-hierarchy-secondary-v1="true"' in html
    assert 'data-market-decision-hierarchy-tertiary-v1="true"' in html
    assert 'data-market-decision-secondary-group-v1="true"' in html

    landmarks = [
        "GLOBAL_HEADER",
        "PRIMARY_MARKET_SURFACE",
        "DECISION_SURFACE",
        "OBSERVABILITY_SURFACE",
        "ENGINEERING_DRAWER",
    ]
    positions = [html.find(f'data-landmark="{name}"') for name in landmarks]
    assert all(p >= 0 for p in positions)
    assert positions == sorted(positions)

    primary_pos = html.find('data-market-decision-hierarchy-primary-v1="true"')
    secondary_pos = html.find('data-market-decision-hierarchy-secondary-v1="true"')
    tertiary_pos = html.find('data-market-decision-hierarchy-tertiary-v1="true"')
    assert 0 <= primary_pos < secondary_pos < tertiary_pos

    # Top-20 include remains inside primary hierarchy slot; funnel inside secondary.
    top20_include = html.find("market_governed_top20_primary_v1.html")
    funnel_include = html.find("market_decision_funnel_visual_v1.html")
    assert primary_pos < top20_include < secondary_pos < funnel_include < tertiary_pos

    # Engineering remains last landmark and collapsed via details (no open attr in template).
    eng = html[html.find('data-landmark="ENGINEERING_DRAWER"') :]
    assert eng.find("<details") >= 0
    assert 'open="' not in eng.split("{% endblock %}")[0][:800]


def test_hierarchy_partial_markers_stable() -> None:
    top20 = TOP20_TMPL.read_text(encoding="utf-8")
    funnel = FUNNEL_TMPL.read_text(encoding="utf-8")
    assert 'data-market-decision-hierarchy-top20-v1="true"' in top20
    assert 'data-market-governed-top20-primary-v1="true"' in top20
    assert 'data-market-decision-hierarchy-funnel-v1="true"' in funnel
    assert 'data-market-decision-funnel-visual-v1="true"' in funnel
    assert 'data-market-read-only="true"' in funnel


def test_ssr_market_hierarchy_readonly_and_no_second_truth(
    client_decision_hierarchy: TestClient,
) -> None:
    response = client_decision_hierarchy.get("/market?timeframe=1h")
    assert response.status_code == 200
    html = response.text
    assert 'data-market-decision-surface-hierarchy-v1="true"' in html
    assert 'data-market-decision-hierarchy-primary-v1="true"' in html
    assert 'data-market-decision-hierarchy-secondary-v1="true"' in html
    assert 'data-market-decision-hierarchy-tertiary-v1="true"' in html
    assert 'data-market-readonly="true"' in html or 'data-market-read-only="true"' in html
    assert 'data-market-trading-authority-v1="false"' in html
    assert 'data-market-non-authorizing="true"' in html or "non-authorizing" in html.lower()
    assert "data-market-live-locked-v1" in html or "no live" in html.lower()
    # No invented second business authority surface.
    assert "authorize-trade" not in html.lower()
    assert "place-order" not in html.lower()
    # Hierarchy order in rendered SSR.
    assert html.find('data-market-decision-hierarchy-primary-v1="true"') < html.find(
        'data-market-decision-hierarchy-secondary-v1="true"'
    )
    assert html.find('data-market-decision-hierarchy-secondary-v1="true"') < html.find(
        'data-market-decision-hierarchy-tertiary-v1="true"'
    )
    # Top-N navigation remains present.
    assert "data-market-governed-topn-toolbar-v1" in html or "data-market-governed-top-n" in html
    # Futures-only / no-bitcoin contract surface remains for default selection.
    assert "BTCUSDT" not in html
    assert "bitcoin" not in html.lower()
    # Engineering drawer closed by default.
    assert not re.search(
        r'data-landmark="ENGINEERING_DRAWER"[\s\S]{0,400}<details[^>]*\sopen',
        html,
    )


def test_no_new_python_domain_or_runtime_decision_owner() -> None:
    """Slice is templates/CSS only — no new Python decision/runtime owner modules."""
    webui = project_root / "src" / "webui"
    unexpected = list(webui.glob("*decision*hierarchy*")) + list(
        webui.glob("*composition*hierarchy*")
    )
    assert unexpected == []
    # Canonical owners stay the existing dashboard CSS/templates.
    assert LAYOUT.is_file()
    assert TOKENS.is_file()
    assert MARKET_TMPL.is_file()
