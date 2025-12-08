# src/webui/app.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import toml
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates


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


def create_app() -> FastAPI:
    app = FastAPI(title="Peak_Trade Dashboard v0")

    @app.get("/")
    async def index(request: Request) -> Any:
        status = get_project_status()
        strategy_tiering = load_strategy_tiering()
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "status": status,
                "strategy_tiering": strategy_tiering,
            },
        )

    return app
