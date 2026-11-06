"""Caller-bound position continuity through the actual existing exit/DP owners."""

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.exit_policy_producer_binding_v1.constants_v1 import FROZEN_PROFIT_PROTECTION_DISTANCE
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    PositionEpisodeIdentityV1,
    PositionEpisodeScopeV1,
    open_position_episode_binding_v1,
)
from src.ops.exit_policy_producer_binding_v1.persistence_v1 import ExitPolicyPersistenceError
from tests.ops.test_current_productive_occupied_scope_continuity_v1 import _cycle, _bound
from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    layer_c_derived_exit_policy_adverse_config_digest_v1,
)


def _identity(direction=1):
    bound = _bound()
    return PositionEpisodeIdentityV1(
        lane_id="LANE_1",
        instrument_id=bound.instrument_id,
        venue_native_id=bound.venue_native_id,
        episode_id="injected-confirmed-position",
        position_side="long" if direction == 1 else "short",
        account_scope=PositionEpisodeScopeV1("test-account", "INTERNAL_SIMULATED_EXECUTION"),
    )


def _open(root, direction=1, mode="create", unknown=False, **overrides):
    kwargs = dict(
        identity=_identity(direction),
        state_root=root,
        mode=mode,
        repository_sha="test-revision",
        config_digest=layer_c_derived_exit_policy_adverse_config_digest_v1(
            profit_protection_distance=FROZEN_PROFIT_PROTECTION_DISTANCE
        ),
        writer_session_id="test-episode",
    )
    if mode == "create" and not unknown:
        kwargs.update(
            entry_price=1000.0 + direction * 21.2,
            entry_event_time=1700000120.0,
            entry_trading_epoch=3,
            entry_source_ref="test-only/confirmed-entry-observation",
            entry_price_basis="CONFIRMED_POSITION_ENTRY_PRICE",
        )
    kwargs.update(overrides)
    return open_position_episode_binding_v1(**kwargs)


def _natural_entry(root, direction, event_time_base=1700000000.0):
    cursor = None
    for step in range(3):
        result = _cycle(
            root, direction=direction, step=step, incoming=cursor, event_time_base=event_time_base
        )
        assert result.replay_pass == "true", result.fail_reasons
        cursor = result.outgoing_cursor
    assert result.decision_outcome == ("enter_long" if direction == 1 else "enter_short")
    return cursor


@pytest.mark.parametrize("direction", [1, -1])
def test_real_cycle_consumes_original_entry_time_after_durable_episode_reload(tmp_path, direction):
    core_root = tmp_path / "core"
    cursor = _natural_entry(core_root, direction)
    episode_root = tmp_path / "exit-episode"
    context = _open(episode_root, direction)
    first = _cycle(
        core_root,
        direction=direction,
        step=3,
        incoming=cursor,
        occupied=True,
        position_episode_binding=context,
    )
    assert first.replay_pass == "true", first.fail_reasons
    assert not context.binding.last_bundle["time_exit"]["triggered"]
    original_entry_time = context.binding.entry_event_time
    context = _open(episode_root, direction, mode="recover")
    after = _cycle(
        core_root,
        direction=direction,
        step=63,
        incoming=first.outgoing_cursor,
        occupied=True,
        position_episode_binding=context,
    )
    assert after.replay_pass == "true", after.fail_reasons
    assert context.binding.entry_event_time == original_entry_time
    assert context.binding.last_bundle["time_exit"]["triggered"]
    assert after.decision_outcome == "exit"
    assert after.replay.intermediate.entry_exit_decision.exit_class.value == "time_exit"
    assert context.binding.pending_exit_identity
    restored = _open(episode_root, direction, mode="recover")
    assert restored.binding.pending_exit_identity == context.binding.pending_exit_identity


def test_unknown_entry_is_not_replaced_by_mark_or_current_time(tmp_path):
    core_root = tmp_path / "core"
    cursor = _natural_entry(core_root, 1)
    context = _open(tmp_path / "episode", unknown=True)
    result = _cycle(
        core_root, step=63, incoming=cursor, occupied=True, position_episode_binding=context
    )
    assert result.replay_pass == "true", result.fail_reasons
    assert context.binding.entry_price is None
    assert context.binding.entry_event_time is None
    assert not context.binding.last_bundle["time_exit"]["triggered"]
    assert not context.binding.last_bundle["profit_protection"]["triggered"]
    assert result.replay.intermediate.entry_exit_decision.exit_class.value != "time_exit"


