"""Policy v1: cost/edge gate — deterministic rule based on expected edge vs costs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


MIN_EDGE_BUFFER_BP_V1 = 1.0  # conservative default buffer


@dataclass(frozen=True)
class PolicyDecisionV1:
    action: str  # "ALLOW" | "NO_TRADE"
    reason_codes: list[str]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Enforcer-compatible dict (action, reason_codes)."""
        return {"action": self.action, "reason_codes": list(self.reason_codes), **self.metadata}


def _bp_sum(*vals: Optional[float]) -> float:
    s = 0.0
    for v in vals:
        if v is None:
            continue
        try:
            s += float(v)
        except Exception:
            continue
    return s


def decide_policy_v1(*, env: str, decision: dict[str, Any]) -> PolicyDecisionV1:
    """
    Minimal deterministic policy based on expected edge vs. expected costs.

    Inputs (best-effort, missing -> conservative NO_TRADE):
      - decision["inputs"]["current_price"]
      - decision["costs"] (fees_bp, slippage_bp, impact_bp, latency_bp)
      - decision["forecast"]["mu_bp"] (expected edge in bp); if missing => 0

    Rules:
      - env == "live" => NO_TRADE (ENV_LIVE)
      - missing current_price => NO_TRADE (MISSING_CURRENT_PRICE)
      - missing costs dict => NO_TRADE (MISSING_COSTS_V1)
      - if edge_bp <= costs_bp + MIN_EDGE_BUFFER_BP_V1 => NO_TRADE (EDGE_LT_COSTS_V1)
      - else => ALLOW (EDGE_GT_COSTS_V1)
    """
    reason: list[str] = []
    meta: dict[str, Any] = {}

    if env == "live":
        return PolicyDecisionV1(action="NO_TRADE", reason_codes=["ENV_LIVE"], metadata={"env": env})

    inputs = (decision or {}).get("inputs") or {}
    current_price = inputs.get("current_price")
    if current_price is None:
        return PolicyDecisionV1(
            action="NO_TRADE",
            reason_codes=["MISSING_CURRENT_PRICE"],
            metadata={"env": env},
        )

    costs = (decision or {}).get("costs")
    if not isinstance(costs, dict):
        return PolicyDecisionV1(action="NO_TRADE", reason_codes=["MISSING_COSTS_V1"], metadata={"env": env})

    fees_bp = costs.get("fees_bp")
    slippage_bp = costs.get("slippage_bp")
    impact_bp = costs.get("impact_bp")
    latency_bp = costs.get("latency_bp")

    costs_bp = _bp_sum(fees_bp, slippage_bp, impact_bp, latency_bp)

    forecast = (decision or {}).get("forecast") or {}
    mu_bp = forecast.get("mu_bp")
    edge_bp = float(mu_bp) if mu_bp is not None else 0.0

    meta.update(
        {
            "env": env,
            "edge_bp": edge_bp,
            "costs_bp": costs_bp,
            "buffer_bp": MIN_EDGE_BUFFER_BP_V1,
        }
    )

    if edge_bp <= costs_bp + MIN_EDGE_BUFFER_BP_V1:
        reason.append("EDGE_LT_COSTS_V1")
        return PolicyDecisionV1(action="NO_TRADE", reason_codes=reason, metadata=meta)

    reason.append("EDGE_GT_COSTS_V1")
    return PolicyDecisionV1(action="ALLOW", reason_codes=reason, metadata=meta)
