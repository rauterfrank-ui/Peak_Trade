"""Durable N1 handoff between existing close, membership, budget and Core owners.

The receipt records sequencing only. An interrupted Core invocation stays fenced:
absence of its ACK is never permission to consume another cycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path

from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
    checkpoint_root_for,
    RECOVERY_MODE_RESTART,
    recover_durable_lane_assignment_v1,
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
from src.ops.portfolio_capital_reservation_budget_v1.recovery_v1 import (
    reconcile_durable_budget_startup_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import PortfolioTruthSnapshotV1
from src.ops.single_selected_future_policy_v1.persistence_v1 import load_and_validate_selection_v1

SCHEMA = "productive_n1_post_close_continuation.v1"


class PostCloseContinuationError(ValueError):
    pass


@dataclass(frozen=True)
class ProductiveN1PostCloseContinuationV1:
    lifecycle: FullCorePostSubmitLifecycleReconciliationJoinResultV1
    identity: FullCoreExchangeReconciliationIdentityV1
    request: PostCloseFeedbackRequestV1
    membership_store_root: Path
    budget_observed: PortfolioTruthSnapshotV1
    capital_max_age_seconds: float


@dataclass(frozen=True)
class PostCloseContinuationReplayV1:
    receipt: dict
    replayed: bool = True


def _digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _fail(code):
    raise PostCloseContinuationError(code)


def _write_receipt(path, record):
    body = {k: v for k, v in record.items() if k != "content_digest"}
    sealed = {**body, "content_digest": _digest(body)}
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    try:
        with temporary.open("w") as stream:
            stream.write(json.dumps(sealed, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        temporary.unlink(missing_ok=True)
    return sealed


def _read_receipt(path):
    record = json.loads(path.read_text())
    body = {k: v for k, v in record.items() if k != "content_digest"}
    if record.get("content_digest") != _digest(body) or record.get("schema") not in {
        SCHEMA,
        "bounded_slot_post_close_continuation.v1",
    }:
        _fail("POST_CLOSE_RECEIPT_INTEGRITY_INVALID")
    if record.get("phase") not in {"MEMBERSHIP_STORED", "CONSUMING", "ACKED"}:
        _fail("POST_CLOSE_RECEIPT_PHASE_INVALID")
    if record.get("binding_digest") != _digest(record.get("binding")):
        _fail("POST_CLOSE_RECEIPT_BINDING_INVALID")
    if record["phase"] in {"CONSUMING", "ACKED"}:
        bindings = record.get("bound_by_lane", {})
        expected = (
            1 if record["schema"] == SCHEMA else record["binding"].get("target_cardinality", 0)
        )
        if not 1 <= expected <= 5 or len(bindings) != expected:
            _fail("POST_CLOSE_RECEIPT_BOUND_TARGET_MISSING")
        if record["phase"] == "ACKED":
            consumed = record.get("consumed", {})
            if set(consumed) != set(bindings) or any(
                not row.get("cycle_id")
                or not row.get("input_digest")
                or row.get("instrument_id") != bindings[lane]["instrument_id"]
                or row.get("native_id") != bindings[lane]["venue_native_id"]
                for lane, row in consumed.items()
            ):
                _fail("POST_CLOSE_RECEIPT_CONSUMER_ACK_INVALID")
    return record


def _read_original_consumer_completion(record, *, recover=False):
    from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
        lane_state_root_for,
    )
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1.consumer_completion_v1 import (
        N1ConsumerCompletionError,
        N1ConsumerCompletionPublicationError,
        read_n1_consumer_completion_v1,
        recover_n1_consumer_completion_v1,
    )

    lane, bound = next(iter(record["bound_by_lane"].items()))
    root = lane_state_root_for(
        topology_state_root_base=record["binding"]["topology_root"], lane_id=lane
    )
    try:
        reader = recover_n1_consumer_completion_v1 if recover else read_n1_consumer_completion_v1
        return reader(
            lane_state_root=root,
            binding_digest=record["binding_digest"],
            lane_id=lane,
            bound=bound,
            cycle_prefix=record["binding"]["next_cycle"],
            origin_main_sha=record["binding"]["origin_main_sha"],
        )
    except N1ConsumerCompletionPublicationError as exc:
        raise PostCloseContinuationError(
            "POST_CLOSE_CONSUMER_PUBLICATION_RETRY_REQUIRED:" + str(exc)
        ) from exc
    except N1ConsumerCompletionError as exc:
        raise PostCloseContinuationError(
            "POST_CLOSE_CORE_OUTCOME_UNCERTAIN_RECONCILIATION_REQUIRED:" + str(exc)
        ) from exc


def prepare_post_close_continuation_v1(
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
    """Validate the original close; store the original selector's exact proposal."""
    from .bounded_slot_post_close_v1 import BoundedSlotPostCloseContinuationV1, prepare_v1

    if type(context) is BoundedSlotPostCloseContinuationV1:
        return prepare_v1(
            context,
            membership=membership,
            ranking_snapshot=ranking_snapshot,
            topology_root=topology_root,
            writer=writer,
            owner=owner,
            repository_sha=repository_sha,
            origin_main_sha=origin_main_sha,
            observed_unix=observed_unix,
            cap24=cap24,
            target_cardinality=target_cardinality,
            cycle_kwargs=cycle_kwargs,
        )
    if not isinstance(context, ProductiveN1PostCloseContinuationV1):
        _fail("POST_CLOSE_CONTEXT_INVALID")
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
        target_cardinality != 1
        or len(membership.ordered_instrument_ids) != 1
        or owner is None
        or owner is not request.budget_owner
        or not owner.budget_state_v1().durable_state_enabled
        or cycle_kwargs.get("host_budget_recovery") is not None
    ):
        _fail("POST_CLOSE_DURABLE_N1_OWNER_REQUIRED")
    if (
        membership.to_dict() != request.ranking.prior.to_dict()
        or ranking_snapshot != request.ranking.snapshot.to_dict()
    ):
        _fail("POST_CLOSE_MEMBERSHIP_OR_RANKING_MISMATCH")
    close_time = datetime.fromisoformat(request.observed_at_utc.replace("Z", "+00:00"))
    if close_time.tzinfo is None:
        _fail("POST_CLOSE_TIMEZONE_REQUIRED")
    floor = close_time.timestamp()
    times = (observed_unix, cap24.now_unix, cycle_kwargs.get("observed_unix"))
    if any(type(v) not in (int, float) or not math.isfinite(v) or v < floor for v in times):
        _fail("POST_CLOSE_NEXT_CONSUMER_BEFORE_CLOSE")
    if (
        not isinstance(context.budget_observed, PortfolioTruthSnapshotV1)
        or context.budget_observed != cap24.observed_portfolio
        or context.budget_observed.event_time_unix is None
        or context.budget_observed.event_time_unix < floor
        or cycle_kwargs.get("observed_portfolio", context.budget_observed)
        != context.budget_observed
        or type(context.capital_max_age_seconds) not in (int, float)
        or not math.isfinite(context.capital_max_age_seconds)
        or context.capital_max_age_seconds <= 0
        or context.capital_max_age_seconds > NUMERIC_EQUITY_TTL_SECONDS
    ):
        _fail("POST_CLOSE_FRESH_TARGET_OBSERVATION_REQUIRED")
    envelope = request.execution.envelope
    close_ref = envelope.envelope_digest
    if len(close_ref) != 64 or any(c not in "0123456789abcdef" for c in close_ref):
        _fail("POST_CLOSE_ENVELOPE_IDENTITY_INVALID")
    prefix = cycle_kwargs.get("cycle_id_prefix")
    if not isinstance(prefix, str) or not prefix.strip():
        _fail("POST_CLOSE_NEXT_CYCLE_REQUIRED")
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
    }
    path = checkpoint_root_for(topology_root) / "post_close" / (close_ref + ".json")
    fingerprint = _digest(binding)
    prior = _read_receipt(path) if path.exists() else None
    if prior is not None:
        if prior["binding_digest"] != fingerprint:
            _fail("POST_CLOSE_CONTINUATION_REPLAY_CONFLICT")
        if prior["phase"] == "ACKED":
            return PostCloseContinuationReplayV1(prior)
        if prior["phase"] == "CONSUMING":
            completion = _read_original_consumer_completion(prior, recover=True)
            lane = completion["lane_id"]
            prior.update(
                phase="ACKED",
                consumed={lane: completion["consumed"]},
                terminal_boundary="PRE_EXTERNAL_EFFECT",
                consumer_completion_digest=completion["content_digest"],
                acknowledgement_source="ORIGINAL_N1_CONSUMER_COMPLETION_READBACK",
            )
            return PostCloseContinuationReplayV1(_write_receipt(path, prior))
    else:
        topology = recover_durable_lane_assignment_v1(
            topology_state_root_base=topology_root,
            recovery_mode=RECOVERY_MODE_RESTART,
            expected_universe_snapshot_id=request.bound_instrument.universe_snapshot_id,
        )
        occupied = topology.occupied_slots()
        if (
            len(occupied) != 1
            or topology.membership_instance_id != membership.instance_id
            or occupied[0].lane_id != binding["source_lane_id"]
        ):
            _fail("POST_CLOSE_PRIOR_N1_TOPOLOGY_MISMATCH")
        selection = load_and_validate_selection_v1(Path(occupied[0].lane_state_root))
        bound = request.bound_instrument
        if (
            not selection.ok
            or selection.selection is None
            or any(
                getattr(selection.selection, name) != getattr(bound, name)
                for name in (
                    "instrument_id",
                    "venue_native_id",
                    "selection_id",
                    "ranking_snapshot_id",
                    "ranking_integrity_digest",
                )
            )
            or selection.selection.integrity_digest != bound.selection_integrity_digest
        ):
            _fail("POST_CLOSE_PRIOR_SELECTION_MISMATCH")
    feedback = compose_post_close_feedback_v1(
        lifecycle=context.lifecycle,
        identity=context.identity,
        request=request,
    )
    if (
        not feedback.ranking_review_allowed
        or feedback.membership_review is None
        or feedback.capital_refresh is None
        or feedback.capital_refresh.disposition.value not in {"ADMITTED", "IDEMPOTENT_REPLAY"}
        or owner.active_sum_v1() != 0
    ):
        _fail("POST_CLOSE_FINANCIAL_CONTINUATION_NOT_ADMITTED")
    review = feedback.membership_review
    if len(review.ordered_membership) != 1:
        _fail("POST_CLOSE_N1_TARGET_CARDINALITY_REQUIRED")
    stored = persist_selector_result_v1(review, store_root=Path(context.membership_store_root))
    target = stored.persisted_artifact or review.proposed_artifact
    if target is None:
        _fail("POST_CLOSE_TARGET_MEMBERSHIP_MISSING")
    record = {
        "schema": SCHEMA,
        "binding_digest": fingerprint,
        "binding": binding,
        "phase": "MEMBERSHIP_STORED",
        "close_ref": close_ref,
        "membership": target.to_dict(),
        "execution_authority_effect": "NONE",
    }
    if prior is not None and prior["membership"] != record["membership"]:
        _fail("POST_CLOSE_TARGET_REPLAY_CONFLICT")
    _write_receipt(path, record)
    return target, (path, record)


