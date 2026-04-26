# src/webui/double_play_dashboard_display_json_route_v0.py
"""
Master V2 Double Play — read-only dashboard display JSON route (v0).

GET-only, fixture-backed snapshot from pure `build_dashboard_display_snapshot`.
No scanner, exchange, session, evidence, or market-data imports.

See docs/ops/specs/MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from trading.master_v2.double_play_dashboard_display import (
    DoublePlayDashboardDisplaySnapshot,
    DoublePlayDashboardPanel,
    build_dashboard_display_snapshot,
)

router = APIRouter(
    prefix="/api/master-v2/double-play",
    tags=["master-v2", "double-play", "dashboard-display-readonly"],
)


def _jsonable_panel(panel: DoublePlayDashboardPanel) -> Dict[str, Any]:
    st = panel.status
    status_val = st.value if isinstance(st, Enum) else str(st)
    return {
        "name": panel.name,
        "status": status_val,
        "summary": panel.summary,
        "blockers": list(panel.blockers),
        "missing_inputs": list(panel.missing_inputs),
        "live_authorization": panel.live_authorization,
        "is_authority": panel.is_authority,
        "is_signal": panel.is_signal,
    }


def snapshot_to_jsonable(snap: DoublePlayDashboardDisplaySnapshot) -> Dict[str, Any]:
    """Convert display snapshot to JSON-serializable dict (enum values as strings)."""
    overall = snap.overall_status
    overall_val = overall.value if isinstance(overall, Enum) else str(overall)
    return {
        "panels": [_jsonable_panel(p) for p in snap.panels],
        "overall_status": overall_val,
        "no_live_banner_visible": snap.no_live_banner_visible,
        "display_only": snap.display_only,
        "trading_ready": snap.trading_ready,
        "testnet_ready": snap.testnet_ready,
        "live_ready": snap.live_ready,
        "live_authorization": snap.live_authorization,
        "warnings": list(snap.warnings),
    }


@router.get("/dashboard-display.json")
async def get_double_play_dashboard_display_json() -> JSONResponse:
    """
    Read-only JSON snapshot of Double Play dashboard display DTO (pure, in-memory).

    All optional pure inputs omitted → DISPLAY_MISSING panels; still display-only / no-live.
    """
    snap = build_dashboard_display_snapshot()
    return JSONResponse(
        content=snapshot_to_jsonable(snap),
        headers={"Cache-Control": "no-store"},
    )
