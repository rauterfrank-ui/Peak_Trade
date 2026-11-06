"""Explicit flat is a local episode boundary, not an order/capital acknowledgement."""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from src.ops.exit_policy_producer_binding_v1.simulated_accounting_close_v1 import (
    seal_simulated_accounting_episode_flat_v1,
    inspect_sealed_simulated_episode_v1,
    create_successor_after_sealed_simulated_episode_v1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    bind_simulated_accounting_episode_identity_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (
    build_simulated_fill_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
    persist_current_productive_sidestate_confirmation_cursor_v1,
)
from tests.ops.test_simulated_accounting_episode_progress_v1 import _setup, _recover
from tests.ops.test_position_episode_exit_continuity_v1 import _bound, _natural_entry
from tests.ops.test_current_productive_occupied_scope_continuity_v1 import _cycle


def _close(accounting, fills, direction=1):
    fill = build_simulated_fill_v1(
        fill_id="actual-simulated-full-close",
        instrument_id=accounting.contract.symbol,
        side="SELL" if direction == 1 else "BUY",
        quantity="0.4",
        mark_price="1050",
        contract=accounting.contract,
        reduce_only=True,
        event_time_unix=1700004000.0,
    )
    accounting.apply_fill(fill)
    return (*fills, fill)


def _observation(identity):
    return dict(
        occupancy_payloads={
            "POSITIONS": {
                "code": "0",
                "data": [{"instId": identity.venue_native_id, "pos": "0", "posSide": "net"}],
            },
            "PENDING": {"code": "0", "data": []},
        },
        observed_portfolio=PortfolioTruthSnapshotV1(
            positions=(
                PositionTruthV1.from_signed(
                    instrument_id=identity.instrument_id,
                    signed_quantity="0",
                    source_id="offline-explicit-flat",
                ),
            ),
            source_id="offline-explicit-flat",
            event_time_unix=1700004001.0,
            wall_time_unix=1700004001.0,
            max_age_seconds=5.0,
        ),
        observed_unix=1700004002.0,
    )


def _seal(root, context, accounting, fills, **overrides):
    kwargs = _observation(context.identity)
    kwargs.update(overrides)
    return seal_simulated_accounting_episode_flat_v1(
        episode=context,
        accounting_session=accounting,
        fills=fills,
        bound=_bound(),
        expected_scope=context.identity.account_scope,
        source_archive_root=root / "sources",
        cursor_store_root=root / "core",
        writer_session_id="offline-flat-seal",
        **kwargs,
    )


def _inspect(root, context):
    return inspect_sealed_simulated_episode_v1(
        identity=context.identity,
        state_root=root / "episode",
        repository_sha=context.binding.repository_sha,
        config_digest=context.binding.config_digest,
        expected_initial_source_ref=context.entry_source_ref,
    )


@pytest.mark.parametrize("direction", [1, -1])
def test_full_close_seals_episode_retains_obligation_evidence_and_leaves_ledgers(
    tmp_path, direction
):
    context, accounting, fills, cursor = _setup(tmp_path, direction)
    first = _cycle(
        tmp_path / "core",
        direction=direction,
        step=63,
        incoming=cursor,
        occupied=True,
        position_episode_binding=context,
    )
    assert first.replay_pass == "true"
    pending = context.binding.pending_exit_identity
    assert pending
    persist_current_productive_sidestate_confirmation_cursor_v1(
        first.outgoing_cursor, store_root=tmp_path / "core"
    )
    cursor_bytes = (tmp_path / "core" / CURSOR_FILENAME).read_bytes()
    old_files = {
        p.name: p.read_bytes()
        for p in (tmp_path / "episode").iterdir()
        if p.is_file() and not p.name.endswith(".lock")
    }
    # Explicit retained unrelated obligation material must not be purged at flat.
    ledger = tmp_path / "core" / "retained_outcome_obligation.jsonl"
    ledger.write_text('{"pending":"must survive flat"}\n')
    fills = _close(accounting, fills, direction)
    result = _seal(tmp_path, context, accounting, fills)
    assert result["status"] == "SEALED"
    assert not context.binding.has_open_position and not context.binding.pending_exit_identity
    assert context.binding.entry_event_time is None
    assert (tmp_path / "core" / CURSOR_FILENAME).read_bytes() == cursor_bytes
    assert ledger.read_text() == '{"pending":"must survive flat"}\n'
    inspected = _inspect(tmp_path, context)
    assert inspected["closure_ref"] == result["closure_ref"]
    raw = json.loads(Path(result["closure_ref"].split(":", 2)[2]).read_text())["payload"]
    assert raw["prior_exit_state"]["pending_exit_identity"] == pending
    import base64

    for name, data in old_files.items():
        assert base64.b64decode(raw["prior_owner_files"][name]["base64"]) == data
    with pytest.raises(ValueError, match="RESTORE_POSITION_MISMATCH"):
        _recover(tmp_path, context)


@pytest.mark.parametrize(
    "change",
    [
        "empty",
        "missing_pending",
        "pending",
        "nonzero",
        "duplicate_zero",
        "portfolio_absent",
        "portfolio_open",
        "stale",
        "future",
        "close_unapplied",
    ],
)
def test_no_implicit_flat_or_unproven_closure_can_change_exit_state(tmp_path, change):
    context, accounting, fills, cursor = _setup(tmp_path)
    if change != "close_unapplied":
        fills = _close(accounting, fills)
    kwargs = _observation(context.identity)
    if change == "empty":
        kwargs["occupancy_payloads"]["POSITIONS"]["data"] = []
    elif change == "missing_pending":
        kwargs["occupancy_payloads"].pop("PENDING")
    elif change == "pending":
        kwargs["occupancy_payloads"]["PENDING"]["data"] = [{"ordId": "still-pending"}]
    elif change == "nonzero":
        kwargs["occupancy_payloads"]["POSITIONS"]["data"][0]["pos"] = "0.1"
    elif change == "duplicate_zero":
        kwargs["occupancy_payloads"]["POSITIONS"]["data"] *= 2
    elif change == "portfolio_absent":
        kwargs["observed_portfolio"] = replace(kwargs["observed_portfolio"], positions=())
    elif change == "portfolio_open":
        kwargs["observed_portfolio"] = replace(
            kwargs["observed_portfolio"],
            positions=(
                PositionTruthV1.from_signed(
                    instrument_id=context.identity.instrument_id, signed_quantity="0.1"
                ),
            ),
        )
    elif change == "stale":
        kwargs["observed_portfolio"] = replace(kwargs["observed_portfolio"], stale=True)
    elif change == "future":
        kwargs["observed_unix"] = 1700003999.0
    before = context.binding.to_canonical_state().to_dict()
    with pytest.raises(ValueError):
        _seal(tmp_path, context, accounting, fills, **kwargs)
    assert context.binding.to_canonical_state().to_dict() == before
    assert _recover(tmp_path, context).binding.to_canonical_state().to_dict() == before


@pytest.mark.parametrize("direction", [1, -1])
def test_successor_uses_new_identity_and_roots_without_inheriting_old_scope(tmp_path, direction):
    context, accounting, fills, cursor = _setup(tmp_path, direction)
    fills = _close(accounting, fills, direction)
    _seal(tmp_path, context, accounting, fills)
    old_files = {
        p: p.read_bytes()
        for directory in (tmp_path / "episode", tmp_path / "core")
        for p in directory.rglob("*.json")
    }
    opening = build_simulated_fill_v1(
        fill_id="new-episode-open",
        instrument_id=accounting.contract.symbol,
        side="SELL" if direction == 1 else "BUY",
        quantity="0.2",
        mark_price="1000",
        contract=accounting.contract,
        event_time_unix=1700004100.0,
    )
    accounting.apply_fill(opening)
    fills = (*fills, opening)
    identity = bind_simulated_accounting_episode_identity_v1(
        identity=replace(context.identity, position_side="short" if direction == 1 else "long"),
        opening_fill=opening,
    )
    new = create_successor_after_sealed_simulated_episode_v1(
        prior_identity=context.identity,
        prior_state_root=tmp_path / "episode",
        prior_repository_sha=context.binding.repository_sha,
        prior_config_digest=context.binding.config_digest,
        prior_initial_source_ref=context.entry_source_ref,
        identity=identity,
        accounting_session=accounting,
        fills=fills,
        source_archive_root=tmp_path / "new" / "sources",
        state_root=tmp_path / "new" / "episode",
        repository_sha=context.binding.repository_sha,
        config_digest=context.binding.config_digest,
        writer_session_id="explicit-next-episode",
    )
    assert new.identity.episode_id != context.identity.episode_id
    assert (
        new.binding.entry_event_time == opening.event_time_unix
        and not new.binding.pending_exit_identity
    )
    new_cursor = _natural_entry(tmp_path / "new" / "core", -direction, event_time_base=1700003980.0)
    # Existing Scope labels are locally deterministic, not global episode IDs.
    assert new_cursor.existing_scope.scope_id == cursor.existing_scope.scope_id
    assert new_cursor.existing_scope.semantic_digest != cursor.existing_scope.semantic_digest
    assert new_cursor.side_state != cursor.side_state
    result = _cycle(
        tmp_path / "new" / "core",
        direction=-direction,
        step=3,
        incoming=new_cursor,
        occupied=True,
        event_time_base=1700003980.0,
        position_episode_binding=new,
    )
    assert result.replay_pass == "true", result.fail_reasons
    blocked = _cycle(
        tmp_path / "core",
        direction=direction,
        step=64,
        incoming=cursor,
        occupied=True,
        position_episode_binding=context,
    )
    assert blocked.replay_pass == "false"
    assert "POSITION_EPISODE_OPEN_POSITION_MISMATCH" in blocked.fail_reasons
    assert {p: p.read_bytes() for p in old_files} == old_files


def test_session_sealed_status_can_be_inspected_but_never_reenters_runtime(tmp_path):
    from tests.ops.test_bounded_offline_episode_session_v1 import _setup as session_setup, _session
    from tests.ops.test_simulated_accounting_entry_source_v1 import _history

    manifest, pairs = session_setup(tmp_path)
    identity, accounting, fills = _history()
    fills = _close(accounting, fills)
    root = tmp_path / "session"
    with _session(manifest, root) as opened:
        before = opened.state
        result = opened.seal_flat_episode_v1(
            pairs, accounting_session=accounting, fills=fills, **_observation(identity)
        )
        assert result["status"] == "SEALED"
        assert opened.state["attempts_used"] == before["attempts_used"]
        with pytest.raises(ValueError, match="TERMINAL_SEALED"):
            opened.run_occupied_cycle_v1(pairs)
    with _session(manifest, root, "recover") as reopened:
        assert reopened.state["status"] == "SEALED"
        with pytest.raises(ValueError, match="TERMINAL_SEALED"):
            reopened.advance_accounting_episode_v1(
                lane_id="LANE_1", accounting_session=accounting, fills=fills
            )


@pytest.mark.parametrize("direction", [1, -1])
def test_actual_n1_close_envelope_feeds_original_simulation_accounting_then_seal(
    tmp_path, monkeypatch, direction
):
    from tests.ops import test_simulated_accounting_entry_source_v1 as scenario
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
        invoke_join_v1 as consumer,
    )
    from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
        ProductiveFuturesAccountingSessionV1,
    )
    from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import (
        SimulatedFillInputV1,
    )
    from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
        recover_position_episode_from_simulated_accounting_v1,
        _load_source,
    )

    original = consumer.invoke_occupied_lane_governed_cycle_n1_consumer_v1
    completed = []

    def close_from_envelope(pairs, **kwargs):
        records = original(pairs, **kwargs)
        record = records["LANE_1"]
        envelope = record.governed_cycle_result.final_order_envelope
        prior = kwargs["position_episode_bindings"]["LANE_1"]
        source_path = Path(prior.entry_source_ref.split(":", 2)[2])
        _, _, payload = _load_source(source_path, prior.identity, include_payload=True)
        accounting = ProductiveFuturesAccountingSessionV1.from_durable_dict(
            payload["accounting_checkpoint"]
        )
        numeric = {"quantity", "mark_price", "fill_price", "fee", "slippage_cost", "notional"}
        fills = tuple(
            SimulatedFillInputV1(**{k: Decimal(v) if k in numeric else v for k, v in row.items()})
            for row in payload["fills"]
        )
        fill_time = kwargs["observed_unix"] + 1
        closing = build_simulated_fill_v1(
            fill_id="simulated-envelope:" + envelope.envelope_id,
            instrument_id=accounting.contract.symbol,
            side=envelope.side.upper(),
            quantity=Decimal(envelope.quantity),
            mark_price=str(kwargs["mark_px"]),
            contract=accounting.contract,
            reduce_only=envelope.reduce_only,
            event_time_unix=fill_time,
        )
        accounting.apply_fill(closing)
        assert accounting.position is None
        episode = recover_position_episode_from_simulated_accounting_v1(
            identity=prior.identity,
            source_path=source_path,
            state_root=Path(prior.binding.state_root),
            repository_sha=prior.binding.repository_sha,
            config_digest=prior.binding.config_digest,
            writer_session_id="post-simulated-close",
        )
        observation = _observation(episode.identity)
        observation["observed_portfolio"] = replace(
            observation["observed_portfolio"],
            event_time_unix=fill_time + 1,
            wall_time_unix=fill_time + 1,
        )
        observation["observed_unix"] = fill_time + 2
        sealed = seal_simulated_accounting_episode_flat_v1(
            episode=episode,
            accounting_session=accounting,
            fills=(*fills, closing),
            bound=pairs["LANE_1"][1],
            expected_scope=episode.identity.account_scope,
            source_archive_root=source_path.parent,
            cursor_store_root=Path(pairs["LANE_1"][0].lane_state_root),
            writer_session_id="simulated-close-from-envelope",
            **observation,
        )
        assert sealed["status"] == "SEALED" and not episode.binding.has_open_position
        assert (
            record.governed_cycle_result.post_count == 0
            and not record.governed_cycle_result.permit_created
        )
        completed.append(sealed["closure_ref"])
        return records

    monkeypatch.setattr(
        consumer, "invoke_occupied_lane_governed_cycle_n1_consumer_v1", close_from_envelope
    )
    scenario.test_accounting_source_reaches_actual_n1_remaining_position_close(
        tmp_path, monkeypatch, direction
    )
    assert len(completed) == 1


