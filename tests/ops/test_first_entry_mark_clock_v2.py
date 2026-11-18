import json
import socket
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from src.ops.first_entry_mark_clock_v2 import run_first_entry_mark_cycle_v2
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
    load_current_productive_sidestate_confirmation_cursor_v1,
    parse_current_productive_sidestate_confirmation_cursor_v1,
)
from tests.ops._current_productive_reconciliation_admission_test_helpers_v1 import (
    non_productive_harness_master_v2_reconciliation_admission_v1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    assert_complete_decision_ssot_layer_trace_v1,
    governed_c1_aligned_g17_dk_producer_v1,
)
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1 import (
    _bound,
)


CANDLE_OPEN = 1_700_000_040
INSTRUMENT = "okx_eea:linear_perpetual:BREV:USDT:USDT:brev-usdt-swap"
NATIVE = "BREV-USDT-SWAP"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def deny(*args, **kwargs):
        pytest.fail("The first-entry and occupied-scope proof is offline")

    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)


def market_kwargs(tmp_path, direction):
    bound = replace(_bound(lane_id="LANE_1", instrument_id=INSTRUMENT), venue_native_id=NATIVE)
    closes = [0.11 * (1 + direction * (i - 99) * 0.002) for i in range(100)]
    candles = [
        [str(1000 * (CANDLE_OPEN + (i - 99) * 60)), *(str(close),) * 4, "5", "5", "5", "1"]
        for i, close in enumerate(closes)
    ]
    return {
        "offline_state_root": tmp_path,
        "bound": bound,
        "candles_payload": {"code": "0", "data": candles},
        "index_tickers_payload": None,
        "bid_px": 0.1099,
        "ask_px": 0.1101,
        "volume": 100.0,
        "open_interest": 200.0,
        "funding_rate": 0.0001,
        "venue_flat": True,
        "g17_producer": governed_c1_aligned_g17_dk_producer_v1(
            bound=bound, anchor_event_ts_unix=CANDLE_OPEN, evidence_store_root=tmp_path / "g17"
        ),
        "reconciliation": non_productive_harness_master_v2_reconciliation_admission_v1(
            bound=bound, session_id="offline-brev-mark", repository_sha="f" * 40
        ),
    }


def mark_kwargs(seconds, mark, *, native=NATIVE, acquisition_lag=0.1):
    event = CANDLE_OPEN + 60 + seconds
    acquired = event + acquisition_lag
    return {
        "cycle_id": f"brev-first-entry-{seconds}",
        "observed_unix": acquired + 0.1,
        "mark_acquired_at_utc": datetime.fromtimestamp(acquired, timezone.utc).isoformat(),
        "mark_price_payload": {
            "code": "0",
            "data": [
                {"instId": native, "markPx": str(mark), "idxPx": "0.11", "ts": str(event * 1000)}
            ],
        },
    }


@pytest.mark.parametrize(("direction", "side"), [(1, "long"), (-1, "short")])
def test_brev_entry_confirms_on_new_marks_in_same_bar(tmp_path, direction, side):
    market = market_kwargs(tmp_path, direction)
    lane = tmp_path / "flat-entry-mark-v2" / "LANE_1"
    outcomes = []
    for i, seconds in enumerate((2, 4, 6, 8, 10)):
        mark = round(0.11 + direction * i * 0.001, 5)
        tick = mark_kwargs(seconds, mark)
        result = run_first_entry_mark_cycle_v2(**market, **tick)
        assert result.candle_open_unix == CANDLE_OPEN
        replay = result.cycle.replay
        assert replay.replay_pass, replay.fail_reasons
        assert replay.intermediate.market_context.mark_price == pytest.approx(mark)
        cursor_path = lane / CURSOR_FILENAME
        disk = cursor_path.read_bytes()
        cursor = json.loads(disk)
        state = cursor["cap61_confirmation_state"]["observation_acceptance_state"]
        assert (
            state["last_accepted_observation_identity"]["venue_event_time"]
            == result.mark_event_unix
        )
        assert state["market_observation_epoch"]["value"] == i + 1
        outcomes.append(result.cycle.decision_outcome)
        if result.status == "ENTRY_DECIDED":
            break
        if i:
            duplicate = run_first_entry_mark_cycle_v2(**market, **tick)
            assert duplicate.status == "WAITING_FOR_NEW_MARK" and duplicate.cycle is None
            old = run_first_entry_mark_cycle_v2(**market, **mark_kwargs(seconds - 1, mark))
            assert old.status == "WAITING_FOR_NEW_MARK" and old.cycle is None
            assert cursor_path.read_bytes() == disk
    assert outcomes[-1] == "enter_" + side, outcomes
    assert_complete_decision_ssot_layer_trace_v1(result.cycle, expected_selected_side=side)
    assert all(outcome in {"no_action", "observe", "hold"} for outcome in outcomes[:-1]), outcomes
    terminal = run_first_entry_mark_cycle_v2(**market, **mark_kwargs(12, 0.11))
    assert terminal.status == "ENTRY_ALREADY_DECIDED" and terminal.cycle is None
    assert cursor_path.read_bytes() == disk


