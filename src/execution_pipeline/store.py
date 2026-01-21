"""
Read-only store for execution_pipeline events (JSONL).

Used by watch-only API/UI.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def _safe_parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


@dataclass(frozen=True)
class RunSummaryV0:
    run_id: str
    correlation_id: str
    started_at: Optional[str]
    last_event_at: Optional[str]
    status: str
    counts: Dict[str, int]


class JsonlExecutionRunStore:
    def __init__(
        self,
        *,
        root: Path = Path("logs/execution"),
        filename: str = "execution_pipeline_events_v0.jsonl",
    ) -> None:
        self.root = root
        self.filename = filename

    @property
    def path(self) -> Path:
        return self.root / self.filename

    def _iter_events(self) -> Iterable[Dict[str, Any]]:
        p = self.path
        if not p.exists():
            return []
        out: List[Dict[str, Any]] = []
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("schema") != "execution_event_v0":
                    continue
                out.append(obj)
        return out

    def list_runs(self, *, limit: int = 200) -> List[RunSummaryV0]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for ev in self._iter_events():
            rid = str(ev.get("run_id") or "")
            if not rid:
                continue
            grouped.setdefault(rid, []).append(ev)

        summaries: List[RunSummaryV0] = []
        for rid, evs in grouped.items():
            evs_sorted = sorted(evs, key=lambda e: (e.get("ts") or ""))
            started = evs_sorted[0].get("ts")
            last = evs_sorted[-1].get("ts")
            corr = str(evs_sorted[0].get("correlation_id") or "")
            counts: Dict[str, int] = {}
            status = "unknown"
            for e in evs_sorted:
                et = str(e.get("event_type") or "")
                if et:
                    counts[et] = counts.get(et, 0) + 1
            if counts.get("failed", 0) > 0:
                status = "failed"
            elif counts.get("canceled", 0) > 0:
                status = "canceled"
            elif counts.get("filled", 0) > 0:
                status = "success"
            summaries.append(
                RunSummaryV0(
                    run_id=rid,
                    correlation_id=corr,
                    started_at=started,
                    last_event_at=last,
                    status=status,
                    counts=counts,
                )
            )

        summaries.sort(key=lambda s: (s.last_event_at or ""), reverse=True)
        return summaries[:limit]

    def get_run(self, run_id: str, *, limit: int = 2000) -> Dict[str, Any]:
        evs = [e for e in self._iter_events() if str(e.get("run_id") or "") == run_id]
        evs = sorted(evs, key=lambda e: (e.get("ts") or ""))[:limit]
        if not evs:
            return {"run_id": run_id, "events": [], "count": 0, "summary": None}

        counts: Dict[str, int] = {}
        for e in evs:
            et = str(e.get("event_type") or "")
            if et:
                counts[et] = counts.get(et, 0) + 1

        status = "unknown"
        if counts.get("failed", 0) > 0:
            status = "failed"
        elif counts.get("canceled", 0) > 0:
            status = "canceled"
        elif counts.get("filled", 0) > 0:
            status = "success"

        return {
            "run_id": run_id,
            "correlation_id": evs[0].get("correlation_id"),
            "events": evs,
            "count": len(evs),
            "summary": {
                "started_at": evs[0].get("ts"),
                "last_event_at": evs[-1].get("ts"),
                "status": status,
                "counts": counts,
            },
        }
