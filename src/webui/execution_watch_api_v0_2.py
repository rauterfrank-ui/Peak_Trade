"""
Execution Watch API v0.2 — read-only.

Mission goals:
- WATCH-ONLY / NO-LIVE: read-only endpoints, no broker connectivity, no actions.
- Deterministic: stable sorting, predictable pagination cursor.
- Testable: allow overriding JSONL root/filename + registry base_dir via query params.

Endpoints (v0.2):
- GET /api/healthz
- GET /api/execution/runs
- GET /api/execution/runs/{run_id}
- GET /api/execution/runs/{run_id}/events?limit=&cursor=
- GET /api/live/sessions
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

API_VERSION = "v0.2"

router = APIRouter(tags=["execution-watch-v0.2"])


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_int_cursor(cursor: Optional[str]) -> int:
    if cursor is None or cursor == "":
        return 0
    try:
        n = int(cursor)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_cursor")
    if n < 0:
        raise HTTPException(status_code=400, detail="invalid_cursor")
    return n


def _read_jsonl_events_v0(root: Path, filename: str) -> List[Dict[str, Any]]:
    """
    Read JSONL file and return raw event dicts for schema=execution_event_v0.

    We attach a deterministic file order key `_file_seq` (line index starting at 0)
    to guarantee stable ordering when timestamps tie.
    """
    p = root / filename
    if not p.exists():
        return []

    out: List[Dict[str, Any]] = []
    try:
        with p.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("schema") != "execution_event_v0":
                    continue
                obj["_file_seq"] = idx
                out.append(obj)
    except Exception:
        # Watch-only endpoint: fail soft (empty list) unless caller expects 404 for missing run.
        return []

    return out


def _event_sort_key(ev: Dict[str, Any]) -> Tuple[str, int, str, str, str]:
    """
    Stable deterministic ordering:
    - primary: ts
    - tie-breaker: file order (line index)
    - then: idempotency_key/event_type/order_id as last-resort for determinism
    """
    return (
        str(ev.get("ts") or ""),
        int(ev.get("_file_seq") or 0),
        str(ev.get("idempotency_key") or ""),
        str(ev.get("event_type") or ""),
        str(ev.get("order_id") or ""),
    )


def _group_events_by_run(events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for ev in events:
        rid = str(ev.get("run_id") or "")
        if not rid:
            continue
        grouped.setdefault(rid, []).append(ev)
    return grouped


def _status_from_counts(counts: Dict[str, int]) -> str:
    if counts.get("failed", 0) > 0:
        return "failed"
    if counts.get("canceled", 0) > 0:
        return "canceled"
    if counts.get("filled", 0) > 0:
        return "success"
    return "unknown"


class ApiEnvelope(BaseModel):
    api_version: str = Field(default=API_VERSION)
    generated_at_utc: str = Field(..., description="UTC ISO timestamp when payload was generated")


class HealthzResponse(ApiEnvelope):
    status: str = Field(default="ok")
    watch_only: bool = Field(default=True)


class RunSummary(BaseModel):
    api_version: str = Field(default=API_VERSION)

    run_id: str
    correlation_id: str = ""
    started_at_utc: Optional[str] = None
    last_event_at_utc: Optional[str] = None
    status: str = "unknown"
    counts: Dict[str, int] = Field(default_factory=dict)


class ExecutionEvent(BaseModel):
    api_version: str = Field(default=API_VERSION)

    # Monotonic per-run sequence number (stable cursor)
    seq: int
    ts: str
    event_type: str
    order_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class RunDetail(BaseModel):
    api_version: str = Field(default=API_VERSION)

    run_id: str
    correlation_id: str = ""
    started_at_utc: Optional[str] = None
    last_event_at_utc: Optional[str] = None
    status: str = "unknown"
    counts: Dict[str, int] = Field(default_factory=dict)
    total_events: int = 0


class RunsListResponse(ApiEnvelope):
    count: int
    runs: List[RunSummary]


class RunDetailResponse(ApiEnvelope):
    run: RunDetail


class RunEventsResponse(ApiEnvelope):
    run_id: str
    count: int
    items: List[ExecutionEvent]
    next_cursor: Optional[str] = None
    has_more: bool = False


class SessionSummary(BaseModel):
    api_version: str = Field(default=API_VERSION)

    session_id: str
    status: str
    mode: str = ""
    environment: str = ""
    started_at_utc: str
    ended_at_utc: Optional[str] = None
    last_update_utc: str


class SessionsListResponse(ApiEnvelope):
    count: int
    sessions: List[SessionSummary]


@router.get("/api/healthz", response_model=HealthzResponse)
async def api_healthz_v0_2() -> HealthzResponse:
    # Dedicated v0.2 health endpoint (watch-only).
    return HealthzResponse(generated_at_utc=_utc_now_iso())


@router.get("/api/execution/runs", response_model=RunsListResponse)
async def api_execution_runs_v0_2(
    limit: int = Query(200, ge=1, le=2000, description="Max runs to return"),
    root: str = Query("logs/execution", description="JSONL root (read-only)"),
    filename: str = Query(
        "execution_pipeline_events_v0.jsonl", description="JSONL filename (read-only)"
    ),
) -> RunsListResponse:
    events = _read_jsonl_events_v0(Path(root), filename)
    grouped = _group_events_by_run(events)

    runs: List[RunSummary] = []
    for run_id, evs in grouped.items():
        evs_sorted = sorted(evs, key=_event_sort_key)
        counts: Dict[str, int] = {}
        for e in evs_sorted:
            et = str(e.get("event_type") or "")
            if et:
                counts[et] = counts.get(et, 0) + 1

        runs.append(
            RunSummary(
                run_id=run_id,
                correlation_id=str(evs_sorted[0].get("correlation_id") or ""),
                started_at_utc=str(evs_sorted[0].get("ts") or "") or None,
                last_event_at_utc=str(evs_sorted[-1].get("ts") or "") or None,
                status=_status_from_counts(counts),
                counts=dict(sorted(counts.items())),
            )
        )

    # Newest first, deterministic tie-breakers
    runs.sort(
        key=lambda r: (
            r.last_event_at_utc or "",
            r.run_id,
        ),
        reverse=True,
    )
    runs = runs[:limit]

    return RunsListResponse(
        generated_at_utc=_utc_now_iso(),
        count=len(runs),
        runs=runs,
    )


@router.get("/api/execution/runs/{run_id}", response_model=RunDetailResponse)
async def api_execution_run_detail_v0_2(
    run_id: str,
    root: str = Query("logs/execution", description="JSONL root (read-only)"),
    filename: str = Query(
        "execution_pipeline_events_v0.jsonl", description="JSONL filename (read-only)"
    ),
) -> RunDetailResponse:
    events = _read_jsonl_events_v0(Path(root), filename)
    evs = [e for e in events if str(e.get("run_id") or "") == run_id]
    if not evs:
        raise HTTPException(status_code=404, detail="run_not_found")

    evs_sorted = sorted(evs, key=_event_sort_key)
    counts: Dict[str, int] = {}
    for e in evs_sorted:
        et = str(e.get("event_type") or "")
        if et:
            counts[et] = counts.get(et, 0) + 1

    detail = RunDetail(
        run_id=run_id,
        correlation_id=str(evs_sorted[0].get("correlation_id") or ""),
        started_at_utc=str(evs_sorted[0].get("ts") or "") or None,
        last_event_at_utc=str(evs_sorted[-1].get("ts") or "") or None,
        status=_status_from_counts(counts),
        counts=dict(sorted(counts.items())),
        total_events=len(evs_sorted),
    )

    return RunDetailResponse(generated_at_utc=_utc_now_iso(), run=detail)


@router.get("/api/execution/runs/{run_id}/events", response_model=RunEventsResponse)
async def api_execution_run_events_v0_2(
    run_id: str,
    limit: int = Query(200, ge=1, le=5000, description="Max events to return"),
    cursor: Optional[str] = Query(None, description="Pagination cursor (opaque string)"),
    root: str = Query("logs/execution", description="JSONL root (read-only)"),
    filename: str = Query(
        "execution_pipeline_events_v0.jsonl", description="JSONL filename (read-only)"
    ),
) -> RunEventsResponse:
    start = _parse_int_cursor(cursor)

    events = _read_jsonl_events_v0(Path(root), filename)
    evs = [e for e in events if str(e.get("run_id") or "") == run_id]
    if not evs:
        raise HTTPException(status_code=404, detail="run_not_found")

    evs_sorted = sorted(evs, key=_event_sort_key)
    total = len(evs_sorted)

    if start > total:
        # Cursor beyond end: return empty page deterministically
        return RunEventsResponse(
            generated_at_utc=_utc_now_iso(),
            run_id=run_id,
            count=0,
            items=[],
            next_cursor=None,
            has_more=False,
        )

    page = evs_sorted[start : start + limit]
    items: List[ExecutionEvent] = []
    for idx, raw in enumerate(page, start=start):
        payload = raw.get("payload")
        payload_dict = payload if isinstance(payload, dict) else {}
        items.append(
            ExecutionEvent(
                seq=idx,
                ts=str(raw.get("ts") or ""),
                event_type=str(raw.get("event_type") or ""),
                order_id=raw.get("order_id"),
                idempotency_key=raw.get("idempotency_key"),
                payload=payload_dict,
            )
        )

    next_start = start + len(items)
    has_more = next_start < total
    next_cursor_out = str(next_start) if has_more else None

    return RunEventsResponse(
        generated_at_utc=_utc_now_iso(),
        run_id=run_id,
        count=len(items),
        items=items,
        next_cursor=next_cursor_out,
        has_more=has_more,
    )


@router.get("/api/live/sessions", response_model=SessionsListResponse)
async def api_live_sessions_v0_2(
    limit: int = Query(50, ge=1, le=500, description="Max sessions to return"),
    base_dir: Optional[str] = Query(None, description="Registry base_dir override (tests/dev)"),
) -> SessionsListResponse:
    from .live_track import get_recent_live_sessions

    base_path = Path(base_dir) if base_dir else None
    sessions_raw = get_recent_live_sessions(limit=limit, base_dir=base_path)

    sessions: List[SessionSummary] = []
    for s in sessions_raw:
        started = s.started_at.isoformat()
        ended = s.ended_at.isoformat() if s.ended_at else None
        last_update = ended or started
        sessions.append(
            SessionSummary(
                session_id=s.session_id,
                status=str(s.status),
                mode=str(s.mode or ""),
                environment=str(s.environment or ""),
                started_at_utc=started,
                ended_at_utc=ended,
                last_update_utc=last_update,
            )
        )

    # Deterministic ordering: newest first, stable tie-breakers
    sessions.sort(key=lambda x: (x.last_update_utc, x.session_id), reverse=True)
    sessions = sessions[:limit]

    return SessionsListResponse(
        generated_at_utc=_utc_now_iso(),
        count=len(sessions),
        sessions=sessions,
    )
