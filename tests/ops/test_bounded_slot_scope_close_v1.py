"""Connect the native intrabar switch to the original close owners offline."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from datetime import datetime
from decimal import Decimal
import json
import signal
import subprocess
from pathlib import Path

import pytest

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    invoke_join_v1 as occupied,
)
from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
    orchestrator_v1 as host_orchestrator,
)
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    open_position_episode_binding_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    CYCLE_EXCLUSION_LOCK_NAME,
    LEDGER_FILENAME,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    CurrentProductiveDoublePlay29PInputV1,
    CurrentProductiveEnterLive29PPortfolioSlotContextV1,
    DoublePlay29PTestStopV1,
    STATUS_DOUBLE_PLAY_ASSESSED,
    STATUS_DOUBLE_PLAY_RESERVED,
    join_current_productive_enter_live_29p_before_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_close_feedback_v1 import (
    PostCloseFeedbackRequestV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    bind_current_productive_double_play_execution_plan_v1,
    try_prepare_current_productive_double_play_venue_plan_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.constants_v1 import (
    USDT_USDC_SOURCE_IDENTITY,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalBudgetError,
    PortfolioCapitalReservationBudgetOwnerV1,
    ReservationStateV1,
    ReserveDispositionV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import (
    ReservationSizingBindingV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.slot_loss_budget_v1 import (
    SlotCapitalAllocationV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.slot_economic_source_v1 import (
    SlotCloseAccountingSourceV1,
)
from tests.ops import test_bounded_slot_connected_roundtrip_v1 as fixture
from tests.ops import test_durable_portfolio_budget_recovery_v1 as durable_fixture
from tests.ops import test_test_phase_slot_loss_budget_v1 as loss_fixture
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    _compose_layered_lane_cycle_v1,
    prepare_layered_long_armed_seed_for_pre_external_invoke_v1,
    prepare_layered_short_armed_seed_for_pre_external_invoke_v1,
)
from tests.ops.test_current_scope_mark_clock_v1 import provenance
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
    read_occupied_scope_mark_snapshot_v1,
    restore_episode_from_store_v1,
)


def _market(world, root, closes, event, now, prefix, monkeypatch, *, target=None, mark=None):
    bounds, host, sessions = world["bounds"], world["host"], world["sessions"]

    class OfflineClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls.fromtimestamp(now, tz)

    monkeypatch.setattr(occupied, "datetime", OfflineClock)
    observed = fixture.portfolio_from_accounting(bounds, sessions, now)
    fixture.persist_applied_inventory(host.root / "reconciliation", observed, sessions)
    inputs = fixture.market(bounds, closes, event, prefix, root)
    inputs.update(
        observed_unix=now,
        portfolio_budget_owner=host.owner,
        host_budget_recovery=world["recovery"],
        observed_portfolio=observed,
        position_episode_bindings=world["episodes"],
        position_episode_scope=world["scope"],
        occupancy_payloads=fixture._positions_payload(
            *(
                (b.venue_native_id, "net", fixture.signed_accounting_quantity(sessions[lane]))
                for lane, b in bounds.items()
            )
        ),
    )
    for lane, bound in bounds.items():
        price = mark if lane == target else closes[-1]
        inputs["canonical_price_provenance_by_lane"][lane] = provenance(
            native=bound.venue_native_id,
            mark=price,
            index=price * 0.995,
            event=now - 0.125,
            captured=now,
        )
    return inputs


def _apply_simulated_close(world, lane, execution, mark, now, root, *, foreign_close=False):
    bound = world["bounds"][lane]
    host = world["host"]
    session = world["sessions"][lane]
    order = execution.envelope
    binding = replace(
        fixture._binding(),
        account_scope=world["scope"].account_identity,
        environment=world["scope"].execution_environment,
        execution_mode="INTERNAL_SIMULATED_EXECUTION",
        instrument_id=order.instrument_id,
        native_id=order.instrument_id,
        selected_direction="EXIT",
        order_side=order.side,
        final_quantity=order.quantity,
        order_type="market",
        order_price="",
        clordid=order.client_order_id,
        canonical_decision_id=execution.source.canonical_intent.decision_id,
        envelope_digest=order.envelope_digest,
    )
    ack = fixture.join_full_core_post_result_to_lifecycle_v1(
        result=fixture._ack_fixture(order), sent_clordid=order.client_order_id, submit_count=1
    )
    order_time, flat_time, balance_time = now + 0.25, now + 0.5, now + 0.75
    lifecycle_args = dict(
        post_submit_join=ack,
        binding=binding,
        decision_outcome="EXIT",
        venue_plan_identity=order.client_order_id,
        envelope_identity=order.envelope_digest,
        submit_attempt_id="intrabar-scope-close",
        local_durable_state_version="v1",
        offline_fixture=fixture.OfflineExchangeFixtureV1(
            pending_orders={"code": "0", "data": []},
            order_history={
                "code": "0",
                "data": [
                    dict(
                        instId=order.instrument_id,
                        clOrdId=order.client_order_id,
                        ordId=ack.venue_order_id,
                        state="filled",
                        sz=order.quantity,
                        accFillSz=order.quantity,
                        uTime=str(int(order_time * 1000)),
                        sCode="0",
                    )
                ],
            },
            positions={
                "code": "0",
                "data": [
                    dict(
                        instId=order.instrument_id,
                        pos="0",
                        posSide="net",
                        uTime=str(int(flat_time * 1000)),
                    )
                ],
            },
        ),
    )
    fill = fixture.build_simulated_fill_v1(
        fill_id="original-close:" + ("different-close" if foreign_close else order.envelope_digest),
        instrument_id=order.instrument_id,
        side=order.side.upper(),
        quantity=order.quantity,
        mark_price=str(mark),
        contract=session.contract,
        event_time_unix=order_time,
        reduce_only=True,
    )
    funding = "2" if order.side == "sell" else "-2"
    session.apply_funding_observation_v1(
        event_id="intrabar-funding:" + order.envelope_digest,
        amount=funding,
        currency=session.contract.quote_currency,
        instrument_id=order.instrument_id,
        event_time_unix=order_time - 0.001,
    )
    session.apply_fill(fill)
    world["fills"][lane].append(fill)
    fixture.seal_simulated_accounting_episode_flat_v1(
        episode=world["episodes"][lane],
        accounting_session=session,
        fills=tuple(world["fills"][lane]),
        bound=bound,
        occupancy_payloads=fixture._positions_payload((bound.venue_native_id, "net", Decimal(0))),
        observed_portfolio=fixture.PortfolioTruthSnapshotV1(
            positions=(
                fixture.PositionTruthV1.from_signed(
                    instrument_id=bound.instrument_id, signed_quantity=Decimal(0)
                ),
            ),
            event_time_unix=flat_time,
            wall_time_unix=flat_time,
            max_age_seconds=5,
        ),
        observed_unix=flat_time,
        source_archive_root=root / lane,
        cursor_store_root=Path(world["pairs"][lane][0].lane_state_root),
        expected_scope=world["scope"],
        writer_session_id="intrabar-simulated-close",
    )
    assert fixture.signed_accounting_quantity(session) == Decimal(0)
    host.clock = lambda: balance_time
    fresh = fixture.capital(host, bound, balance_time)
    money = host.owner.reservation_monetary_source_v1(world["holds"][lane])
    index_tickers = json.loads(money.index_tickers_json)
    if index_tickers is not None:
        for row in index_tickers["data"]:
            row["ts"] = str(int(balance_time * 1000))
    accounting = SlotCloseAccountingSourceV1.from_episode_v1(
        world["episodes"][lane],
        valuation_epoch=fixture.utc(balance_time),
        index_tickers_payload=index_tickers,
        pair_instruments_payload=json.loads(money.conversion_pair_instruments_json),
        fx_acquired_at_utc=fixture.utc(balance_time),
    )
    request = PostCloseFeedbackRequestV1(
        execution,
        bound,
        fixture.utc(balance_time),
        fresh,
        host.owner,
        (world["holds"][lane],),
        host.owner.budget_state_v1().observation_id,
        slot_accounting_source=accounting,
    )
    return {**lifecycle_args, "post_close_feedback_request": request}


def _prepare_counter_replay(bound, root, target_side):
    # A typed original entry input for testing financial/order owners. It
    # lives in a different store and cannot confirm the occupied slot's C3.
    prepare = {
        "short": prepare_layered_short_armed_seed_for_pre_external_invoke_v1,
        "long": prepare_layered_long_armed_seed_for_pre_external_invoke_v1,
    }[target_side]
    _, closes, mark, event, volatility = prepare(
        bound=bound, g17_typed_vol_producer=None, lane_state_root=root
    )
    prepared = _compose_layered_lane_cycle_v1(
        pair=fixture._lane_pair_v1(lane_state_root=root, bound=bound),
        g17_typed_vol_producer=volatility,
        closes=closes,
        mark_px=mark,
        event_ts_unix=event,
        cycle_id_prefix="counter-fixture",
    )
    assert prepared.decision_outcome == f"enter_{target_side}"
    return prepared.replay


def _counter_recovery(world, now):
    bounds, host, sessions = world["bounds"], world["host"], world["sessions"]
    observed = fixture.portfolio_from_accounting(bounds, sessions, now)
    fixture.persist_applied_inventory(host.root / "reconciliation", observed, sessions)
    host.fetch = fixture._fetch(
        uid="acct-1",
        positions=[
            dict(instId=bounds[slot].venue_native_id, posSide="net", pos=str(qty))
            for slot, session in sessions.items()
            if (qty := fixture.signed_accounting_quantity(session))
        ],
    )
    host.clock = lambda: now
    return host.observe_v1(bounds)


def _exercise_counter_plan(world, lane, continuation, replay, now):
    bound = continuation.bound_instrument
    target_side = continuation.target_side
    order_side = {"long": "buy", "short": "sell"}[target_side]
    assert continuation.switch.episode.lane_id == lane
    assert bound == world["bounds"][lane]
    assert replay.evidence.decision_outcome == f"enter_{target_side}"
    assert replay.evidence.instrument_id == bound.instrument_id
    seal_id = continuation.switch.scope_seal_id
    host = world["host"]
    recovery = _counter_recovery(world, now)
    epoch = fixture.utc(now)
    slot = CurrentProductiveEnterLive29PPortfolioSlotContextV1(
        slot_id=lane, decision_id=replay.evidence.decision_id, cycle_id="counter:" + seal_id
    )
    args = dict(
        replay=replay,
        bound_instrument=bound,
        injected=fixture.ports(bound, epoch, slot.cycle_id, account="acct-1"),
        decision_epoch=epoch,
        portfolio_budget_owner=host.owner,
        portfolio_slot=slot,
        host_budget_recovery=recovery,
    )
    result = join_current_productive_enter_live_29p_before_venue_plan_v1(**args)
    assert result.status == occupied.STATUS_PASS, (result.first_blocker, result.reason_codes)
    status, reasons, plan = occupied.try_bind_current_productive_venue_plan_v1(
        replay=result.replay,
        bound_instrument=bound,
        session_id=slot.cycle_id,
        run_id=slot.cycle_id,
        composed_epoch=epoch,
        execution_mode="INTERNAL_SIMULATED_EXECUTION",
    )
    assert status is occupied.CompositionStatusV1.PASS and plan is not None, reasons
    envelope = occupied.bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref=slot.cycle_id,
        provenance_ref=seal_id,
        creation_epoch=epoch,
    )
    assert envelope.instrument_id == bound.venue_native_id
    assert envelope.side == order_side and not envelope.reduce_only
    assert result.post_count == "0"
    replayed = join_current_productive_enter_live_29p_before_venue_plan_v1(**args)
    assert replayed.status == occupied.STATUS_PASS
    assert replayed.portfolio_reservation_id == result.portfolio_reservation_id
    return envelope


def test_pending_slot_allocation_survives_restart_and_needs_original_funds(tmp_path):
    declaration = SlotCapitalAllocationV1(
        durable_fixture.ACCOUNT, "fixture:explicit-slot-allocation", (("LANE_1", Decimal(40)),)
    )
    original = durable_fixture._owner(
        tmp_path, entry_budget_policy=fixture.policy(), slot_capital_allocation=declaration
    )
    original.close()
    with pytest.raises(PortfolioCapitalBudgetError, match="ALLOCATION_BOOTSTRAP_REQUIRED"):
        durable_fixture._owner(tmp_path, "recover", slot_capital_allocation=declaration)
    owner = durable_fixture._owner(tmp_path, "recover")
    try:

        def recover(value):
            return durable_fixture._auto(
                owner, tmp_path, output=fixture._produce(value=value, epoch=durable_fixture.EPOCH)
            )

        insufficient = recover("39")
        assert insufficient.reason_codes == ("SLOT_CAPITAL_ALLOCATION_EXCEEDS_OBSERVED_FUNDS",)
        assert not owner.budget_state_v1().admitted
        with pytest.raises(PortfolioCapitalBudgetError, match="ALLOCATION_FUNDING_UNPROVEN"):
            owner.slot_capital_basis_v1("LANE_1")
        assert recover("40").disposition.value == "ADMITTED"
        basis = owner.slot_capital_basis_v1("LANE_1")
        assert basis.net_basis_usdc == Decimal(40)
        assert basis.booked_net_usdc == 0
        assert basis.funding_observation_id == owner.budget_state_v1().observation_id

        assert recover("26").disposition.value == "ADMITTED"
        assert owner.budget_state_v1().canonical_available_capital == Decimal(26)
        assert owner.slot_capital_basis_v1("LANE_1") == basis
    finally:
        owner.close()


def test_allocated_slot_also_books_original_non_switch_close(tmp_path, monkeypatch):
    policy_factory = fixture.policy
    worlds = loss_fixture._install_test_path(monkeypatch, exhausted=False)
    monkeypatch.setattr(fixture, "policy", policy_factory)
    host_type = fixture.PortfolioBudgetHostV1

    def allocated_host(**kwargs):
        if kwargs["durable_mode"] == "create":
            kwargs["slot_capital_allocation"] = SlotCapitalAllocationV1(
                "acct-1",
                "fixture:ordinary-close-allocation",
                (("LANE_1", Decimal(40)), ("LANE_2", Decimal(50))),
            )
        return host_type(**kwargs)

    monkeypatch.setattr(fixture, "PortfolioBudgetHostV1", allocated_host)
    fixture.roundtrip(tmp_path, monkeypatch, 2, "LANE_1", False)
    (world,) = worlds
    owner = PortfolioCapitalReservationBudgetOwnerV1(
        durable_root=world["host"].root / "owner",
        durable_account_identity="acct-1",
        durable_mode="recover",
        durable_lane_bindings=world["bounds"],
        entry_budget_policy=policy_factory(),
    )
    try:
        basis = owner.slot_capital_basis_v1("LANE_1")
        (record,) = owner.risk_snapshot_v1()["state"]["test_slot_economics"]["LANE_1"]["records"]
        assert "l10_scope" not in record
        assert basis.latest_booking_digest == record["digest"]
        assert basis.net_basis_usdc == Decimal(40) + Decimal(record["net_result_usdc"])
        assert owner.slot_capital_basis_v1("LANE_2").net_basis_usdc == Decimal(50)
    finally:
        owner.close()


@pytest.mark.parametrize(
    ("lane", "opening_side", "foreign_close", "allocated", "reserve_native", "release_unfilled"),
    [
        pytest.param(
            f"LANE_{number}",
            side,
            False,
            True,
            reserve_native,
            False,
            id=f"{side}-LANE_{number}" + ("-native-reserve" if reserve_native else ""),
        )
        for reserve_native in (False, True)
        for side in ("long", "short")
        for number in range(1, 6)
    ]
    + [
        pytest.param("LANE_1", "short", True, True, False, False, id="sealed-foreign-fill"),
        pytest.param("LANE_1", "long", False, False, False, False, id="legacy-without-allocation"),
        pytest.param("LANE_2", "short", False, True, True, True, id="released-native-plan"),
    ],
)
def test_same_candle_scope_switch_reaches_full_close_and_original_budget(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    lane: str,
    opening_side: str,
    foreign_close: bool,
    allocated: bool,
    reserve_native: bool,
    release_unfilled: bool,
):
    declared = {f"LANE_{i}": Decimal(30 + 5 * i) for i in range(1, 6)}
    low_basis = allocated and lane == "LANE_1" and opening_side == "long"
    if low_basis:
        declared[lane] = Decimal(18)
    if allocated:
        host_type = fixture.PortfolioBudgetHostV1

        def allocated_host(**kwargs):
            return host_type(
                **kwargs,
                slot_capital_allocation=SlotCapitalAllocationV1(
                    "acct-1", "fixture:connected-five-slot-allocation", tuple(declared.items())
                ),
            )

        monkeypatch.setattr(fixture, "PortfolioBudgetHostV1", allocated_host)
    world = fixture.connected_open_positions(tmp_path, monkeypatch, 5, opening_side=opening_side)
    bounds, sessions, host = world["bounds"], world["sessions"], world["host"]
    try:
        initial_bases = {slot: host.owner.slot_capital_basis_v1(slot) for slot in bounds}
        if allocated:
            assert {slot: basis.net_basis_usdc for slot, basis in initial_bases.items()} == declared
        else:
            assert all(basis is None for basis in initial_bases.values())
        direction = 1 if opening_side == "long" else -1
        target_side = "short" if opening_side == "long" else "long"
        if not reserve_native:
            counter_replay = _prepare_counter_replay(
                bounds[lane], tmp_path / "counter-fixture", target_side
            )
        event = world["event"] + 60
        closes = (*world["closes"], world["closes"][-1] + direction * 0.1)
        baseline = _market(
            world, tmp_path / "g17", closes, event, event + 1.25, "occupied", monkeypatch
        )
        established = occupied.invoke_occupied_lane_governed_cycle_n1_consumer_v1(
            world["pairs"], **baseline
        )
        assert all(result.s7_invocation is not None for result in established.values())
        assert all(
            result.position_management_close_intent is None for result in established.values()
        )
        original_holds = {slot: host.owner.active_slot_sum_v1(slot) for slot in bounds}
        other_reservations = [
            record
            for record in host.owner.risk_snapshot_v1()["state"]["reservations"]
            if record["slot_id"] != lane
        ]
        positions = {slot: fixture.signed_accounting_quantity(s) for slot, s in sessions.items()}
        assert all(qty * direction > 0 for qty in positions.values())
        other_cursor_files = [
            Path(pair[0].lane_state_root) / occupied.CURSOR_FILENAME
            for slot, pair in world["pairs"].items()
            if slot != lane
        ]
        other_cursors = {path: path.read_bytes() for path in other_cursor_files}

        def forbidden_selection(*args, **kwargs):
            pytest.fail("Running reversal must not select or bind another instrument")

        for name in (
            "publish_checked_lane_selections_v1",
            "bind_occupied_lane_cap24_n1_instruments_v1",
        ):
            monkeypatch.setattr(host_orchestrator, name, forbidden_selection)

        now = event + 1.5
        mark = closes[-1] * (1 - direction * 0.02)
        intrabar = _market(
            world,
            tmp_path / "g17",
            closes,
            event,
            now,
            "scope",
            monkeypatch,
            target=lane,
            mark=mark,
        )
        assert intrabar["candles_payload_by_lane"] == baseline["candles_payload_by_lane"]
        root = Path(world["pairs"][lane][0].lane_state_root)
        before_scope = restore_episode_from_store_v1(
            root, expected_instrument_id=bounds[lane].instrument_id
        )
        cursor_file = root / occupied.CURSOR_FILENAME
        cursor_before_switch = cursor_file.read_bytes()
        before_c3 = occupied.load_current_productive_sidestate_confirmation_cursor_v1(root)[
            "cap61_confirmation_state"
        ]

        result = occupied.invoke_occupied_lane_governed_cycle_n1_consumer_v1(
            world["pairs"], occupied_scope_mark_lane_id=lane, **intrabar
        )
        assert set(result) == {lane}
        target = result[lane]
        dispatched = target.governed_cycle_result
        snapshot = read_occupied_scope_mark_snapshot_v1(root)
        assert snapshot is not None, dispatched.first_genuine_blocker
        regimes = ("bull", "bear") if opening_side == "long" else ("bear", "bull")
        assert (before_scope.regime.value, snapshot["snapshot"]["regime"]) == regimes
        assert snapshot["mark"]["previous_snapshot_id"] == before_scope.snapshot_id
        assert (
            snapshot["mark"]["position_episode_id"] == world["episodes"][lane].identity.episode_id
        )
        assert snapshot["mark"]["prices"] == [mark]
        after_c3 = occupied.load_current_productive_sidestate_confirmation_cursor_v1(root)[
            "cap61_confirmation_state"
        ]
        assert after_c3 == before_c3
        assert not dispatched.eg_consumed
        assert dispatched.master_v2_decision == "exit", dispatched.first_genuine_blocker
        policy = target.s7_invocation.cycle_result.replay.intermediate.entry_exit_decision
        assert policy.exit_class.value == "strategy_invalidation_exit"
        assert "l10_scope_switch_exit:" + snapshot["mark"]["seal_id"] in policy.reason_codes
        execution = dispatched.position_management_execution_handoff
        assert execution is not None, dispatched.first_genuine_blocker
        order = execution.envelope
        assert order.instrument_id == bounds[lane].venue_native_id
        assert order.side == ("sell" if opening_side == "long" else "buy") and order.reduce_only
        assert Decimal(order.quantity) == abs(positions[lane])
        assert dispatched.post_count == 0 and not dispatched.permit_created

        retry = occupied.invoke_occupied_lane_governed_cycle_n1_consumer_v1(
            world["pairs"],
            occupied_scope_mark_lane_id=lane,
            **{**intrabar, "cycle_id_prefix": "scope-repeated"},
        )[lane].governed_cycle_result
        assert retry.first_genuine_blocker == "OCCUPIED_SCOPE_MARK_DUPLICATE"
        assert retry.position_management_execution_handoff is None
        assert read_occupied_scope_mark_snapshot_v1(root) == snapshot

        prior_episode = world["episodes"][lane]
        reopened = open_position_episode_binding_v1(
            identity=prior_episode.identity,
            state_root=Path(prior_episode.binding.state_root),
            mode="recover",
            repository_sha=prior_episode.binding.repository_sha,
            config_digest=prior_episode.binding.config_digest,
            writer_session_id="reopened-close",
        )
        recovery_inputs = dict(
            lane_id=lane,
            lane_pair=world["pairs"][lane],
            episode=reopened,
            expected_scope=world["scope"],
        )
        recover = occupied.recover_occupied_scope_close_for_reconciliation_v1
        if opening_side == "long" and lane == "LANE_1":
            ledger_path = Path(target.evidence_root) / LEDGER_FILENAME
            ledger_text = ledger_path.read_text()
            lock_path = Path(target.lock_root) / CYCLE_EXCLUSION_LOCK_NAME
            child = subprocess.run(
                [
                    "./scripts/pt",
                    "-B",
                    "-c",
                    """
