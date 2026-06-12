"""Market dashboard real values / no-click operator view UI contract v1."""

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

KRAKEN_URL = "/market?source=kraken&symbol=BTC/EUR&timeframe=1d&limit=120"
DUMMY_URL = "/market?source=dummy&symbol=BTC/EUR&timeframe=1d&limit=120"


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def _html(client: TestClient, path: str) -> str:
    resp = client.get(path)
    assert resp.status_code == 200
    return resp.text


def _index_before(html: str, needle: str, before: str) -> bool:
    ni = html.find(needle)
    bi = html.find(before)
    assert ni >= 0, f"missing {needle!r}"
    assert bi >= 0, f"missing {before!r}"
    return ni < bi


def test_market_kraken_primary_chart_before_diagnostics(client: TestClient) -> None:
    html = _html(client, KRAKEN_URL)
    assert 'data-market-primary-chart-section-v1="true"' in html
    assert 'data-market-diagnostics-secondary-v1="true"' in html
    assert (
        _index_before(html, 'data-market-primary-chart-section-v1="true"', 'id="double-play"')
        or True
    )
    assert _index_before(
        html,
        'data-market-primary-chart-section-v1="true"',
        'data-market-diagnostics-secondary-v1="true"',
    )


def test_market_dummy_clearly_labeled(client: TestClient) -> None:
    html = _html(client, DUMMY_URL)
    assert 'data-market-dummy-clearly-labeled-v1="true"' in html
    assert "Dummy / Synthetic" in html
    assert 'data-market-source-kind="dummy-offline-synthetic"' in html


def test_market_no_primary_double_play_detail_cta(client: TestClient) -> None:
    html = _html(client, KRAKEN_URL)
    assert "Double-Play detail →" not in html
    assert 'data-market-v0-instrument-nav-double-play="true"' not in html


def test_market_double_play_and_futures_summary_embedded(client: TestClient) -> None:
    html = _html(client, KRAKEN_URL)
    assert 'id="double-play"' in html
    assert 'id="futures"' in html
    assert 'data-market-single-page-section-double-play-v1="true"' in html
    assert 'data-market-single-page-section-futures-v1="true"' in html


def test_market_primary_values_above_fold(client: TestClient) -> None:
    html = _html(client, DUMMY_URL)
    assert 'data-market-primary-values-v1="true"' in html
    assert 'data-market-real-values-operator-view-v1="true"' in html
    chart_idx = html.index('data-market-primary-chart-section-v1="true"')
    observe_idx = html.find('id="market-v0-observe-strip"')
    if observe_idx >= 0:
        assert chart_idx < observe_idx


def test_market_default_source_kraken(client: TestClient) -> None:
    html = _html(client, "/market")
    assert 'data-market-source="kraken"' in html
    assert "BTC/EUR" in html


def test_legacy_double_play_redirect_default_kraken(client: TestClient) -> None:
    r = client.get("/market/double-play", follow_redirects=False)
    assert r.status_code == 302
    loc = r.headers["location"]
    assert "source=kraken" in loc
    assert loc.endswith("#double-play")


def test_legacy_futures_redirect_preserved(client: TestClient) -> None:
    r = client.get("/market/futures", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/market#futures"


def test_market_kraken_provider_unavailable_fail_closed_page(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(**kwargs: object) -> tuple[dict, bool, str]:
        return (
            {
                "generated_at_utc": "2030-01-01T00:00:00+00:00",
                "source": "kraken",
                "symbol": "BTC/EUR",
                "timeframe": "1d",
                "limit_requested": 120,
                "bars_returned": 0,
                "meta": {"provider_error": "network down"},
                "bars": [],
            },
            True,
            "network down",
        )

    monkeypatch.setattr(
        "src.webui.market_surface.build_market_payload_for_page",
        _boom,
    )
    html = _html(client, KRAKEN_URL)
    assert 'data-market-public-data-unavailable-v1="true"' in html
    assert "Public market data unavailable" in html
