# src/webui/app.py
"""
Peak_Trade: Web Dashboard v1.4 (R&D Comparison View)
====================================================

FastAPI-App für read-only Status-Ansichten:
- v1.0 Projekt-Status & Snapshot
- Strategy-Tiering Übersicht
- Live-Track Panel mit letzten Sessions (Phase 82)
- Session Explorer mit Filter & Detail-View (Phase 85)
- R&D Dashboard API (Phase 76)
- R&D Experiment Detail View (Phase 77)
- R&D Multi-Run Comparison View (Phase 78)

v1.4 Features (Phase 78):
- Multi-Run Comparison View (/r_and_d/comparison)
- Checkbox-Auswahl in der R&D-Übersicht
- Best-Metric-Hervorhebung im Comparison-View

v1.3 Features (Phase 77):
- R&D Experiment Detail View mit Report-Links
- Klickbare Zeilen in der R&D-Übersicht → Detail-Ansicht
- Report-Link-Integration (HTML, Markdown, Charts)

v1.2 Features:
- R&D Dashboard API mit Experiments, Aggregations und Stats
- Endpoints analog zu `view_r_and_d_experiments.py`

v1.1 Polish:
- Verbesserte Status-Badges (System OK, Live LOCKED)
- Stats-Kacheln für Session Explorer
- Polished Tabellen mit Zebra-Stripes
- Sticky Header & Footer

Start:
    uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000

HTML Pages:
- GET / (Dashboard Home)
- GET /session/{session_id} (Session Detail)
- GET /r_and_d (R&D Experiments Overview - Phase 76)
- GET /r_and_d/experiment/{run_id} (R&D Experiment Detail - Phase 77)
- GET /r_and_d/comparison (R&D Multi-Run Comparison - Phase 78)

API Endpoints:
Live-Track:
- GET /api/live_sessions?mode=shadow&status=completed (Filter)
- GET /api/live_sessions/{session_id} (Detail)
- GET /api/live_sessions/stats (Statistiken)

R&D Dashboard (Phase 76/77/78):
- GET /api/r_and_d/experiments (Liste mit Filtern)
- GET /api/r_and_d/experiments/{run_id} (Detail mit Report-Links - v1.2)
- GET /api/r_and_d/experiments/batch (Batch-Abfrage für Comparison - v1.3)
- GET /api/r_and_d/summary (Summary-Statistiken)
- GET /api/r_and_d/presets (Aggregation nach Preset)
- GET /api/r_and_d/strategies (Aggregation nach Strategy)
- GET /api/r_and_d/stats (Globale Statistiken)

System:
- GET /api/health (Health-Check)
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import toml
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

from .live_track import (
    LiveSessionSummary,
    LiveSessionDetail,
    get_recent_live_sessions,
    get_filtered_sessions,
    get_session_by_id,
    get_session_stats,
)
from .r_and_d_api import (
    router as r_and_d_router,
    set_base_dir as set_r_and_d_base_dir,
    load_experiments_from_dir,
    filter_experiments,
    extract_flat_fields,
    compute_global_stats,
    # v1.3 (Phase 78)
    find_experiment_by_run_id,
    build_experiment_detail,
    compute_best_metrics,
    parse_and_validate_run_ids,
)
from .alerts_api import (
    AlertSummary,
    AlertStats,
    AlertListResponse,
    get_alerts_for_ui,
    get_alert_statistics,
    get_alerts_template_context,
)
# Phase 16F: Telemetry Health & Console
try:
    from src.execution.telemetry_retention import discover_sessions as discover_telemetry_sessions, RetentionPolicy
    from src.execution.telemetry_health import run_health_checks, HealthThresholds
    TELEMETRY_AVAILABLE = True
except ImportError:
    discover_telemetry_sessions = None
    RetentionPolicy = None
    run_health_checks = None
    HealthThresholds = None
    TELEMETRY_AVAILABLE = False

from .health_endpoint import (
    router as health_router,
    register_standard_checks,
)
# Phase 16K: Stage1 Ops Dashboard
from .ops_stage1_router import (
    router as stage1_router,
    set_stage1_config,
)
# Ops Workflows Hub
from .ops_workflows_router import (
    router as workflows_router,
    set_workflows_config,
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


def load_strategy_tiering(include_research: bool = False) -> Dict[str, Any]:
    """
    Lädt das Strategy-Tiering aus config/strategy_tiering.toml und bereitet
    es für das Template auf.

    Args:
        include_research: Wenn True, werden auch R&D/Research-Strategien inkludiert.
                         Default: False (nur freigegebene Tiers)

    Erwartete Struktur (vereinfacht):
        [strategy.rsi_reversion]
        tier = "core"
        allow_live = true
        label = "RSI Reversion Basic"

        # R&D-Strategien haben zusätzlich:
        category = "cycles"           # Gruppierung (cycles, volatility, ml, microstructure)
        risk_profile = "experimental" # Risikoprofil
        owner = "research"            # Team/Bereich
        tags = ["cycles", "timing"]   # Schlagworte

    Returns:
        Dict mit:
        - rows: Liste aller Strategien
        - counts: Anzahl pro Tier
        - tiers: Gruppierte Strategien pro Tier (für API)
        - categories: Verfügbare R&D-Kategorien (nur wenn include_research=True)
    """
    path = BASE_DIR / "config" / "strategy_tiering.toml"
    if not path.exists():
        return {"rows": [], "counts": {}, "tiers": [], "categories": []}

    raw = toml.loads(path.read_text(encoding="utf-8"))

    # Entweder ist alles unter [strategy], oder direkt auf Top-Level
    strategy_block = raw.get("strategy", raw)

    rows: List[Dict[str, Any]] = []
    counts: Dict[str, int] = {}
    categories_set: set = set()

    # Tier-Label-Mapping für bessere Anzeige
    tier_labels = {
        "core": "Core",
        "aux": "Auxiliary",
        "legacy": "Legacy",
        "r_and_d": "R&D / Research",
        "unclassified": "Unclassified",
    }

    # Category-Label-Mapping für R&D-Strategien
    category_labels = {
        "cycles": "Cycles & Timing",
        "volatility": "Volatility Models",
        "microstructure": "Microstructure",
        "ml": "Machine Learning",
    }

    # Tiers die standardmäßig angezeigt werden (ohne Research)
    standard_tiers = {"core", "aux", "legacy", "unclassified"}

    for sid, meta in strategy_block.items():
        tier = meta.get("tier", "unknown")
        allow_live = bool(meta.get("allow_live", False))
        label = meta.get("label", "") or meta.get("name", "")
        notes = meta.get("notes", "")

        # R&D-spezifische Felder
        category = meta.get("category", "")
        risk_profile = meta.get("risk_profile", "")
        owner = meta.get("owner", "")
        tags = meta.get("tags", [])

        # Filtere R&D-Strategien wenn include_research=False
        if tier == "r_and_d" and not include_research:
            continue

        # Sammle Kategorien für R&D
        if tier == "r_and_d" and category:
            categories_set.add(category)

        # Extrahiere is_live_ready und allowed_environments aus Notes/Meta
        is_live_ready = allow_live
        allowed_environments = ["offline_backtest"]
        if tier in {"core", "aux"}:
            allowed_environments.append("shadow")
        if allow_live:
            allowed_environments.extend(["testnet", "live"])
        if tier == "r_and_d":
            allowed_environments = ["offline_backtest", "research"]

        row_data: Dict[str, Any] = {
            "id": sid,
            "tier": tier,
            "tier_label": tier_labels.get(tier, tier),
            "allow_live": allow_live,
            "is_live_ready": is_live_ready,
            "label": label,
            "notes": notes,
            "allowed_environments": allowed_environments,
        }

        # R&D-spezifische Felder hinzufügen wenn vorhanden
        if tier == "r_and_d":
            row_data["category"] = category
            row_data["category_label"] = category_labels.get(category, category)
            row_data["risk_profile"] = risk_profile
            row_data["owner"] = owner
            row_data["tags"] = tags

        rows.append(row_data)
        counts[tier] = counts.get(tier, 0) + 1

    rows_sorted = sorted(rows, key=lambda r: (r["tier"], r["id"]))

    # Gruppiere nach Tier für API-Response
    tiers_grouped: List[Dict[str, Any]] = []
    for tier_key in ["core", "aux", "legacy", "r_and_d", "unclassified"]:
        tier_strategies = [r for r in rows_sorted if r["tier"] == tier_key]
        if tier_strategies:
            tier_group: Dict[str, Any] = {
                "tier": tier_key,
                "label": tier_labels.get(tier_key, tier_key),
                "strategies": tier_strategies,
            }
            # Für R&D-Tier: Gruppiere auch nach Kategorie
            if tier_key == "r_and_d" and include_research:
                by_category: Dict[str, List[Dict[str, Any]]] = {}
                for s in tier_strategies:
                    cat = s.get("category", "other")
                    if cat not in by_category:
                        by_category[cat] = []
                    by_category[cat].append(s)
                tier_group["by_category"] = [
                    {
                        "category": cat,
                        "label": category_labels.get(cat, cat),
                        "strategies": strats,
                    }
                    for cat, strats in sorted(by_category.items())
                ]
            tiers_grouped.append(tier_group)

    # Kategorien-Liste für UI-Filter
    categories_list = [
        {"id": cat, "label": category_labels.get(cat, cat)}
        for cat in sorted(categories_set)
    ]

    return {
        "rows": rows_sorted,
        "counts": counts,
        "tiers": tiers_grouped,
        "categories": categories_list,
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
        title="Peak_Trade Dashboard v1.2",
        description=(
            "Read-only Dashboard für Projekt-Status, Strategy-Tiering, Live-Sessions und R&D-Experimente. "
            "v1.2: R&D Dashboard API (Phase 76) mit Experiments, Aggregations und Stats. "
            "Live-Mode ist bewusst gesperrt (Safety-First)."
        ),
        version="1.2.0",
    )

    # R&D API: Setze Basis-Verzeichnis und registriere Router
    set_r_and_d_base_dir(BASE_DIR)
    app.include_router(r_and_d_router)
    
    # Health Check API: Registriere Health Check Router
    app.include_router(health_router)
    register_standard_checks()
    
    # Phase 16K: Stage1 Ops Dashboard API
    stage1_report_root = BASE_DIR / "reports" / "obs" / "stage1"
    set_stage1_config(stage1_report_root, templates)
    app.include_router(stage1_router)
    
    # Ops Workflows Hub
    set_workflows_config(BASE_DIR, templates)
    app.include_router(workflows_router)
    
    # JSON API Alias für /api/ops/workflows
    @app.get("/api/ops/workflows")
    async def api_ops_workflows() -> List[Dict[str, Any]]:
        """JSON API Alias: Get list of workflow scripts."""
        from .ops_workflows_router import _get_workflow_definitions, _enrich_with_filesystem_metadata
        from dataclasses import asdict
        workflow_defs = _get_workflow_definitions()
        workflows = _enrich_with_filesystem_metadata(workflow_defs)
        return [asdict(wf) for wf in workflows]

    # =========================================================================
    # HTML Dashboard Endpoints
    # =========================================================================

    @app.get("/", response_class=HTMLResponse)
    async def index(
        request: Request,
        mode: Optional[str] = Query(None, description="Filter: shadow, testnet, paper, live"),
        status: Optional[str] = Query(None, description="Filter: completed, failed, aborted, started"),
        include_research: bool = Query(False, description="Zeige auch R&D/Research-Strategien"),
    ) -> Any:
        """HTML Dashboard mit Projekt-Status, Strategy-Tiering und Live-Track."""
        proj_status = get_project_status()
        strategy_tiering = load_strategy_tiering(include_research=include_research)
        strategy_tiering["include_research"] = include_research

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

    @app.get("/r_and_d", response_class=HTMLResponse)
    async def r_and_d_experiments_page(
        request: Request,
        preset: Optional[str] = Query(None, description="Filter nach Preset-ID"),
        strategy: Optional[str] = Query(None, description="Filter nach Strategy-ID"),
        tag_substr: Optional[str] = Query(None, description="Filter nach Tag-Substring"),
        run_type: Optional[str] = Query(None, description="Filter nach Run-Type"),
        with_trades: bool = Query(False, description="Nur Experimente mit Trades"),
        limit: int = Query(100, ge=1, le=500, description="Max. Anzahl"),
    ) -> Any:
        """HTML Overview-Page für R&D-Experimente (Phase 76 v1.1)."""
        from datetime import date

        proj_status = get_project_status()

        # Experimente laden
        all_experiments = load_experiments_from_dir()

        # Alle Experimente zu flachen Dicts konvertieren (für Stats)
        all_flat = [extract_flat_fields(exp) for exp in all_experiments]

        # Filter anwenden
        filtered_experiments = filter_experiments(
            all_experiments,
            preset=preset,
            strategy=strategy,
            tag_substr=tag_substr,
            with_trades=with_trades,
        )

        # Zusätzlicher Run-Type Filter (v1.1)
        if run_type:
            filtered_experiments = [
                exp for exp in filtered_experiments
                if extract_flat_fields(exp).get("run_type") == run_type
            ]

        # Limit anwenden
        limited_experiments = filtered_experiments[:limit]

        # Zu flachen Dicts konvertieren für Template
        experiments = [extract_flat_fields(exp) for exp in limited_experiments]

        # Statistiken berechnen
        stats = compute_global_stats(all_experiments)

        # v1.1: Daily Summary Stats (heute fertig, laufend)
        today_str = date.today().strftime("%Y-%m-%d")
        today_experiments = [e for e in all_flat if e.get("date_str") == today_str and e.get("status") != "running"]
        running_experiments = [e for e in all_flat if e.get("status") == "running"]

        stats["today_date"] = today_str
        stats["today_count"] = len(today_experiments)
        stats["today_success"] = sum(1 for e in today_experiments if e.get("status") == "success")
        stats["today_failed"] = sum(1 for e in today_experiments if e.get("status") == "failed")
        stats["running_count"] = len(running_experiments)

        # Filter-State für Template
        filters = {
            "preset": preset,
            "strategy": strategy,
            "tag_substr": tag_substr,
            "run_type": run_type,
            "with_trades": with_trades,
        }

        return templates.TemplateResponse(
            request,
            "r_and_d_experiments.html",
            {
                "status": proj_status,
                "experiments": experiments,
                "stats": stats,
                "filters": filters,
                "total": len(all_experiments),
                "filtered": len(filtered_experiments),
                "limit": limit,
            },
        )

    @app.get("/r_and_d/experiment/{run_id}", response_class=HTMLResponse)
    async def r_and_d_experiment_detail_page(
        request: Request,
        run_id: str,
    ) -> Any:
        """
        HTML Detail-Page für ein einzelnes R&D-Experiment (Phase 77 v1.1).

        Zeigt:
        - Vollständige Meta-Daten und Parameter
        - Kern-Metriken mit visueller Hervorhebung
        - Report-Links (HTML, Markdown, Charts)
        - Status-/Run-Type-Badges
        - Raw JSON (collapsible)
        
        v1.1: Refactored - nutzt zentralisierte Helper-Funktionen aus r_and_d_api.py
        """
        proj_status = get_project_status()

        # Experiment laden (nutze zentralisierte Lookup-Funktion)
        all_experiments = load_experiments_from_dir()
        exp = find_experiment_by_run_id(all_experiments, run_id)

        if exp is None:
            # 404 - Experiment nicht gefunden
            return templates.TemplateResponse(
                request,
                "error.html",
                {
                    "status": proj_status,
                    "error_code": 404,
                    "error_message": f"Experiment nicht gefunden: {run_id}",
                    "back_link": "/r_and_d",
                    "back_label": "Zurück zum R&D Hub",
                },
                status_code=404,
            )

        # Baue Detail-Data (nutze zentralisierte Funktion)
        experiment_data = build_experiment_detail(exp)
        experiment_data["raw"] = exp  # Nur für Detail-View

        return templates.TemplateResponse(
            request,
            "r_and_d_experiment_detail.html",
            {
                "status": proj_status,
                "experiment": experiment_data,
            },
        )

    # =========================================================================
    # Phase 83: Alert-Historie & Status
    # =========================================================================

    @app.get("/live/alerts", response_class=HTMLResponse)
    async def alerts_page(
        request: Request,
        hours: int = Query(24, ge=1, le=168, description="Zeitfenster in Stunden"),
        severity: Optional[List[str]] = Query(None, description="Severity-Filter"),
        category: Optional[List[str]] = Query(None, description="Category-Filter"),
        session_id: Optional[str] = Query(None, description="Session-ID-Filter"),
        limit: int = Query(100, ge=1, le=500, description="Max. Anzahl Alerts"),
    ) -> Any:
        """
        HTML-View für Alert-Historie (Phase 83).

        Zeigt:
        - Status-Kacheln (Total, CRITICAL, WARN, Sessions)
        - Filterbare Alert-Tabelle
        - Link zum Operator-Runbook
        """
        proj_status = get_project_status()

        # Template-Context aufbauen
        context = get_alerts_template_context(
            limit=limit,
            hours=hours,
            severity=severity,
            category=category,
            session_id=session_id,
        )

        return templates.TemplateResponse(
            request,
            "alerts.html",
            {
                "status": proj_status,
                **context,
            },
        )

    @app.get("/r_and_d/comparison", response_class=HTMLResponse)
    async def r_and_d_comparison_page(
        request: Request,
        run_ids: Optional[str] = Query(None, description="Komma-separierte Run-IDs"),
    ) -> Any:
        """
        HTML Comparison-Page für mehrere R&D-Experimente (Phase 78 v1.1).

        Zeigt einen Vergleich mehrerer Experimente nebeneinander:
        - Kern-Metriken mit Best-Metric-Hervorhebung
        - Links zu Einzelansichten
        - Status-/Run-Type-Badges
        
        v1.1: Refactored - nutzt zentralisierte Helper-Funktionen aus r_and_d_api.py
        """
        proj_status = get_project_status()

        # Validierung: run_ids erforderlich
        if not run_ids or not run_ids.strip():
            return templates.TemplateResponse(
                request,
                "r_and_d_experiment_comparison.html",
                {
                    "status": proj_status,
                    "experiments": [],
                    "error": "Keine Run-IDs angegeben. Bitte wähle Experimente in der Übersicht aus.",
                    "best_metrics": {},
                },
            )

        # Parse und validiere IDs (ValueError → HTML-Fehlerseite)
        try:
            unique_ids = parse_and_validate_run_ids(run_ids, min_ids=2, max_ids=10)
        except ValueError as e:
            return templates.TemplateResponse(
                request,
                "r_and_d_experiment_comparison.html",
                {
                    "status": proj_status,
                    "experiments": [],
                    "error": str(e),
                    "best_metrics": {},
                },
            )

        # Lade Experimente und suche nach IDs
        all_experiments = load_experiments_from_dir()
        found_experiments: list = []
        not_found_ids: list = []

        for requested_id in unique_ids:
            exp = find_experiment_by_run_id(all_experiments, requested_id)
            
            if exp:
                experiment_data = build_experiment_detail(exp)
                found_experiments.append(experiment_data)
            else:
                not_found_ids.append(requested_id)

        # Berechne Best-Metrics (nutze API-Funktion)
        best_metrics = compute_best_metrics(found_experiments) if found_experiments else {}

        # Error/Warning Messages
        error_msg = None
        warning_msg = None
        if not found_experiments:
            error_msg = f"Keine gültigen Experimente gefunden für: {', '.join(unique_ids)}"
        elif not_found_ids:
            warning_msg = f"Hinweis: {len(not_found_ids)} Run-ID(s) nicht gefunden: {', '.join(not_found_ids)}"

        return templates.TemplateResponse(
            request,
            "r_and_d_experiment_comparison.html",
            {
                "status": proj_status,
                "experiments": found_experiments,
                "best_metrics": best_metrics,
                "not_found_ids": not_found_ids,
                "error": error_msg,
                "warning": warning_msg,
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

    # =========================================================================
    # Phase 57 Extension: Live Status Snapshot Endpoints
    # =========================================================================

    @app.get(
        "/api/live/status/snapshot.json",
        summary="Live Status Snapshot (JSON)",
        description="Returns a deterministic live status snapshot as JSON (Phase 57 Extension).",
        tags=["live-status"],
    )
    async def api_live_status_snapshot_json() -> Dict[str, Any]:
        """
        Live Status Snapshot Endpoint (JSON).

        Returns:
            Dict with version, generated_at, panels, meta (deterministic, sorted)
        """
        from fastapi.responses import JSONResponse
        from src.reporting.live_status_snapshot_builder import build_live_status_snapshot_auto
        from src.reporting.status_snapshot_schema import model_dump_helper

        try:
            snapshot = build_live_status_snapshot_auto(meta={"source": "webui_api"})
            snapshot_dict = model_dump_helper(snapshot)

            return JSONResponse(
                content=snapshot_dict,
                headers={"Cache-Control": "no-store"},
            )
        except Exception as e:
            logger.error(f"Error building live status snapshot: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to build snapshot: {str(e)}")

    @app.get(
        "/api/live/status/snapshot.html",
        response_class=HTMLResponse,
        summary="Live Status Snapshot (HTML)",
        description="Returns a live status snapshot as HTML (Phase 57 Extension, XSS-safe).",
        tags=["live-status"],
    )
    async def api_live_status_snapshot_html() -> str:
        """
        Live Status Snapshot Endpoint (HTML).

        Returns:
            HTML page with escaped panel data (XSS-safe via Phase-57 formatter)
        """
        from fastapi.responses import HTMLResponse
        from src.reporting.live_status_snapshot_builder import build_live_status_snapshot_auto
        from src.reporting.html_reports import _html_escape

        try:
            snapshot = build_live_status_snapshot_auto(meta={"source": "webui_api"})

            # Build HTML using Phase-57 formatter (_html_escape)
            html_lines = []
            html_lines.append("<!DOCTYPE html>")
            html_lines.append("<html lang='en'>")
            html_lines.append("<head>")
            html_lines.append("  <meta charset='UTF-8'>")
            html_lines.append("  <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
            html_lines.append("  <title>Peak_Trade Live Status Snapshot</title>")
            html_lines.append("  <style>")
            html_lines.append("    body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }")
            html_lines.append("    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }")
            html_lines.append("    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }")
            html_lines.append("    .meta { background: #ecf0f1; padding: 10px; border-radius: 4px; margin: 15px 0; font-size: 0.9em; }")
            html_lines.append("    .panel { margin: 20px 0; border: 1px solid #ddd; border-radius: 4px; padding: 15px; }")
            html_lines.append("    .panel h2 { margin: 0 0 10px 0; font-size: 1.2em; }")
            html_lines.append("    .status-ok { color: #27ae60; font-weight: bold; }")
            html_lines.append("    .status-warn { color: #f39c12; font-weight: bold; }")
            html_lines.append("    .status-error { color: #e74c3c; font-weight: bold; }")
            html_lines.append("    .status-unknown { color: #95a5a6; font-weight: bold; }")
            html_lines.append("    .details { background: #f9f9f9; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 0.85em; white-space: pre-wrap; }")
            html_lines.append("  </style>")
            html_lines.append("</head>")
            html_lines.append("<body>")
            html_lines.append("  <div class='container'>")
            html_lines.append("    <h1>Peak_Trade Live Status Snapshot</h1>")
            html_lines.append(f"    <div class='meta'>")
            html_lines.append(f"      <strong>Version:</strong> {_html_escape(snapshot.version)}<br>")
            html_lines.append(f"      <strong>Generated:</strong> {_html_escape(snapshot.generated_at)}")
            html_lines.append(f"    </div>")

            # Render panels
            for panel in snapshot.panels:
                status_class = f"status-{panel.status}"
                html_lines.append(f"    <div class='panel'>")
                html_lines.append(f"      <h2>{_html_escape(panel.title)}</h2>")
                html_lines.append(f"      <p><strong>ID:</strong> {_html_escape(panel.id)}</p>")
                html_lines.append(f"      <p><strong>Status:</strong> <span class='{status_class}'>{_html_escape(panel.status.upper())}</span></p>")

                # Render details (XSS-safe)
                if panel.details:
                    import json
                    details_json = json.dumps(panel.details, indent=2, sort_keys=True)
                    html_lines.append(f"      <div class='details'>{_html_escape(details_json)}</div>")

                html_lines.append(f"    </div>")

            html_lines.append("  </div>")
            html_lines.append("</body>")
            html_lines.append("</html>")

            html_content = "\n".join(html_lines)

            return HTMLResponse(
                content=html_content,
                headers={"Cache-Control": "no-store"},
            )
        except Exception as e:
            logger.error(f"Error building live status snapshot HTML: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to build snapshot HTML: {str(e)}")

    # =========================================================================
    # Phase 83: Alert-Historie API Endpoints
    # =========================================================================

    @app.get(
        "/api/live/alerts",
        response_model=AlertListResponse,
        summary="Liste der letzten Alerts",
        description="Liefert Alerts aus der Alert-Pipeline mit optionalen Filtern (Phase 83).",
        tags=["alerts"],
    )
    async def api_live_alerts(
        limit: int = Query(100, ge=1, le=500, description="Max. Anzahl Alerts"),
        hours: int = Query(24, ge=1, le=168, description="Zeitfenster in Stunden"),
        severity: Optional[List[str]] = Query(None, description="Severity-Filter"),
        category: Optional[List[str]] = Query(None, description="Category-Filter"),
        session_id: Optional[str] = Query(None, description="Session-ID-Filter"),
    ) -> AlertListResponse:
        """
        API-Endpoint für Alert-Liste (Phase 83).

        Returns:
            AlertListResponse mit gefilterten Alerts
        """
        return get_alerts_for_ui(
            limit=limit,
            hours=hours,
            severity=severity,
            category=category,
            session_id=session_id,
        )

    @app.get(
        "/api/live/alerts/stats",
        response_model=AlertStats,
        summary="Alert-Statistiken",
        description="Aggregierte Statistiken über Alerts für Status-Kacheln (Phase 83).",
        tags=["alerts"],
    )
    async def api_live_alerts_stats(
        hours: int = Query(24, ge=1, le=168, description="Zeitfenster in Stunden"),
    ) -> AlertStats:
        """
        API-Endpoint für Alert-Statistiken (Phase 83).

        Returns:
            AlertStats mit aggregierten Daten
        """
        return get_alert_statistics(hours=hours)

    # =========================================================================
    # Phase 16B: Execution Timeline API Endpoints
    # =========================================================================

    @app.get(
        "/api/live/execution/{session_id}",
        summary="Execution Timeline für Session",
        description="Liefert Execution-Events für eine Session (Phase 16B).",
        tags=["execution"],
    )
    async def api_execution_timeline(
        session_id: str,
        limit: int = Query(200, ge=1, le=1000, description="Max. Anzahl Events"),
        kind: Optional[str] = Query(None, description="Filter nach Event-Kind (intent/order/fill/gate)"),
    ) -> Dict[str, Any]:
        """
        API-Endpoint für Execution Timeline (Phase 16B).

        Returns:
            Dict mit timeline, summary, filters
        """
        from src.live.execution_bridge import get_execution_timeline, get_execution_summary

        # Load timeline
        timeline_rows = get_execution_timeline(session_id, limit=limit)

        # Filter by kind if specified
        if kind:
            timeline_rows = [row for row in timeline_rows if row.kind == kind]

        # Convert to dicts for JSON
        timeline = [
            {
                "ts": row.ts.isoformat(),
                "kind": row.kind,
                "symbol": row.symbol,
                "description": row.description,
                "details": row.details,
            }
            for row in timeline_rows
        ]

        # Get summary
        summary = get_execution_summary(session_id)

        return {
            "session_id": session_id,
            "timeline": timeline,
            "summary": summary,
            "filters": {"kind": kind, "limit": limit},
            "count": len(timeline),
        }

    @app.get(
        "/live/execution/{session_id}",
        response_class=HTMLResponse,
        summary="Execution Timeline View (HTML)",
        description="HTML-View für Execution-Timeline einer Session (Phase 16B).",
    )
    async def execution_timeline_page(
        request: Request,
        session_id: str,
        limit: int = Query(200, ge=1, le=1000, description="Max. Anzahl Events"),
        kind: Optional[str] = Query(None, description="Filter nach Event-Kind"),
    ) -> Any:
        """
        HTML-View für Execution Timeline (Phase 16B).

        Zeigt:
        - Execution-Events in Tabelle
        - Filter nach Kind (intent/order/fill/gate)
        - Summary-Stats
        """
        from src.live.execution_bridge import get_execution_timeline, get_execution_summary

        proj_status = get_project_status()

        # Load timeline
        timeline_rows = get_execution_timeline(session_id, limit=limit)

        # Filter by kind if specified
        if kind:
            timeline_rows = [row for row in timeline_rows if row.kind == kind]

        # Get summary
        summary = get_execution_summary(session_id)

        # Prepare timeline for template
        timeline = [
            {
                "ts": row.ts.strftime("%Y-%m-%d %H:%M:%S"),
                "kind": row.kind,
                "symbol": row.symbol,
                "description": row.description,
                "details": row.details,
            }
            for row in timeline_rows
        ]

        return templates.TemplateResponse(
            request,
            "execution_timeline.html",
            {
                "status": proj_status,
                "session_id": session_id,
                "timeline": timeline,
                "summary": summary,
                "filters": {"kind": kind, "limit": limit},
                "count": len(timeline),
            },
        )

    # =========================================================================
    # Strategy-Tiering API Endpoints
    # =========================================================================

    @app.get(
        "/api/strategy_tiering",
        summary="Strategy-Tiering Übersicht",
        description=(
            "Liefert alle Strategien gruppiert nach Tier. "
            "Standardmäßig werden nur freigegebene Tiers (core, aux, legacy) angezeigt. "
            "Mit include_research=true werden auch R&D-Strategien inkludiert."
        ),
        tags=["strategy-tiering"],
    )
    async def api_strategy_tiering(
        include_research: bool = Query(
            default=False,
            description=(
                "Wenn true, werden auch R&D/Research-Strategien angezeigt. "
                "Diese sind NICHT für Live-Trading freigegeben."
            ),
        ),
    ) -> Dict[str, Any]:
        """
        API-Endpoint für Strategy-Tiering.

        Returns:
            Dict mit:
            - tiers: Liste der Tier-Gruppen mit Strategien
            - counts: Anzahl Strategien pro Tier
            - include_research: Ob Research-Strategien inkludiert sind

        Notes:
            R&D-Strategien (tier="r_and_d") werden nur mit include_research=true
            zurückgegeben. Diese sind ausschließlich für Offline-Backtests und
            Research gedacht - NICHT für Live-Trading.
        """
        tiering = load_strategy_tiering(include_research=include_research)

        return {
            "tiers": tiering.get("tiers", []),
            "counts": tiering.get("counts", {}),
            "categories": tiering.get("categories", []) if include_research else [],
            "include_research": include_research,
            "research_notice": (
                "R&D-Strategien sind ausschließlich für Offline-Backtests und "
                "Research gedacht. Deployment erst nach Phase-X-Freigabe möglich."
                if include_research
                else None
            ),
        }

    @app.get(
        "/api/strategy_tiering/{strategy_id}",
        summary="Strategy-Tiering Detail",
        description="Liefert Tiering-Details für eine einzelne Strategie.",
        tags=["strategy-tiering"],
    )
    async def api_strategy_tiering_detail(
        strategy_id: str,
        include_research: bool = Query(
            default=False,
            description="Erlaube Zugriff auf R&D-Strategien",
        ),
    ) -> Dict[str, Any]:
        """
        Detail-Endpoint für eine einzelne Strategie.

        Returns:
            Dict mit Strategie-Tiering-Details oder 404 wenn nicht gefunden.

        Raises:
            HTTPException 404: Wenn Strategie nicht gefunden oder R&D ohne Flag.
        """
        tiering = load_strategy_tiering(include_research=include_research)

        for row in tiering.get("rows", []):
            if row["id"] == strategy_id:
                # Zusätzliche Safety-Info für R&D-Strategien
                if row["tier"] == "r_and_d":
                    row["deployment_notice"] = (
                        "Research-only. Deployment nur nach Phase-X-Freigabe möglich."
                    )
                    row["deployment_blocked"] = True
                else:
                    row["deployment_blocked"] = not row["allow_live"]

                return row

        raise HTTPException(
            status_code=404,
            detail=f"Strategy '{strategy_id}' nicht gefunden oder R&D-Strategie (setze include_research=true)",
        )

    # ========================================================================
    # PHASE 16C: TELEMETRY VIEWER API
    # ========================================================================

    @app.get("/api/telemetry", response_model=None)
    def get_telemetry_data(
        request: Request,
        session_id: Optional[str] = Query(None, description="Filter by session ID"),
        type: Optional[str] = Query(None, description="Filter by event type"),
        symbol: Optional[str] = Query(None, description="Filter by symbol"),
        from_ts: Optional[str] = Query(None, alias="from", description="Filter events after ISO timestamp"),
        to_ts: Optional[str] = Query(None, alias="to", description="Filter events before ISO timestamp"),
        limit: int = Query(200, le=2000, description="Maximum events to return"),
        format: str = Query("json", regex="^(json|csv)$", description="Response format (json or csv)"),
    ):
        """
        Query telemetry events (Phase 16C+16D).

        Returns:
            JSON (default):
            {
                "summary": {...},
                "timeline": [...],
                "query": {...},
                "stats": {...}
            }
            
            CSV (format=csv): timeline as CSV download
        """
        from pathlib import Path
        from src.execution.telemetry_viewer import (
            TelemetryQuery,
            build_timeline,
            find_session_logs,
            iter_events,
            summarize_events,
        )

        # Build query
        query = TelemetryQuery(
            session_id=session_id,
            event_type=type,
            symbol=symbol,
            ts_from=from_ts,
            ts_to=to_ts,
            limit=limit,
        )

        # Find log files
        base_path = Path("logs/execution")
        if session_id:
            log_path = base_path / f"{session_id}.jsonl"
            if not log_path.exists():
                raise HTTPException(status_code=404, detail=f"Session log not found: {session_id}")
            paths = [log_path]
        else:
            paths = find_session_logs(base_path)
            if not paths:
                raise HTTPException(status_code=404, detail="No telemetry logs found")

        # Read events
        event_iter, stats = iter_events(paths, query)
        events_list = list(event_iter)

        if not events_list:
            return {
                "summary": {"total_events": 0, "counts_by_type": {}},
                "timeline": [],
                "query": {
                    "session_id": session_id,
                    "type": type,
                    "symbol": symbol,
                    "from": from_ts,
                    "to": to_ts,
                    "limit": limit,
                },
                "stats": {
                    "total_lines": stats.total_lines,
                    "valid_events": stats.valid_events,
                    "invalid_lines": stats.invalid_lines,
                    "error_rate": stats.error_rate,
                },
            }

        # Generate summary and timeline
        summary = summarize_events(events_list)
        timeline = build_timeline(events_list, max_items=limit)

        # CSV export (Phase 16D)
        if format == "csv":
            import csv
            import io
            from fastapi.responses import StreamingResponse
            
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=["ts", "kind", "symbol", "session_id", "description", "details"],
                extrasaction="ignore"
            )
            writer.writeheader()
            
            for item in timeline:
                # Flatten nested details for CSV
                details_str = ""
                if "details" in item and isinstance(item["details"], dict):
                    details_str = "; ".join(f"{k}={v}" for k, v in item["details"].items())
                
                writer.writerow({
                    "ts": item.get("ts", ""),
                    "kind": item.get("kind", ""),
                    "symbol": item.get("symbol", ""),
                    "session_id": item.get("session_id", ""),
                    "description": item.get("description", ""),
                    "details": details_str,
                })
            
            output.seek(0)
            filename = f"telemetry_{session_id or 'all'}_{type or 'all'}.csv"
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

        # JSON response (default)
        return {
            "summary": summary,
            "timeline": timeline,
            "query": {
                "session_id": session_id,
                "type": type,
                "symbol": symbol,
                "from": from_ts,
                "to": to_ts,
                "limit": limit,
            },
            "stats": {
                "total_lines": stats.total_lines,
                "valid_events": stats.valid_events,
                "invalid_lines": stats.invalid_lines,
                "error_rate": stats.error_rate,
            },
        }

    # ========================================================================
    # PHASE 16F: Telemetry Console & Health Endpoints
    # ========================================================================

    @app.get("/live/telemetry", response_class=HTMLResponse, tags=["Phase 16F"])
    async def telemetry_console_page(request: Request):
        """Telemetry Console - Session overview + health status (Phase 16F)."""
        if not TELEMETRY_AVAILABLE:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": "Telemetry module not available",
                    "details": "Phase 16F telemetry health module not imported",
                },
                status_code=503,
            )
        
        # Discover sessions
        telemetry_root = Path("logs/execution")
        sessions = []
        total_size_mb = 0.0
        
        if telemetry_root.exists():
            try:
                sessions_meta = discover_telemetry_sessions(telemetry_root, include_compressed=True)
                # Sort by mtime (newest first)
                sessions_meta.sort(key=lambda s: s.mtime, reverse=True)
                
                for s in sessions_meta[:50]:  # Limit to 50 most recent
                    sessions.append({
                        "session_id": s.session_id,
                        "size_mb": s.size_mb,
                        "age_days": s.age_days,
                        "is_compressed": s.is_compressed,
                        "mtime": s.mtime.isoformat(),
                        "path": str(s.path),
                    })
                    total_size_mb += s.size_mb
            except Exception as e:
                logger.warning(f"Error discovering sessions: {e}")
        
        # Run health checks
        health_report = None
        try:
            health_report = run_health_checks(telemetry_root)
        except Exception as e:
            logger.warning(f"Error running health checks: {e}")
        
        # Load health trends (Phase 16H)
        trends_summary = None
        try:
            from src.execution.telemetry_health_trends import load_snapshots, compute_rollup
            from datetime import datetime, timedelta, timezone
            
            snapshots_path = Path("logs/telemetry_health_snapshots.jsonl")
            if snapshots_path.exists():
                now = datetime.now(timezone.utc)
                
                # Load snapshots for different time windows
                snapshots_24h = load_snapshots(
                    snapshots_path,
                    since_ts=now - timedelta(hours=24),
                )
                snapshots_7d = load_snapshots(
                    snapshots_path,
                    since_ts=now - timedelta(days=7),
                )
                snapshots_30d = load_snapshots(
                    snapshots_path,
                    since_ts=now - timedelta(days=30),
                )
                
                if snapshots_30d:
                    rollup_24h = compute_rollup(snapshots_24h) if snapshots_24h else None
                    rollup_7d = compute_rollup(snapshots_7d) if snapshots_7d else None
                    rollup_30d = compute_rollup(snapshots_30d)
                    
                    trends_summary = {
                        "available": True,
                        "last_24h": {
                            "count": len(snapshots_24h),
                            "worst_severity": rollup_24h.worst_severity if rollup_24h else "unknown",
                            "critical_count": rollup_24h.critical_count if rollup_24h else 0,
                            "warn_count": rollup_24h.warn_count if rollup_24h else 0,
                        } if snapshots_24h else None,
                        "last_7d": {
                            "count": len(snapshots_7d),
                            "worst_severity": rollup_7d.worst_severity if rollup_7d else "unknown",
                            "critical_count": rollup_7d.critical_count if rollup_7d else 0,
                            "warn_count": rollup_7d.warn_count if rollup_7d else 0,
                            "disk_avg": rollup_7d.disk_avg if rollup_7d else 0.0,
                            "disk_max": rollup_7d.disk_max if rollup_7d else 0.0,
                        } if snapshots_7d else None,
                        "last_30d": {
                            "count": len(snapshots_30d),
                            "worst_severity": rollup_30d.worst_severity,
                            "critical_count": rollup_30d.critical_count,
                            "warn_count": rollup_30d.warn_count,
                            "disk_avg": rollup_30d.disk_avg,
                            "disk_max": rollup_30d.disk_max,
                        },
                    }
        except Exception as e:
            logger.warning(f"Error loading health trends: {e}")
        
        # Retention policy (default)
        retention_policy = {
            "enabled": True,
            "max_age_days": 30,
            "keep_last_n_sessions": 200,
            "max_total_mb": 2048,
            "compress_after_days": 7,
        }
        
        return templates.TemplateResponse(
            "peak_trade_dashboard/telemetry_console.html",
            {
                "request": request,
                "sessions": sessions,
                "total_sessions": len(sessions),
                "total_size_mb": round(total_size_mb, 2),
                "health_report": health_report,
                "retention_policy": retention_policy,
                "telemetry_root": str(telemetry_root),
                "trends_summary": trends_summary,
            },
        )

    @app.get("/api/telemetry/health", tags=["Phase 16F"])
    async def telemetry_health_api(
        root: str = Query("logs/execution", description="Telemetry root directory"),
    ):
        """Get telemetry health status (Phase 16F)."""
        if not TELEMETRY_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="Telemetry health module not available",
            )
        
        telemetry_root = Path(root)
        
        try:
            report = run_health_checks(telemetry_root)
            return report.to_dict()
        except Exception as e:
            logger.error(f"Error running health checks: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Health check failed: {str(e)}",
            )

    @app.get("/api/telemetry/health/trends", tags=["Phase 16H"])
    async def telemetry_health_trends_api(
        days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
        snapshots_path: str = Query(
            "logs/telemetry_health_snapshots.jsonl",
            description="Path to snapshots file"
        ),
    ):
        """Get telemetry health trends over time (Phase 16H)."""
        try:
            from src.execution.telemetry_health_trends import (
                load_snapshots,
                compute_rollup,
                detect_degradation,
            )
            from datetime import datetime, timedelta, timezone
            
            path = Path(snapshots_path)
            
            # Load snapshots for requested period
            since_ts = datetime.now(timezone.utc) - timedelta(days=days)
            snapshots = load_snapshots(path, since_ts=since_ts)
            
            if not snapshots:
                return {
                    "period_days": days,
                    "snapshots_found": 0,
                    "message": "No health snapshots found for requested period",
                    "hint": "Run 'python scripts/telemetry_health_snapshot.py' to start collecting data",
                }
            
            # Compute overall rollup
            rollup = compute_rollup(snapshots)
            
            # Compute rollups for different time windows
            now = datetime.now(timezone.utc)
            last_24h = [s for s in snapshots if s.ts_utc >= now - timedelta(hours=24)]
            last_7d = [s for s in snapshots if s.ts_utc >= now - timedelta(days=7)]
            
            rollup_24h = compute_rollup(last_24h) if last_24h else None
            rollup_7d = compute_rollup(last_7d) if last_7d else None
            
            # Detect degradation
            degradation = detect_degradation(snapshots, window_size=min(10, len(snapshots)))
            
            # Build time series (simplified: just timestamps + severity)
            time_series = [
                {
                    "ts": s.ts_utc.isoformat(),
                    "severity": s.severity,
                    "disk_mb": s.disk_usage_mb,
                    "parse_error_rate": s.parse_error_rate,
                }
                for s in snapshots
            ]
            
            return {
                "period_days": days,
                "snapshots_found": len(snapshots),
                "period_start": rollup.period_start.isoformat(),
                "period_end": rollup.period_end.isoformat(),
                "overall": {
                    "worst_severity": rollup.worst_severity,
                    "ok_count": rollup.ok_count,
                    "warn_count": rollup.warn_count,
                    "critical_count": rollup.critical_count,
                    "disk_mb": {
                        "min": rollup.disk_min,
                        "avg": rollup.disk_avg,
                        "max": rollup.disk_max,
                    },
                    "parse_error_rate": {
                        "min": rollup.parse_error_min,
                        "avg": rollup.parse_error_avg,
                        "max": rollup.parse_error_max,
                    },
                },
                "last_24h": {
                    "snapshots": len(last_24h),
                    "worst_severity": rollup_24h.worst_severity if rollup_24h else "unknown",
                    "warn_count": rollup_24h.warn_count if rollup_24h else 0,
                    "critical_count": rollup_24h.critical_count if rollup_24h else 0,
                } if last_24h else None,
                "last_7d": {
                    "snapshots": len(last_7d),
                    "worst_severity": rollup_7d.worst_severity if rollup_7d else "unknown",
                    "warn_count": rollup_7d.warn_count if rollup_7d else 0,
                    "critical_count": rollup_7d.critical_count if rollup_7d else 0,
                } if last_7d else None,
                "degradation": degradation,
                "time_series": time_series,
            }
        
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="Telemetry health trends module not available",
            )
        except Exception as e:
            logger.error(f"Error loading health trends: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load trends: {str(e)}",
            )

    @app.get("/api/telemetry/alerts/latest", tags=["Phase 16I"])
    async def telemetry_alerts_latest_api(
        limit: int = Query(50, ge=1, le=500, description="Maximum alerts to return"),
        severity: Optional[str] = Query(None, description="Filter by severity (info/warn/critical)"),
    ):
        """Get latest alerts (Phase 16I)."""
        try:
            from src.execution.alerting.persistence import get_global_alert_store
            
            store = get_global_alert_store()
            
            if severity:
                alerts = store.get_by_severity(severity, limit=limit)
            else:
                alerts = store.get_latest(limit=limit)
            
            return {
                "alerts": [a.to_dict() for a in alerts],
                "count": len(alerts),
                "severity_filter": severity,
            }
        
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="Telemetry alerting module not available",
            )
        except Exception as e:
            logger.error(f"Error loading alerts: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load alerts: {str(e)}",
            )

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
