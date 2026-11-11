"""Re-evaluate a stopped loss/position scope under the original risk gate."""

from dataclasses import asdict
import math

from src.ops.filegate_recovery_authority_v1 import (
    FilegateAuthorityError,
    FilegateRecoveryScopeV1,
    attest_filegate_owner_evidence_v1,
    is_digest_v1,
    require_filegate_loss_violation_v1,
)
from src.ops.gates.risk_gate import RiskContext, RiskDenyReason, RiskLimits, evaluate_risk
from src.ops.managed_filegate_v1 import ManagedFilegateV1
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest


def _evaluate_loss(limits, context, observation_sha256):
    if (
        type(limits) is not RiskLimits
        or type(context) is not RiskContext
        or not is_digest_v1(observation_sha256)
        or not all(
            type(value) in {float, int} and math.isfinite(value)
            for value in asdict(context).values()
        )
        or context.market_data_age_seconds < 0
        or type(limits.max_session_loss_usd) not in {float, int}
        or not math.isfinite(limits.max_session_loss_usd)
        or limits.max_session_loss_usd <= 0
    ):
        raise FilegateAuthorityError("FAULT_RISK_ORIGINAL_EVIDENCE_UNPROVEN")
    return evaluate_risk(limits, context)


def record_managed_session_loss_stop_v1(*, writer, scope, limits, context, observation_sha256):
    """Bind the original RiskGate denial to the Safety generation."""
    if type(writer) is not ManagedFilegateV1 or type(scope) is not FilegateRecoveryScopeV1:
        raise FilegateAuthorityError("FAULT_RISK_ORIGINAL_SCOPE_UNPROVEN")
    decision = _evaluate_loss(limits, context, observation_sha256)
    if decision.allow or decision.reason is not RiskDenyReason.LOSS_LIMIT:
        raise FilegateAuthorityError("FAULT_RISK_ORIGINAL_LOSS_DENIAL_UNPROVEN")
    violation = {
        "rule": "RISK_GATE_SESSION_LOSS_LIMIT_V1",
        "scope": scope.binding_v1(),
        "policy_sha256": fact_digest(asdict(limits)),
        "observation_sha256": observation_sha256,
    }
    return writer.kill_v1(
        cause="R05",
        reason="RISK_GATE_SESSION_LOSS_LIMIT",
        incident_id=fact_digest({"risk_violation": violation, "original_context": asdict(context)}),
        risk_violation=violation,
    )


def attest_managed_risk_recovery_v1(
    *,
    stop,
    scope,
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
        or type(scope) is not FilegateRecoveryScopeV1
        or scope.binding_v1() != stop["scope"]
    ):
        raise FilegateAuthorityError("FAULT_RISK_ORIGINAL_SCOPE_UNPROVEN")
    violation = require_filegate_loss_violation_v1(stop.get("risk_violation"), scope=stop["scope"])
    decision = _evaluate_loss(limits, context, original_observation_sha256)
    if (
        context.now_epoch < stop["killed_at"]
        or fact_digest(asdict(limits)) != original_policy_sha256
        or violation["policy_sha256"] != original_policy_sha256
        or violation["observation_sha256"] == original_observation_sha256
    ):
        raise FilegateAuthorityError("FAULT_RISK_ORIGINAL_EVIDENCE_UNPROVEN")
    if not decision.allow:
        raise FilegateAuthorityError("FAULT_RISK_STILL_DENIED")
    return attest_filegate_owner_evidence_v1(
        role="CAUSE",
        cause="R05",
        stop=stop,
        evidence_sha256=fact_digest(
            {
                "risk_violation": violation,
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
