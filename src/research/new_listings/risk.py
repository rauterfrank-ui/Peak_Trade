from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class RiskResult:
    severity: str  # LOW/MED/HIGH
    flags: dict[str, Any]


def assess_risk_seed(asset_row: Mapping[str, Any]) -> RiskResult:
    """
    P4: deterministic placeholder risk assessment.
    - Seed assets are always LOW unless tags indicate otherwise.
    """
    tags_json = asset_row.get("tags_json") or "{}"
    flags: dict[str, Any] = {"seed": True}
    severity = "LOW"
    if isinstance(tags_json, str) and ('"high_risk"' in tags_json or "high_risk" in tags_json):
        severity = "HIGH"
        flags["tag_high_risk"] = True
    return RiskResult(severity=severity, flags=flags)
