"""Market active Paper run panel on GET /market (env-gated, view-only)."""

from __future__ import annotations

import json
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


@pytest.fixture()
def client_default(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.delenv("PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_BRIDGE_ROOT", raising=False)
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture()
def bridge_root(tmp_path: Path) -> Path:
    root = tmp_path / "bridge_run"
    root.mkdir()
    (root / "meta.json").write_text(
        json.dumps(
            {
                "run_id": "paper_2h_sanity_first_bounded_20260608T192744Z",
                "mode": "paper",
                "strategy_name": "high_vol_no_trade",
                "symbol": "BTC",
                "timeframe": "1m",
                "started_at": "2026-06-08T19:27:44+00:00",
                "ended_at": None,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "evidence_pointer.json").write_text(
        json.dumps(
            {
                "view_only": True,
                "non_authorizing": True,
                "no_live": True,
                "evidence_pointer": True,
                "fake_data": False,
                "run_id": "paper_2h_sanity_first_bounded_20260608T192744Z",
                "mode": "paper",
                "runtime_out": str(tmp_path / "runtime_out"),
                "heartbeat_snapshot": {
                    "iteration": 53,
                    "ts_utc": "2026-06-08T19:57:13Z",
                    "reason": "idle_no_due_jobs",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    runtime_out = tmp_path / "runtime_out"
    runtime_out.mkdir()
    (runtime_out / "fills.json").write_text(
        '{"fills":[],"schema_version":"p7.fills.v0"}\n',
        encoding="utf-8",
    )
    (root / "events.csv").write_text(
        "step,ts_bar,ts_event,cash,equity,position_size\n"
        "53,2026-06-08T19:57:13Z,2026-06-08T19:57:13Z,1000.0,1000.0,0.0\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture()
def client_bridge_on(monkeypatch: pytest.MonkeyPatch, bridge_root: Path) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.setenv("PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_BRIDGE_ROOT", str(bridge_root))
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-06-08T19:58:00+00:00")
    with TestClient(create_app()) as test_client:
        yield test_client


def test_market_active_paper_run_panel_disabled_by_default(client_default: TestClient) -> None:
    response = client_default.get("/market")
    assert response.status_code == 200
    html = response.text
    assert 'data-market-v0-active-paper-run="true"' not in html


def test_market_active_paper_run_panel_renders_with_bridge(client_bridge_on: TestClient) -> None:
    html = client_bridge_on.get("/market").text
    assert 'data-market-v0-active-paper-run="true"' in html
    assert "Active Paper Run — View Only — Non Authorizing" in html
    assert "NOT LIVE" in html
    assert "NOT PREFLIGHT LIFT" in html
    assert "EVIDENCE ONLY" in html
    assert "paper_2h_sanity_first_bounded_20260608T192744Z" in html
    assert "display metadata, not Futures truth" in html
    assert "fetch(" not in html


def test_market_double_play_unchanged_without_active_panel(client_bridge_on: TestClient) -> None:
    response = client_bridge_on.get("/market/double-play")
    assert response.status_code == 200
    html = response.text
    assert 'data-market-v0-active-paper-run="true"' not in html
