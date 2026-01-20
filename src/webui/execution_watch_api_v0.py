"""
Execution Watch API v0 (Phase 16A) — read-only.

Endpoints:
- GET /api/v0/execution/health
- GET /api/v0/execution/runs
- GET /api/v0/execution/runs/{run_id}
- GET /watch/execution (HTML)
"""

from __future__ import annotations

import html
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse

from src.execution_pipeline.store import JsonlExecutionRunStore

router = APIRouter(tags=["execution-watch-v0"])


def _store(root: str, filename: str) -> JsonlExecutionRunStore:
    return JsonlExecutionRunStore(root=Path(root), filename=filename)


@router.get("/api/v0/execution/health")
async def execution_health_v0(
    root: str = Query("logs/execution", description="JSONL root (read-only)"),
    filename: str = Query(
        "execution_pipeline_events_v0.jsonl", description="JSONL filename (read-only)"
    ),
) -> Dict[str, Any]:
    p = Path(root) / filename
    return {
        "status": "ok",
        "watch_only": True,
        "schema": "execution_event_v0",
        "root": str(Path(root)),
        "filename": filename,
        "exists": p.exists(),
    }


@router.get("/api/v0/execution/runs")
async def execution_runs_v0(
    limit: int = Query(200, ge=1, le=2000),
    root: str = Query("logs/execution", description="JSONL root (read-only)"),
    filename: str = Query(
        "execution_pipeline_events_v0.jsonl", description="JSONL filename (read-only)"
    ),
) -> Dict[str, Any]:
    st = _store(root, filename)
    runs = [asdict(r) for r in st.list_runs(limit=limit)]
    return {"count": len(runs), "runs": runs}


@router.get("/api/v0/execution/runs/{run_id}")
async def execution_run_detail_v0(
    run_id: str,
    limit: int = Query(2000, ge=1, le=50000),
    root: str = Query("logs/execution", description="JSONL root (read-only)"),
    filename: str = Query(
        "execution_pipeline_events_v0.jsonl", description="JSONL filename (read-only)"
    ),
) -> Dict[str, Any]:
    st = _store(root, filename)
    data = st.get_run(run_id, limit=limit)
    if not data.get("events"):
        raise HTTPException(status_code=404, detail="run_not_found")
    return data


@router.get("/watch/execution", response_class=HTMLResponse)
async def execution_watch_page_v0(
    request: Request,
    run_id: Optional[str] = Query(None, description="Optional run selector"),
    root: str = Query("logs/execution", description="JSONL root (read-only)"),
    filename: str = Query(
        "execution_pipeline_events_v0.jsonl", description="JSONL filename (read-only)"
    ),
) -> Any:
    st = _store(root, filename)
    runs = st.list_runs(limit=200)

    detail: Optional[Dict[str, Any]] = None
    if run_id:
        try:
            detail = st.get_run(run_id, limit=2000)
        except Exception:
            detail = None

    def esc(x: Any) -> str:
        return html.escape("" if x is None else str(x))

    base = str(request.url.path)
    q_root = f"&root={esc(root)}&filename={esc(filename)}"

    lines: list[str] = []
    lines.append("<!doctype html>")
    lines.append("<html><head><meta charset='utf-8'>")
    lines.append("<meta name='viewport' content='width=device-width,initial-scale=1'>")
    lines.append("<title>Execution Watch (v0)</title>")
    lines.append(
        "<style>"
        "body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:24px;background:#0b0f14;color:#e6edf3}"
        "a{color:#7ee787;text-decoration:none} a:hover{text-decoration:underline}"
        ".note{padding:10px 12px;border:1px solid #30363d;border-radius:8px;background:#0d1117;margin-bottom:16px}"
        "table{border-collapse:collapse;width:100%;background:#0d1117;border:1px solid #30363d}"
        "th,td{padding:8px 10px;border-bottom:1px solid #30363d;font-size:13px;vertical-align:top}"
        "th{position:sticky;top:0;background:#161b22;text-align:left}"
        ".pill{display:inline-block;padding:2px 8px;border-radius:999px;border:1px solid #30363d;font-size:12px}"
        ".ok{color:#7ee787}.bad{color:#ffa198}.muted{color:#9da7b3}"
        ".grid{display:grid;grid-template-columns:1fr;gap:16px}"
        "</style>"
    )
    lines.append("</head><body>")
    lines.append("<div class='note'>")
    lines.append(
        "<strong>WATCH-ONLY</strong> — Read-only Execution/Telemetry UI. No actions. NO-LIVE."
    )
    lines.append("<div class='muted'>Quelle: JSONL Events (schema=execution_event_v0)</div>")
    lines.append("</div>")

    lines.append("<div class='grid'>")
    lines.append("<div>")
    lines.append("<h2>Runs</h2>")
    lines.append("<table><thead><tr>")
    lines.append("<th>run_id</th><th>status</th><th>started</th><th>last</th><th>counts</th>")
    lines.append("</tr></thead><tbody>")
    for r in runs:
        status = r.status
        cls = "ok" if status == "success" else ("bad" if status == "failed" else "muted")
        href = f"{base}?run_id={esc(r.run_id)}{q_root}"
        counts = ", ".join([f"{k}={v}" for k, v in sorted(r.counts.items())]) if r.counts else ""
        lines.append("<tr>")
        lines.append(
            f"<td><a href='{href}'>{esc(r.run_id)}</a><div class='muted'>{esc(r.correlation_id)}</div></td>"
        )
        lines.append(f"<td><span class='pill {cls}'>{esc(status)}</span></td>")
        lines.append(f"<td>{esc(r.started_at)}</td>")
        lines.append(f"<td>{esc(r.last_event_at)}</td>")
        lines.append(f"<td class='muted'>{esc(counts)}</td>")
        lines.append("</tr>")
    lines.append("</tbody></table>")
    lines.append("</div>")

    if detail and detail.get("events"):
        lines.append("<div>")
        lines.append(f"<h2>Timeline: {esc(detail.get('run_id'))}</h2>")
        summ = detail.get("summary") or {}
        lines.append(
            "<div class='note'>"
            f"<div><strong>Status:</strong> {esc(summ.get('status'))}</div>"
            f"<div class='muted'>started_at={esc(summ.get('started_at'))} last_event_at={esc(summ.get('last_event_at'))}</div>"
            "</div>"
        )
        lines.append("<table><thead><tr>")
        lines.append("<th>ts</th><th>event_type</th><th>order_id</th><th>payload</th>")
        lines.append("</tr></thead><tbody>")
        for ev in detail.get("events", []):
            lines.append("<tr>")
            lines.append(f"<td>{esc(ev.get('ts'))}</td>")
            lines.append(f"<td>{esc(ev.get('event_type'))}</td>")
            lines.append(f"<td>{esc(ev.get('order_id'))}</td>")
            payload = ev.get("payload") or {}
            lines.append(f"<td class='muted'>{esc(payload)}</td>")
            lines.append("</tr>")
        lines.append("</tbody></table>")
        lines.append("</div>")

    lines.append("</div>")
    lines.append("</body></html>")

    return HTMLResponse(content="\n".join(lines), headers={"Cache-Control": "no-store"})
