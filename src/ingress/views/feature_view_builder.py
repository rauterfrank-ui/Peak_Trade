"""
Build FeatureView from event JSONL (Runbook A3).
Deterministic aggregations; never include raw payload in output.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from src.ingress.normalized_event import NormalizedEvent
from src.ingress.views.feature_view import ArtifactPointer, FeatureView
from src.risk.cmes import default_cmes_facts


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_feature_view_from_jsonl(
    jsonl_path: str,
    run_id: str = "default",
) -> FeatureView:
    """
    Read events from JSONL, aggregate counts and safe facts only.
    Never put payload, raw, transcript, api_key, secret, token into FeatureView.
    """
    path = Path(jsonl_path)
    if not jsonl_path or not str(jsonl_path).strip() or not path.exists() or not path.is_file():
        facts = default_cmes_facts()
        return FeatureView(run_id=run_id, ts_ms=0, counts={}, facts=facts, artifacts=[])

    counts: Dict[str, int] = {}
    facts: Dict[str, Any] = {}
    ts_min: int | None = None
    ts_max: int | None = None

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                ev = NormalizedEvent(
                    event_id=obj["event_id"],
                    ts_ms=int(obj["ts_ms"]),
                    source=obj["source"],
                    kind=obj["kind"],
                    scope=obj["scope"],
                    tags=list(obj.get("tags", [])),
                    sensitivity=obj.get("sensitivity", "internal"),
                    payload=obj.get("payload", {}),
                )
            except (KeyError, TypeError, ValueError):
                continue
            # Aggregate counts by kind
            kind = ev.kind
            counts[kind] = counts.get(kind, 0) + 1
            if ts_min is None or ev.ts_ms < ts_min:
                ts_min = ev.ts_ms
            if ts_max is None or ev.ts_ms > ts_max:
                ts_max = ev.ts_ms
            # Safe facts from scope/source (no payload)
            if ev.scope and "scope" not in facts:
                facts["scope"] = ev.scope
            if ev.source and "source" not in facts:
                facts["source"] = ev.source

    if ts_max is None:
        ts_max = 0
    if ts_min is None:
        ts_min = 0

    # CMES 7 facts (canonical, pointer-only); default for now; upstream can override later
    cmes = default_cmes_facts()
    # Safe run-scope facts (no payload)
    final_facts: Dict[str, Any] = {
        **cmes,
        "event_count_total": sum(counts.values()),
        "ts_min": ts_min,
        "ts_max": ts_max,
    }
    if facts.get("scope"):
        final_facts["scope"] = facts["scope"]
    if facts.get("source"):
        final_facts["source"] = facts["source"]

    # Artifact pointer for the JSONL itself (path + sha256 of file)
    file_sha = _sha256_hex(path.read_bytes())
    artifacts: List[ArtifactPointer] = [
        ArtifactPointer(path=str(path), sha256=file_sha),
    ]

    return FeatureView(
        run_id=run_id,
        ts_ms=ts_max,
        counts=counts,
        facts=final_facts,
        artifacts=artifacts,
    )
