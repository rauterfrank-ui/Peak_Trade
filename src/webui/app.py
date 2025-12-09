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
