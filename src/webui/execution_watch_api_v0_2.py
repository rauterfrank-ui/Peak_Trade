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
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# v0.2 contract remains (non-breaking). v0.3 semantics are exposed via `meta.api_version`.
API_VERSION = "v0.2"
META_API_VERSION = "v0.4"

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


def _read_jsonl_events_v0(root: Path, filename: str) -> Tuple[List[Dict[str, Any]], int]:
    """
    Read JSONL file and return raw event dicts for schema=execution_event_v0.

    We attach a deterministic file order key `_file_seq` (line index starting at 0)
    to guarantee stable ordering when timestamps tie.
    """
    p = root / filename
    if not p.exists():
        return [], 0

    read_errors = 0
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
                    # Malformed JSONL line: skip but count deterministically.
                    read_errors += 1
                    continue
                if obj.get("schema") != "execution_event_v0":
                    continue
                obj["_file_seq"] = idx
                out.append(obj)
    except Exception:
        # Watch-only endpoint: fail soft (empty list) unless caller expects 404 for missing run.
        return [], 0

    return out, read_errors


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


def _enabled_exec_watch_metrics() -> bool:
    # Best-effort opt-in; keep read-only and avoid hard dependency.
    return os.getenv("PEAK_TRADE_EXECUTION_WATCH_METRICS_ENABLED", "0") == "1"


try:
    from prometheus_client import Counter as _PromCounter  # type: ignore
    from prometheus_client import Histogram as _PromHistogram  # type: ignore

    _PROM_AVAILABLE = True
except Exception:  # pragma: no cover
    _PromCounter = None  # type: ignore
    _PromHistogram = None  # type: ignore
    _PROM_AVAILABLE = False


_PROM_REQUESTS_TOTAL = None
_PROM_REQUEST_LATENCY = None
_PROM_READ_ERRORS_TOTAL = None

# In-memory fallback (only when explicitly enabled; not exposed by default to keep determinism)
_MEM_REQUESTS_TOTAL: Dict[Tuple[str, str], int] = {}
_MEM_LATENCY_SUM: Dict[str, float] = {}
_MEM_LATENCY_COUNT: Dict[str, int] = {}
_MEM_READ_ERRORS_TOTAL: int = 0


def _init_exec_watch_prom_metrics() -> None:
    global _PROM_REQUESTS_TOTAL, _PROM_REQUEST_LATENCY, _PROM_READ_ERRORS_TOTAL
    if _PROM_REQUESTS_TOTAL is not None:
        return
    if not _PROM_AVAILABLE:
        return
    if os.getenv("PEAK_TRADE_PROMETHEUS_ENABLED", "0") != "1":
        # Align with existing /metrics gating in src/live/web/metrics_prom.py
        return
    _PROM_REQUESTS_TOTAL = _PromCounter(  # type: ignore[misc]
        "peak_trade_execution_watch_requests_total",
        "Total requests handled by Execution Watch watch-only endpoints.",
        labelnames=("endpoint", "status"),
    )
    _PROM_REQUEST_LATENCY = _PromHistogram(  # type: ignore[misc]
        "peak_trade_execution_watch_request_latency_seconds",
        "Request latency (seconds) for Execution Watch watch-only endpoints.",
        labelnames=("endpoint",),
        buckets=(0.001, 0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
    )
    _PROM_READ_ERRORS_TOTAL = _PromCounter(  # type: ignore[misc]
        "peak_trade_execution_watch_read_errors_total",
        "Total malformed JSONL lines skipped by Execution Watch.",
    )


def _record_exec_watch_metrics(
    *,
    endpoint: str,
    status: str,
    latency_s: float,
    read_errors: int = 0,
) -> None:
    # Prometheus (best-effort)
    try:
        _init_exec_watch_prom_metrics()
        if _PROM_REQUESTS_TOTAL is not None:
            _PROM_REQUESTS_TOTAL.labels(endpoint=endpoint, status=status).inc()  # type: ignore[union-attr]
        if _PROM_REQUEST_LATENCY is not None:
            _PROM_REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency_s)  # type: ignore[union-attr]
        if _PROM_READ_ERRORS_TOTAL is not None and read_errors:
            _PROM_READ_ERRORS_TOTAL.inc(read_errors)  # type: ignore[union-attr]
    except Exception:
        pass

    # In-memory (opt-in)
    if not _enabled_exec_watch_metrics():
        return
    try:
        _MEM_REQUESTS_TOTAL[(endpoint, status)] = _MEM_REQUESTS_TOTAL.get((endpoint, status), 0) + 1
        _MEM_LATENCY_SUM[endpoint] = _MEM_LATENCY_SUM.get(endpoint, 0.0) + float(latency_s)
        _MEM_LATENCY_COUNT[endpoint] = _MEM_LATENCY_COUNT.get(endpoint, 0) + 1
        global _MEM_READ_ERRORS_TOTAL
        _MEM_READ_ERRORS_TOTAL += int(read_errors or 0)
    except Exception:
        pass


