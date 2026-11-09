"""Planner persistence/negative cases; separate from the connected fill proofs."""

from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1.rotation_plan_v1 import (
    SlotRotationPlanOwnerV1,
    load_slot_rotation_plan_owner_v1,
)
from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1.post_close_continuation_v1 import (
    _digest,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_rotation_close_v1 import (
    RotationEntryHoldV1,
    RotationJournalEntryHoldV1,
    assess_rotation_close_v1,
)
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    PositionEpisodeIdentityV1,
    PositionEpisodeScopeV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)
from tests.ops import test_bounded_slot_connected_roundtrip_v1 as connected
from tests.ops.test_current_productive_rotation_close_v1 import review_for, T0, utc
from tests.test_mf_membership_selector_and_rotation_runtime_contract_v1 import _provenance


def rank(review, ordered_ids, event, label):
    by_id = {r.canonical_instrument_id: r for r in review.snapshot.ranked_candidates}
    snapshot = replace(
        review.snapshot,
        ranking_snapshot_id=label,
        event_time=utc(event),
        ranked_candidates=tuple(
            replace(by_id[cid], rank=i + 1) for i, cid in enumerate(ordered_ids)
        ),
    ).with_integrity_digest()
    return replace(review, snapshot=snapshot, provenance=_provenance(snapshot.to_dict()))


@pytest.fixture
def world(tmp_path, monkeypatch):
    sources = connected.sources
    monkeypatch.setattr(sources, "OBSERVED_UNIX", T0 - 3700)
    monkeypatch.setattr(sources, "SOURCE_EVENT", str(int((T0 - 3700) * 1000)))
    chain = sources._persist_universe_and_ranking(
        tmp_path,
        sources._five_rows()
        + [
            sources._perp("NEAR-USDT-SWAP", base="NEAR"),
            sources._perp("DOT-USDT-SWAP", base="DOT"),
        ],
    )
    membership = sources._membership(
        chain["ranking"],
        [sources._cid(chain["ranking"], r["instId"]) for r in sources._five_rows()],
    )
    topology = tmp_path / "topology"
    writer = sources._held_writer(topology)
    publication = connected.publish_checked_lane_selections_v1(
        membership=membership,
        ranking_snapshot=chain["ranking"],
        topology_state_root_base=topology,
        writer=writer,
        repository_sha=sources.REPO_SHA,
        producer_observed_at_unix=T0 - 3700,
    )
    bounds = connected.bind_occupied_lane_cap24_n1_instruments_v1(
        selections=publication.selections,
        topology_state_root_base=topology,
        ranking_state_root=chain["ranking_root"],
        universe_state_root=chain["universe_root"],
        reconciliation_state_root=chain["recon_root"],
        observed_portfolio=PortfolioTruthSnapshotV1(
            event_time_unix=T0 - 3700, wall_time_unix=T0 - 3700
        ),
        mark_price_by_native_id=chain["mark_price_by_native_id"],
        repository_sha=sources.REPO_SHA,
        session_id="planner-fixture",
        now_unix=T0 - 3700,
    )
    scope = PositionEpisodeScopeV1("planner-test-account", "INTERNAL_SIMULATED_EXECUTION")
    episodes = {
        l: SimpleNamespace(
            identity=PositionEpisodeIdentityV1(
                l, b.instrument_id, b.venue_native_id, "synthetic-planner-only:" + l, "long", scope
            ),
            binding=SimpleNamespace(has_open_position=True, pending_rotation_close=None),
        )
        for l, b in bounds.items()
    }
    review = review_for(
        bounds=bounds, membership=membership, chain=chain, event=T0 - 1740, weakest_lane="LANE_1"
    )
    near, dot = (
        sources._cid(chain["ranking"], native) for native in ("NEAR-USDT-SWAP", "DOT-USDT-SWAP")
    )
    incumbent = bounds["LANE_1"].instrument_id
    order = [b.instrument_id for l, b in bounds.items() if l != "LANE_1"] + [near, incumbent, dot]
    review = rank(review, order, T0 - 1740, "initial-nomination")
    owner = SlotRotationPlanOwnerV1(topology_root=topology, writer=writer)
    portfolio = PortfolioTruthSnapshotV1(
        positions=tuple(
            PositionTruthV1.from_signed(instrument_id=b.instrument_id, signed_quantity=1)
            for b in bounds.values()
        ),
        event_time_unix=T0 - 1739,
        wall_time_unix=T0 - 1739,
    )
    args = dict(
        selections=publication.selections, bindings=bounds, episodes=episodes, portfolio=portfolio
    )
    assert owner.prepare_v1(review=review, observed_unix=T0 - 1739, **args) == {}
    assert owner.active is not None
    try:
        yield SimpleNamespace(
            owner=owner,
            args=args,
            review=review,
            topology=topology,
            writer=writer,
            near=near,
            dot=dot,
            incumbent=incumbent,
            order=order,
        )
    finally:
        writer.release()


