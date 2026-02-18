"""Policy enforcer v0 — enforce policy decisions in execution pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class PolicyEnforceResult:
    allowed: bool
    reason_code: str
    reason_detail: str
    action: str


class PolicyEnforcerV0:
    """
    Enforce policy decisions produced by src.observability.policy.policy_v0.decide_policy_v0.

    Default stance:
    - If policy is missing -> allow (non-breaking)
    - If env is live -> block
    - If policy.action == "NO_TRADE" -> block
    """

    def __init__(self, *, enforce: bool = False) -> None:
        self.enforce = enforce

    def evaluate(self, *, env: str, policy: Optional[dict[str, Any]]) -> PolicyEnforceResult:
        if not self.enforce:
            return PolicyEnforceResult(
                True, "POLICY_ENFORCE_OFF", "policy enforcement disabled", action="ALLOW"
            )

        if env == "live":
            return PolicyEnforceResult(
                False, "ENV_LIVE", "policy gate blocks live by default (v0)", action="BLOCK"
            )

        if not policy:
            return PolicyEnforceResult(
                True, "POLICY_MISSING", "no policy attached; allow (v0)", action="ALLOW"
            )

        action = str(policy.get("action", "ALLOW")).upper()
        if action == "NO_TRADE":
            reason_codes = policy.get("reason_codes") or []
            return PolicyEnforceResult(
                False, "NO_TRADE", f"policy NO_TRADE: {reason_codes}", action="BLOCK"
            )

        return PolicyEnforceResult(
            True, "POLICY_ALLOW", "policy allows execution (v0)", action="ALLOW"
        )
