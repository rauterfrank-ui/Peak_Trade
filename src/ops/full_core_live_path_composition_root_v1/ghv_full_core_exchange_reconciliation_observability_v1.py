"""GHV flight-recorder stages for Full-Core exchange reconciliation (AUTHORITY=NONE)."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.ops.full_core_live_path_composition_root_v1.ghv_full_core_capital_guard_observability_v1 import (
    GHV_AUTHORITY,
    register_observed_surface_v1,
)

CONTRACT_ID = "GHV_FULL_CORE_EXCHANGE_RECONCILIATION_OBSERVABILITY_V1"
OWNER = (
    "full_core_live_path_composition_root_v1.ghv_full_core_exchange_reconciliation_observability_v1"
)

STAGE_SUBMIT_OUTCOME = "SUBMIT_OUTCOME"
STAGE_RECONCILIATION_SNAPSHOT = "RECONCILIATION_SNAPSHOT"
STAGE_RECONCILIATION_DECISION = "RECONCILIATION_DECISION"
STAGE_DURABLE_RECOVERY_STATE = "DURABLE_RECOVERY_STATE"


def record_full_core_exchange_reconciliation_ghv_stage_v1(
    *,
    stage: str,
    session_id: str,
    identity_digest: str,
    payload: Mapping[str, Any] | None = None,
    simulation_mode: str = "OFFLINE_SIMULATED",
) -> dict[str, Any]:
    row = {
        "stage": stage,
        "session_id": session_id,
        "identity_digest": identity_digest,
        "ghv_authority": GHV_AUTHORITY,
        "simulation_mode": simulation_mode,
        "payload": dict(payload or {}),
        "contract_id": CONTRACT_ID,
    }
    register_observed_surface_v1(
        producer_symbol="full_core_exchange_reconciliation_integration_v1",
        consumer_symbol="ghv_full_core_exchange_reconciliation_observability_v1",
        causal_relation="GATES_TRACED_STATE",
        execution_domain="OFFLINE_SIMULATED",
        stage=stage,
        discovery_reason="full_core_exchange_reconciliation_forensic",
        module=OWNER,
        file="ghv_full_core_exchange_reconciliation_observability_v1.py",
    )
    return row


def build_full_core_exchange_reconciliation_ghv_bundle_v1(
    *,
    session_id: str,
    stages_observed: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "ghv_full_core_exchange_reconciliation_stages": [dict(s) for s in stages_observed],
        "ghv_authority": GHV_AUTHORITY,
        "contract_id": CONTRACT_ID,
    }


__all__ = [
    "CONTRACT_ID",
    "STAGE_DURABLE_RECOVERY_STATE",
    "STAGE_RECONCILIATION_DECISION",
    "STAGE_RECONCILIATION_SNAPSHOT",
    "STAGE_SUBMIT_OUTCOME",
    "build_full_core_exchange_reconciliation_ghv_bundle_v1",
    "record_full_core_exchange_reconciliation_ghv_stage_v1",
]
