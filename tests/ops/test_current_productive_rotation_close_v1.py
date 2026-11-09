"""One better candidate closes only the weakest occupied stable slot."""

from dataclasses import replace
import json

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_post_close_feedback_v1 import (
    PostCloseRankingReviewRequestV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_rotation_close_v1 import (
    RotationCloseRequestV1,
    assess_rotation_close_v1,
    verify_pending_rotation_close_v1,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    build_membership_context_artifact_v1,
    membership_context_artifact_from_dict,
)
from src.ops.mf_membership_selector_and_rotation_runtime_contract_v1 import (
    select_membership_v1,
    parse_eligible_cap22_top20,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
)
from tests.test_mf_membership_selector_and_rotation_runtime_contract_v1 import _provenance
from tests.ops.test_bounded_slot_connected_roundtrip_v1 import connected_close, T0, utc
from tests.ops import test_bounded_slot_connected_roundtrip_v1 as connected
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)


def review_for(*, bounds, membership, chain, event, weakest_lane):
    initial = ProductiveFuturesRankingSnapshotV1.from_dict(chain["ranking"])
    observation = replace(
        initial, ranking_snapshot_id="rotation-held-observation", event_time=utc(T0 - 3600)
    ).with_integrity_digest()
    prior = build_membership_context_artifact_v1(
        ordered_instrument_ids=membership.ordered_instrument_ids,
        cap22_provenance=_provenance(observation.to_dict()),
        bootstrap=False,
        prior_membership_reference=membership.instance_id,
    )
    history = chain.get("rotation_membership_chain", (membership, prior))
    if "rotation_membership_chain" in chain:
        prior = membership
    weakest = bounds[weakest_lane].instrument_id
    # Explicit synthetic upstream rank order: the weakest can occupy ANY slot.
    ordered = sorted(
        initial.ranked_candidates,
        key=lambda r: (
            2
            if r.canonical_instrument_id == weakest
            else 1
            if r.venue_native_id == "NEAR-USDT-SWAP"
            else 0,
            r.rank,
        ),
    )
    ranking = replace(
        initial,
        ranking_snapshot_id=f"rotation-one-better:{int(event)}",
        event_time=utc(event),
        ranked_candidates=tuple(replace(r, rank=i + 1) for i, r in enumerate(ordered)),
    ).with_integrity_digest()
    return PostCloseRankingReviewRequestV1(
        ranking, _provenance(ranking.to_dict()), prior, tuple(history)
    )


