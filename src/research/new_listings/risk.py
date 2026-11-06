from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping


def _num(x: Any) -> float | None:
    return float(x) if isinstance(x, (int, float)) else None


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


def assess_risk_ccxt(asset_row: Mapping[str, Any], *, cfg: Mapping[str, Any]) -> RiskResult:
    """
    Deterministic risk for CEX assets from ticker (spread/volume heuristics).
    Config: spread_high_pct (default 10), spread_med_pct (default 5).
    """
    tags_json = asset_row.get("tags_json") or "{}"
    tags = tags_json if isinstance(tags_json, dict) else {}
    if isinstance(tags_json, str):
        try:
            tags = json.loads(tags_json)
        except (json.JSONDecodeError, TypeError):
            pass
    if not isinstance(tags, dict):
        tags = {}

    bid = _num(tags.get("ticker_bid"))
    ask = _num(tags.get("ticker_ask"))
    spread_high_pct = float(cfg.get("spread_high_pct", 10.0))
    spread_med_pct = float(cfg.get("spread_med_pct", 5.0))

    severity = "LOW"
    flags: dict[str, Any] = {"cex": True}

    if bid is not None and ask is not None and bid > 0 and ask >= bid:
        spread_pct = (ask - bid) / bid * 100.0
        flags["spread_pct"] = round(spread_pct, 4)
        if spread_pct >= spread_high_pct:
            severity = "HIGH"
            flags["spread_high"] = True
        elif spread_pct >= spread_med_pct:
            severity = "MED"
            flags["spread_med"] = True

    return RiskResult(severity=severity, flags=flags)
