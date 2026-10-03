"""Real-time market observation cadence — read-only OKX refresh path."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.ops.okx_selected_instrument_ohlcv_readmodel_v1 import OkxOhlcvReadmodelError
from src.webui.app import app
from src.webui.market_surface_greenfield_v1.contracts_v1 import (
    MARKET_OBSERVATION_INTERVAL_SECONDS,
    POLL_INTERVAL_SECONDS,
    SYSTEM_INSTRUMENTS_CACHE_SECONDS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_JS = REPO_ROOT / "static/js/market_surface_greenfield_v1/surface_app_v1.js"


def test_observation_contract_constants() -> None:
    assert POLL_INTERVAL_SECONDS == 1
    assert MARKET_OBSERVATION_INTERVAL_SECONDS == 1
    assert SYSTEM_INSTRUMENTS_CACHE_SECONDS == 5


def test_state_api_exposes_observation_block() -> None:
    body = TestClient(app).get("/api/operator-trading-surface/v1/state").json()
    obs = body["observation"]
    assert obs["market_interval_seconds"] == 1
    assert obs["browser_poll_interval_seconds"] == 1
    assert obs["system_instruments_cache_seconds"] == 5


def test_surface_app_single_poller_and_incremental_chart_path() -> None:
    js = APP_JS.read_text(encoding="utf-8")
    assert js.count("fetch(") == 1
    assert "pollInFlight" in js
    assert "applyCandleSeries" in js
    assert "chartSeriesInitialized" in js
    assert "okx.com" not in js.lower()
    assert "WebSocket" not in js
    assert "interpolat" not in js.lower()
    assert "synthetic" not in js.lower()


def test_refresh_in_progress_maps_to_skipped_not_hard_fail() -> None:
    from unittest.mock import patch

    from src.webui.market_surface_greenfield_v1 import canonical_state_v1 as cs

    async def _run() -> str:
        with patch.object(
            cs,
            "refresh_selected_okx_ohlcv_readmodel_from_archive_v1",
            side_effect=OkxOhlcvReadmodelError("REFRESH_IN_PROGRESS"),
        ):
            body = await cs.build_canonical_surface_state_v1(force_refresh=False)
        return str(body["market"]["refresh_status"])

    import asyncio

    status = asyncio.run(_run())
    assert status == "SKIPPED_IN_PROGRESS"