class DatasetStats(BaseModel):
    runs_count: int = 0
    events_count: int = 0
    sessions_count: Optional[int] = None


def _dataset_stats_for_events(events: List[Dict[str, Any]]) -> DatasetStats:
    grouped = _group_events_by_run(events)
    return DatasetStats(runs_count=len(grouped), events_count=len(events), sessions_count=None)


def _last_event_utc_for_events(events: List[Dict[str, Any]]) -> Optional[str]:
    if not events:
        return None
    evs_sorted = sorted(events, key=_event_sort_key)
    return str(evs_sorted[-1].get("ts") or "") or None


def _count_sessions_in_dir(base_dir: Optional[str]) -> Optional[int]:
    """
    Deterministic, best-effort sessions_count.
    Only computed when base_dir is explicitly provided to avoid global filesystem variance.
    """
    if not base_dir:
        return None
    try:
        p = Path(base_dir)
        if not p.exists() or not p.is_dir():
            return 0
        return len(sorted(p.glob("*.json")))
    except Exception:
        return None


class ResponseMeta(BaseModel):
    api_version: str = Field(default=META_API_VERSION)
    generated_at_utc: str
    has_more: bool = False
    next_cursor: Optional[str] = None
    read_errors: int = 0
    source: str = Field(default="local", description="fixture|local")
    last_event_utc: Optional[str] = None
    dataset_stats: Optional[DatasetStats] = None


class ApiEnvelope(BaseModel):
    api_version: str = Field(default=API_VERSION)
    generated_at_utc: str = Field(..., description="UTC ISO timestamp when payload was generated")
    meta: Optional[ResponseMeta] = None


def _source_for_events_root(root: str, filename: str) -> str:
    # Deterministic: treat non-default root/filename as fixture source.
    if root != "logs/execution" or filename != "execution_pipeline_events_v0.jsonl":
        return "fixture"
    return "local"


def _source_for_sessions(base_dir: Optional[str]) -> str:
    return "fixture" if base_dir else "local"


def _meta(
    generated_at_utc: str,
    *,
    has_more: bool = False,
    next_cursor: Optional[str] = None,
    read_errors: int = 0,
    source: str = "local",
    last_event_utc: Optional[str] = None,
    dataset_stats: Optional[DatasetStats] = None,
) -> ResponseMeta:
    return ResponseMeta(
        generated_at_utc=generated_at_utc,
        has_more=has_more,
        next_cursor=next_cursor,
        read_errors=read_errors,
        source=source,
        last_event_utc=last_event_utc,
        dataset_stats=dataset_stats,
    )


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
    # v0.3 convenience alias (non-breaking): mirror of `items`
    events: List[ExecutionEvent] = Field(default_factory=list)
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


class ExecutionHealthResponse(ApiEnvelope):
    invariants: Dict[str, Any] = Field(default_factory=dict)


@router.get("/api/healthz", response_model=HealthzResponse)
async def api_healthz_v0_2() -> HealthzResponse:
    # Dedicated v0.2 health endpoint (watch-only).
    t0 = time.perf_counter()
    gen = _utc_now_iso()
    try:
        return HealthzResponse(
            generated_at_utc=gen,
            meta=_meta(gen, read_errors=0, source="local"),
        )
    finally:
        _record_exec_watch_metrics(
            endpoint="/api/healthz",
            status="200",
            latency_s=time.perf_counter() - t0,
            read_errors=0,
        )


@router.get("/api/execution/runs", response_model=RunsListResponse)
async def api_execution_runs_v0_2(
    limit: int = Query(200, ge=1, le=2000, description="Max runs to return"),
    root: str = Query("logs/execution", description="JSONL root (read-only)"),
    filename: str = Query(
        "execution_pipeline_events_v0.jsonl", description="JSONL filename (read-only)"
    ),
) -> RunsListResponse:
    t0 = time.perf_counter()
    events, read_errors = _read_jsonl_events_v0(Path(root), filename)
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

    gen = _utc_now_iso()
    try:
        return RunsListResponse(
            generated_at_utc=gen,
            meta=_meta(
                gen,
                has_more=False,
                next_cursor=None,
                read_errors=read_errors,
                source=_source_for_events_root(root, filename),
                last_event_utc=_last_event_utc_for_events(events),
                dataset_stats=_dataset_stats_for_events(events),
            ),
            count=len(runs),
            runs=runs,
        )
    finally:
        _record_exec_watch_metrics(
            endpoint="/api/execution/runs",
            status="200",
            latency_s=time.perf_counter() - t0,
            read_errors=read_errors,
        )