def admit_post_close_target_v1(context, handle, *, owner, pairs, now_unix, repo_sha, recon_root):
    """The existing budget owner admits the exact new Cap24 bindings."""
    from .bounded_slot_post_close_v1 import BoundedSlotPostCloseContinuationV1, admit_v1

    if type(context) is BoundedSlotPostCloseContinuationV1:
        return admit_v1(context, handle, owner=owner, pairs=pairs)
    path, record = handle
    if len(pairs) != 1:
        _fail("POST_CLOSE_N1_BOUND_CARDINALITY_REQUIRED")
    bindings = {lane: pair[1] for lane, pair in pairs.items()}
    result = reconcile_durable_budget_startup_v1(
        owner,
        output=context.request.capital_handoff.producer_output,
        observed=context.budget_observed,
        lane_bindings=bindings,
        reconciliation_state_root=Path(recon_root),
        session_id=record["binding"]["next_cycle"],
        repository_sha=repo_sha,
        now_unix=now_unix,
        capital_max_age_seconds=context.capital_max_age_seconds,
    )
    if result.disposition.value != "ADMITTED":
        _fail("POST_CLOSE_TARGET_BUDGET_RECOVERY_REQUIRED:" + ",".join(result.reason_codes))
    record.update(
        phase="CONSUMING",
        bound_by_lane={lane: b.to_dict() for lane, b in bindings.items()},
    )
    _write_receipt(path, record)


