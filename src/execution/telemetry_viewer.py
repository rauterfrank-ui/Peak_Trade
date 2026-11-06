# src/execution/telemetry_viewer.py
"""
Telemetry Viewer - Read-only queries for execution event logs.

Phase 16C: Operator tools for reading, filtering, and analyzing
execution telemetry without modifying logs.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, Iterable, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TelemetryQuery:
    """
    Query parameters for telemetry events.

    Attributes:
        session_id: Filter by session ID (optional)
        event_type: Filter by event kind (intent/order/fill/gate/error)
        symbol: Filter by trading symbol
        ts_from: Filter events after this ISO timestamp
        ts_to: Filter events before this ISO timestamp
        limit: Maximum number of events to return
    """

    session_id: Optional[str] = None
    event_type: Optional[str] = None  # intent|order|fill|gate|error
    symbol: Optional[str] = None
    ts_from: Optional[str] = None  # ISO8601
    ts_to: Optional[str] = None  # ISO8601
    limit: int = 2000


@dataclass
class TelemetryStats:
    """
    Statistics about parsed telemetry events.

    Attributes:
        total_lines: Total lines read
        valid_events: Successfully parsed events
        invalid_lines: Lines that couldn't be parsed
        error_rate: Ratio of invalid lines to total lines
    """

    total_lines: int = 0
    valid_events: int = 0
    invalid_lines: int = 0

    @property
    def error_rate(self) -> float:
        """Calculate error rate (0.0 to 1.0)."""
        if self.total_lines == 0:
            return 0.0
        return self.invalid_lines / self.total_lines


def iter_events(
    paths: List[Path], query: TelemetryQuery
) -> tuple[Iterator[Dict[str, Any]], TelemetryStats]:
    """
    Iterate over telemetry events from JSONL files with filtering.

    Args:
        paths: List of JSONL file paths to read
        query: Filter criteria

    Yields:
        Event dictionaries matching query filters

    Returns:
        Tuple of (event iterator, stats)

    Example:
        >>> paths = [Path("logs/execution/session_123.jsonl")]
        >>> query = TelemetryQuery(event_type="fill", limit=100)
        >>> events, stats = iter_events(paths, query)
        >>> for event in events:
        ...     print(event["ts"], event["kind"])
    """
    stats = TelemetryStats()

    def _event_generator():
        count = 0

        for path in paths:
            if not path.exists():
                logger.warning(f"Telemetry log not found: {path}")
                continue

            try:
                with path.open("r") as f:
                    for line in f:
                        stats.total_lines += 1

                        # Skip empty lines
                        if not line.strip():
                            continue

                        # Parse JSON
                        try:
                            event = json.loads(line)
                            stats.valid_events += 1
                        except json.JSONDecodeError as e:
                            stats.invalid_lines += 1
                            logger.debug(f"Failed to parse JSONL line: {e}")
                            continue

                        # Apply filters
                        if query.session_id and event.get("session_id") != query.session_id:
                            continue
                        if query.event_type and event.get("kind") != query.event_type:
                            continue
                        if query.symbol and event.get("symbol") != query.symbol:
                            continue

                        # Timestamp filters
                        if query.ts_from or query.ts_to:
                            event_ts = event.get("ts")
                            if event_ts:
                                if query.ts_from and event_ts < query.ts_from:
                                    continue
                                if query.ts_to and event_ts > query.ts_to:
                                    continue

                        yield event
                        count += 1

                        # Respect limit
                        if count >= query.limit:
                            return

            except Exception as e:
                logger.error(f"Error reading telemetry log {path}: {e}")
                continue

    return _event_generator(), stats


def summarize_events(events: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate summary statistics from telemetry events.

    Args:
        events: Iterable of event dictionaries

    Returns:
        Summary dictionary with counts, timestamps, symbols, latency

    Example:
        >>> events = [{"kind": "fill", "symbol": "BTC-USD", "ts": "2025-01-01T12:00:00"}]
        >>> summary = summarize_events(events)
        >>> print(summary["counts_by_type"])
        {'fill': 1}
    """
    # Accumulators
    total_count = 0
    counts_by_type: Dict[str, int] = {}
    symbols = set()
    first_ts: Optional[str] = None
    last_ts: Optional[str] = None
    session_ids = set()

    # Latency tracking (if fields present)
    intent_timestamps = {}  # symbol -> ts
    order_timestamps = {}  # order_id -> ts
    latencies = []  # intent->order or order->fill

    for event in events:
        total_count += 1

        # Count by type
        kind = event.get("kind", "unknown")
        counts_by_type[kind] = counts_by_type.get(kind, 0) + 1

        # Track symbols
        symbol = event.get("symbol")
        if symbol:
            symbols.add(symbol)

        # Track sessions
        session_id = event.get("session_id")
        if session_id:
            session_ids.add(session_id)

        # Track timestamps
        ts = event.get("ts")
        if ts:
            if first_ts is None or ts < first_ts:
                first_ts = ts
            if last_ts is None or ts > last_ts:
                last_ts = ts

        # Latency tracking (optional)
        if kind == "intent" and symbol and ts:
            intent_timestamps[symbol] = ts
        elif kind == "order" and symbol and ts:
            order_ts = ts
            if symbol in intent_timestamps:
                try:
                    intent_dt = datetime.fromisoformat(intent_timestamps[symbol])
                    order_dt = datetime.fromisoformat(order_ts)
                    latency_ms = (order_dt - intent_dt).total_seconds() * 1000
                    latencies.append(latency_ms)
                except Exception:
                    pass

    summary = {
        "total_events": total_count,
        "counts_by_type": counts_by_type,
        "unique_symbols": sorted(symbols),
        "unique_sessions": sorted(session_ids),
        "first_ts": first_ts,
        "last_ts": last_ts,
    }

    # Add latency metrics if available
    if latencies:
        latencies.sort()
        summary["latency_ms"] = {
            "min": latencies[0],
            "max": latencies[-1],
            "median": latencies[len(latencies) // 2],
            "p95": latencies[int(len(latencies) * 0.95)] if len(latencies) > 20 else None,
        }

    return summary


def build_timeline(events: Iterable[Dict[str, Any]], max_items: int = 200) -> List[Dict[str, Any]]:
    """
    Build compact timeline view for dashboard.

    Args:
        events: Iterable of event dictionaries
        max_items: Maximum timeline items to return

    Returns:
        List of compact timeline entries

    Example:
        >>> events = [{"ts": "2025-01-01T12:00:00", "kind": "fill", "symbol": "BTC-USD"}]
        >>> timeline = build_timeline(events, max_items=10)
        >>> print(timeline[0])
        {'ts': '2025-01-01T12:00:00', 'type': 'fill', 'symbol': 'BTC-USD', ...}
    """
    timeline = []

    for event in events:
        # Extract core fields
        entry = {
            "ts": event.get("ts", ""),
            "type": event.get("kind", "unknown"),
            "symbol": event.get("symbol", ""),
            "session_id": event.get("session_id", ""),
            "mode": event.get("mode", ""),
        }

        # Add type-specific fields
        payload = event.get("payload", {})
        kind = event.get("kind")

        if kind == "intent":
            entry["side"] = payload.get("side", "")
            entry["quantity"] = payload.get("quantity", 0)
            entry["price"] = payload.get("current_price", 0)

        elif kind == "order":
            entry["order_id"] = payload.get("client_id", "")
            entry["side"] = payload.get("side", "")
            entry["quantity"] = payload.get("quantity", 0)
            entry["order_type"] = payload.get("order_type", "")

        elif kind == "fill":
            entry["order_id"] = payload.get("client_id", "")
            entry["filled_quantity"] = payload.get("filled_quantity", 0)
            entry["fill_price"] = payload.get("fill_price", 0)
            entry["fill_fee"] = payload.get("fill_fee", 0)

        elif kind == "gate":
            entry["gate_name"] = payload.get("gate_name", "")
            entry["passed"] = payload.get("passed", False)
            entry["reason"] = payload.get("reason", "")

        elif kind == "error":
            entry["error_message"] = payload.get("error", "")

        timeline.append(entry)

        # Respect max_items
        if len(timeline) >= max_items:
            break

    return timeline


def find_session_logs(base_path: Path = Path("logs/execution")) -> List[Path]:
    """
    Find all session log files in base path.

    Args:
        base_path: Base directory for execution logs

    Returns:
        List of JSONL log file paths

    Example:
        >>> logs = find_session_logs()
        >>> print(f"Found {len(logs)} session logs")
    """
    if not base_path.exists():
        logger.warning(f"Telemetry log directory not found: {base_path}")
        return []

    logs = list(base_path.glob("*.jsonl"))
    logger.info(f"Found {len(logs)} telemetry log files in {base_path}")
    return logs
