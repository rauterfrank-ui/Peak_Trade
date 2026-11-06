"""Crash between Exit and cursor publication, using the actual current core."""

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.exit_policy_producer_binding_v1.current_cursor_recovery_v1 import (
    recover_current_cursor_publication_v1,
)
from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_sidestate_confirmation_cursor_v1 as cursors,
)
from tests.ops.test_position_episode_exit_continuity_v1 import _natural_entry, _open
from tests.ops.test_current_productive_occupied_scope_continuity_v1 import _cycle


def _prepared(tmp_path, direction=1):
    root, episode_root = tmp_path / "core", tmp_path / "episode"
    incoming = _natural_entry(root, direction)
    cursors.persist_current_productive_sidestate_confirmation_cursor_v1(incoming, store_root=root)
    context = _open(episode_root, direction)
    result = _cycle(
        root,
        direction=direction,
        step=63,
        incoming=incoming,
        occupied=True,
        position_episode_binding=context,
    )
    assert result.replay_pass == "true", result.fail_reasons
    assert result.decision_outcome == "exit"
    return root, context, incoming, result


def _recover(context, root):
    return recover_current_cursor_publication_v1(
        episode=context,
        store_root=root,
        expected_scope=context.identity.account_scope,
        writer_session_id="explicit-offline-test-recovery",
    )


@pytest.mark.parametrize("direction", [1, -1])
@pytest.mark.parametrize("interruption", ["before", "after"])
def test_interrupted_pair_blocks_old_cursor_then_recovers_without_second_decision(
    tmp_path, monkeypatch, direction, interruption
):
    root, context, incoming, result = _prepared(tmp_path, direction)
    obligation = context.binding.pending_exit_identity
    sequence = context.binding.commit_sequence
    # Simulate interrupted caller cursor publication after the actual Exit commit.
    original_replace = cursors.os.replace

    def fail_publish(source, destination):
        if Path(destination) == root / cursors.CURSOR_FILENAME:
            if interruption == "after":
                original_replace(source, destination)
            raise OSError("injected cursor replacement interruption")
        return original_replace(source, destination)

    with monkeypatch.context() as patch:
        patch.setattr(cursors.os, "replace", fail_publish)
        with pytest.raises(OSError, match="injected"):
            cursors.persist_current_productive_sidestate_confirmation_cursor_v1(
                result.outgoing_cursor, store_root=root
            )
    expected_disk = incoming if interruption == "before" else result.outgoing_cursor
    assert (
        cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)
        == expected_disk.to_dict()
    )
    context = _open(tmp_path / "episode", direction, mode="recover")
    before = context.binding.to_canonical_state().to_dict()
    blocked = _cycle(
        root,
        direction=direction,
        step=64,
        incoming=incoming,
        occupied=True,
        position_episode_binding=context,
    )
    assert blocked.replay_pass == "false"
    assert "POSITION_EPISODE_CURSOR_RECOVERY_REQUIRED" in blocked.fail_reasons
    assert context.binding.to_canonical_state().to_dict() == before
    # Recovery is a retained write only; any accidental recomputation fails.
    import src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 as core

    with monkeypatch.context() as patch:
        patch.setattr(
            core,
            "run_current_productive_master_v2_runtime_cycle_v1",
            lambda **kw: pytest.fail("replayed decision"),
        )
        assert _recover(context, root)["status"] == (
            "PUBLISHED_RETAINED_CURSOR" if interruption == "before" else "ALREADY_PUBLISHED"
        )
        assert _recover(context, root)["status"] == "ALREADY_PUBLISHED"
    assert context.binding.commit_sequence == sequence
    assert context.binding.pending_exit_identity == obligation
    payload = cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)
    assert payload == result.outgoing_cursor.to_dict()
    after = _cycle(
        root,
        direction=direction,
        step=64,
        incoming=payload,
        occupied=True,
        position_episode_binding=context,
    )
    assert after.replay_pass == "true", after.fail_reasons
    assert context.binding.pending_exit_identity == obligation
    assert context.binding.commit_sequence == sequence + 1


@pytest.mark.parametrize("change", ["missing", "foreign", "corrupt", "root", "scope", "stale"])
def test_recovery_never_overwrites_unproven_or_unrelated_state(tmp_path, change):
    root, context, incoming, result = _prepared(tmp_path)
    target = root / cursors.CURSOR_FILENAME
    if change == "missing":
        target.unlink()
    elif change == "foreign":
        cursors.persist_current_productive_sidestate_confirmation_cursor_v1(
            replace(incoming, now_tick=incoming.now_tick + 10), store_root=root
        )
    elif change == "corrupt":
        target.write_text('{"torn":')
    elif change == "stale":
        stale = _open(tmp_path / "episode", mode="recover")
        next_cycle = _cycle(
            root,
            step=64,
            incoming=result.outgoing_cursor,
            occupied=True,
            position_episode_binding=context,
        )
        assert next_cycle.replay_pass == "true"
        context = stale
    before = target.read_bytes() if target.exists() else None
    with pytest.raises((ValueError, cursors.CurrentProductiveCursorError)):
        recover_current_cursor_publication_v1(
            episode=context,
            store_root=(tmp_path / "foreign-root") if change == "root" else root,
            expected_scope=replace(context.identity.account_scope, account_identity="foreign")
            if change == "scope"
            else context.identity.account_scope,
            writer_session_id="refused-recovery",
        )
    assert (target.read_bytes() if target.exists() else None) == before


