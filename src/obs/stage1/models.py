"""
Peak_Trade Stage1 Data Models
==============================

Pydantic models for Stage1 JSON summaries and trends.
"""

from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Stage1Metrics(BaseModel):
    """Metrics for a single day's Stage1 snapshot."""
    
    new_alerts: int = Field(ge=0, description="New alerts detected in 24h window")
    critical_alerts: int = Field(ge=0, description="Critical severity alerts")
    parse_errors: int = Field(ge=0, description="Parse errors encountered")
    operator_actions: int = Field(ge=0, description="Operator actions taken")
    legacy_alerts: int = Field(ge=0, description="Legacy keyword hits")


class Stage1Summary(BaseModel):
    """Daily Stage1 snapshot summary."""
    
    schema_version: int = Field(ge=1, description="Schema version (currently 1)")
    date: str = Field(description="Date in YYYY-MM-DD format")
    created_at_utc: str = Field(description="ISO8601 UTC timestamp")
    report_dir: str = Field(description="Path to report directory")
    metrics: Stage1Metrics
    notes: List[str] = Field(default_factory=list, description="Optional notes")


class Stage1TrendRange(BaseModel):
    """Time range for trend analysis."""
    
    days: int = Field(ge=1, description="Number of days in range")
    start: Optional[str] = Field(None, description="Start date YYYY-MM-DD")
    end: Optional[str] = Field(None, description="End date YYYY-MM-DD")


class Stage1TrendSeries(BaseModel):
    """Single data point in trend series."""
    
    date: str = Field(description="Date in YYYY-MM-DD format")
    new_alerts: int = Field(ge=0)
    critical_alerts: int = Field(ge=0)
    parse_errors: int = Field(ge=0)
    operator_actions: int = Field(ge=0)


class Stage1TrendRollups(BaseModel):
    """Aggregated statistics and go/no-go assessment."""
    
    new_alerts_total: int = Field(ge=0, description="Total new alerts in range")
    new_alerts_avg: float = Field(ge=0.0, description="Average new alerts per day")
    critical_days: int = Field(ge=0, description="Days with critical alerts")
    parse_error_days: int = Field(ge=0, description="Days with parse errors")
    operator_action_days: int = Field(ge=0, description="Days with operator actions")
    go_no_go: Literal["GO", "HOLD", "NO_GO"] = Field(description="Readiness assessment")
    reasons: List[str] = Field(default_factory=list, description="Assessment reasons")


class Stage1Trend(BaseModel):
    """Stage1 trend analysis over time."""
    
    schema_version: int = Field(ge=1, description="Schema version (currently 1)")
    generated_at_utc: str = Field(description="ISO8601 UTC timestamp")
    range: Stage1TrendRange
    series: List[Stage1TrendSeries] = Field(default_factory=list)
    rollups: Stage1TrendRollups

