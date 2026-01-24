#!/usr/bin/env python3
"""
AI Live Exporter (watch-only)
============================
Prometheus Exporter, der eine JSONL Event-Datei tailt und kanonische AI-Metriken
ausgibt.

Env:
- PEAK_TRADE_AI_EVENTS_JSONL (required)  : Pfad zur JSONL Datei
- PEAK_TRADE_AI_RUN_ID (optional)        : Default run_id Label
- PEAK_TRADE_AI_COMPONENT (default: execution_watch)
- PEAK_TRADE_AI_EXPORTER_PORT (default: 9110)

Kanonische Metriken (definiert in src/obs/ai_telemetry.py):
- peaktrade_ai_decisions_total{decision,reason,component,run_id}
- peaktrade_ai_actions_total{action,component,run_id}
- peaktrade_ai_decision_latency_seconds{component,run_id}
- peaktrade_ai_last_decision_timestamp_seconds{component,run_id}
- peaktrade_ai_live_heartbeat{component,run_id}  (Gauge=1)

Safety:
- Watch-only: keine Trading-Aktion, nur /metrics
- Wenn JSONL Datei fehlt: Exporter läuft weiter und setzt nur Heartbeat
"""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from prometheus_client import start_http_server

    _PROM_AVAILABLE = True
except Exception:
    _PROM_AVAILABLE = False

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.obs.ai_telemetry import (  # noqa: E402
    inc_events_dropped,
    inc_events_parse_error,
    observe_decision_latency_ms,
    record_action,
    record_decision,
    set_heartbeat,
    set_last_event_timestamp_seconds,
)

logger = logging.getLogger(__name__)


DEFAULT_COMPONENT = "execution_watch"
DEFAULT_PORT = 9110
_CANON_REASON = {
    "none",
    "no_signal",
    "cooldown",
    "market_closed",
    "risk_limit",
    "governance_no_live",
    "invalid_order",
    "other",
}
_CANON_ACTION = {"order_intent", "order_request", "submit", "cancel", "fill", "none"}


class _RateLimitedWarn:
    def __init__(self, min_interval_s: float = 60.0):
        self._min_interval_s = float(min_interval_s)
        self._last: Dict[str, float] = {}

    def warn(self, key: str, msg: str) -> None:
        now = time.time()
        last = self._last.get(key, 0.0)
        if now - last >= self._min_interval_s:
            self._last[key] = now
            logger.warning("%s", msg)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except Exception:
        return default


def _pick_label(ev: Dict[str, Any], *, key: str, env_fallback: Optional[str]) -> Optional[str]:
    v = ev.get(key)
    if isinstance(v, str) and v.strip():
        return v.strip()
    return env_fallback


def _coerce_latency_s(ev: Dict[str, Any]) -> Optional[float]:
    v = ev.get("latency_s")
    if isinstance(v, (int, float)):
        return float(v)
    v_ms = ev.get("latency_ms")
    if isinstance(v_ms, (int, float)):
        return float(v_ms) / 1000.0
    return None


def _parse_ts_utc_to_unix(ts_utc: str) -> Optional[float]:
    raw = (ts_utc or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).timestamp()
    except Exception:
        return None


def _canon_reason(v: str) -> str:
    s = (v or "").strip()
    if not s:
        return "none"
    s = s.lower()
    return s if s in _CANON_REASON else "other"


def _canon_action(v: Optional[str]) -> str:
    s = (v or "").strip()
    if not s:
        return "none"
    s = s.lower()
    return s if s in _CANON_ACTION else "none"


def _canon_decision(v: str) -> Optional[str]:
    s = (v or "").strip().lower()
    if not s:
        return None
    if s in {"accept", "reject", "noop"}:
        return s
    if s in {"approve", "approved", "allow", "allowed"}:
        return "accept"
    if s in {"deny", "denied", "block", "blocked"}:
        return "reject"
    if s in {"no_op", "skip", "ignored"}:
        return "noop"
    return None


def _map_beta_reason(reason_code: Optional[str], *, fallback: str) -> str:
    rc = (reason_code or "").strip().upper()
    if not rc:
        return fallback
    if rc.startswith("VALIDATION_") or rc.startswith("ADAPTER_"):
        return "invalid_order"
    if rc.startswith("RISK_"):
        return "risk_limit"
    if rc.startswith("POLICY_"):
        return "governance_no_live"
    return "other"


def _determine_source(ev: Dict[str, Any]) -> str:
    """
    Finite source taxonomy:
    {"sample_v1","beta_exec_v1","exec_event_v0","unknown"}
    """
    if "v" in ev:
        return "sample_v1"
    if str(ev.get("schema_version") or "") == "BETA_EXEC_V1":
        return "beta_exec_v1"
    if str(ev.get("schema") or "") == "execution_event_v0":
        return "exec_event_v0"
    return "unknown"