class RotationDriver:
    def __init__(self, root, lane):
        self.root, self.lane = root, lane
        self.initial_record = None

    def _run(self, inputs, closes, event, prefix):
        bounds, host = inputs["bounds"], inputs["host"]
        observed = connected.portfolio_from_accounting(bounds, inputs["sessions"], event + 1)
        connected.persist_applied_inventory(
            host.root / "reconciliation", observed, inputs["sessions"]
        )
        host.fetch = connected._fetch(
            uid="acct-1",
            positions=[
                dict(
                    instId=bounds[l].venue_native_id,
                    posSide="net",
                    pos=str(connected.signed_accounting_quantity(s)),
                )
                for l, s in inputs["sessions"].items()
            ],
        )
        host.clock = lambda: event + 1
        recovery = host.observe_v1(bounds)
        recovery.recover_v1(host.owner, connected._produce(value="1000", epoch=utc(event + 1)))
        review = review_for(
            bounds=bounds,
            membership=inputs["membership"],
            chain=inputs["chain"],
            event=event,
            weakest_lane=self.lane,
        )
        from src.ops.mf_membership_context_artifact_contract_v1 import (
            write_membership_context_artifact_v1,
        )

        for artifact in review.observation_chain:
            write_membership_context_artifact_v1(artifact, store_root=self.root / "membership")
        self.membership = review.prior
        base_ranking = ProductiveFuturesRankingSnapshotV1.from_dict(inputs["chain"]["ranking"])
        base_ranking = replace(
            base_ranking,
            ranking_snapshot_id=review.prior.cap22_provenance.ranking_snapshot_id,
            event_time=review.prior.cap22_provenance.ranking_event_time,
        ).with_integrity_digest()
        assert (
            base_ranking.integrity_digest == review.prior.cap22_provenance.ranking_integrity_digest
        )
        kwargs = connected.market(bounds, closes, event, prefix, self.root / "g17")
        kwargs.update(
            host_budget_recovery=recovery,
            observed_portfolio=observed,
            position_episode_bindings=inputs["episodes"],
            position_episode_scope=inputs["scope"],
            occupancy_payloads=connected._positions_payload(
                *[
                    (bounds[l].venue_native_id, "net", connected.signed_accounting_quantity(s))
                    for l, s in inputs["sessions"].items()
                ]
            ),
        )
        cap = connected.ProductiveFullAutonomyCap24BindContextV1(
            inputs["chain"]["ranking_root"],
            inputs["chain"]["universe_root"],
            host.root / "reconciliation",
            observed,
            {n: str(closes[-1]) for n in inputs["chain"]["mark_price_by_native_id"]},
            prefix,
            event + 1,
        )
        result = connected.run(
            membership=review.prior,
            ranking_snapshot=base_ranking.to_dict(),
            topology_state_root_base=inputs["topology"],
            lane_assignment_writer=inputs["writer"],
            cap24_bind=cap,
            repository_sha=connected.sources.REPO_SHA,
            producer_observed_at_unix=event + 1,
            target_cardinality=5,
            portfolio_budget_owner=host.owner,
            rotation_ranking_review=review,
            **kwargs,
        )
        return result, recovery

    def nominate(self, inputs):
        from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
            checkpoint_root_for,
        )

        closes = tuple(inputs["closes"]) + tuple(
            inputs["closes"][-1] + 0.1 * i for i in range(1, 32)
        )
        result, recovery = self._run(inputs, closes, T0 - 1740, "nominate-rotation")
        self.path = checkpoint_root_for(inputs["topology"]) / "rotation_plan_v1.json"
        self.initial_record = json.loads(self.path.read_text())
        inputs["chain"]["rotation_membership_chain"] = tuple(
            membership_context_artifact_from_dict(a)
            for a in self.initial_record["active"]["nomination"]["initial_sources"][
                "observation_chain"
            ]
        )
        plan = self.initial_record["active"]["nomination"]
        assert plan["lane_id"] == self.lane
        assert plan["deadline_unix"] - plan["started_at_unix"] == 1800
        assert all(
            p.n1_consumer_result.position_management_close_intent is None
            for p in result.readiness_projections.values()
        )
        return recovery

    def close(self, inputs):
        result, _recovery = self._run(inputs, inputs["closes"], inputs["event"], "execute-rotation")
        record = json.loads(self.path.read_text())
        assert record["active"]["nomination"] == self.initial_record["active"]["nomination"]
        assert record["active"]["phase"] == "CLOSE_REQUESTED"
        return {l: p.n1_consumer_result for l, p in result.readiness_projections.items()}


def test_unreadable_rotation_journal_keeps_existing_risk_exits_and_blocks_new_entry(
    tmp_path, monkeypatch, synthetic_ports_and_isolation
):
    class ProbeFinished(Exception):
        pass

    class FaultDriver(RotationDriver):
        world = None

        def close(self, inputs):
            self.world = inputs
            self.path.write_bytes(b"{")
            closes = tuple(inputs["closes"]) + (inputs["closes"][-1] + 300,)
            result, _recovery = self._run(inputs, closes, T0 + 120, "unreadable-journal-risk")
            assert result.rotation_status_v1["phase"] == "UNREADABLE"
            assert self.path.read_bytes() == b"{", "Unreadable original metadata was overwritten"
            for lane, projection in result.readiness_projections.items():
                consumer = projection.n1_consumer_result
                assert consumer.position_management_close_intent is not None
                assert consumer.s7_invocation.cycle_result.replay_pass == "true"
                assert consumer.s7_invocation.cycle_result.decision_outcome == "exit"
                assert (
                    consumer.s7_invocation.cycle_result.replay.intermediate.entry_exit_decision.exit_class.value
                    != "time_exit"
                )
                assert projection.bound_instrument == inputs["bounds"][lane]
            raise ProbeFinished

    driver = FaultDriver(tmp_path, "LANE_1")
    try:
        with pytest.raises(ProbeFinished):
            connected_close(tmp_path, monkeypatch, 5, "LANE_1", rotation_driver=driver)
    finally:
        if driver.world is not None:
            driver.world["host"].close()
            driver.world["writer"].release()