@pytest.mark.parametrize(
    "field,value",
    [
        ("lane_id", "LANE_2"),
        ("instrument_id", "foreign"),
        ("venue_native_id", "FOREIGN-SWAP"),
        ("episode_id", "other-episode"),
        ("position_side", "short"),
    ],
)
def test_recovery_rejects_different_episode_identity_without_mutation(tmp_path, field, value):
    root = tmp_path / "episode"
    _open(root)
    before = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
    with pytest.raises(ValueError, match="RESTORE_IDENTITY_UNPROVEN"):
        _open(root, mode="recover", identity=replace(_identity(), **{field: value}))
    assert {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()} == before


def test_existing_episode_never_implicitly_recreates_or_overwrites_anchors(tmp_path):
    root = tmp_path / "episode"
    _open(root)
    with pytest.raises(FileExistsError):
        _open(root)
    with pytest.raises(ValueError, match="CANNOT_REPLACE_ENTRY_ANCHORS"):
        _open(root, mode="recover", entry_price=999.0)


def test_stale_episode_writer_cannot_overwrite_newer_exit_obligation(tmp_path):
    root = tmp_path / "episode"
    first = _open(root)
    stale = _open(root, mode="recover")
    args = dict(
        instrument_id=_identity().instrument_id,
        venue_native_id=_identity().venue_native_id,
        position_side="long",
        venue_flat=False,
        event_time=1700000180.0,
        expected_scope=PositionEpisodeScopeV1("test-account", "INTERNAL_SIMULATED_EXECUTION"),
    )
    evaluated = first.prepare_for_cycle_v1(**args)
    evaluated.pending_exit_identity = "retained-obligation"
    first.commit_evaluated_v1(evaluated, writer_session_id="first")
    evaluated_stale = stale.prepare_for_cycle_v1(**args)
    with pytest.raises(ExitPolicyPersistenceError, match="WRITER_CONFLICT"):
        stale.commit_evaluated_v1(evaluated_stale, writer_session_id="stale")
    assert stale.binding.alpha_blocked
    assert _open(root, mode="recover").binding.pending_exit_identity == "retained-obligation"


