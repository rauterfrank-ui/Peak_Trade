"""Reject synthetic / non-productive-real Cap22 ranking facts from productive handoff."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.hard_facts_system_closure_v1.constants_v1 import (
    PRODUCTIVE_RANKING_CAPABILITY_ID,
    PRODUCTIVE_RANKING_PRODUCER_VERSION,
    SYNTHETIC_RANKING_MARKERS,
)
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import SNAPSHOT_STATE_VALID


class Cap22ProductiveRealGateError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.code = code


def assert_cap22_productive_real_ranking_v1(snapshot: Mapping[str, Any]) -> None:
    capability = str(snapshot.get("capability_id") or "")
    if capability != PRODUCTIVE_RANKING_CAPABILITY_ID:
        raise Cap22ProductiveRealGateError("CAP22_CAPABILITY_MISMATCH", capability)
    producer = str(snapshot.get("producer_version") or "")
    if producer != PRODUCTIVE_RANKING_PRODUCER_VERSION:
        raise Cap22ProductiveRealGateError("CAP22_PRODUCER_MISMATCH", producer)
    state = str(snapshot.get("snapshot_state") or "")
    if state != SNAPSHOT_STATE_VALID:
        raise Cap22ProductiveRealGateError("CAP22_SNAPSHOT_NOT_VALID", state)
    provenance = str(snapshot.get("ranking_policy_provenance") or "")
    lowered = provenance.lower()
    for marker in SYNTHETIC_RANKING_MARKERS:
        if marker.lower() in lowered:
            raise Cap22ProductiveRealGateError("SYNTHETIC_RANKING_PROVENANCE", marker)
    authority = snapshot.get("authority")
    if isinstance(authority, Mapping):
        if authority.get("productive_real_fact") is False:
            raise Cap22ProductiveRealGateError("PRODUCTIVE_REAL_FACT_FALSE")
        if authority.get("synthetic_ranking_fact") is True:
            raise Cap22ProductiveRealGateError("SYNTHETIC_RANKING_FACT_TRUE")
    call_graph = snapshot.get("call_graph") or ()
    if isinstance(call_graph, list):
        call_graph = tuple(call_graph)
    for step in call_graph:
        step_s = str(step).lower()
        if "synthesize" in step_s or "synthetic" in step_s:
            raise Cap22ProductiveRealGateError("SYNTHETIC_CALL_GRAPH_STEP", str(step))
