"""Phase 1A composition foundation — landmark order, eye path, engineering drawer."""

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
def client_phase1a_comp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[TestClient]:
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


def _body(client: TestClient) -> str:
    resp = client.get("/market?timeframe=1h")
    assert resp.status_code == 200
    return re.sub(r"<style>.*?</style>", "", resp.text, flags=re.S)


def test_phase1a_exactly_one_global_header_and_safety_rail(client_phase1a_comp: TestClient) -> None:
    body = _body(client_phase1a_comp)
    assert body.count('data-landmark="GLOBAL_HEADER"') == 1
    assert body.count('data-landmark-global-header="true"') == 1
    assert body.count('data-market-phase-1a-global-header-v1="true"') == 1
    assert body.count('data-market-phase-1a-single-safety-rail-v1="true"') == 1
    assert body.count('aria-label="Visual operator safety rail"') == 1
    assert body.count('aria-label="System status rail"') == 0


def test_phase1a_landmark_dom_order(client_phase1a_comp: TestClient) -> None:
    body = _body(client_phase1a_comp)
    markers = [
        'data-landmark="GLOBAL_HEADER"',
        'data-landmark="PRIMARY_MARKET_SURFACE"',
        'data-landmark="DECISION_SURFACE"',
        'data-landmark="OBSERVABILITY_SURFACE"',
        'data-landmark="ENGINEERING_DRAWER"',
    ]
    idxs = [body.find(m) for m in markers]
    assert all(i >= 0 for i in idxs)
    assert idxs == sorted(idxs)


def test_phase1a_eye_path_chart_before_decision_narrative(client_phase1a_comp: TestClient) -> None:
    """Reductive composition: primary decision precedes chart; DECISION_SURFACE stays after."""
    body = _body(client_phase1a_comp)
    chart_i = body.find('data-market-phase-1a-chart-above-fold-v1="true"')
    narrative_i = body.find('data-market-operator-decision-narrative-v1="true"')
    post_i = body.find('data-market-phase1a-post-chart-decision-v1="true"')
    decision_surface_i = body.find('data-landmark="DECISION_SURFACE"')
    assert min(chart_i, narrative_i, post_i, decision_surface_i) >= 0
    assert narrative_i < chart_i
    assert post_i < chart_i
    assert chart_i < decision_surface_i


def test_phase1a_no_duplicate_decision_narrative(client_phase1a_comp: TestClient) -> None:
    body = _body(client_phase1a_comp)
    assert body.count('data-market-operator-decision-narrative-v1="true"') == 1
    assert body.count('data-market-phase-2-decision-sentence-v1="true"') == 1


def test_phase1a_engineering_drawer_default_closed(client_phase1a_comp: TestClient) -> None:
    body = _body(client_phase1a_comp)
    assert body.count('data-landmark="ENGINEERING_DRAWER"') == 1
    for marker in (
        'data-market-system-governance-details-v1="true"',
        'data-market-diagnostics-drawer-v1="true"',
        'data-market-remodel-detail-anchors-v2="true"',
    ):
        m = re.search(rf"<details[^>]*{re.escape(marker)}[^>]*>", body)
        assert m is not None, marker
        assert " open" not in m.group(0)


def test_phase1a_no_level4_visible_open_details(client_phase1a_comp: TestClient) -> None:
    body = _body(client_phase1a_comp)
    # Engineering / secondary technical dumps must not render open by default.
    for marker in (
        'data-market-phase-1a-secondary-instrument-details-v1="true"',
        'data-market-system-governance-details-v1="true"',
        'data-market-diagnostics-drawer-v1="true"',
        'data-market-remodel-detail-anchors-v2="true"',
    ):
        m = re.search(rf"<details[^>]*{re.escape(marker)}[^>]*>", body)
        assert m is not None
        assert " open" not in m.group(0)


def test_phase1a_no_duplicate_authority_orders_live_primary(
    client_phase1a_comp: TestClient,
) -> None:
    body = _body(client_phase1a_comp)
    assert body.count("data-market-visual-operator-runtime-authority=") == 1
    assert 'data-market-visual-operator-orders-allowed="false"' in body
    assert 'data-market-visual-operator-live-allowed="false"' in body
    assert body.count("data-market-visual-operator-orders-allowed=") == 1
    assert body.count("data-market-visual-operator-live-allowed=") == 1


def test_phase1a_chart_before_observability_and_engineering(
    client_phase1a_comp: TestClient,
) -> None:
    body = _body(client_phase1a_comp)
    chart_i = body.find('data-market-phase-1a-chart-above-fold-v1="true"')
    obs_i = body.find('data-landmark="OBSERVABILITY_SURFACE"')
    eng_i = body.find('data-landmark="ENGINEERING_DRAWER"')
    assert min(chart_i, obs_i, eng_i) >= 0
    assert chart_i < obs_i < eng_i


def test_phase1a_consumer_only_markers_preserved(client_phase1a_comp: TestClient) -> None:
    body = _body(client_phase1a_comp)
    assert 'data-market-readonly="true"' in body
    assert 'data-market-non-authorizing="true"' in body
    assert 'data-market-trading-authority-v1="false"' in body
    assert re.search(r'type=["\']submit["\']', body, re.I) is None
