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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ..monitoring import (
    list_runs as monitoring_list_runs,
    get_run_snapshot,
    tail_events,
    RunNotFoundError,
    RunSnapshot,
)
from ..run_logging import load_run_events, load_run_metadata

logger = logging.getLogger(__name__)


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
# Pydantic Models for API Responses
# =============================================================================


class RunMetadataResponse(BaseModel):
    """API Response für Run-Metadaten."""

    run_id: str
    mode: str
    strategy_name: str
    symbol: str
    timeframe: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None


class RunSnapshotResponse(BaseModel):
    """API Response für Run-Snapshot."""

    run_id: str
    mode: str
    strategy_name: str
    symbol: str
    timeframe: str
    total_steps: int = 0
    total_orders: int = 0
    total_blocked_orders: int = 0
    equity: Optional[float] = None
    realized_pnl: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    drawdown: Optional[float] = None


class TailRowResponse(BaseModel):
    """API Response für Tail-Row."""

    ts_bar: Optional[str] = None
    equity: Optional[float] = None
    realized_pnl: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    position_size: Optional[float] = None
    orders_count: int = 0
    risk_allowed: bool = True
    risk_reasons: str = ""


class AlertResponse(BaseModel):
    """API Response für Alert."""

    rule_id: str
    severity: str
    message: str
    run_id: str
    timestamp: str


class HealthResponse(BaseModel):
    """API Response für Health-Check."""

    status: str


# =============================================================================
# API v0 Models (contracted, read-only)
# =============================================================================


class RunMetaV0(BaseModel):
    """v0: meta.json contract (subset + config_snapshot)."""

    run_id: str
    mode: str
    strategy_name: str
    symbol: str
    timeframe: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    config_snapshot: Dict[str, Any] = Field(default_factory=dict)
    notes: str = ""


class RunDetailV0(BaseModel):
    """v0: run detail = meta + snapshot."""

    meta: RunMetaV0
    snapshot: RunSnapshotResponse


class RunMetricsV0(BaseModel):
    """v0: metrics subset."""

    equity: Optional[float] = None
    realized_pnl: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    drawdown: Optional[float] = None
    total_steps: int = 0
    total_orders: int = 0
    total_blocked_orders: int = 0