def _process_line(
    ln: str,
    *,
    default_component: str,
    default_run_id: str,
    warn: _RateLimitedWarn,
) -> None:
    try:
        ev = json.loads(ln)
    except Exception:
        warn.warn("ai_live.bad_json", "ai_live_exporter: bad JSON line (skipped)")
        # Source unknown when JSON can't be parsed.
        inc_events_parse_error(source="unknown")
        inc_events_dropped(source="unknown", reason="bad_json")
        return

    if not isinstance(ev, dict):
        inc_events_dropped(source="unknown", reason="other")
        return

    try:
        _process_event(
            ev,
            default_component=default_component,
            default_run_id=default_run_id,
            warn=warn,
        )
    except Exception:
        # Exporter loop must never crash on a malformed event shape.
        warn.warn("ai_live.process_error", "ai_live_exporter: error processing event (skipped)")
        inc_events_dropped(source=_determine_source(ev), reason="other")
        return


def _process_event(
    ev: Dict[str, Any],
    *,
    default_component: str,
    default_run_id: str,
    warn: _RateLimitedWarn,
) -> None:
    ev_source = _determine_source(ev)

    # Canonical v=1 schema
    if "v" in ev:
        v = ev.get("v")
        if v != 1:
            warn.warn("ai_live.unknown_v", f"ai_live_exporter: ignoring unknown schema v={v!r}")
            inc_events_dropped(source=ev_source, reason="unknown_schema")
            return

        ev_run_id = _pick_label(ev, key="run_id", env_fallback=default_run_id) or default_run_id
        ev_component = (
            _pick_label(ev, key="component", env_fallback=default_component) or default_component
        )

        decision = _canon_decision(str(ev.get("decision") or ""))
        reason = _canon_reason(str(ev.get("reason") or "none"))
        action = _canon_action(ev.get("action") if isinstance(ev.get("action"), str) else None)
        latency_s = _coerce_latency_s(ev)

        ts_event_s = _parse_ts_utc_to_unix(str(ev.get("ts_utc") or ""))
        ts_s = ts_event_s or time.time()

        # v2 freshness: only update on valid events and only with event timestamp.
        # Missing ts_utc → do not update (don't fabricate).
        if decision is None:
            inc_events_dropped(source=ev_source, reason="missing_fields")
            return
        if ts_event_s is not None:
            set_last_event_timestamp_seconds(source=ev_source, timestamp_s=ts_event_s)

        # Emit action (always finite enum)
        if action and action != "none":
            record_action(action=action, component=ev_component, run_id=ev_run_id)

        record_decision(
            decision=decision,
            reason=reason,
            component=ev_component,
            run_id=ev_run_id,
            latency_s=latency_s,
            timestamp_s=ts_s,
        )

        # v2 latency histogram (ms): observe only if event provides latency_ms.
        v_ms = ev.get("latency_ms")
        if isinstance(v_ms, (int, float)):
            observe_decision_latency_ms(source=ev_source, decision=decision, latency_ms=float(v_ms))
        return

    # Real pipeline schema: BETA_EXEC_V1
    if str(ev.get("schema_version") or "") == "BETA_EXEC_V1":
        ev_run_id = _pick_label(ev, key="run_id", env_fallback=default_run_id) or default_run_id
        ev_component = default_component  # pipeline is execution watch by default
        et = str(ev.get("event_type") or "").strip().upper()
        ts_event_s = _parse_ts_utc_to_unix(str(ev.get("ts_utc") or ""))
        ts_s = ts_event_s or time.time()
        reason_code = ev.get("reason_code")
        reason = _map_beta_reason(
            reason_code if isinstance(reason_code, str) else None, fallback="other"
        )

        if not et:
            inc_events_dropped(source=ev_source, reason="missing_fields")
            return

        # Actions (finite)
        if et == "INTENT":
            if ts_event_s is not None:
                set_last_event_timestamp_seconds(source=ev_source, timestamp_s=ts_event_s)
            record_action(action="order_intent", component=ev_component, run_id=ev_run_id)
            return
        if et == "SUBMIT":
            if ts_event_s is not None:
                set_last_event_timestamp_seconds(source=ev_source, timestamp_s=ts_event_s)
            record_action(action="submit", component=ev_component, run_id=ev_run_id)
            record_decision(
                decision="accept",
                reason="none",
                component=ev_component,
                run_id=ev_run_id,
                latency_s=None,
                timestamp_s=ts_s,
            )
            return
        if et == "FILL":
            if ts_event_s is not None:
                set_last_event_timestamp_seconds(source=ev_source, timestamp_s=ts_event_s)
            record_action(action="fill", component=ev_component, run_id=ev_run_id)
            return
        if et == "REJECT":
            if ts_event_s is not None:
                set_last_event_timestamp_seconds(source=ev_source, timestamp_s=ts_event_s)
            record_action(action="order_request", component=ev_component, run_id=ev_run_id)
            record_decision(
                decision="reject",
                reason=reason,
                component=ev_component,
                run_id=ev_run_id,
                latency_s=None,
                timestamp_s=ts_s,
            )
            return
        if et in {"VALIDATION_REJECT", "RISK_REJECT", "ERROR"}:
            if ts_event_s is not None:
                set_last_event_timestamp_seconds(source=ev_source, timestamp_s=ts_event_s)
            record_decision(
                decision="reject",
                reason=reason,
                component=ev_component,
                run_id=ev_run_id,
                latency_s=None,
                timestamp_s=ts_s,
            )
            return
        inc_events_dropped(source=ev_source, reason="unknown_schema")
        return

    # ExecutionEventV0 schema (best-effort)
    if str(ev.get("schema") or "") == "execution_event_v0":
        ev_run_id = _pick_label(ev, key="run_id", env_fallback=default_run_id) or default_run_id
        ev_component = default_component
        et = str(ev.get("event_type") or "").strip().lower()
        ts_event_s = _parse_ts_utc_to_unix(str(ev.get("ts") or ""))
        ts_s = ts_event_s or time.time()

        if not et:
            inc_events_dropped(source=ev_source, reason="missing_fields")
            return

        if et == "created":
            if ts_event_s is not None:
                set_last_event_timestamp_seconds(source=ev_source, timestamp_s=ts_event_s)
            record_action(action="order_intent", component=ev_component, run_id=ev_run_id)
            return
        if et == "submitted":
            if ts_event_s is not None:
                set_last_event_timestamp_seconds(source=ev_source, timestamp_s=ts_event_s)
            record_action(action="submit", component=ev_component, run_id=ev_run_id)
            record_decision(
                decision="accept",
                reason="none",
                component=ev_component,
                run_id=ev_run_id,
                timestamp_s=ts_s,
            )
            return
        if et == "filled":
            if ts_event_s is not None:
                set_last_event_timestamp_seconds(source=ev_source, timestamp_s=ts_event_s)
            record_action(action="fill", component=ev_component, run_id=ev_run_id)
            return
        if et == "canceled":
            if ts_event_s is not None:
                set_last_event_timestamp_seconds(source=ev_source, timestamp_s=ts_event_s)
            record_action(action="cancel", component=ev_component, run_id=ev_run_id)
            return
        if et == "failed":
            if ts_event_s is not None:
                set_last_event_timestamp_seconds(source=ev_source, timestamp_s=ts_event_s)
            record_decision(
                decision="reject",
                reason="other",
                component=ev_component,
                run_id=ev_run_id,
                timestamp_s=ts_s,
            )
            return
        inc_events_dropped(source=ev_source, reason="unknown_schema")
        return

    # Legacy / fallback mapping (best-effort)
    inc_events_dropped(source=ev_source, reason="unknown_schema")
    ev_run_id = _pick_label(ev, key="run_id", env_fallback=default_run_id) or default_run_id
    ev_component = (
        _pick_label(ev, key="component", env_fallback=default_component) or default_component
    )
    latency_s = _coerce_latency_s(ev)
    decision = _coerce_decision(ev)
    if decision:
        record_decision(
            decision=decision,
            reason=_coerce_reason(ev),
            component=ev_component,
            run_id=ev_run_id,
            latency_s=latency_s,
            timestamp_s=time.time(),
        )
    action = _coerce_action(ev)
    if action:
        record_action(action=action, component=ev_component, run_id=ev_run_id)


