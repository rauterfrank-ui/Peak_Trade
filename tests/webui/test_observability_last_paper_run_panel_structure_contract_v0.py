"""Structure contract: Last Paper Run panel on GET /observability (read-only)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

from src.webui.app import create_app

FIXTURE_BUNDLE = (
    project_root
    / "tests"
    / "fixtures"
    / "last_paper_run_panel_readmodel_v0"
    / "p1_complete_minimal"
).resolve()


@pytest.fixture()
def client_off() -> TestClient:
    return TestClient(create_app())


@pytest.fixture()
def client_on(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("PEAK_TRADE_LAST_PAPER_RUN_PANEL_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_LAST_PAPER_RUN_BUNDLE_ROOT", str(FIXTURE_BUNDLE))
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-06-08T00:00:02+00:00")
    return TestClient(create_app())


def test_panel_absent_when_gate_disabled(client_off: TestClient) -> None:
    html = client_off.get("/observability").text
    assert 'data-observability-last-paper-run-panel-v0="true"' not in html


def test_panel_present_when_gate_enabled(client_on: TestClient) -> None:
    html = client_on.get("/observability").text
    assert 'data-observability-last-paper-run-panel-v0="true"' in html
    assert 'data-observability-last-paper-run-readonly="true"' in html
    assert 'data-observability-last-paper-run-authority="false"' in html
    assert "Last Paper Run — View Only" in html
    assert "daemon_paper_24h_test_fixture_v0" in html
    assert "paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0" in html
    assert "NOT_PERSISTED" in html
    assert "instrument_truth_status: NOT_PERSISTED" in html


def test_btc_usd_not_paper_instrument_truth(client_on: TestClient) -> None:
    html = client_on.get("/observability").text
    assert "selected_symbol" not in html or "BTC/USD" not in html.split("Instrument")[1][:500]
    assert "Market Surface BTC/USD dummy is not Paper Run Truth" in html


def test_no_forms_or_post(client_on: TestClient) -> None:
    html = client_on.get("/observability").text
    panel_start = html.index('data-observability-last-paper-run-panel-v0="true"')
    panel_end = html.index('data-observability-paper-shadow-panel="true"')
    panel = html[panel_start:panel_end]
    assert "<form" not in panel.lower()
    assert 'method="POST"' not in panel
    assert "<button" not in panel.lower()
    assert "fetch(" not in panel


def test_safety_flags_false(client_on: TestClient) -> None:
    html = client_on.get("/observability").text
    assert "LIVE_AUTHORIZED" in html
    assert "READY_FOR_OPERATOR_ARMING" in html


def test_market_without_last_paper_primary_panel(client_off: TestClient) -> None:
    html = client_off.get("/market").text
    assert 'data-observability-last-paper-run-panel-v0="true"' not in html
    assert 'data-market-v0-paper-run-truth-separation-v0="true"' in html
