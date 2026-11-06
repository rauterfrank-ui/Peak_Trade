"""Execution events JSONL logger (NO_TRADE, default OFF).

Emit execution events to a local JSONL file for Shadow/Testnet evidence.
Enable via PT_EXEC_EVENTS_ENABLED=true. Writes only under out/.

Session-scoped: when set_session_context(session_id) is active, events
go to out/ops/execution_events/sessions/<session_id>/execution_events.jsonl.
"""

from __future__ import annotations

import json
import os
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

DEFAULT_JSONL_PATH = Path("out/ops/execution_events/execution_events.jsonl")

_SESSION_CONTEXT: ContextVar[str | None] = ContextVar("execution_events_session_id", default=None)


def expected_session_scoped_events_jsonl_path(session_id: str) -> Path:
    """
    Canonical repo-relative path for session-scoped execution events JSONL.

    Matches the session branch of _jsonl_path() when set_session_context is active.
    Read-only helper for operator tooling (no writes, no env).
    """
    base = Path("out/ops/execution_events/sessions")
    safe_id = (session_id or "").replace("/", "_").replace(":", "_").replace(" ", "_")
    return base / safe_id / "execution_events.jsonl"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _enabled() -> bool:
    v = os.getenv("PT_EXEC_EVENTS_ENABLED", "false").strip().lower()
    return v in ("1", "true", "yes", "y", "t")


def _mode() -> str:
    return os.getenv("PT_EXEC_MODE", "").strip().lower() or "unknown"


def _jsonl_path() -> Path:
    session_id = _SESSION_CONTEXT.get()
    if session_id:
        base = Path("out/ops/execution_events/sessions")
        safe_id = (session_id or "").replace("/", "_").replace(":", "_").replace(" ", "_")
        return base / safe_id / "execution_events.jsonl"
    p = os.getenv("PT_EXEC_EVENTS_JSONL_PATH", str(DEFAULT_JSONL_PATH)).strip()
    return Path(p)


def set_session_context(session_id: str | None) -> None:
    """Set execution session context for session-scoped JSONL paths."""
    _SESSION_CONTEXT.set(session_id)


def clear_session_context() -> None:
    """Clear execution session context."""
    _SESSION_CONTEXT.set(None)


def get_session_context() -> str | None:
    """Return current session context (None if unset)."""
    return _SESSION_CONTEXT.get()


def _guard_out_only(p: Path) -> None:
    out_root = (Path.cwd() / "out").resolve()
    try:
        p.resolve().relative_to(out_root)
    except ValueError as e:
        raise ValueError("Refusing to write outside out/") from e


@dataclass(frozen=True)
class ExecEvent:
    ts: str
    mode: str
    event_type: str
    level: str
    is_anomaly: bool = False
    is_error: bool = False
    msg: str = ""
    session_id: str | None = None
    exchange: str | None = None
    symbol: str | None = None
    order_id: str | None = None
    client_order_id: str | None = None
    side: str | None = None
    qty: float | None = None
    price: float | None = None
    extra: dict[str, Any] | None = None


def emit(
    *,
    event_type: str,
    level: str = "info",
    is_anomaly: bool = False,
    is_error: bool = False,
    msg: str = "",
    exchange: str | None = None,
    symbol: str | None = None,
    order_id: str | None = None,
    client_order_id: str | None = None,
    side: str | None = None,
    qty: float | None = None,
    price: float | None = None,
    extra: Mapping[str, Any] | None = None,
) -> None:
    """Append one execution event to JSONL. No-op when PT_EXEC_EVENTS_ENABLED is false."""
    if not _enabled():
        return

    path = _jsonl_path()
    _guard_out_only(path)

    path.parent.mkdir(parents=True, exist_ok=True)

    # Include session_id when context is set (session-scoped correlation)
    session_id = _SESSION_CONTEXT.get()

    evt = ExecEvent(
        ts=_utc_now(),
        mode=_mode(),
        event_type=event_type,
        level=level,
        is_anomaly=bool(is_anomaly),
        is_error=bool(is_error),
        msg=msg,
        session_id=session_id,
        exchange=exchange,
        symbol=symbol,
        order_id=order_id,
        client_order_id=client_order_id,
        side=side,
        qty=qty,
        price=price,
        extra=dict(extra) if extra is not None else None,
    )
    line = json.dumps(
        {k: v for k, v in asdict(evt).items() if v is not None},
        ensure_ascii=False,
    )
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
