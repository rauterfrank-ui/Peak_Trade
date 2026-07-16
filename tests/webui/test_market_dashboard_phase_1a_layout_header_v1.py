"""Phase 1A layout contracts: single safety rail + chart after compact hero."""

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
def client_phase_1a(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[TestClient]:
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


def test_phase_1a_single_safety_rail(client_phase_1a: TestClient) -> None:
    body = _html(client_phase_1a)
    # Count attribute occurrences outside the <style> block.
    body_wo_style = re.sub(r"<style>.*?</style>", "", body, flags=re.S)
    assert body_wo_style.count('data-market-phase-1a-single-safety-rail-v1="true"') == 1
    assert body_wo_style.count('data-market-system-status-rail-v1="true"') == 1
    assert body_wo_style.count('data-market-visual-operator-header-v1="true"') == 1
    assert 'data-market-phase-1a-primary-status-count-v1="8"' in body_wo_style


def test_phase_1a_no_duplicate_prominent_status_rails(client_phase_1a: TestClient) -> None:
    body = _html(client_phase_1a)
    # Legacy standalone rail section removed; markers live on the single rail only.
    assert body.count('aria-label="System status rail"') == 0
    assert body.count('aria-label="Visual operator safety rail"') == 1


def test_phase_1a_chart_dom_order_after_header_and_hero(client_phase_1a: TestClient) -> None:
    body = re.sub(r"<style>.*?</style>", "", _html(client_phase_1a), flags=re.S)
    header_i = body.find('data-market-phase-1a-global-header-v1="true"')
    rail_i = body.find('data-market-phase-1a-single-safety-rail-v1="true"')
    hero_i = body.find('data-market-phase-1a-hero-compact-v1="true"')
    chart_i = body.find('data-market-phase-1a-chart-above-fold-v1="true"')
    secondary_i = body.find('data-market-phase-1a-secondary-instrument-details-v1="true"')
    assert min(header_i, rail_i, hero_i, chart_i) >= 0
    assert header_i < rail_i < hero_i < chart_i
    if secondary_i >= 0:
        assert chart_i < secondary_i


def test_phase_1a_technical_dump_not_primary(client_phase_1a: TestClient) -> None:
    body = _html(client_phase_1a)
    assert 'data-market-phase-1a-secondary-instrument-details-v1="true"' in body
    # Secondary details must be collapsed by default (no open attribute on the details tag).
    m = re.search(
        r"<details[^>]*data-market-phase-1a-secondary-instrument-details-v1=\"true\"[^>]*>",
        body,
    )
    assert m is not None
    assert " open" not in m.group(0)
    assert 'data-market-operator-decision-narrative-v1="true"' in body
    assert 'data-market-phase-1a-compact-metadata-row-v1="true"' in body


def test_phase_1a_no_mutating_controls_or_forbidden_authority(client_phase_1a: TestClient) -> None:
    body = _html(client_phase_1a)
    assert 'data-market-trading-authority-v1="false"' in body
    assert 'data-market-visual-operator-orders-allowed="false"' in body
    assert 'data-market-visual-operator-live-allowed="false"' in body
    assert 'data-market-visual-operator-runtime-authority="NONE"' in body
    assert re.search(r'type=["\']submit["\']', body, re.I) is None
    assert "BTCUSDT" not in body


def test_phase_1a_governance_still_collapsed(client_phase_1a: TestClient) -> None:
    body = _html(client_phase_1a)
    assert 'data-market-system-governance-details-v1="true"' in body
    m = re.search(
        r"<details[^>]*data-market-system-governance-details-v1=\"true\"[^>]*>",
        body,
    )
    assert m is not None
    assert " open" not in m.group(0)


def test_phase_1a_context_markers_preserved(client_phase_1a: TestClient) -> None:
    body = _html(client_phase_1a)
    assert 'data-market-workspace-f5-strip-v1="true"' in body
    assert 'data-market-workspace-contract-metadata-v1="true"' in body
    assert 'data-market-chart-above-fold-v1="true"' in body
    assert 'data-market-phase-1a-layout-v1="true"' in body