def test_journal_failure_entry_hold_restricts_real_confirmed_candidate_without_replacing_c3(
    tmp_path, monkeypatch
):
    from tests.ops import test_current_productive_occupied_scope_continuity_v1 as flow
    from src.ops.full_core_live_path_composition_root_v1.current_productive_rotation_close_v1 import (
        RotationJournalEntryHoldV1,
    )

    cursor = None
    for step in range(2):
        current = flow._cycle(tmp_path, step=step, incoming=cursor)
        assert current.replay_pass == "true"
        cursor = current.outgoing_cursor
    original = flow.run_current_productive_master_v2_runtime_cycle_v1
    hold = RotationJournalEntryHoldV1(json.dumps(flow._bound().to_dict()), "a" * 64)

    def restricted(**kwargs):
        return original(**kwargs, rotation_time_exit_only=True, rotation_exit_request=hold)

    monkeypatch.setattr(flow, "run_current_productive_master_v2_runtime_cycle_v1", restricted)
    denied = flow._cycle(tmp_path, step=2, incoming=cursor)
    assert denied.replay_pass == "true", denied.fail_reasons
    assert denied.decision_outcome not in {"enter_long", "enter_short"}
    state = (
        denied.replay.intermediate.directional_confirmation_progress_after.bull_confirmation_state
    )
    assert (
        state.assessment_state.value == "confirmed"
        and state.distinct_confirmation_observation_count == 2
    )


@pytest.mark.parametrize("weakest_lane", ["LANE_1", "LANE_5"])
def test_actual_five_slot_core_closes_only_rank_weakest_and_keeps_other_slots(
    tmp_path, monkeypatch, weakest_lane, synthetic_ports_and_isolation
):
    driver = RotationDriver(tmp_path, weakest_lane)
    world = connected_close(tmp_path, monkeypatch, 5, weakest_lane, rotation_driver=driver)
    try:
        target = world["episodes"][weakest_lane]
        proof = target.binding.pending_rotation_close
        assert proof is not None
        assert (
            verify_pending_rotation_close_v1(
                proof, bound=world["bounds"][weakest_lane], episode_identity=target.identity
            )
            == proof
        )
        assert proof["replacement"]["displaced"] == target.identity.instrument_id
        assert proof["replacement"]["challenger"] not in {
            b.instrument_id for b in world["bounds"].values()
        }
        assert proof["minimum_holding_seconds"] == 1800
        assert target.binding.simulated_accounting_close is not None
        for lane, bound in world["bounds"].items():
            assert world["pairs"][lane][1] == bound
            if lane != weakest_lane:
                assert world["sessions"][lane].position is not None
                assert world["episodes"][lane].binding.pending_rotation_close is None
                assert world["host"].owner.active_slot_sum_v1(lane) > 0
        # Membership/topology are NOT replaced merely because a close was planned.
        assert (
            world["publication"].topology.instrument_to_lane()[target.identity.instrument_id]
            == weakest_lane
        )
    finally:
        world["host"].close()
        world["writer"].release()


