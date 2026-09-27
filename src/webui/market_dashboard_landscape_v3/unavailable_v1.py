"""Fail-closed unavailable field envelopes for Landscape V3."""

from __future__ import annotations

from typing import Any


def missing_source(reason: str) -> dict[str, Any]:
    return {"availability": "MISSING_SOURCE", "reason": reason, "value": None}


def not_bound(reason: str) -> dict[str, Any]:
    return {"availability": "NOT_BOUND", "reason": reason, "value": None}


def unknown(reason: str) -> dict[str, Any]:
    return {"availability": "UNKNOWN", "reason": reason, "value": None}


def available(value: Any, *, provenance: dict[str, Any] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"availability": "AVAILABLE", "value": value}
    if provenance is not None:
        out["provenance"] = provenance
    return out