def _coerce_decision(ev: Dict[str, Any]) -> Optional[str]:
    """
    Map common event shapes to decision=accept|reject|noop.
    """
    v = ev.get("decision")
    if isinstance(v, str) and v.strip():
        s = v.strip().lower()
        if s in {"accept", "approve", "approved", "allow", "allowed"}:
            return "accept"
        if s in {"reject", "deny", "denied", "block", "blocked"}:
            return "reject"
        if s in {"noop", "no_op", "skip", "ignored"}:
            return "noop"
        return s

    # Fallback: derive from type / event_type
    et = ev.get("type") or ev.get("event_type")
    if isinstance(et, str) and et.strip():
        s = et.strip().lower()
        if "reject" in s or "block" in s or "deny" in s:
            return "reject"
        if "accept" in s or "approve" in s or "allow" in s:
            return "accept"
        if "noop" in s or "skip" in s:
            return "noop"
    return None


def _coerce_reason(ev: Dict[str, Any]) -> str:
    for k in ("reason", "block_reason", "gate_reason", "policy_reason"):
        v = ev.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return "none"


def _coerce_action(ev: Dict[str, Any]) -> Optional[str]:
    v = ev.get("action")
    if isinstance(v, str) and v.strip():
        return v.strip()
    v2 = ev.get("action_type")
    if isinstance(v2, str) and v2.strip():
        return v2.strip()
    return None


