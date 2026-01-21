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
    assert payload["meta"]["api_version"] == "v0.3"
    assert payload["meta"]["read_errors"] == 0


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
    assert rp["meta"]["api_version"] == "v0.3"
    assert rp["meta"]["source"] == "fixture"
    assert rp["count"] == 2
    assert [r["run_id"] for r in rp["runs"]] == ["run_new", "run_old"]

    # Detail
    detail = client.get(f"/api/execution/runs/run_new?root={root}&filename={p.name}")
    assert detail.status_code == 200
    dp = detail.json()
    assert dp["api_version"] == "v0.2"
    assert dp["meta"]["api_version"] == "v0.3"
    assert dp["meta"]["source"] == "fixture"
    assert dp["run"]["run_id"] == "run_new"
    assert dp["run"]["status"] == "success"
    assert dp["run"]["total_events"] == 3

    # Events pagination stable
    page1 = client.get(f"/api/execution/runs/run_new/events?root={root}&filename={p.name}&limit=2")
    assert page1.status_code == 200
    p1 = page1.json()
    assert p1["api_version"] == "v0.2"
    assert p1["meta"]["api_version"] == "v0.3"
    assert p1["meta"]["source"] == "fixture"
    assert p1["run_id"] == "run_new"
    assert p1["count"] == 2
    assert p1["items"][0]["seq"] == 0
    assert p1["items"][1]["seq"] == 1
    assert p1["has_more"] is True
    assert p1["next_cursor"] == "2"
    assert p1["meta"]["has_more"] is True
    assert p1["meta"]["next_cursor"] == "2"
    assert p1["meta"]["read_errors"] == 0

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
    assert miss.json()["detail"] == "run_not_found"


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
    assert payload["meta"]["api_version"] == "v0.3"
    assert payload["meta"]["source"] == "fixture"
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
    assert payload["meta"]["read_errors"] == 0
    assert payload["meta"]["has_more"] is False
    assert payload["meta"]["next_cursor"] is None

    # No run exists -> 404
    detail = client.get(f"/api/execution/runs/run_missing?root={root}&filename={p.name}")
    assert detail.status_code == 404
    assert detail.json()["detail"] == "run_not_found"

    events = client.get(
        f"/api/execution/runs/run_missing/events?root={root}&filename={p.name}&limit=10"
    )
    assert events.status_code == 404
    assert events.json()["detail"] == "run_not_found"

    # Empty registry dir -> sessions list empty
    base_dir = tmp_path / "live_sessions"
    base_dir.mkdir(parents=True, exist_ok=True)
    sessions = client.get(f"/api/live/sessions?limit=50&base_dir={base_dir.as_posix()}")
    assert sessions.status_code == 200
    sp = sessions.json()
    assert sp["api_version"] == "v0.2"
    assert sp["count"] == 0
    assert sp["sessions"] == []
    assert sp["meta"]["read_errors"] == 0
    assert sp["meta"]["has_more"] is False
    assert sp["meta"]["next_cursor"] is None


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


def test_execution_watch_api_v0_3_malformed_jsonl_line_is_counted_and_skipped(
    client: TestClient, tmp_path: Path
) -> None:
    fx = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "execution_watch_v0_3"
        / "execution_pipeline_events_v0_malformed.jsonl"
    )
    p = tmp_path / "execution_pipeline_events_v0_malformed.jsonl"
    _copy_fixture(fx, p)
    root = tmp_path.as_posix()

    # Runs should be readable, with read_errors exposed
    runs = client.get(f"/api/execution/runs?root={root}&filename={p.name}&limit=10")
    assert runs.status_code == 200
    rp = runs.json()
    assert rp["meta"]["read_errors"] == 1

    # Events should skip the bad line, keep deterministic ordering, and expose read_errors
    ev = client.get(
        f"/api/execution/runs/run_badline/events?root={root}&filename={p.name}&limit=50"
    )
    assert ev.status_code == 200
    ep = ev.json()
    assert ep["meta"]["read_errors"] == 1
    assert [it["seq"] for it in ep["items"]] == [0, 1]
    assert [it["order_id"] for it in ep["items"]] == ["o1", "o2"]

    # Determinism: same input -> same output (ordering/cursor)
    ev2 = client.get(
        f"/api/execution/runs/run_badline/events?root={root}&filename={p.name}&limit=50"
    )
    assert ev2.status_code == 200
    ep2 = ev2.json()
    assert ep2["items"] == ep["items"]
    assert ep2["has_more"] == ep["has_more"]
    assert ep2["next_cursor"] == ep["next_cursor"]
    assert ep2["meta"]["read_errors"] == ep["meta"]["read_errors"]


def test_execution_watch_api_v0_3_since_cursor_tail_returns_only_new_events(
    client: TestClient, tmp_path: Path
) -> None:
    fx = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "execution_watch_v0_3"
        / "execution_pipeline_events_v0_tail.jsonl"
    )
    p = tmp_path / "execution_pipeline_events_v0_tail.jsonl"
    _copy_fixture(fx, p)
    root = tmp_path.as_posix()

    # Tail from seq=1 -> should return seq 2..4
    tail = client.get(
        f"/api/execution/runs/run_tail/events?root={root}&filename={p.name}&limit=10&since_cursor=1"
    )
    assert tail.status_code == 200
    tp = tail.json()
    assert [it["seq"] for it in tp["items"]] == [2, 3, 4]
    assert tp["meta"]["has_more"] is False
    assert tp["next_cursor"] == "4"
    assert tp["meta"]["next_cursor"] == "4"

    # Calling again with since_cursor=4 should yield no new events, cursor stable
    tail2 = client.get(
        f"/api/execution/runs/run_tail/events?root={root}&filename={p.name}&limit=10&since_cursor={tp['next_cursor']}"
    )
    assert tail2.status_code == 200
    tp2 = tail2.json()
    assert tp2["items"] == []
    assert tp2["has_more"] is False
    assert tp2["next_cursor"] == "4"
    assert tp2["meta"]["next_cursor"] == "4"
