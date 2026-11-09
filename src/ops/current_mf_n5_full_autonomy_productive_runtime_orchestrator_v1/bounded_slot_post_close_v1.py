"""Bounded slot sequencing through the original close, selection and host owners."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import math

from .post_close_continuation_v1 import (
    ProductiveN1PostCloseContinuationV1,
    PostCloseContinuationReplayV1,
    _digest,
    _fail,
    _read_receipt,
    _write_receipt,
    _read_original_consumer_completion,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
    PortfolioBudgetHostV1,
    HostBudgetRecoveryContextV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    BoundedSlotEntryBudgetV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from src.ops.single_selected_future_policy_v1.persistence_v1 import load_and_validate_selection_v1
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
    checkpoint_root_for,
    recover_durable_lane_assignment_v1,
    RECOVERY_MODE_RESTART,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_close_feedback_v1 import (
    PostCloseFeedbackRequestV1,
    compose_post_close_feedback_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    FullCorePostSubmitLifecycleReconciliationJoinResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    FullCoreExchangeReconciliationIdentityV1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import NUMERIC_EQUITY_TTL_SECONDS
from src.ops.mf_membership_selector_and_rotation_runtime_contract_v1 import (
    persist_selector_result_v1,
)

SCHEMA = "bounded_slot_post_close_continuation.v1"


@dataclass(frozen=True, kw_only=True)
class BoundedSlotPostCloseContinuationV1(ProductiveN1PostCloseContinuationV1):
    host: PortfolioBudgetHostV1


def original_bounded_host_v1(owner, recovery):
    """Recognize only the existing simulated host and its immutable slot policy."""
    if owner is None or not isinstance(owner.entry_budget_policy_v1(), BoundedSlotEntryBudgetV1):
        return None
    if (
        not isinstance(recovery, HostBudgetRecoveryContextV1)
        or recovery.host.owner is not owner
        or recovery.host.closed
        or recovery.host.execution_environment != "INTERNAL_SIMULATED_EXECUTION"
    ):
        _fail("BOUNDED_CLOSE_ORIGINAL_SIMULATED_HOST_REQUIRED")
    return recovery.host


def retained_bounds_v1(record):
    return {
        lane: BoundInstrumentV1(**raw)
        for lane, raw in record.get("retained_bound_by_lane", {}).items()
    }


def read_group_completion_v1(record, *, recover=False):
    return {
        lane: _read_original_consumer_completion(
            {**record, "bound_by_lane": {lane: bound}}, recover=recover
        )
        for lane, bound in record["bound_by_lane"].items()
    }


def prepare_v1(
    context,
    *,
    membership,
    ranking_snapshot,
    topology_root,
    writer,
    owner,
    repository_sha,
    origin_main_sha,
    observed_unix,
    cap24,
    target_cardinality,
    cycle_kwargs,
):
    writer.assert_held()
    if Path(writer.state_root).resolve() != checkpoint_root_for(topology_root).resolve():
        _fail("POST_CLOSE_WRITER_SCOPE_MISMATCH")
    request = context.request
    if (
        not isinstance(request, PostCloseFeedbackRequestV1)
        or request.ranking is None
        or not isinstance(context.lifecycle, FullCorePostSubmitLifecycleReconciliationJoinResultV1)
        or not isinstance(context.identity, FullCoreExchangeReconciliationIdentityV1)
    ):
        _fail("POST_CLOSE_ORIGINAL_REVIEW_REQUIRED")
    if (
        not isinstance(context.host, PortfolioBudgetHostV1)
        or owner is None
        or owner is not context.host.owner
        or request.budget_owner is not owner
        or not isinstance(owner.entry_budget_policy_v1(), BoundedSlotEntryBudgetV1)
        or context.host.execution_environment != "INTERNAL_SIMULATED_EXECUTION"
        or not owner.budget_state_v1().durable_state_enabled
        or type(target_cardinality) is not int
        or not 1 <= target_cardinality <= 5
        or len(membership.ordered_instrument_ids) != target_cardinality
    ):
        _fail("BOUNDED_CLOSE_ORIGINAL_SIMULATED_HOST_REQUIRED")
    if (
        membership.to_dict() != request.ranking.prior.to_dict()
        or ranking_snapshot != request.ranking.snapshot.to_dict()
    ):
        _fail("POST_CLOSE_MEMBERSHIP_OR_RANKING_MISMATCH")
    prefix = cycle_kwargs.get("cycle_id_prefix")
    if type(prefix) is not str or not prefix.strip():
        _fail("POST_CLOSE_NEXT_CYCLE_REQUIRED")
    close_ref = request.execution.envelope.envelope_digest
    binding = {
        "identity": context.identity.identity_digest(),
        "close_snapshot": dict(context.lifecycle.reconciliation.snapshot),
        "old_bound": request.bound_instrument.to_dict(),
        "source_lane_id": request.execution.source.quantity_handoff.lane_id,
        "prior_membership": membership.to_dict(),
        "ranking": ranking_snapshot,
        "observation_chain": [r.to_dict() for r in request.ranking.observation_chain],
        "closed_reservations": list(request.closed_reservation_ids),
        "budget_observation": request.expected_budget_observation_id,
        "next_cycle": prefix,
        "next_observed_unix": observed_unix,
        "target_observation_digest": context.budget_observed.digest(),
        "repository_sha": repository_sha,
        "origin_main_sha": origin_main_sha,
        "membership_root": str(Path(context.membership_store_root).resolve()),
        "topology_root": str(Path(topology_root).resolve()),
        "target_cardinality": target_cardinality,
        "policy_digest": owner.entry_budget_policy_v1().digest_v1(),
    }
    path = checkpoint_root_for(topology_root) / "post_close" / (close_ref + ".json")
    if request.ranking.reserved_challenger_v1 is not None or request.ranking.rotation_waiting_v1:
        binding["rotation_constraint_v1"] = dict(
            reserved_challenger=request.ranking.reserved_challenger_v1,
            reserved_incumbent=request.ranking.reserved_incumbent_v1,
            waiting=request.ranking.rotation_waiting_v1,
        )
    fingerprint = _digest(binding)
    prior = _read_receipt(path) if path.exists() else None
    if prior is not None:
        if prior["schema"] != SCHEMA or prior["binding_digest"] != fingerprint:
            _fail("POST_CLOSE_CONTINUATION_REPLAY_CONFLICT")
        if prior["phase"] == "ACKED":
            return PostCloseContinuationReplayV1(prior)
        if prior["phase"] == "CONSUMING":
            completions = read_group_completion_v1(prior, recover=True)
            prior.update(
                phase="ACKED",
                consumed={l: r["consumed"] for l, r in completions.items()},
                terminal_boundary="PRE_EXTERNAL_EFFECT",
                consumer_completion_digests={
                    l: r["content_digest"] for l, r in completions.items()
                },
                acknowledgement_source="ORIGINAL_N1_CONSUMER_COMPLETION_READBACK",
            )
            return PostCloseContinuationReplayV1(_write_receipt(path, prior))
    recovery = cycle_kwargs.get("host_budget_recovery")
    floor = datetime.fromisoformat(request.observed_at_utc.replace("Z", "+00:00"))
    if floor.tzinfo is None:
        _fail("POST_CLOSE_TIMEZONE_REQUIRED")
    if (
        context.host.closed
        or not isinstance(recovery, HostBudgetRecoveryContextV1)
        or recovery.host is not context.host
        or recovery.observed != context.budget_observed
    ):
        _fail("BOUNDED_CLOSE_FRESH_ORIGINAL_HOST_CONTEXT_REQUIRED")
    if any(
        type(t) not in (float, int) or not math.isfinite(t) or t < floor.timestamp()
        for t in (observed_unix, cap24.now_unix, cycle_kwargs.get("observed_unix"))
    ):
        _fail("POST_CLOSE_NEXT_CONSUMER_BEFORE_CLOSE")
    observed = context.budget_observed
    if (
        observed != cap24.observed_portfolio
        or observed.event_time_unix is None
        or observed.event_time_unix < floor.timestamp()
        or Path(cap24.reconciliation_state_root).resolve()
        != (context.host.root / "reconciliation").resolve()
        or cycle_kwargs.get("observed_portfolio", observed) != observed
        or not 0 < context.capital_max_age_seconds <= NUMERIC_EQUITY_TTL_SECONDS
    ):
        _fail("POST_CLOSE_FRESH_TARGET_OBSERVATION_REQUIRED")
    topology = recover_durable_lane_assignment_v1(
        topology_state_root_base=topology_root,
        recovery_mode=RECOVERY_MODE_RESTART,
        expected_universe_snapshot_id=request.bound_instrument.universe_snapshot_id,
    )
    slots = {s.lane_id: s for s in topology.occupied_slots()}
    lane = binding["source_lane_id"]
    if (
        len(slots) != target_cardinality
        or lane not in slots
        or (prior is None and topology.membership_instance_id != membership.instance_id)
    ):
        _fail("BOUNDED_CLOSE_PRIOR_TOPOLOGY_MISMATCH")
    snapshot = owner.risk_snapshot_v1()["state"]
    old_bounds = {l: BoundInstrumentV1(**r["bound"]) for l, r in snapshot["lane_bindings"].items()}
    if prior is None:
        if old_bounds.get(lane) != request.bound_instrument or context.host.bindings != old_bounds:
            _fail("BOUNDED_CLOSE_PRIOR_BINDINGS_MISMATCH")
        for l, bound in old_bounds.items():
            loaded = load_and_validate_selection_v1(Path(slots[l].lane_state_root))
            if (
                not loaded.ok
                or loaded.selection is None
                or loaded.selection.integrity_digest != bound.selection_integrity_digest
                or loaded.selection.selection_id != bound.selection_id
                or slots[l].canonical_instrument_id != bound.instrument_id
            ):
                _fail("POST_CLOSE_PRIOR_SELECTION_MISMATCH")
        retained = {l: b for l, b in old_bounds.items() if l != lane}
    else:
        retained = retained_bounds_v1(prior)
    for l, bound in retained.items():
        if old_bounds.get(l) != bound or not any(
            p.instrument_id == bound.instrument_id and p.signed_quantity != 0
            for p in observed.positions
        ):
            _fail("BOUNDED_CLOSE_RETAINED_POSITION_UNPROVEN")
    feedback = compose_post_close_feedback_v1(
        lifecycle=context.lifecycle, identity=context.identity, request=request
    )
    if (
        not feedback.ranking_review_allowed
        or feedback.membership_review is None
        or feedback.capital_refresh is None
        or feedback.capital_refresh.disposition.value not in {"ADMITTED", "IDEMPOTENT_REPLAY"}
    ):
        _fail("POST_CLOSE_FINANCIAL_CONTINUATION_NOT_ADMITTED:" + ",".join(feedback.reason_codes))
    owner.inspect_bounded_slot_close_refresh_v1(request)
    review = feedback.membership_review
    if len(review.ordered_membership) != target_cardinality or not {
        b.instrument_id for b in retained.values()
    }.issubset(review.ordered_membership):
        _fail("BOUNDED_CLOSE_FOREIGN_MEMBERSHIP_CHANGE_FORBIDDEN")
    stored = persist_selector_result_v1(review, store_root=Path(context.membership_store_root))
    target = stored.persisted_artifact or review.proposed_artifact
    record = {
        "schema": SCHEMA,
        "binding_digest": fingerprint,
        "binding": binding,
        "phase": "MEMBERSHIP_STORED",
        "close_ref": close_ref,
        "membership": target.to_dict(),
        "retained_bound_by_lane": {l: b.to_dict() for l, b in retained.items()},
        "execution_authority_effect": "NONE",
    }
    if prior is not None and prior["membership"] != record["membership"]:
        _fail("POST_CLOSE_TARGET_REPLAY_CONFLICT")
    _write_receipt(path, record)
    return target, (path, record)


def admit_v1(context, handle, *, owner, pairs, **kwargs):
    path, record = handle
    if len(pairs) != record["binding"]["target_cardinality"] or {
        l: b for l, (_, b) in pairs.items() if l in retained_bounds_v1(record)
    } != retained_bounds_v1(record):
        _fail("BOUNDED_CLOSE_FOREIGN_BOUND_GENERATION_CHANGED")
    bindings = {lane: pair[1] for lane, pair in pairs.items()}
    recovery = context.host.observe_after_bounded_slot_close_v1(bindings, request=context.request)
    record.update(phase="CONSUMING", bound_by_lane={l: b.to_dict() for l, b in bindings.items()})
    _write_receipt(path, record)
    return recovery


def acknowledge_v1(handle, result):
    path, record = handle
    completions = read_group_completion_v1(record)
    consumed = {}
    for lane, projection in result.readiness_projections.items():
        invocation = projection.n1_consumer_result.s7_invocation
        if (
            invocation is None
            or invocation.bound_instrument.to_dict() != record["bound_by_lane"][lane]
            or projection.bound_instrument != invocation.bound_instrument
        ):
            _fail("POST_CLOSE_ORIGINAL_CORE_CONSUMER_UNPROVEN")
        core = invocation.cycle_result
        consumed[lane] = {
            "instrument_id": projection.instrument_id,
            "native_id": projection.native_id,
            "cycle_id": core.cycle_id,
            "input_digest": core.input_digest,
            "decision_outcome": core.decision_outcome,
        }
    if (
        consumed != {l: r["consumed"] for l, r in completions.items()}
        or result.post_allowed
        or result.external_effect_authorized
    ):
        _fail("POST_CLOSE_CONSUMER_COMPLETION_CONFLICT")
    record.update(
        phase="ACKED",
        consumed=consumed,
        terminal_boundary=result.terminal_boundary,
        consumer_completion_digests={l: r["content_digest"] for l, r in completions.items()},
        acknowledgement_source="ORIGINAL_N1_CONSUMER_COMPLETION",
    )
    return _write_receipt(path, record)