class _JSONLTailer:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._fh: Optional[Any] = None
        self._pos = 0
        self._last_size = -1

    def _open_tail(self) -> bool:
        if not self.path.exists():
            return False
        try:
            self._fh = self.path.open("r", encoding="utf-8")
            self._fh.seek(0, 2)  # tail: start at end
            self._pos = self._fh.tell()
            self._last_size = int(self.path.stat().st_size)
            return True
        except Exception:
            self._fh = None
            return False

    def _maybe_reopen_on_rotation(self) -> None:
        if not self.path.exists():
            self.close()
            self._last_size = -1
            return
        try:
            size = int(self.path.stat().st_size)
        except Exception:
            return
        # If truncated, reopen and tail from end.
        if self._last_size >= 0 and size < self._last_size:
            self.close()
            self._open_tail()
        self._last_size = size

    def read_new_lines(self) -> list[str]:
        if self._fh is None:
            if not self._open_tail():
                return []
        self._maybe_reopen_on_rotation()
        if self._fh is None:
            return []
        try:
            self._fh.seek(self._pos)
            chunk = self._fh.read()
            if not chunk:
                return []
            self._pos = self._fh.tell()
            return [ln for ln in chunk.splitlines() if ln.strip()]
        except Exception:
            self.close()
            return []

    def close(self) -> None:
        if self._fh is not None:
            try:
                self._fh.close()
            except Exception:
                pass
        self._fh = None


class AILiveExporter:
    def __init__(self, *, jsonl_path: Path, component: str, run_id: str, port: int) -> None:
        self.jsonl_path = jsonl_path
        self.component = component
        self.run_id = run_id
        self.port = port
        self._shutdown = False
        self._tailer = _JSONLTailer(jsonl_path)

        signal.signal(signal.SIGINT, self._on_signal)
        signal.signal(signal.SIGTERM, self._on_signal)

    def _on_signal(self, signum: int, frame: Any) -> None:
        logger.info("signal=%s shutdown=1", signum)
        self._shutdown = True

    def run(self) -> int:
        if not _PROM_AVAILABLE:
            logger.error("prometheus_client not available. Install: pip install prometheus-client")
            return 1

        try:
            start_http_server(self.port)
        except Exception as e:
            logger.error("failed to start /metrics server: %s", e)
            return 1

        if self.port == 9110:
            logger.info("serving /metrics on :%s (Prometheus-local expects job=ai_live at :9110)", self.port)
        else:
            logger.warning(
                "serving /metrics on :%s (Prometheus-local expects :9110; update scrape target if you override)",
                self.port,
            )

        warned_missing = False
        empty_reads = 0
        warn = _RateLimitedWarn(min_interval_s=60.0)

        logger.info(
            "ai_live_exporter started port=%s component=%s run_id=%s",
            self.port,
            self.component,
            self.run_id,
        )
        logger.info("jsonl=%s", str(self.jsonl_path))

        while not self._shutdown:
            # Heartbeat: always 1 while process is alive.
            set_heartbeat(component=self.component, run_id=self.run_id)

            if not self.jsonl_path.exists():
                if not warned_missing:
                    logger.warning(
                        "events file missing; exporter running with heartbeat only: %s",
                        str(self.jsonl_path),
                    )
                    warned_missing = True
                time.sleep(1.0)
                continue
            warned_missing = False

            lines = self._tailer.read_new_lines()
            if not lines:
                empty_reads += 1
                time.sleep(0.2 if empty_reads < 10 else 1.0)
                continue
            empty_reads = 0

            for ln in lines:
                _process_line(
                    ln,
                    default_component=self.component,
                    default_run_id=self.run_id,
                    warn=warn,
                )

        self._tailer.close()
        return 0


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    jsonl_path_str = os.getenv("PEAK_TRADE_AI_EVENTS_JSONL")
    if not jsonl_path_str:
        logger.error("PEAK_TRADE_AI_EVENTS_JSONL environment variable not set")
        return 1

    component = os.getenv("PEAK_TRADE_AI_COMPONENT", DEFAULT_COMPONENT).strip() or DEFAULT_COMPONENT
    run_id = (os.getenv("PEAK_TRADE_AI_RUN_ID") or "na").strip() or "na"
    port = _env_int("PEAK_TRADE_AI_EXPORTER_PORT", DEFAULT_PORT)

    exporter = AILiveExporter(
        jsonl_path=Path(jsonl_path_str),
        component=component,
        run_id=run_id,
        port=port,
    )
    return exporter.run()


if __name__ == "__main__":
    raise SystemExit(main())
