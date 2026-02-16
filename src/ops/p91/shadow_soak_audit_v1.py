from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


_TICK_RE = re.compile(r"^tick_(\d{8}T\d{6}Z)$")
_RUN_RE = re.compile(r"^run_(\d{8}T\d{6}Z)$")


@dataclass(frozen=True)
class P91AuditContextV1:
    out_dir: Path
    max_age_sec: int = 900
    min_ticks: int = 2
    max_ticks_listed: int = 50


def _utc_now_ts() -> int:
    return int(time.time())


def _parse_tick_ts(name: str) -> Optional[str]:
    m = _TICK_RE.match(name)
    return m.group(1) if m else None


def _list_ticks(out_dir: Path) -> List[Path]:
    if not out_dir.exists():
        return []
    ticks: List[Path] = []
    for p in out_dir.iterdir():
        if p.is_dir() and _parse_tick_ts(p.name):
            ticks.append(p)
    ticks.sort(key=lambda p: p.name)
    return ticks


def _safe_read_text(p: Path, max_bytes: int = 4096) -> Optional[str]:
    try:
        data = p.read_bytes()
        if len(data) > max_bytes:
            data = data[:max_bytes]
        return data.decode("utf-8", errors="replace")
    except Exception:
        return None


def _safe_read_json(p: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _latest_p76_result(tick_dir: Path) -> Tuple[Optional[str], Optional[str]]:
    """
    Return (status, path_rel) where status is 'ready'/'not_ready'/etc (lowercased) if found.
    Looks at tick/p76/P76_RESULT.txt.
    """
    p = tick_dir / "p76" / "P76_RESULT.txt"
    txt = _safe_read_text(p)
    if not txt:
        return None, None
    # Expect first token like "P76_READY" or "P76_NOT_READY"
    first = txt.strip().split()[0].strip()
    return first.replace("P76_", "").lower(), str(p)


def _latest_p90_metrics(out_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Best-effort: read last JSON line from $OUT_DIR/P90_WATCH.nohup.log if present.
    """
    candidates = [
        out_dir / "P90_WATCH.nohup.log",
        out_dir / "p90_supervisor_metrics_watch_v1.nohup.log",
        out_dir / "p90_supervisor_metrics_watch_v1.log",
    ]
    for c in candidates:
        if not c.exists():
            continue
        try:
            lines = c.read_text(encoding="utf-8", errors="replace").splitlines()
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                if line.startswith("{") and line.endswith("}"):
                    try:
                        return json.loads(line)
                    except Exception:
                        continue
        except Exception:
            continue
    return None


def build_shadow_soak_audit_v1(ctx: P91AuditContextV1) -> Dict[str, Any]:
    """
    Read-only audit helper:
    - summarizes tick timeline
    - finds latest p76 status (tick_*/p76/P76_RESULT.txt)
    - surfaces anomalies (missing artifacts, stale ticks, gaps)
    No network, no model calls, no execution.
    """
    out_dir = Path(ctx.out_dir)
    now = _utc_now_ts()

    ticks = _list_ticks(out_dir)
    tick_count = len(ticks)

    alerts: List[str] = []
    if not out_dir.exists():
        alerts.append("out_dir_missing")
    if tick_count < ctx.min_ticks:
        alerts.append(f"insufficient_ticks:{tick_count}<{ctx.min_ticks}")

    latest_tick = ticks[-1] if ticks else None
    latest_tick_name = latest_tick.name if latest_tick else None

    age_sec: Optional[int] = None
    if latest_tick:
        try:
            mtime = int(latest_tick.stat().st_mtime)
            age_sec = max(0, now - mtime)
            if age_sec > ctx.max_age_sec:
                alerts.append(f"ticks_stale:age_sec={age_sec}>max_age_sec={ctx.max_age_sec}")
        except Exception:
            alerts.append("latest_tick_stat_failed")

    # detect gaps based on tick directory mtimes (coarse but robust)
    gap_max_sec: Optional[int] = None
    if tick_count >= 2:
        mtimes: List[int] = []
        for t in ticks:
            try:
                mtimes.append(int(t.stat().st_mtime))
            except Exception:
                mtimes.append(0)
        gaps = [max(0, mtimes[i] - mtimes[i - 1]) for i in range(1, len(mtimes))]
        if gaps:
            gap_max_sec = max(gaps)
            # heuristic: if largest gap exceeds 2x max_age_sec, flag
            if gap_max_sec > (ctx.max_age_sec * 2):
                alerts.append(f"large_gap_detected:max_gap_sec={gap_max_sec}")

    latest_p76_status: Optional[str] = None
    latest_p76_path: Optional[str] = None
    if latest_tick:
        latest_p76_status, latest_p76_path = _latest_p76_result(latest_tick)
        if latest_p76_status is None:
            alerts.append("latest_p76_result_missing")

    # per-tick lightweight checks (last N)
    listed = ticks[-ctx.max_ticks_listed :] if tick_count else []
    tick_items: List[Dict[str, Any]] = []
    for t in listed:
        status, p76_path = _latest_p76_result(t)
        item = {
            "tick": t.name,
            "has_manifest": (t / "manifest.json").exists(),
            "has_p86": (t / "p86_result.json").exists(),
            "p76_status": status,
            "p76_path": p76_path,
        }
        if status is None:
            item["alerts"] = ["p76_missing"]
        tick_items.append(item)

    # p79 / p78 metadata (best-effort)
    p79_json = _safe_read_json(out_dir / "p79_health_gate_v1.json") if out_dir.exists() else None
    supervisor_meta = (
        _safe_read_json(out_dir / "supervisor_meta.json") if out_dir.exists() else None
    )
    p90_metrics = _latest_p90_metrics(out_dir) if out_dir.exists() else None

    report: Dict[str, Any] = {
        "meta": {
            "version": "p91_shadow_soak_audit_v1",
            "out_dir": str(out_dir),
            "max_age_sec": ctx.max_age_sec,
            "min_ticks": ctx.min_ticks,
            "max_ticks_listed": ctx.max_ticks_listed,
            "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        },
        "summary": {
            "tick_count": tick_count,
            "latest_tick": latest_tick_name,
            "age_sec": age_sec,
            "gap_max_sec": gap_max_sec,
            "latest_p76_status": latest_p76_status,
            "latest_p76_path": latest_p76_path,
        },
        "alerts": alerts,
        "ticks": tick_items,
        "p79_health_gate_v1": p79_json,
        "supervisor_meta": supervisor_meta,
        "p90_metrics": p90_metrics,
    }

    return report
