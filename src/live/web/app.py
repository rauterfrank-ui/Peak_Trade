# src/live/web/app.py
"""
Peak_Trade: Web UI Application (Phase 67)
==========================================

FastAPI-basierte Web-Anwendung für das Monitoring von Shadow-/Paper-Runs.

Features:
- REST API für Run-Listen, Snapshots, Tail-Events, Alerts
- Einfaches HTML-Dashboard
- Auto-Refresh im Browser

WICHTIG: Die Web-UI ist read-only und trifft keine Trading-Entscheidungen.

Example:
    >>> from src.live.web.app import create_app
    >>> app = create_app()
    >>> # Start with: uvicorn src.live.web.app:app --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from .api_v0 import build_api_v0_router
from .metrics_prom import instrument_app, maybe_register_metrics
from .models_v0 import (
    AlertResponse,
    HealthResponse,
    RunMetadataResponse,
    RunSnapshotResponse,
    TailRowResponse,
)

from ..monitoring import (
    list_runs as monitoring_list_runs,
    get_run_snapshot,
    tail_events,
    RunNotFoundError,
    RunSnapshot,
)
from ..run_logging import load_run_events, load_run_metadata

logger = logging.getLogger(__name__)

DASHBOARD_API_CONTRACT_VERSION = "v0.1B"


# =============================================================================
# Config
# =============================================================================


@dataclass
class WebUIConfig:
    """
    Konfiguration für die Web-UI.

    Attributes:
        enabled: Web-UI aktiviert
        host: Host für den Server
        port: Port für den Server
        base_runs_dir: Basis-Verzeichnis für Runs
        auto_refresh_seconds: Auto-Refresh-Intervall im Browser
    """

    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 8000
    base_runs_dir: str = "live_runs"
    auto_refresh_seconds: int = 5


def load_web_ui_config(cfg: Any) -> WebUIConfig:
    """
    Lädt WebUIConfig aus PeakConfig.

    Args:
        cfg: PeakConfig-Objekt

    Returns:
        WebUIConfig mit Werten aus Config
    """
    return WebUIConfig(
        enabled=cfg.get("web_ui.enabled", True),
        host=cfg.get("web_ui.host", "127.0.0.1"),
        port=cfg.get("web_ui.port", 8000),
        base_runs_dir=cfg.get("shadow_paper_logging.base_dir", "live_runs"),
        auto_refresh_seconds=cfg.get("web_ui.auto_refresh_seconds", 5),
    )


# =============================================================================
# Helper Functions
# =============================================================================


def load_alerts_from_file(run_dir: Path, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Lädt Alerts aus alerts.jsonl Datei.

    Args:
        run_dir: Run-Verzeichnis
        limit: Maximale Anzahl Alerts

    Returns:
        Liste von Alert-Dictionaries
    """
    alerts_path = run_dir / "alerts.jsonl"
    if not alerts_path.exists():
        return []

    alerts = []
    try:
        with open(alerts_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    alert = json.loads(line)
                    alerts.append(alert)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in alerts.jsonl: {line}")
                    continue

        # Neueste zuerst, dann limitieren
        alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return alerts[:limit]

    except Exception as e:
        logger.warning(f"Error loading alerts from {alerts_path}: {e}")
        return []


def _calculate_orders_count(events: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Berechnet Order-Statistiken aus Events.

    Args:
        events: Liste von Event-Dictionaries

    Returns:
        Dict mit total_orders, total_blocked_orders
    """
    total_orders = 0
    total_blocked_orders = 0

    for event in events:
        # Orders: Summe von orders_filled (oder orders_generated falls filled nicht vorhanden)
        orders_filled = event.get("orders_filled", 0) or 0
        orders_generated = event.get("orders_generated", 0) or 0
        # Verwende filled falls vorhanden, sonst generated
        orders_count = orders_filled if orders_filled > 0 else orders_generated
        total_orders += orders_count

        # Blocked orders
        orders_blocked = event.get("orders_blocked", 0) or 0
        total_blocked_orders += orders_blocked

    return {
        "total_orders": total_orders,
        "total_blocked_orders": total_blocked_orders,
    }


# =============================================================================
# HTML Templates
# =============================================================================


def _generate_dashboard_html(
    base_runs_dir: str,
    auto_refresh_seconds: int,
) -> str:
    """Generiert das Dashboard-HTML."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Peak_Trade Live Dashboard</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #1a1a2e;
            color: #eee;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 1px solid #333;
        }}
        h1 {{
            color: #00d4ff;
            font-size: 1.8em;
        }}
        .status {{
            font-size: 0.9em;
            color: #888;
        }}
        .status.connected {{
            color: #00ff88;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 20px;
        }}
        .panel {{
            background: #16213e;
            border-radius: 8px;
            padding: 20px;
            border: 1px solid #333;
        }}
        .panel h2 {{
            font-size: 1.1em;
            color: #00d4ff;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #333;
        }}
        .run-list {{
            list-style: none;
        }}
        .run-list li {{
            padding: 10px;
            margin-bottom: 8px;
            background: #1a1a2e;
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .run-list li:hover {{
            background: #2a2a4e;
        }}
        .run-list li.active {{
            background: #0e4429;
            border-left: 3px solid #00ff88;
        }}
        .run-id {{
            font-family: monospace;
            font-size: 0.85em;
            color: #00d4ff;
        }}
        .run-meta {{
            font-size: 0.75em;
            color: #888;
            margin-top: 4px;
        }}
        .detail-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .metric {{
            background: #1a1a2e;
            padding: 15px;
            border-radius: 6px;
        }}
        .metric-label {{
            font-size: 0.75em;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .metric-value {{
            font-size: 1.5em;
            font-weight: bold;
            margin-top: 5px;
        }}
        .metric-value.positive {{
            color: #00ff88;
        }}
        .metric-value.negative {{
            color: #ff4757;
        }}
        .metric-value.warning {{
            color: #ffa502;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85em;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #333;
        }}
        th {{
            color: #888;
            font-weight: normal;
            text-transform: uppercase;
            font-size: 0.75em;
            letter-spacing: 1px;
        }}
        .risk-ok {{
            color: #00ff88;
        }}
        .risk-blocked {{
            color: #ff4757;
            font-weight: bold;
        }}
        .alert-panel {{
            margin-top: 20px;
        }}
        .alert {{
            padding: 10px 15px;
            margin-bottom: 8px;
            border-radius: 4px;
            font-size: 0.85em;
        }}
        .alert.critical {{
            background: rgba(255, 71, 87, 0.2);
            border-left: 3px solid #ff4757;
        }}
        .alert.warning {{
            background: rgba(255, 165, 2, 0.2);
            border-left: 3px solid #ffa502;
        }}
        .alert.info {{
            background: rgba(0, 212, 255, 0.2);
            border-left: 3px solid #00d4ff;
        }}
        .no-data {{
            text-align: center;
            padding: 40px;
            color: #666;
        }}
        .loading {{
            text-align: center;
            padding: 20px;
            color: #00d4ff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Peak_Trade Live Dashboard</h1>
            <div class="status" id="status">Connecting...</div>
        </header>

        <div class="grid">
            <div class="panel">
                <h2>Runs</h2>
                <ul class="run-list" id="run-list">
                    <li class="loading">Loading runs...</li>
                </ul>
            </div>

            <div class="panel">
                <h2>Run Details</h2>
                <div id="run-details">
                    <div class="no-data">Select a run from the list</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const BASE_URL = window.location.origin;
        const REFRESH_INTERVAL = {auto_refresh_seconds * 1000};
        let selectedRunId = null;
        let refreshTimer = null;

        async function fetchJSON(url) {{
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
            return response.json();
        }}

        async function loadRuns() {{
            try {{
                const runs = await fetchJSON(`${{BASE_URL}}/runs`);
                const list = document.getElementById('run-list');

                if (runs.length === 0) {{
                    list.innerHTML = '<li class="no-data">No runs found</li>';
                    return;
                }}

                list.innerHTML = runs.map(run => `
                    <li onclick="selectRun('${{run.run_id}}')"
                        class="${{selectedRunId === run.run_id ? 'active' : ''}}"
                        id="run-${{run.run_id}}">
                        <div class="run-id">${{run.run_id}}</div>
                        <div class="run-meta">${{run.strategy_name}} | ${{run.symbol}} | ${{run.timeframe}}</div>
                    </li>
                `).join('');

                document.getElementById('status').textContent = `${{runs.length}} runs | Auto-refresh: ${{REFRESH_INTERVAL/1000}}s`;
                document.getElementById('status').className = 'status connected';

                // Auto-select first run if none selected
                if (!selectedRunId && runs.length > 0) {{
                    selectRun(runs[0].run_id);
                }}
            }} catch (e) {{
                console.error('Error loading runs:', e);
                document.getElementById('status').textContent = 'Connection error';
                document.getElementById('status').className = 'status';
            }}
        }}

        async function selectRun(runId) {{
            selectedRunId = runId;

            // Update active state
            document.querySelectorAll('.run-list li').forEach(li => {{
                li.classList.remove('active');
            }});
            const activeLi = document.getElementById(`run-${{runId}}`);
            if (activeLi) activeLi.classList.add('active');

            await loadRunDetails(runId);
        }}

        async function loadRunDetails(runId) {{
            const detailsDiv = document.getElementById('run-details');
            detailsDiv.innerHTML = '<div class="loading">Loading...</div>';

            try {{
                const [snapshot, tail, alerts] = await Promise.all([
                    fetchJSON(`${{BASE_URL}}/runs/${{runId}}/snapshot`),
                    fetchJSON(`${{BASE_URL}}/runs/${{runId}}/tail?limit=10`),
                    fetchJSON(`${{BASE_URL}}/runs/${{runId}}/alerts?limit=5`).catch(() => [])
                ]);

                const pnlClass = (snapshot.realized_pnl || 0) >= 0 ? 'positive' : 'negative';
                const blockedClass = snapshot.total_blocked_orders > 0 ? 'warning' : '';

                let html = `
                    <div class="detail-grid">
                        <div class="metric">
                            <div class="metric-label">Equity</div>
                            <div class="metric-value">${{formatNumber(snapshot.equity)}}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Realized PnL</div>
                            <div class="metric-value ${{pnlClass}}">${{formatPnL(snapshot.realized_pnl)}}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Position</div>
                            <div class="metric-value">${{formatNumber(snapshot.position_size, 6)}}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Steps</div>
                            <div class="metric-value">${{snapshot.total_steps}}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Orders</div>
                            <div class="metric-value">${{snapshot.total_orders}}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Blocked</div>
                            <div class="metric-value ${{blockedClass}}">${{snapshot.total_blocked_orders}}</div>
                        </div>
                    </div>
                `;

                // Alerts
                if (alerts.length > 0) {{
                    html += `
                        <div class="alert-panel">
                            <h3 style="color: #ffa502; margin-bottom: 10px;">Recent Alerts</h3>
                            ${{alerts.map(a => `
                                <div class="alert ${{a.severity}}">
                                    <strong>[${{a.severity.toUpperCase()}}]</strong> ${{a.message}}
                                </div>
                            `).join('')}}
                        </div>
                    `;
                }}

                // Tail table
                html += `
                    <h3 style="margin: 20px 0 10px; color: #00d4ff;">Recent Events</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Equity</th>
                                <th>R. PnL</th>
                                <th>Position</th>
                                <th>Orders</th>
                                <th>Risk</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${{tail.map(row => `
                                <tr>
                                    <td>${{formatTime(row.ts_bar)}}</td>
                                    <td>${{formatNumber(row.equity)}}</td>
                                    <td>${{formatNumber(row.realized_pnl)}}</td>
                                    <td>${{formatNumber(row.position_size, 4)}}</td>
                                    <td>${{row.orders_count}}</td>
                                    <td class="${{row.risk_allowed ? 'risk-ok' : 'risk-blocked'}}">
                                        ${{row.risk_allowed ? 'OK' : 'BLOCKED'}}
                                    </td>
                                </tr>
                            `).join('')}}
                        </tbody>
                    </table>
                `;

                detailsDiv.innerHTML = html;

            }} catch (e) {{
                console.error('Error loading run details:', e);
                detailsDiv.innerHTML = '<div class="no-data">Error loading run details</div>';
            }}
        }}

        function formatNumber(val, decimals = 2) {{
            if (val === null || val === undefined) return 'N/A';
            return Number(val).toLocaleString('en-US', {{ minimumFractionDigits: decimals, maximumFractionDigits: decimals }});
        }}

        function formatPnL(val) {{
            if (val === null || val === undefined) return 'N/A';
            const sign = val >= 0 ? '+' : '';
            return sign + formatNumber(val);
        }}

        function formatTime(ts) {{
            if (!ts) return 'N/A';
            const date = new Date(ts);
            return date.toLocaleTimeString();
        }}

        async function refresh() {{
            await loadRuns();
            if (selectedRunId) {{
                await loadRunDetails(selectedRunId);
            }}
        }}

        // Initial load
        refresh();

        // Auto-refresh
        refreshTimer = setInterval(refresh, REFRESH_INTERVAL);
    </script>
</body>
</html>
"""


# =============================================================================
# App Factory
# =============================================================================


def create_app(
    config: Optional[WebUIConfig] = None,
    base_runs_dir: Optional[str] = None,
) -> FastAPI:
    """
    Erstellt die FastAPI-Anwendung.

    Args:
        config: Optional WebUIConfig
        base_runs_dir: Optional Override für Runs-Verzeichnis

    Returns:
        FastAPI app instance
    """
    cfg = config or WebUIConfig()
    runs_dir = Path(base_runs_dir or cfg.base_runs_dir)

    app = FastAPI(
        title="Peak_Trade Live Dashboard",
        description="Web UI for monitoring Shadow/Paper Runs",
        version="0.1.0",
    )

    # =============================================================================
    # Safety: hard-reject mutating methods on API paths (watch-only/read-only)
    # =============================================================================

    @app.middleware("http")
    async def _reject_mutating_api_methods(request: Request, call_next):
        if request.url.path.startswith("/api/") and request.method not in {
            "GET",
            "HEAD",
            "OPTIONS",
        }:
            return PlainTextResponse("method_not_allowed: read-only api", status_code=405)
        return await call_next(request)

    # =============================================================================
    # Observability (optional): Prometheus instrumentation + /metrics (watch-only)
    # =============================================================================
    # NOTE: fail-open when prometheus_client is not installed; only enabled via env flag.
    instrument_app(app)
    maybe_register_metrics(app)

    # =============================================================================
    # API Endpoints
    # =============================================================================

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health-Check-Endpoint."""
        return HealthResponse(
            status="ok",
            contract_version=DASHBOARD_API_CONTRACT_VERSION,
            server_time=datetime.now(timezone.utc).isoformat(),
        )

    @app.get("/runs", response_model=List[RunMetadataResponse])
    async def get_runs():
        """Listet alle verfügbaren Runs."""
        try:
            snapshots = monitoring_list_runs(base_dir=runs_dir, include_inactive=True)
            result: List[RunMetadataResponse] = []

            for snapshot in snapshots[:50]:  # Max 50 Runs
                try:
                    result.append(
                        RunMetadataResponse(
                            run_id=snapshot.run_id,
                            mode=snapshot.mode,
                            strategy_name=snapshot.strategy or "",
                            symbol=snapshot.symbol or "",
                            timeframe=snapshot.timeframe or "",
                            started_at=(
                                snapshot.started_at.isoformat() if snapshot.started_at else None
                            ),
                            ended_at=snapshot.ended_at.isoformat() if snapshot.ended_at else None,
                            is_active=bool(snapshot.is_active),
                            last_event_time=(
                                snapshot.last_event_time.isoformat()
                                if snapshot.last_event_time
                                else None
                            ),
                        )
                    )
                except Exception as e:
                    logger.warning(f"Error converting snapshot {snapshot.run_id}: {e}")
                    continue

            return result
        except Exception as e:
            logger.error(f"Error listing runs: {e}")
            return []

    @app.get("/runs/{run_id}/snapshot", response_model=RunSnapshotResponse)
    async def get_run_snapshot_endpoint(run_id: str):
        """Lädt Snapshot für einen Run."""
        try:
            snapshot = get_run_snapshot(run_id, base_dir=runs_dir)

            # Events laden für Order-Statistiken
            events = tail_events(run_id, limit=10000, base_dir=runs_dir)
            order_stats = _calculate_orders_count(events)

            return RunSnapshotResponse(
                run_id=snapshot.run_id,
                mode=snapshot.mode,
                strategy_name=snapshot.strategy or "",
                symbol=snapshot.symbol or "",
                timeframe=snapshot.timeframe or "",
                total_steps=snapshot.num_events,
                total_orders=order_stats["total_orders"],
                total_blocked_orders=order_stats["total_blocked_orders"],
                equity=snapshot.equity,
                realized_pnl=snapshot.pnl,
                unrealized_pnl=snapshot.unrealized_pnl,
                drawdown=snapshot.drawdown,
                last_event_time=(
                    snapshot.last_event_time.isoformat() if snapshot.last_event_time else None
                ),
            )
        except RunNotFoundError:
            raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
        except Exception as e:
            logger.error(f"Error loading snapshot for {run_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/runs/{run_id}/tail", response_model=List[TailRowResponse])
    async def get_run_tail(
        run_id: str,
        limit: int = Query(default=50, ge=1, le=500),
    ):
        """Lädt Tail-Events für einen Run."""
        try:
            events = tail_events(run_id, limit=limit, base_dir=runs_dir)
            result: List[TailRowResponse] = []

            for event in events:
                # Orders count berechnen (verwende filled falls vorhanden, sonst generated)
                orders_filled = event.get("orders_filled", 0) or 0
                orders_generated = event.get("orders_generated", 0) or 0
                orders_count = orders_filled if orders_filled > 0 else orders_generated

                result.append(
                    TailRowResponse(
                        ts_bar=event.get("ts_bar"),
                        equity=event.get("equity"),
                        realized_pnl=event.get("realized_pnl"),
                        unrealized_pnl=event.get("unrealized_pnl"),
                        position_size=event.get("position_size"),
                        orders_count=orders_count,
                        risk_allowed=event.get("risk_allowed", True),
                        risk_reasons=event.get("risk_reasons", "") or "",
                    )
                )

            return result
        except RunNotFoundError:
            raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
        except Exception as e:
            logger.error(f"Error loading tail for {run_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/runs/{run_id}/alerts", response_model=List[AlertResponse])
    async def get_run_alerts(
        run_id: str,
        limit: int = Query(default=20, ge=1, le=100),
    ):
        """Lädt Alerts für einen Run."""
        run_dir = runs_dir / run_id

        if not run_dir.exists():
            raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

        try:
            alerts = load_alerts_from_file(run_dir, limit=limit)
            result: List[AlertResponse] = []

            for alert in alerts:
                result.append(
                    AlertResponse(
                        rule_id=alert.get("rule_id", ""),
                        severity=alert.get("severity", "info"),
                        message=alert.get("message", ""),
                        run_id=alert.get("run_id", run_id),
                        timestamp=alert.get("timestamp", ""),
                    )
                )

            return result
        except Exception as e:
            logger.warning(f"Error loading alerts for {run_id}: {e}")
            return []

    # =============================================================================
    # HTML Dashboard
    # =============================================================================

    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        """HTML Dashboard."""
        return _generate_dashboard_html(
            base_runs_dir=str(runs_dir),
            auto_refresh_seconds=cfg.auto_refresh_seconds,
        )

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard_alias():
        """Alias für Dashboard."""
        return await dashboard()

    # =============================================================================
    # Watch-only UI v0.1B (HTML + optional JS polling/backoff, read-only)
    # =============================================================================

    def _html_escape(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def _watch_only_banner() -> str:
        return (
            "<div class='watch-only-banner'>"
            "<strong>WATCH-ONLY</strong> — Read-only Observability UI. No actions. No secrets."
            "</div>"
        )

    def _base_css() -> str:
        return """
    * { box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; background: #0b1220; color: #e5e7eb; margin: 0; }
    a { color: #60a5fa; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .wrap { max-width: 1200px; margin: 0 auto; padding: 18px; }
    .watch-only-banner { background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.35); padding: 10px 12px; border-radius: 10px; margin-bottom: 14px; position: sticky; top: 0; backdrop-filter: blur(6px); }
    .header { display:flex; justify-content: space-between; align-items: baseline; gap: 12px; margin-bottom: 14px; }
    .title { font-size: 20px; font-weight: 700; color: #93c5fd; }
    .sub { font-size: 12px; color: #9ca3af; }
    .grid-2 { display: grid; grid-template-columns: 1fr 2fr; gap: 14px; }
    .grid-4 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    .card { background: #0f172a; border: 1px solid rgba(148,163,184,0.18); border-radius: 12px; padding: 14px; }
    .card h2 { margin: 0 0 10px 0; font-size: 14px; color: #e5e7eb; }
    .row { display:flex; justify-content: space-between; gap: 10px; margin: 6px 0; }
    .k { color: #9ca3af; font-size: 12px; }
    .v { font-size: 12px; }
    .badge { display: inline-flex; align-items: center; gap: 6px; padding: 2px 8px; border-radius: 999px; font-size: 12px; border: 1px solid rgba(148,163,184,0.25); }
    .ok { background: rgba(16,185,129,0.12); border-color: rgba(16,185,129,0.35); }
    .degraded { background: rgba(239,68,68,0.12); border-color: rgba(239,68,68,0.35); }
    .muted { color: #9ca3af; }
    .pill { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 11px; color: #93c5fd; }
    .loading { color: #93c5fd; }
    .error { color: #fca5a5; }
    table { width: 100%; border-collapse: collapse; font-size: 12px; }
    th, td { padding: 8px 8px; border-bottom: 1px solid rgba(148,163,184,0.18); text-align: left; vertical-align: top; }
    th { color: #9ca3af; font-weight: 600; }
"""

    def _polling_js(poll_ms: int, max_backoff_ms: int) -> str:
        # Small helper used by both pages; no secrets, no mutations.
        return f"""
  <script>
  (() => {{
    const POLL_MS = {poll_ms};
    const MAX_BACKOFF_MS = {max_backoff_ms};
    let nextDelayMs = POLL_MS;

    function nowIso() {{ return new Date().toISOString(); }}
    function esc(s) {{
      return String(s).replace(/[&<>\"']/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}}[c]));
    }}

    async function fetchJson(path, timeoutMs = 2500) {{
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), timeoutMs);
      try {{
        const t0 = performance.now();
        const res = await fetch(path, {{ signal: controller.signal, headers: {{ "Accept": "application/json" }} }});
        const latencyMs = Math.round(performance.now() - t0);
        if (!res.ok) {{
          const err = new Error(`HTTP ${{res.status}}`);
          err.status = res.status;
          err.latencyMs = latencyMs;
          throw err;
        }}
        return {{ data: await res.json(), latencyMs }};
      }} finally {{
        clearTimeout(timeout);
      }}
    }}

    function schedule(nextFn, hadError) {{
      nextDelayMs = hadError ? Math.min(nextDelayMs * 2, MAX_BACKOFF_MS) : POLL_MS;
      setTimeout(nextFn, nextDelayMs);
    }}

    window.__PT_WATCH_ONLY__ = {{ nowIso, esc, fetchJson, schedule }};
  }})();
  </script>
"""

    @app.get("/watch", response_class=HTMLResponse)
    async def watch_only_overview():
        # Server-rendered initial state (no JS required)
        health = await api_v0_health()
        runs = await api_v0_runs()

        rows_html = ""
        active_strategy = "unknown"
        if runs:
            active = next((r for r in runs if r.is_active is True), runs[0])
            active_strategy = active.strategy_name or "unknown"

            for r in runs:
                href = f"/watch/runs/{_html_escape(r.run_id)}"
                last = _html_escape(r.last_event_time) if r.last_event_time else "—"
                status_badge = (
                    "<span class='badge ok'>active</span>"
                    if r.is_active is True
                    else "<span class='badge muted'>inactive</span>"
                )
                rows_html += (
                    "<tr>"
                    f"<td><a class='pill' href='{href}'>{_html_escape(r.run_id)}</a></td>"
                    f"<td>{status_badge}</td>"
                    f"<td>{last}</td>"
                    f"<td>{_html_escape(r.strategy_name or '—')}</td>"
                    f"<td>{_html_escape(r.symbol or '—')}</td>"
                    "</tr>"
                )
        else:
            rows_html = "<tr><td colspan='5' class='muted'>No runs found</td></tr>"

        health_badge = (
            "<span class='badge ok'>ok</span>"
            if health.status == "ok"
            else "<span class='badge degraded'>degraded</span>"
        )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Peak_Trade Dashboard v0.1B — Watch-Only</title>
  <style>{_base_css()}</style>
</head>
<body>
  <div class="wrap">
    {_watch_only_banner()}
    <div class="header">
      <div>
        <div class="title">Peak_Trade Dashboard v0.1B — Watch-Only</div>
        <div class="sub">Overview · read-only · polling with backoff</div>
      </div>
      <div class="sub" id="last-updated">Last updated: {datetime.now(timezone.utc).isoformat()}</div>
    </div>

    <div class="grid-2">
      <div class="card">
        <h2>System Health</h2>
        <div class="row"><span class="k">Status</span><span class="v" id="health-status">{health_badge}</span></div>
        <div class="row"><span class="k">Latency</span><span class="v" id="health-latency">—</span></div>
        <div class="row"><span class="k">Contract</span><span class="v pill" id="health-contract">{_html_escape(health.contract_version)}</span></div>
        <div class="row"><span class="k">Server time</span><span class="v" id="health-server-time">{_html_escape(health.server_time)}</span></div>
        <div class="sub" id="health-error" style="display:none;"></div>
      </div>

      <div class="card">
        <h2>Live Sessions (Runs)</h2>
        <table>
          <thead>
            <tr><th>Run</th><th>Status</th><th>Last update</th><th>Strategy</th><th>Symbol</th></tr>
          </thead>
          <tbody id="runs-tbody">{rows_html}</tbody>
        </table>
        <div class="sub" style="margin-top:10px;">
          Active strategy: <span id="active-strategy" class="pill">{_html_escape(active_strategy)}</span>
        </div>
        <div class="sub error" id="runs-error" style="display:none;"></div>
      </div>
    </div>
  </div>

{_polling_js(poll_ms=3000, max_backoff_ms=30000)}
  <script>
  (() => {{
    const helper = window.__PT_WATCH_ONLY__;
    async function tick() {{
      let hadError = false;
      document.getElementById("last-updated").textContent = `Last updated: ${{helper.nowIso()}}`;

      // Health
      try {{
        const r = await helper.fetchJson("/api/v0/health");
        const h = r.data;
        const badge = (h.status === "ok") ? "<span class='badge ok'>ok</span>" : "<span class='badge degraded'>degraded</span>";
        document.getElementById("health-status").innerHTML = badge;
        document.getElementById("health-latency").textContent = `${{r.latencyMs}} ms`;
        document.getElementById("health-contract").textContent = h.contract_version;
        document.getElementById("health-server-time").textContent = h.server_time;
        document.getElementById("health-error").style.display = "none";
      }} catch (e) {{
        hadError = true;
        const el = document.getElementById("health-error");
        el.textContent = `Health error: ${{e.message || "unknown"}}`;
        el.className = "sub error";
        el.style.display = "block";
      }}

      // Runs
      try {{
        const r = await helper.fetchJson("/api/v0/runs");
        const runs = Array.isArray(r.data) ? r.data : [];
        const tbody = document.getElementById("runs-tbody");
        if (!runs.length) {{
          tbody.innerHTML = "<tr><td colspan='5' class='muted'>No runs found</td></tr>";
          document.getElementById("active-strategy").textContent = "unknown";
        }} else {{
          const active = runs.find(x => x.is_active === true) || runs[0];
          document.getElementById("active-strategy").textContent = active.strategy_name || "unknown";
          tbody.innerHTML = runs.map(run => {{
            const last = run.last_event_time ? helper.esc(run.last_event_time) : "—";
            const badge = (run.is_active === true) ? "<span class='badge ok'>active</span>" : "<span class='badge muted'>inactive</span>";
            const href = `/watch/runs/${{encodeURIComponent(run.run_id)}}`;
            return `<tr>
              <td><a class='pill' href='${{href}}'>${{helper.esc(run.run_id)}}</a></td>
              <td>${{badge}}</td>
              <td>${{last}}</td>
              <td>${{helper.esc(run.strategy_name || "—")}}</td>
              <td>${{helper.esc(run.symbol || "—")}}</td>
            </tr>`;
          }}).join("");
        }}
        document.getElementById("runs-error").style.display = "none";
      }} catch (e) {{
        hadError = true;
        const el = document.getElementById("runs-error");
        el.textContent = `Runs error: ${{e.message || "unknown"}}`;
        el.style.display = "block";
      }}

      helper.schedule(tick, hadError);
    }}

    tick();
  }})();
  </script>
</body>
</html>"""

        return HTMLResponse(content=html, headers={"Cache-Control": "no-store"})

    @app.get("/watch/runs/{run_id}", response_class=HTMLResponse)
    async def watch_only_run_detail(run_id: str):
        # Validate existence early
        _run_dir_for(run_id)

        # Server-rendered initial state per panel (no JS required)
        detail_error = None
        signals_error = None
        positions_error = None
        orders_error = None

        try:
            detail = await api_v0_run_detail(run_id)
        except Exception as e:
            detail = None
            detail_error = str(e)

        try:
            signals = await api_v0b_run_signals(run_id, limit=50)
        except Exception as e:
            signals = SignalsResponseV0B(
                run_id=run_id, asof=datetime.now(timezone.utc).isoformat(), count=0, items=[]
            )
            signals_error = str(e)

        try:
            positions = await api_v0b_run_positions(run_id, limit=50)
        except Exception as e:
            positions = PositionsResponseV0B(
                run_id=run_id, asof=datetime.now(timezone.utc).isoformat(), count=0, items=[]
            )
            positions_error = str(e)

        try:
            orders = await api_v0b_run_orders(run_id, limit=200, only_nonzero=True)
        except Exception as e:
            orders = OrdersResponseV0B(
                run_id=run_id, asof=datetime.now(timezone.utc).isoformat(), count=0, items=[]
            )
            orders_error = str(e)

        def _rows_signals() -> str:
            if signals_error:
                return f"<tr><td colspan='4' class='error'>Signals error: {_html_escape(signals_error)}</td></tr>"
            if not signals.items:
                return "<tr><td colspan='4' class='muted'>Empty</td></tr>"
            return "".join(
                "<tr>"
                f"<td>{_html_escape(it.ts)}</td>"
                f"<td>{it.step if it.step is not None else '—'}</td>"
                f"<td>{it.signal if it.signal is not None else '—'}</td>"
                f"<td>{it.signal_changed if it.signal_changed is not None else '—'}</td>"
                "</tr>"
                for it in signals.items
            )

        def _rows_positions() -> str:
            if positions_error:
                return f"<tr><td colspan='4' class='error'>Positions error: {_html_escape(positions_error)}</td></tr>"
            if not positions.items:
                return "<tr><td colspan='4' class='muted'>Empty</td></tr>"
            return "".join(
                "<tr>"
                f"<td>{_html_escape(it.ts)}</td>"
                f"<td>{it.step if it.step is not None else '—'}</td>"
                f"<td>{it.position_size if it.position_size is not None else '—'}</td>"
                f"<td>{it.equity if it.equity is not None else '—'}</td>"
                "</tr>"
                for it in positions.items
            )

        def _rows_orders() -> str:
            if orders_error:
                return f"<tr><td colspan='7' class='error'>Orders error: {_html_escape(orders_error)}</td></tr>"
            if not orders.items:
                return "<tr><td colspan='7' class='muted'>Empty</td></tr>"
            tail = orders.items[-50:] if len(orders.items) > 50 else orders.items
            return "".join(
                "<tr>"
                f"<td>{_html_escape(it.ts)}</td>"
                f"<td>{it.step if it.step is not None else '—'}</td>"
                f"<td>{it.orders_generated if it.orders_generated is not None else '—'}</td>"
                f"<td>{it.orders_filled if it.orders_filled is not None else '—'}</td>"
                f"<td>{it.orders_rejected if it.orders_rejected is not None else '—'}</td>"
                f"<td>{it.orders_blocked if it.orders_blocked is not None else '—'}</td>"
                f"<td>{'BLOCKED' if it.risk_allowed is False else ('OK' if it.risk_allowed is True else '—')}</td>"
                "</tr>"
                for it in tail
            )

        meta_html = "<div class='muted'>Meta unavailable</div>"
        if detail_error:
            meta_html = f"<div class='error'>Detail error: {_html_escape(detail_error)}</div>"
        elif detail is not None:
            meta = detail.meta
            snap = detail.snapshot
            meta_html = (
                "<div class='row'><span class='k'>Strategy</span><span class='v pill'>"
                f"{_html_escape(meta.strategy_name or '—')}</span></div>"
                "<div class='row'><span class='k'>Symbol</span><span class='v pill'>"
                f"{_html_escape(meta.symbol or '—')}</span></div>"
                "<div class='row'><span class='k'>Mode</span><span class='v pill'>"
                f"{_html_escape(meta.mode or '—')}</span></div>"
                "<div class='row'><span class='k'>Started</span><span class='v'>"
                f"{_html_escape(meta.started_at or '—')}</span></div>"
                "<div class='row'><span class='k'>Last event</span><span class='v'>"
                f"{_html_escape(snap.last_event_time or '—')}</span></div>"
            )

        safe_run = _html_escape(run_id)
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Peak_Trade Watch-Only — {safe_run}</title>
  <style>{_base_css()}</style>
</head>
<body>
  <div class="wrap">
    {_watch_only_banner()}
    <div class="header">
      <div>
        <div class="title">Session Detail (Run): <span class="pill" id="run-id">{safe_run}</span></div>
        <div class="sub"><a href="/watch">← Back to Overview</a> · read-only · panel-level states</div>
      </div>
      <div class="sub" id="last-updated">Last updated: {datetime.now(timezone.utc).isoformat()}</div>
    </div>

    <div class="grid-4">
      <div class="card">
        <h2>Signals</h2>
        <table>
          <thead><tr><th>ts</th><th>step</th><th>signal</th><th>changed</th></tr></thead>
          <tbody id="signals-tbody">{_rows_signals()}</tbody>
        </table>
        <div class="sub error" id="signals-error" style="display:none;"></div>
      </div>

      <div class="card">
        <h2>Positions</h2>
        <table>
          <thead><tr><th>ts</th><th>step</th><th>position</th><th>equity</th></tr></thead>
          <tbody id="positions-tbody">{_rows_positions()}</tbody>
        </table>
        <div class="sub error" id="positions-error" style="display:none;"></div>
      </div>

      <div class="card">
        <h2>Orders (read-only counters)</h2>
        <table>
          <thead><tr><th>ts</th><th>step</th><th>gen</th><th>fill</th><th>rej</th><th>blk</th><th>risk</th></tr></thead>
          <tbody id="orders-tbody">{_rows_orders()}</tbody>
        </table>
        <div class="sub error" id="orders-error" style="display:none;"></div>
      </div>

      <div class="card">
        <h2>Session Meta (contracted)</h2>
        <div id="meta-wrap">{meta_html}</div>
      </div>

      <div class="card">
        <h2>Logs / Events (v0.2)</h2>
        <div class="sub" style="margin-bottom:8px;">
          <button id="logs-toggle" class="pill" style="cursor:pointer;">Pause</button>
          <span class="muted" style="margin-left:8px;">source: <span class="pill">/api/v0/runs/{safe_run}/events</span></span>
        </div>
        <pre id="logs-pre" style="max-height:260px; overflow:auto; background:#050a14; border:1px solid #1f2937; padding:10px; border-radius:8px; white-space:pre-wrap;">(connecting…)</pre>
        <div class="sub error" id="logs-error" style="display:none;"></div>
      </div>
    </div>
  </div>

{_polling_js(poll_ms=3000, max_backoff_ms=30000)}
  <script>
  (() => {{
    const helper = window.__PT_WATCH_ONLY__;
    const RUN_ID = document.getElementById("run-id").textContent;
    let logsPaused = false;
    let logsSince = 0;
    let logsEs = null;

    function logsSetPaused(next) {{
      logsPaused = !!next;
      const btn = document.getElementById("logs-toggle");
      btn.textContent = logsPaused ? "Resume" : "Pause";
    }}

    function logsAppend(line) {{
      const pre = document.getElementById("logs-pre");
      const txt = pre.textContent === "(connecting…)" ? "" : pre.textContent;
      const next = (txt + line + "\n").split("\n");
      const tail = next.slice(Math.max(0, next.length - 200));
      pre.textContent = tail.join("\n");
      pre.scrollTop = pre.scrollHeight;
    }}

    function logsShowError(msg) {{
      const el = document.getElementById("logs-error");
      el.textContent = msg;
      el.style.display = "block";
    }}

    function logsClearError() {{
      const el = document.getElementById("logs-error");
      el.style.display = "none";
    }}

    function logsStopSse() {{
      try {{
        if (logsEs) logsEs.close();
      }} catch (_) {{}}
      logsEs = null;
    }}

    function logsStartSseOrPoll() {{
      // Try SSE first (bounded by max_seconds). Fall back to polling on error.
      logsStopSse();
      logsClearError();
      const url = `/api/v0/runs/${{encodeURIComponent(RUN_ID)}}/events?sse=1&follow=1&since_seq=${{logsSince}}&max_seconds=30`;
      try {{
        logsEs = new EventSource(url);
        logsEs.addEventListener("pt_event", (ev) => {{
          if (logsPaused) return;
          try {{
            const item = JSON.parse(ev.data);
            if (typeof item.seq === "number") logsSince = item.seq + 1;
            logsAppend(`[${{item.ts}}] ${{item.level}} ${{item.component}}: ${{item.msg}}`);
          }} catch (e) {{
            logsShowError(`Logs parse error: ${{e.message || "unknown"}}`);
          }}
        }});
        logsEs.onerror = () => {{
          logsStopSse();
          logsShowError("SSE unavailable; falling back to polling.");
          logsPollTick();
        }};
      }} catch (e) {{
        logsShowError("SSE unavailable; falling back to polling.");
        logsPollTick();
      }}
    }}

    async function logsPollTick() {{
      if (logsPaused) {{
        helper.schedule(logsPollTick, false);
        return;
      }}
      let hadError = false;
      try {{
        const r = await helper.fetchJson(`/api/v0/runs/${{encodeURIComponent(RUN_ID)}}/events?since_seq=${{logsSince}}&limit=200`);
        const payload = r.data;
        const items = payload.items || [];
        if (items.length) {{
          for (const it of items) {{
            logsSince = (typeof it.seq === "number") ? (it.seq + 1) : logsSince;
            logsAppend(`[${{it.ts}}] ${{it.level}} ${{it.component}}: ${{it.msg}}`);
          }}
        }}
        logsClearError();
      }} catch (e) {{
        hadError = true;
        logsShowError(`Logs poll error: ${{e.message || "unknown"}}`);
      }}
      helper.schedule(logsPollTick, hadError);
    }}

    document.getElementById("logs-toggle").addEventListener("click", () => {{
      logsSetPaused(!logsPaused);
    }});
    logsSetPaused(false);
    logsStartSseOrPoll();

    async function tick() {{
      let hadError = false;
      document.getElementById("last-updated").textContent = `Last updated: ${{helper.nowIso()}}`;

      // Signals
      try {{
        const r = await helper.fetchJson(`/api/v0/runs/${{encodeURIComponent(RUN_ID)}}/signals?limit=50`);
        const payload = r.data;
        const items = payload.items || [];
        const tb = document.getElementById("signals-tbody");
        tb.innerHTML = items.length
          ? items.map(it => `<tr><td>${{helper.esc(it.ts)}}</td><td>${{it.step ?? "—"}}</td><td>${{it.signal ?? "—"}}</td><td>${{it.signal_changed ?? "—"}}</td></tr>`).join("")
          : "<tr><td colspan='4' class='muted'>Empty</td></tr>";
        document.getElementById("signals-error").style.display = "none";
      }} catch (e) {{
        hadError = true;
        const el = document.getElementById("signals-error");
        el.textContent = `Signals error: ${{e.message || "unknown"}}`;
        el.style.display = "block";
      }}

      // Positions
      try {{
        const r = await helper.fetchJson(`/api/v0/runs/${{encodeURIComponent(RUN_ID)}}/positions?limit=50`);
        const payload = r.data;
        const items = payload.items || [];
        const tb = document.getElementById("positions-tbody");
        tb.innerHTML = items.length
          ? items.map(it => `<tr><td>${{helper.esc(it.ts)}}</td><td>${{it.step ?? "—"}}</td><td>${{it.position_size ?? "—"}}</td><td>${{it.equity ?? "—"}}</td></tr>`).join("")
          : "<tr><td colspan='4' class='muted'>Empty</td></tr>";
        document.getElementById("positions-error").style.display = "none";
      }} catch (e) {{
        hadError = true;
        const el = document.getElementById("positions-error");
        el.textContent = `Positions error: ${{e.message || "unknown"}}`;
        el.style.display = "block";
      }}

      // Orders
      try {{
        const r = await helper.fetchJson(`/api/v0/runs/${{encodeURIComponent(RUN_ID)}}/orders?limit=200&only_nonzero=true`);
        const payload = r.data;
        const items = payload.items || [];
        const tail = (items.length > 50) ? items.slice(items.length - 50) : items;
        const tb = document.getElementById("orders-tbody");
        tb.innerHTML = tail.length
          ? tail.map(it => {{
              const risk = (it.risk_allowed === false) ? "BLOCKED" : (it.risk_allowed === true ? "OK" : "—");
              return `<tr>
                <td>${{helper.esc(it.ts)}}</td>
                <td>${{it.step ?? "—"}}</td>
                <td>${{it.orders_generated ?? "—"}}</td>
                <td>${{it.orders_filled ?? "—"}}</td>
                <td>${{it.orders_rejected ?? "—"}}</td>
                <td>${{it.orders_blocked ?? "—"}}</td>
                <td>${{risk}}</td>
              </tr>`;
            }}).join("")
          : "<tr><td colspan='7' class='muted'>Empty</td></tr>";
        document.getElementById("orders-error").style.display = "none";
      }} catch (e) {{
        hadError = true;
        const el = document.getElementById("orders-error");
        el.textContent = `Orders error: ${{e.message || "unknown"}}`;
        el.style.display = "block";
      }}

      helper.schedule(tick, hadError);
    }}

    tick();
  }})();
  </script>
</body>
</html>"""

        return HTMLResponse(content=html, headers={"Cache-Control": "no-store"})

    # Alias to match operator mental model: /sessions/<id>
    @app.get("/sessions/{run_id}", response_class=HTMLResponse)
    async def watch_only_run_detail_alias(run_id: str):
        return await watch_only_run_detail(run_id)

    # =============================================================================
    # API v0 (read-only) router
    # =============================================================================

    app.include_router(
        build_api_v0_router(
            runs_dir=runs_dir,
            contract_version=DASHBOARD_API_CONTRACT_VERSION,
            health_check=health_check,
            get_runs=get_runs,
            get_run_snapshot_endpoint=get_run_snapshot_endpoint,
        )
    )

    return app
