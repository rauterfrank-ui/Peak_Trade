"""Bounded offline position feedback; a terminal order does not end a position."""

from dataclasses import replace

import pytest

from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    OccupiedLaneRuntimeInstrumentIdentityV1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.position_truth_v1 import (
    PerLanePositionTruthError,
    resolve_all_lane_position_truths_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_integration_v1 import (
    run_full_core_offline_exchange_reconciliation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    LocalSubmitOutcome,
)
from tests.ops.test_current_productive_occupied_scope_continuity_v1 import _cycle
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _bound,
)
from tests.ops.test_full_core_exchange_reconciliation_v1 import _binding, _identity, _order_row
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide


def _position(payload, *, global_flat=True, global_side=ExistingPositionSide.NONE):
    identity = OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(lane_id="LANE_1", bound=_bound())
    return resolve_all_lane_position_truths_v1(
        identities={"LANE_1": identity},
        occupancy_payloads=payload,
        global_venue_flat=global_flat,
        global_existing_position_side=global_side,
        multi_lane=False,
    )["LANE_1"]


@pytest.mark.parametrize(
    "side,qty,expected",
    [
        ("long", "1", ExistingPositionSide.LONG),
        ("short", "1", ExistingPositionSide.SHORT),
        ("net", "-1", ExistingPositionSide.SHORT),
    ],
)
def test_single_slot_uses_supplied_position_instead_of_flat_default(side, qty, expected):
    response = {
        "code": "0",
        "data": [{"instId": _bound().venue_native_id, "posSide": side, "pos": qty}],
    }
    for payload in (response, {"POSITIONS": response}):
        truth = _position(payload)
        assert truth.venue_flat is False
        assert truth.existing_position_side is expected
        assert truth.position_status_source == "extract_position_truth_v1"


def test_confirmed_flat_response_is_not_replaced_by_old_global_position():
    truth = _position(
        {"POSITIONS": {"code": "0", "data": []}},
        global_flat=False,
        global_side=ExistingPositionSide.LONG,
    )
    assert truth.venue_flat is True
    assert truth.existing_position_side is ExistingPositionSide.NONE


@pytest.mark.parametrize(
    "response",
    [
        None,
        {"code": "50011", "data": []},
        {"code": "0"},
        {"code": "0", "data": [None]},
        {"code": "0", "data": [{"instId": "x", "pos": "nan"}]},
        {"code": "0", "data": [{"instId": "x"}]},
    ],
)
def test_unusable_explicit_position_response_never_becomes_flat(response):
    with pytest.raises(PerLanePositionTruthError):
        _position({"POSITIONS": response})


def test_legacy_single_slot_without_position_response_retains_explicit_global_input():
    truth = _position({}, global_flat=False, global_side=ExistingPositionSide.SHORT)
    assert truth.venue_flat is False
    assert truth.existing_position_side is ExistingPositionSide.SHORT


def test_foreign_open_position_is_not_hidden_by_single_slot_flat_default():
    truth = _position(
        {
            "POSITIONS": {
                "code": "0",
                "data": [{"instId": "another-future", "posSide": "long", "pos": "1"}],
            }
        }
    )
    assert truth.venue_flat is False
    assert truth.status == "FOREIGN_OPEN_POSITION_MAX_POSITIONS_1"


@pytest.mark.parametrize("direction", [1, -1])
def test_filled_order_with_open_position_continues_the_same_scope(tmp_path, direction):
    cursor = None
    for step in range(3):
        cycle = _cycle(tmp_path, direction=direction, step=step, incoming=cursor)
        assert cycle.replay_pass == "true", cycle.fail_reasons
        cursor = cycle.outgoing_cursor
    assert cycle.decision_outcome == ("enter_long" if direction == 1 else "enter_short")
    bound = _bound()
    binding = replace(
        _binding(),
        instrument_id=bound.instrument_id,
        native_id=bound.venue_native_id,
        selected_direction="ENTER_LONG" if direction == 1 else "ENTER_SHORT",
        order_side="buy" if direction == 1 else "sell",
    )
    row = {**_order_row(state="filled", acc="10"), "instId": bound.venue_native_id}
    positions = {
        "code": "0",
        "data": [
            {
                "instId": bound.venue_native_id,
                "pos": "10",
                "posSide": "long" if direction == 1 else "short",
            }
        ],
    }
    reconciled = run_full_core_offline_exchange_reconciliation_v1(
        identity=_identity(binding),
        binding=binding,
        fixture=OfflineExchangeFixtureV1(order_history={"data": [row]}, positions=positions),
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert reconciled.decision.reconciliation_complete is True
    assert reconciled.decision.outcome == "CONFIRMED_FILLED"
    assert reconciled.decision.exposure_retained is True
    truth = _position({"POSITIONS": positions})
    assert truth.venue_flat is False
    assert truth.existing_position_side is (
        ExistingPositionSide.LONG if direction == 1 else ExistingPositionSide.SHORT
    )
    followup = _cycle(
        tmp_path,
        direction=direction,
        step=3,
        incoming=cursor,
        occupied=not truth.venue_flat,
    )
    assert followup.replay_pass == "true", followup.fail_reasons
    assert followup.cursor_restore_status == "restored"
    assert followup.outgoing_cursor.existing_scope.scope_id == cursor.existing_scope.scope_id
    assert followup.decision_outcome not in {"enter_long", "enter_short"}
