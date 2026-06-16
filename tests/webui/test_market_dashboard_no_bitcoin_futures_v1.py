"""No-Bitcoin contracts for canonical futures-first GET /market (read-only, fail-closed)."""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

from src.webui.app import create_app
from src.webui.market_futures_ohlcv_runtime_v0 import (
    ENV_BUNDLE_ROOT as OHLCV_ENV_BUNDLE_ROOT,
    ENV_ENABLED as OHLCV_ENV_ENABLED,
)
from src.webui.market_instrument_eligibility_v0 import (
    CANONICAL_EXCLUSION_OWNER,
    is_bitcoin_underlying,
    is_eligible_market_dashboard_instrument,
)
from src.webui.market_ranking_funnel_runtime_v0 import (
    ENV_BUNDLE_ROOT as RANKING_ENV_BUNDLE_ROOT,
    ENV_ENABLED as RANKING_ENV_ENABLED,
)
from src.webui.market_surface import (
    CANONICAL_INSTRUMENT_EXCLUSION_OWNER,
    build_market_governed_top20_display_context,
    build_market_v0_page_template_context,
    collect_governed_futures_symbols,
    is_valid_governed_futures_symbol,
    resolve_market_page_data,
    resolve_selected_futures_symbol_from_ranking_funnel,
)
from src.webui.futures_read_only_market_dashboard_runtime_v0 import (
    ENV_BUNDLE_ROOT as F5_ENV_BUNDLE_ROOT,
    ENV_ENABLED as F5_ENV_ENABLED,
    build_futures_read_only_market_dashboard_display_context,
)

