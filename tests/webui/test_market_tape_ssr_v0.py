"""Web UI tests for env-gated market tape readmodel SSR v0 on GET /market."""

from __future__ import annotations

import re
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
from src.webui.market_surface import build_market_tape_display_context

FIXTURE_ROOT = project_root / "tests" / "fixtures" / "market_tape_readmodel_v0" / "complete_minimal"
MALFORMED_ROOT = (
    project_root / "tests" / "fixtures" / "market_tape_readmodel_v0" / "malformed_trades"
)

BOUNDARY_COPY = (
    "Read-only tape display. This panel does not authorize runtime, testnet, live trading, "
    "broker access, exchange access, or strategy execution. Tape rows are offline fixture "
    "evidence only — not order, fill, or position truth."
)

TAPE_MARKERS = (
    'data-market-v0-tape="true"',
    'data-market-v0-tape-readonly="true"',
    'data-market-v0-tape-authority="false"',
    'data-market-v0-tape-non-authorizing="true"',
    'data-market-v0-tape-evidence-only="true"',
    'data-market-v0-tape-provider-truth-blocked="true"',
    'data-market-v0-tape-dashboard-truth-blocked="true"',
    'data-market-v0-tape-trading-readiness-blocked="true"',
    'data-market-v0-tape-selected-future-truth-blocked="true"',
    'data-market-v0-tape-order-fill-position-truth-blocked="true"',
)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.delenv("PEAK_TRADE_MARKET_TAPE_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_MARKET_TAPE_BUNDLE_ROOT", raising=False)
    monkeypatch.delenv("PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_MARKET_RUN_PROJECTION_PAYLOAD_JSON", raising=False)
    with TestClient(create_app()) as test_client:
        yield test_client


def _html(client: TestClient, path: str = "/market") -> str:
    response = client.get(path)
    assert response.status_code == 200
    return response.text


def _tape_section(html: str) -> str:
    match = re.search(r'id="market-v0-tape-ssr"[\s\S]*?</section>', html)
    assert match, "tape SSR section missing"
    return match.group(0)


def test_gate_disabled_no_tape_section(client: TestClient) -> None:
    html = _html(client)
    for marker in TAPE_MARKERS:
        assert marker not in html
    assert BOUNDARY_COPY not in html
    assert "market-v0-tape-ssr" not in html


def test_gate_enabled_valid_fixture_shows_panel(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PEAK_TRADE_MARKET_TAPE_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_TAPE_BUNDLE_ROOT", str(FIXTURE_ROOT.resolve()))
    html = _html(client)

    for marker in TAPE_MARKERS:
        assert marker in html
    assert 'data-market-v0-tape-enabled="true"' in html
    assert 'data-market-v0-tape-ready="true"' in html
    assert 'data-market-v0-tape-readmodel-id="market_tape_readmodel.v0"' in html
    assert BOUNDARY_COPY in html
    assert "BTC/EUR" in html
    assert "Top trades (display subset)" in html
    assert "63020" in html
    assert str(FIXTURE_ROOT.resolve()) not in html
    lowered = _tape_section(html).lower()
    assert "trading_ready" not in lowered
    assert "live_ready" not in lowered
    assert "provider_ok" not in lowered


def test_gate_enabled_invalid_fixture_fail_closed(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PEAK_TRADE_MARKET_TAPE_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_TAPE_BUNDLE_ROOT", str(MALFORMED_ROOT.resolve()))
    html = _html(client)

    assert 'data-market-v0-tape="true"' in html
    assert 'data-market-v0-tape-ready="false"' in html
    assert 'data-market-v0-tape-readmodel-id="market_tape_readmodel.v0"' in html
    assert "Top trades (display subset)" not in html
    assert "63020.00" not in html


def test_gate_enabled_missing_bundle_root_fail_closed(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PEAK_TRADE_MARKET_TAPE_ENABLED", "1")
    monkeypatch.delenv("PEAK_TRADE_MARKET_TAPE_BUNDLE_ROOT", raising=False)
    html = _html(client)

    assert 'data-market-v0-tape-ready="false"' in html
    assert "Top trades (display subset)" not in html


def test_double_play_excludes_tape_markers(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PEAK_TRADE_MARKET_TAPE_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_TAPE_BUNDLE_ROOT", str(FIXTURE_ROOT.resolve()))
    response = client.get("/market/double-play", follow_redirects=False)
    assert response.status_code == 302
    assert "#double-play" in response.headers["location"]
    html = response.text
    for marker in TAPE_MARKERS:
        assert marker not in html
    assert BOUNDARY_COPY not in html
    assert "market-v0-tape-ssr" not in html


def test_build_context_unit_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PEAK_TRADE_MARKET_TAPE_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_TAPE_BUNDLE_ROOT", str(FIXTURE_ROOT.resolve()))
    ctx = build_market_tape_display_context()
    assert ctx["section_visible"] is True
    assert ctx["tape_ready"] is True
    assert ctx["readmodel_id"] == "market_tape_readmodel.v0"
    assert ctx["trade_count"] == 3


def test_build_context_gate_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PEAK_TRADE_MARKET_TAPE_ENABLED", raising=False)
    ctx = build_market_tape_display_context()
    assert ctx["section_visible"] is False
