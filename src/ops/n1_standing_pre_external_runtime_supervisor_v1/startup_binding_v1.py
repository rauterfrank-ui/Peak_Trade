"""N1 startup: inspect selection, observe the bound account, then admit binding."""

from dataclasses import dataclass, replace
from pathlib import Path
import time
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    CurrentProductive29PCap24BoundInstrumentProvenanceHandoffV1,
    acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
    inspect_selection_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
    HostAccountObservationV1,
    collect_host_account_observation_v1,
)


@dataclass(frozen=True)
class AccountBoundN1StartupV1:
    handoff: CurrentProductive29PCap24BoundInstrumentProvenanceHandoffV1
    observation: HostAccountObservationV1


@dataclass(frozen=True)
class PostCloseStartupRecoveryRequestV1:
    """The exact original invocation, retained by its caller across restart.

    Only an already CONSUMING/ACKED original transition can be recovered. This
    request cannot start a new membership publication or a new Core invocation.
    """

    original_invocation: Mapping[str, Any]


def recover_post_close_before_runtime_v1(
    request, *, current_bound, current_topology_root, budget_host
):
    """Join original ACK recovery to the actual host's fresh account observation."""
    from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
        checkpoint_root_for,
    )
    from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
        PostCloseContinuationReplayV1,
        ProductiveN1PostCloseContinuationV1,
        run_productive_full_autonomy_n5_runtime_orchestrator_v1,
    )
    from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1.post_close_continuation_v1 import (
        _read_receipt,
    )

    if not isinstance(request, PostCloseStartupRecoveryRequestV1) or budget_host.closed:
        raise ValueError("N1_START_POST_CLOSE_RECOVERY_CONTEXT_INVALID")
    invocation = dict(request.original_invocation)
    context = invocation.get("post_close_continuation")
    if not isinstance(context, ProductiveN1PostCloseContinuationV1):
        raise ValueError("N1_START_POST_CLOSE_ORIGINAL_CONTEXT_REQUIRED")
    writer = invocation["lane_assignment_writer"]
    writer.assert_held()
    topology = Path(invocation["topology_state_root_base"]).resolve()
    if Path(writer.state_root).resolve() != checkpoint_root_for(topology).resolve():
        raise ValueError("N1_START_POST_CLOSE_WRITER_SCOPE_MISMATCH")
    if Path(current_topology_root).resolve() != topology:
        raise ValueError("N1_START_POST_CLOSE_LANE_SCOPE_MISMATCH")
    old_owner = context.request.budget_owner
    expected_scope = old_owner.durable_scope_identity_v1()
    if (
        expected_scope["root"] != str((budget_host.root / "owner").resolve())
        or expected_scope["account"] != budget_host.expected_account_identity
        or context.identity.account_identity != budget_host.expected_account_identity
    ):
        raise ValueError("N1_START_POST_CLOSE_BUDGET_SCOPE_MISMATCH")
    close_ref = context.request.execution.envelope.envelope_digest
    if len(close_ref) != 64 or any(c not in "0123456789abcdef" for c in close_ref):
        raise ValueError("N1_START_POST_CLOSE_IDENTITY_INVALID")
    path = checkpoint_root_for(topology) / "post_close" / (close_ref + ".json")
    if not path.is_file():
        raise ValueError("N1_START_POST_CLOSE_EXISTING_RECEIPT_REQUIRED")
    record = _read_receipt(path)
    if record["phase"] not in {"CONSUMING", "ACKED"}:
        raise ValueError("N1_START_POST_CLOSE_ORIGINAL_CONTINUATION_REQUIRED")
    if record["bound_by_lane"] != {"LANE_1": current_bound.to_dict()}:
        raise ValueError("N1_START_POST_CLOSE_TARGET_GENERATION_MISMATCH")

    fresh = budget_host.observe_v1({"LANE_1": current_bound})
    if fresh.pending_orders or any(
        row.get("matched") is not True
        or row.get("decision", {}).get("reconciliation_complete") is not True
        for row in fresh.execution_reconciliation.values()
    ):
        raise ValueError("N1_START_POST_CLOSE_EXECUTION_RECONCILIATION_REQUIRED")
    invocation["portfolio_budget_owner"] = budget_host.owner
    invocation["post_close_continuation"] = replace(
        context, request=replace(context.request, budget_owner=budget_host.owner)
    )
    replay = run_productive_full_autonomy_n5_runtime_orchestrator_v1(**invocation)
    if not isinstance(replay, PostCloseContinuationReplayV1):
        raise ValueError("N1_START_POST_CLOSE_HISTORICAL_REPLAY_REQUIRED")
    return {
        "scope": "ORIGINAL_POST_CLOSE_ACK_AND_FRESH_ACCOUNT_OBSERVATION",
        "trigger": "STANDING_SUPERVISOR_STARTUP",
        "handoff_binding_digest": replay.receipt["binding_digest"],
        "consumer_completion_digest": replay.receipt.get("consumer_completion_digest"),
        "phase": replay.receipt["phase"],
        "consumed": replay.receipt["consumed"],
        "budget_scope": budget_host.owner.durable_scope_identity_v1(),
        "fresh_account_observation_digest": fresh.observed.digest(),
        "budget_admitted": budget_host.owner.budget_state_v1().admitted,
        "runtime_admission_granted": False,
        "post_allowed": False,
    }


def acquire_account_bound_n1_startup_v1(
    *,
    productivity_root: Path,
    repository_sha: str,
    binding_epoch: str,
    expected_account_identity: str,
    session_id: str,
    private_rest_fetch,
    expected_bound=None,
    clock=time.time,
) -> AccountBoundN1StartupV1:
    if not isinstance(expected_account_identity, str) or not expected_account_identity.strip():
        raise ValueError("N1_START_ACCOUNT_IDENTITY_REQUIRED")
    inspected = inspect_selection_v1(
        productivity_root=productivity_root,
        repository_sha=repository_sha,
        binding_epoch=binding_epoch,
    )
    selection = inspected.selection
    identity = {
        "instrument_id": selection.instrument_id,
        "venue_native_id": selection.venue_native_id,
        "selection_id": selection.selection_id,
        "selection_integrity_digest": selection.integrity_digest,
        "ranking_snapshot_id": inspected.ranking.ranking_snapshot_id,
        "ranking_integrity_digest": inspected.ranking.integrity_digest,
        "universe_snapshot_id": inspected.universe.snapshot_id,
    }
    if expected_bound is not None and any(
        str(getattr(expected_bound, name, None)) != str(value) for name, value in identity.items()
    ):
        raise ValueError("N1_START_SELECTION_BINDING_MISMATCH")
    observation = collect_host_account_observation_v1(
        private_rest_fetch=private_rest_fetch,
        instrument_ids_by_native_id={selection.venue_native_id: selection.instrument_id},
        session_id=session_id,
        clock=clock,
        expected_account=expected_account_identity,
    )
    if observation.pending_orders:
        raise ValueError("N1_START_PENDING_ORDERS_UNRESOLVED")
    handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
        productivity_root=productivity_root,
        repository_sha=repository_sha,
        binding_epoch=binding_epoch,
        session_id=session_id,
        observed_portfolio=observation.observed,
        expected_selection_integrity_digest=selection.integrity_digest,
        observation_now_unix=clock(),
    )
    if (
        handoff.selection_id != selection.selection_id
        or handoff.selection_integrity_digest != selection.integrity_digest
    ):
        raise ValueError("N1_START_SELECTION_CHANGED_DURING_OBSERVATION")
    return AccountBoundN1StartupV1(handoff, observation)
