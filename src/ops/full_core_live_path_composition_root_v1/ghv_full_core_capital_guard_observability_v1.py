"""Read-only GHV evidence for Full-Core capital guard join (AUTHORITY=NONE)."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.ops.full_core_live_path_composition_root_v1.current_full_core_capital_guard_v1 import (
    CONTRACT_ID,
    FullCoreCapitalGuardEvaluationV1,
)

GHV_AUTHORITY = "NONE"
OWNER = "full_core_live_path_composition_root_v1.ghv_full_core_capital_guard_observability_v1"

STAGE_CURRENT_DECISION_BOUND = "CURRENT_DECISION_BOUND"
STAGE_VENUE_PLAN_BOUND = "VENUE_PLAN_BOUND"
STAGE_FINAL_ENVELOPE_BOUND = "FINAL_ENVELOPE_BOUND"
STAGE_PRE_EXTERNAL_REACHED = "PRE_EXTERNAL_REACHED"
STAGE_CAPITAL_GUARD_INPUT = "CAPITAL_GUARD_INPUT"
STAGE_CAPITAL_GUARD_LIMITS = "CAPITAL_GUARD_LIMITS"
STAGE_CAPITAL_GUARD_DECISION = "CAPITAL_GUARD_DECISION"
STAGE_ONE_SHOT_RESERVATION = "ONE_SHOT_RESERVATION"
STAGE_SUBMIT_BOUNDARY = "SUBMIT_BOUNDARY"
STAGE_SUBMIT_ACK_OR_UNKNOWN = "SUBMIT_ACK_OR_UNKNOWN"
STAGE_RECONCILIATION_STATE = "RECONCILIATION_STATE"


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
        "ghv_authority": GHV_AUTHORITY,
    }


def record_full_core_capital_guard_ghv_stage_v1(
    *,
    stage: str,
    session_id: str,
    binding_digest: str,
    guard_config_digest: str,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "stage": stage,
        "session_id": session_id,
        "binding_digest": binding_digest,
        "guard_config_digest": guard_config_digest,
        "ghv_authority": GHV_AUTHORITY,
        "guard_contract_id": CONTRACT_ID,
        "payload": dict(payload or {}),
    }
    register_observed_surface_v1(
        producer_symbol="full_core_pre_post_capital_guard_join_v1",
        consumer_symbol="ghv_full_core_capital_guard_observability_v1",
        causal_relation="GATES_TRACED_STATE",
        execution_domain="PRODUCT_RUNTIME",
        stage=stage,
        discovery_reason="full_core_capital_guard_forensic",
        module=OWNER,
        file="ghv_full_core_capital_guard_observability_v1.py",
    )
    return row


def build_full_core_capital_guard_ghv_bundle_v1(
    *,
    session_id: str,
    guard_config: Mapping[str, Any],
    guard_input: Mapping[str, Any],
    evaluation: FullCoreCapitalGuardEvaluationV1 | None,
    stages_observed: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    binding_digest = str(guard_input.get("binding_digest") or "")
    cfg_digest = str(
        guard_config.get("config_digest") or evaluation.guard_config_digest if evaluation else ""
    )
    rows: list[dict[str, Any]] = []
    for stage_row in stages_observed:
        rows.append(dict(stage_row))
    if evaluation is not None:
        rows.append(
            record_full_core_capital_guard_ghv_stage_v1(
                stage=STAGE_CAPITAL_GUARD_LIMITS,
                session_id=session_id,
                binding_digest=binding_digest,
                guard_config_digest=cfg_digest,
                payload={"limits": dict(guard_config)},
            )
        )
        rows.append(
            record_full_core_capital_guard_ghv_stage_v1(
                stage=STAGE_CAPITAL_GUARD_INPUT,
                session_id=session_id,
                binding_digest=binding_digest,
                guard_config_digest=cfg_digest,
                payload=dict(guard_input),
            )
        )
        rows.append(
            record_full_core_capital_guard_ghv_stage_v1(
                stage=STAGE_CAPITAL_GUARD_DECISION,
                session_id=session_id,
                binding_digest=binding_digest,
                guard_config_digest=cfg_digest,
                payload=evaluation.to_dict(),
            )
        )
    return {
        "ghv_full_core_capital_guard_stages": rows,
        "ghv_authority": GHV_AUTHORITY,
        "contract_id": CONTRACT_ID,
    }
