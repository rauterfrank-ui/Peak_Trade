from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _write_events(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, sort_keys=True) + "\n")


def test_execution_watch_api_v0_health(client: TestClient, tmp_path: Path) -> None:
    p = tmp_path / "execution_pipeline_events_v0.jsonl"
    _write_events(
        p,
        [
            {
                "schema": "execution_event_v0",
                "ts": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
                "run_id": "run_001",
                "correlation_id": "corr_001",
                "event_type": "created",
                "order_id": None,
                "idempotency_key": "idem_001",
                "payload": {"n_orders": 1},
            }
        ],
    )

    r = client.get(f"/api/v0/execution/health?root={tmp_path.as_posix()}&filename={p.name}")
    assert r.status_code == 200
    payload = r.json()
    assert payload["status"] == "ok"
    assert payload["watch_only"] is True
    assert payload["schema"] == "execution_event_v0"
    assert payload["exists"] is True


def test_execution_watch_api_v0_runs_and_detail(client: TestClient, tmp_path: Path) -> None:
    p = tmp_path / "execution_pipeline_events_v0.jsonl"
    ts0 = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat()
    ts1 = datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc).isoformat()
    _write_events(
        p,
        [
            {
                "schema": "execution_event_v0",
                "ts": ts0,
                "run_id": "run_ok",
                "correlation_id": "corr_ok",
                "event_type": "created",
                "order_id": None,
                "idempotency_key": "idem_ok",
                "payload": {"n_orders": 1},
            },
            {
                "schema": "execution_event_v0",
                "ts": ts1,
                "run_id": "run_ok",
                "correlation_id": "corr_ok",
                "event_type": "filled",
                "order_id": "ord_1",
                "idempotency_key": "idem_ok:ord_1",
                "payload": {"fill": {"quantity": 1}},
            },
            {
                "schema": "execution_event_v0",
                "ts": ts0,
                "run_id": "run_fail",
                "correlation_id": "corr_fail",
                "event_type": "failed",
                "order_id": "ord_x",
                "idempotency_key": "idem_fail:ord_x",
                "payload": {"final": True},
            },
        ],
    )

    runs = client.get(f"/api/v0/execution/runs?root={tmp_path.as_posix()}&filename={p.name}")
    assert runs.status_code == 200
    rp = runs.json()
    assert rp["count"] == 2
    by_id = {r["run_id"]: r for r in rp["runs"]}
    assert by_id["run_ok"]["status"] == "success"
    assert by_id["run_fail"]["status"] == "failed"

    detail = client.get(
        f"/api/v0/execution/runs/run_ok?root={tmp_path.as_posix()}&filename={p.name}"
    )
    assert detail.status_code == 200
    dp = detail.json()
    assert dp["run_id"] == "run_ok"
    assert dp["summary"]["status"] == "success"
    assert dp["count"] == len(dp["events"])


def test_execution_watch_html_page_renders(client: TestClient, tmp_path: Path) -> None:
    p = tmp_path / "execution_pipeline_events_v0.jsonl"
    _write_events(
        p,
        [
            {
                "schema": "execution_event_v0",
                "ts": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
                "run_id": "run_html",
                "correlation_id": "corr_html",
                "event_type": "created",
                "order_id": None,
                "idempotency_key": "idem_html",
                "payload": {"n_orders": 1},
            }
        ],
    )

    r = client.get(f"/watch/execution?root={tmp_path.as_posix()}&filename={p.name}")
    assert r.status_code == 200
    assert "WATCH-ONLY" in r.text
    assert "run_html" in r.text
