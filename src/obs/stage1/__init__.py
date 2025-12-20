"""
Peak_Trade Stage1 Monitoring Core Module
=========================================

Phase 16K: Maschinenlesbare Stage1 Reports + Web Dashboard

Provides:
- Stage1Summary: Daily snapshot data model
- Stage1Trend: Trend analysis data model
- discover_stage1_days: Find available report days
- load_stage1_summary: Load daily summary JSON
- load_latest_summary: Load most recent summary
- load_trend: Load or compute trend analysis
"""

from .models import Stage1Summary, Stage1Metrics, Stage1Trend, Stage1TrendRange, Stage1TrendRollups
from .io import discover_stage1_days, load_stage1_summary, load_latest_summary
from .trend import load_trend, compute_trend_from_summaries

__all__ = [
    "Stage1Summary",
    "Stage1Metrics",
    "Stage1Trend",
    "Stage1TrendRange",
    "Stage1TrendRollups",
    "discover_stage1_days",
    "load_stage1_summary",
    "load_latest_summary",
    "load_trend",
    "compute_trend_from_summaries",
]

