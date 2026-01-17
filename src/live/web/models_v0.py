from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Pydantic Models for API Responses (read-only)
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
    is_active: Optional[bool] = None
    last_event_time: Optional[str] = None


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
    last_event_time: Optional[str] = None


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
    contract_version: str
    server_time: str


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


class SignalPointV0B(BaseModel):
    """v0.1B: signal point (best effort, read-only)."""

    ts: str
    step: Optional[int] = None
    signal: Optional[int] = None
    signal_changed: Optional[bool] = None


class PositionPointV0B(BaseModel):
    """v0.1B: position point (best effort, read-only)."""

    ts: str
    step: Optional[int] = None
    position_size: Optional[float] = None
    cash: Optional[float] = None
    equity: Optional[float] = None


class OrderPointV0B(BaseModel):
    """v0.1B: order counters + risk summary per event (best effort, read-only)."""

    ts: str
    step: Optional[int] = None
    orders_generated: Optional[int] = None
    orders_filled: Optional[int] = None
    orders_rejected: Optional[int] = None
    orders_blocked: Optional[int] = None
    risk_allowed: Optional[bool] = None
    risk_reasons: Optional[str] = None


class SignalsResponseV0B(BaseModel):
    """v0.1B: signals response wrapper."""

    run_id: str
    asof: str
    count: int
    items: List[SignalPointV0B]


class PositionsResponseV0B(BaseModel):
    """v0.1B: positions response wrapper."""

    run_id: str
    asof: str
    count: int
    items: List[PositionPointV0B]


class OrdersResponseV0B(BaseModel):
    """v0.1B: orders response wrapper."""

    run_id: str
    asof: str
    count: int
    items: List[OrderPointV0B]


# =============================================================================
# API v0.2 Models (control center, additive, read-only)
# =============================================================================


class RunSummaryV02(BaseModel):
    """v0.2: run/session summary (watch-only control center)."""

    run_id: str
    status: str
    started_at: Optional[str] = None
    last_heartbeat: Optional[str] = None
    strategy_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    base_dir: Optional[str] = None


class RunDetailV02(BaseModel):
    """v0.2: run/session detail (pointers + summaries; no side effects)."""

    summary: RunSummaryV02
    pointers: Dict[str, str] = Field(default_factory=dict)
    alerts_summary: Dict[str, Any] = Field(default_factory=dict)
    config_snapshot: Dict[str, Any] = Field(default_factory=dict)


class HealthV02(BaseModel):
    """v0.2: expanded health (components)."""

    status: str
    contract_version: str
    server_time: str
    last_update: str
    components: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class EventItemV02(BaseModel):
    """v0.2: event item for polling/SSE."""

    seq: int
    ts: str
    level: str
    component: str
    msg: str
    run_id: str


class EventsPollResponseV02(BaseModel):
    """v0.2: polling response."""

    run_id: str
    asof: str
    next_seq: int
    count: int
    items: List[EventItemV02]