@pytest.mark.parametrize("direction", [1, -1])
@pytest.mark.parametrize("episode_lane", ["LANE_1", "LANE_2"])
def test_lane_host_uses_reloaded_time_anchor_for_full_remaining_close(
    tmp_path, monkeypatch, direction, episode_lane
):
    from decimal import Decimal
    from functools import partial
    from unittest.mock import Mock
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
    from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
        provenance_for_bound_v1,
    )
    from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
        governed_c1_candles_payload_from_enter_closes_v1,
    )
    from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
        _produced_g17_producer,
    )
    from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide

    bound = _bound()
    root = Path(lane_state_root_for(topology_state_root_base=tmp_path, lane_id="LANE_1"))
    base = float(PREVIOUS_C1_VENUE_EVENT_TIME) + 60.0
    cursor = _natural_entry(root, direction, event_time_base=base)
    persist_current_productive_sidestate_confirmation_cursor_v1(cursor, store_root=root)
    identity = replace(_identity(direction), lane_id=episode_lane)
    _open(tmp_path / "episode", direction, entry_event_time=base + 120.0, identity=identity)
    context = _open(tmp_path / "episode", direction, mode="recover", identity=identity)
    slot = IsolatedLaneSlotV1(
        lane_id="LANE_1",
        occupancy="OCCUPIED",
        canonical_instrument_id=bound.instrument_id,
        lane_state_root=str(root),
        universe_snapshot_id=bound.universe_snapshot_id,
        ranking_snapshot_id=bound.ranking_snapshot_id,
        ranking_integrity_digest=bound.ranking_integrity_digest,
    )
    ts, mark = base + 63 * 60, 1000.0 + direction * (20.0 + 1.2 * 62)
    closes = tuple(1000.0 + direction * 20.0 * i / 99 for i in range(100))
    entry = Mock(side_effect=AssertionError("Position exit must not call entry sizing"))
    venue_plan = Mock(wraps=consumer.try_bind_current_productive_venue_plan_v1)
    monkeypatch.setattr(consumer, "try_bind_current_productive_venue_plan_v1", venue_plan)
    monkeypatch.setattr(
        consumer, "join_current_productive_enter_live_29p_before_venue_plan_v1", entry
    )
    invoke = partial(
        consumer.invoke_occupied_lane_governed_cycle_n1_consumer_v1,
        {"LANE_1": (slot, bound)},
        origin_main_sha="offline-episode-test",
        cycle_id_prefix=f"episode-exit:{direction}",
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
            enter_closes=closes, last_event_ts_unix=ts
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
        position_episode_bindings={"LANE_1": context},
        position_episode_scope=PositionEpisodeScopeV1(
            "test-account", "INTERNAL_SIMULATED_EXECUTION"
        ),
        live_29p_injected=consumer.CurrentProductiveEnterLive29PInjectedGetV1(
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
        ),
    )
    if episode_lane != "LANE_1":
        before = context.binding.to_canonical_state().to_dict()
        with pytest.raises(ValueError, match="POSITION_EPISODE_CYCLE_IDENTITY_MISMATCH"):
            invoke()
        assert context.binding.to_canonical_state().to_dict() == before
        assert not list(root.rglob("governed_cycle_orchestrator_ledger_v1.json"))
        entry.assert_not_called()
        return
    records = invoke()
    record = records["LANE_1"]
    replay = record.s7_invocation.cycle_result.replay
    assert replay.intermediate.entry_exit_decision.exit_class.value == "time_exit"
    assert record.governed_cycle_result.master_v2_decision == "exit"
    assert record.position_management_quantity_handoff.open_quantity == Decimal("0.4")
    envelope = record.governed_cycle_result.final_order_envelope
    assert envelope is not None and envelope.quantity == "0.4" and envelope.reduce_only
    assert envelope.side == ("sell" if direction == 1 else "buy")
    venue_plan.assert_called_once()
    assert venue_plan.call_args.kwargs["execution_mode"] == "INTERNAL_SIMULATED_EXECUTION"
    assert (
        not record.governed_cycle_result.permit_created
        and record.governed_cycle_result.post_count == 0
    )
    assert context.binding.entry_event_time == base + 120.0
    entry.assert_not_called()


@pytest.mark.parametrize("direction", [1, -1])
def test_entry_time_intervention_changes_actual_exit_at_equal_market_inputs(tmp_path, direction):
    outcomes, digests = {}, {}
    for known in (True, False):
        core = tmp_path / str(known) / "core"
        cursor = _natural_entry(core, direction)
        context = _open(
            tmp_path / str(known) / "episode",
            direction,
            entry_event_time=1700000120.0 if known else None,
        )
        first = _cycle(
            core,
            direction=direction,
            step=3,
            incoming=cursor,
            occupied=True,
            position_episode_binding=context,
        )
        assert first.replay_pass == "true", first.fail_reasons
        final = _cycle(
            core,
            direction=direction,
            step=63,
            incoming=first.outgoing_cursor,
            occupied=True,
            position_episode_binding=context,
        )
        assert final.replay_pass == "true", final.fail_reasons
        outcomes[known] = final.replay.intermediate.entry_exit_decision.exit_class.value
        digests[known] = final.input_digest
    assert outcomes[True] == "time_exit"
    assert outcomes[False] != "time_exit"
    assert digests[True] != digests[False]


@pytest.mark.parametrize(
    "field,value",
    [
        ("entry_price", float("nan")),
        ("entry_event_time", True),
        ("entry_price", -1.0),
        ("entry_source_ref", None),
    ],
)
def test_invalid_entry_source_is_not_persisted(tmp_path, field, value):
    root = tmp_path / "episode"
    with pytest.raises(ValueError):
        _open(root, **{field: value})
    assert not root.exists()


