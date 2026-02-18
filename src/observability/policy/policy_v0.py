from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PolicyDecisionV0:
    action: str  # e.g. NO_TRADE, ALLOW
    reason_codes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {"action": self.action, "reason_codes": list(self.reason_codes)}


def decide_policy_v0(
    *,
    decision_ctx: Dict[str, Any],
    intent: Any,
    env: str,
) -> Dict[str, Any]:
    """
    Phase v0 policy: safety-first.
    Default: NO_TRADE unless explicitly in non-live and intent is marked as paper/shadow safe AND inputs are present.
    This does NOT constitute trading advice; it's an internal execution gating policy.
    """

    reason: List[str] = []

    # Hard rule: never "ALLOW" in live via v0 policy
    if env == "live":
        reason.append("ENV_LIVE")
        return PolicyDecisionV0(action="NO_TRADE", reason_codes=reason).to_dict()

    # Require current_price for any future evolution (v0 keeps NO_TRADE)
    inputs = decision_ctx.get("inputs") or {}
    if inputs.get("current_price") is None:
        reason.append("MISSING_CURRENT_PRICE")

    # v0: no model, no edge — keep conservative
    reason.append("NO_MODEL_EDGE_V0")

    return PolicyDecisionV0(action="NO_TRADE", reason_codes=reason).to_dict()