def test_restart_keeps_exact_pair_when_new_candidate_and_other_slot_are_stronger_or_weaker(world):
    w = world
    original = deepcopy(w.owner.active)
    owner = SlotRotationPlanOwnerV1(topology_root=w.topology, writer=w.writer)
    other_weak = w.args["bindings"]["LANE_5"].instrument_id
    order = (
        [w.dot, w.near]
        + [cid for cid in w.order if cid not in {w.dot, w.near, w.incumbent, other_weak}]
        + [w.incumbent, other_weak]
    )
    review = rank(w.review, order, T0 + 60, "new-stronger-and-other-weaker")
    requests = owner.prepare_v1(review=review, observed_unix=T0 + 61, **w.args)
    assert set(requests) == {"LANE_1"}
    assessment = assess_rotation_close_v1(
        requests["LANE_1"],
        bound=w.args["bindings"]["LANE_1"],
        episode_identity=w.args["episodes"]["LANE_1"].identity,
        event_time=T0 + 61,
    )
    assert assessment["allowed"]
    assert assessment["replacement"]["challenger"] == w.near
    assert assessment["replacement"]["displaced"] == w.incumbent
    assert owner.active == original


@pytest.mark.parametrize("case", ["1799-seconds", "stale", "future", "missing"])
def test_time_or_unusable_ranking_alone_cannot_close_or_reset_the_plan(world, case):
    w = world
    original = deepcopy(w.owner.active)
    now = T0 + 60 if case == "1799-seconds" else T0 + 61
    event = now - 301 if case == "stale" else now + 1 if case == "future" else now - 1
    review = None if case == "missing" else rank(w.review, w.order, event, case)
    result = w.owner.prepare_v1(review=review, observed_unix=now, **w.args)
    assert all(type(value) is RotationEntryHoldV1 for value in result.values())
    assert w.owner.active == original


def test_recovery_cancels_fixed_pair_and_same_snapshot_does_not_immediately_retarget(world):
    w = world
    order = (
        [w.dot, w.incumbent]
        + [cid for cid in w.order if cid not in {w.dot, w.incumbent, w.near}]
        + [w.near]
    )
    recovered = rank(w.review, order, T0 + 30, "incumbent-recovered-vs-reserved")
    before = {l: b.to_dict() for l, b in w.args["bindings"].items()}
    assert w.owner.prepare_v1(review=recovered, observed_unix=T0 + 31, **w.args) == {}
    assert w.owner.active is None
    assert w.owner.record["last_terminal"]["status"] == "ROTATION_INCUMBENT_RECOVERED"
    assert w.owner.prepare_v1(review=recovered, observed_unix=T0 + 32, **w.args) == {}
    assert w.owner.active is None
    assert {l: b.to_dict() for l, b in w.args["bindings"].items()} == before
    next_review = rank(recovered, order, T0 + 60, "next-distinct-ranking")
    assert w.owner.prepare_v1(review=next_review, observed_unix=T0 + 61, **w.args) == {}
    assert w.owner.active["nomination"]["candidate"] == w.dot
    assert w.owner.active["nomination"]["started_at_unix"] == T0 + 61


def test_mature_flat_slot_gets_only_an_entry_hold_when_handoff_is_missing(world):
    requests = world.owner.prepare_v1(
        review=None, observed_unix=T0 + 61, **{**world.args, "episodes": {}}
    )
    hold = requests["LANE_1"]
    assert type(hold) is RotationEntryHoldV1
    assert hold.validate_v1(bound=world.args["bindings"]["LANE_1"], now=T0 + 61)
    assert world.owner.active["phase"] == "WAITING"


def test_normal_double_play_successor_does_not_restart_the_instrument_wait(world):
    w = world
    original = deepcopy(w.owner.active["nomination"])
    selection = replace(
        w.args["selections"]["LANE_1"], selection_id="same-instrument-new-selection"
    ).with_integrity_digest()
    bound = replace(
        w.args["bindings"]["LANE_1"],
        selection_id=selection.selection_id,
        selection_integrity_digest=selection.integrity_digest,
    )
    previous = w.args["episodes"]["LANE_1"]
    successor = SimpleNamespace(
        identity=replace(previous.identity, episode_id="next-original-fill", position_side="short"),
        binding=SimpleNamespace(has_open_position=True, pending_rotation_close=None),
    )
    args = {
        **w.args,
        "selections": {**w.args["selections"], "LANE_1": selection},
        "bindings": {**w.args["bindings"], "LANE_1": bound},
        "episodes": {**w.args["episodes"], "LANE_1": successor},
    }
    review = rank(w.review, w.order, T0 + 60, "new-position-same-instrument")
    requests = w.owner.prepare_v1(review=review, observed_unix=T0 + 61, **args)
    assert set(requests) == {"LANE_1"}
    receipt = assess_rotation_close_v1(
        requests["LANE_1"], bound=bound, episode_identity=successor.identity, event_time=T0 + 61
    )
    assert (
        receipt["allowed"] and receipt["sources"]["episode"]["episode_id"] == "next-original-fill"
    )
    assert w.owner.active["nomination"] == original


