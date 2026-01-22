from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping


def iter_beta_exec_v1_events(events: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """
    Thin adapter layer (Slice 1 -> Slice 2):
    Normalize a stream of BETA_EXEC_V1 events into plain dicts.

    Notes:
    - Slice 2 ignores ts_utc by design (non-deterministic).
    - This function does not sort; callers should sort deterministically upstream
      (e.g., (run_id, session_id, ts_sim, event_type, event_id)).
    """
    out: List[Dict[str, Any]] = []
    for e in events:
        d = dict(e)
        d.pop("ts_utc", None)
        out.append(d)
    return out
