from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.live.web.app import create_app


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    app = create_app(base_runs_dir=str(tmp_path))
    return TestClient(app)


def _write_run(tmp_path: Path, run_id: str = "20260115_shadow_demo_BTC-EUR_1m") -> Path:
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)

    meta = {
        "run_id": run_id,
        "mode": "shadow",
        "strategy_name": "demo_strategy",
        "symbol": "BTC/EUR",
        "timeframe": "1m",
        "started_at": "2026-01-15T18:00:00+00:00",
        "ended_at": None,
        "config_snapshot": {"shadow_paper_logging": {"base_dir": "live_runs"}},
        "notes": "",
    }
    (run_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

    # Minimal events.csv so snapshot + equity endpoints can work.
    (run_dir / "events.csv").write_text(
        "\n".join(
            [
                "step,ts_event,equity,realized_pnl,unrealized_pnl,orders_generated,orders_filled,orders_blocked,risk_allowed,risk_reasons,position_size",
                "0,2026-01-15T18:00:00+00:00,1000.0,0.0,0.0,0,0,0,True,,0.0",
                "1,2026-01-15T18:01:00+00:00,1005.0,1.0,0.0,1,1,0,True,,0.1",
                "2,2026-01-15T18:02:00+00:00,1002.0,1.0,-3.0,1,0,1,False,limit,0.1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return run_dir


def test_api_v0_health_ok(client: TestClient) -> None:
    r = client.get("/api/v0/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_api_v0_runs_empty(client: TestClient) -> None:
    r = client.get("/api/v0/runs")
    assert r.status_code == 200
    assert r.json() == []


def test_api_v0_run_not_found(client: TestClient) -> None:
    r = client.get("/api/v0/runs/does-not-exist")
    assert r.status_code == 404


def test_api_v0_run_detail_and_metrics(tmp_path: Path) -> None:
    run_id = "20260115_shadow_demo_BTC-EUR_1m"
    _write_run(tmp_path, run_id=run_id)

    app = create_app(base_runs_dir=str(tmp_path))
    client = TestClient(app)

    detail = client.get(f"/api/v0/runs/{run_id}")
    assert detail.status_code == 200
    payload = detail.json()
    assert "meta" in payload
    assert "snapshot" in payload
    assert payload["meta"]["run_id"] == run_id
    assert payload["snapshot"]["run_id"] == run_id

    metrics = client.get(f"/api/v0/runs/{run_id}/metrics")
    assert metrics.status_code == 200
    mp = metrics.json()
    assert "equity" in mp
    assert "realized_pnl" in mp


def test_api_v0_equity_series(tmp_path: Path) -> None:
    run_id = "20260115_shadow_demo_BTC-EUR_1m"
    _write_run(tmp_path, run_id=run_id)

    app = create_app(base_runs_dir=str(tmp_path))
    client = TestClient(app)

    r = client.get(f"/api/v0/runs/{run_id}/equity?limit=2")
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    assert len(rows) == 2
    assert "ts" in rows[0]


def test_api_v0_trades_not_available(tmp_path: Path) -> None:
    run_id = "20260115_shadow_demo_BTC-EUR_1m"
    _write_run(tmp_path, run_id=run_id)

    app = create_app(base_runs_dir=str(tmp_path))
    client = TestClient(app)

    r = client.get(f"/api/v0/runs/{run_id}/trades")
    assert r.status_code == 404
