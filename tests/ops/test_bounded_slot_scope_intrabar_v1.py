"""Offline characterization of the first close boundary with five open slots."""

from datetime import datetime
from pathlib import Path

import pytest

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    invoke_join_v1 as occupied,
)
from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
    orchestrator_v1 as host_orchestrator,
)
from src.ops.p5_10_productive_activation_and_binding_v1 import (
    productive_cycle_bind_seam_v1 as layered_binding,
)
from tests.ops import test_bounded_slot_connected_roundtrip_v1 as fixture
from tests.ops.test_current_scope_mark_clock_v1 import provenance
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
    SNAPSHOT_FILENAME,
)
from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
    read_occupied_scope_mark_snapshot_v1,
    restore_layered_core_episode_v1,
)
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)


@pytest.mark.parametrize(
    "scenario",
    ["just-opened-same-c1", "established-same-c1", "next-c1-control", "occupied-mark-below-scope"],
)
def test_valid_scope_mark_at_the_original_five_slot_host_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, scenario: str
):
    world = fixture.connected_open_positions(tmp_path, monkeypatch, 5)
    bounds, sessions, host = world["bounds"], world["sessions"], world["host"]
    target = "LANE_1"
    try:
        holds = {lane: host.owner.active_slot_sum_v1(lane) for lane in bounds}
        quantities = {
            lane: fixture.signed_accounting_quantity(session) for lane, session in sessions.items()
        }
        assert len(holds) == len(quantities) == 5
        assert all(amount > 0 for amount in holds.values())
        assert all(quantity > 0 for quantity in quantities.values())

        def unexpected_selection(**kwargs):
            pytest.fail("The already bound N1 path called instrument selection")

        monkeypatch.setattr(
            host_orchestrator, "publish_checked_lane_selections_v1", unexpected_selection
        )
        monkeypatch.setattr(
            host_orchestrator, "bind_occupied_lane_cap24_n1_instruments_v1", unexpected_selection
        )

        seals = {}
        original_seam = layered_binding.run_p5_layered_core_authority_seam_v1

        def record_seal(*args, **kwargs):
            result = original_seam(*args, **kwargs)
            if result.seal is not None:
                seals[result.seal.instrument_id] = result.seal
            return result

        monkeypatch.setattr(layered_binding, "run_p5_layered_core_authority_seam_v1", record_seal)

        def cycle_inputs(closes, event, prefix, *, target_mark=None, receipt_delay=1.25):
            now = event + receipt_delay
            mark_event = now - 0.125

            class OfflineClock(datetime):
                @classmethod
                def now(cls, tz=None):
                    return cls.fromtimestamp(now, tz)

            monkeypatch.setattr(occupied, "datetime", OfflineClock)
            mark_by_lane = {
                lane: target_mark if lane == target and target_mark is not None else closes[-1]
                for lane in bounds
            }
            source_by_lane = {
                lane: provenance(
                    native=bound.venue_native_id,
                    mark=mark_by_lane[lane],
                    index=mark_by_lane[lane] * 0.995,
                    event=mark_event,
                    captured=now,
                )
                for lane, bound in bounds.items()
            }
            for source in source_by_lane.values():
                assert source.require_current_mark_clock_v1(observed_unix=now) == mark_event
            observed = fixture.portfolio_from_accounting(bounds, sessions, now)
            fixture.persist_applied_inventory(host.root / "reconciliation", observed, sessions)
            inputs = fixture.market(bounds, closes, event, prefix, tmp_path / "g17")
            inputs.update(
                observed_unix=now,
                canonical_price_provenance_by_lane=source_by_lane,
                portfolio_budget_owner=host.owner,
                host_budget_recovery=world["recovery"],
                observed_portfolio=observed,
                position_episode_bindings=world["episodes"],
                position_episode_scope=world["scope"],
                occupancy_payloads=fixture._positions_payload(
                    *(
                        (bounds[lane].venue_native_id, "net", qty)
                        for lane, qty in quantities.items()
                    )
                ),
            )
            return inputs

        event, closes = world["event"], world["closes"]
        accepted_candles = world["kwargs"]["candles_payload_by_lane"]
        if scenario != "just-opened-same-c1":
            event += 60
            closes = (*closes, closes[-1] + 0.1)
            prior_inputs = cycle_inputs(closes, event, "establish-open-slots")
            prior = occupied.invoke_occupied_lane_governed_cycle_n1_consumer_v1(
                world["pairs"], **prior_inputs
            )
            assert all(item.s7_invocation is not None for item in prior.values())
            assert all(
                item.governed_cycle_result.position_management_execution_handoff is None
                for item in prior.values()
            )
            assert not any(seal.switch_condition_met for seal in seals.values())
            seals.clear()
            accepted_candles = prior_inputs["candles_payload_by_lane"]

        root = Path(world["pairs"][target][0].lane_state_root)
        before = restore_layered_core_episode_v1(
            root, expected_instrument_id=bounds[target].instrument_id
        )
        target_mark = closes[-1] * 0.98
        if scenario == "occupied-mark-below-scope":
            target_mark = before.running_reference.reference_price_r_t - before.scope.d_t * 0.75
        if scenario == "next-c1-control":
            event += 60
            closes = (*closes, closes[-1] + 0.1)
        inputs = cycle_inputs(
            closes, event, "scope-intrabar", target_mark=target_mark, receipt_delay=1.5
        )
        if scenario != "next-c1-control":
            assert inputs["candles_payload_by_lane"] == accepted_candles
        if scenario == "just-opened-same-c1":
            with pytest.raises(
                occupied.FullAutonomyOccupiedLaneGovernedCycleN1ConsumerJoinError,
                match="POSITION_EPISODE_ENTRY_AFTER_OBSERVATION",
            ):
                occupied.invoke_occupied_lane_governed_cycle_n1_consumer_v1(
                    world["pairs"], **inputs
                )
            assert not seals
            assert {lane: host.owner.active_slot_sum_v1(lane) for lane in bounds} == holds
            result = occupied.invoke_occupied_lane_governed_cycle_n1_consumer_v1(
                world["pairs"], occupied_scope_mark_lane_id=target, **inputs
            )[target]
            assert result.s7_invocation is not None, (
                result.governed_cycle_result.first_genuine_blocker
            )
            assert result.governed_cycle_result.position_management_execution_handoff is not None
            assert result.governed_cycle_result.post_count == 0
            assert seals[bounds[target].instrument_id].switch_condition_met
            return
        if scenario == "occupied-mark-below-scope":
            result = occupied.invoke_occupied_lane_governed_cycle_n1_consumer_v1(
                world["pairs"], occupied_scope_mark_lane_id=target, **inputs
            )[target]
            assert result.s7_invocation is not None, (
                result.governed_cycle_result.first_genuine_blocker
            )
            assert result.governed_cycle_result.master_v2_decision == "hold"
            assert result.governed_cycle_result.position_management_execution_handoff is None
            seal = seals[bounds[target].instrument_id]
            assert not seal.switch_condition_met and seal.cm_t < seal.d_t
            assert seal.cm_t > seal.d_t * 0.4
            snapshot = read_occupied_scope_mark_snapshot_v1(root)
            assert snapshot["mark"]["pending_close_episode_id"] is None
            assert snapshot["snapshot"]["mechanical_step_count"] == before.mechanical_step_count + 1
            # Damage the replacement record while the old manifest is still present.
            # The occupied position must retain its cursor and stop.
            snapshot_path = root / SNAPSHOT_FILENAME
            snapshot_path.write_text("{}")
            cursor_path = root / occupied.CURSOR_FILENAME
            before_cursor = cursor_path.read_bytes()
            retry_inputs = {**inputs, "cycle_id_prefix": "corrupt-occupied-mark"}
            retry = occupied.invoke_occupied_lane_governed_cycle_n1_consumer_v1(
                world["pairs"], occupied_scope_mark_lane_id=target, **retry_inputs
            )[target]
            assert (
                retry.governed_cycle_result.first_genuine_blocker
                == "OCCUPIED_MARK_SNAPSHOT_INVALID"
            )
            assert retry.governed_cycle_result.position_management_execution_handoff is None
            assert cursor_path.read_bytes() == before_cursor and snapshot_path.read_text() == "{}"
            return
        results = occupied.invoke_occupied_lane_governed_cycle_n1_consumer_v1(
            world["pairs"], **inputs
        )
        assert {lane: result.bound_instrument for lane, result in results.items()} == bounds
        assert all(result.governed_cycle_result.post_count == 0 for result in results.values())
        assert {lane: host.owner.active_slot_sum_v1(lane) for lane in bounds} == holds
        assert {
            lane: fixture.signed_accounting_quantity(session) for lane, session in sessions.items()
        } == quantities

        result = results[target]
        cycle = result.governed_cycle_result
        if scenario == "established-same-c1":
            assert cycle.first_genuine_blocker == "DUPLICATE_C1"
            assert not cycle.t2_consumed and result.s7_invocation is None
            assert not seals
        else:
            assert set(seals) == {bound.instrument_id for bound in bounds.values()}
            seal = seals[bounds[target].instrument_id]
            assert seal.switch_condition_met and seal.cm_t >= seal.d_t
            assert (seal.regime_pre, seal.regime_post) == ("bull", "bear")
            assert all(
                not seals[bound.instrument_id].switch_condition_met
                for lane, bound in bounds.items()
                if lane != target
            )
            assert cycle.master_v2_decision == "reduce"
            assert cycle.first_genuine_blocker == "REDUCE_RISK_RULE_REQUIRED"
        assert all(
            item.governed_cycle_result.position_management_execution_handoff is None
            for item in results.values()
        )
    finally:
        host.close()
        world["writer"].release()
