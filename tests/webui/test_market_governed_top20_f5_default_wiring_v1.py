"""Contract tests: governed Top-20 + F5 default wiring on futures-first GET /market."""

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
from src.webui.futures_read_only_market_dashboard_runtime_v0 import (
    ENV_BUNDLE_ROOT as F5_ENV_BUNDLE_ROOT,
    ENV_ENABLED as F5_ENV_ENABLED,
)
from src.webui.market_ranking_funnel_runtime_v0 import (
    ENV_BUNDLE_ROOT as RANKING_ENV_BUNDLE_ROOT,
    ENV_ENABLED as RANKING_ENV_ENABLED,
)
from src.webui.market_surface import (
    FORBIDDEN_IMPLICIT_SPOT_DEFAULT_SYMBOL,
    build_market_governed_top20_display_context,
    build_market_ranking_funnel_display_context,
    build_market_v0_page_template_context,
    resolve_market_page_data,
)
from src.webui.futures_read_only_market_dashboard_runtime_v0 import (
    build_futures_read_only_market_dashboard_display_context,
)

RANKING_FIXTURE = (
    project_root / "tests" / "fixtures" / "market_ranking_funnel_readmodel_v0" / "complete_minimal"
).resolve()
F5_FIXTURE = (
    project_root
    / "tests"
    / "fixtures"
    / "futures_read_only_market_dashboard_v0"
    / "complete_minimal"
).resolve()
MARKET_SURFACE_PATH = project_root / "src" / "webui" / "market_surface.py"
PIPELINE_CALL_RE = re.compile(
    r"build_u2c_governed_snapshot|persist_governed_snapshot|run_ops_pipeline|subprocess",
)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.delenv(RANKING_ENV_ENABLED, raising=False)
    monkeypatch.delenv(RANKING_ENV_BUNDLE_ROOT, raising=False)
    monkeypatch.delenv(F5_ENV_ENABLED, raising=False)
    monkeypatch.delenv(F5_ENV_BUNDLE_ROOT, raising=False)
    kraken_mock = MagicMock(
        side_effect=AssertionError("fetch_ohlcv_df must not run on default /market")
    )
    monkeypatch.setattr("src.data.kraken.fetch_ohlcv_df", kraken_mock)
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture()
def client_governed_wiring_on(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
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
    assert "text/html" in resp.headers.get("content-type", "")
    return resp.text


def test_static_guard_no_pipeline_calls_in_market_surface() -> None:
    text = MARKET_SURFACE_PATH.read_text(encoding="utf-8")
    assert PIPELINE_CALL_RE.search(text) is None


def test_market_default_futures_first_no_spot_fallback(client: TestClient) -> None:
    body = _html(client)
    assert 'data-market-futures-first-v1="true"' in body
    assert 'data-market-source="futures"' in body
    assert FORBIDDEN_IMPLICIT_SPOT_DEFAULT_SYMBOL not in body
    assert 'data-market-dummy-explicit-synthetic-v1="true"' not in body


def test_market_missing_snapshot_shows_futures_data_unavailable(client: TestClient) -> None:
    body = _html(client)
    assert 'data-market-futures-data-unavailable-v1="true"' in body
    assert "Futures data unavailable" in body
    assert 'data-market-governed-top20-unavailable-v1="true"' in body
    assert 'data-market-governed-top20-missing-state-v1="true"' in body


def test_governed_top20_primary_visible_when_fixture_on(
    client_governed_wiring_on: TestClient,
) -> None:
    body = _html(client_governed_wiring_on)
    assert 'data-market-governed-top20-primary-v1="true"' in body
    assert 'data-market-governed-top20-available-v1="true"' in body
    assert 'data-market-governed-top20-table-v1="true"' in body
    assert "ETHUSDT" in body
    assert 'data-market-governed-top20-row-v1="true"' in body
    assert FORBIDDEN_IMPLICIT_SPOT_DEFAULT_SYMBOL not in body


def test_governed_top20_preserves_order_and_count_not_padded(
    client_governed_wiring_on: TestClient,
) -> None:
    body = _html(client_governed_wiring_on)
    assert 'data-market-governed-top20-row-count="8"' in body
    assert "no padding to 20" in body


def test_governed_top20_data_source_and_freshness_visible(
    client_governed_wiring_on: TestClient,
) -> None:
    body = _html(client_governed_wiring_on)
    assert "fixture:complete_minimal" in body
    assert "2026-05-27T00:00:00Z" in body


def test_f5_metadata_wired_in_compact_panel(client_governed_wiring_on: TestClient) -> None:
    body = _html(client_governed_wiring_on)
    assert 'data-f5-market-dashboard-gate-enabled="true"' in body
    assert 'data-f5-overall-status="futures_metadata_partial"' in body
    assert "futures_metadata_partial" in body


def test_f5_missing_state_when_gate_off(client: TestClient) -> None:
    body = _html(client)
    assert 'data-f5-market-dashboard-missing-state-v1="true"' in body
    assert "F5 metadata unavailable" in body


def test_f5_malformed_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bundle = tmp_path / "bad_f5"
    bundle.mkdir()
    (bundle / "dashboard.json").write_text("{not-json", encoding="utf-8")
    monkeypatch.setenv(F5_ENV_ENABLED, "1")
    monkeypatch.setenv(F5_ENV_BUNDLE_ROOT, str(bundle))
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    with TestClient(create_app()) as test_client:
        body = _html(test_client)
    assert 'data-f5-market-dashboard-malformed-state-v1="true"' in body
    assert "invalid/malformed" in body.lower()


def test_ranking_malformed_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bundle = tmp_path / "bad_ranking"
    bundle.mkdir()
    (bundle / "ranking_funnel.json").write_text("{bad", encoding="utf-8")
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(bundle))
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    with TestClient(create_app()) as test_client:
        body = _html(test_client)
    assert 'data-market-governed-top20-malformed-v1="true"' in body
    assert "invalid/malformed" in body.lower()