class EquityPointV0(BaseModel):
    """v0: equity time series point (best effort)."""

    ts: str
    equity: Optional[float] = None
    realized_pnl: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    drawdown: Optional[float] = None


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
    # API Endpoints
    # =============================================================================

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health-Check-Endpoint."""
        return HealthResponse(status="ok")

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
    # API v0 (read-only, contract-stable)
    # =============================================================================

    def _run_dir_for(run_id: str) -> Path:
        run_dir = runs_dir / run_id
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail=f"run_not_found: {run_id}")
        return run_dir

    def _load_meta_v0(run_id: str) -> RunMetaV0:
        run_dir = _run_dir_for(run_id)
        try:
            meta = load_run_metadata(run_dir)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"meta_not_found: {run_id}")

        return RunMetaV0(
            run_id=meta.run_id,
            mode=meta.mode,
            strategy_name=meta.strategy_name,
            symbol=meta.symbol,
            timeframe=meta.timeframe,
            started_at=meta.started_at.isoformat() if meta.started_at else None,
            ended_at=meta.ended_at.isoformat() if meta.ended_at else None,
            config_snapshot=meta.config_snapshot or {},
            notes=meta.notes or "",
        )

    @app.get("/api/v0/health", response_model=HealthResponse)
    async def api_v0_health():
        return await health_check()

    @app.get("/api/v0/runs", response_model=List[RunMetadataResponse])
    async def api_v0_runs():
        return await get_runs()

    @app.get("/api/v0/runs/{run_id}", response_model=RunDetailV0)
    async def api_v0_run_detail(run_id: str):
        meta = _load_meta_v0(run_id)
        snapshot = await get_run_snapshot_endpoint(run_id)
        return RunDetailV0(meta=meta, snapshot=snapshot)

    @app.get("/api/v0/runs/{run_id}/metrics", response_model=RunMetricsV0)
    async def api_v0_run_metrics(run_id: str):
        snapshot = await get_run_snapshot_endpoint(run_id)
        return RunMetricsV0(
            equity=snapshot.equity,
            realized_pnl=snapshot.realized_pnl,
            unrealized_pnl=snapshot.unrealized_pnl,
            drawdown=snapshot.drawdown,
            total_steps=snapshot.total_steps,
            total_orders=snapshot.total_orders,
            total_blocked_orders=snapshot.total_blocked_orders,
        )

    @app.get("/api/v0/runs/{run_id}/equity", response_model=List[EquityPointV0])
    async def api_v0_run_equity(
        run_id: str,
        limit: int = Query(default=500, ge=1, le=5000),
    ):
        run_dir = _run_dir_for(run_id)
        try:
            events_df = load_run_events(run_dir)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"equity_not_available: {run_id}")

        if len(events_df) == 0:
            return []

        ts_col = "ts_event" if "ts_event" in events_df.columns else "ts_bar" if "ts_bar" in events_df.columns else None
        if ts_col is None:
            raise HTTPException(status_code=404, detail=f"equity_not_available: {run_id}")

        # Ensure chronological order if step exists, otherwise keep file order.
        if "step" in events_df.columns:
            try:
                events_df = events_df.sort_values("step")
            except Exception:
                pass

        if limit and len(events_df) > limit:
            events_df = events_df.tail(limit)

        equity_col = "equity" if "equity" in events_df.columns else None
        realized_col = "realized_pnl" if "realized_pnl" in events_df.columns else ("pnl" if "pnl" in events_df.columns else None)
        unrealized_col = "unrealized_pnl" if "unrealized_pnl" in events_df.columns else None
        drawdown_col = "drawdown" if "drawdown" in events_df.columns else None

        # Best-effort drawdown compute if missing and equity available.
        drawdown_series = None
        if drawdown_col is None and equity_col is not None:
            try:
                eq = events_df[equity_col].astype(float)
                running_max = eq.expanding().max()
                dd = (eq - running_max) / running_max
                drawdown_series = dd
            except Exception:
                drawdown_series = None

        def _to_float(val: Any) -> Optional[float]:
            try:
                if val is None:
                    return None
                if pd.isna(val):
                    return None
                return float(val)
            except Exception:
                return None

        points: List[EquityPointV0] = []
        for idx, row in events_df.iterrows():
            ts_val = row.get(ts_col)
            if ts_val is None:
                continue
            ts_str = str(ts_val)
            points.append(
                EquityPointV0(
                    ts=ts_str,
                    equity=_to_float(row.get(equity_col)) if equity_col else None,
                    realized_pnl=_to_float(row.get(realized_col)) if realized_col else None,
                    unrealized_pnl=_to_float(row.get(unrealized_col)) if unrealized_col else None,
                    drawdown=(
                        _to_float(row.get(drawdown_col))
                        if drawdown_col
                        else (_to_float(drawdown_series.loc[idx]) if drawdown_series is not None else None)
                    ),
                )
            )

        return points

    @app.get("/api/v0/runs/{run_id}/trades")
    async def api_v0_run_trades(run_id: str):
        # Optional v0: only if an explicit trades artifact exists.
        run_dir = _run_dir_for(run_id)
        trades_parquet = run_dir / "trades.parquet"
        trades_csv = run_dir / "trades.csv"
        if trades_parquet.exists() or trades_csv.exists():
            # Intentionally minimal: return raw records (best effort).
            try:
                if trades_parquet.exists():
                    df = pd.read_parquet(trades_parquet)
                else:
                    df = pd.read_csv(trades_csv)
                return {"run_id": run_id, "available": True, "rows": df.to_dict(orient="records")}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"trades_parse_error: {e}")

        raise HTTPException(status_code=404, detail=f"trades_not_available: {run_id}")

    return app
