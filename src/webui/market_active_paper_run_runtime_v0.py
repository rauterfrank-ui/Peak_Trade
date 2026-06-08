"""SSR-only active Paper run panel for GET /market (env-gated, bridge/staging evidence)."""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ENV_ENABLED = "PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_ENABLED"
ENV_BRIDGE_ROOT = "PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_BRIDGE_ROOT"
ENV_DETAIL_URL = "PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_DETAIL_URL"
FIXED_GEN_ENV = "PEAK_TRADE_FIXED_GENERATED_AT_UTC"
ACTIVE_IDLE_MINUTES = 10


def enabled_explicitly_on() -> bool:
    raw = os.environ.get(ENV_ENABLED)
    return raw is not None and raw.strip() == "1"


def resolved_bridge_root_or_none() -> Path | None:
    raw = os.environ.get(ENV_BRIDGE_ROOT)
    if raw is None or not str(raw).strip():
        return None
    path = Path(raw).expanduser()
    try:
        path = path.resolve(strict=True)
    except OSError:
        return None
    if not path.is_dir():
        return None
    return path


def _now_utc() -> datetime:
    fixed = (os.environ.get(FIXED_GEN_ENV) or "").strip()
    if fixed:
        return datetime.fromisoformat(fixed.replace("Z", "+00:00"))
    return datetime.now(timezone.utc)


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _last_event_row(events_path: Path) -> dict[str, str]:
    try:
        with events_path.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    except OSError:
        return {}
    if not rows:
        return {}
    return {k: (v or "") for k, v in rows[-1].items()}


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _count_fills(runtime_out: Path) -> int | None:
    fills_path = runtime_out / "fills.json"
    data = _load_json(fills_path)
    if data is None:
        return None
    fills = data.get("fills")
    if isinstance(fills, list):
        return len(fills)
    return None


def _base_context(*, gate_enabled: bool, display_status: str) -> dict[str, Any]:
    return {
        "section_visible": False,
        "gate_enabled": gate_enabled,
        "display_status": display_status,
        "non_authorizing": True,
        "evidence_only": True,
        "not_live": True,
        "not_preflight_lift": True,
        "run_id": "",
        "mode": "",
        "is_active": False,
        "strategy_name": "",
        "symbol_display": "",
        "started_at": "",
        "elapsed_seconds": None,
        "heartbeat_iteration": None,
        "heartbeat_ts_utc": "",
        "heartbeat_reason": "",
        "last_event_time": "",
        "cash": None,
        "equity": None,
        "orders_executed": 0,
        "fills_count": None,
        "no_trade": True,
        "evidence_root_label": "",
        "detail_url": "",
        "live_authorized": False,
        "ready_for_operator_arming": False,
        "preflight_lift_authorized": False,
        "operator_truth_go_granted": False,
        "summary_line": "",
    }