def test_ranking_stale_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bundle = tmp_path / "stale_ranking"
    bundle.mkdir()
    payload = json.loads((RANKING_FIXTURE / "ranking_funnel.json").read_text(encoding="utf-8"))
    payload["stale"] = True
    payload["stale_reason"] = "fixture_stale"
    (bundle / "ranking_funnel.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(bundle))
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    with TestClient(create_app()) as test_client:
        body = _html(test_client)
    assert 'data-market-governed-top20-stale-v1="true"' in body
    assert "fixture_stale" in body
    assert 'data-market-governed-top20-available-v1="true"' in body


def test_build_market_governed_top20_display_context_unit() -> None:
    ranking = build_market_ranking_funnel_display_context()
    f5 = build_futures_read_only_market_dashboard_display_context()
    ctx = build_market_governed_top20_display_context(ranking_funnel=ranking, f5_dashboard=f5)
    assert ctx["snapshot_available"] is False
    assert ctx["row_count"] == 0
    assert ctx["unavailable_message"] == "Futures data unavailable"


def test_resolve_market_page_data_no_network_no_pipeline(client: TestClient) -> None:
    sym, src, payload, unavailable = resolve_market_page_data(
        symbol=None, timeframe="1d", limit=120, source=None
    )
    assert src == "futures"
    assert unavailable is True
    assert payload["bars"] == []


def test_diagnostics_remain_collapsed(client_governed_wiring_on: TestClient) -> None:
    body = _html(client_governed_wiring_on)
    assert 'data-market-remodel-diagnostics-collapsed-default-v2="true"' in body
    assert "<details" in body and "Diagnostics / internals" in body


def test_governed_top20_context_determinism_three_runs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    monkeypatch.setenv(F5_ENV_ENABLED, "1")
    monkeypatch.setenv(F5_ENV_BUNDLE_ROOT, str(F5_FIXTURE))

    def _snapshot() -> dict[str, object]:
        ranking = build_market_ranking_funnel_display_context()
        f5 = build_futures_read_only_market_dashboard_display_context()
        ctx = build_market_governed_top20_display_context(ranking_funnel=ranking, f5_dashboard=f5)
        return {
            "row_count": ctx["row_count"],
            "rows": ctx["rows"],
            "snapshot_status": ctx["snapshot_status"],
            "f5_overall_status": ctx["f5_overall_status"],
        }

    first = _snapshot()
    second = _snapshot()
    third = _snapshot()
    assert first == second == third


def test_template_context_includes_governed_top20(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    sym, src, payload, unavailable = resolve_market_page_data(
        symbol=None, timeframe="1d", limit=120, source="futures"
    )
    ctx = build_market_v0_page_template_context(
        get_project_status=lambda: {"ok": True},
        symbol=sym,
        timeframe="1d",
        limit=120,
        source=src,
        payload=payload,
        data_unavailable=unavailable,
    )
    assert "governed_top20" in ctx
    assert ctx["governed_top20"]["snapshot_available"] is True
    assert ctx["governed_top20"]["row_count"] == 8
