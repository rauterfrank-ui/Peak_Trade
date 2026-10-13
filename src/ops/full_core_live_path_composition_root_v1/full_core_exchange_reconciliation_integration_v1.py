"""Full-Core offline exchange reconciliation handoff (POST disabled, provider OFFLINE_STUB).

PRODUCTION provider remains unwired (OWNER_PRIVATE_GET_GO=NOT_GRANTED).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    FullCoreAuthorizationBindingV1,
    atomic_mark_halted_unresolved_v1,
    atomic_mark_reconciliation_pending_v1,
    atomic_mark_terminal_reconciled_v1,
    load_full_core_atomic_authorization_state_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
    fetch_offline_reconciliation_snapshot_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    OUTCOME_HALTED_UNRESOLVED,
    RECONCILIATION_PROVIDER_OFFLINE_STUB,
    FullCoreExchangeReconciliationDecisionV1,
    FullCoreExchangeReconciliationIdentityV1,
    LocalSubmitOutcome,
    adjudicate_full_core_exchange_reconciliation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_core_exchange_reconciliation_observability_v1 import (
    STAGE_DURABLE_RECOVERY_STATE,
    STAGE_RECONCILIATION_DECISION,
    STAGE_RECONCILIATION_SNAPSHOT,
    STAGE_SUBMIT_OUTCOME,
    build_full_core_exchange_reconciliation_ghv_bundle_v1,
    record_full_core_exchange_reconciliation_ghv_stage_v1,
)

CONTRACT_ID = "FULL_CORE_EXCHANGE_RECONCILIATION_INTEGRATION_V1"
PRODUCTION_PROVIDER_WIRING = "NOT_AUTHORIZED"
POST_COUNT = 0
PRIVATE_GET_COUNT = 0
NETWORK_REQUEST_COUNT = 0


@dataclass(frozen=True)
class FullCoreOfflineReconciliationRunResultV1:
    decision: FullCoreExchangeReconciliationDecisionV1
    snapshot: Mapping[str, Any]
    ghv_bundle: dict[str, Any]
    atomic_state_after: str | None
    post_count: int
    provider: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.to_dict(),
            "snapshot": dict(self.snapshot),
            "ghv_bundle": dict(self.ghv_bundle),
            "atomic_state_after": self.atomic_state_after,
            "post_count": self.post_count,
            "provider": self.provider,
            "contract_id": CONTRACT_ID,
        }


def identity_from_full_core_binding_v1(
    binding: FullCoreAuthorizationBindingV1,
    *,
    decision_outcome: str,
    venue_plan_identity: str,
    envelope_identity: str,
    submit_attempt_id: str,
    local_durable_state_version: str,
    exchange_ord_id: str | None = None,
) -> FullCoreExchangeReconciliationIdentityV1:
    return FullCoreExchangeReconciliationIdentityV1(
        canonical_decision_id=binding.canonical_decision_id,
        decision_outcome=decision_outcome,
        selected_side=binding.selected_direction,
        instrument_id=binding.instrument_id,
        native_id=binding.native_id,
        account_identity=binding.account_scope,
        execution_environment=binding.environment,
        venue="OKX",
        venue_plan_identity=venue_plan_identity,
        venue_plan_digest=binding.venue_plan_digest,
        envelope_identity=envelope_identity,
        envelope_digest=binding.envelope_digest,
        final_quantity=binding.final_quantity,
        quantity_unit="CONTRACTS",
        order_type=binding.order_type,
        order_price=binding.order_price,
        clordid=binding.clordid,
        exchange_ord_id=exchange_ord_id,
        owner_go=binding.owner_go,
        atomic_consumption_key=binding.consumption_key(),
        submit_attempt_id=submit_attempt_id,
        local_durable_state_version=local_durable_state_version,
    )


def _apply_atomic_recommendation_v1(
    *,
    state_dir: Path,
    binding: FullCoreAuthorizationBindingV1,
    decision: FullCoreExchangeReconciliationDecisionV1,
    apply_durable: bool,
) -> str | None:
    if not apply_durable:
        return decision.recommended_atomic_state
    rec = decision.recommended_atomic_state
    if rec == "TERMINAL_RECONCILED":
        canary = binding.to_canary_atomic_binding_v1()
        current = load_full_core_atomic_authorization_state_v1(
            state_dir=state_dir, consumption_key=binding.consumption_key()
        )
        if current is not None and current.state == "SUBMIT_MAY_HAVE_OCCURRED":
            atomic_mark_reconciliation_pending_v1(state_dir=state_dir, binding=canary)
        st = atomic_mark_terminal_reconciled_v1(state_dir=state_dir, binding=canary)
        return st.state
    if rec == "RECONCILIATION_PENDING":
        st = atomic_mark_reconciliation_pending_v1(
            state_dir=state_dir, binding=binding.to_canary_atomic_binding_v1()
        )
        return st.state
    if rec == "HALTED_UNRESOLVED" or decision.outcome == OUTCOME_HALTED_UNRESOLVED:
        st = atomic_mark_halted_unresolved_v1(
            state_dir=state_dir, binding=binding.to_canary_atomic_binding_v1()
        )
        return st.state
    return rec


def run_full_core_offline_exchange_reconciliation_v1(
    *,
    identity: FullCoreExchangeReconciliationIdentityV1,
    binding: FullCoreAuthorizationBindingV1,
    fixture: OfflineExchangeFixtureV1,
    local_submit_outcome: LocalSubmitOutcome,
    state_dir: Path | None = None,
    apply_durable_state: bool = False,
    proven_never_submitted: bool = False,
) -> FullCoreOfflineReconciliationRunResultV1:
    """Offline reconciliation cycle: snapshot → adjudicate → optional durable update → GHV."""
    stages: list[dict[str, Any]] = []
    digest = identity.identity_digest()
    session = binding.session_id

    stages.append(
        record_full_core_exchange_reconciliation_ghv_stage_v1(
            stage=STAGE_SUBMIT_OUTCOME,
            session_id=session,
            identity_digest=digest,
            payload={
                "local_submit_outcome": local_submit_outcome.value,
                "post_count": POST_COUNT,
                "simulation_mode": "OFFLINE_SIMULATED",
            },
        )
    )

    snapshot = fetch_offline_reconciliation_snapshot_v1(identity=identity, fixture=fixture)
    snap_dict = snapshot.to_dict()
    stages.append(
        record_full_core_exchange_reconciliation_ghv_stage_v1(
            stage=STAGE_RECONCILIATION_SNAPSHOT,
            session_id=session,
            identity_digest=digest,
            payload=snap_dict,
        )
    )

    decision = adjudicate_full_core_exchange_reconciliation_v1(
        identity=identity,
        snapshot=snapshot,
        local_submit_outcome=local_submit_outcome,
        proven_never_submitted=proven_never_submitted,
    )
    stages.append(
        record_full_core_exchange_reconciliation_ghv_stage_v1(
            stage=STAGE_RECONCILIATION_DECISION,
            session_id=session,
            identity_digest=digest,
            payload=decision.to_dict(),
        )
    )

    atomic_after: str | None = None
    if state_dir is not None:
        atomic_after = _apply_atomic_recommendation_v1(
            state_dir=state_dir,
            binding=binding,
            decision=decision,
            apply_durable=apply_durable_state,
        )
        stages.append(
            record_full_core_exchange_reconciliation_ghv_stage_v1(
                stage=STAGE_DURABLE_RECOVERY_STATE,
                session_id=session,
                identity_digest=digest,
                payload={"atomic_state_after": atomic_after},
            )
        )

    ghv = build_full_core_exchange_reconciliation_ghv_bundle_v1(
        session_id=session,
        stages_observed=stages,
    )

    return FullCoreOfflineReconciliationRunResultV1(
        decision=decision,
        snapshot=snap_dict,
        ghv_bundle=ghv,
        atomic_state_after=atomic_after,
        post_count=POST_COUNT,
        provider=RECONCILIATION_PROVIDER_OFFLINE_STUB,
    )


__all__ = [
    "CONTRACT_ID",
    "POST_COUNT",
    "PRIVATE_GET_COUNT",
    "NETWORK_REQUEST_COUNT",
    "PRODUCTION_PROVIDER_WIRING",
    "FullCoreOfflineReconciliationRunResultV1",
    "identity_from_full_core_binding_v1",
    "run_full_core_offline_exchange_reconciliation_v1",
]
