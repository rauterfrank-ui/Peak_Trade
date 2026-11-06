"""Same-episode average/quantity progress, actual Exit effects and restart."""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.exit_policy_producer_binding_v1.simulated_accounting_progress_v1 import (
    advance_position_episode_from_simulated_accounting_v1,
    verify_simulated_accounting_progress_v1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    create_position_episode_from_simulated_accounting_v1,
    recover_position_episode_from_simulated_accounting_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (
    build_simulated_fill_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
    persist_current_productive_sidestate_confirmation_cursor_v1,
)
from tests.ops.test_simulated_accounting_entry_source_v1 import _history, _args
from tests.ops.test_position_episode_exit_continuity_v1 import _natural_entry
from tests.ops.test_current_productive_occupied_scope_continuity_v1 import _cycle


def _setup(tmp_path, direction=1, time=1700000120.0):
    identity, session, fills = _history(direction, time=time)
    args = _args(tmp_path, identity)
    context = create_position_episode_from_simulated_accounting_v1(
        **args, session=session, fills=fills
    )
    cursor = _natural_entry(tmp_path / "core", direction)
    persist_current_productive_sidestate_confirmation_cursor_v1(
        cursor, store_root=tmp_path / "core"
    )
    return context, session, fills, cursor


def _append(session, fills, direction=1, *, reduce=False, time=1700000300.0, mark=None):
    fill = build_simulated_fill_v1(
        fill_id="later:" + str(len(fills)),
        instrument_id=session.contract.symbol,
        side=("BUY" if direction == 1 else "SELL")
        if not reduce
        else ("SELL" if direction == 1 else "BUY"),
        quantity="0.4",
        mark_price=mark or ("1050" if direction == 1 else "1000"),
        contract=session.contract,
        reduce_only=reduce,
        event_time_unix=time,
    )
    session.apply_fill(fill)
    return (*fills, fill)


def _advance(root, context, session, fills):
    return advance_position_episode_from_simulated_accounting_v1(
        episode=context,
        session=session,
        fills=fills,
        source_archive_root=root / "sources",
        cursor_store_root=root / "core",
        expected_scope=context.identity.account_scope,
        writer_session_id="offline-progress-test",
    )


def _recover(root, context):
    return recover_position_episode_from_simulated_accounting_v1(
        identity=context.identity,
        source_path=Path(context.entry_source_ref.split(":", 2)[2]),
        state_root=root / "episode",
        repository_sha=context.binding.repository_sha,
        config_digest=context.binding.config_digest,
        writer_session_id="offline-progress-reload",
    )


@pytest.mark.parametrize("direction", [1, -1])
def test_increase_and_partial_reduce_preserve_first_open_and_original_sources(tmp_path, direction):
    context, session, fills, cursor = _setup(tmp_path, direction)
    original_source = Path(context.entry_source_ref.split(":", 2)[2])
    original_bytes = original_source.read_bytes()
    cursor_bytes = (tmp_path / "core" / CURSOR_FILENAME).read_bytes()
    original_time, original_id = context.binding.entry_event_time, context.identity.episode_id
    average_before = context.binding.entry_price
    fills = _append(session, fills, direction)
    assert _advance(tmp_path, context, session, fills)["status"] == "APPLIED"
    assert context.binding.entry_price == float(session.position.entry_price) != average_before
    assert (
        context.binding.entry_event_time == original_time
        and context.identity.episode_id == original_id
    )
    assert verify_simulated_accounting_progress_v1(context)["quantity"] == Decimal("0.8")
    assert context.input_binding_v1()["entry_source_ref"] == context.entry_source_ref
    assert context.input_binding_v1()["current_entry_source_ref"] != context.entry_source_ref
    before_sequence = context.binding.commit_sequence
    assert _advance(tmp_path, context, session, fills)["status"] == "ALREADY_APPLIED"
    assert context.binding.commit_sequence == before_sequence
    fills = _append(session, fills, direction, reduce=True, time=1700000360.0)
    assert _advance(tmp_path, context, session, fills)["status"] == "APPLIED"
    assert verify_simulated_accounting_progress_v1(context)["quantity"] == Decimal("0.4")
    assert (
        context.input_binding_v1()["current_entry_source_ref"]
        == context.binding.simulated_accounting_progress["current_source_ref"]
    )
    assert (tmp_path / "core" / CURSOR_FILENAME).read_bytes() == cursor_bytes
    assert original_source.read_bytes() == original_bytes
    restored = _recover(tmp_path, context)
    assert (
        restored.binding.to_canonical_state().to_dict()
        == context.binding.to_canonical_state().to_dict()
    )
    after = _cycle(
        tmp_path / "core",
        direction=direction,
        step=63,
        incoming=cursor,
        occupied=True,
        position_episode_binding=restored,
    )
    assert after.replay_pass == "true", after.fail_reasons
    assert after.replay.intermediate.entry_exit_decision.exit_class.value == "time_exit"


@pytest.mark.parametrize("direction", [1, -1])
def test_actual_profit_exit_consumes_updated_average_at_equal_market_inputs(tmp_path, direction):
    outcomes = {}
    for updated in (False, True):
        root = tmp_path / str(updated)
        context, session, fills, cursor = _setup(root, direction, time=None)
        if updated:
            fills = _append(session, fills, direction, mark="1200" if direction == 1 else "800")
            _advance(root, context, session, fills)
        result = _cycle(
            root / "core",
            direction=direction,
            step=177,
            incoming=cursor,
            occupied=True,
            position_episode_binding=context,
        )
        assert result.replay_pass == "true", result.fail_reasons
        assert context.binding.entry_event_time is None
        outcomes[updated] = context.binding.last_bundle["profit_protection"]["triggered"]
        if not updated:
            assert (
                result.replay.intermediate.entry_exit_decision.exit_class.value
                == "profit_protection_exit"
            )
    assert outcomes == {False: True, True: False}


@pytest.mark.parametrize("direction", [1, -1])
def test_pending_exit_survives_average_update_and_remains_actionable(tmp_path, direction):
    context, session, fills, cursor = _setup(tmp_path, direction)
    first = _cycle(
        tmp_path / "core",
        direction=direction,
        step=63,
        incoming=cursor,
        occupied=True,
        position_episode_binding=context,
    )
    assert first.replay_pass == "true"
    obligation = context.binding.pending_exit_identity
    assert obligation
    persist_current_productive_sidestate_confirmation_cursor_v1(
        first.outgoing_cursor, store_root=tmp_path / "core"
    )
    fills = _append(session, fills, direction, time=1700003790.0)
    _advance(tmp_path, context, session, fills)
    assert context.binding.pending_exit_identity == obligation
    restored = _recover(tmp_path, context)
    second = _cycle(
        tmp_path / "core",
        direction=direction,
        step=64,
        incoming=first.outgoing_cursor,
        occupied=True,
        position_episode_binding=restored,
    )
    assert second.replay_pass == "true", second.fail_reasons
    assert second.decision_outcome == "exit"
    assert restored.binding.pending_exit_identity == obligation


def test_progress_from_future_fill_is_not_consumed_by_earlier_observation(tmp_path):
    context, session, fills, cursor = _setup(tmp_path)
    fills = _append(session, fills, time=1700004000.0)
    _advance(tmp_path, context, session, fills)
    before = context.binding.to_canonical_state().to_dict()
    blocked = _cycle(
        tmp_path / "core", step=63, incoming=cursor, occupied=True, position_episode_binding=context
    )
    assert blocked.replay_pass == "false"
    assert "SIMULATED_ENTRY_PROGRESS_AFTER_OBSERVATION" in blocked.fail_reasons
    assert context.binding.to_canonical_state().to_dict() == before


def test_existing_adverse_priority_does_not_erase_pending_time_exit(tmp_path):
    context, session, fills, cursor = _setup(tmp_path)
    first = _cycle(
        tmp_path / "core", step=63, incoming=cursor, occupied=True, position_episode_binding=context
    )
    assert first.decision_outcome == "exit"
    obligation = context.binding.pending_exit_identity
    persist_current_productive_sidestate_confirmation_cursor_v1(
        first.outgoing_cursor, store_root=tmp_path / "core"
    )
    fills = _append(session, fills, time=1700003790.0, mark="1200")
    _advance(tmp_path, context, session, fills)
    second = _cycle(
        tmp_path / "core",
        step=64,
        incoming=first.outgoing_cursor,
        occupied=True,
        position_episode_binding=context,
    )
    assert second.replay_pass == "true", second.fail_reasons
    assert context.binding.pending_exit_identity == obligation
    assert context.binding.pending_exit_class == "time_exit"
    assert context.binding.last_bundle["time_exit"]["triggered"]
    assert second.replay.intermediate.entry_exit_decision.exit_class.value == "adverse_scope_exit"
    assert second.decision_outcome == "reduce"


@pytest.mark.parametrize("change", ["unknown_new_time", "flat", "rewrite", "stale"])
def test_unproven_progress_cannot_overwrite_existing_state(tmp_path, change):
    context, session, fills, cursor = _setup(tmp_path)
    if change == "unknown_new_time":
        fills = _append(session, fills, time=None)
        reason = "NEW_FILL_TIME_REQUIRED"
    elif change == "flat":
        fills = _append(session, fills, reduce=True)
        reason = "OPEN_EPISODE_REQUIRED"
    elif change == "rewrite":
        altered = build_simulated_fill_v1(
            fill_id=fills[1].fill_id,
            instrument_id=session.contract.symbol,
            side="BUY",
            quantity="0.3",
            mark_price="1100",
            contract=session.contract,
            event_time_unix=fills[1].event_time_unix,
        )
        fills = (fills[0], altered, fills[2])
        replay = ProductiveFuturesAccountingSessionV1(contract=session.contract)
        for f in fills:
            replay.apply_fill(f)
        session = replay
        fills = _append(session, fills)
        reason = "HISTORY_REWRITE"
    else:
        stale = _recover(tmp_path, context)
        fills = _append(session, fills)
        _advance(tmp_path, context, session, fills)
        context = stale
        reason = "STALE_HANDLE"
    state_paths = list((tmp_path / "episode").glob("*.json"))
    before = {p: p.read_bytes() for p in state_paths}
    with pytest.raises(ValueError, match=reason):
        _advance(tmp_path, context, session, fills)
    assert {p: p.read_bytes() for p in before} == before


@pytest.mark.parametrize("change", ["contract", "initial_equity", "writer"])
def test_fill_prefix_does_not_allow_accounting_domain_or_unit_change(tmp_path, change):
    context, session, fills, cursor = _setup(tmp_path)
    replay = ProductiveFuturesAccountingSessionV1(
        contract=replace(session.contract, contract_size=Decimal("2"))
        if change == "contract"
        else session.contract,
        initial_equity=Decimal("200000") if change == "initial_equity" else session.initial_equity,
        writer_identity="another-writer" if change == "writer" else session.writer_identity,
    )
    for fill in fills:
        replay.apply_fill(fill)
    fills = _append(replay, fills)
    before = context.binding.to_canonical_state().to_dict()
    with pytest.raises(ValueError, match="ACCOUNTING_DOMAIN_CHANGED"):
        _advance(tmp_path, context, replay, fills)
    assert context.binding.to_canonical_state().to_dict() == before


def test_decision_commit_cannot_use_new_update_path_to_change_entry_anchor(tmp_path):
    context, session, fills, cursor = _setup(tmp_path)
    evaluated = deepcopy(context.binding)
    evaluated.entry_price += 1
    with pytest.raises(ValueError, match="IMMUTABLE_CONTEXT_MISMATCH:entry_price"):
        context.commit_evaluated_v1(evaluated, writer_session_id="invalid-decision-change")


def test_session_update_preserves_manifest_allowance_and_recovers_new_source(tmp_path):
    from tests.ops.test_bounded_offline_episode_session_v1 import _setup as session_setup, _session

    manifest, pairs = session_setup(tmp_path)
    identity, session, fills = _history()
    fills = _append(session, fills)
    root = tmp_path / "session"
    with _session(manifest, root) as opened:
        before = opened.state
        result = opened.advance_accounting_episode_v1(
            lane_id="LANE_1", accounting_session=session, fills=fills
        )
        assert result["status"] == "APPLIED"
        assert opened.state == before
    with _session(manifest, root, "recover") as restored:
        assert restored.state["attempts_used"] == 0
        assert (
            restored.advance_accounting_episode_v1(
                lane_id="LANE_1", accounting_session=session, fills=fills
            )["status"]
            == "ALREADY_APPLIED"
        )


@pytest.mark.parametrize("direction", [1, -1])
def test_updated_source_quantity_is_checked_before_actual_n1_full_remaining_close(
    tmp_path, monkeypatch, direction
):
    from tests.ops import test_position_episode_exit_continuity_v1 as scenario
    from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
        lane_state_root_for,
    )
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
        invoke_join_v1 as consumer,
    )
    from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
        bind_simulated_accounting_episode_identity_v1,
    )

    saved = {}
    real_invoke = consumer.invoke_occupied_lane_governed_cycle_n1_consumer_v1

    def source_open(root, direction=1, mode="create", **overrides):
        if mode == "create":
            _, accounting, fills = _history(direction, time=overrides["entry_event_time"])
            identity = bind_simulated_accounting_episode_identity_v1(
                identity=overrides["identity"], opening_fill=fills[0]
            )
            args = _args(root.parent / "accounting", identity)
            args["state_root"] = root
            context = create_position_episode_from_simulated_accounting_v1(
                **args, session=accounting, fills=fills
            )
            source = Path(context.entry_source_ref.split(":", 2)[2])
            cursor_root = Path(
                lane_state_root_for(topology_state_root_base=tmp_path, lane_id="LANE_1")
            )
            for offset, reduce in ((180, False), (240, True)):
                fills = _append(
                    accounting,
                    fills,
                    direction,
                    reduce=reduce,
                    time=overrides["entry_event_time"] + offset,
                )
                advance_position_episode_from_simulated_accounting_v1(
                    episode=context,
                    session=accounting,
                    fills=fills,
                    source_archive_root=args["source_archive_root"],
                    cursor_store_root=cursor_root,
                    expected_scope=identity.account_scope,
                    writer_session_id="n1-source-progress",
                )
            args.pop("source_archive_root")
            saved[root] = (args, source)
            return context
        args, source = saved[root]
        return recover_position_episode_from_simulated_accounting_v1(**args, source_path=source)

    def quantity_control(pairs, **kwargs):
        context = kwargs["position_episode_bindings"]["LANE_1"]
        before = context.binding.to_canonical_state().to_dict()
        wrong = dict(kwargs)
        wrong["occupancy_payloads"] = deepcopy(kwargs["occupancy_payloads"])
        wrong["occupancy_payloads"]["POSITIONS"]["data"][0]["pos"] = "0.8"
        with pytest.raises(ValueError, match="PROGRESS_POSITION_QUANTITY_MISMATCH"):
            real_invoke(pairs, **wrong)
        root = Path(pairs["LANE_1"][0].lane_state_root)
        assert not list(root.rglob("governed_cycle_orchestrator_ledger_v1.json"))
        assert context.binding.to_canonical_state().to_dict() == before
        return real_invoke(pairs, **kwargs)

    monkeypatch.setattr(scenario, "_open", source_open)
    monkeypatch.setattr(
        consumer, "invoke_occupied_lane_governed_cycle_n1_consumer_v1", quantity_control
    )
    scenario.test_lane_host_uses_reloaded_time_anchor_for_full_remaining_close(
        tmp_path, monkeypatch, direction, "LANE_1"
    )


