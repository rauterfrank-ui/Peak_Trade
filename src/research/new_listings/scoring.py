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


def _num(x: Any) -> float | None:
    return float(x) if isinstance(x, (int, float)) else None


def score_ccxt(
    asset_tags: Mapping[str, Any], *, risk_severity: str, cfg: Mapping[str, Any]
) -> ScoreResult:
    """
    Deterministic score for CEX assets based on ticker fields.
    Config:
      - volume_bonus_k (default: 0.002)  (bonus = min(20, quoteVolume * k))
      - spread_penalty_max (default: 20)
    """
    base = 50.0
    breakdown: dict[str, Any] = {"base": 50.0}

    # risk penalty
    if risk_severity == "HIGH":
        base -= 40.0
        breakdown["risk_penalty"] = -40.0
    elif risk_severity == "MED":
        base -= 20.0
        breakdown["risk_penalty"] = -20.0
    else:
        breakdown["risk_penalty"] = 0.0

    qv = _num(asset_tags.get("ticker_quoteVolume"))
    k = float(cfg.get("volume_bonus_k", 0.002))
    volume_bonus = 0.0
    if qv is not None and qv > 0:
        volume_bonus = min(20.0, qv * k)
        base += volume_bonus
    breakdown["volume_bonus"] = volume_bonus

    bid = _num(asset_tags.get("ticker_bid"))
    ask = _num(asset_tags.get("ticker_ask"))
    spread_penalty = 0.0
    if bid is not None and ask is not None and bid > 0 and ask >= bid:
        spread_pct = (ask - bid) / bid * 100.0
        spread_penalty_max = float(cfg.get("spread_penalty_max", 20.0))
        spread_penalty = min(spread_penalty_max, spread_pct)
        base -= spread_penalty
    breakdown["spread_penalty"] = -spread_penalty

    score = max(0.0, min(100.0, base))
    return ScoreResult(score=score, breakdown=breakdown, reason="cex_score")
