"""Occupied-position management reaches DP without opening the entry path."""

from pathlib import Path
from decimal import Decimal
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    invoke_join_v1 as consumer,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneSlotV1,
    lane_state_root_for,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    persist_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    PREVIOUS_C1_VENUE_EVENT_TIME,
)
from tests.ops._current_productive_canonical_price_test_helpers_v1 import provenance_for_bound_v1
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_candles_payload_from_enter_closes_v1,
)
from tests.ops.test_current_productive_occupied_scope_continuity_v1 import _cycle
from tests.ops.test_full_core_current_productive_governed_cycle_orchestrator_v1 import (
    _run,
    _occupancy_present,
    _t2_hold,
    _t2_enter,
)
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _bound,
    _produced_g17_producer,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide


def test_known_open_position_uses_only_management_dispatch(tmp_path):
    entry = Mock(side_effect=AssertionError("entry must remain closed"))
    management = Mock(side_effect=_t2_hold)
    result = _run(
        tmp_path,
        occupancy_payloads=_occupancy_present(),
        t2_cycle_dispatch=entry,
        position_management_cycle_dispatch=management,
    )
    assert result.disposition == "COMPLETED"
    assert result.terminal_class == "POSITION_MANAGEMENT_EVALUATED"
    management.assert_called_once()
    entry.assert_not_called()
    assert not result.envelope_created
    assert not result.permit_created
    assert result.post_count == 0


@pytest.mark.parametrize("problem", ["foreign", "pending", "unknown", "duplicate", "config_error"])
def test_ambiguous_or_foreign_occupancy_never_reaches_either_dispatch(tmp_path, problem):
    payload = _occupancy_present()
    if problem == "foreign":
        payload["POSITIONS"]["data"][0]["instId"] = "foreign-future"
    elif problem == "duplicate":
        payload["POSITIONS"]["data"] *= 2
    elif problem == "pending":
        payload["PENDING"]["data"] = [{"instId": "0G-USDT-SWAP", "ordId": "pending"}]
    elif problem == "unknown":
        payload["PENDING_ERROR"] = "UNKNOWN_OUTCOME"
    else:
        payload["CONFIG"]["code"] = "50011"
    entry, management = Mock(), Mock()
    result = _run(
        tmp_path,
        occupancy_payloads=payload,
        t2_cycle_dispatch=entry,
        position_management_cycle_dispatch=management,
    )
    assert result.disposition == "FAIL_CLOSED"
    entry.assert_not_called()
    management.assert_not_called()


def test_management_result_cannot_smuggle_an_entry_envelope(tmp_path):
    result = _run(
        tmp_path,
        occupancy_payloads=_occupancy_present(),
        position_management_cycle_dispatch=_t2_enter,
    )
    assert result.disposition == "FAIL_CLOSED"
    assert result.reason_code == "POSITION_MANAGEMENT_ENTRY_FORBIDDEN"
    assert not result.envelope_created
    assert not result.permit_created


def test_management_can_report_reduce_without_preparing_a_new_order(tmp_path):
    def reduce(**kwargs):
        result = _t2_hold(**kwargs)
        result.master_v2_decision = "reduce"
        result.decision_result = "POSITION_MANAGEMENT_ACTION_PENDING"
        return result

    result = _run(
        tmp_path, occupancy_payloads=_occupancy_present(), position_management_cycle_dispatch=reduce
    )
    assert result.disposition == "COMPLETED"
    assert result.master_v2_decision == "reduce"
    assert result.first_genuine_blocker == "POSITION_MANAGEMENT_EXECUTION_HANDOFF_REQUIRED"
    assert result.terminal_class == "POSITION_MANAGEMENT_ACTION_PENDING"
    assert not result.envelope_created
    assert result.post_count == 0


def test_claimed_close_plan_without_typed_receipt_is_rejected(tmp_path):
    def unbound_close(**kwargs):
        result = _t2_hold(**kwargs)
        result.master_v2_decision = "exit"
        result.decision_result = "POSITION_MANAGEMENT_VENUE_PLAN_BOUND"
        return result

    result = _run(
        tmp_path,
        occupancy_payloads=_occupancy_present(),
        position_management_cycle_dispatch=unbound_close,
    )
    assert result.disposition == "FAIL_CLOSED"
    assert not result.envelope_created and result.post_count == 0