def test_racing_writer_cannot_be_overwritten_by_progress_commit(tmp_path, monkeypatch):
    from src.ops.exit_policy_producer_binding_v1 import simulated_accounting_progress_v1 as progress
    from src.ops.exit_policy_producer_binding_v1.persistence_v1 import ExitPolicyPersistenceError

    context, session, fills, cursor = _setup(tmp_path)
    other = _recover(tmp_path, context)
    fills = _append(session, fills)
    archive = progress._archive_verified_source_v1

    def race(**kwargs):
        result = archive(**kwargs)
        staged = deepcopy(other.binding)
        staged.pending_exit_identity = "concurrent-owner-obligation"
        staged.pending_exit_class = "time_exit"
        other.commit_evaluated_v1(staged, writer_session_id="concurrent-writer")
        return result

    monkeypatch.setattr(progress, "_archive_verified_source_v1", race)
    with pytest.raises(ExitPolicyPersistenceError, match="WRITER_CONFLICT"):
        _advance(tmp_path, context, session, fills)
    assert context.binding.alpha_blocked
    restored = _recover(tmp_path, other)
    assert restored.binding.pending_exit_identity == "concurrent-owner-obligation"
    assert restored.binding.simulated_accounting_progress is None


def test_partial_progress_publication_blocks_reload_without_repair(tmp_path, monkeypatch):
    from src.ops.exit_policy_producer_binding_v1 import persistence_v1 as persistence
    from src.ops.exit_policy_producer_binding_v1.constants_v1 import COMMIT_MARKER_FILENAME

    context, session, fills, cursor = _setup(tmp_path)
    fills = _append(session, fills)
    original = persistence.os.replace

    def interrupt(source, target):
        if Path(target) == tmp_path / "episode" / COMMIT_MARKER_FILENAME:
            raise OSError("injected progress marker interruption")
        return original(source, target)

    monkeypatch.setattr(persistence.os, "replace", interrupt)
    with pytest.raises(OSError, match="injected"):
        _advance(tmp_path, context, session, fills)
    assert context.binding.alpha_blocked
    with pytest.raises(persistence.ExitPolicyPersistenceError):
        _recover(tmp_path, context)


def test_interrupted_session_source_update_does_not_reset_attempt_allowance(tmp_path, monkeypatch):
    from tests.ops.test_bounded_offline_episode_session_v1 import _setup as session_setup, _session
    from src.ops.exit_policy_producer_binding_v1 import simulated_accounting_progress_v1 as progress

    manifest, pairs = session_setup(tmp_path)
    _, session, fills = _history()
    root = tmp_path / "session"

    def interrupt(**kwargs):
        raise OSError("injected after source-update checkpoint")

    monkeypatch.setattr(
        progress, "advance_position_episode_from_simulated_accounting_v1", interrupt
    )
    with _session(manifest, root) as opened:
        with pytest.raises(OSError, match="injected"):
            opened.advance_accounting_episode_v1(
                lane_id="LANE_1", accounting_session=session, fills=fills
            )
        assert opened.state["attempts_used"] == 0
        assert opened.state["status"] == "RECOVERY_REQUIRED"
    with pytest.raises(ValueError, match="REQUIRES_REVIEW"):
        with _session(manifest, root, "recover"):
            pytest.fail("resumed unproven update")