@pytest.mark.parametrize(
    ("overrides", "tick", "reason"),
    [
        ({"venue_flat": False}, mark_kwargs(4, 0.11), "REQUIRES_FLAT_POSITION"),
        ({}, mark_kwargs(4, 0.11, native="ETH-USDT-SWAP"), "CMC_MARK_MISSING"),
        ({}, mark_kwargs(4, 0.11, acquisition_lag=6.0), "STALE_OVER_MAX_AGE"),
        ({}, mark_kwargs(-1, 0.11), "PRECEDES_CANDLE_CLOSE"),
    ],
)
def test_rejections_leave_the_original_lane_untouched(tmp_path, overrides, tick, reason):
    market = market_kwargs(tmp_path, 1)
    run_first_entry_mark_cycle_v2(**market, **mark_kwargs(2, 0.11))
    cursor_path = tmp_path / "flat-entry-mark-v2" / "LANE_1" / CURSOR_FILENAME
    before = cursor_path.read_bytes()
    with pytest.raises(ValueError, match=reason):
        run_first_entry_mark_cycle_v2(**(market | overrides), **tick)
    assert cursor_path.read_bytes() == before


@pytest.mark.parametrize("publish_c1", ["original", "v2", "v2-interrupted"])
def test_brev_simulated_fill_hands_fresh_mark_and_full_scope_to_occupied_logic(
    tmp_path, monkeypatch, publish_c1
):
    from decimal import Decimal

    from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
        compose_occupied_lane_mv2_dp_durable_cycle_v1,
    )
    from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
        PositionEpisodeIdentityV1,
        PositionEpisodeScopeV1,
    )
    from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
        bind_simulated_accounting_episode_identity_v1,
        create_position_episode_from_simulated_accounting_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
        build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
        extract_finalized_candle_closes_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
        build_s8_occupied_lane_pairs_v1,
    )
    from src.ops.offline_first_entry_budget_v2 import OfflineFirstEntryBudgetOwnerV2
    from src.ops import offline_first_entry_position_v2 as occupied_entry
    from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
        read_occupied_scope_mark_snapshot_v1,
        restore_layered_core_episode_v1,
    )
    from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
        ProductiveFuturesAccountingSessionV1,
    )
    from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (
        build_simulated_fill_v1,
    )
    from tests.ops.test_bounded_slot_connected_roundtrip_v1 import _contract
    from tests.ops.test_simulated_accounting_entry_source_v1 import _args
    from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide

    market = market_kwargs(tmp_path, 1)
    bound = market["bound"]
    for i in range(5):
        price = round(0.11 + i * 0.001, 5)
        entry = run_first_entry_mark_cycle_v2(**market, **mark_kwargs(2 + 2 * i, price))
        if entry.status == "ENTRY_DECIDED":
            break
    assert entry.cycle.decision_outcome == "enter_long"

    scope = PositionEpisodeScopeV1("offline-brev", "INTERNAL_SIMULATED_EXECUTION")
    session = ProductiveFuturesAccountingSessionV1(
        contract=_contract(NATIVE, contract_size="0.01", min_qty="1")
    )
    fill = build_simulated_fill_v1(
        fill_id=entry.cycle.replay.evidence.decision_id,
        instrument_id=NATIVE,
        side="BUY",
        quantity="7",
        mark_price=str(price),
        contract=session.contract,
        event_time_unix=entry.mark_event_unix + 1,
    )
    session.apply_fill(fill)
    assert session.position.qty == Decimal("7")
    identity = bind_simulated_accounting_episode_identity_v1(
        identity=PositionEpisodeIdentityV1("LANE_1", INSTRUMENT, NATIVE, "pending", "long", scope),
        opening_fill=fill,
    )
    episode = create_position_episode_from_simulated_accounting_v1(
        **_args(tmp_path / "position-episode", identity), session=session, fills=(fill,)
    )
    pairs = build_s8_occupied_lane_pairs_v1(
        lane_state_root=tmp_path / "flat-entry-mark-v2", bound=bound
    )
    lane = tmp_path / "flat-entry-mark-v2" / "LANE_1"
    assert read_occupied_scope_mark_snapshot_v1(lane) is None
    entry_confirmation = (
        entry.cycle.outgoing_cursor.cap61_confirmation_state.observation_acceptance_state
    )
    closes, candle_open = extract_finalized_candle_closes_v1(market["candles_payload"])
    assert candle_open == entry.candle_open_unix
    if publish_c1 != "original":
        # This fixture isolates the clock transition. Its synthetic fill does
        # not include the cost-bound reservation exercised by the ZKP replay.
        owner = OfflineFirstEntryBudgetOwnerV2.__new__(OfflineFirstEntryBudgetOwnerV2)
        monkeypatch.setattr(owner, "retain_opening_fill_v2", lambda **_: "retained")
        handoff = dict(
            owner=owner,
            reservation_id="fixture-hold",
            episode=episode,
            cursor_root=lane,
            g17_producer=market["g17_producer"],
            writer_session_id="brev-occupied-c1",
        )
        if publish_c1 == "v2-interrupted":

            def interrupt(**_):
                raise InterruptedError("after the Exit publication commit")

            with monkeypatch.context() as fault:
                fault.setattr(occupied_entry, "recover_current_cursor_publication_v1", interrupt)
                with pytest.raises(InterruptedError, match="Exit publication"):
                    occupied_entry.bind_offline_first_entry_position_v2(**handoff)
            unchanged = load_current_productive_sidestate_confirmation_cursor_v1(lane)
            assert unchanged == entry.cycle.outgoing_cursor.to_dict()

        published = occupied_entry.bind_offline_first_entry_position_v2(**handoff)
        assert published["status"] == "PUBLISHED_RETAINED_CURSOR"
        assert (
            occupied_entry.bind_offline_first_entry_position_v2(**handoff)["status"]
            == "ALREADY_PUBLISHED"
        )
        raw = load_current_productive_sidestate_confirmation_cursor_v1(lane)
        clock = raw["cap61_confirmation_state"]["observation_acceptance_state"][
            "last_accepted_observation_identity"
        ]
        assert clock["venue_event_time"] == candle_open
        (last_c1,) = market["g17_producer"].history.trailing_window_records_v1(count=1)
        assert clock["mark_price"] == last_c1.mark_price
        assert raw["trading_epoch"] == entry.cycle.outgoing_cursor.trading_epoch
        entry_confirmation = parse_current_productive_sidestate_confirmation_cursor_v1(
            raw
        ).cap61_confirmation_state.observation_acceptance_state

    for offset in (2, 4, 6):
        native = restore_layered_core_episode_v1(lane, expected_instrument_id=INSTRUMENT)
        favorable = 1 if native.regime.value == "bull" else -1
        switch = offset == 6
        move = -1.5 * native.scope.d_t if switch else 0.00001
        current_mark = round(native.running_reference.reference_price_r_t + favorable * move, 8)
        seconds = int(entry.mark_event_unix - CANDLE_OPEN - 60 + offset)
        tick = mark_kwargs(seconds, current_mark)
        provenance = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
            mark_price_payload=tick["mark_price_payload"],
            venue_native_id=NATIVE,
            mark_acquired_at_utc=tick["mark_acquired_at_utc"],
        )
        cycle = compose_occupied_lane_mv2_dp_durable_cycle_v1(
            pairs,
            cycle_id_prefix=f"brev-occupied-{seconds}",
            observed_unix=tick["observed_unix"],
            mark_px=provenance.mark_px,
            index_px=provenance.index_px,
            bid_px=market["bid_px"],
            ask_px=market["ask_px"],
            volume=market["volume"],
            open_interest=market["open_interest"],
            funding_rate=market["funding_rate"],
            finalized_closes=closes,
            last_finalized_event_ts_unix=candle_open,
            venue_flat=False,
            existing_position_side=ExistingPositionSide.LONG,
            g17_typed_vol_producers={"LANE_1": market["g17_producer"]},
            canonical_price_provenance=provenance,
            master_v2_reconciliation_admission=market["reconciliation"],
            position_episode_bindings={"LANE_1": episode},
            position_episode_scope=scope,
            occupied_scope_mark=True,
            incoming_cursor_override=load_current_productive_sidestate_confirmation_cursor_v1(lane),
        )["LANE_1"].cycle_result
        assert cycle.replay.replay_pass, cycle.fail_reasons
        assert cycle.decision_outcome not in {"enter_long", "enter_short"}
        price_frame = cycle.outgoing_cursor.entry_assessment_frame
        observed = json.loads(price_frame["market_context"]["canonical"])
        assert observed["mark_price"] == current_mark
        ctx = cycle.replay.intermediate.market_context
        assert ctx.mark_price == current_mark
        assert ctx.market_event_time == observed["market_event_time"]
        distance = ctx.volatility_estimate * current_mark
        snapshot = read_occupied_scope_mark_snapshot_v1(lane)
        assert snapshot["mark"]["prices"] == [current_mark]
        assert snapshot["mark"]["switch_condition_met"] is switch
        assert (snapshot["mark"]["counter_move"] >= distance) is switch
        assert snapshot["mark"]["event_unix"] == entry.mark_event_unix + offset
        assert snapshot["mark"]["position_episode_id"] == episode.identity.episode_id
        assert snapshot["snapshot"]["scope"]["d_t"] == pytest.approx(distance)
        assert cycle.replay.intermediate.effective_scope_magnitude == pytest.approx(distance)
        confirmation = cycle.outgoing_cursor.cap61_confirmation_state.observation_acceptance_state
        assert confirmation.market_observation_epoch == entry_confirmation.market_observation_epoch
        assert (
            confirmation.last_accepted_observation_identity
            == entry_confirmation.last_accepted_observation_identity
        )