def build_market_active_paper_run_display_context() -> dict[str, Any]:
    """SSR-only active Paper run panel for GET /market (fail closed by default)."""

    if not enabled_explicitly_on():
        ctx = _base_context(gate_enabled=False, display_status="disabled")
        ctx["summary_line"] = "Active Paper run panel disabled (env gate off)."
        return ctx

    bridge_root = resolved_bridge_root_or_none()
    if bridge_root is None:
        ctx = _base_context(gate_enabled=True, display_status="unconfigured")
        ctx["summary_line"] = "Active Paper run bridge root unconfigured."
        return ctx

    meta = _load_json(bridge_root / "meta.json")
    pointer = _load_json(bridge_root / "evidence_pointer.json")
    if meta is None or pointer is None:
        ctx = _base_context(gate_enabled=True, display_status="bridge_unreadable")
        ctx["summary_line"] = "Bridge meta/evidence_pointer unreadable."
        return ctx

    if pointer.get("view_only") is not True or pointer.get("fake_data") is True:
        ctx = _base_context(gate_enabled=True, display_status="pointer_guard_failed")
        ctx["summary_line"] = "Bridge pointer failed view-only guard."
        return ctx

    events_row = _last_event_row(bridge_root / "events.csv")
    heartbeat = pointer.get("heartbeat_snapshot")
    if not isinstance(heartbeat, dict):
        hb_path_raw = pointer.get("heartbeat_file") or pointer.get("runtime_out")
        if hb_path_raw:
            hb_file = Path(str(hb_path_raw)) / "scheduler_heartbeat_freshness_v0.json"
            if hb_file.is_file():
                heartbeat = _load_json(hb_file)

    runtime_out_raw = pointer.get("runtime_out")
    runtime_out = Path(str(runtime_out_raw)).expanduser() if runtime_out_raw else None
    fills_count = _count_fills(runtime_out) if runtime_out and runtime_out.is_dir() else None

    run_id = str(meta.get("run_id") or pointer.get("run_id") or "").strip()
    started_at = str(meta.get("started_at") or "").strip()
    last_event_time = events_row.get("ts_event") or events_row.get("ts_bar") or ""
    if isinstance(heartbeat, dict) and not last_event_time:
        last_event_time = str(heartbeat.get("ts_utc") or "")

    now = _now_utc()
    started_dt = _parse_ts(started_at)
    elapsed_seconds = int((now - started_dt).total_seconds()) if started_dt else None
    last_event_dt = _parse_ts(last_event_time)
    is_active = meta.get("ended_at") in (None, "") and last_event_dt is not None
    if is_active and last_event_dt is not None:
        idle = (now - last_event_dt).total_seconds()
        is_active = idle <= ACTIVE_IDLE_MINUTES * 60

    cash_raw = events_row.get("cash") or events_row.get("equity")
    cash: float | None = None
    if cash_raw not in ("", None):
        try:
            cash = float(cash_raw)
        except (TypeError, ValueError):
            cash = None

    detail_url = (os.environ.get(ENV_DETAIL_URL) or "").strip()
    if not detail_url and run_id:
        detail_url = f"http://127.0.0.1:8010/watch/runs/{run_id}"

    evidence_root_label = ""
    if runtime_out_raw:
        evidence_root_label = Path(str(runtime_out_raw)).name

    iteration = None
    reason = ""
    hb_ts = ""
    if isinstance(heartbeat, dict):
        iteration = heartbeat.get("iteration")
        reason = str(heartbeat.get("reason") or "")
        hb_ts = str(heartbeat.get("ts_utc") or "")

    return {
        "section_visible": True,
        "gate_enabled": True,
        "display_status": "ready",
        "non_authorizing": True,
        "evidence_only": True,
        "not_live": True,
        "not_preflight_lift": True,
        "run_id": run_id,
        "mode": str(meta.get("mode") or pointer.get("mode") or "paper").upper(),
        "is_active": is_active,
        "strategy_name": str(meta.get("strategy_name") or ""),
        "symbol_display": str(meta.get("symbol") or ""),
        "started_at": started_at,
        "elapsed_seconds": elapsed_seconds,
        "heartbeat_iteration": iteration,
        "heartbeat_ts_utc": hb_ts,
        "heartbeat_reason": reason,
        "last_event_time": last_event_time,
        "cash": cash,
        "equity": cash,
        "orders_executed": 0,
        "fills_count": fills_count,
        "no_trade": fills_count == 0 if fills_count is not None else True,
        "evidence_root_label": evidence_root_label,
        "detail_url": detail_url,
        "live_authorized": False,
        "ready_for_operator_arming": False,
        "preflight_lift_authorized": False,
        "operator_truth_go_granted": False,
        "summary_line": (
            f"Active Paper run {run_id} — iteration {iteration or '—'} — "
            f"{'active' if is_active else 'idle/stale'} (bridge evidence, view-only)"
        ),
    }


__all__ = [
    "ENV_BRIDGE_ROOT",
    "ENV_DETAIL_URL",
    "ENV_ENABLED",
    "build_market_active_paper_run_display_context",
    "enabled_explicitly_on",
    "resolved_bridge_root_or_none",
]