def test_close_archive_tampering_cannot_reopen_or_validate_sealed_state(tmp_path):
    context, accounting, fills, cursor = _setup(tmp_path)
    fills = _close(accounting, fills)
    result = _seal(tmp_path, context, accounting, fills)
    path = Path(result["closure_ref"].split(":", 2)[2])
    envelope = json.loads(path.read_text())
    envelope["payload"]["resolution"] = "CLAIMED_ORDER_ACK"
    path.write_text(json.dumps(envelope))
    before = context.binding.to_canonical_state().to_dict()
    with pytest.raises(ValueError, match="SEAL_DIGEST_MISMATCH"):
        _inspect(tmp_path, context)
    assert context.binding.to_canonical_state().to_dict() == before
    assert not context.binding.has_open_position


def test_interrupted_close_publication_blocks_without_ledger_purge(tmp_path, monkeypatch):
    from src.ops.exit_policy_producer_binding_v1 import persistence_v1 as persistence
    from src.ops.exit_policy_producer_binding_v1.constants_v1 import COMMIT_MARKER_FILENAME

    context, accounting, fills, cursor = _setup(tmp_path)
    fills = _close(accounting, fills)
    cursor_bytes = (tmp_path / "core" / CURSOR_FILENAME).read_bytes()
    original = persistence.os.replace

    def interrupt(source, target):
        if Path(target) == tmp_path / "episode" / COMMIT_MARKER_FILENAME:
            raise OSError("injected close marker interruption")
        return original(source, target)

    monkeypatch.setattr(persistence.os, "replace", interrupt)
    with pytest.raises(OSError, match="injected"):
        _seal(tmp_path, context, accounting, fills)
    assert context.binding.alpha_blocked
    with pytest.raises(persistence.ExitPolicyPersistenceError):
        _inspect(tmp_path, context)
    assert (tmp_path / "core" / CURSOR_FILENAME).read_bytes() == cursor_bytes