def test_invalid_review_object_preserves_lock_without_suppressing_the_cycle(world):
    original = deepcopy(world.owner.active)
    result = world.owner.prepare_v1(review={"bad": "source"}, observed_unix=T0 + 61, **world.args)
    assert all(type(v) is RotationEntryHoldV1 for v in result.values())
    assert world.owner.active == original


def test_other_slot_cannot_consume_the_reserved_close_sources(world):
    w = world
    review = rank(w.review, w.order, T0 + 60, "scope-check")
    request = w.owner.prepare_v1(review=review, observed_unix=T0 + 61, **w.args)["LANE_1"]
    with pytest.raises(ValueError, match="ROTATION_NOMINATION_INSTRUMENT_SCOPE_MISMATCH"):
        assess_rotation_close_v1(
            request,
            bound=w.args["bindings"]["LANE_2"],
            episode_identity=w.args["episodes"]["LANE_2"].identity,
            event_time=T0 + 61,
        )


def test_stale_second_owner_cannot_overwrite_a_newer_plan_generation(world):
    w = world
    stale = SlotRotationPlanOwnerV1(topology_root=w.topology, writer=w.writer)
    order = [w.incumbent] + [cid for cid in w.order if cid != w.incumbent]
    recovered = rank(w.review, order, T0 + 30, "recovered-new-generation")
    w.owner.prepare_v1(review=recovered, observed_unix=T0 + 31, **w.args)
    before = w.owner.path.read_bytes()
    with pytest.raises(ValueError, match="ROTATION_PLAN_GENERATION_CONFLICT"):
        stale._save()
    assert w.owner.path.read_bytes() == before


def test_restart_finishes_archive_to_index_transition_without_a_new_timer(world, monkeypatch):
    w = world
    original = deepcopy(w.owner.active["nomination"])
    save = w.owner._save
    monkeypatch.setattr(
        w.owner,
        "_save",
        lambda: (_ for _ in ()).throw(OSError("power-loss boundary after archive")),
    )
    with pytest.raises(OSError):
        w.owner._finish("ROTATION_INCUMBENT_RECOVERED", ranking_key=["final-ranking", "a" * 64])
    monkeypatch.setattr(w.owner, "_save", save)
    recovered = SlotRotationPlanOwnerV1(topology_root=w.topology, writer=w.writer)
    assert recovered.active is None
    assert recovered.record["last_terminal"]["plan_id"] == original["plan_id"]
    assert recovered.record["last_terminal"]["ranking_key"] == ["final-ranking", "a" * 64]
    archives = list((recovered.root / "rotation_history").glob("*.json"))
    assert len(archives) == 1
    assert json.loads(archives[0].read_text())["nomination"] == original


@pytest.mark.parametrize("malformation", ["truncated", "array", "terminal-list", "terminal-key"])
def test_controller_reader_fences_new_entry_without_repairing_unreadable_metadata(
    world, malformation
):
    if malformation == "truncated":
        broken = b"{"
    elif malformation == "array":
        broken = b"[]"
    else:
        raw = json.loads(world.owner.path.read_text())
        raw["active"] = None
        raw["last_terminal"] = (
            []
            if malformation == "terminal-list"
            else dict(plan_id="bad-terminal", status="COMPLETED", ranking_key=123)
        )
        raw["content_digest"] = _digest({k: v for k, v in raw.items() if k != "content_digest"})
        broken = json.dumps(raw).encode()
    world.owner.path.write_bytes(broken)
    owner = load_slot_rotation_plan_owner_v1(topology_root=world.topology, writer=world.writer)
    assert owner.status_v1()["phase"] == "UNREADABLE"
    requests = owner.prepare_v1(**world.args)
    assert set(requests) == set(world.args["bindings"])
    assert all(type(value) is RotationJournalEntryHoldV1 for value in requests.values())
    assert world.owner.path.read_bytes() == broken


@pytest.mark.parametrize(
    "field,value",
    [("lane_id", "LANE_2"), ("candidate", "foreign-instrument"), ("deadline_unix", T0 + 3600)],
)
def test_semantically_forged_journal_is_rejected_even_after_outer_hash_rebinding(
    world, field, value
):
    path = world.owner.path
    raw = json.loads(path.read_text())
    raw["active"]["nomination"][field] = value
    body = {k: v for k, v in raw.items() if k != "content_digest"}
    raw["content_digest"] = _digest(body)
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="ROTATION_NOMINATION"):
        SlotRotationPlanOwnerV1(topology_root=world.topology, writer=world.writer)
