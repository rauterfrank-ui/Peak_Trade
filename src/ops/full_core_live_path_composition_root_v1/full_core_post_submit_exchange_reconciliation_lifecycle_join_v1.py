"""Full-Core post-submit lifecycle → exchange reconciliation → atomic recovery join.

Connects Cap 11.1 / §11.2.1.DW post-submit join output to the existing offline or
injected-OKX reconciliation pipeline and optional durable atomic recovery updates.

No productive network wiring. `PRODUCTION_PROVIDER_WIRING=NOT_AUTHORIZED`.
Does not POST. Does not resubmit. Does not release capital without proven terminal
reconciliation.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    POST_SUBMIT_RECON,
    UNKNOWN_OUTCOME_RECON,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FullCoreFreshPretradeGetTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    FullCoreAuthorizationBindingV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_integration_v1 import (
    POST_COUNT,
    PRIVATE_GET_COUNT,
    PRODUCTION_PROVIDER_WIRING,
    FullCoreOfflineReconciliationRunResultV1,
    identity_from_full_core_binding_v1,
    run_full_core_offline_exchange_reconciliation_v1,
    run_full_core_okx_injected_exchange_reconciliation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
    OkxReadOnlyReconciliationQueryOptionsV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    OUTCOME_CONFIRMED_CANCELED,
    OUTCOME_CONFIRMED_FILLED,
    OUTCOME_CONFIRMED_OPEN,
    OUTCOME_CONFIRMED_PARTIALLY_FILLED,
    OUTCOME_CONFIRMED_REJECTED,
    OUTCOME_HALTED_UNRESOLVED,
    FullCoreExchangeReconciliationDecisionV1,
    LocalSubmitOutcome,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
    ACKNOWLEDGED,
    REJECTED,
    UNKNOWN,
    FullCorePostSubmitJoinResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_core_exchange_reconciliation_observability_v1 import (
    STAGE_POST_SUBMIT_LIFECYCLE_JOIN,
    build_full_core_exchange_reconciliation_ghv_bundle_v1,
    record_full_core_exchange_reconciliation_ghv_stage_v1,
)

CONTRACT_ID = "FULL_CORE_POST_SUBMIT_EXCHANGE_RECONCILIATION_LIFECYCLE_JOIN_V1"
NETWORK_REQUEST_COUNT = 0
REAL_ORDER_COUNT = 0

_TERMINAL_CONFIRMED_OUTCOMES = frozenset(
    {
        OUTCOME_CONFIRMED_FILLED,
        OUTCOME_CONFIRMED_OPEN,
        OUTCOME_CONFIRMED_PARTIALLY_FILLED,
        OUTCOME_CONFIRMED_CANCELED,
        OUTCOME_CONFIRMED_REJECTED,
    }
)


class FullCorePostSubmitLifecycleReconciliationJoinError(RuntimeError):
    """Fail-closed lifecycle ↔ reconciliation join violation."""


@dataclass(frozen=True)
class FullCorePostSubmitLifecycleReconciliationJoinResultV1:
    post_submit_join: FullCorePostSubmitJoinResultV1
    local_submit_outcome: LocalSubmitOutcome
    reconciliation: FullCoreOfflineReconciliationRunResultV1
    ghv_forward_join: Literal["PASS", "FAIL"]
    ghv_reverse_join: Literal["PASS", "FAIL"]
    provider_mode: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": CONTRACT_ID,
            "post_submit_join": {
                "typed_outcome": self.post_submit_join.typed_outcome,
                "lifecycle_state": self.post_submit_join.lifecycle_state,
                "recon_class": self.post_submit_join.recon_class,
                "reason": self.post_submit_join.reason,
            },
            "local_submit_outcome": self.local_submit_outcome.value,
            "reconciliation_outcome": self.reconciliation.decision.outcome,
            "atomic_state_after": self.reconciliation.atomic_state_after,
            "ghv_forward_join": self.ghv_forward_join,
            "ghv_reverse_join": self.ghv_reverse_join,
            "provider_mode": self.provider_mode,
            "post_count": POST_COUNT,
            "production_provider_wiring": PRODUCTION_PROVIDER_WIRING,
        }


def local_submit_outcome_from_post_submit_join_v1(
    join: FullCorePostSubmitJoinResultV1,
) -> LocalSubmitOutcome:
    """Map Cap-11.1 post-submit join to reconciliation-local submit outcome."""

    if join.post_attempted is not True:
        return LocalSubmitOutcome.NOT_SUBMITTED
    outcome = str(join.typed_outcome or "").strip().upper()
    reason = str(join.reason or "").upper()
    if outcome == ACKNOWLEDGED:
        return LocalSubmitOutcome.TRANSPORT_ACK
    if outcome == REJECTED:
        return LocalSubmitOutcome.TRANSPORT_REJECT
    if outcome == UNKNOWN:
        if "TIMEOUT" in reason:
            return LocalSubmitOutcome.TRANSPORT_TIMEOUT
        return LocalSubmitOutcome.TRANSPORT_UNKNOWN
    return LocalSubmitOutcome.TRANSPORT_UNKNOWN


def _assert_post_submit_join_admits_reconciliation_v1(join: FullCorePostSubmitJoinResultV1) -> None:
    if join.resubmit_allowed is True:
        raise FullCorePostSubmitLifecycleReconciliationJoinError("AUTOMATIC_RESUBMIT_FORBIDDEN")
    if join.blind_retry_forbidden is not True:
        raise FullCorePostSubmitLifecycleReconciliationJoinError(
            "BLIND_RETRY_MUST_REMAIN_FORBIDDEN"
        )
    recon = str(join.recon_class or "")
    if recon not in {POST_SUBMIT_RECON, UNKNOWN_OUTCOME_RECON}:
        raise FullCorePostSubmitLifecycleReconciliationJoinError(
            "POST_SUBMIT_JOIN_RECON_CLASS_NOT_RECONCILABLE"
        )


def verify_ghv_forward_join_v1(
    *,
    join: FullCorePostSubmitJoinResultV1,
    local_submit_outcome: LocalSubmitOutcome,
    decision: FullCoreExchangeReconciliationDecisionV1,
) -> bool:
    """Forward: post-submit join classification must map to the local submit outcome used."""

    expected = local_submit_outcome_from_post_submit_join_v1(join)
    if local_submit_outcome is not expected:
        return False
    if join.typed_outcome == UNKNOWN and local_submit_outcome not in {
        LocalSubmitOutcome.TRANSPORT_TIMEOUT,
        LocalSubmitOutcome.TRANSPORT_UNKNOWN,
    }:
        return False
    if (
        join.typed_outcome == ACKNOWLEDGED
        and local_submit_outcome is not LocalSubmitOutcome.TRANSPORT_ACK
    ):
        return False
    if decision.recommended_atomic_state == "TERMINAL_RECONCILED":
        if join.typed_outcome == UNKNOWN and decision.outcome in _TERMINAL_CONFIRMED_OUTCOMES:
            return False
    return True


def verify_ghv_reverse_join_v1(
    *,
    join: FullCorePostSubmitJoinResultV1,
    local_submit_outcome: LocalSubmitOutcome,
    decision: FullCoreExchangeReconciliationDecisionV1,
) -> bool:
    """Reverse: reconciliation must not silently collapse UNKNOWN submit into proven terminal."""

    if join.typed_outcome == UNKNOWN:
        if decision.outcome in _TERMINAL_CONFIRMED_OUTCOMES and local_submit_outcome in {
            LocalSubmitOutcome.TRANSPORT_TIMEOUT,
            LocalSubmitOutcome.TRANSPORT_UNKNOWN,
        }:
            return False
        if decision.outcome == OUTCOME_HALTED_UNRESOLVED:
            return True
        if decision.recommended_atomic_state in {"RECONCILIATION_PENDING", "HALTED_UNRESOLVED"}:
            return True
        if decision.outcome in _TERMINAL_CONFIRMED_OUTCOMES:
            return False
    if join.typed_outcome == REJECTED and decision.outcome == OUTCOME_CONFIRMED_FILLED:
        return False
    return True


def run_full_core_post_submit_lifecycle_reconciliation_join_v1(
    *,
    post_submit_join: FullCorePostSubmitJoinResultV1,
    binding: FullCoreAuthorizationBindingV1,
    decision_outcome: str,
    venue_plan_identity: str,
    envelope_identity: str,
    submit_attempt_id: str,
    local_durable_state_version: str,
    offline_fixture: OfflineExchangeFixtureV1 | None = None,
    read_only_get_transport: FullCoreFreshPretradeGetTransportV1 | None = None,
    pretrade_decision_id: str | None = None,
    query_options: OkxReadOnlyReconciliationQueryOptionsV1 | None = None,
    state_dir: Path | None = None,
    apply_durable_state: bool = False,
    proven_never_submitted: bool = False,
) -> FullCorePostSubmitLifecycleReconciliationJoinResultV1:
    """Run exchange reconciliation immediately after a post-submit lifecycle join."""

    _assert_post_submit_join_admits_reconciliation_v1(post_submit_join)
    has_offline = offline_fixture is not None
    has_okx = read_only_get_transport is not None
    if has_offline == has_okx:
        raise FullCorePostSubmitLifecycleReconciliationJoinError(
            "EXACTLY_ONE_RECONCILIATION_PROVIDER_REQUIRED"
        )
    if has_okx and not str(pretrade_decision_id or "").strip():
        raise FullCorePostSubmitLifecycleReconciliationJoinError("PRETRADE_DECISION_ID_REQUIRED")

    local_outcome = local_submit_outcome_from_post_submit_join_v1(post_submit_join)
    exchange_ord_id = (
        post_submit_join.venue_order_id if post_submit_join.typed_outcome == ACKNOWLEDGED else None
    )
    identity = identity_from_full_core_binding_v1(
        binding,
        decision_outcome=decision_outcome,
        venue_plan_identity=venue_plan_identity,
        envelope_identity=envelope_identity,
        submit_attempt_id=submit_attempt_id,
        local_durable_state_version=local_durable_state_version,
        exchange_ord_id=exchange_ord_id or None,
    )

    if has_offline:
        recon = run_full_core_offline_exchange_reconciliation_v1(
            identity=identity,
            binding=binding,
            fixture=offline_fixture or OfflineExchangeFixtureV1(),
            local_submit_outcome=local_outcome,
            state_dir=state_dir,
            apply_durable_state=apply_durable_state,
            proven_never_submitted=proven_never_submitted,
        )
        provider_mode = "OFFLINE_STUB"
        simulation_mode = "OFFLINE_SIMULATED"
    else:
        recon = run_full_core_okx_injected_exchange_reconciliation_v1(
            identity=identity,
            binding=binding,
            read_only_get_transport=read_only_get_transport,  # type: ignore[arg-type]
            pretrade_decision_id=str(pretrade_decision_id),
            local_submit_outcome=local_outcome,
            query_options=query_options,
            state_dir=state_dir,
            apply_durable_state=apply_durable_state,
            proven_never_submitted=proven_never_submitted,
        )
        provider_mode = "OKX_INJECTED_READ_ONLY"
        simulation_mode = "OKX_TRANSPORT_INJECTED"

    join_stage = record_full_core_exchange_reconciliation_ghv_stage_v1(
        stage=STAGE_POST_SUBMIT_LIFECYCLE_JOIN,
        session_id=binding.session_id,
        identity_digest=identity.identity_digest(),
        payload={
            "typed_outcome": post_submit_join.typed_outcome,
            "recon_class": post_submit_join.recon_class,
            "local_submit_outcome": local_outcome.value,
            "lifecycle_state": post_submit_join.lifecycle_state,
        },
        simulation_mode=simulation_mode,
    )
    prior_stages = list(recon.ghv_bundle.get("ghv_full_core_exchange_reconciliation_stages") or [])
    merged_ghv = build_full_core_exchange_reconciliation_ghv_bundle_v1(
        session_id=binding.session_id,
        stages_observed=[join_stage, *prior_stages],
    )
    recon = FullCoreOfflineReconciliationRunResultV1(
        decision=recon.decision,
        snapshot=recon.snapshot,
        ghv_bundle=merged_ghv,
        atomic_state_after=recon.atomic_state_after,
        post_count=recon.post_count,
        provider=recon.provider,
    )

    forward = verify_ghv_forward_join_v1(
        join=post_submit_join,
        local_submit_outcome=local_outcome,
        decision=recon.decision,
    )
    reverse = verify_ghv_reverse_join_v1(
        join=post_submit_join,
        local_submit_outcome=local_outcome,
        decision=recon.decision,
    )
    return FullCorePostSubmitLifecycleReconciliationJoinResultV1(
        post_submit_join=post_submit_join,
        local_submit_outcome=local_outcome,
        reconciliation=recon,
        ghv_forward_join="PASS" if forward else "FAIL",
        ghv_reverse_join="PASS" if reverse else "FAIL",
        provider_mode=provider_mode,
    )


__all__ = [
    "CONTRACT_ID",
    "NETWORK_REQUEST_COUNT",
    "POST_COUNT",
    "PRIVATE_GET_COUNT",
    "PRODUCTION_PROVIDER_WIRING",
    "REAL_ORDER_COUNT",
    "FullCorePostSubmitLifecycleReconciliationJoinError",
    "FullCorePostSubmitLifecycleReconciliationJoinResultV1",
    "local_submit_outcome_from_post_submit_join_v1",
    "run_full_core_post_submit_lifecycle_reconciliation_join_v1",
    "verify_ghv_forward_join_v1",
    "verify_ghv_reverse_join_v1",
]