def acknowledge_post_close_consumer_v1(handle, result):
    """ACK only an actual original S7/Core invocation with the published binding."""
    from .bounded_slot_post_close_v1 import SCHEMA as BOUNDED_SCHEMA, acknowledge_v1

    if handle[1]["schema"] == BOUNDED_SCHEMA:
        return acknowledge_v1(handle, result)
    path, record = handle
    consumed = {}
    for lane, projection in result.readiness_projections.items():
        invocation = projection.n1_consumer_result.s7_invocation
        if (
            invocation is None
            or projection.bound_instrument.to_dict() != record["bound_by_lane"][lane]
            or invocation.bound_instrument.to_dict() != record["bound_by_lane"][lane]
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
    if len(consumed) != 1 or result.post_allowed or result.external_effect_authorized:
        _fail("POST_CLOSE_CONSUMER_BOUNDARY_INVALID")
    completion = _read_original_consumer_completion(record)
    if consumed != {completion["lane_id"]: completion["consumed"]}:
        _fail("POST_CLOSE_CONSUMER_COMPLETION_CONFLICT")
    record.update(
        phase="ACKED",
        consumed=consumed,
        terminal_boundary=result.terminal_boundary,
        consumer_completion_digest=completion["content_digest"],
        acknowledgement_source="ORIGINAL_N1_CONSUMER_COMPLETION",
    )
    return _write_receipt(path, record)
