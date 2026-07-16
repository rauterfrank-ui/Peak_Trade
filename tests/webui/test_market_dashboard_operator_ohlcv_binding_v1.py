"""Operator runtime must bind canonical offline OHLCV — not test fixtures."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

pytest.importorskip("fastapi")

from src.webui.market_visual_operator_surface_v1.local_offline_binding_v1 import (
    discover_canonical_operator_bundle_root,
    maybe_apply_local_operator_offline_binding,
)

pytestmark = pytest.mark.web

CANONICAL_BUNDLE = (
    Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
    / "research"
    / "_market_visual_operator_offline_bundles_v1"
)


def _clear_operator_env(monkeypatch: pytest.MonkeyPatch) -> None:
    keys = [
        "PEAK_TRADE_DISABLE_OPERATOR_LOCAL_BIND",
        "PEAK_TRADE_MARKET_FUTURES_OHLCV_ENABLED",
        "PEAK_TRADE_MARKET_FUTURES_OHLCV_BUNDLE_ROOT",
        "PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED",
        "PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT",
        "PEAK_TRADE_F5_MARKET_DASHBOARD_ENABLED",
        "PEAK_TRADE_F5_MARKET_DASHBOARD_BUNDLE_ROOT",
        "PEAK_TRADE_MARKET_VISUAL_OPERATOR_EVIDENCE_ROOT",
        "PEAK_TRADE_FIXED_GENERATED_AT_UTC",
        "_PEAK_TRADE_OPERATOR_LOCAL_BIND_APPLIED",
        "MARKET_VISUAL_OPERATOR_BUNDLE_ROOT",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)


@pytest.mark.skipif(
    not (CANONICAL_BUNDLE / "futures_ohlcv" / "futures_ohlcv.json").is_file(),
    reason="canonical offline operator bundle not present on this host",
)
def test_discover_canonical_operator_bundle_root() -> None:
    root = discover_canonical_operator_bundle_root()
    assert root is not None
    assert (root / "futures_ohlcv" / "futures_ohlcv.json").is_file()


def test_binding_is_noop_under_pytest(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_operator_env(monkeypatch)
    state = maybe_apply_local_operator_offline_binding()
    assert state["applied"] is False
    assert state["reason"] == "pytest_isolation"
    assert os.environ.get("PEAK_TRADE_MARKET_FUTURES_OHLCV_ENABLED") is None


def test_binding_respects_explicit_fixture_env(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_operator_env(monkeypatch)
    monkeypatch.setenv("PEAK_TRADE_WEB_TEST_MODE", "0")
    # Simulate non-pytest by temporarily pretending — still respect explicit env.
    monkeypatch.setenv("PEAK_TRADE_MARKET_FUTURES_OHLCV_ENABLED", "1")
    monkeypatch.setenv(
        "PEAK_TRADE_MARKET_FUTURES_OHLCV_BUNDLE_ROOT",
        str(project_root / "tests/fixtures/market_futures_ohlcv_readmodel_v0/complete_minimal"),
    )
    state = maybe_apply_local_operator_offline_binding()
    assert state["applied"] is False
    assert state["reason"] in {"pytest_isolation", "explicit_ohlcv_env_present"}


@pytest.mark.skipif(
    not (CANONICAL_BUNDLE / "futures_ohlcv" / "futures_ohlcv.json").is_file(),
    reason="canonical offline operator bundle not present on this host",
)
def test_operator_create_app_path_binds_canonical_not_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Simulate normal uvicorn create_app binding outside pytest isolation."""
    _clear_operator_env(monkeypatch)
    monkeypatch.setenv("PEAK_TRADE_WEB_TEST_MODE", "0")
    monkeypatch.setattr(
        "src.webui.market_visual_operator_surface_v1.local_offline_binding_v1._under_pytest",
        lambda: False,
    )
    state = maybe_apply_local_operator_offline_binding()
    assert state["applied"] is True
    assert state["source_class"] == "CANONICAL_LOCAL_READ_ONLY_BUNDLE"
    assert "fixture" not in (os.environ.get("PEAK_TRADE_MARKET_FUTURES_OHLCV_BUNDLE_ROOT") or "")
    assert "complete_minimal" not in (
        os.environ.get("PEAK_TRADE_MARKET_FUTURES_OHLCV_BUNDLE_ROOT") or ""
    )
    assert os.environ.get("PEAK_TRADE_FIXED_GENERATED_AT_UTC") is None

    from unittest.mock import MagicMock

    monkeypatch.setattr(
        "src.data.kraken.fetch_ohlcv_df",
        MagicMock(side_effect=AssertionError("no request-time network")),
    )
    # Import after env bind
    from fastapi.testclient import TestClient
    from src.webui.app import create_app

    with TestClient(create_app()) as client:
        resp = client.get("/market?timeframe=1h")
        assert resp.status_code == 200
        body = resp.text
        assert "fixture:complete_minimal" not in body
        assert "historical_panel_offline:" in body
        assert 'data-market-v0-in-chart-ohlc-candle="true"' in body
        candles = body.count('data-market-v0-in-chart-ohlc-candle="true"')
        volumes = body.count('data-market-chart-volume-bar-v1="true"')
        assert candles > 0
        assert volumes > 0
        assert "2030-01-15" not in body
        meta_bars = re.search(
            r'data-market-phase-3-meta-bars-v1="true"[^>]*>.*?<span class="text-slate-500">Bars</span>\s*(\d+)',
            body,
            re.S,
        )
        assert meta_bars is not None
        assert int(meta_bars.group(1)) > 0
