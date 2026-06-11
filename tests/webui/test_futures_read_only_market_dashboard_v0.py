"""F5 Futures Read-only Market Dashboard v0 (GET /market/futures) — SSR contract tests."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

from src.webui.app import create_app
from src.webui.futures_read_only_market_dashboard_runtime_v0 import (
    ENV_BUNDLE_ROOT,
    ENV_ENABLED,
    STATUS_MODEL_VALUES,
    build_futures_read_only_market_dashboard_display_context,
)

F5_BANNER = (
    "Futures dashboard is read-only. No orders, no sessions, "
    "no testnet activation, no Live authorization."
)
KRAKEN_LABEL_WARNING = (
    "Metadata label only. No governed Kraken Futures adapter or futures execution path proven."
)

FIXTURE_BUNDLE = (
    project_root
    / "tests"
    / "fixtures"
    / "futures_read_only_market_dashboard_v0"
    / "complete_minimal"
).resolve()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture()
def client_f5_fixture_on(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(FIXTURE_BUNDLE))
    with TestClient(create_app()) as test_client:
        yield test_client


def _html(client: TestClient, path: str = "/market/futures") -> str:
    response = client.get(path)
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    return response.text


def test_f5_market_dashboard_route_exists_v0(client: TestClient) -> None:
    body = _html(client)
    assert "Futures Read-only Market Dashboard v0" in body
    assert 'data-f5-market-dashboard-v0="true"' in body


def test_f5_market_dashboard_readonly_markers_v0(client: TestClient) -> None:
    body = _html(client)
    for marker in (
        'data-f5-market-dashboard-ssr-only="true"',
        'data-f5-market-dashboard-readonly="true"',
        'data-f5-market-dashboard-no-fetch="true"',
        'data-f5-market-dashboard-no-live="true"',
        'data-f5-market-dashboard-no-orders="true"',
        'data-f5-market-dashboard-no-authority="true"',
        'data-f5-market-dashboard-non-authorizing="true"',
    ):
        assert marker in body


def test_f5_market_dashboard_no_form_no_fetch_v0(client: TestClient) -> None:
    body = _html(client)
    lower = body.lower()
    assert "<form" not in lower
    assert 'method="post"' not in lower
    assert "<button" not in lower
    assert 'type="submit"' not in lower
    assert "fetch(" not in body
    assert "xmlhttprequest" not in lower
    assert "setinterval" not in lower


def test_f5_market_dashboard_mandatory_no_live_banner_v0(client: TestClient) -> None:
    body = _html(client)
    assert F5_BANNER in body
    assert 'data-f5-no-live-banner="true"' in body
    assert "Display is not enforcement" in body


def test_f5_market_dashboard_f1_metadata_section_missing_state_v0(client: TestClient) -> None:
    body = _html(client)
    assert 'data-f5-instrument-metadata-section="true"' in body
    assert 'data-f5-f1-status="futures_metadata_missing"' in body
    assert 'data-f5-f1-display-status="missing"' in body


def test_f5_market_dashboard_f2_provenance_section_missing_state_v0(client: TestClient) -> None:
    body = _html(client)
    assert 'data-f5-provenance-section="true"' in body
    assert 'data-f5-f2-status="provenance_missing"' in body


def test_f5_market_dashboard_f3_backtest_realism_incomplete_v0(client: TestClient) -> None:
    body = _html(client)
    assert 'data-f5-backtest-realism-section="true"' in body
    assert 'data-f5-f3-status="backtest_realism_incomplete"' in body


def test_f5_market_dashboard_f4_risk_safety_incomplete_v0(client: TestClient) -> None:
    body = _html(client)
    assert 'data-f5-risk-safety-section="true"' in body
    assert 'data-f5-f4-status="risk_safety_incomplete"' in body


def test_f5_market_dashboard_kraken_futures_testnet_metadata_label_only_v0(
    client_f5_fixture_on: TestClient,
) -> None:
    body = _html(client_f5_fixture_on)
    assert 'data-f5-kraken-futures-testnet-label="true"' in body
    assert KRAKEN_LABEL_WARNING in body
    assert 'data-f5-env-name="kraken_futures_testnet"' in body
    assert "not execution authority" in body.lower()


def test_f5_market_dashboard_fixture_partial_f1_and_missing_f2_f4_v0(
    client_f5_fixture_on: TestClient,
) -> None:
    body = _html(client_f5_fixture_on)
    assert 'data-f5-f1-status="futures_metadata_partial"' in body
    assert 'data-f5-f2-status="provenance_missing"' in body
    assert 'data-f5-f3-status="backtest_realism_incomplete"' in body
    assert 'data-f5-f4-status="risk_safety_incomplete"' in body
    assert 'data-f5-f1-field="instrument_id"' in body
    assert ">PF_XBTUSD<" in body


def test_f5_market_dashboard_no_live_authorization_styling_v0(client: TestClient) -> None:
    body = _html(client)
    lower = body.lower()
    forbidden = ("live-ready", "live ready", "production-ready", "live_authorization")
    for phrase in forbidden:
        assert phrase not in lower
    assert 'data-f5-market-dashboard-no-live="true"' in body


def test_f5_market_dashboard_status_model_twelve_values_v0(client: TestClient) -> None:
    body = _html(client)
    assert 'data-f5-status-model="true"' in body
    for status in STATUS_MODEL_VALUES:
        assert f'data-f5-status-value="{status}"' in body


def test_f5_market_dashboard_truth_boundary_markers_v0(client: TestClient) -> None:
    body = _html(client)
    for marker in (
        'data-f5-provider-truth-blocked="true"',
        'data-f5-dashboard-truth-blocked="true"',
        'data-f5-trading-readiness-blocked="true"',
        'data-f5-selected-future-truth-blocked="true"',
        'data-f5-execution-readiness-blocked="true"',
    ):
        assert marker in body


def test_f5_market_dashboard_orthogonal_to_market_surface_v0(client: TestClient) -> None:
    f5_body = _html(client)
    market = client.get("/market")
    assert market.status_code == 200
    market_body = market.text
    assert 'data-f5-market-dashboard-v0="true"' in f5_body
    assert 'data-f5-market-dashboard-v0="true"' not in market_body
    assert 'data-market-surface-v0="true"' in market_body
    assert 'data-market-surface-v0="true"' not in f5_body


def test_f5_market_dashboard_double_play_route_untouched_v0(client: TestClient) -> None:
    dp = client.get("/market/double-play")
    assert dp.status_code == 200
    body = dp.text
    assert 'data-double-play-market-dashboard-v0="true"' in body
    assert 'data-f5-market-dashboard-v0="true"' not in body


def test_f5_market_dashboard_display_context_fail_closed_default_v0(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)
    ctx = build_futures_read_only_market_dashboard_display_context()
    assert ctx["gate_enabled"] is False
    assert ctx["display_status"] == "disabled"
    assert ctx["f1"]["status"] == "futures_metadata_missing"
    assert ctx["f2"]["status"] == "provenance_missing"
    assert ctx["authority"]["provider_truth"] is False
    assert ctx["authority"]["execution_readiness"] is False


def test_f5_market_dashboard_runtime_module_no_exchange_import_v0() -> None:
    runtime_path = (
        project_root / "src" / "webui" / "futures_read_only_market_dashboard_runtime_v0.py"
    )
    text = runtime_path.read_text(encoding="utf-8")
    lowered = text.lower()
    for forbidden_import in (
        "import requests",
        "import httpx",
        "import aiohttp",
        "from src.execution",
        "from src.broker",
        "from src.exchange",
    ):
        assert forbidden_import not in lowered
    assert "build_market_payload" not in text


def test_f5_market_dashboard_no_chartjs_dependency_v0(client: TestClient) -> None:
    body = _html(client)
    lower = body.lower()
    assert "chart.js" not in lower
    assert "chartjs" not in lower
    assert 'data-chartjs-cdn-monitored-v0="true"' not in body
