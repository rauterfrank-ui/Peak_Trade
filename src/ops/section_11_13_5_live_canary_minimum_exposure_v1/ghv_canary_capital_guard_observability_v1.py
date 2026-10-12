"""Read-only GHV evidence for canary capital guard (AUTHORITY=NONE)."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

CANARY_AUTHORITY = "NONE"


def register_observed_surface_v1(
    *,
    producer_symbol: str,
    consumer_symbol: str,
    causal_relation: str,
    execution_domain: str,
    stage: str = "",
    discovery_reason: str,
    module: str = "",
    file: str = "",
    **_kwargs: Any,
) -> dict[str, Any]:
    """Local read-only GHV surface row (AUTHORITY=NONE; no Full-Core session coupling)."""
    return {
        "surface_id": f"OBS:{producer_symbol}->{consumer_symbol}@{stage or 'unknown'}",
        "module": module or "unknown",
        "symbol": producer_symbol,
        "file": file or "unknown",
        "consumer_symbol": consumer_symbol,
        "stage_if_known": stage,
        "execution_domain": execution_domain,
        "causal_relation": causal_relation,
        "discovery_reason": discovery_reason,
        "canary_authority": CANARY_AUTHORITY,
    }


from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.current_live_canary_capital_guard_v1 import (
    CanaryCapitalGuardEvaluationV1,
    CONTRACT_ID,
)

OWNER = "section_11_13_5_live_canary_minimum_exposure_v1.ghv_canary_capital_guard_observability_v1"

STAGE_CANARY_CAPITAL_GUARD_INPUT = "CANARY_CAPITAL_GUARD_INPUT"
STAGE_CANARY_CAPITAL_GUARD_LIMITS = "CANARY_CAPITAL_GUARD_LIMITS"
STAGE_CANARY_CAPITAL_GUARD_DECISION = "CANARY_CAPITAL_GUARD_DECISION"
STAGE_OWNER_PERMIT_ONE_SHOT = "OWNER_PERMIT_ONE_SHOT"
STAGE_SUBMIT_ATTEMPT = "SUBMIT_ATTEMPT"
STAGE_ACK_OR_UNKNOWN = "ACK_OR_UNKNOWN"
STAGE_FILL_OR_REJECT = "FILL_OR_REJECT"
STAGE_RECONCILIATION_TERMINAL = "RECONCILIATION_TERMINAL"
STAGE_ATOMIC_ONE_SHOT = "CANARY_ATOMIC_ONE_SHOT"


def record_canary_capital_guard_ghv_stage_v1(
    *,
    stage: str,
    session_id: str,
    plan_digest: str,
    guard_config_digest: str,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "stage": stage,
        "session_id": session_id,
        "plan_digest": plan_digest,
        "guard_config_digest": guard_config_digest,
        "canary_authority": CANARY_AUTHORITY,
        "guard_contract_id": CONTRACT_ID,
        "payload": dict(payload or {}),
    }
    register_observed_surface_v1(
        producer_symbol="current_live_canary_capital_guard_v1",
        consumer_symbol="ghv_canary_capital_guard_observability_v1",
        causal_relation="GATES_TRACED_STATE",
        execution_domain="PRODUCT_RUNTIME",
        stage=stage,
        discovery_reason="canary_capital_guard_forensic",
        module=OWNER,
        file="ghv_canary_capital_guard_observability_v1.py",
    )
    return row


def record_canary_atomic_one_shot_ghv_stage_v1(
    *,
    session_id: str,
    consumption_key: str,
    binding_digest: str,
    stage: str,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "stage": STAGE_ATOMIC_ONE_SHOT,
        "atomic_stage": stage,
        "session_id": session_id,
        "consumption_key": consumption_key,
        "binding_digest": binding_digest,
        "canary_authority": CANARY_AUTHORITY,
        "payload": dict(payload or {}),
        "authorization_permanently_consumed": True,
    }
    register_observed_surface_v1(
        producer_symbol="canary_capital_guard_atomic_one_shot_v1",
        consumer_symbol="ghv_canary_capital_guard_observability_v1",
        causal_relation="GATES_TRACED_STATE",
        execution_domain="PRODUCT_RUNTIME",
        stage=STAGE_ATOMIC_ONE_SHOT,
        discovery_reason="canary_atomic_one_shot_forensic",
        module=OWNER,
        file="ghv_canary_capital_guard_observability_v1.py",
    )
    return row


def build_canary_capital_guard_ghv_bundle_v1(
    *,
    session_id: str,
    guard_config: Mapping[str, Any],
    guard_input: Mapping[str, Any],
    evaluation: CanaryCapitalGuardEvaluationV1,
    extra_stages: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    limits_row = record_canary_capital_guard_ghv_stage_v1(
        stage=STAGE_CANARY_CAPITAL_GUARD_LIMITS,
        session_id=session_id,
        plan_digest=evaluation.plan_digest,
        guard_config_digest=evaluation.guard_config_digest,
        payload={"limits": dict(guard_config)},
    )
    input_row = record_canary_capital_guard_ghv_stage_v1(
        stage=STAGE_CANARY_CAPITAL_GUARD_INPUT,
        session_id=session_id,
        plan_digest=evaluation.plan_digest,
        guard_config_digest=evaluation.guard_config_digest,
        payload=dict(guard_input),
    )
    decision_row = record_canary_capital_guard_ghv_stage_v1(
        stage=STAGE_CANARY_CAPITAL_GUARD_DECISION,
        session_id=session_id,
        plan_digest=evaluation.plan_digest,
        guard_config_digest=evaluation.guard_config_digest,
        payload=evaluation.to_dict(),
    )
    stages = [input_row, limits_row, decision_row, *list(extra_stages)]
    return {
        "ghv_canary_capital_guard_stages": stages,
        "ghv_authority": CANARY_AUTHORITY,
        "contract_id": CONTRACT_ID,
    }
