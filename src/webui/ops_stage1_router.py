"""
Peak_Trade: Stage1 Ops Dashboard API
====================================

Phase 16K: Read-only Stage1 monitoring dashboard endpoints.

Endpoints:
- GET /ops/stage1 - HTML dashboard page
- GET /ops/stage1/latest - Latest daily summary (JSON)
- GET /ops/stage1/trend - Trend analysis (JSON)

Reports: reports/obs/stage1/
Files:
- YYYY-MM-DD_summary.json (daily summaries from stage1_daily_snapshot.py)
- stage1_trend.json (trend analysis from stage1_trend_report.py)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.obs.stage1 import (
    Stage1Summary,
    Stage1Trend,
    load_latest_summary,
    load_trend,
)

logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/ops/stage1", tags=["ops", "stage1"])

# Global config (set by app during initialization)
_STAGE1_REPORT_ROOT: Optional[Path] = None
_TEMPLATES: Optional[Jinja2Templates] = None


def set_stage1_config(report_root: Path, templates: Jinja2Templates) -> None:
    """
    Configure Stage1 router with paths.
    
    Args:
        report_root: Path to Stage1 reports directory
        templates: Jinja2Templates instance
    """
    global _STAGE1_REPORT_ROOT, _TEMPLATES
    _STAGE1_REPORT_ROOT = report_root
    _TEMPLATES = templates
    logger.info(f"Stage1 router configured: report_root={report_root}")


def get_report_root() -> Path:
    """Get configured report root or raise error."""
    if _STAGE1_REPORT_ROOT is None:
        raise RuntimeError("Stage1 router not configured. Call set_stage1_config() first.")
    return _STAGE1_REPORT_ROOT


def get_templates() -> Jinja2Templates:
    """Get configured templates or raise error."""
    if _TEMPLATES is None:
        raise RuntimeError("Stage1 router not configured. Call set_stage1_config() first.")
    return _TEMPLATES


# =============================================================================
# API ENDPOINTS
# =============================================================================


@router.get("/latest")
async def get_latest_summary() -> Stage1Summary:
    """
    Get the most recent Stage1 daily summary.
    
    Returns:
        Stage1Summary object with latest metrics.
    
    Raises:
        HTTPException: 404 if no summary found.
    """
    report_root = get_report_root()
    
    summary = load_latest_summary(report_root)
    if summary is None:
        raise HTTPException(
            status_code=404,
            detail=f"No Stage1 summary found in {report_root}",
        )
    
    return summary


@router.get("/trend")
async def get_trend(days: int = Query(14, ge=1, le=90)) -> Stage1Trend:
    """
    Get Stage1 trend analysis.
    
    Priority:
    1. Load pre-computed stage1_trend.json if available
    2. Compute from recent summaries
    
    Args:
        days: Number of days to analyze (1-90, default 14)
    
    Returns:
        Stage1Trend object with series and rollups.
    
    Raises:
        HTTPException: 404 if no data available.
    """
    report_root = get_report_root()
    
    trend = load_trend(report_root, days=days)
    if trend is None:
        raise HTTPException(
            status_code=404,
            detail=f"No Stage1 trend data available in {report_root}",
        )
    
    return trend


@router.get("", response_class=HTMLResponse)
async def stage1_dashboard(
    request: Request,
    days: int = Query(14, ge=1, le=90, description="Number of days for trend"),
) -> Any:
    """
    Stage1 Ops Dashboard HTML page.
    
    Shows:
    - Latest metrics badge (GO/HOLD/NO_GO)
    - Most recent measurement
    - Trend table (last N days)
    - Auto-refresh (30s)
    
    Args:
        request: FastAPI request object
        days: Number of days to show in trend (1-90, default 14)
    
    Returns:
        HTML page with Stage1 monitoring status.
    """
    templates = get_templates()
    report_root = get_report_root()
    
    # Load data
    try:
        latest = load_latest_summary(report_root)
    except Exception as e:
        logger.error(f"Failed to load latest summary: {e}")
        latest = None
    
    try:
        trend = load_trend(report_root, days=days)
    except Exception as e:
        logger.error(f"Failed to load trend: {e}")
        trend = None
    
    # Build context
    context: Dict[str, Any] = {
        "request": request,
        "latest": latest,
        "trend": trend,
        "days": days,
        "report_root": str(report_root),
        "has_data": latest is not None or trend is not None,
    }
    
    return templates.TemplateResponse(request, "ops_stage1.html", context)

