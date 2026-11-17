from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from src.ops.mf_membership_context_artifact_contract_v1 import (
    build_bootstrap_membership_from_cap22_snapshot_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.slot_loss_budget_v1 import (
    SlotCapitalAllocationV1,
)
from tests.ops import test_bounded_slot_connected_roundtrip_v1 as fixture
from tests.ops import test_bounded_slot_scope_close_v1 as scope_test


@pytest.mark.parametrize("opening_side", ["long", "short"])
def test_native_l10_plans_one_net_reversal_on_the_ranked_slot(tmp_path, monkeypatch, opening_side):
    rank_path = tmp_path / "ranking/productive_futures_ranking_snapshot_v1.json"
    host_type = fixture.PortfolioBudgetHostV1

    def no_network(event, arguments):
        raise AssertionError("Use simulated ports for the occupied lane")

    def fund_simulated_host(**kwargs):
        return host_type(
            **kwargs,
            slot_capital_allocation=SlotCapitalAllocationV1(
                "acct-1", "offline-reversal", tuple((f"LANE_{i}", Decimal(25)) for i in range(1, 6))
            ),
        )

    def select_ranked_membership(ranking, _fixture_order):
        membership = build_bootstrap_membership_from_cap22_snapshot_v1(
            snapshot_path=rank_path, source_relative_path=rank_path.relative_to(tmp_path).as_posix()
        )
        assert membership.cap22_provenance.ranking_integrity_digest == ranking["integrity_digest"]
        return membership

    monkeypatch.setattr("socket.socket.connect", no_network)
    monkeypatch.setattr(fixture.sources, "_membership", select_ranked_membership)
    monkeypatch.setattr(fixture, "PortfolioBudgetHostV1", fund_simulated_host)
    world = fixture.connected_open_positions(tmp_path, monkeypatch, 5, opening_side=opening_side)
    host = world["host"]
    try:
        lane = "LANE_1"
        slot, bound = world["pairs"][lane]
        selection = world["publication"].selections[lane]
        assert selection.selected_rank == 1 and selection.instrument_id == bound.instrument_id
        assert (
            selection.ranking_snapshot_id == slot.ranking_snapshot_id == bound.ranking_snapshot_id
        )
        policy = host.owner.entry_budget_policy_v1()
        assert policy.per_slot_reserved_notional_limit == 25
        assert policy.aggregate_reserved_notional_limit == 125
        previous = host.owner.local_commitment_readback_v1()
        direction = 1 if opening_side == "long" else -1
        event = world["event"] + 60
        closes = (*world["closes"], world["closes"][-1] + direction * 0.1)
        world["recovery"] = scope_test._counter_recovery(world, event + 1.25)
        baseline = scope_test._market(
            world, tmp_path / "g17", closes, event, event + 1.25, "occupied", monkeypatch
        )
        occupied = scope_test.occupied.invoke_occupied_lane_governed_cycle_n1_consumer_v1
        held = occupied(world["pairs"], **baseline)[lane].governed_cycle_result
        assert held.position_management_reversal is None

        now = event + 1.5
        mark = closes[-1] * (1 - direction * 0.02)
        if opening_side == "long":
            favorable = scope_test._market(
                world,
                tmp_path / "g17",
                closes,
                event,
                now,
                "favorable",
                monkeypatch,
                target=lane,
                mark=closes[-1] * 1.03,
            )
            continued = occupied(world["pairs"], occupied_scope_mark_lane_id=lane, **favorable)[
                lane
            ]
            assert continued.governed_cycle_result.master_v2_decision == "hold"
            now += 0.25
            mark = closes[-1] * 1.02
        world["recovery"] = scope_test._counter_recovery(world, now)
        switched = scope_test._market(
            world,
            tmp_path / "g17",
            closes,
            event,
            now,
            "switch",
            monkeypatch,
            target=lane,
            mark=mark,
        )
        result = occupied(world["pairs"], occupied_scope_mark_lane_id=lane, **switched)[lane]
        governed = result.governed_cycle_result
        plan = governed.position_management_reversal
        assert plan is not None, governed.first_genuine_blocker
        assert plan.episode == world["episodes"][lane].identity
        assert plan.selection_id == bound.selection_id
        assert plan.current_contracts == fixture.signed_accounting_quantity(world["sessions"][lane])
        assert plan.target_contracts * direction < 0
        assert plan.signed_order_contracts == plan.target_contracts - plan.current_contracts
        assert plan.slot_capital_basis_usdc == 25 and plan.portfolio_slot_capital_usdc == 125
        assert 0 < plan.target_notional_usdc <= 25
        seal = scope_test.read_occupied_scope_mark_snapshot_v1(Path(slot.lane_state_root))
        assert plan.scope_digest == seal["digest"]
        assert plan.scope_distance == Decimal(str(seal["snapshot"]["scope"]["d_t"]))
        assert plan.protective_stop == plan.reference_mark + direction * plan.scope_distance
        assert seal["mark"]["pending_close_episode_id"] is None
        assert governed.position_management_execution_handoff is None
        assert governed.final_order_envelope is None
        assert governed.post_count == 0 and not governed.permit_created
        assert host.owner.local_commitment_readback_v1() == previous
        ledger = json.loads((Path(result.evidence_root) / scope_test.LEDGER_FILENAME).read_bytes())
        assert ledger["direct_reversal"] == plan.to_dict_v1()
        assert ledger["direct_reversal_digest"] == plan.digest_v1()
        accounting = world["sessions"][lane]
        before = accounting.to_durable_dict()
        fill = fixture.build_simulated_fill_v1(
            fill_id="direct-reversal:" + plan.digest_v1(),
            instrument_id=bound.venue_native_id,
            side=plan.to_dict_v1()["side"].upper(),
            quantity=str(abs(plan.signed_order_contracts)),
            mark_price=str(plan.reference_mark),
            contract=accounting.contract,
            event_time_unix=now + 0.25,
        )
        foreign_ledger = {**ledger, "direct_reversal_digest": "foreign"}
        with pytest.raises(ValueError, match="DIRECT_REVERSAL_SIMULATED_FILL_SOURCE_MISMATCH"):
            plan.apply_simulated_fill_v1(ledger=foreign_ledger, accounting=accounting, fill=fill)
        with pytest.raises(RuntimeError, match="NET_REVERSAL_FILL_MISMATCH"):
            plan.apply_simulated_fill_v1(
                ledger=ledger,
                accounting=accounting,
                fill=replace(fill, quantity=abs(plan.current_contracts)),
            )
        assert accounting.to_durable_dict() == before
        booked = plan.apply_simulated_fill_v1(
            ledger=ledger,
            accounting=accounting,
            fill=fill,
            budget_owner=host.owner,
        )
        assert booked.action_code == ("REVERSE_TO_SHORT" if direction > 0 else "REVERSE_TO_LONG")
        assert fixture.signed_accounting_quantity(accounting) == plan.target_contracts
        assert accounting.fill_order == [*before["fill_order"], fill.fill_id]
        assert accounting.cumulative_fees == Decimal(before["cumulative_fees"]) + fill.fee
        persisted = accounting.to_durable_dict()
        reopened = type(accounting).from_durable_dict(json.loads(json.dumps(persisted)))
        cold_before = reopened.to_durable_dict()
        assert cold_before["portfolio_state"] == persisted["portfolio_state"]
        assert cold_before["risk_state"] == persisted["risk_state"]
        assert cold_before["fill_order"] == persisted["fill_order"]
        repeated = plan.apply_simulated_fill_v1(ledger=ledger, accounting=reopened, fill=fill)
        assert repeated.idempotent_replay
        assert repeated.accounting_output_digest == booked.accounting_output_digest
        assert reopened.to_durable_dict() == cold_before
        settled = (
            accounting.realized_pnl + accounting.funding_pnl - accounting.cumulative_fees
        ) * plan.quote_to_usdc
        slot_basis = host.owner.slot_capital_basis_v1(lane)
        assert slot_basis.net_basis_usdc == 25 + settled
        assert (slot_basis.net_basis_usdc > 25) == (opening_side == "long")
        assert all(
            host.owner.slot_capital_basis_v1(other).net_basis_usdc == 25
            for other in world["bounds"]
            if other != lane
        )
        assert plan.apply_simulated_fill_v1(
            ledger=ledger,
            accounting=accounting,
            fill=fill,
            budget_owner=host.owner,
        ).idempotent_replay
        if opening_side == "long":
            next_identity = fixture.bind_simulated_accounting_episode_identity_v1(
                identity=replace(plan.episode, position_side="short"),
                opening_fill=fill,
            )
            world["fills"][lane].append(fill)
            world["episodes"][lane] = fixture.create_position_episode_from_simulated_accounting_v1(
                **fixture._args(tmp_path / "successor", next_identity),
                session=accounting,
                fills=world["fills"][lane],
            )
            next_event = event + 60
            next_closes = (*closes, closes[-1] - 0.1)
            world["recovery"] = scope_test._counter_recovery(world, next_event + 1.25)
            held = scope_test._market(
                world,
                tmp_path / "g17",
                next_closes,
                next_event,
                next_event + 1.25,
                "successor-occupied",
                monkeypatch,
            )
            occupied(world["pairs"], **held)
            next_now = next_event + 1.5
            world["recovery"] = scope_test._counter_recovery(world, next_now)
            return_mark = scope_test._market(
                world,
                tmp_path / "g17",
                next_closes,
                next_event,
                next_now,
                "return-switch",
                monkeypatch,
                target=lane,
                mark=next_closes[-1] * 1.02,
            )
            following = occupied(world["pairs"], occupied_scope_mark_lane_id=lane, **return_mark)[
                lane
            ]
            next_plan = following.governed_cycle_result.position_management_reversal
            assert next_plan is not None, following.governed_cycle_result.first_genuine_blocker
            assert (
                next_plan.episode == next_identity and next_plan.selection_id == plan.selection_id
            )
            assert (
                next_plan.current_contracts == plan.target_contracts
                and next_plan.target_contracts > 0
            )
            assert next_plan.slot_capital_basis_usdc == slot_basis.net_basis_usdc > 25
            assert next_plan.portfolio_slot_capital_usdc == 100 + slot_basis.net_basis_usdc > 125
            next_ledger = json.loads(
                (Path(following.evidence_root) / scope_test.LEDGER_FILENAME).read_bytes()
            )
            next_fill = fixture.build_simulated_fill_v1(
                fill_id="direct-reversal:" + next_plan.digest_v1(),
                instrument_id=bound.venue_native_id,
                side="BUY",
                quantity=str(abs(next_plan.signed_order_contracts)),
                mark_price=str(next_plan.reference_mark),
                contract=accounting.contract,
                event_time_unix=next_now + 0.25,
            )
            closing_native = (
                accounting.realized_pnl + accounting.funding_pnl - accounting.cumulative_fees
            )
            opposite = next_plan.apply_simulated_fill_v1(
                ledger=next_ledger,
                accounting=accounting,
                fill=next_fill,
                budget_owner=host.owner,
            )
            assert opposite.action_code == "REVERSE_TO_LONG"
            assert fixture.signed_accounting_quantity(accounting) == next_plan.target_contracts
            next_native = (
                accounting.realized_pnl + accounting.funding_pnl - accounting.cumulative_fees
            )
            net_change = (next_native - closing_native) * next_plan.quote_to_usdc
            assert (
                host.owner.slot_capital_basis_v1(lane).net_basis_usdc
                == slot_basis.net_basis_usdc + net_change
            )
            slot_basis = host.owner.slot_capital_basis_v1(lane)
        owner_class = type(host.owner)
        host.owner.close()
        cold_owner = owner_class(
            durable_root=host.root / "owner",
            durable_mode="recover",
            durable_account_identity="acct-1",
            durable_lane_bindings=world["bounds"],
        )
        try:
            assert cold_owner.slot_capital_basis_v1(lane) == slot_basis
            recovered_accounting = type(accounting).from_durable_dict(before)
            recovered_fill = plan.apply_simulated_fill_v1(
                ledger=ledger, accounting=recovered_accounting, fill=fill, budget_owner=cold_owner
            )
            assert recovered_fill.idempotent_replay
            assert recovered_fill.accounting_output_digest == booked.accounting_output_digest
            assert fixture.signed_accounting_quantity(recovered_accounting) == plan.target_contracts
            assert cold_owner.slot_capital_basis_v1(lane) == slot_basis
        finally:
            cold_owner.close()
    finally:
        host.owner.close()
        world["writer"].release()