def test_episode_cannot_change_side_or_clear_pending_on_flat(tmp_path):
    context = _open(tmp_path / "episode")
    context.binding.pending_exit_identity = "existing-obligation"
    for side, flat in [("short", False), ("none", True)]:
        with pytest.raises(ValueError, match="IDENTITY_MISMATCH"):
            context.prepare_for_cycle_v1(
                instrument_id=_identity().instrument_id,
                venue_native_id=_identity().venue_native_id,
                position_side=side,
                venue_flat=flat,
                event_time=1700000180.0,
                expected_scope=PositionEpisodeScopeV1(
                    "test-account", "INTERNAL_SIMULATED_EXECUTION"
                ),
            )
    assert context.binding.pending_exit_identity == "existing-obligation"
    assert context.binding.entry_event_time == 1700000120.0


def test_interrupted_episode_publication_blocks_handle_and_restore(tmp_path, monkeypatch):
    from src.ops.exit_policy_producer_binding_v1 import persistence_v1 as store
    from src.ops.exit_policy_producer_binding_v1.constants_v1 import COMMIT_MARKER_FILENAME

    root = tmp_path / "episode"
    context = _open(root)
    evaluated = context.prepare_for_cycle_v1(
        instrument_id=_identity().instrument_id,
        venue_native_id=_identity().venue_native_id,
        position_side="long",
        venue_flat=False,
        event_time=1700000180.0,
        expected_scope=PositionEpisodeScopeV1("test-account", "INTERNAL_SIMULATED_EXECUTION"),
    )
    evaluated.pending_exit_identity = "new-obligation"
    original_replace = store.os.replace

    def interrupt_marker(source, destination):
        if Path(destination) == root / COMMIT_MARKER_FILENAME:
            raise OSError("injected publication interruption")
        return original_replace(source, destination)

    monkeypatch.setattr(store.os, "replace", interrupt_marker)
    with pytest.raises(OSError):
        context.commit_evaluated_v1(evaluated, writer_session_id="interrupted")
    assert context.binding.alpha_blocked
    with pytest.raises(ExitPolicyPersistenceError):
        _open(root, mode="recover")


def test_blocked_cycle_does_not_commit_staged_exit_state(tmp_path):
    core = tmp_path / "core"
    cursor = _natural_entry(core, 1)
    context = _open(tmp_path / "episode")
    before = {p.name: p.read_bytes() for p in (tmp_path / "episode").iterdir() if p.is_file()}
    result = _cycle(core, step=3, incoming=None, occupied=True, position_episode_binding=context)
    assert result.replay_pass == "false"
    assert {
        p.name: p.read_bytes() for p in (tmp_path / "episode").iterdir() if p.is_file()
    } == before


@pytest.mark.parametrize(
    "scope",
    [
        PositionEpisodeScopeV1("another-account", "INTERNAL_SIMULATED_EXECUTION"),
        PositionEpisodeScopeV1("test-account", "LIVE"),
    ],
)
def test_cycle_cannot_apply_exit_state_from_another_account_or_mode(tmp_path, scope):
    core = tmp_path / "core"
    cursor = _natural_entry(core, 1)
    context = _open(tmp_path / "episode")
    before = context.binding.to_canonical_state().to_dict()
    result = _cycle(
        core,
        step=63,
        incoming=cursor,
        occupied=True,
        position_episode_binding=context,
        position_episode_scope=scope,
    )
    assert result.replay_pass == "false"
    assert "POSITION_EPISODE_ACCOUNT_SCOPE_MISMATCH" in result.fail_reasons
    assert context.binding.to_canonical_state().to_dict() == before


@pytest.mark.parametrize("basis", [None, "CURRENT_MARK", "LAST_TRADE"])
def test_current_market_price_cannot_be_declared_as_position_entry(tmp_path, basis):
    with pytest.raises(ValueError, match="ENTRY_PRICE_BASIS_UNPROVEN"):
        _open(tmp_path / "episode", entry_price_basis=basis)
    assert not (tmp_path / "episode").exists()


def test_episode_cannot_silently_replace_existing_time_exit_policy(tmp_path):
    core = tmp_path / "core"
    cursor = _natural_entry(core, 1)
    context = _open(tmp_path / "episode")
    context.binding.time_exit_max_hold_seconds += 1
    before = context.binding.to_canonical_state().to_dict()
    result = _cycle(core, step=63, incoming=cursor, occupied=True, position_episode_binding=context)
    assert result.replay_pass == "false"
    assert "POSITION_EPISODE_TIME_POLICY_MISMATCH" in result.fail_reasons
    assert context.binding.to_canonical_state().to_dict() == before