@pytest.mark.parametrize("change", ["old_id", "account", "old_root", "forked_history"])
def test_successor_requires_sealed_prefix_identity_and_separate_owner_root(tmp_path, change):
    context, accounting, fills, cursor = _setup(tmp_path)
    fills = _close(accounting, fills)
    _seal(tmp_path, context, accounting, fills)
    opening = build_simulated_fill_v1(
        fill_id="next-opening",
        instrument_id=accounting.contract.symbol,
        side="BUY",
        quantity="0.2",
        mark_price="1000",
        contract=accounting.contract,
        event_time_unix=1700004100.0,
    )
    if change == "forked_history":
        from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
            ProductiveFuturesAccountingSessionV1,
        )

        accounting = ProductiveFuturesAccountingSessionV1(contract=accounting.contract)
        fills = ()
    accounting.apply_fill(opening)
    fills = (*fills, opening)
    identity = bind_simulated_accounting_episode_identity_v1(
        identity=context.identity, opening_fill=opening
    )
    if change == "old_id":
        identity = replace(identity, episode_id=context.identity.episode_id)
    elif change == "account":
        identity = replace(
            identity, account_scope=replace(identity.account_scope, account_identity="other")
        )
    target = (
        tmp_path / "episode" / "child" if change == "old_root" else tmp_path / "next" / "episode"
    )
    with pytest.raises(ValueError):
        create_successor_after_sealed_simulated_episode_v1(
            prior_identity=context.identity,
            prior_state_root=tmp_path / "episode",
            prior_repository_sha=context.binding.repository_sha,
            prior_config_digest=context.binding.config_digest,
            prior_initial_source_ref=context.entry_source_ref,
            identity=identity,
            accounting_session=accounting,
            fills=fills,
            source_archive_root=tmp_path / "next" / "sources",
            state_root=target,
            repository_sha=context.binding.repository_sha,
            config_digest=context.binding.config_digest,
            writer_session_id="refused-successor",
        )
    assert not target.exists()