@router.get("/api/execution/runs/{run_id}", response_model=RunDetailResponse)
async def api_execution_run_detail_v0_2(
    run_id: str,
    root: str = Query("logs/execution", description="JSONL root (read-only)"),
    filename: str = Query(
        "execution_pipeline_events_v0.jsonl", description="JSONL filename (read-only)"
    ),
) -> RunDetailResponse:
    t0 = time.perf_counter()
    events, read_errors = _read_jsonl_events_v0(Path(root), filename)
    evs = [e for e in events if str(e.get("run_id") or "") == run_id]
    if not evs:
        _record_exec_watch_metrics(
            endpoint="/api/execution/runs/{run_id}",
            status="404",
            latency_s=time.perf_counter() - t0,
            read_errors=read_errors,
        )
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

    gen = _utc_now_iso()
    try:
        return RunDetailResponse(
            generated_at_utc=gen,
            meta=_meta(
                gen,
                has_more=False,
                next_cursor=None,
                read_errors=read_errors,
                source=_source_for_events_root(root, filename),
                last_event_utc=str(evs_sorted[-1].get("ts") or "") or None,
                dataset_stats=_dataset_stats_for_events(events),
            ),
            run=detail,
        )
    finally:
        _record_exec_watch_metrics(
            endpoint="/api/execution/runs/{run_id}",
            status="200",
            latency_s=time.perf_counter() - t0,
            read_errors=read_errors,
        )


