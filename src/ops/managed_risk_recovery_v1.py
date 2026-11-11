"""Re-evaluate a stopped loss/position scope under the original risk gate."""

from dataclasses import asdict
import math

from src.ops.filegate_recovery_authority_v1 import (
    FilegateAuthorityError,
    attest_filegate_owner_evidence_v1,
    is_digest_v1,
)
from src.ops.gates.risk_gate import RiskContext, RiskLimits, evaluate_risk
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest


def attest_managed_risk_recovery_v1(
    *,
    stop,
    limits,
    context,
    original_policy_sha256,
    original_observation_sha256,
    expires_at,
    key,
):
    """Use the existing quantitative decision. The Safety state is read separately."""
    if (
        "R05" not in stop["causes"]
        or type(limits) is not RiskLimits
        or type(context) is not RiskContext
        or fact_digest(asdict(limits)) != original_policy_sha256
        or not is_digest_v1(original_observation_sha256)
        or not all(
            type(value) in {float, int} and math.isfinite(value)
            for value in asdict(context).values()
        )
        or context.now_epoch < stop["killed_at"]
        or context.market_data_age_seconds < 0
        or limits.max_session_loss_usd <= 0
    ):
        raise FilegateAuthorityError("FAULT_RISK_ORIGINAL_EVIDENCE_UNPROVEN")
    decision = evaluate_risk(limits, context)
    if not decision.allow:
        raise FilegateAuthorityError("FAULT_RISK_STILL_DENIED")
    return attest_filegate_owner_evidence_v1(
        role="CAUSE",
        cause="R05",
        stop=stop,
        evidence_sha256=fact_digest(
            {
                "original_policy_sha256": original_policy_sha256,
                "original_observation_sha256": original_observation_sha256,
                "original_decision": asdict(decision),
                "original_context": asdict(context),
            }
        ),
        observed_at=context.now_epoch,
        expires_at=expires_at,
        key=key,
    )
