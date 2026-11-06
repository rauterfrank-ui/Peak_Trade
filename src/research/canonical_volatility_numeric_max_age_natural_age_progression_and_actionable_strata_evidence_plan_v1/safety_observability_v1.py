"""Counterfactual STALE safety/risk/exit observability (non-enforcing)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.actionable_strata_v1 import (
    ActionableAlphaStrataEvidenceV1,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.constants_v1 import (
    ALPHA_ONLY_COUNTERFACTUAL_BLOCK,
    EXIT_COUNTERFACTUAL_BLOCK,
    RECONCILIATION_COUNTERFACTUAL_BLOCK,
    RISK_COUNTERFACTUAL_BLOCK,
    SAFETY_COUNTERFACTUAL_BLOCK,
    SAFETY_RISK_EXIT_ACTION_KEYS,
)


@dataclass(frozen=True)
class SafetyRiskExitObservabilityV1:
    counterfactual_stale: bool
    alpha_only_counterfactual_block: bool
    actions_available_when_stale: Mapping[str, bool]
    exit_counterfactual_block: bool
    risk_counterfactual_block: bool
    safety_counterfactual_block: bool
    reconciliation_counterfactual_block: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "actions_available_when_stale": dict(self.actions_available_when_stale),
            "alpha_only_counterfactual_block": self.alpha_only_counterfactual_block,
            "counterfactual_stale": self.counterfactual_stale,
            "exit_counterfactual_block": self.exit_counterfactual_block,
            "reconciliation_counterfactual_block": self.reconciliation_counterfactual_block,
            "risk_counterfactual_block": self.risk_counterfactual_block,
            "safety_counterfactual_block": self.safety_counterfactual_block,
        }


def project_safety_risk_exit_observability_v1(
    *,
    strata: ActionableAlphaStrataEvidenceV1 | Mapping[str, Any],
    counterfactual_stale: bool,
) -> SafetyRiskExitObservabilityV1:
    """Mark exit/risk/safety/reconciliation as still evaluable under stale CF block.

    Does not implement an enforcing stale gate. Alpha-only CF block means those
    actions remain observationally available from productive flags.
    """
    if isinstance(strata, ActionableAlphaStrataEvidenceV1):
        exit_ok = bool(strata.exit_action_available)
        risk_ok = bool(strata.risk_action_available)
        recon_ok = bool(strata.reconciliation_action_available)
    else:
        payload = dict(strata)
        exit_ok = bool(payload.get("exit_action_available", True))
        risk_ok = bool(payload.get("risk_action_available", True))
        recon_ok = bool(payload.get("reconciliation_action_available", True))

    # Under counterfactual stale, alpha is the only blocked dimension.
    available = {
        "SAFETY_EXIT": exit_ok and not SAFETY_COUNTERFACTUAL_BLOCK,
        "HARD_RISK_REDUCE": risk_ok and not RISK_COUNTERFACTUAL_BLOCK,
        "POSITION_RECONCILIATION": recon_ok and not RECONCILIATION_COUNTERFACTUAL_BLOCK,
        "MANDATORY_ADVERSE_REDUCE": risk_ok and not RISK_COUNTERFACTUAL_BLOCK,
        "PROFIT_EXIT": exit_ok and not EXIT_COUNTERFACTUAL_BLOCK,
        "TIME_EXIT": exit_ok and not EXIT_COUNTERFACTUAL_BLOCK,
        "INVALIDATION_EXIT": exit_ok and not EXIT_COUNTERFACTUAL_BLOCK,
    }
    if set(available) != set(SAFETY_RISK_EXIT_ACTION_KEYS):
        raise ValueError("safety_risk_exit_action_key_drift")

    return SafetyRiskExitObservabilityV1(
        counterfactual_stale=bool(counterfactual_stale),
        alpha_only_counterfactual_block=ALPHA_ONLY_COUNTERFACTUAL_BLOCK,
        actions_available_when_stale=available,
        exit_counterfactual_block=EXIT_COUNTERFACTUAL_BLOCK,
        risk_counterfactual_block=RISK_COUNTERFACTUAL_BLOCK,
        safety_counterfactual_block=SAFETY_COUNTERFACTUAL_BLOCK,
        reconciliation_counterfactual_block=RECONCILIATION_COUNTERFACTUAL_BLOCK,
    )


def safety_risk_exit_independence_matrix_v1() -> Mapping[str, Any]:
    return {
        "ALPHA_ONLY_COUNTERFACTUAL_BLOCK": ALPHA_ONLY_COUNTERFACTUAL_BLOCK,
        "EXIT_COUNTERFACTUAL_BLOCK": EXIT_COUNTERFACTUAL_BLOCK,
        "RISK_COUNTERFACTUAL_BLOCK": RISK_COUNTERFACTUAL_BLOCK,
        "SAFETY_COUNTERFACTUAL_BLOCK": SAFETY_COUNTERFACTUAL_BLOCK,
        "RECONCILIATION_COUNTERFACTUAL_BLOCK": RECONCILIATION_COUNTERFACTUAL_BLOCK,
        "enforcing_stale_gate_implemented": False,
        "action_keys": list(SAFETY_RISK_EXIT_ACTION_KEYS),
    }
