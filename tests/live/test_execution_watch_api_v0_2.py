from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _copy_fixture(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())


def test_execution_watch_api_v0_2_healthz(client: TestClient) -> None:
    r = client.get("/api/healthz")
    assert r.status_code == 200
    payload = r.json()
    assert payload["api_version"] == "v0.2"
    assert payload["status"] == "ok"
    assert payload["watch_only"] is True
    assert "generated_at_utc" in payload


def test_execution_watch_api_v0_2_runs_detail_events_pagination(
    client: TestClient, tmp_path: Path
) -> None:
    # Arrange: JSONL fixture
    fx = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "execution_watch_v0_2"
        / "execution_pipeline_events_v0.jsonl"
    )
    p = tmp_path / "execution_pipeline_events_v0.jsonl"
    _copy_fixture(fx, p)

    root = tmp_path.as_posix()

    # Runs: newest first (run_new has latest events at ts=00:00:03)
    runs = client.get(f"/api/execution/runs?root={root}&filename={p.name}&limit=10")
    assert runs.status_code == 200
    rp = runs.json()
    assert rp["api_version"] == "v0.2"
    assert rp["count"] == 2
    assert [r["run_id"] for r in rp["runs"]] == ["run_new", "run_old"]

    # Detail
    detail = client.get(f"/api/execution/runs/run_new?root={root}&filename={p.name}")
    assert detail.status_code == 200
    dp = detail.json()
    assert dp["api_version"] == "v0.2"
    assert dp["run"]["run_id"] == "run_new"
    assert dp["run"]["status"] == "success"
    assert dp["run"]["total_events"] == 3

    # Events pagination stable
    page1 = client.get(f"/api/execution/runs/run_new/events?root={root}&filename={p.name}&limit=2")
    assert page1.status_code == 200
    p1 = page1.json()
    assert p1["api_version"] == "v0.2"
    assert p1["run_id"] == "run_new"
    assert p1["count"] == 2
    assert p1["items"][0]["seq"] == 0
    assert p1["items"][1]["seq"] == 1
    assert p1["has_more"] is True
    assert p1["next_cursor"] == "2"

    page2 = client.get(
        f"/api/execution/runs/run_new/events?root={root}&filename={p.name}&limit=2&cursor={p1['next_cursor']}"
    )
    assert page2.status_code == 200
    p2 = page2.json()
    assert p2["count"] == 1
    assert p2["items"][0]["seq"] == 2
    assert p2["has_more"] is False
    assert p2["next_cursor"] is None

    # 404 on unknown run_id
    miss = client.get(f"/api/execution/runs/nope?root={root}&filename={p.name}")
    assert miss.status_code == 404


def test_execution_watch_api_v0_2_live_sessions_from_registry_fixture(
    client: TestClient, tmp_path: Path
) -> None:
    fx_dir = (
        Path(__file__).resolve().parents[1] / "fixtures" / "execution_watch_v0_2" / "live_sessions"
    )
    base_dir = tmp_path / "live_sessions"
    base_dir.mkdir(parents=True, exist_ok=True)

    for src in sorted(fx_dir.glob("*.json")):
        _copy_fixture(src, base_dir / src.name)

    r = client.get(f"/api/live/sessions?limit=50&base_dir={base_dir.as_posix()}")
    assert r.status_code == 200
    payload = r.json()
    assert payload["api_version"] == "v0.2"
    assert payload["count"] == 2

    # Deterministic ordering: last_update_utc desc -> session_bbb (started, no ended_at) newer than session_aaa
    assert payload["sessions"][0]["session_id"] == "session_bbb"
    assert payload["sessions"][1]["session_id"] == "session_aaa"


def test_execution_watch_api_v0_2_empty_state_is_deterministic(
    client: TestClient, tmp_path: Path
) -> None:
    # Empty JSONL file -> runs list empty
    p = tmp_path / "execution_pipeline_events_v0.jsonl"
    p.write_text("", encoding="utf-8")
    root = tmp_path.as_posix()

    runs = client.get(f"/api/execution/runs?root={root}&filename={p.name}&limit=10")
    assert runs.status_code == 200
    payload = runs.json()
    assert payload["api_version"] == "v0.2"
    assert payload["count"] == 0
    assert payload["runs"] == []

    # No run exists -> 404
    detail = client.get(f"/api/execution/runs/run_missing?root={root}&filename={p.name}")
    assert detail.status_code == 404

    events = client.get(
        f"/api/execution/runs/run_missing/events?root={root}&filename={p.name}&limit=10"
    )
    assert events.status_code == 404

    # Empty registry dir -> sessions list empty
    base_dir = tmp_path / "live_sessions"
    base_dir.mkdir(parents=True, exist_ok=True)
    sessions = client.get(f"/api/live/sessions?limit=50&base_dir={base_dir.as_posix()}")
    assert sessions.status_code == 200
    sp = sessions.json()
    assert sp["api_version"] == "v0.2"
    assert sp["count"] == 0
    assert sp["sessions"] == []


def test_execution_watch_api_v0_2_events_invalid_cursor_400(
    client: TestClient, tmp_path: Path
) -> None:
    fx = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "execution_watch_v0_2"
        / "execution_pipeline_events_v0.jsonl"
    )
    p = tmp_path / "execution_pipeline_events_v0.jsonl"
    _copy_fixture(fx, p)
    root = tmp_path.as_posix()

    bad = client.get(
        f"/api/execution/runs/run_new/events?root={root}&filename={p.name}&limit=10&cursor=not_an_int"
    )
    assert bad.status_code == 400
