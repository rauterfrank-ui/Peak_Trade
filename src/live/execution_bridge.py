# src/live/execution_bridge.py
"""
Execution Bridge for Live-Track Integration.

Phase 16B: Reads execution events from JSONL logs and maps them to
Live-Track timeline format for monitoring and visualization.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExecutionTimelineRow:
    """
    Timeline row for Live-Track display.

    Attributes:
        ts: Timestamp
        kind: Event kind (gate/intent/order/fill)
        symbol: Trading symbol
        description: Human-readable description
        details: Additional details dict
    """

    ts: datetime
    kind: str
    symbol: str
    description: str
    details: Dict[str, Any]


def get_execution_timeline(
    session_id: str,
    base_path: str = "logs/execution",
    limit: int = 200,
) -> List[ExecutionTimelineRow]:
    """
    Load execution timeline for a session.

    Reads last N events from logs/execution/<session_id>.jsonl
    and maps them to Live-Track timeline rows.

    Args:
        session_id: Session ID to load
        base_path: Base path for execution logs
        limit: Maximum number of events to load (from end of file)

    Returns:
        List of ExecutionTimelineRow objects (newest first)

    Example:
        >>> timeline = get_execution_timeline("session_123", limit=50)
        >>> for row in timeline:
        ...     print(f"{row.ts} [{row.kind}] {row.description}")
    """
    log_path = Path(base_path) / f"{session_id}.jsonl"

    if not log_path.exists():
        logger.warning(f"Execution log not found: {log_path}")
        return []

    events = []

    try:
        # Read all lines (JSONL format)
        with log_path.open("r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    event_dict = json.loads(line)
                    events.append(event_dict)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSONL line: {e}")
                    continue

        # Take last N events
        events = events[-limit:]

        # Map to timeline rows
        timeline = []
        for event in events:
            row = _event_to_timeline_row(event)
            if row:
                timeline.append(row)

        # Newest first
        timeline.reverse()

        return timeline

    except Exception as e:
        logger.error(f"Failed to load execution timeline: {e}")
        return []


def _event_to_timeline_row(event_dict: Dict[str, Any]) -> Optional[ExecutionTimelineRow]:
    """
    Map execution event to timeline row.

    Args:
        event_dict: Event dictionary from JSONL

    Returns:
        ExecutionTimelineRow or None if mapping fails
    """
    try:
        ts_str = event_dict.get("ts")
        if not ts_str:
            return None

        ts = datetime.fromisoformat(ts_str)
        kind = event_dict.get("kind", "unknown")
        symbol = event_dict.get("symbol", "")
        payload = event_dict.get("payload", {})

        # Build description based on kind
        if kind == "intent":
            side = payload.get("side", "")
            qty = payload.get("quantity", 0)
            price = payload.get("current_price", 0)
            description = f"Intent: {side.upper()} {qty:.6f} @ ${price:,.2f}"

        elif kind == "order":
            side = payload.get("side", "")
            qty = payload.get("quantity", 0)
            order_type = payload.get("order_type", "market")
            description = f"Order: {side.upper()} {qty:.6f} ({order_type})"

        elif kind == "fill":
            qty = payload.get("filled_quantity", 0)
            price = payload.get("fill_price", 0)
            fee = payload.get("fill_fee", 0)
            description = f"Fill: {qty:.6f} @ ${price:,.2f} (fee: ${fee:.4f})"

        elif kind == "gate":
            gate_name = payload.get("gate_name", "")
            passed = payload.get("passed", False)
            status = "✅ PASS" if passed else "❌ BLOCK"
            description = f"Gate [{gate_name}]: {status}"

        elif kind == "error":
            error_msg = payload.get("error", "Unknown error")
            description = f"Error: {error_msg}"

        else:
            description = f"{kind.upper()}: {payload}"

        return ExecutionTimelineRow(
            ts=ts,
            kind=kind,
            symbol=symbol,
            description=description,
            details=payload,
        )

    except Exception as e:
        logger.error(f"Failed to map event to timeline row: {e}")
        return None


def get_execution_summary(
    session_id: str,
    base_path: str = "logs/execution",
) -> Dict[str, Any]:
    """
    Get execution summary statistics for a session.

    Args:
        session_id: Session ID
        base_path: Base path for execution logs

    Returns:
        Summary dict with counts and statistics
    """
    timeline = get_execution_timeline(session_id, base_path, limit=10000)

    if not timeline:
        return {
            "session_id": session_id,
            "event_count": 0,
            "found": False,
        }

    # Count by kind
    kind_counts = {}
    for row in timeline:
        kind_counts[row.kind] = kind_counts.get(row.kind, 0) + 1

    # Get time range
    timestamps = [row.ts for row in timeline]
    start_time = min(timestamps) if timestamps else None
    end_time = max(timestamps) if timestamps else None

    return {
        "session_id": session_id,
        "event_count": len(timeline),
        "found": True,
        "kind_counts": kind_counts,
        "start_time": start_time.isoformat() if start_time else None,
        "end_time": end_time.isoformat() if end_time else None,
        "symbols": list(set(row.symbol for row in timeline)),
    }
