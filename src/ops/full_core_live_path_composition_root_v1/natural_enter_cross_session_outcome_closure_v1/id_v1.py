"""Deterministic pending outcome identity."""

from __future__ import annotations

import hashlib


def pending_outcome_id_from_decision_event_ref_v1(decision_event_ref: str) -> str:
    ref = str(decision_event_ref or "").strip()
    if not ref:
        raise ValueError("DECISION_EVENT_REF_REQUIRED")
    digest = hashlib.sha256(ref.encode("utf-8")).hexdigest()[:32]
    return f"neo.pending.{digest}"
