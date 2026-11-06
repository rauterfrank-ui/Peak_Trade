"""Actual Cap23 policy → guarded selection/topology publication, all offline."""

from dataclasses import replace
from decimal import Decimal
import json
import multiprocessing
import os

import pytest

from src.ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1 import (
    checked_publication_v1 as publication,
)
from src.ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1.produce_join_v1 import (
    RankingDomainOccupiedLaneCap23ProduceJoinError,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
    recover_durable_lane_assignment_v1,
    checkpoint_root_for,
    RECOVERY_MODE_RESTART,
    FAILURE_PUBLICATION_PENDING,
    DurableLaneAssignmentPersistenceError,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.single_selected_future_policy_v1.single_writer_v1 import (
    SingleSelectedFutureSingleWriterV1,
)
from src.ops.hard_facts_system_closure_v1.position_aware_rotation_v1 import (
    evaluate_position_aware_rotation_v1,
    RotationPhase,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
)
from tests.ops.test_current_mf_n5_isolated_lane_instance_topology_v1 import (
    _ranking,
    _perp,
    _membership,
    REPO_SHA,
    OBSERVED_UNIX,
)


def _rank(snapshot, first, now):
    typed = ProductiveFuturesRankingSnapshotV1.from_dict(snapshot)
    ordered = sorted(typed.ranked_candidates, key=lambda c: c.canonical_instrument_id != first)
    return (
        replace(
            typed,
            ranking_snapshot_id=f"rank-{now}",
            event_time=str(int(now * 1000)),
            ranked_candidates=tuple(replace(c, rank=n) for n, c in enumerate(ordered, 1)),
        )
        .with_integrity_digest()
        .to_dict()
    )


def _files(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


@pytest.fixture
def lane_case(tmp_path):
    root = tmp_path / "topology"
    writer = DurableLaneAssignmentSingleWriterV1(checkpoint_root_for(root))
    writer.acquire()
    ranking = _ranking(
        [
            _perp(n)
            for n in [
                "ETH-USDT-SWAP",
                "SOL-USDT-SWAP",
                "ADA-USDT-SWAP",
                "LINK-USDT-SWAP",
                "APT-USDT-SWAP",
                "XRP-USDT-SWAP",
            ]
        ]
    )
    try:
        yield root, writer, ranking
    finally:
        writer.release()


def _bootstrap(case, count=1):
    root, writer, ranking = case
    members = [c["canonical_instrument_id"] for c in ranking["ranked_candidates"][:count]]
    result = publication.publish_checked_lane_selections_v1(
        membership=_membership(ranking, members),
        ranking_snapshot=ranking,
        topology_state_root_base=root,
        writer=writer,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    return result


def _replacement(case, initial, now, *, good_rank=True):
    root, writer, ranking = case
    chosen = set(initial.topology.instrument_to_lane())
    new = next(
        c["canonical_instrument_id"]
        for c in ranking["ranked_candidates"]
        if c["canonical_instrument_id"] not in chosen
    )
    changed_lane = sorted(initial.selections)[-1]
    old = initial.selections[changed_lane].instrument_id
    fresh = _rank(ranking, new if good_rank else old, now)
    members = [new if cid == old else cid for cid in initial.topology.instrument_to_lane()]
    clear = evaluate_position_aware_rotation_v1(
        phase=RotationPhase.COMMIT,
        venue_flat=True,
        reconciled=True,
        pending_external_custody=False,
        pending_pre_external_custody=False,
        lane_health_allows_replacement=True,
    )
    args = dict(
        membership=_membership(
            fresh, members, bootstrap=False, prior=initial.topology.membership_instance_id
        ),
        ranking_snapshot=fresh,
        topology_state_root_base=root,
        writer=writer,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=now,
        observed_portfolio=PortfolioTruthSnapshotV1(event_time_unix=now, max_age_seconds=60),
        replacement_admission_by_lane={changed_lane: clear},
    )
    return args, changed_lane, old, new


@pytest.mark.parametrize("count", [1, 5])
@pytest.mark.parametrize(
    "problem",
    ["holding", "rank", "position", "pending", "unknown", "missing_selection", "corrupt_selection"],
)
def test_rejected_change_preserves_all_stored_assignments_and_selections(lane_case, count, problem):
    initial = _bootstrap(lane_case, count)
    root, _, _ = lane_case
    now = OBSERVED_UNIX + (60 if problem == "holding" else 4000)
    args, lane, old, _ = _replacement(lane_case, initial, now, good_rank=problem != "rank")
    if problem == "position":
        args["observed_portfolio"] = replace(
            args["observed_portfolio"],
            positions=(
                PositionTruthV1.from_signed(instrument_id=old, signed_quantity=Decimal("1")),
            ),
        )
    elif problem == "pending":
        args["replacement_admission_by_lane"] = {}
    elif problem == "unknown":
        args["observed_portfolio"] = None
    elif problem in ("missing_selection", "corrupt_selection"):
        file = root / lane / "single_selected_future_selection_v1.json"
        if problem == "missing_selection":
            file.unlink()
        else:
            file.write_text("broken")
    before = _files(root)
    with pytest.raises((RankingDomainOccupiedLaneCap23ProduceJoinError, RuntimeError)):
        publication.publish_checked_lane_selections_v1(**args)
    assert _files(root) == before
    recovered = recover_durable_lane_assignment_v1(
        topology_state_root_base=root, recovery_mode=RECOVERY_MODE_RESTART
    )
    assert recovered.to_dict() == initial.topology.to_dict()


@pytest.mark.parametrize("count", [1, 5])
def test_allowed_replacement_is_consistent_after_restart(lane_case, count):
    initial = _bootstrap(lane_case, count)
    args, lane, old, new = _replacement(lane_case, initial, OBSERVED_UNIX + 4000)
    result = publication.publish_checked_lane_selections_v1(**args)
    assert result.selections[lane].instrument_id == new
    assert old not in result.topology.instrument_to_lane()
    assert result.topology.instrument_to_lane()[new] == lane
    recovered = recover_durable_lane_assignment_v1(
        topology_state_root_base=args["topology_state_root_base"],
        recovery_mode=RECOVERY_MODE_RESTART,
    )
    assert recovered.to_dict() == result.topology.to_dict()


@pytest.mark.parametrize(
    "stage", ["selection", "within_selection", "within_topology", "after_topology"]
)
def test_interrupted_publication_fences_readers_then_resumes(lane_case, monkeypatch, stage):
    initial = _bootstrap(lane_case, 5)
    args, _, _, _ = _replacement(lane_case, initial, OBSERVED_UNIX + 4000)
    if stage == "selection":
        real = publication.commit_prepared_lane_selection_v1
        calls = 0

        def fail(item):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected second owner write failure")
            return real(item)

        monkeypatch.setattr(publication, "commit_prepared_lane_selection_v1", fail)
    elif stage == "within_selection":
        from src.ops.single_selected_future_policy_v1 import producer_v1

        real = producer_v1.persist_selection_bundle_atomic_v1

        def fail(**kwargs):
            return real(**kwargs, simulate_partial_write=True)

        monkeypatch.setattr(producer_v1, "persist_selection_bundle_atomic_v1", fail)
    elif stage == "within_topology":
        real = publication.persist_durable_lane_assignment_v1

        def fail(**kwargs):
            return real(**kwargs, simulate_crash_after_checkpoint_before_marker=True)

        monkeypatch.setattr(publication, "persist_durable_lane_assignment_v1", fail)
    else:

        def fail(**kwargs):
            raise OSError("injected after topology write")

        monkeypatch.setattr(publication, "finish_selection_publication_v1", fail)
    with pytest.raises((OSError, RuntimeError, ValueError)):
        publication.publish_checked_lane_selections_v1(**args)
    root = args["topology_state_root_base"]
    with pytest.raises(DurableLaneAssignmentPersistenceError, match=FAILURE_PUBLICATION_PENDING):
        recover_durable_lane_assignment_v1(
            topology_state_root_base=root, recovery_mode=RECOVERY_MODE_RESTART
        )
    monkeypatch.undo()
    result = publication.publish_checked_lane_selections_v1(**args)
    assert result.resumed is True
    recovered = recover_durable_lane_assignment_v1(
        topology_state_root_base=root, recovery_mode=RECOVERY_MODE_RESTART
    )
    assert recovered.to_dict() == result.topology.to_dict()
    for lane, selected in result.selections.items():
        loaded = publication.load_and_validate_selection_v1(root / lane)
        assert loaded.ok and loaded.selection.to_dict() == selected.to_dict()


def test_duplicate_selection_writer_cannot_publish_topology(lane_case):
    initial = _bootstrap(lane_case)
    args, lane, _, _ = _replacement(lane_case, initial, OBSERVED_UNIX + 4000)
    root = args["topology_state_root_base"]
    other = SingleSelectedFutureSingleWriterV1(root / lane, session_id="other")
    other.acquire()
    try:
        before = _files(root)
        with pytest.raises(RuntimeError, match="DUPLICATE_SELECTION_WRITER"):
            publication.publish_checked_lane_selections_v1(**args)
        assert _files(root) == before
    finally:
        other.release()


def _crash_during_publication(args):
    args["writer"].acquire()
    real = publication.commit_prepared_lane_selection_v1
    calls = 0

    def crash(item):
        nonlocal calls
        calls += 1
        if calls == 2:
            os._exit(23)
        return real(item)

    publication.commit_prepared_lane_selection_v1 = crash
    publication.publish_checked_lane_selections_v1(**args)


def test_dead_process_locks_and_partial_publication_resume_together(lane_case):
    initial = _bootstrap(lane_case, 5)
    args, _, _, _ = _replacement(lane_case, initial, OBSERVED_UNIX + 4000)
    writer = args["writer"]
    writer.release()
    child = multiprocessing.get_context("fork").Process(
        target=_crash_during_publication, args=(args,)
    )
    child.start()
    try:
        child.join(timeout=10)
        assert child.exitcode == 23
    finally:
        if child.is_alive():
            child.kill()
            child.join(timeout=5)
    writer.acquire()
    result = publication.publish_checked_lane_selections_v1(**args)
    assert result.resumed
    root = args["topology_state_root_base"]
    archives = list(root.rglob("*.dead_process.*"))
    assert len(archives) == 6  # topology writer plus all five held selection writers
    assert all(json.loads(p.read_text())["pid"] == child.pid for p in archives)
    assert (
        recover_durable_lane_assignment_v1(
            topology_state_root_base=root, recovery_mode=RECOVERY_MODE_RESTART
        ).to_dict()
        == result.topology.to_dict()
    )


@pytest.mark.parametrize("kind", ["selection", "topology"])
@pytest.mark.parametrize("payload", ["broken", '{"pid":-1}', '{"pid":true}'])
def test_unknown_lock_is_preserved_and_requires_owner_repair(tmp_path, kind, payload):
    owner = (
        SingleSelectedFutureSingleWriterV1
        if kind == "selection"
        else DurableLaneAssignmentSingleWriterV1
    )(tmp_path)
    owner.lock_path.write_text(payload)
    with pytest.raises(RuntimeError):
        owner.acquire()
    assert owner.lock_path.read_text() == payload
    assert not list(tmp_path.glob("*.dead_process.*"))


@pytest.mark.parametrize("kind", ["selection", "topology"])
def test_failed_lock_publication_leaves_no_empty_canonical_lock(tmp_path, monkeypatch, kind):
    from src.ops import local_single_writer_lock_recovery_v1 as recovery

    owner = (
        SingleSelectedFutureSingleWriterV1
        if kind == "selection"
        else DurableLaneAssignmentSingleWriterV1
    )(tmp_path)

    def fail(*args, **kwargs):
        raise OSError("injected before atomic lock publication")

    with monkeypatch.context() as patch:
        patch.setattr(recovery.os, "link", fail)
        with pytest.raises(OSError):
            owner.acquire()
    assert not owner.lock_path.exists()
    assert not list(tmp_path.glob("*.acquiring.*"))
    owner.acquire()
    try:
        owner.assert_held()
    finally:
        owner.release()


@pytest.mark.parametrize("problem", ["position", "pending", "receipt", "selection", "topology"])
def test_resume_preserves_barrier_until_recovery_conditions_are_proven(
    lane_case, monkeypatch, problem
):
    initial = _bootstrap(lane_case, 5)
    args, lane, old, _ = _replacement(lane_case, initial, OBSERVED_UNIX + 4000)

    def interrupt(**kwargs):
        raise OSError("interrupted before releasing publication barrier")

    with monkeypatch.context() as patch:
        patch.setattr(publication, "finish_selection_publication_v1", interrupt)
        with pytest.raises(OSError):
            publication.publish_checked_lane_selections_v1(**args)
    root = args["topology_state_root_base"]
    if problem == "position":
        args["observed_portfolio"] = replace(
            args["observed_portfolio"],
            positions=(
                PositionTruthV1.from_signed(instrument_id=old, signed_quantity=Decimal("1")),
            ),
        )
    elif problem == "pending":
        args["replacement_admission_by_lane"] = {}
    elif problem == "receipt":
        (checkpoint_root_for(root) / "selection_publication_pending_v1.json").write_text("{}")
    elif problem == "topology":
        from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
            checkpoint_path,
        )

        checkpoint_path(checkpoint_root_for(root)).write_text("{}")
    else:
        (root / lane / "single_selected_future_selection_v1.json").write_text("broken")
    before = _files(root)
    with pytest.raises((RuntimeError, ValueError)):
        publication.publish_checked_lane_selections_v1(**args)
    assert _files(root) == before
    with pytest.raises(DurableLaneAssignmentPersistenceError, match=FAILURE_PUBLICATION_PENDING):
        recover_durable_lane_assignment_v1(
            topology_state_root_base=root, recovery_mode=RECOVERY_MODE_RESTART
        )


@pytest.mark.parametrize("problem", ["holding", "rank", "pending", "unknown"])
def test_temporary_denial_has_recovery_action_and_does_not_latch(lane_case, problem):
    initial = _bootstrap(lane_case, 5)
    early = OBSERVED_UNIX + (60 if problem == "holding" else 4000)
    args, _, _, _ = _replacement(lane_case, initial, early, good_rank=problem != "rank")
    if problem == "pending":
        args["replacement_admission_by_lane"] = {}
    if problem == "unknown":
        args["observed_portfolio"] = None
    with pytest.raises(RankingDomainOccupiedLaneCap23ProduceJoinError) as denied:
        publication.publish_checked_lane_selections_v1(**args)
    assert denied.value.recovery_action
    assert "recovery_action=" in str(denied.value)
    args, lane, _, new = _replacement(lane_case, initial, OBSERVED_UNIX + 5000)
    result = publication.publish_checked_lane_selections_v1(**args)
    assert result.selections[lane].instrument_id == new
    assert not result.resumed