from pathlib import Path
import os, signal, sys
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import occupied_scope_mark_cycle_lock_v1

lock = occupied_scope_mark_cycle_lock_v1(
    lock_root=Path(sys.argv[1]), evidence_root=Path(sys.argv[2]), native_id=sys.argv[3],
)
lock.acquire()
os.kill(os.getpid(), signal.SIGKILL)
""",
                    target.lock_root,
                    target.evidence_root,
                    target.native_id,
                ],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True,
                check=False,
            )
            assert child.returncode == -signal.SIGKILL, child.stderr.decode()
            dead_receipt = lock_path.read_bytes()
            try:
                incomplete = json.loads(ledger_text)
                incomplete["state"] = "IN_PROGRESS"
                ledger_path.write_text(json.dumps(incomplete))
                with pytest.raises(ValueError, match="OCCUPIED_SCOPE_CLOSE_LEDGER_NOT_COMPLETE"):
                    recover(**recovery_inputs)
                tampered = json.loads(ledger_text)
                tampered["occupied_scope_close"]["envelope"]["client_order_id"] = "foreign-order"
                ledger_path.write_text(json.dumps(tampered))
                with pytest.raises(ValueError, match="RETAINED_CLOSE_READBACK_INVALID"):
                    recover(**recovery_inputs)
                wrong_account = replace(world["scope"], account_identity="different-account")
                with pytest.raises(ValueError, match="OCCUPIED_SCOPE_CLOSE_ACCOUNT_SCOPE_MISMATCH"):
                    recover(**{**recovery_inputs, "expected_scope": wrong_account})
                assert lock_path.read_bytes() == dead_receipt
            finally:
                ledger_path.write_text(ledger_text)
            recovered = recover(**recovery_inputs)
            assert not lock_path.exists()
            (archived_lock,) = lock_path.parent.glob(lock_path.name + ".dead_process.*")
            assert archived_lock.read_bytes() == dead_receipt
        else:
            recovered = recover(**recovery_inputs)
        assert recovered == execution == recover(**recovery_inputs)
        assert not recovered.source.quantity_handoff.submission_authorized
        switch = recovered.l10_close
        assert switch is not None and switch.target_side == target_side
        assert switch.episode == reopened.identity
        assert switch.scope_digest == snapshot["digest"]
        assert switch.scope_seal_id == snapshot["mark"]["seal_id"]
        assert read_occupied_scope_mark_snapshot_v1(root) == snapshot
        assert host.owner.active_slot_sum_v1(lane) == original_holds[lane]
        closed_source = SlotCloseAccountingSourceV1.from_episode_v1(
            reopened, valuation_epoch=fixture.utc(now + 0.75)
        )
        sealed_recovery_inputs = {
            key: value for key, value in recovery_inputs.items() if key != "episode"
        }
        sealed_recovery_inputs["sealed_accounting_source"] = closed_source
        if lane == "LANE_1":
            with pytest.raises(ValueError, match="SIMULATED_CLOSE_SEAL_REQUIRED"):
                recover(**sealed_recovery_inputs)

        world["episodes"][lane] = reopened
        reconciliation = _apply_simulated_close(
            world, lane, recovered, mark, now, tmp_path / "closed", foreign_close=foreign_close
        )
        if foreign_close:
            with pytest.raises(ValueError, match="OCCUPIED_SCOPE_CLOSE_SEALED_FILL_MISMATCH"):
                recover(**sealed_recovery_inputs)
            assert host.owner.active_slot_sum_v1(lane) == original_holds[lane]
            return
        if lane == "LANE_1":
            with pytest.raises(ValueError, match="OCCUPIED_SCOPE_CLOSE_EPISODE_MISMATCH"):
                recover(**recovery_inputs)
            after_switch_cursor = cursor_file.read_bytes()
            try:
                cursor_file.write_bytes(cursor_before_switch)
                with pytest.raises(ValueError, match="POSITION_EPISODE_CURSOR_RECOVERY_REQUIRED"):
                    recover(**sealed_recovery_inputs)
            finally:
                cursor_file.write_bytes(after_switch_cursor)

        # Reopen the exact Close and switch from the sealed source before the
        # original post-close capital refresh. No open episode handle is used.
        from_flat = recover(**sealed_recovery_inputs)
        assert from_flat == execution == recovered
        assert read_occupied_scope_mark_snapshot_v1(root) == snapshot
        assert host.owner.active_slot_sum_v1(lane) == original_holds[lane]
        if opening_side == "long" and lane == "LANE_1":
            slot, bound = world["pairs"][lane]
            process = subprocess.run(
                [
                    "./scripts/pt",
                    "-B",
                    "-c",
                    """
