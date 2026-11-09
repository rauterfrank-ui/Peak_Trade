"""Assess all lane selections before publishing their matching topology.

No ranking policy, trading activation, unknown-state repair or background retry.
An interrupted multi-owner write is fenced by the existing checkpoint owner.
"""

from contextlib import ExitStack
from dataclasses import dataclass, replace
import json
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
    load_completed_selection_publication_v1,
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
from src.ops.mf_membership_context_artifact_contract_v1 import (
    validate_membership_context_artifact_v1,
)
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
    retained_bound_by_lane: Mapping | None = None,
) -> CheckedLanePublicationV1:
    from .produce_join_v1 import _assert_non_authority, _fail

    _assert_non_authority()
    writer.assert_held()
    retained_bound_by_lane = dict(retained_bound_by_lane or {})
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
    if prior is not None and prior.membership_instance_id == membership.instance_id:
        from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
            ProductiveFuturesRankingSnapshotV1,
        )
        from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
            validate_ranking_snapshot_bindings_v1,
        )

        validate_membership_context_artifact_v1(membership)
        valid = validate_ranking_snapshot_bindings_v1(
            ProductiveFuturesRankingSnapshotV1.from_dict(ranking_snapshot)
        )
        receipt = load_completed_selection_publication_v1(topology_state_root_base)
        if (
            not valid.ok
            or receipt is None
            or receipt["topology_digest"] != topology_integrity_digest_v1(prior.to_dict())
            or prior.ranking_snapshot_id != ranking_snapshot["ranking_snapshot_id"]
            or prior.ranking_integrity_digest != ranking_snapshot["integrity_digest"]
            or set(prior.instrument_to_lane()) != set(membership.ordered_instrument_ids)
        ):
            _fail("LANE_COMPLETED_PUBLICATION_REPLAY_MISMATCH")
        selections = {}
        for slot in prior.occupied_slots():
            loaded = load_and_validate_selection_v1(Path(slot.lane_state_root))
            selection = loaded.selection
            if (
                not loaded.ok
                or selection is None
                or selection.instrument_id != slot.canonical_instrument_id
                or selection.ranking_snapshot_id != slot.ranking_snapshot_id
                or selection.ranking_integrity_digest != slot.ranking_integrity_digest
                or selection.integrity_digest != receipt["selection_digests"].get(slot.lane_id)
            ):
                _fail("LANE_COMPLETED_PUBLICATION_SELECTION_MISMATCH", slot.lane_id)
            selections[slot.lane_id] = selection
        return CheckedLanePublicationV1(prior, selections, resumed=True)
    if prior is not None and membership.prior_membership_reference != prior.membership_instance_id:
        _fail("LANE_MEMBERSHIP_CONTINUITY_UNPROVEN")
    proposed = apply_isolated_lane_topology_v1(
        membership=membership,
        ranking_snapshot=ranking_snapshot,
        topology_state_root_base=topology_state_root_base,
        prior_topology=prior,
    )
    if retained_bound_by_lane:
        if prior is None or set(retained_bound_by_lane) - {
            s.lane_id for s in prior.occupied_slots()
        }:
            _fail("LANE_RETAINED_BINDING_SOURCE_REQUIRED")
        old_slots = {s.lane_id: s for s in prior.occupied_slots()}
        for slot in proposed.occupied_slots():
            if (
                slot.lane_id in retained_bound_by_lane
                and slot.canonical_instrument_id != old_slots[slot.lane_id].canonical_instrument_id
            ):
                _fail("LANE_RETAINED_INSTRUMENT_CHANGED", slot.lane_id)
        proposed = replace(
            proposed,
            slots=tuple(
                old_slots[s.lane_id] if s.lane_id in retained_bound_by_lane else s
                for s in proposed.slots
            ),
            retained_binding_lanes_v1=tuple(sorted(retained_bound_by_lane)),
        )
        proposed = isolated_lane_topology_from_dict(proposed.to_dict())
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
        retained = {}
        # Locks stay held through assessment, publication and readback. No lane
        # is written when another lane rejects the same proposed transition.
        for lane, pin in sorted(pins.items()):
            if lane in retained_bound_by_lane:
                from src.ops.single_selected_future_policy_v1.single_writer_v1 import (
                    SingleSelectedFutureSingleWriterV1,
                )
                from src.ops.single_selected_future_policy_v1.constants_v1 import EVIDENCE_FILENAME

                lane_writer = SingleSelectedFutureSingleWriterV1(Path(pin.lane_state_root))
                lane_writer.acquire(now_unix=producer_observed_at_unix)
                locks.callback(lane_writer.release)
                loaded = load_and_validate_selection_v1(Path(pin.lane_state_root))
                selection = loaded.selection
                bound = retained_bound_by_lane[lane]
                if (
                    not loaded.ok
                    or selection is None
                    or pin.resolved_venue_native_id != bound.venue_native_id
                    or bound.universe_snapshot_id != prior.universe_snapshot_id
                    or any(
                        getattr(selection, name) != getattr(bound, name)
                        for name in (
                            "instrument_id",
                            "venue_native_id",
                            "selection_id",
                            "ranking_snapshot_id",
                            "ranking_integrity_digest",
                        )
                    )
                    or selection.integrity_digest != bound.selection_integrity_digest
                ):
                    _fail("LANE_RETAINED_SELECTION_UNPROVEN", lane)
                retained[lane] = (
                    selection,
                    json.loads((Path(pin.lane_state_root) / EVIDENCE_FILENAME).read_text()),
                )
                continue
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
                    assessed.previous.ranking_snapshot_id
                    != next(
                        s for s in prior.occupied_slots() if s.lane_id == lane
                    ).ranking_snapshot_id
                    or assessed.previous.ranking_integrity_digest
                    != next(
                        s for s in prior.occupied_slots() if s.lane_id == lane
                    ).ranking_integrity_digest
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
                **{
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
                **{
                    lane: {
                        "selection": selection.to_dict(),
                        "evidence": evidence,
                        "previous_digest": selection.integrity_digest,
                        "previous_instrument": selection.instrument_id,
                    }
                    for lane, (selection, evidence) in retained.items()
                },
            },
            selection_digests={
                **{
                    lane: item.publication_selection.integrity_digest
                    for lane, item in prepared.items()
                },
                **{lane: selection.integrity_digest for lane, (selection, _) in retained.items()},
            },
        )
        # From this point, any exception deliberately leaves the durable barrier.
        # Never roll back a possibly published owner state or clear it on failure.
        selections = {
            lane: commit_prepared_lane_selection_v1(item) for lane, item in prepared.items()
        }
        selections.update({lane: selection for lane, (selection, _) in retained.items()})
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
        or selections[lane].ranking_snapshot_id != slot.ranking_snapshot_id
        or selections[lane].ranking_integrity_digest != slot.ranking_integrity_digest
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