@pytest.mark.parametrize("direction", [1, -1], ids=["two-long", "two-short"])
def test_rotation_replacement_requires_own_two_confirmations_before_next_entry(
    tmp_path, monkeypatch, direction, synthetic_ports_and_isolation
):
    lane = "LANE_1"
    observations = []
    execution_orders = []
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1 import (
        readiness_join_v1 as ready,
    )

    original_invoke = ready.invoke_occupied_lane_governed_cycle_n1_consumer_v1

    def observe_invoke(pairs, **kwargs):
        result = original_invoke(pairs, **kwargs)
        portfolio = kwargs.get("observed_portfolio")
        if portfolio is not None and any(
            b.venue_native_id == "NEAR-USDT-SWAP" for _, b in pairs.values()
        ):
            occupied = {p.instrument_id for p in portfolio.positions if p.signed_quantity != 0}
            expected = sorted(pairs, key=lambda l: (pairs[l][1].instrument_id not in occupied, l))
            assert list(result) == expected
            execution_orders.append(expected)
        return result

    original_run = connected.run
    original_ready = connected.orchestrator.compose_occupied_lane_n1_host_join_readiness_v1

    def trace_readiness(*args, **kwargs):
        result = original_ready(*args, **kwargs)
        for l, projection in result.items():
            governed = projection.n1_consumer_result.governed_cycle_result
            assert governed.disposition != "FAIL_CLOSED", (
                l,
                governed.first_genuine_blocker,
                governed.extra,
            )
        return result

    def observe_run(**kwargs):
        result = original_run(**kwargs)
        if hasattr(result, "readiness_projections"):
            invocation = result.readiness_projections[lane].n1_consumer_result.s7_invocation
            if invocation.bound_instrument.venue_native_id == "NEAR-USDT-SWAP":
                core = invocation.cycle_result
                context = core.replay.intermediate.market_context
                scope = core.replay.intermediate.current_scope
                assert context.instrument_id == invocation.bound_instrument.instrument_id
                assert context.mark_price == pytest.approx(
                    float(kwargs["cap24_bind"].mark_price_by_native_id["NEAR-USDT-SWAP"])
                )
                assert scope.instrument_id == context.instrument_id
                assert scope.initial_volatility_distance == pytest.approx(
                    scope.reference_price * scope.volatility_estimate
                )
                carrier = core.replay.intermediate.directional_confirmation_progress_after
                state = (
                    carrier.bull_confirmation_state
                    if direction == 1
                    else carrier.bear_confirmation_state
                )
                assert (
                    state.instrument.canonical_instrument_id
                    == invocation.bound_instrument.instrument_id
                )
                observations.append(
                    (
                        core.decision_outcome,
                        state.distinct_confirmation_observation_count,
                        state.assessment_state.value,
                        state.latest_accepted_market_observation_epoch,
                    )
                )
        return result

    monkeypatch.setattr(connected, "run", observe_run)
    monkeypatch.setattr(ready, "invoke_occupied_lane_governed_cycle_n1_consumer_v1", observe_invoke)
    monkeypatch.setattr(
        connected.orchestrator, "compose_occupied_lane_n1_host_join_readiness_v1", trace_readiness
    )
    try:
        connected.roundtrip(
            tmp_path,
            monkeypatch,
            5,
            lane,
            True,
            rotation_driver=RotationDriver(tmp_path, lane),
            follow_direction=direction,
        )
    except BaseException as exc:
        raise AssertionError(observations) from exc
    expected_entry = "enter_long" if direction == 1 else "enter_short"
    entries = [r for r in observations if r[0] in {"enter_long", "enter_short"}]
    assert entries and entries[0][:3] == (expected_entry, 2, "confirmed"), observations
    first_entry = observations.index(entries[0])
    assert all(r[0] not in {"enter_long", "enter_short"} for r in observations[:first_entry])
    assert any(r[1] == 1 and r[2] == "candidate" for r in observations[:first_entry]), observations
    assert observations[0][1] < 2, "Replacement inherited a confirmed predecessor"
    epochs = [r[3] for r in observations[: first_entry + 1] if r[1] in {1, 2}]
    assert len(set(epochs)) >= 2, "Repeated observation counted as two confirmations"
    assert ["LANE_2", "LANE_3", "LANE_4", "LANE_5", "LANE_1"] in execution_orders