RANKING_FIXTURE = (
    project_root / "tests" / "fixtures" / "market_ranking_funnel_readmodel_v0" / "complete_minimal"
).resolve()
RANKING_TOP50_FIXTURE = (
    project_root / "tests" / "fixtures" / "market_ranking_funnel_readmodel_v0" / "top50_minimal"
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

DASHBOARD_FIXTURE_PATHS = (
    RANKING_FIXTURE / "ranking_funnel.json",
    RANKING_TOP50_FIXTURE / "ranking_funnel.json",
    OHLCV_FIXTURE / "futures_ohlcv.json",
    F5_FIXTURE / "dashboard.json",
)

BITCOIN_ALIAS_RE = re.compile(
    r"\b(?:BTCUSDT|BTCUSD|BTC/EUR|BTCEUR|XBTUSD|XBTUSDT|XBT/USD|PF_XBTUSD|PI_XBTUSD|Bitcoin|bitcoin)\b",
    re.IGNORECASE,
)

MIXED_UNIVERSE_FIXTURE = {
    "stages": {
        "selected": [
            {"symbol": "BTCUSDT", "rank": 1, "display_score": 0.99},
            {"symbol": "ETHUSDT", "rank": 2, "display_score": 0.88},
            {"symbol": "SOLUSDT", "rank": 3, "display_score": 0.77},
            {"symbol": "XBTUSD", "rank": 4, "display_score": 0.66},
        ]
    },
    "gate_enabled": True,
    "display_status": "ready",
    "has_rows": True,
    "source": "fixture:mixed",
    "generated_at_iso": "2026-05-27T00:00:00Z",
    "stale": False,
}


@pytest.fixture()
def client_full_wiring_on(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    monkeypatch.setenv(OHLCV_ENV_ENABLED, "1")
    monkeypatch.setenv(OHLCV_ENV_BUNDLE_ROOT, str(OHLCV_FIXTURE))
    monkeypatch.setenv(F5_ENV_ENABLED, "1")
    monkeypatch.setenv(F5_ENV_BUNDLE_ROOT, str(F5_FIXTURE))
    kraken_mock = MagicMock(
        side_effect=AssertionError("fetch_ohlcv_df must not run on futures-first /market")
    )
    monkeypatch.setattr("src.data.kraken.fetch_ohlcv_df", kraken_mock)
    with TestClient(create_app()) as test_client:
        yield test_client


def _html(client: TestClient, path: str = "/market") -> str:
    resp = client.get(path)
    assert resp.status_code == 200
    return resp.text


def test_canonical_exclusion_owner_constant() -> None:
    assert CANONICAL_INSTRUMENT_EXCLUSION_OWNER == CANONICAL_EXCLUSION_OWNER


@pytest.mark.parametrize(
    "symbol,expected",
    [
        ("BTCUSDT", True),
        ("XBTUSD", True),
        ("PF_XBTUSD", True),
        ("PI_XBTUSD", True),
        ("BTC/EUR", True),
        ("ETHUSDT", False),
        ("SOLUSDT", False),
        ("PF_ETHUSD", False),
    ],
)
def test_bitcoin_underlying_detection(symbol: str, expected: bool) -> None:
    assert is_bitcoin_underlying(symbol) is expected
    assert is_eligible_market_dashboard_instrument(symbol) is (not expected)


def test_mixed_universe_preserves_non_bitcoin_order() -> None:
    symbols = sorted(collect_governed_futures_symbols(MIXED_UNIVERSE_FIXTURE))
    assert symbols == ["ETHUSDT", "SOLUSDT"]
    governed = build_market_governed_top20_display_context(
        ranking_funnel=MIXED_UNIVERSE_FIXTURE,
        f5_dashboard={"gate_enabled": False, "display_status": "disabled"},
        top_n=20,
    )
    assert [row["symbol"] for row in governed["rows"]] == ["ETHUSDT", "SOLUSDT"]
    assert governed["row_count"] == 2


def test_top50_fixture_excludes_bitcoin(client_full_wiring_on: TestClient) -> None:
    body = _html(client_full_wiring_on, "/market?top_n=50")
    assert "BTCUSDT" not in body
    assert "XBT" not in body
    assert "ETHUSDT" in body


def test_bitcoin_query_fail_closed(client_full_wiring_on: TestClient) -> None:
    body = _html(client_full_wiring_on, "/market?symbol=BTCUSDT")
    assert 'data-market-futures-selector-invalid-v1="true"' in body


def test_default_selection_is_non_bitcoin(client_full_wiring_on: TestClient) -> None:
    body = _html(client_full_wiring_on)
    assert "ETHUSDT" in body
    assert "BTCUSDT" not in body
    assert 'data-market-futures-selector-selected-v1="true"' in body


def test_f5_ohlcv_chart_exclude_bitcoin(client_full_wiring_on: TestClient) -> None:
    body = _html(client_full_wiring_on, "/market?symbol=ETHUSDT")
    assert "PF_ETHUSD" in body
    assert "PF_XBTUSD" not in body
    assert 'data-market-futures-ohlcv-wired-v1="true"' in body
    assert 'data-market-futures-chart-complete-v1="true"' in body
    assert "BTCUSDT" not in body


def test_dummy_explicit_bitcoin_rejected() -> None:
    with TestClient(create_app()) as client:
        body = _html(client, "/market?source=dummy&symbol=BTCUSDT")
    assert "BTCUSDT" not in body or "bitcoin_instrument_excluded" in body
    sym, _, payload, unavailable = resolve_market_page_data(
        symbol="BTCUSDT",
        timeframe="1d",
        limit=120,
        source="dummy",
    )
    assert sym == "BTCUSDT"
    assert unavailable is True
    assert payload["meta"]["reason"] == "bitcoin_instrument_excluded"


def test_market_response_contains_no_bitcoin_aliases(client_full_wiring_on: TestClient) -> None:
    body = _html(client_full_wiring_on)
    assert not BITCOIN_ALIAS_RE.search(body)


def test_preview_fixtures_contain_no_bitcoin_symbols() -> None:
    offenders: list[str] = []
    for path in DASHBOARD_FIXTURE_PATHS:
        text = path.read_text(encoding="utf-8")
        payload = json.loads(text)
        serialized = json.dumps(payload)
        if BITCOIN_ALIAS_RE.search(serialized):
            offenders.append(f"{path}: contains bitcoin alias")
        for symbol in _iter_fixture_symbols(payload):
            if is_bitcoin_underlying(symbol):
                offenders.append(f"{path}: symbol {symbol!r}")
    assert offenders == [], "\n".join(offenders)


def test_resolve_selected_skips_bitcoin_only_fixture() -> None:
    ranking = {
        "stages": {
            "selected": [{"symbol": "BTCUSDT", "rank": 1}],
            "shortlist": [{"symbol": "XBTUSD", "rank": 1}],
            "universe": [{"symbol": "ETHUSDT", "rank": 1}],
        }
    }
    assert resolve_selected_futures_symbol_from_ranking_funnel(ranking) == "ETHUSDT"


def _iter_fixture_symbols(payload: object) -> list[str]:
    symbols: list[str] = []
    if isinstance(payload, dict):
        if "symbol" in payload and isinstance(payload["symbol"], str):
            symbols.append(payload["symbol"])
        if "instrument_id" in payload and isinstance(payload["instrument_id"], str):
            symbols.append(payload["instrument_id"])
        if "series" in payload and isinstance(payload["series"], dict):
            symbols.extend(str(key) for key in payload["series"])
        for value in payload.values():
            symbols.extend(_iter_fixture_symbols(value))
    elif isinstance(payload, list):
        for item in payload:
            symbols.extend(_iter_fixture_symbols(item))
    return symbols


def test_is_valid_governed_futures_symbol_rejects_bitcoin() -> None:
    ranking = MIXED_UNIVERSE_FIXTURE
    assert is_valid_governed_futures_symbol("BTCUSDT", ranking) is False
    assert is_valid_governed_futures_symbol("ETHUSDT", ranking) is True


def test_template_context_hero_has_no_bitcoin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    sym, _, payload, unavailable = resolve_market_page_data(
        symbol=None,
        timeframe="1d",
        limit=120,
        source="futures",
    )
    ctx = build_market_v0_page_template_context(
        get_project_status=lambda: {},
        symbol=sym,
        timeframe="1d",
        limit=120,
        source="futures",
        payload=payload,
        data_unavailable=unavailable,
    )
    primary = ctx["primary_values"]
    assert primary.get("symbol") == "ETHUSDT"
    assert not BITCOIN_ALIAS_RE.search(str(primary))
