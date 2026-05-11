"""Market Dashboard read-only structure contract v0.

This module is intentionally UI/HTML-structure only. It must not authorize
runtime, scheduler, paper/testnet/live, broker, exchange, or order flows.
"""

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

FORM_ACTION_RE = re.compile(
    r"<form\b[^>]*\baction\s*=\s*[\"']([^\"']*)[\"']",
    re.IGNORECASE,
)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    with TestClient(create_app()) as test_client:
        yield test_client


def _html(client: TestClient, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200
    ctype = response.headers.get("content-type", "")
    assert "text/html" in ctype
    return response.text


def test_market_dashboard_keeps_depth_ssr_without_client_depth_fetch(
    client: TestClient,
) -> None:
    html = _html(client, "/market")

    assert 'data-market-depth-panel="true"' in html
    assert "data-market-depth-status=" in html
    assert 'data-market-depth-summary="true"' in html

    assert "/api/market/depth" not in html
    assert "fetch(" not in html
    assert "XMLHttpRequest" not in html


def test_double_play_market_dashboard_does_not_embed_market_depth_api_fetch(
    client: TestClient,
) -> None:
    html = _html(client, "/market/double-play")

    assert "/api/market/depth" not in html
    assert "fetch(" not in html
    assert "XMLHttpRequest" not in html


def test_market_dashboard_has_no_trade_action_affordance(client: TestClient) -> None:
    combined_html = "\n".join(
        [
            _html(client, "/market"),
            _html(client, "/market/double-play"),
        ]
    ).lower()

    forbidden_action_terms = [
        "place order",
        "submit order",
        "send order",
        "buy now",
        "sell now",
        "go long",
        "go short",
        "execute trade",
        "live authorize",
        "authorize live",
        "broker submit",
        "exchange submit",
    ]

    for term in forbidden_action_terms:
        assert term not in combined_html


def test_market_dashboard_readonly_banner_markers(client: TestClient) -> None:
    market_html = _html(client, "/market")
    assert 'data-market-readonly="true"' in market_html
    assert 'data-market-non-authorizing="true"' in market_html


def test_market_dashboard_forms_do_not_target_order_or_live_paths(
    client: TestClient,
) -> None:
    combined_html = "\n".join(
        [
            _html(client, "/market"),
            _html(client, "/market/double-play"),
        ]
    )

    form_actions = [m for m in FORM_ACTION_RE.findall(combined_html) if m.strip()]

    forbidden_fragments = [
        "order",
        "broker",
        "exchange",
        "live",
        "testnet",
        "kill",
        "scheduler",
        "runtime",
    ]

    for action in form_actions:
        lowered = action.lower()
        for fragment in forbidden_fragments:
            assert fragment not in lowered
