"""Offline linear evidence reporting helpers.

Reports produced here are diagnostic-only. They do not create trading,
runtime, sizing, promotion, or economic-pass authority.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, MutableMapping


AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"


def normalize_linear_evidence_report(
    payload: Mapping[str, object],
) -> dict[str, object]:
    report = dict(payload)
    report["authority_effect"] = AUTHORITY_EFFECT
    report["runtime_effect"] = RUNTIME_EFFECT
    report.setdefault("status", "DIAGNOSTIC_ONLY")
    report.setdefault("cost_policy_output", "diagnostic_only")
    return report


def write_linear_evidence_report(
    payload: Mapping[str, object],
    output_path: str | Path,
) -> dict[str, object]:
    normalized = normalize_linear_evidence_report(payload)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, sort_keys=True, indent=2) + "\n")
    return normalized


def merge_report_fields(
    base: Mapping[str, object],
    updates: Mapping[str, object],
) -> dict[str, object]:
    merged: MutableMapping[str, object] = dict(base)
    merged.update(updates)
    return normalize_linear_evidence_report(merged)


__all__ = [
    "AUTHORITY_EFFECT",
    "RUNTIME_EFFECT",
    "merge_report_fields",
    "normalize_linear_evidence_report",
    "write_linear_evidence_report",
]
