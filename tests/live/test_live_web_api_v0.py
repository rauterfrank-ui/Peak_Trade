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
                "step,ts_event,equity,cash,realized_pnl,unrealized_pnl,signal,signal_changed,orders_generated,orders_filled,orders_rejected,orders_blocked,risk_allowed,risk_reasons,position_size",
                "0,2026-01-15T18:00:00+00:00,1000.0,1000.0,0.0,0.0,0,False,0,0,0,0,True,,0.0",
                "1,2026-01-15T18:01:00+00:00,1005.0,995.0,1.0,0.0,1,True,1,1,0,0,True,,0.1",
                "2,2026-01-15T18:02:00+00:00,1002.0,995.0,1.0,-3.0,1,False,1,0,0,1,False,limit,0.1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return run_dir


def test_api_v0_health_ok(client: TestClient) -> None:
    r = client.get("/api/v0/health")
    assert r.status_code == 200
    payload = r.json()
    assert payload["status"] == "ok"
    assert "contract_version" in payload
    assert "server_time" in payload


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


def test_api_v0_signals_positions_orders(tmp_path: Path) -> None:
    run_id = "20260115_shadow_demo_BTC-EUR_1m"
    _write_run(tmp_path, run_id=run_id)

    app = create_app(base_runs_dir=str(tmp_path))
    client = TestClient(app)

    signals = client.get(f"/api/v0/runs/{run_id}/signals?limit=50")
    assert signals.status_code == 200
    sp = signals.json()
    assert sp["run_id"] == run_id
    assert "asof" in sp
    assert sp["count"] == len(sp["items"])
    assert len(sp["items"]) == 3
    assert sp["items"][0]["ts"].startswith("2026-01-15T18:00:00")
    assert sp["items"][1]["signal"] == 1

    positions = client.get(f"/api/v0/runs/{run_id}/positions?limit=50")
    assert positions.status_code == 200
    pp = positions.json()
    assert pp["run_id"] == run_id
    assert pp["count"] == len(pp["items"])
    assert len(pp["items"]) == 3
    assert pp["items"][1]["position_size"] == 0.1

    orders = client.get(f"/api/v0/runs/{run_id}/orders?limit=200&only_nonzero=true")
    assert orders.status_code == 200
    op = orders.json()
    assert op["run_id"] == run_id
    assert op["count"] == len(op["items"])
    # only_nonzero=true filters out the first row (all zeros)
    assert len(op["items"]) == 2


def test_api_v0_runs_v02_and_detail_v02(tmp_path: Path) -> None:
    run_id = "20260115_shadow_demo_BTC-EUR_1m"
    _write_run(tmp_path, run_id=run_id)

    app = create_app(base_runs_dir=str(tmp_path))
    client = TestClient(app)

    r = client.get("/api/v0/runs_v02?limit=10")
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    assert rows[0]["run_id"] == run_id
    assert "status" in rows[0]
    assert "last_heartbeat" in rows[0]

    d = client.get(f"/api/v0/runs/{run_id}/detail_v02")
    assert d.status_code == 200
    payload = d.json()
    assert payload["summary"]["run_id"] == run_id
    assert "pointers" in payload
    assert payload["pointers"]["events"].endswith(f"/api/v0/runs/{run_id}/events")


def test_api_v0_events_poll_and_sse(tmp_path: Path) -> None:
    run_id = "20260115_shadow_demo_BTC-EUR_1m"
    _write_run(tmp_path, run_id=run_id)

    app = create_app(base_runs_dir=str(tmp_path))
    client = TestClient(app)

    poll = client.get(f"/api/v0/runs/{run_id}/events?since_seq=0&limit=2")
    assert poll.status_code == 200
    p = poll.json()
    assert p["run_id"] == run_id
    assert p["count"] == len(p["items"])
    assert p["next_seq"] >= 2
    assert p["items"][0]["seq"] == 0

    # SSE (bounded, initial batch only; no sleeps)
    with client.stream(
        "GET",
        f"/api/v0/runs/{run_id}/events?sse=1&since_seq=0&limit=1",
        headers={"accept": "text/event-stream"},
    ) as resp:
        assert resp.status_code == 200
        text = "".join(list(resp.iter_text()))
        assert "event: pt_event" in text
        assert '"run_id"' in text


def test_api_paths_reject_mutating_methods(tmp_path: Path) -> None:
    app = create_app(base_runs_dir=str(tmp_path))
    client = TestClient(app)

    r = client.post("/api/v0/health")
    assert r.status_code == 405
