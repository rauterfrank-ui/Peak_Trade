# src/webui/app.py
"""
Peak_Trade: Web Dashboard v1.1 (Quick-Wins Polish)
==================================================

FastAPI-App für read-only Status-Ansichten:
- v1.0 Projekt-Status & Snapshot
- Strategy-Tiering Übersicht
- Live-Track Panel mit letzten Sessions (Phase 82)
- Session Explorer mit Filter & Detail-View (Phase 85)

v1.1 Polish:
- Verbesserte Status-Badges (System OK, Live LOCKED)
- Stats-Kacheln für Session Explorer
- Polished Tabellen mit Zebra-Stripes
- Sticky Header & Footer

Start:
    uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000

API Endpoints:
- GET /api/live_sessions?mode=shadow&status=completed (Filter)
- GET /api/live_sessions/{session_id} (Detail)
- GET /api/live_sessions/stats (Statistiken)
- GET /session/{session_id} (HTML Detail-Page)
- GET /api/health (Health-Check)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import toml
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .live_track import (
    LiveSessionSummary,
    LiveSessionDetail,
    get_recent_live_sessions,
    get_filtered_sessions,
    get_session_by_id,
    get_session_stats,
)


# Wir gehen davon aus: src/webui/app.py -> src/webui -> src -> REPO_ROOT
BASE_DIR = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = BASE_DIR / "templates" / "peak_trade_dashboard"


def get_project_status() -> Dict[str, Any]:
    """
    Statischer v1.0-Snapshot-Status für das Dashboard v0.

    Wenn sich später Tests / Tags ändern, kann dieser Block easy angepasst werden.
    """
    return {
        "version": "v1.0",
        "snapshot_commit": "48ecf50",
        "tags": ["v1.0-research", "v1.0-live-beta"],
        "tests_total": 2147,
        "tests_skipped": 6,
        "tests_failed": 0,
        "last_audit": "2025-12-08",
        "docs": {
            "overview": "docs/PEAK_TRADE_V1_OVERVIEW_FULL.md",
            "status": "docs/PEAK_TRADE_STATUS_OVERVIEW.md",
            "release_notes": "docs/PEAK_TRADE_V1_RELEASE_NOTES.md",
            "mini_roadmap": "docs/PEAK_TRADE_MINI_ROADMAP_V1_RESEARCH_LIVE_BETA.md",
        },
    }


def load_strategy_tiering() -> Dict[str, Any]:
    """
    Lädt das Strategy-Tiering aus config/strategy_tiering.toml und bereitet
    es für das Template auf.

    Erwartete Struktur (vereinfacht):
        [strategy.rsi_reversion]
        tier = "core"
        allow_live = true
        label = "RSI Reversion Basic"
    """
    path = BASE_DIR / "config" / "strategy_tiering.toml"
    if not path.exists():
        return {"rows": [], "counts": {}}

    raw = toml.loads(path.read_text(encoding="utf-8"))

    # Entweder ist alles unter [strategy], oder direkt auf Top-Level
    strategy_block = raw.get("strategy", raw)

    rows: List[Dict[str, Any]] = []
    counts: Dict[str, int] = {}

    for sid, meta in strategy_block.items():
        tier = meta.get("tier", "unknown")
        allow_live = bool(meta.get("allow_live", False))
        label = meta.get("label", "") or meta.get("name", "")

        rows.append(
            {
                "id": sid,
                "tier": tier,
                "allow_live": allow_live,
                "label": label,
            }
        )
        counts[tier] = counts.get(tier, 0) + 1

    rows_sorted = sorted(rows, key=lambda r: (r["tier"], r["id"]))

    return {
        "rows": rows_sorted,
        "counts": counts,
    }


templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


def load_live_sessions(limit: int = 10) -> Dict[str, Any]:
    """
    Lädt Live-Sessions für das Dashboard-Template.

    Args:
        limit: Maximale Anzahl Sessions

    Returns:
        Dict mit:
        - sessions: Liste der Sessions
        - latest: Die neueste Session (oder None)
        - has_sessions: Boolean ob Sessions vorhanden
    """
    sessions = get_recent_live_sessions(limit=limit)

    return {
        "sessions": sessions,
        "latest": sessions[0] if sessions else None,
        "has_sessions": len(sessions) > 0,
    }


def create_app() -> FastAPI:
    app = FastAPI(
        title="Peak_Trade Dashboard v1.1",
        description=(
            "Read-only Dashboard für Projekt-Status, Strategy-Tiering und Live-Sessions. "
            "v1.1: Polished UI mit Status-Badges, Stats-Kacheln und verbesserter Tabellen-Darstellung. "
            "Live-Mode ist bewusst gesperrt (Safety-First)."
        ),
        version="1.1.0",
    )

    # =========================================================================
    # HTML Dashboard Endpoints
    # =========================================================================

    @app.get("/", response_class=HTMLResponse)
    async def index(
        request: Request,
        mode: Optional[str] = Query(None, description="Filter: shadow, testnet, paper, live"),
        status: Optional[str] = Query(None, description="Filter: completed, failed, aborted, started"),
    ) -> Any:
        """HTML Dashboard mit Projekt-Status, Strategy-Tiering und Live-Track."""
        proj_status = get_project_status()
        strategy_tiering = load_strategy_tiering()

        # Phase 85: Filter anwenden wenn gesetzt
        if mode or status:
            live_track = load_filtered_sessions(limit=20, mode_filter=mode, status_filter=status)
        else:
            live_track = load_live_sessions(limit=10)

        # Filter-State für Template
        live_track["active_mode_filter"] = mode
        live_track["active_status_filter"] = status

        # Session-Statistiken
        live_track["stats"] = get_session_stats()

        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "status": proj_status,
                "strategy_tiering": strategy_tiering,
                "live_track": live_track,
            },
        )

    @app.get("/session/{session_id}", response_class=HTMLResponse)
    async def session_detail_page(
        request: Request,
        session_id: str,
    ) -> Any:
        """HTML Detail-Page für eine einzelne Session (Phase 85)."""
        detail = get_session_by_id(session_id)

        if detail is None:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

        proj_status = get_project_status()

        return templates.TemplateResponse(
            request,
            "session_detail.html",
            {
                "status": proj_status,
                "session": detail,
            },
        )

    # =========================================================================
    # API Endpoints
    # =========================================================================

    @app.get(
        "/api/live_sessions",
        response_model=List[LiveSessionSummary],
        summary="Liste der letzten Live-Sessions (mit Filter)",
        description=(
            "Liefert die letzten N Live-Sessions (Shadow/Testnet/Paper/Live) "
            "aus der Session-Registry. Phase 85: Optional filterbar nach Mode und Status."
        ),
        tags=["live-track"],
    )
    async def api_live_sessions(
        limit: int = Query(
            default=10,
            ge=1,
            le=100,
            description="Maximale Anzahl Sessions (1-100)",
        ),
        mode: Optional[str] = Query(
            None,
            description="Filter nach Mode: shadow, testnet, paper, live",
        ),
        status: Optional[str] = Query(
            None,
            description="Filter nach Status: completed, failed, aborted, started",
        ),
    ) -> List[LiveSessionSummary]:
        """
        API-Endpoint für Live-Sessions mit optionalen Filtern.

        Returns:
            Liste von LiveSessionSummary-Objekten.
            Leere Liste falls keine Sessions vorhanden.
        """
        if mode or status:
            return get_filtered_sessions(
                limit=limit,
                mode_filter=mode,
                status_filter=status,
            )
        return get_recent_live_sessions(limit=limit)

    @app.get(
        "/api/live_sessions/stats",
        summary="Aggregierte Session-Statistiken",
        description="Liefert Statistiken über alle Sessions (Phase 85).",
        tags=["live-track"],
    )
    async def api_live_sessions_stats() -> Dict[str, Any]:
        """
        Aggregierte Statistiken über alle Sessions.

        Returns:
            Dict mit total_sessions, by_mode, by_status, total_pnl, avg_drawdown
        """
        return get_session_stats()

    @app.get(
        "/api/live_sessions/{session_id}",
        response_model=LiveSessionDetail,
        summary="Detail-Ansicht einer Session",
        description="Liefert alle Details einer einzelnen Session nach ID (Phase 85).",
        tags=["live-track"],
    )
    async def api_live_session_detail(session_id: str) -> LiveSessionDetail:
        """
        Detail-Endpoint für eine einzelne Session.

        Returns:
            LiveSessionDetail mit allen Feldern inkl. Config, Metrics, CLI-Args.

        Raises:
            HTTPException 404: Wenn Session nicht gefunden.
        """
        detail = get_session_by_id(session_id)
        if detail is None:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
        return detail

    @app.get(
        "/api/health",
        summary="Health-Check",
        tags=["system"],
    )
    async def api_health() -> Dict[str, str]:
        """Einfacher Health-Check Endpoint."""
        return {"status": "ok"}

    return app


def load_filtered_sessions(
    limit: int = 20,
    mode_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Lädt gefilterte Live-Sessions für das Dashboard-Template (Phase 85).

    Args:
        limit: Maximale Anzahl Sessions
        mode_filter: Filter nach Mode
        status_filter: Filter nach Status

    Returns:
        Dict mit sessions, latest, has_sessions
    """
    sessions = get_filtered_sessions(
        limit=limit,
        mode_filter=mode_filter,
        status_filter=status_filter,
    )

    return {
        "sessions": sessions,
        "latest": sessions[0] if sessions else None,
        "has_sessions": len(sessions) > 0,
    }


# Für uvicorn: `uvicorn src.webui.app:app --reload`
app = create_app()