import json, sys
from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import recover_occupied_scope_close_for_reconciliation_v1
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import IsolatedLaneSlotV1
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import PositionEpisodeScopeV1
from src.ops.portfolio_capital_reservation_budget_v1.slot_economic_source_v1 import SlotCloseAccountingSourceV1
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

inputs = json.load(sys.stdin)
result = recover_occupied_scope_close_for_reconciliation_v1(
    lane_id=inputs["lane_id"],
    lane_pair=(IsolatedLaneSlotV1(**inputs["slot"]), BoundInstrumentV1(**inputs["bound"])),
    expected_scope=PositionEpisodeScopeV1(**inputs["scope"]),
    sealed_accounting_source=SlotCloseAccountingSourceV1.from_dict_v1(inputs["source"]),
)
print(json.dumps({"order": result.envelope.to_runtime_json_v1(), "target": result.l10_close.target_side}))
""",
                ],
                cwd=Path(__file__).resolve().parents[2],
                input=json.dumps(
                    {
                        "lane_id": lane,
                        "slot": asdict(slot),
                        "bound": bound.to_dict(),
                        "scope": asdict(world["scope"]),
                        "source": closed_source.to_dict_v1(),
                    }
                ),
                capture_output=True,
                text=True,
                check=False,
            )
            assert process.returncode == 0, process.stderr
            assert json.loads(process.stdout.splitlines()[-1]) == {
                "order": order.to_runtime_json_v1(),
                "target": target_side,
            }
        reconcile = fixture.run_full_core_post_submit_lifecycle_reconciliation_join_v1
        request = replace(reconciliation["post_close_feedback_request"], execution=from_flat)
        if lane == "LANE_1":
            missing_capital = reconcile(
                **{
                    **reconciliation,
                    "post_close_feedback_request": replace(request, capital_handoff=None),
                }
            ).post_close_feedback
            assert missing_capital.status == "RECONCILED_FLAT_DOUBLE_PLAY_PENDING", (
                missing_capital.reason_codes
            )
            assert missing_capital.double_play_continuation is None
            assert missing_capital.reason_codes == ("POST_CLOSE_FRESH_CAPITAL_HANDOFF_REQUIRED",)
            assert not missing_capital.ranking_review_allowed

            for invalid in (
                replace(recovered, l10_close=None),
                replace(recovered, l10_close=replace(switch, scope_seal_id="foreign-seal")),
            ):
                bad_proof = reconcile(
                    **{
                        **reconciliation,
                        "post_close_feedback_request": replace(request, execution=invalid),
                    }
                ).post_close_feedback
                assert bad_proof.reason_codes == ("POST_CLOSE_SOURCE_INVALID",)
                assert bad_proof.double_play_continuation is None

            wrong_account = reconcile(
                **{
                    **reconciliation,
                    "binding": replace(reconciliation["binding"], account_scope="foreign-account"),
                }
            ).post_close_feedback
            assert wrong_account.reason_codes == ("POST_CLOSE_L10_ACCOUNT_SCOPE_MISMATCH",)
            assert wrong_account.double_play_continuation is None

            wrong_generation = reconcile(
                **{
                    **reconciliation,
                    "post_close_feedback_request": replace(
                        request,
                        bound_instrument=replace(bounds[lane], selection_id="foreign-selection"),
                    ),
                }
            ).post_close_feedback
            assert wrong_generation.reason_codes == ("POST_CLOSE_LANE_GENERATION_MISMATCH",)
            assert wrong_generation.double_play_continuation is None

            offline = reconciliation["offline_fixture"]
            unfilled_order = {**offline.order_history["data"][0], "state": "live", "accFillSz": "0"}
            unfilled_close = reconcile(
                **{
                    **reconciliation,
                    "offline_fixture": replace(
                        offline, order_history={"code": "0", "data": [unfilled_order]}
                    ),
                }
            ).post_close_feedback
            assert unfilled_close.status == "FLAT_NOT_RELEASED", unfilled_close.reason_codes
            assert unfilled_close.double_play_continuation is None

            pending = reconcile(
                **{
                    **reconciliation,
                    "offline_fixture": replace(
                        offline,
                        positions={
                            "code": "0",
                            "data": [{**offline.positions["data"][0], "pos": str(positions[lane])}],
                        },
                    ),
                }
            ).post_close_feedback
            assert pending.status == "POSITION_REMAINS_OPEN"
            assert pending.double_play_continuation is None
            assert host.owner.active_slot_sum_v1(lane) == original_holds[lane]

        expected_refresh = "ADMITTED"
        if lane == "LANE_1":
            missing_booking = reconcile(
                **{
                    **reconciliation,
                    "post_close_feedback_request": replace(request, slot_accounting_source=None),
                }
            ).post_close_feedback
            assert missing_booking.capital_refresh.disposition.value == "ADMITTED"
            assert missing_booking.status == "RECONCILED_FLAT_DOUBLE_PLAY_PENDING"
            assert missing_booking.double_play_continuation is None
            assert any(
                "CLOSE_ACCOUNTING_SOURCE_REQUIRED" in reason
                for reason in missing_booking.reason_codes
            )
            assert "test_slot_economics" not in host.owner.risk_snapshot_v1()["state"]
            if allocated:
                with pytest.raises(PortfolioCapitalBudgetError, match="CLOSE_ECONOMICS_PENDING"):
                    host.owner.slot_capital_basis_v1(lane)

            foreign_source = replace(
                request.slot_accounting_source,
                identity_json=json.dumps(asdict(world["episodes"]["LANE_2"].identity)),
            )
            bad_booking = reconcile(
                **{
                    **reconciliation,
                    "post_close_feedback_request": replace(
                        request, slot_accounting_source=foreign_source
                    ),
                }
            ).post_close_feedback
            assert bad_booking.double_play_continuation is None
            assert any(
                "ACCOUNTING_EPISODE_MISMATCH" in reason for reason in bad_booking.reason_codes
            )
            assert "test_slot_economics" not in host.owner.risk_snapshot_v1()["state"]
            expected_refresh = "IDEMPOTENT_REPLAY"

        # A supplied ranking is immaterial for the admitted L10 close.
        reconciliation["post_close_feedback_request"] = replace(request, ranking=object())
        lifecycle = reconcile(**reconciliation)
        feedback = lifecycle.post_close_feedback
        assert feedback is not None and feedback.capital_refresh is not None, feedback
        assert feedback.capital_refresh.disposition.value == expected_refresh, feedback.reason_codes
        assert feedback.status == "RECONCILED_FLAT_DOUBLE_PLAY_READY", feedback.reason_codes
        assert not feedback.ranking_review_allowed and feedback.membership_review is None
        assert feedback.execution_authority_effect == "NONE"
        continuation = feedback.double_play_continuation
        assert continuation is not None
        assert continuation.target_side == target_side
        assert continuation.switch == switch
        assert continuation.bound_instrument == bounds[lane]
        assert continuation.close_envelope_digest == order.envelope_digest
        assert continuation.close_evidence_digest == feedback.evidence_digest
        booked = host.owner.risk_snapshot_v1()["state"]["test_slot_economics"]
        (record,) = booked[lane]["records"]
        booking = continuation.net_booking
        assert booking.episode_id == switch.episode.episode_id
        assert booking.reservation_id == world["holds"][lane]
        assert booking.booking_digest == record["digest"]
        assert booking.slot_booked_net_usdc == booking.episode_net_usdc
        session = sessions[lane]
        native_net = session.portfolio_state().equity - session.initial_equity
        assert native_net == Decimal(record["native_net_result"])
        if session.contract.quote_currency == "USDT":
            fx = request.slot_accounting_source
            rate = next(
                Decimal(row["idxPx"])
                for row in json.loads(fx.index_tickers_json)["data"]
                if row["instId"] == USDT_USDC_SOURCE_IDENTITY
            )
            expected_net = native_net * (Decimal(1) / rate)
        else:
            expected_net = native_net
        assert booking.episode_net_usdc == expected_net
        assert direction * booking.episode_net_usdc > 0
        basis = continuation.capital_basis
        if allocated:
            assert basis.initial_usdc == declared[lane]
            assert basis.net_basis_usdc == declared[lane] + expected_net
            assert basis.funding_observation_id == initial_bases[lane].funding_observation_id
            assert basis.allocation_digest == initial_bases[lane].allocation_digest
            assert basis.latest_booking_digest == booking.booking_digest
            assert all(
                host.owner.slot_capital_basis_v1(other) == original
                for other, original in initial_bases.items()
                if other != lane
            )
            with pytest.raises(PortfolioCapitalBudgetError, match="LATEST_BOOKING_MISMATCH"):
                host.owner.slot_capital_basis_v1(
                    lane, close_booking=replace(booking, booking_digest="foreign-booking")
                )
        else:
            assert basis is None
        assert not booked[lane]["exhausted"]
        assert all(not booked[other]["records"] for other in bounds if other != lane)
        assert (
            lifecycle.to_dict()["post_close_feedback"]["double_play_continuation"]
            == continuation.to_dict()
        )
        assert host.owner.active_slot_sum_v1(lane) == 0
        assert recover(**sealed_recovery_inputs) == from_flat
        replayed_feedback = reconcile(**reconciliation).post_close_feedback
        assert replayed_feedback.capital_refresh.disposition.value == "IDEMPOTENT_REPLAY"
        assert replayed_feedback.double_play_continuation == continuation
        assert host.owner.risk_snapshot_v1()["state"]["test_slot_economics"] == booked

        counter_now = now + 1
        epoch = fixture.utc(counter_now)
        current_mark = intrabar["canonical_price_provenance_by_lane"][lane]
        stop = DoublePlay29PTestStopV1(
            venue_native_id=bounds[lane].venue_native_id,
            target_side=target_side,
            reference_mark=Decimal(str(mark)),
            stop_price=Decimal(str(mark)) + Decimal(direction),
            source_ref="fixture:independent-sizing-stop",
        )
        double_play = CurrentProductiveDoublePlay29PInputV1(
            continuation=continuation,
            close_request=request,
            lane=world["pairs"][lane][0],
            mark=current_mark,
            test_stop=stop,
        )
        sizing_args = dict(
            replay=None,
            bound_instrument=bounds[lane],
            injected=fixture.ports(
                bounds[lane], epoch, "l10:" + order.envelope_digest, account="acct-1"
            ),
            decision_epoch=epoch,
            portfolio_budget_owner=host.owner,
            host_budget_recovery=_counter_recovery(world, counter_now),
        )
        stored_count = host.owner.stored_reservation_count_v1()
        if allocated:
            sizing_result = join_current_productive_enter_live_29p_before_venue_plan_v1(
                double_play=double_play, **sizing_args
            )
            assert sizing_result.status == STATUS_DOUBLE_PLAY_ASSESSED, sizing_result.reason_codes
            assert not sizing_result.venue_plan_authorized
            assert sizing_result.replay is None and not sizing_result.portfolio_reservation_id
            assert sizing_result.post_count == "0" and sizing_result.permit_created == "false"
            assessment = sizing_result.double_play_sizing
            assert assessment is not None and assessment.capital_basis == continuation.capital_basis
            assert assessment.test_stop == stop
            quantity = assessment.sizing_decision.canonical_position_sizing
            assert assessment.sizing_decision.selected_side == target_side.upper()
            assert assessment.sizing_decision.scope_capital_envelope.per_order_cap == min(
                Decimal(25), basis.net_basis_usdc
            )
            if low_basis:
                assert sizing_result.sizing_outcome == "BLOCKED", sizing_result.reason_codes
                assert "BELOW_MIN_QUANTITY" in sizing_result.reason_codes
                assert assessment.sizing_decision.final_quantity == 0
            else:
                assert sizing_result.sizing_outcome == "PASS", sizing_result.reason_codes
                assert 0 < quantity.resulting_notional <= min(Decimal(25), basis.net_basis_usdc)
            if lane == "LANE_1":
                wrong_stop = replace(
                    double_play, test_stop=replace(stop, stop_price=stop.reference_mark)
                )
                denied = join_current_productive_enter_live_29p_before_venue_plan_v1(
                    double_play=wrong_stop, **sizing_args
                )
                assert denied.first_blocker == "DOUBLE_PLAY_29P_BOUND_TEST_STOP_REQUIRED"
                assert denied.get_count == 0 and denied.double_play_sizing is None
                wrong_mark = provenance(
                    native=bounds[lane].venue_native_id,
                    mark=mark + 0.5,
                    index=mark * 0.995,
                    event=now - 0.125,
                    captured=now,
                )
                denied = join_current_productive_enter_live_29p_before_venue_plan_v1(
                    double_play=replace(double_play, mark=wrong_mark), **sizing_args
                )
                assert denied.first_blocker == "DOUBLE_PLAY_29P_CURRENT_SWITCH_MARK_UNPROVEN"
                forged = replace(
                    double_play,
                    continuation=replace(
                        continuation,
                        capital_basis=replace(basis, initial_usdc=basis.initial_usdc + 1),
                    ),
                )
                denied = join_current_productive_enter_live_29p_before_venue_plan_v1(
                    double_play=forged, **sizing_args
                )
                assert (
                    denied.first_blocker == "DOUBLE_PLAY_29P_POSITIVE_CURRENT_SLOT_BASIS_REQUIRED"
                )
        else:
            denied = join_current_productive_enter_live_29p_before_venue_plan_v1(
                double_play=double_play, **sizing_args
            )
            assert denied.first_blocker == "DOUBLE_PLAY_29P_POSITIVE_CURRENT_SLOT_BASIS_REQUIRED"
            assert denied.double_play_sizing is None
        assert host.owner.stored_reservation_count_v1() == stored_count
        assert host.owner.active_slot_sum_v1(lane) == 0

        if reserve_native and lane == "LANE_5" and opening_side == "short":
            host_args = dict(
                double_play=double_play,
                injected=sizing_args["injected"],
                decision_epoch=epoch,
                recovery=sizing_args["host_budget_recovery"],
            )
            reservation_id, envelope = host.prepare_simulated_double_play_reversal_v1(**host_args)
            assert host.prepare_simulated_double_play_reversal_v1(**host_args) == (
                reservation_id,
                envelope,
            )
            assert Decimal(envelope.quantity) == quantity.rounded_quantity
            fill = fixture.build_simulated_fill_v1(
                fill_id="original-plan:" + envelope.envelope_digest,
                instrument_id=envelope.instrument_id,
                side=envelope.side.upper(),
                quantity=envelope.quantity,
                mark_price=str(mark - direction * 0.1),
                contract=sessions[lane].contract,
                event_time_unix=counter_now,
            )
            next_episode, next_accounting, next_fills = host.open_simulated_double_play_episode_v1(
                reservation_id=reservation_id, fill=fill, **host_args
            )
            assert next_episode.identity.position_side == target_side
            assert fixture.signed_accounting_quantity(next_accounting) == fill.quantity
            assert next_fills == (*world["fills"][lane], fill)
            world["episodes"][lane] = next_episode
            world["holds"][lane] = reservation_id
            world["sessions"][lane] = next_accounting
            world["fills"][lane] = list(next_fills)

            return_now = counter_now + 1
            return_mark = mark * 0.96
            reverse_market = _market(
                world,
                tmp_path / "g17",
                closes,
                event,
                return_now,
                "scope-return",
                monkeypatch,
                target=lane,
                mark=float(return_mark),
            )
            second = occupied.invoke_occupied_lane_governed_cycle_n1_consumer_v1(
                world["pairs"], occupied_scope_mark_lane_id=lane, **reverse_market
            )[lane].governed_cycle_result
            returned = second.position_management_execution_handoff
            assert returned is not None, second.first_genuine_blocker
            assert returned.l10_close.episode == next_episode.identity
            assert returned.l10_close.target_side == opening_side
            assert returned.envelope.side == "sell" and returned.envelope.reduce_only
            assert Decimal(returned.envelope.quantity) == fill.quantity

            next_close_args = _apply_simulated_close(
                world, lane, returned, return_mark, return_now, tmp_path / "closed-return"
            )
            next_request = next_close_args["post_close_feedback_request"]
            next_feedback = reconcile(**next_close_args).post_close_feedback
            next_continuation = next_feedback.double_play_continuation
            assert next_continuation is not None, next_feedback.reason_codes
            assert next_continuation.target_side == opening_side
            assert next_continuation.capital_basis.net_basis_usdc == (
                basis.net_basis_usdc + next_continuation.net_booking.episode_net_usdc
            )
            return_epoch = fixture.utc(return_now + 1)
            return_id = "l10:" + returned.envelope.envelope_digest
            return_reference = Decimal(str(return_mark))
            return_args = dict(
                double_play=CurrentProductiveDoublePlay29PInputV1(
                    continuation=next_continuation,
                    close_request=next_request,
                    lane=world["pairs"][lane][0],
                    mark=reverse_market["canonical_price_provenance_by_lane"][lane],
                    test_stop=DoublePlay29PTestStopV1(
                        venue_native_id=bounds[lane].venue_native_id,
                        target_side=opening_side,
                        reference_mark=return_reference,
                        stop_price=return_reference + 1,
                        source_ref="fixture:independent-sizing-stop",
                    ),
                ),
                injected=fixture.ports(bounds[lane], return_epoch, return_id, account="acct-1"),
                decision_epoch=return_epoch,
                recovery=_counter_recovery(world, return_now + 1),
            )
            return_reservation, return_plan = host.prepare_simulated_double_play_reversal_v1(
                **return_args
            )
            assert (
                return_reservation != reservation_id
                and return_plan.instrument_id == fill.instrument_id
            )
            assert return_plan.side == "sell"
            return_fill = fixture.build_simulated_fill_v1(
                fill_id="original-plan:" + return_plan.envelope_digest,
                instrument_id=return_plan.instrument_id,
                side=return_plan.side.upper(),
                quantity=return_plan.quantity,
                mark_price=str(return_reference - Decimal("0.1")),
                contract=next_accounting.contract,
                event_time_unix=return_now + 1,
            )
            last_episode, last_accounting, last_fills = host.open_simulated_double_play_episode_v1(
                reservation_id=return_reservation, fill=return_fill, **return_args
            )
            assert last_episode.identity.position_side == opening_side
            assert last_episode.identity.episode_id != next_episode.identity.episode_id
            assert fixture.signed_accounting_quantity(last_accounting) == -return_fill.quantity
            assert last_fills == (*world["fills"][lane], return_fill)
            assert host.owner.active_slot_sum_v1(lane) > 0
            assert (
                host.owner.lookup_v1(
                    slot_id=lane,
                    decision_id="l10:" + order.envelope_digest,
                    cycle_id="l10:" + order.envelope_digest,
                    observation_id="",
                ).state
                is ReservationStateV1.RELEASED
            )
            assert all(
                host.owner.active_slot_sum_v1(other) == original_holds[other]
                and fixture.signed_accounting_quantity(sessions[other]) == positions[other]
                for other in bounds
                if other != lane
            )
            assert all(path.read_bytes() == before for path, before in other_cursors.items())
            return

        if reserve_native:
            reserve_request = replace(double_play, reserve=True)
            decision_id = "l10:" + order.envelope_digest
            owner = host.owner
            original_try_reserve = owner.try_reserve_v1
            reserve_calls = []

            def try_reserve_with_competitor(**kwargs):
                reserve_calls.append(kwargs)
                if lane == "LANE_1":
                    unbound = original_try_reserve(**dict(kwargs, double_play_source=None))
                    assert unbound.reason_codes == ("DOUBLE_PLAY_RESERVATION_SOURCE_REQUIRED",)
                    source = kwargs["double_play_source"]
                    wrong_basis = replace(
                        source,
                        continuation=replace(
                            source.continuation,
                            capital_basis=replace(basis, initial_usdc=basis.initial_usdc + 1),
                        ),
                    )
                    forged = original_try_reserve(**dict(kwargs, double_play_source=wrong_basis))
                    assert forged.reason_codes == ("DOUBLE_PLAY_RESERVATION_SLOT_BASIS_CHANGED",)
                    assert not forged.mutated
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        futures = [
                            executor.submit(original_try_reserve, **kwargs) for _ in range(2)
                        ]
                        attempts = [future.result() for future in futures]
                    admitted, blocked = sorted(attempts, key=lambda result: not result.mutated)
                    assert admitted.disposition is ReserveDispositionV1.ADMITTED
                    assert blocked.disposition is ReserveDispositionV1.FAIL_CLOSED
                    assert blocked.reason_codes == (
                        "LOCAL_COMMITMENT_GENERATION_CHANGED_BEFORE_RESERVE",
                    )
                    retried = original_try_reserve(
                        **dict(
                            kwargs,
                            expected_local_commitment_generation=(
                                owner.local_commitment_readback_v1().generation_digest
                            ),
                        )
                    )
                    assert retried.reason_codes == (
                        "BOUNDED_CLOSE_REFRESH_UNPROVEN_OR_SLOT_OCCUPIED",
                    )
                    assert not retried.mutated
                    return admitted
                return original_try_reserve(**kwargs)

            with monkeypatch.context() as patch:
                patch.setattr(owner, "try_reserve_v1", try_reserve_with_competitor)
                native = join_current_productive_enter_live_29p_before_venue_plan_v1(
                    double_play=reserve_request, **sizing_args
                )
            assert not native.venue_plan_authorized and native.replay is None
            assert native.post_count == "0" and native.permit_created == "false"
            assert native.double_play_sizing == assessment
            if low_basis:
                assert native.portfolio_reservation_disposition == "DENIED"
                assert native.first_blocker == sizing_result.first_blocker
                assert not native.portfolio_reservation_id and not reserve_calls
                assert owner.stored_reservation_count_v1() == stored_count
                assert owner.active_slot_sum_v1(lane) == 0
                return

            assert native.status == STATUS_DOUBLE_PLAY_RESERVED, native.reason_codes
            assert native.portfolio_reservation_disposition == "ADMITTED"
            assert len(reserve_calls) == 1
            reservation_id = native.portfolio_reservation_id
            snapshot = owner.risk_snapshot_v1()["state"]
            stored = ReservationSizingBindingV1.from_dict_v1(
                snapshot["sizing_bindings"][reservation_id]
            )
            assert stored.decision == native.double_play_sizing.sizing_decision
            assert stored.applied_input.decision_id == decision_id
            assert stored.applied_input.instrument_id == bounds[lane].instrument_id
            assert stored.applied_input.selected_side == target_side.upper()
            assert owner.active_slot_sum_v1(lane) == quantity.resulting_notional
            assert owner.stored_reservation_count_v1() == stored_count + 1
            assert reservation_id not in owner.execution_links_v1()
            assert snapshot["test_slot_economics"] == booked
            assert [
                record for record in snapshot["reservations"] if record["slot_id"] != lane
            ] == other_reservations
            assert all(path.read_bytes() == before for path, before in other_cursors.items())
            assert fixture.signed_accounting_quantity(sessions[lane]) == 0

            repeat = join_current_productive_enter_live_29p_before_venue_plan_v1(
                double_play=reserve_request, **sizing_args
            )
            assert repeat.first_blocker == "BOUNDED_CLOSE_REFRESH_UNPROVEN_OR_SLOT_OCCUPIED"
            assert not repeat.portfolio_reservation_id
            assert owner.risk_snapshot_v1()["state"] == snapshot

            plan_args = {
                name: sizing_args[name]
                for name in (
                    "bound_instrument",
                    "injected",
                    "decision_epoch",
                    "host_budget_recovery",
                )
            }
            plan_args.update(reservation_id=reservation_id, double_play=reserve_request)
            status, reasons, plan = try_prepare_current_productive_double_play_venue_plan_v1(
                **plan_args
            )
            assert status is occupied.CompositionStatusV1.PASS and plan is not None, reasons
            assert plan.reservation_id == reservation_id
            assert plan.close_envelope_digest == order.envelope_digest
            assert plan.scope_digest == continuation.switch.scope_digest
            intent, wire = plan.canonical_intent, plan.venue_plan
            assert (
                intent.decision_id == decision_id
                and intent.instrument_id == bounds[lane].instrument_id
            )
            assert intent.intent_action == f"ENTER_{target_side.upper()}"
            assert intent.quantity == quantity.rounded_quantity
            assert not intent.submission_authorized and not intent.execution_eligible
            assert wire.environment == "INTERNAL_SIMULATED_EXECUTION"
            assert wire.side == ("buy" if target_side == "long" else "sell")
            assert wire.instrument_id == bounds[lane].venue_native_id
            assert Decimal(wire.quantity) == intent.quantity and not wire.reduce_only
            assert plan.quantity_admission.allowed
            assert owner.risk_snapshot_v1()["state"] == snapshot
            if lane == "LANE_1":
                prepare = try_prepare_current_productive_double_play_venue_plan_v1
                assert prepare(**plan_args) == (status, reasons, plan)
                assert prepare(**dict(plan_args, reservation_id="foreign-hold")) == (
                    occupied.CompositionStatusV1.DENY,
                    ("DOUBLE_PLAY_PLAN_REQUIRES_ORIGINAL_UNBOUND_HOLD",),
                    None,
                )
                altered_stop = replace(stop, stop_price=stop.stop_price + Decimal(direction))
                altered = replace(reserve_request, test_stop=altered_stop)
                assert prepare(**dict(plan_args, double_play=altered)) == (
                    occupied.CompositionStatusV1.DENY,
                    ("DOUBLE_PLAY_PLAN_ORIGINAL_SIZING_SOURCE_CHANGED",),
                    None,
                )
                missing_limits = replace(sizing_args["injected"], venue_quantity_limits=None)
                assert prepare(**dict(plan_args, injected=missing_limits)) == (
                    occupied.CompositionStatusV1.DENY,
                    ("VENUE_QUANTITY_OBSERVATION_MISSING",),
                    None,
                )
                insufficient_limits = fixture.ports(
                    bounds[lane], epoch, decision_id, account="acct-1", denied=True
                )
                denied, reasons, missing = prepare(**dict(plan_args, injected=insufficient_limits))
                assert denied is occupied.CompositionStatusV1.DENY and missing is None
                assert any("MAX" in reason for reason in reasons), reasons
                assert owner.risk_snapshot_v1()["state"] == snapshot

            envelope = bind_current_productive_double_play_execution_plan_v1(**plan_args)
            bound_link = owner.read_bound_double_play_execution_plan_v1(reservation_id)
            assert bound_link["envelope"] == envelope.to_runtime_json_v1()
            assert bound_link["phase"] == "PLAN_BOUND" and bound_link["identity"] is None
            assert bound_link["double_play"]["close_envelope_digest"] == order.envelope_digest
            assert envelope.side == wire.side and envelope.quantity == wire.quantity
            assert owner.active_slot_sum_v1(lane) == quantity.resulting_notional
            assert owner.stored_reservation_count_v1() == stored_count + 1
            if lane == "LANE_1":
                before_rebind = owner.risk_snapshot_v1()
                assert (
                    bind_current_productive_double_play_execution_plan_v1(**plan_args) == envelope
                )
                assert owner.risk_snapshot_v1() == before_rebind
                with pytest.raises(
                    ValueError, match="DOUBLE_PLAY_ORIGINAL_SIMULATED_PLAN_REQUIRED"
                ):
                    owner.bind_execution_plan_v1(reservation_id, envelope)
                with pytest.raises(
                    ValueError, match="DOUBLE_PLAY_SIMULATED_PLAN_HAS_NO_EXTERNAL_SUBMIT_CONTEXT"
                ):
                    owner.execution_plan_context_v1(reservation_id, envelope)
            expected_state = ReservationStateV1.COMMITTED
            if release_unfilled:
                owner.release_plan_failure_v1(reservation_id)
                expected_state = ReservationStateV1.RELEASED
                repeat = join_current_productive_enter_live_29p_before_venue_plan_v1(
                    double_play=reserve_request, **sizing_args
                )
                assert repeat.first_blocker == "DOUBLE_PLAY_RESERVATION_ALREADY_CONSUMED"
                assert not repeat.portfolio_reservation_id
                assert owner.stored_reservation_count_v1() == stored_count + 1
                assert owner.active_slot_sum_v1(lane) == 0
                assert try_prepare_current_productive_double_play_venue_plan_v1(**plan_args) == (
                    occupied.CompositionStatusV1.DENY,
                    ("DOUBLE_PLAY_PLAN_REQUIRES_ORIGINAL_UNBOUND_HOLD",),
                    None,
                )
            else:
                fill = fixture.build_simulated_fill_v1(
                    fill_id="original-plan:" + envelope.envelope_digest,
                    instrument_id=envelope.instrument_id,
                    side=envelope.side.upper(),
                    quantity=envelope.quantity,
                    mark_price=str(mark - direction * 0.1),
                    contract=sessions[lane].contract,
                    event_time_unix=counter_now,
                )
                fill_args = dict(
                    reservation_id=reservation_id,
                    double_play=reserve_request,
                    injected=plan_args["injected"],
                    decision_epoch=epoch,
                    recovery=plan_args["host_budget_recovery"],
                    fill=fill,
                )
                if lane == "LANE_1":
                    with pytest.raises(
                        ValueError, match="DOUBLE_PLAY_SIMULATED_FILL_ENVELOPE_MISMATCH"
                    ):
                        host.open_simulated_double_play_episode_v1(
                            **dict(fill_args, fill=replace(fill, fill_id="foreign-fill"))
                        )
                    with pytest.raises(
                        ValueError, match="DOUBLE_PLAY_SIMULATED_FILL_ENVELOPE_MISMATCH"
                    ):
                        host.open_simulated_double_play_episode_v1(
                            **dict(fill_args, fill=replace(fill, quantity=fill.quantity + 1))
                        )
                if lane == "LANE_1":
                    from src.ops.exit_policy_producer_binding_v1 import (
                        simulated_accounting_close_v1,
                    )

                    def interrupt_before_episode(**_kwargs):
                        raise OSError("simulated writer interruption")

                    with monkeypatch.context() as patch:
                        patch.setattr(
                            simulated_accounting_close_v1,
                            "create_successor_after_sealed_simulated_episode_v1",
                            interrupt_before_episode,
                        )
                        with pytest.raises(OSError, match="simulated writer interruption"):
                            host.open_simulated_double_play_episode_v1(**fill_args)
                    assert owner.release_plan_failure_v1(reservation_id).reason_codes == (
                        "DOUBLE_PLAY_SIMULATED_FILL_RECONCILIATION_REQUIRED",
                    )
                    with pytest.raises(
                        ValueError, match="DOUBLE_PLAY_SIMULATED_FILL_ALREADY_BOUND"
                    ):
                        host.open_simulated_double_play_episode_v1(
                            **dict(fill_args, fill=replace(fill, mark_price=fill.mark_price + 1))
                        )
                    host.clock = lambda: counter_now + 10
                episode, accounting, native_fills = host.open_simulated_double_play_episode_v1(
                    **fill_args
                )
                assert episode.identity.episode_id != continuation.switch.episode.episode_id
                assert episode.identity.account_scope == world["scope"]
                assert episode.identity.position_side == target_side
                assert episode.identity.instrument_id == bounds[lane].instrument_id
                assert episode.identity.venue_native_id == envelope.instrument_id
                assert episode.binding.entry_price == float(fill.fill_price)
                assert fixture.signed_accounting_quantity(accounting) == -direction * fill.quantity
                assert native_fills == (*world["fills"][lane], fill)
                reopened, reloaded, replayed_fills = host.open_simulated_double_play_episode_v1(
                    **fill_args
                )
                assert reopened.identity == episode.identity
                assert replayed_fills == native_fills
                assert reloaded.to_durable_dict() == accounting.to_durable_dict()
                bound_link["simulated_fill_digest"] = fill.digest()
                assert owner.read_bound_double_play_execution_plan_v1(reservation_id) == bound_link
                assert owner.risk_snapshot_v1()["state"]["test_slot_economics"] == booked
                assert all(
                    owner.active_slot_sum_v1(other) == original_holds[other]
                    and fixture.signed_accounting_quantity(sessions[other]) == positions[other]
                    for other in bounds
                    if other != lane
                )
                assert all(path.read_bytes() == before for path, before in other_cursors.items())

            policy = owner.entry_budget_policy_v1()
            host.close()
            cold_owner = PortfolioCapitalReservationBudgetOwnerV1(
                durable_root=host.root / "owner",
                durable_account_identity=world["scope"].account_identity,
                durable_mode="recover",
                durable_lane_bindings=bounds,
                entry_budget_policy=policy,
            )
            try:
                restored = cold_owner.lookup_v1(
                    slot_id=lane,
                    decision_id=decision_id,
                    cycle_id=decision_id,
                    observation_id="other-observation",
                )
                assert str(restored.reservation_id) == reservation_id
                assert restored.state is expected_state
                assert restored.amount == quantity.resulting_notional
                assert (
                    cold_owner.risk_snapshot_v1()["state"]["sizing_bindings"][reservation_id]
                    == (snapshot["sizing_bindings"][reservation_id])
                )
                assert not cold_owner.budget_state_v1().admitted
                assert (
                    cold_owner.read_bound_double_play_execution_plan_v1(reservation_id)
                    == bound_link
                )
            finally:
                cold_owner.close()
            return

        counter = _exercise_counter_plan(world, lane, continuation, counter_replay, counter_now)
        sessions[lane].apply_fill(
            fixture.build_simulated_fill_v1(
                fill_id="intrabar-counter:" + counter.envelope_digest,
                instrument_id=counter.instrument_id,
                side=counter.side.upper(),
                quantity=counter.quantity,
                mark_price=str(mark - direction * 0.1),
                contract=sessions[lane].contract,
                event_time_unix=now + 1.25,
            )
        )
        assert fixture.signed_accounting_quantity(sessions[lane]) == (
            -direction * Decimal(counter.quantity)
        )
        assert 0 < host.owner.active_slot_sum_v1(lane) <= Decimal(25)
        after_counter = host.owner.risk_snapshot_v1()
        repeated_feedback = reconcile(**reconciliation).post_close_feedback
        assert repeated_feedback.capital_refresh.disposition.value == "IDEMPOTENT_REPLAY"
        assert repeated_feedback.status == "RECONCILED_FLAT_DOUBLE_PLAY_PENDING"
        assert repeated_feedback.double_play_continuation is None
        assert "BOUNDED_CLOSE_REFRESH_UNPROVEN_OR_SLOT_OCCUPIED" in repeated_feedback.reason_codes
        assert host.owner.risk_snapshot_v1() == after_counter
        assert [
            record for record in after_counter["state"]["reservations"] if record["slot_id"] != lane
        ] == other_reservations
        assert all(
            host.owner.active_slot_sum_v1(slot) == hold
            and fixture.signed_accounting_quantity(sessions[slot]) == positions[slot]
            and host.bindings[slot] == bounds[slot]
            for slot, hold in original_holds.items()
            if slot != lane
        )
        assert all(path.read_bytes() == before for path, before in other_cursors.items())
        if lane == "LANE_1":
            policy = host.owner.entry_budget_policy_v1()
            assert policy.per_slot_test_loss_limit is None
            host.close()
            cold_owner = PortfolioCapitalReservationBudgetOwnerV1(
                durable_root=host.root / "owner",
                durable_account_identity=world["scope"].account_identity,
                durable_mode="recover",
                durable_lane_bindings=bounds,
                entry_budget_policy=policy,
            )
            try:
                assert cold_owner.risk_snapshot_v1()["state"]["test_slot_economics"] == booked
                assert cold_owner.slot_capital_basis_v1(lane, close_booking=booking) == basis
                assert not cold_owner.budget_state_v1().admitted
            finally:
                cold_owner.close()
    finally:
        host.close()
