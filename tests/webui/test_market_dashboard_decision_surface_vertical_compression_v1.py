"""COMPOSITION_DECISION_SURFACE_VERTICAL_COMPRESSION_V1 — presentation contracts."""

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
PLAN = (
    project_root
    / "docs"
    / "product"
    / "evidence"
    / "composition_rebaseline_next_slice_v1_20260717T001413Z"
    / "next_slice_plan.md"
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
def client_decision_compression(
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


def test_authorized_slice_title_still_points_to_decision_compression() -> None:
    text = PLAN.read_text(encoding="utf-8")
    assert "COMPOSITION_DECISION_SURFACE_VERTICAL_COMPRESSION_V1" in text


def test_decision_compression_tokens_and_layout_owner() -> None:
    tokens = TOKENS.read_text(encoding="utf-8")
    layout = LAYOUT.read_text(encoding="utf-8")
    assert "--pt-decision-matrix-max-height:" in tokens
    assert "--pt-decision-table-row-height:" in tokens
    assert "--pt-decision-secondary-gap:" in tokens
    assert "COMPOSITION_DECISION_SURFACE_VERTICAL_COMPRESSION_V1" in layout
    assert 'data-market-decision-surface-vertical-compression-v1="true"' in layout
    assert "max-height: var(--pt-decision-matrix-max-height)" in layout


def test_market_template_decision_compression_markers() -> None:
    html = MARKET_TMPL.read_text(encoding="utf-8")
    assert 'data-landmark="DECISION_SURFACE"' in html
    assert 'data-market-decision-surface-vertical-compression-v1="true"' in html
    assert 'data-market-decision-secondary-dense-v1="true"' in html
    order = [
        "GLOBAL_HEADER",
        "PRIMARY_MARKET_SURFACE",
        "DECISION_SURFACE",
        "OBSERVABILITY_SURFACE",
        "ENGINEERING_DRAWER",
    ]
    positions = [html.find(f'data-landmark="{name}"') for name in order]
    assert all(p >= 0 for p in positions)
    assert positions == sorted(positions)


def test_ssr_decision_compression_and_readonly_markers(
    client_decision_compression: TestClient,
) -> None:
    resp = client_decision_compression.get("/market?timeframe=1h")
    assert resp.status_code == 200
    body = resp.text
    assert 'data-market-decision-surface-vertical-compression-v1="true"' in body
    assert 'data-market-decision-matrix-vertical-scroll-v1="true"' in body
    assert 'data-market-readonly="true"' in body
    assert 'data-market-live-locked-v1="true"' in body
    assert 'data-market-non-authorizing="true"' in body
    assert 'data-market-trading-authority-v1="false"' in body
    assert re.search(
        r'class="[^"]*grid-cols-1[^"]*lg:grid-cols-4[^"]*"[^>]*'
        r'data-market-remodel-secondary-grid-v2="true"',
        body,
    )
