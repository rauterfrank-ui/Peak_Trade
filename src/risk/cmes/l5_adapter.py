"""
L5 Risk Gate adapter: deterministic allow/block from CMES facts (Runbook step I).

Same facts => same decision; reason_codes sorted for determinism.
Kill-switch and existing risk gate wiring remain primary; this is a deterministic reader.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .facts import CMESFactsValidationError, canonicalize_facts

RISK_DECISION_BLOCK = frozenset({"BLOCK", "REDUCE"})
STRATEGY_STATE_TRADING_OK = frozenset({"ENABLED"})


@dataclass(frozen=True)
class L5Decision:
    """Deterministic allow/block + ordered reason codes."""

    allow: bool
    reason_codes: List[str]


def l5_decision_from_facts(facts: Dict[str, Any]) -> L5Decision:
    """
    Produce allow/block from CMES facts. Deterministic: same facts => same decision.
    Block if: risk_decision in (BLOCK, REDUCE), or no_trade_triggered, or strategy_state not ENABLED.
    reason_codes are sorted for stable ordering. Invalid facts => fail-closed (block).
    """
    try:
        canonical = canonicalize_facts(facts)
    except CMESFactsValidationError:
        return L5Decision(allow=False, reason_codes=["FACTS_INVALID"])
    reasons: List[str] = []

    if canonical.get("risk_decision") in RISK_DECISION_BLOCK:
        reasons.extend(canonical.get("risk_reason_codes") or [])
    if canonical.get("no_trade_triggered"):
        reasons.extend(canonical.get("no_trade_trigger_ids") or [])
    if canonical.get("strategy_state") not in STRATEGY_STATE_TRADING_OK:
        reasons.append(f"strategy_state={canonical.get('strategy_state', '')}")

    reasons = sorted(set(reasons))
    allow = (
        canonical.get("risk_decision") not in RISK_DECISION_BLOCK
        and not canonical.get("no_trade_triggered")
        and canonical.get("strategy_state") in STRATEGY_STATE_TRADING_OK
    )
    return L5Decision(allow=allow, reason_codes=reasons)