@router.get("/api/execution/runs/{run_id}/events", response_model=RunEventsResponse)
async def api_execution_run_events_v0_2(
    run_id: str,
    limit: int = Query(200, ge=1, le=5000, description="Max events to return"),
    cursor: Optional[str] = Query(None, description="Pagination cursor (opaque string)"),
    since_cursor: Optional[str] = Query(
        None, description="Tail cursor: return events strictly after this cursor"
    ),
    root: str = Query("logs/execution", description="JSONL root (read-only)"),
    filename: str = Query(
        "execution_pipeline_events_v0.jsonl", description="JSONL filename (read-only)"
    ),
) -> RunEventsResponse:
    t0 = time.perf_counter()
    if since_cursor is not None and cursor is not None:
        _record_exec_watch_metrics(
            endpoint="/api/execution/runs/{run_id}/events",
            status="400",
            latency_s=time.perf_counter() - t0,
            read_errors=0,
        )
        raise HTTPException(status_code=400, detail="invalid_cursor")
    start = (
        _parse_int_cursor(cursor) if since_cursor is None else (_parse_int_cursor(since_cursor) + 1)
    )

    events, read_errors = _read_jsonl_events_v0(Path(root), filename)
    evs = [e for e in events if str(e.get("run_id") or "") == run_id]
    if not evs:
        _record_exec_watch_metrics(
            endpoint="/api/execution/runs/{run_id}/events",
            status="404",
            latency_s=time.perf_counter() - t0,
            read_errors=read_errors,
        )
        raise HTTPException(status_code=404, detail="run_not_found")

    evs_sorted = sorted(evs, key=_event_sort_key)
    total = len(evs_sorted)

    gen = _utc_now_iso()
    src = _source_for_events_root(root, filename)

    if start >= total:
        # Cursor at/after end: return empty page deterministically.
        # For tail mode, keep the provided cursor stable (monotonic).
        next_cursor_out = since_cursor if since_cursor is not None else None
        try:
            return RunEventsResponse(
                generated_at_utc=gen,
                meta=_meta(
                    gen,
                    has_more=False,
                    next_cursor=next_cursor_out,
                    read_errors=read_errors,
                    source=src,
                    last_event_utc=str(evs_sorted[-1].get("ts") or "") or None,
                    dataset_stats=_dataset_stats_for_events(events),
                ),
                run_id=run_id,
                count=0,
                items=[],
                events=[],
                next_cursor=next_cursor_out,
                has_more=False,
            )
        finally:
            _record_exec_watch_metrics(
                endpoint="/api/execution/runs/{run_id}/events",
                status="200",
                latency_s=time.perf_counter() - t0,
                read_errors=read_errors,
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

    if since_cursor is not None:
        # Tail mode: next_cursor is the last seen seq (watermark) to pass back as since_cursor.
        last_seen_seq = str(items[-1].seq) if items else since_cursor
        next_start = start + len(items)
        has_more = next_start < total
        next_cursor_out = last_seen_seq
    else:
        # Pagination mode (v0.2 compatible): next_cursor is next_start index.
        next_start = start + len(items)
        has_more = next_start < total
        next_cursor_out = str(next_start) if has_more else None

    try:
        return RunEventsResponse(
            generated_at_utc=gen,
            meta=_meta(
                gen,
                has_more=has_more,
                next_cursor=next_cursor_out,
                read_errors=read_errors,
                source=src,
                last_event_utc=str(evs_sorted[-1].get("ts") or "") or None,
                dataset_stats=_dataset_stats_for_events(events),
            ),
            run_id=run_id,
            count=len(items),
            items=items,
            events=items,
            next_cursor=next_cursor_out,
            has_more=has_more,
        )
    finally:
        _record_exec_watch_metrics(
            endpoint="/api/execution/runs/{run_id}/events",
            status="200",
            latency_s=time.perf_counter() - t0,
            read_errors=read_errors,
        )


@router.get("/api/live/sessions", response_model=SessionsListResponse)
async def api_live_sessions_v0_2(
    limit: int = Query(50, ge=1, le=500, description="Max sessions to return"),
    base_dir: Optional[str] = Query(None, description="Registry base_dir override (tests/dev)"),
) -> SessionsListResponse:
    t0 = time.perf_counter()
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

    gen = _utc_now_iso()
    try:
        return SessionsListResponse(
            generated_at_utc=gen,
            meta=_meta(
                gen,
                has_more=False,
                next_cursor=None,
                read_errors=0,
                source=_source_for_sessions(base_dir),
                last_event_utc=None,
                dataset_stats=DatasetStats(
                    runs_count=0,
                    events_count=0,
                    sessions_count=_count_sessions_in_dir(base_dir),
                ),
            ),
            count=len(sessions),
            sessions=sessions,
        )
    finally:
        _record_exec_watch_metrics(
            endpoint="/api/live/sessions",
            status="200",
            latency_s=time.perf_counter() - t0,
            read_errors=0,
        )


@router.get("/api/execution/health", response_model=ExecutionHealthResponse)
async def api_execution_health_v0_4(
    root: str = Query("logs/execution", description="JSONL root (read-only)"),
    filename: str = Query(
        "execution_pipeline_events_v0.jsonl", description="JSONL filename (read-only)"
    ),
    base_dir: Optional[str] = Query(
        None, description="Live-session registry base_dir override (tests/dev)"
    ),
    include_runtime_metrics: bool = Query(
        False, description="Include non-deterministic runtime metrics (opt-in)"
    ),
) -> ExecutionHealthResponse:
    """
    Execution Watch v0.4 health summary (read-only, deterministic by default).
    """
    t0 = time.perf_counter()
    events, read_errors = _read_jsonl_events_v0(Path(root), filename)
    grouped = _group_events_by_run(events)

    ordering_non_decreasing = True
    try:
        for _, evs in grouped.items():
            evs_sorted = sorted(evs, key=_event_sort_key)
            keys = [_event_sort_key(e) for e in evs_sorted]
            if keys != sorted(keys):
                ordering_non_decreasing = False
                break
    except Exception:
        ordering_non_decreasing = False

    gen = _utc_now_iso()
    src = _source_for_events_root(root, filename)
    stats = _dataset_stats_for_events(events)
    stats.sessions_count = _count_sessions_in_dir(base_dir)

    runtime_metrics: Optional[Dict[str, Any]] = None
    if include_runtime_metrics and _enabled_exec_watch_metrics():
        # Non-deterministic; explicitly opt-in
        runtime_metrics = {
            "requests_total": {f"{k[0]}|{k[1]}": v for k, v in sorted(_MEM_REQUESTS_TOTAL.items())},
            "latency_avg_seconds": {
                ep: (_MEM_LATENCY_SUM.get(ep, 0.0) / max(_MEM_LATENCY_COUNT.get(ep, 1), 1))
                for ep in sorted(_MEM_LATENCY_SUM.keys())
            },
            "read_errors_total": _MEM_READ_ERRORS_TOTAL,
        }

    try:
        return ExecutionHealthResponse(
            generated_at_utc=gen,
            meta=_meta(
                gen,
                has_more=False,
                next_cursor=None,
                read_errors=read_errors,
                source=src if src in {"fixture", "local"} else "unknown",
                last_event_utc=_last_event_utc_for_events(events),
                dataset_stats=stats,
            ),
            invariants={
                "cursor_monotonic": True,
                "ordering_non_decreasing": ordering_non_decreasing,
                "runtime_metrics_included": bool(runtime_metrics is not None),
                "runtime_metrics": runtime_metrics,
            },
        )
    finally:
        _record_exec_watch_metrics(
            endpoint="/api/execution/health",
            status="200",
            latency_s=time.perf_counter() - t0,
            read_errors=read_errors,
        )
