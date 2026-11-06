"""
Determinism utilities for ExecutionPipeline (RUNBOOK B / Slice 1).

Contract (frozen):
- seed_u64: sha256(f"{run_id}|{symbol}|{intent_id}")[:8] big-endian
- stable_id: sha256(canonical_json(kind + fields))
- ts_sim: monotonic counter per (run_id, session_id), start 0, +1 per event
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping


def seed_u64(run_id: str, symbol: str, intent_id: str) -> int:
    """
    Deterministic seed derivation (u64).

    Contract:
        seed_u64 = int.from_bytes(sha256(f"{run_id}|{symbol}|{intent_id}")[:8], "big")
    """
    material = f"{run_id}|{symbol}|{intent_id}".encode("utf-8")
    digest = hashlib.sha256(material).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def stable_id(*, kind: str, fields: Mapping[str, Any]) -> str:
    """
    Deterministic ID for a structured object.

    Uses sha256 over canonical JSON (sorted keys, stable separators).
    """
    payload = {"kind": kind, **dict(fields)}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class SimClock:
    """
    Monotonic simulated clock for ts_sim.

    Contract:
      - start at 0
      - +1 per emitted event
    """

    _next: int = 0

    def tick(self) -> int:
        ts_sim = self._next
        self._next += 1
        return ts_sim
