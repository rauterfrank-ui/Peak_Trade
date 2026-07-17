"""COMPOSITION_LANDMARK_VERTICAL_RHYTHM_V1 — presentation contracts."""

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
def client_landmark_rhythm(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[TestClient]:
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


def test_landmark_rhythm_tokens_and_layout_owner() -> None:
    tokens = TOKENS.read_text(encoding="utf-8")
    layout = LAYOUT.read_text(encoding="utf-8")
    assert "--pt-landmark-gap-primary-to-decision: 20px;" in tokens
    assert "--pt-landmark-gap-decision-to-observability: 20px;" in tokens
    assert "--pt-landmark-gap-observability-to-engineering: 20px;" in tokens
    assert "--pt-landmark-gap-header-to-primary: 8px;" in tokens
    assert "COMPOSITION_LANDMARK_VERTICAL_RHYTHM_V1" in layout
    assert 'data-market-landmark-vertical-rhythm-v1="true"' in layout
    assert "var(--pt-landmark-gap-primary-to-decision)" in layout
    # Internal decision densify token must remain distinct from landmark rhythm.
    assert "--pt-decision-section-gap: 2px;" in tokens


def test_market_template_landmark_rhythm_markers_and_order() -> None:
    html = MARKET_TMPL.read_text(encoding="utf-8")
    assert 'data-market-landmark-vertical-rhythm-v1="true"' in html
    assert 'data-market-primary-page-share-dominance-v1="true"' in html
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
    # Tailwind abutting margins removed from landmark sections (rhythm owns spacing).
    assert not re.search(
        r'<section\s+class="mt-[23]"\s+data-landmark="DECISION_SURFACE"',
        html,
    )
    assert not re.search(
        r'<section\s+class="mt-[23]"\s+data-landmark="OBSERVABILITY_SURFACE"',
        html,
    )


def test_ssr_landmark_rhythm_and_readonly_markers(
    client_landmark_rhythm: TestClient,
) -> None:
    resp = client_landmark_rhythm.get("/market?timeframe=1h")
    assert resp.status_code == 200
    body = resp.text
    assert 'data-market-landmark-vertical-rhythm-v1="true"' in body
    assert 'data-market-primary-page-share-dominance-v1="true"' in body
    assert 'data-market-readonly="true"' in body
    assert 'data-market-non-authorizing="true"' in body
    assert 'data-market-trading-authority-v1="false"' in body
    assert 'data-landmark="GLOBAL_HEADER"' in body
    assert 'data-landmark="PRIMARY_MARKET_SURFACE"' in body
    assert 'data-landmark="DECISION_SURFACE"' in body
    assert 'data-landmark="OBSERVABILITY_SURFACE"' in body
    assert 'data-landmark="ENGINEERING_DRAWER"' in body