def test_cursor_owner_compare_and_swap_rejects_stale_publication(tmp_path):
    root, context, incoming, result = _prepared(tmp_path)
    prior = cursors.current_productive_cursor_digest_v1(incoming)
    cursors.persist_current_productive_sidestate_confirmation_cursor_v1(
        result.outgoing_cursor, store_root=root, expected_prior_digest=prior
    )
    before = (root / cursors.CURSOR_FILENAME).read_bytes()
    with pytest.raises(cursors.CurrentProductiveCursorError, match="CURSOR_PUBLICATION_CONFLICT"):
        cursors.persist_current_productive_sidestate_confirmation_cursor_v1(
            incoming, store_root=root, expected_prior_digest=prior
        )
    assert (root / cursors.CURSOR_FILENAME).read_bytes() == before


def test_cursor_owner_excludes_simultaneous_writer(tmp_path):
    import fcntl

    root, context, incoming, result = _prepared(tmp_path)
    with (root / (cursors.CURSOR_FILENAME + ".lock")).open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(cursors.CurrentProductiveCursorError, match="CURSOR_WRITER_CONFLICT"):
            _recover(context, root)
    assert _recover(context, root)["status"] == "PUBLISHED_RETAINED_CURSOR"


def test_n1_rejects_mixed_pair_before_governed_authorization(tmp_path, monkeypatch):
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
        invoke_join_v1 as consumer,
    )
    from tests.ops.test_position_episode_exit_continuity_v1 import (
        test_lane_host_uses_reloaded_time_anchor_for_full_remaining_close,
    )

    original_invoke = consumer.invoke_occupied_lane_governed_cycle_n1_consumer_v1

    def check_preflight(pairs, **kwargs):
        root = Path(pairs["LANE_1"][0].lane_state_root)
        path = root / cursors.CURSOR_FILENAME
        incoming_bytes = path.read_bytes()
        records = original_invoke(pairs, **kwargs)
        outgoing_bytes = path.read_bytes()
        path.write_bytes(incoming_bytes)  # simulate retained old publication
        ledgers = {
            p: p.read_bytes() for p in root.rglob("governed_cycle_orchestrator_ledger_v1.json")
        }
        assert ledgers
        before = (
            kwargs["position_episode_bindings"]["LANE_1"].binding.to_canonical_state().to_dict()
        )
        with pytest.raises(ValueError, match="POSITION_EPISODE_CURSOR_RECOVERY_REQUIRED"):
            original_invoke(pairs, **kwargs)
        assert {p: p.read_bytes() for p in ledgers} == ledgers
        assert (
            kwargs["position_episode_bindings"]["LANE_1"].binding.to_canonical_state().to_dict()
            == before
        )
        path.write_bytes(outgoing_bytes)
        return records

    monkeypatch.setattr(
        consumer, "invoke_occupied_lane_governed_cycle_n1_consumer_v1", check_preflight
    )
    test_lane_host_uses_reloaded_time_anchor_for_full_remaining_close(
        tmp_path, monkeypatch, 1, "LANE_1"
    )


@pytest.mark.parametrize(
    "field", ["identity", "outgoing_digest", "outgoing_payload", "prior_exit_sequence"]
)
def test_malformed_retained_publication_blocks_cycle(tmp_path, field):
    root, context, incoming, result = _prepared(tmp_path)
    record = context.binding.current_cursor_publication
    if field == "outgoing_payload":
        record[field] = {"invalid": "cursor"}
        record["outgoing_digest"] = cursors.current_productive_cursor_digest_v1(record[field])
    elif field == "prior_exit_sequence":
        record[field] = True
    else:
        record[field] = "different"
    before = context.binding.to_canonical_state().to_dict()
    blocked = _cycle(
        root,
        step=64,
        incoming=result.outgoing_cursor,
        occupied=True,
        position_episode_binding=context,
    )
    assert blocked.replay_pass == "false"
    assert context.binding.to_canonical_state().to_dict() == before


def test_legacy_state_shape_and_detached_publication_projection(tmp_path):
    context = _open(tmp_path / "unused")
    assert "current_cursor_publication" not in context.binding.to_canonical_state().to_dict()
    root, context, incoming, result = _prepared(tmp_path / "paired")
    projection = context.binding.to_canonical_state().to_dict()
    projection["current_cursor_publication"]["outgoing_payload"]["now_tick"] = 9999
    assert (
        context.binding.current_cursor_publication["outgoing_payload"]
        == result.outgoing_cursor.to_dict()
    )
