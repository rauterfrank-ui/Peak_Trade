from contextlib import closing
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import orchestrator_v1
from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_enter_live_29p_join_v1 as join,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
    capital_context_facts_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.slot_loss_budget_v1 import (
    SlotCapitalAllocationV1,
)
from src.ops.single_selected_future_policy_v1.persistence_v1 import load_and_validate_selection_v1
from tests.ops import test_bounded_slot_connected_roundtrip_v1 as fixture
from tests.ops import test_bounded_slot_scope_close_v1 as scope
from tests.ops import test_test_phase_slot_loss_budget_v1 as loss
from tests.ops.test_current_productive_rotation_close_v1 import RotationDriver
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)


@pytest.mark.parametrize("funding", [Decimal("2"), Decimal("-2")], ids=["surplus", "shortfall"])
def test_direct_reversal_then_rotation_preserves_slot_and_sizes_new_instrument(
    tmp_path, monkeypatch, synthetic_ports_and_isolation, funding
):
    lane = "LANE_1"
    policy = fixture.policy
    closed_worlds = loss._install_test_path(monkeypatch, exhausted=False)
    monkeypatch.setattr(fixture, "policy", policy)
    original_open = fixture.connected_open_positions
    original_size = join.admit_sized_slot_reservation_v1
    original_apply = fixture.ProductiveFuturesAccountingSessionV1.apply_fill
    original_bind = orchestrator_v1.bind_occupied_lane_cap24_n1_instruments_v1
    host_type = fixture.PortfolioBudgetHostV1
    opened = {}
    sized = []

    def funded_host(**kwargs):
        if kwargs["durable_mode"] == "create":
            kwargs["slot_capital_allocation"] = SlotCapitalAllocationV1(
                "acct-1",
                "offline-direct-reversal-rotation",
                tuple((f"LANE_{index}", Decimal(25)) for index in range(1, 6)),
            )
        return host_type(**kwargs)

    def open_and_reverse(*args, **kwargs):
        world = original_open(*args, **kwargs)
        bound = world["bounds"][lane]
        event = world["event"] + 60
        closes = (*world["closes"], world["closes"][-1] + 0.1)
        caller = scope.occupied.invoke_occupied_lane_governed_cycle_n1_consumer_v1
        observed_at = event + 1.25
        account = world["sessions"][lane]
        opened.update(bound=bound, reservation_id=world["holds"][lane])

        with monkeypatch.context() as patch:

            def observe(label, stamp, mark=None):
                world["recovery"] = scope._counter_recovery(world, stamp)
                inputs = scope._market(
                    world,
                    tmp_path / "g17",
                    closes,
                    event,
                    stamp,
                    label,
                    patch,
                    target=lane if mark is not None else None,
                    mark=mark,
                )
                options = {"occupied_scope_mark_lane_id": lane} if mark is not None else {}
                return caller(world["pairs"], **inputs, **options)[lane]

            baseline = observe("held-before-reversal", observed_at)
            assert baseline.governed_cycle_result.position_management_reversal is None
            root = Path(world["pairs"][lane][0].lane_state_root)
            manifest = root / "MANIFEST.sha256"
            legacy_manifest = manifest.read_bytes()
            favorable = observe("favorable", observed_at + 0.25, closes[-1] * 1.03)
            assert favorable.governed_cycle_result.master_v2_decision == "hold"
            assert load_and_validate_selection_v1(root).ok
            manifest.write_bytes(legacy_manifest)
            assert load_and_validate_selection_v1(root).ok
            snapshot = root / "naked_layered_core_episode_v1.json"
            valid_snapshot = snapshot.read_bytes()
            damaged = json.loads(valid_snapshot)
            damaged["mark"]["seal_id"] = "corrupt"
            snapshot.write_text(json.dumps(damaged))
            assert not load_and_validate_selection_v1(root).ok
            snapshot.write_bytes(valid_snapshot)
            switched = observe("reversal", observed_at + 0.5, closes[-1] * 1.02)

        result = switched.governed_cycle_result
        plan = result.position_management_reversal
        assert plan is not None, result.first_genuine_blocker
        assert plan.episode == world["episodes"][lane].identity
        assert result.final_order_envelope is None and result.post_count == 0
        ledger = json.loads((Path(switched.evidence_root) / scope.LEDGER_FILENAME).read_bytes())
        fill = fixture.build_simulated_fill_v1(
            fill_id="direct-reversal:" + plan.digest_v1(),
            instrument_id=bound.venue_native_id,
            side="SELL",
            quantity=str(abs(plan.signed_order_contracts)),
            mark_price=str(plan.reference_mark),
            contract=account.contract,
            event_time_unix=observed_at + 0.75,
        )
        owner = world["host"].owner
        booking = plan.apply_simulated_fill_v1(
            ledger=ledger,
            accounting=account,
            fill=fill,
            budget_owner=owner,
        )
        assert booking.action_code == "REVERSE_TO_SHORT"
        identity = fixture.bind_simulated_accounting_episode_identity_v1(
            identity=replace(plan.episode, position_side="short"),
            opening_fill=fill,
        )
        world["fills"][lane].append(fill)
        world["episodes"][lane] = fixture.create_position_episode_from_simulated_accounting_v1(
            **fixture._args(tmp_path / "reversed-position", identity),
            session=account,
            fills=world["fills"][lane],
        )
        opened["basis"] = owner.slot_capital_basis_v1(lane)
        opened["episode"] = identity
        assert opened["basis"].net_basis_usdc > 25
        return world

    def apply_fill(session, fill):
        bound = opened.get("bound")
        funding_event_id = "settled-funding-before-rotation"
        if (
            bound is not None
            and session.contract.symbol == bound.venue_native_id
            and fill.fill_id.startswith("original-close:")
            and funding_event_id not in session.funding_events
        ):
            session.apply_funding_observation_v1(
                event_id=funding_event_id,
                amount=str(funding),
                currency=session.contract.quote_currency,
                instrument_id=session.contract.symbol,
                event_time_unix=fill.event_time_unix - 0.001,
            )
        return original_apply(session, fill)

    def trace_sizing(owner, **kwargs):
        if (
            closed_worlds
            and str(kwargs["slot_id"]) == lane
            and kwargs["instrument_id"]
            == fixture.sources._cid(closed_worlds[-1]["chain"]["ranking"], "NEAR-USDT-SWAP")
        ):
            basis = owner.slot_capital_basis_v1(lane)
            facts = capital_context_facts_v1(owner, slot_id=lane)
            sizing = kwargs["sizing_input"]
            result = original_size(owner, **kwargs)
            sized.append((basis, facts, sizing, result))
            return result
        return original_size(owner, **kwargs)

    def bind_after_close(**kwargs):
        replacement = kwargs["selections"].get(lane)
        if replacement is not None and replacement.venue_native_id == "NEAR-USDT-SWAP":
            host = closed_worlds[-1]["host"]
            assert host.bindings[lane] == opened["bound"]
            state = host.owner.risk_snapshot_v1()["state"]
            (booking,) = state["test_slot_economics"][lane]["records"]
            assert booking["episode_id"] == opened["episode"].episode_id
            assert booking["reservation_id"] == opened["reservation_id"]
        return original_bind(**kwargs)

    monkeypatch.setattr(fixture, "PortfolioBudgetHostV1", funded_host)
    monkeypatch.setattr(fixture, "connected_open_positions", open_and_reverse)
    monkeypatch.setattr(fixture.ProductiveFuturesAccountingSessionV1, "apply_fill", apply_fill)
    monkeypatch.setattr(
        orchestrator_v1, "bind_occupied_lane_cap24_n1_instruments_v1", bind_after_close
    )
    monkeypatch.setattr(join, "admit_sized_slot_reservation_v1", trace_sizing)
    driver = RotationDriver(tmp_path, lane)
    fixture.roundtrip(tmp_path, monkeypatch, 5, lane, True, rotation_driver=driver)

    assert len(sized) == 1
    basis, facts, sizing, result = sized[0]
    assert (basis.net_basis_usdc > 25) == (funding > 0)
    start_capital = min(Decimal(25), basis.net_basis_usdc)
    assert sizing.scope_capital_limit == facts["slot_remaining_notional"] == start_capital
    assert facts["aggregate_notional_ceiling"] == basis.net_basis_usdc + 100
    assert sizing.total_capital_limit == facts["aggregate_notional_ceiling"]
    assert 0 < result.reservation.amount <= start_capital

    world = closed_worlds[0]
    host = world["host"]
    assert host.bindings[lane].venue_native_id == "NEAR-USDT-SWAP"
    assert (
        host.bindings[lane].selection_integrity_digest != opened["bound"].selection_integrity_digest
    )
    assert all(
        host.bindings[other] == bound for other, bound in world["bounds"].items() if other != lane
    )
    assert driver.initial_record["active"]["nomination"]["observation_seconds"] == 1800
    with closing(
        PortfolioCapitalReservationBudgetOwnerV1(
            durable_root=host.root / "owner",
            durable_account_identity="acct-1",
            durable_mode="recover",
            durable_lane_bindings=host.bindings,
            entry_budget_policy=policy(),
        )
    ) as cold:
        assert cold.slot_capital_basis_v1(lane) == basis
        assert cold.funded_slot_entry_limits_v1(lane) == (
            start_capital,
            Decimal(100) + basis.net_basis_usdc,
        )
        assert (
            cold.direct_reversal_basis_v1(
                lane, str(result.reservation.reservation_id), fixture.utc(fixture.T0 + 1000)
            )
            == start_capital
        )
        state = cold.risk_snapshot_v1()["state"]
        (close,) = state["test_slot_economics"][lane]["records"]
        (reversal,) = state["simulated_direct_reversal_bookings"][lane]
        assert close["episode_id"] == opened["episode"].episode_id
        assert close["reservation_id"] == opened["reservation_id"]
        assert close["previous_direct_reversal_digest"] == reversal["digest"]
        assert basis.booked_net_usdc == opened["basis"].booked_net_usdc + Decimal(
            close["net_result_usdc"]
        )
        assert all(
            cold.slot_capital_basis_v1(other).net_basis_usdc == 25
            for other in host.bindings
            if other != lane
        )
