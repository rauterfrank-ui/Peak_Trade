"""
Balance semantics guardrail classifier.

Classifies raw balance payloads before decision-adjacent use.
Aligns with docs/ops/reviews/balance_semantics_guardrail_runtime_contract/CONTRACT.md.

Usage (Phase 1 stub; no callers yet):
    from src.live.balance_semantics_guardrail import (
        classify_balance_semantics,
        BalanceSemanticsResult,
        BalanceSemanticState,
    )
    result = classify_balance_semantics(balance=raw_balance, source_metadata={"source_type": "fetch_balance"})
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

BalanceSemanticState = Literal[
    "balance_semantics_clear",
    "balance_semantics_warning",
    "balance_semantics_blocked",
]

BalanceReasonCode = Literal[
    "BALANCE_FREE_EXPLICIT",
    "BALANCE_PAPER_BROKER_EXPLICIT",
    "BALANCE_CASH_FALLBACK_AMBIGUOUS",
    "BALANCE_NO_DATA",
    "BALANCE_INVALID_PAYLOAD",
]


@dataclass(frozen=True)
class BalanceSemanticsResult:
    """Contract outputs for the balance-semantics guardrail."""

    semantic_state: BalanceSemanticState
    reason_code: BalanceReasonCode
    decision_use_allowed: bool
    operator_visible_state: str


def classify_balance_semantics(
    *,
    balance: dict[str, Any] | float | int | None,
    source_metadata: dict[str, Any],
) -> BalanceSemanticsResult:
    """
    Classify balance semantics before decision-adjacent use.

    Contract: do not silently upgrade cash fallback into free/usable capacity.
    Fail toward caution or blocked under ambiguity.

    Args:
        balance: Raw balance payload (dict from fetch_balance, or scalar for paper_broker_cash).
        source_metadata: At least "source_type": "fetch_balance" | "paper_broker_cash".

    Returns:
        BalanceSemanticsResult with semantic_state, reason_code, decision_use_allowed, operator_visible_state.
    """
    source_type = source_metadata.get("source_type", "fetch_balance")

    if source_type == "paper_broker_cash":
        return BalanceSemanticsResult(
            semantic_state="balance_semantics_clear",
            reason_code="BALANCE_PAPER_BROKER_EXPLICIT",
            decision_use_allowed=True,
            operator_visible_state="paper_broker_cash_explicit",
        )

    if balance is None or not isinstance(balance, dict):
        return BalanceSemanticsResult(
            semantic_state="balance_semantics_blocked",
            reason_code="BALANCE_INVALID_PAYLOAD",
            decision_use_allowed=False,
            operator_visible_state="blocked: invalid balance payload",
        )

    free_val = balance.get("free")
    cash_val = balance.get("cash")

    if free_val is not None and free_val != "":
        return BalanceSemanticsResult(
            semantic_state="balance_semantics_clear",
            reason_code="BALANCE_FREE_EXPLICIT",
            decision_use_allowed=True,
            operator_visible_state="free_explicit",
        )

    if cash_val is not None and cash_val != "":
        return BalanceSemanticsResult(
            semantic_state="balance_semantics_blocked",
            reason_code="BALANCE_CASH_FALLBACK_AMBIGUOUS",
            decision_use_allowed=False,
            operator_visible_state="blocked: cash fallback not upgradeable to free/usable",
        )

    return BalanceSemanticsResult(
        semantic_state="balance_semantics_blocked",
        reason_code="BALANCE_NO_DATA",
        decision_use_allowed=False,
        operator_visible_state="blocked: no free or cash data",
    )