@pytest.mark.parametrize("direction", [1, -1])
@pytest.mark.parametrize("safety_exit", [False, True])
@pytest.mark.parametrize("remaining_quantity", ["1", "0.4"])
@pytest.mark.parametrize("position_mode", ["net_mode", "long_short_mode"])
def test_real_lane_host_continues_open_position_through_double_play(
    tmp_path, monkeypatch, direction, safety_exit, remaining_quantity, position_mode
):
    bound = _bound()
    root = Path(lane_state_root_for(topology_state_root_base=tmp_path, lane_id="LANE_1"))
    cursor = None
    base_ts = float(PREVIOUS_C1_VENUE_EVENT_TIME) + 60.0
    for step in range(3):
        previous = _cycle(
            root, direction=direction, step=step, incoming=cursor, event_time_base=base_ts
        )
        assert previous.replay_pass == "true", previous.fail_reasons
        cursor = previous.outgoing_cursor
    assert previous.decision_outcome == ("enter_long" if direction == 1 else "enter_short")
    persist_current_productive_sidestate_confirmation_cursor_v1(cursor, store_root=root)
    slot = IsolatedLaneSlotV1(
        lane_id="LANE_1",
        occupancy="OCCUPIED",
        canonical_instrument_id=bound.instrument_id,
        lane_state_root=str(root),
        universe_snapshot_id=bound.universe_snapshot_id,
        ranking_snapshot_id=bound.ranking_snapshot_id,
        ranking_integrity_digest=bound.ranking_integrity_digest,
    )
    mark = 1000.0 + direction * 22.4
    ts = base_ts + 180.0
    closes = tuple(1000.0 + direction * 20.0 * i / 99 for i in range(100))
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=closes, last_event_ts_unix=ts
    )
    entry_join = Mock(side_effect=AssertionError("occupied management reached entry sizing"))
    monkeypatch.setattr(
        consumer, "join_current_productive_enter_live_29p_before_venue_plan_v1", entry_join
    )
    if safety_exit:
        from src.ops.full_core_live_path_composition_root_v1 import (
            current_productive_master_v2_runtime_cycle_v1 as host,
        )

        monkeypatch.setattr(
            host,
            "resolve_durable_kill_switch_for_mv2_host_v1",
            lambda **kwargs: SimpleNamespace(
                killstate_active=True, killstate_trigger="OFFLINE_SAFETY_EXIT_TEST"
            ),
        )
    results = consumer.invoke_occupied_lane_governed_cycle_n1_consumer_v1(
        {"LANE_1": (slot, bound)},
        origin_main_sha="offline-management-proof",
        cycle_id_prefix=f"management:{direction}",
        observed_unix=ts + 1.0,
        mark_px=mark,
        index_px=mark * 0.995,
        bid_px=mark - 0.5,
        ask_px=mark + 0.5,
        volume=12345.0,
        open_interest=1000.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=ts,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        candles_payload=candles,
        occupancy_payloads={
            "POSITIONS": {
                "code": "0",
                "data": [
                    {
                        "instId": bound.venue_native_id,
                        "pos": remaining_quantity,
                        "posSide": "long" if direction == 1 else "short",
                    }
                ],
            },
            "PENDING": {"code": "0", "data": []},
            "CONFIG": {"code": "0", "data": [{"acctLv": "2", "posMode": position_mode}]},
        },
        g17_typed_vol_producers={
            "LANE_1": _produced_g17_producer(instrument_id=bound.instrument_id)
        },
        canonical_price_provenance=provenance_for_bound_v1(
            bound=bound, mark_px=mark, index_px=mark * 0.995
        ),
        live_29p_injected=(
            consumer.CurrentProductiveEnterLive29PInjectedGetV1(
                observed_at=consumer._iso_utc(ts),
                instruments_payload={
                    "code": "0",
                    "data": [
                        {
                            "instId": bound.venue_native_id,
                            "instType": "SWAP",
                            "ctType": "linear",
                            "ctVal": "1",
                            "lotSz": "0.1",
                            "minSz": "0.1",
                            "tickSz": "0.1",
                            "state": "live",
                        }
                    ],
                },
            )
            if safety_exit
            else None
        ),
    )
    record = results["LANE_1"]
    cycle = record.governed_cycle_result
    execution_ready = safety_exit and position_mode == "net_mode"
    assert cycle.disposition == ("PRE_EXTERNAL_EFFECT" if execution_ready else "COMPLETED"), (
        cycle.extra
    )
    assert cycle.t2_consumed is True
    assert cycle.occupancy_used == "OCCUPANCY_PRESENT"
    if safety_exit:
        assert cycle.master_v2_decision == "exit"
        assert cycle.decision_execution_eligible == "false"
        envelope = cycle.final_order_envelope
        if execution_ready:
            assert cycle.terminal_class == "POSITION_MANAGEMENT_PRE_EXTERNAL_EFFECT"
            assert cycle.blocker_class == "PRE_EXTERNAL_EFFECT"
            assert cycle.venue_plan_status == "BOUND"
            assert envelope is not None and cycle.envelope_created
            assert envelope.instrument_id == bound.venue_native_id
            assert envelope.side == ("sell" if direction == 1 else "buy")
            assert envelope.quantity == remaining_quantity
            assert envelope.quantity_unit == "CONTRACTS"
            assert envelope.reduce_only is True
        else:
            assert envelope is None
            assert cycle.terminal_class == "POSITION_MANAGEMENT_ACTION_PENDING"
            assert cycle.first_genuine_blocker == "FULL_CLOSE_NET_POSITION_MODE_REQUIRED"
        handoff = record.position_management_quantity_handoff
        assert handoff.status == "CANONICAL_CLOSE_INTENT_BOUND", handoff.reason_codes
        assert handoff.open_quantity == Decimal(remaining_quantity)
        assert handoff.quantity_unit == "CONTRACTS"
        assert handoff.requested_quantity == Decimal(remaining_quantity)
        assert handoff.reason_codes == ()
        close = record.position_management_close_intent
        assert close is not None
        assert close.intent_action == "EXIT" and close.reduce_only is True
        assert close.quantity == handoff.open_quantity
        assert close.submission_authorized is False
        if execution_ready:
            assert envelope.provenance_ref == close.semantic_digest
        assert (
            json.loads(cycle.extra["POSITION_MANAGEMENT_CANONICAL_CLOSE_INTENT"])["quantity"]
            == remaining_quantity
        )
        assert handoff.lane_id == "LANE_1"
        assert handoff.instrument_id == bound.instrument_id
        assert handoff.position_snapshot_digest
        assert json.loads(cycle.extra["POSITION_MANAGEMENT_QUANTITY_HANDOFF"]) == handoff.to_dict()
        ledger = json.loads(
            (Path(record.evidence_root) / "governed_cycle_orchestrator_ledger_v1.json").read_text()
        )
        assert ledger["position_management_quantity_handoff"] == handoff.to_dict()
        assessment = ledger["position_management_close_quantity_assessment"]
        assert assessment["final_quantity"] == remaining_quantity
        assert assessment["position_snapshot_ref"] == handoff.position_snapshot_digest
        assert assessment["quantity_provenance"]["final_quantity"] == remaining_quantity
        assert (
            ledger["position_management_canonical_close_intent"]["semantic_digest"]
            == close.semantic_digest
        )
    else:
        assert cycle.terminal_class == "POSITION_MANAGEMENT_EVALUATED"
    assert cycle.envelope_created is execution_ready
    assert not cycle.permit_created and cycle.post_count == 0
    assert cycle.master_v2_decision not in {"enter", "enter_long", "enter_short"}
    entry_join.assert_not_called()
    assert (
        record.s7_invocation.cycle_result.outgoing_cursor.existing_scope.scope_id
        == cursor.existing_scope.scope_id
    )
