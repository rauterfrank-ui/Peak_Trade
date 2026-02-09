from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ScoreResult:
    score: float
    breakdown: dict[str, Any]
    reason: str | None = None


def score_seed(
    *,
    asset_row: Mapping[str, Any],
    latest_risk_row: Mapping[str, Any] | None,
    latest_snapshot_row: Mapping[str, Any] | None,
) -> ScoreResult:
    """
    P5: deterministic placeholder scoring.
    - Base score: 50
    - Risk severity HIGH => -40, MED => -20, LOW => 0
    - Snapshot present => +10
    - Seed assets tagged => +5
    Clamp to [0, 100].
    """
    score = 50.0
    breakdown: dict[str, Any] = {"base": 50.0}

    sev = None
    if latest_risk_row is not None:
        sev = latest_risk_row.get("severity")
    if sev == "HIGH":
        score -= 40.0
        breakdown["risk_penalty"] = -40.0
    elif sev == "MED":
        score -= 20.0
        breakdown["risk_penalty"] = -20.0
    else:
        breakdown["risk_penalty"] = 0.0

    if latest_snapshot_row is not None:
        score += 10.0
        breakdown["snapshot_bonus"] = 10.0
    else:
        breakdown["snapshot_bonus"] = 0.0

    tags_json = asset_row.get("tags_json") or ""
    if isinstance(tags_json, str) and ('"seed"' in tags_json or "seed" in tags_json):
        score += 5.0
        breakdown["seed_bonus"] = 5.0
    else:
        breakdown["seed_bonus"] = 0.0

    # clamp
    score = max(0.0, min(100.0, score))
    reason = "seed_placeholder"
    return ScoreResult(score=score, breakdown=breakdown, reason=reason)
