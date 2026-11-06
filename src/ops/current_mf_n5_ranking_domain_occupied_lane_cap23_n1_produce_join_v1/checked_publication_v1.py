"""Assess all lane selections before publishing their matching topology.

No ranking policy, trading activation, unknown-state repair or background retry.
An interrupted multi-owner write is fenced by the existing checkpoint owner.
"""

from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from math import isfinite
from typing import Mapping

from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
    RECOVERY_MODE_BOOTSTRAP,
    RECOVERY_MODE_RESTART,
    begin_selection_publication_v1,
    finish_selection_publication_v1,
    persist_durable_lane_assignment_v1,
    recover_durable_lane_assignment_v1,
    topology_integrity_digest_v1,
    validate_pending_publication_source_v1,
    load_pending_selection_publication_v1,
    checkpoint_root_for,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneTopologyV1,
    apply_isolated_lane_topology_v1,
    build_occupied_lane_pins_v1,
    lane_state_root_for,
    isolated_lane_topology_from_dict,
)
from src.ops.hard_facts_system_closure_v1.position_aware_rotation_v1 import (
    PositionAwareRotationDecisionV1,
    RotationPhase,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import PortfolioTruthSnapshotV1
from src.ops.single_selected_future_policy_v1.models_v1 import SingleSelectedFutureSelectionV1
from src.ops.single_selected_future_policy_v1.persistence_v1 import load_and_validate_selection_v1
from src.ops.single_selected_future_policy_v1.producer_v1 import (
    commit_prepared_lane_selection_v1,
    prepare_lane_selection_v1,
    prepared_lane_publication_evidence_v1,
    resume_lane_selection_publication_v1,
)


@dataclass(frozen=True)
class CheckedLanePublicationV1:
    topology: IsolatedLaneTopologyV1
    selections: dict[str, SingleSelectedFutureSelectionV1]
    resumed: bool = False


def _require_replacement_clearance_v1(
    changed, observed_portfolio, replacement_admission_by_lane, producer_observed_at_unix
):
    from .produce_join_v1 import _fail

    if changed:
        if not isinstance(observed_portfolio, PortfolioTruthSnapshotV1) or any(
            getattr(observed_portfolio, field)
            for field in ("missing", "stale", "duplicate", "writer_conflict")
        ):
            _fail("LANE_REPLACEMENT_POSITION_TRUTH_UNPROVEN")
        event, max_age = observed_portfolio.event_time_unix, observed_portfolio.max_age_seconds
        if (
            event is None
            or max_age is None
            or not all(isfinite(v) for v in (event, max_age, producer_observed_at_unix))
            or not 0 <= producer_observed_at_unix - event <= max_age
        ):
            _fail("LANE_REPLACEMENT_POSITION_TRUTH_UNPROVEN")
        for lane, old in changed.items():
            if any(
                p.instrument_id == old and (p.signed_quantity != 0 or p.side != "FLAT")
                for p in observed_portfolio.positions
            ):
                _fail("LANE_REPLACEMENT_OPEN_POSITION", lane)
            admission = (replacement_admission_by_lane or {}).get(lane)
            if not (
                isinstance(admission, PositionAwareRotationDecisionV1)
                and admission.phase == RotationPhase.COMMIT
                and admission.allowed is True
                and admission.reason_code == "COMMIT_OK"
                and admission.retain_custody_for_open_position is False
            ):
                _fail("LANE_REPLACEMENT_CUSTODY_ADMISSION_REQUIRED", lane)


def publish_checked_lane_selections_v1(
    *,
    membership,
    ranking_snapshot,
    topology_state_root_base,
    writer,
    repository_sha,
    producer_observed_at_unix,
    observed_portfolio: PortfolioTruthSnapshotV1 | None = None,
    replacement_admission_by_lane: Mapping[str, PositionAwareRotationDecisionV1] | None = None,
) -> CheckedLanePublicationV1:
    from .produce_join_v1 import _assert_non_authority, _fail

    _assert_non_authority()
    writer.assert_held()
    resumed = resume_pending_lane_publication_v1(
        topology_state_root_base=topology_state_root_base,
        writer=writer,
        observed_portfolio=observed_portfolio,
        replacement_admission_by_lane=replacement_admission_by_lane,
        producer_observed_at_unix=producer_observed_at_unix,
    )
    if resumed is not None:
        if (
            resumed.topology.membership_instance_id == membership.instance_id
            and resumed.topology.ranking_snapshot_id == ranking_snapshot["ranking_snapshot_id"]
            and resumed.topology.ranking_integrity_digest == ranking_snapshot["integrity_digest"]
        ):
            return resumed
    prior = recover_durable_lane_assignment_v1(
        topology_state_root_base=topology_state_root_base,
        recovery_mode=RECOVERY_MODE_BOOTSTRAP if membership.bootstrap else RECOVERY_MODE_RESTART,
        expected_universe_snapshot_id=ranking_snapshot["universe_snapshot_id"],
    )
    if prior is not None and membership.prior_membership_reference != prior.membership_instance_id:
        _fail("LANE_MEMBERSHIP_CONTINUITY_UNPROVEN")
    proposed = apply_isolated_lane_topology_v1(
        membership=membership,
        ranking_snapshot=ranking_snapshot,
        topology_state_root_base=topology_state_root_base,
        prior_topology=prior,
    )
    pins = build_occupied_lane_pins_v1(proposed, ranking_snapshot=ranking_snapshot)
    old_by_lane = (
        {}
        if prior is None
        else {slot.lane_id: slot.canonical_instrument_id for slot in prior.occupied_slots()}
    )
    changed = {
        lane: old
        for lane, old in old_by_lane.items()
        if lane not in pins or pins[lane].canonical_instrument_id != old
    }
    _require_replacement_clearance_v1(
        changed, observed_portfolio, replacement_admission_by_lane, producer_observed_at_unix
    )
    for lane in changed:
        if lane not in pins:
            _fail("LANE_REMOVAL_REQUIRES_SEPARATE_DISPOSITION", lane)

    with ExitStack() as locks:
        prepared = {}
        # Locks stay held through assessment, publication and readback. No lane
        # is written when another lane rejects the same proposed transition.
        for lane, pin in sorted(pins.items()):
            open_instrument = None
            if observed_portfolio is not None:
                old = old_by_lane.get(lane)
                if any(
                    p.instrument_id == old and p.signed_quantity != 0
                    for p in observed_portfolio.positions
                ):
                    open_instrument = old
            assessed = locks.enter_context(
                prepare_lane_selection_v1(
                    state_root=Path(pin.lane_state_root),
                    ranking_snapshot=ranking_snapshot,
                    repository_sha=repository_sha,
                    producer_observed_at_unix=producer_observed_at_unix,
                    governed_pin=pin,
                    expected_previous_instrument=old_by_lane.get(lane),
                    open_position_instrument_id=open_instrument,
                )
            )
            selection = assessed.produced.selection
            if (
                assessed.previous is not None
                and prior is not None
                and (
                    assessed.previous.ranking_snapshot_id != prior.ranking_snapshot_id
                    or assessed.previous.ranking_integrity_digest != prior.ranking_integrity_digest
                )
            ):
                _fail("LANE_SELECTION_TOPOLOGY_PROVENANCE_MISMATCH", lane)
            if (
                not assessed.produced.ok
                or assessed.produced.hard_stop
                or selection.instrument_id != pin.canonical_instrument_id
                or selection.venue_native_id != pin.resolved_venue_native_id
            ):
                _fail(
                    "LANE_SELECTION_PUBLICATION_DEFERRED",
                    f"{lane}:{','.join(selection.reason_codes)}",
                )
            prepared[lane] = assessed

        transition = begin_selection_publication_v1(
            topology=proposed,
            writer=writer,
            previous_topology_digest=None
            if prior is None
            else topology_integrity_digest_v1(prior.to_dict()),
            recovery_plan={
                lane: {
                    "selection": item.publication_selection.to_dict(),
                    "evidence": prepared_lane_publication_evidence_v1(item),
                    "previous_digest": None
                    if item.previous is None
                    else item.previous.integrity_digest,
                    "previous_instrument": None
                    if item.previous is None
                    else item.previous.instrument_id,
                }
                for lane, item in prepared.items()
            },
            selection_digests={
                lane: item.publication_selection.integrity_digest for lane, item in prepared.items()
            },
        )
        # From this point, any exception deliberately leaves the durable barrier.
        # Never roll back a possibly published owner state or clear it on failure.
        selections = {
            lane: commit_prepared_lane_selection_v1(item) for lane, item in prepared.items()
        }
        if any(
            selections[lane].to_dict() != item.publication_selection.to_dict()
            for lane, item in prepared.items()
        ):
            _fail("LANE_SELECTION_PUBLICATION_READBACK_FAILED", "assessed_result_changed")
        persist_durable_lane_assignment_v1(
            topology=proposed,
            writer=writer,
            selection_publication_id=transition,
        )
        for lane, selection in selections.items():
            loaded = load_and_validate_selection_v1(
                Path(
                    lane_state_root_for(
                        topology_state_root_base=topology_state_root_base, lane_id=lane
                    )
                )
            )
            if (
                not loaded.ok
                or loaded.selection is None
                or loaded.selection.to_dict() != selection.to_dict()
            ):
                _fail("LANE_SELECTION_PUBLICATION_READBACK_FAILED", lane)
        finish_selection_publication_v1(topology=proposed, writer=writer, transition_id=transition)
        return CheckedLanePublicationV1(proposed, selections)


def resume_pending_lane_publication_v1(
    *,
    topology_state_root_base,
    writer,
    observed_portfolio,
    replacement_admission_by_lane,
    producer_observed_at_unix,
) -> CheckedLanePublicationV1 | None:
    from .produce_join_v1 import _fail
    from src.ops.single_selected_future_policy_v1.single_writer_v1 import (
        SingleSelectedFutureSingleWriterV1,
    )
    from src.ops.single_selected_future_policy_v1.governed_pin_v1 import lane_state_root_key

    receipt = load_pending_selection_publication_v1(topology_state_root_base)
    if receipt is None:
        return None
    writer.assert_held()
    if lane_state_root_key(writer.state_root) != lane_state_root_key(
        checkpoint_root_for(topology_state_root_base)
    ):
        _fail("LANE_PUBLICATION_RECOVERY_ROOT_MISMATCH")
    topology = isolated_lane_topology_from_dict(receipt["topology"])
    if lane_state_root_key(topology.topology_state_root_base) != lane_state_root_key(
        topology_state_root_base
    ):
        _fail("LANE_PUBLICATION_RECOVERY_ROOT_MISMATCH")
    validate_pending_publication_source_v1(topology_state_root_base, receipt)
    slots = {slot.lane_id: slot for slot in topology.occupied_slots()}
    plans = receipt["recovery_plan"]
    if set(plans) != set(slots) or set(receipt["selection_digests"]) != set(slots):
        _fail("LANE_PUBLICATION_RECOVERY_PLAN_INVALID")
    selections = {
        lane: SingleSelectedFutureSelectionV1.from_dict(plan["selection"])
        for lane, plan in plans.items()
    }
    if any(
        selections[lane].instrument_id != slot.canonical_instrument_id
        or selections[lane].ranking_snapshot_id != topology.ranking_snapshot_id
        or selections[lane].ranking_integrity_digest != topology.ranking_integrity_digest
        or selections[lane].integrity_digest != receipt["selection_digests"][lane]
        for lane, slot in slots.items()
    ):
        _fail("LANE_PUBLICATION_RECOVERY_PLAN_INVALID")
    changed = {
        lane: plan["previous_instrument"]
        for lane, plan in plans.items()
        if plan["previous_instrument"] is not None
        and plan["previous_instrument"] != selections[lane].instrument_id
    }
    _require_replacement_clearance_v1(
        changed, observed_portfolio, replacement_admission_by_lane, producer_observed_at_unix
    )
    with ExitStack() as locks:
        writers = {}
        for lane, slot in sorted(slots.items()):
            lane_writer = SingleSelectedFutureSingleWriterV1(Path(slot.lane_state_root))
            lane_writer.acquire(now_unix=producer_observed_at_unix)
            locks.callback(lane_writer.release)
            writers[lane] = lane_writer
        for lane, plan in plans.items():
            resume_lane_selection_publication_v1(
                writer=writers[lane],
                selection=selections[lane],
                previous_digest=plan["previous_digest"],
                evidence=plan["evidence"],
            )
        persist_durable_lane_assignment_v1(
            topology=topology, writer=writer, selection_publication_id=receipt["transition_id"]
        )
        finish_selection_publication_v1(
            topology=topology, writer=writer, transition_id=receipt["transition_id"]
        )
    return CheckedLanePublicationV1(topology, selections, resumed=True)
