"""Original natural SHORT entry and accounting reach the same durable loss request."""

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1 as Owner,
)
from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import (
    ReservationSizingBindingV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (
    build_simulated_fill_v1,
)
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    PositionEpisodeIdentityV1,
    PositionEpisodeScopeV1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    bind_simulated_accounting_episode_identity_v1,
    create_position_episode_from_simulated_accounting_v1,
)
from tests.ops.test_closing_execution_cost_provision_v1 import install_policy
from tests.ops.test_next_funding_cost_provision_v1 import attach_funding_probe
from tests.ops._opening_execution_cost_fixture_v1 import install_cost_probe
from tests.ops.test_open_slot_loss_protection_v1 import policy, observation
from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1
from tests.ops.test_productive_futures_accounting_runtime_binding_v1 import _contract
from tests.ops.test_simulated_accounting_entry_source_v1 import _args
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)


def _run_original_short_loss_probe(tmp_path, monkeypatch, *, remaining=Decimal(0)):
    install_policy(monkeypatch, policy())
    attach_funding_probe(monkeypatch, funding_seconds=7200)
    install_cost_probe(monkeypatch)
    bind = Owner.bind_execution_plan_v1
    checked = []
    from tests.ops import _current_productive_natural_mv2_dp_enter_fixture_v1 as seed

    # The original supervisor's financial port uses current UTC acquisition.
    # Give the synthetic SHORT market its own recent event timeline, then
    # advance it explicitly beyond the later financial assessment and fill.
    seed_time = int(datetime.now(timezone.utc).timestamp() // 60) * 60 - 120
    monkeypatch.setattr(
        seed, "governed_productive_c1_event_ts_unix_v1", lambda **kwargs: float(seed_time)
    )
    prepared = []
    prepare = seed.prepare_layered_short_armed_seed_for_pre_external_invoke_v1

    def capture_seed(**kwargs):
        output = prepare(**kwargs)
        prepared.append(output)
        return output

    monkeypatch.setattr(
        seed, "prepare_layered_short_armed_seed_for_pre_external_invoke_v1", capture_seed
    )

    def observe(owner, rid, order, **kwargs):
        result = bind(owner, rid, order, **kwargs)
        assert order.side == "sell"
        raw = owner.risk_snapshot_v1()["state"]
        sizing = ReservationSizingBindingV1.from_dict_v1(raw["sizing_bindings"][rid])
        bound = BoundInstrumentV1(
            **next(r["binding"]["bound"] for r in raw["reservations"] if r["reservation_id"] == rid)
        )
        mark = sizing.monetary_source.native_reference_price
        epoch = datetime.fromisoformat(
            sizing.monetary_source.decision_epoch.replace("Z", "+00:00")
        ).timestamp()
        session = ProductiveFuturesAccountingSessionV1(
            contract=_contract(order.instrument_id, contract_size="0.01", min_qty="1")
        )
        fill = build_simulated_fill_v1(
            fill_id="original-plan:" + order.envelope_digest,
            instrument_id=order.instrument_id,
            side="SELL",
            quantity=order.quantity,
            mark_price=mark,
            contract=session.contract,
            event_time_unix=epoch,
        )
        session.apply_fill(fill)
        assert session.position.side.value == "short"
        before = session.portfolio_state().equity - session.initial_equity
        session.apply_funding_observation_v1(
            event_id="explicit-short-loss-settlement",
            amount=str(remaining - Decimal(25) - before),
            currency=session.contract.quote_currency,
            instrument_id=session.contract.symbol,
            event_time_unix=epoch + 0.25,
        )
        identity = bind_simulated_accounting_episode_identity_v1(
            identity=PositionEpisodeIdentityV1(
                "LANE_1",
                bound.instrument_id,
                bound.venue_native_id,
                "pending-opening",
                "short",
                PositionEpisodeScopeV1(owner._account_identity, "INTERNAL_SIMULATED_EXECUTION"),
            ),
            opening_fill=fill,
        )
        episode = create_position_episode_from_simulated_accounting_v1(
            **_args(tmp_path / "short-episode", identity), session=session, fills=(fill,)
        )
        world = dict(
            host=SimpleNamespace(owner=owner),
            holds={"LANE_1": rid},
            episodes={"LANE_1": episode},
            kwargs=dict(mark_px=mark),
        )
        value = observation(world, "LANE_1", epoch + 1)
        held = owner.budget_state_v1()
        request = owner.observe_open_slot_loss_v1(
            slot_id="LANE_1",
            episode=episode,
            observation=value,
            mark_px=mark,
            observed_unix=epoch + 1,
        )
        assert request.validate_v1(episode=episode, bound=bound, observed_unix=epoch + 1)
        state = owner.test_slot_loss_state_v1("LANE_1")
        proof = state["open_position_protection"]["latest"]
        assert state["exhausted"] is (remaining <= 0)
        assert proof["identity"]["position_side"] == "short"
        assert Decimal(proof["quantity"]) == session.position.qty == Decimal(order.quantity)
        assert owner.budget_state_v1() == held
        from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
            restore_occupied_lane_mv2_dp_decision_state_cursor_v1,
        )
        from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
            provenance_for_bound_v1,
        )
        from tests.ops.test_bounded_slot_connected_roundtrip_v1 import _lane_pair_v1
        from src.trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide

        _, closes, _, event, _ = prepared[-1]
        event += 180
        closes = tuple(closes) + (float(mark),) * 3
        g17 = seed.governed_c1_aligned_g17_dk_producer_v1(
            bound=bound,
            anchor_event_ts_unix=event,
            evidence_store_root=tmp_path / "short-loss-g17",
            mark_closes=closes,
        )
        pair = _lane_pair_v1(lane_state_root=Path(kwargs["core_cursor_root"]).parent, bound=bound)
        invocation = restore_occupied_lane_mv2_dp_decision_state_cursor_v1(
            {"LANE_1": pair},
            cycle_id_prefix="explicit-short-slot-loss",
            observed_unix=event + 1,
            mark_px=float(mark),
            index_px=float(mark) * 0.995,
            bid_px=float(mark) - 0.5,
            ask_px=float(mark) + 0.5,
            volume=10,
            open_interest=20,
            funding_rate=0.0001,
            finalized_closes=closes,
            last_finalized_event_ts_unix=event,
            venue_flat=False,
            existing_position_side=ExistingPositionSide.SHORT,
            g17_typed_vol_producers={"LANE_1": g17},
            canonical_price_provenance=provenance_for_bound_v1(
                bound=bound, mark_px=float(mark), index_px=float(mark) * 0.995
            ),
            position_episode_bindings={"LANE_1": episode},
            position_episode_scope=identity.account_scope,
            rotation_exit_requests={},
            slot_loss_exit_requests={"LANE_1": request},
        )["LANE_1"]
        assert invocation.cycle_result.replay is not None, invocation.cycle_result.fail_reasons
        assert (
            invocation.cycle_result.replay.intermediate.entry_exit_decision.exit_class.value
            == "safety_exit"
        )
        assert owner.budget_state_v1() == held
        checked.append(proof)
        return result

    errors = []

    def report_error(*args, **kwargs):
        try:
            return observe(*args, **kwargs)
        except BaseException as exc:
            errors.append(exc)
            raise

    monkeypatch.setattr(Owner, "bind_execution_plan_v1", report_error)
    run = _run_layered_entry_supervisor_v1(tmp_path, short=True)
    if errors:
        raise errors[0]
    assert checked and run.policy_result.orchestrator_result.post_count == 0
    return checked


def test_original_short_entry_quantity_and_accounting_reach_the_slot_loss_close_request(
    tmp_path, monkeypatch
):
    _run_original_short_loss_probe(tmp_path, monkeypatch)
