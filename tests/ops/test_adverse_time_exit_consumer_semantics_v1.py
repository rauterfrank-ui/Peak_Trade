"""Original priority and retained obligation through actual occupied N1."""

from decimal import Decimal
from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    invoke_join_v1 as consumer,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneSlotV1,
    lane_state_root_for,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    create_position_episode_from_simulated_accounting_v1,
    recover_position_episode_from_simulated_accounting_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    persist_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    PREVIOUS_C1_VENUE_EVENT_TIME,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    CurrentProductiveGovernedCycleOrchestratorError,
)
from tests.ops._current_productive_canonical_price_test_helpers_v1 import provenance_for_bound_v1
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_candles_payload_from_enter_closes_v1,
)
from tests.ops.test_simulated_accounting_entry_source_v1 import _history, _args
from tests.ops.test_position_episode_exit_continuity_v1 import _bound, _natural_entry
from tests.ops.test_current_productive_occupied_scope_continuity_v1 import _cycle
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _produced_g17_producer,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide


def _scenario(tmp_path, direction):
    base = float(PREVIOUS_C1_VENUE_EVENT_TIME) + 60.0
    identity, accounting, fills = _history(direction, time=base + 120)
    context = create_position_episode_from_simulated_accounting_v1(
        **_args(tmp_path, identity), session=accounting, fills=fills
    )
    bound = _bound()
    core = Path(lane_state_root_for(topology_state_root_base=tmp_path / "lanes", lane_id="LANE_1"))
    cursor = _natural_entry(core, direction, event_time_base=base)
    persist_current_productive_sidestate_confirmation_cursor_v1(cursor, store_root=core)
    slot = IsolatedLaneSlotV1(
        lane_id="LANE_1",
        occupancy="OCCUPIED",
        canonical_instrument_id=bound.instrument_id,
        lane_state_root=str(core),
        universe_snapshot_id=bound.universe_snapshot_id,
        ranking_snapshot_id=bound.ranking_snapshot_id,
        ranking_integrity_digest=bound.ranking_integrity_digest,
    )
    # Stage the original policy obligation through its actual core owner.
    # The governed N1 owner is single-use per evidence root, even with a new
    # caller prefix. Never remove/rebind that ledger to manufacture continuation.
    first = _cycle(
        core,
        direction=direction,
        step=63,
        incoming=cursor,
        occupied=True,
        event_time_base=base,
        position_episode_binding=context,
    )
    assert first.replay.intermediate.entry_exit_decision.exit_class.value == "time_exit"
    persist_current_productive_sidestate_confirmation_cursor_v1(
        first.outgoing_cursor, store_root=core
    )

    def recover():
        return recover_position_episode_from_simulated_accounting_v1(
            identity=context.identity,
            source_path=Path(context.entry_source_ref.split(":", 2)[2]),
            state_root=tmp_path / "episode",
            repository_sha=context.binding.repository_sha,
            config_digest=context.binding.config_digest,
            writer_session_id="semantic-reload",
        )

    def invoke(episode, step, mark, metadata=True):
        ts = base + step * 60
        closes = tuple(1000.0 + direction * 20.0 * i / 99 for i in range(100))
        injected = consumer.CurrentProductiveEnterLive29PInjectedGetV1(
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
        result = consumer.invoke_occupied_lane_governed_cycle_n1_consumer_v1(
            {"LANE_1": (slot, bound)},
            origin_main_sha="offline-semantic-proof",
            cycle_id_prefix=f"obligation:{direction}:{step}",
            observed_unix=ts + 1,
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
            candles_payload=governed_c1_candles_payload_from_enter_closes_v1(
                enter_closes=closes,
                last_event_ts_unix=ts,
            ),
            occupancy_payloads={
                "POSITIONS": {
                    "code": "0",
                    "data": [
                        {
                            "instId": bound.venue_native_id,
                            "pos": "0.4",
                            "posSide": "long" if direction == 1 else "short",
                        }
                    ],
                },
                "PENDING": {"code": "0", "data": []},
                "CONFIG": {"code": "0", "data": [{"acctLv": "2", "posMode": "net_mode"}]},
            },
            g17_typed_vol_producers={
                "LANE_1": _produced_g17_producer(instrument_id=bound.instrument_id)
            },
            canonical_price_provenance=provenance_for_bound_v1(
                bound=bound, mark_px=mark, index_px=mark * 0.995
            ),
            position_episode_bindings={"LANE_1": episode},
            position_episode_scope=identity.account_scope,
            live_29p_injected=injected if metadata else None,
        )["LANE_1"]
        assert not result.governed_cycle_result.permit_created
        assert result.governed_cycle_result.post_count == 0
        return result

    return context, accounting, recover, invoke


@pytest.mark.parametrize("direction", [1, -1])
@pytest.mark.parametrize("metadata", [True, False, "rejected"])
def test_due_time_exit_is_not_fulfilled_by_adverse_reduce(
    tmp_path, monkeypatch, direction, metadata
):
    context, accounting, recover, invoke = _scenario(tmp_path, direction)
    normal = 1000.0 + direction * (20 + 1.2 * 62)
    obligation = context.binding.pending_exit_identity
    assert obligation and context.binding.pending_exit_class == "time_exit"
    restored = recover()
    if metadata == "rejected":
        original = consumer.bind_position_management_quantity_handoff_v1

        def reject(**kwargs):
            handoff = original(**kwargs)
            return replace(
                handoff, status="REJECTED", reason_codes=("POSITION_QUANTITY_METADATA_MISMATCH",)
            )

        monkeypatch.setattr(consumer, "bind_position_management_quantity_handoff_v1", reject)
    second = invoke(restored, 64, 800.0 if direction == 1 else 1250.0, metadata)
    replay = second.s7_invocation.cycle_result.replay
    assert replay.intermediate.entry_exit_decision.exit_class.value == "adverse_scope_exit"
    assert second.governed_cycle_result.master_v2_decision == "reduce"
    assert second.governed_cycle_result.terminal_class == "POSITION_MANAGEMENT_ACTION_PENDING"
    handoff = second.position_management_quantity_handoff
    expected = (
        "POSITION_QUANTITY_METADATA_MISMATCH"
        if metadata == "rejected"
        else "REDUCE_RISK_RULE_REQUIRED"
        if metadata
        else "POSITION_QUANTITY_METADATA_REQUIRED"
    )
    assert handoff.reason_codes == (expected,)
    assert second.governed_cycle_result.first_genuine_blocker == expected
    assert handoff.requested_quantity is None
    assert second.governed_cycle_result.final_order_envelope is None
    assert restored.binding.last_bundle["time_exit"]["triggered"]
    restored = recover()
    assert restored.binding.pending_exit_identity == obligation
    assert restored.binding.pending_exit_class == "time_exit"
    assert accounting.position.qty == Decimal("0.4")
    before = restored.binding.to_canonical_state().to_dict()
    with pytest.raises(
        CurrentProductiveGovernedCycleOrchestratorError, match="CYCLE_AUTHORIZATION_REPLAY"
    ):
        invoke(restored, 65, normal)
    assert restored.binding.to_canonical_state().to_dict() == before
    assert recover().binding.pending_exit_identity == obligation
    assert accounting.position.qty == Decimal("0.4")


@pytest.mark.parametrize("direction", [1, -1])
def test_full_close_preserves_missing_metadata_reason(tmp_path, direction):
    context, accounting, recover, invoke = _scenario(tmp_path, direction)
    obligation = context.binding.pending_exit_identity
    result = invoke(recover(), 64, 1000.0 + direction * (20 + 1.2 * 62), metadata=False)
    cycle = result.governed_cycle_result
    assert cycle.master_v2_decision == "exit"
    assert result.position_management_quantity_handoff.reason_codes == (
        "POSITION_QUANTITY_METADATA_REQUIRED",
    )
    assert cycle.first_genuine_blocker == "POSITION_QUANTITY_METADATA_REQUIRED"
    assert cycle.final_order_envelope is None
    assert recover().binding.pending_exit_identity == obligation
    assert accounting.position.qty == Decimal("0.4")
