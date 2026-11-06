"""Applied accounting fills, retained source and actual existing Exit consumers."""

from dataclasses import replace
from decimal import Decimal
import json

import pytest

from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    bind_simulated_accounting_episode_identity_v1,
    create_position_episode_from_simulated_accounting_v1,
    recover_position_episode_from_simulated_accounting_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (
    build_simulated_fill_v1,
)
from tests.ops.test_productive_futures_accounting_runtime_binding_v1 import _contract
from tests.ops.test_position_episode_exit_continuity_v1 import _identity, _natural_entry
from tests.ops.test_current_productive_occupied_scope_continuity_v1 import _cycle
from src.ops.exit_policy_producer_binding_v1.constants_v1 import FROZEN_PROFIT_PROTECTION_DISTANCE
from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    layer_c_derived_exit_policy_adverse_config_digest_v1,
)


def _history(direction=1, time=1700000120.0):
    identity = _identity(direction)
    session = ProductiveFuturesAccountingSessionV1(
        contract=_contract(identity.venue_native_id, contract_size="1", min_qty="0.1")
    )
    fills = []
    for i, (qty, mark, reduce) in enumerate(
        (("0.3", "1020", False), ("0.3", "1030", False), ("0.2", "1040", True))
    ):
        fill = build_simulated_fill_v1(
            fill_id=f"fill:{direction}:{i}",
            instrument_id=identity.venue_native_id,
            side=("BUY" if direction == 1 else "SELL")
            if not reduce
            else ("SELL" if direction == 1 else "BUY"),
            quantity=qty,
            mark_price=mark,
            contract=session.contract,
            reduce_only=reduce,
            event_time_unix=time if i == 0 else (1700000120.0 if time is None else time) + i * 60,
            slippage_bps="10",
            fee_rate_bps="5",
        )
        session.apply_fill(fill)
        fills.append(fill)
    identity = bind_simulated_accounting_episode_identity_v1(
        identity=identity, opening_fill=fills[0]
    )
    return identity, session, tuple(fills)


def _args(tmp_path, identity):
    return dict(
        identity=identity,
        source_archive_root=tmp_path / "sources",
        state_root=tmp_path / "episode",
        repository_sha="offline-source-test",
        config_digest=layer_c_derived_exit_policy_adverse_config_digest_v1(
            profit_protection_distance=FROZEN_PROFIT_PROTECTION_DISTANCE
        ),
        writer_session_id="offline-source-test",
    )


@pytest.mark.parametrize("direction", [1, -1])
def test_applied_weighted_entry_and_first_open_time_survive_reduce_archive_reload_and_actual_exit(
    tmp_path, direction
):
    identity, session, fills = _history(direction)
    before = session.to_durable_dict()
    context = create_position_episode_from_simulated_accounting_v1(
        **_args(tmp_path, identity), session=session, fills=fills
    )
    assert session.to_durable_dict() == before
    assert session.position.qty == Decimal("0.4")
    assert context.binding.entry_price == float(session.position.entry_price)
    assert context.binding.entry_price not in (
        float(session.last_mark),
        float(fills[-1].fill_price),
    )
    assert context.binding.entry_event_time == fills[0].event_time_unix
    assert context.binding.entry_event_time != fills[-1].event_time_unix
    source = next((tmp_path / "sources").glob("*.json"))
    recover_args = _args(tmp_path, identity)
    recover_args.pop("source_archive_root")
    context = recover_position_episode_from_simulated_accounting_v1(
        **recover_args, source_path=source
    )
    cursor = _natural_entry(tmp_path / "core", direction)
    result = _cycle(
        tmp_path / "core",
        direction=direction,
        step=63,
        incoming=cursor,
        occupied=True,
        position_episode_binding=context,
    )
    assert result.replay_pass == "true", result.fail_reasons
    assert result.replay.intermediate.entry_exit_decision.exit_class.value == "time_exit"
    assert context.binding.pending_exit_identity


def test_unknown_open_time_is_not_replaced_by_later_fill_time(tmp_path):
    identity, session, fills = _history(time=None)
    context = create_position_episode_from_simulated_accounting_v1(
        **_args(tmp_path, identity), session=session, fills=fills
    )
    assert context.binding.entry_event_time is None
    cursor = _natural_entry(tmp_path / "core", 1)
    result = _cycle(
        tmp_path / "core", step=63, incoming=cursor, occupied=True, position_episode_binding=context
    )
    assert result.replay_pass == "true", result.fail_reasons
    assert not context.binding.last_bundle["time_exit"]["triggered"]


@pytest.mark.parametrize(
    "change", ["missing", "reordered", "price", "time", "fill_id", "unapplied"]
)
def test_unproven_fill_lineage_rejects_before_source_or_exit_writes(tmp_path, change):
    identity, session, fills = _history()
    if change == "missing":
        fills = fills[1:]
    elif change == "reordered":
        fills = tuple(reversed(fills))
    elif change == "unapplied":
        fills += (replace(fills[-1], fill_id="not-applied"),)
    else:
        field, value = {
            "price": ("fill_price", Decimal("999")),
            "time": ("event_time_unix", 1700000001.0),
            "fill_id": ("fill_id", "foreign"),
        }[change]
        fills = (replace(fills[0], **{field: value}), *fills[1:])
    before = session.to_durable_dict()
    with pytest.raises(ValueError):
        create_position_episode_from_simulated_accounting_v1(
            **_args(tmp_path, identity), session=session, fills=fills
        )
    assert session.to_durable_dict() == before
    assert not (tmp_path / "sources").exists() and not (tmp_path / "episode").exists()


@pytest.mark.parametrize("environment", ["LIVE", "TESTNET", "PAPER_EXCHANGE", "SHADOW"])
def test_simulated_source_cannot_be_relabelled_as_other_environment(tmp_path, environment):
    identity, session, fills = _history()
    identity = replace(
        identity, account_scope=replace(identity.account_scope, execution_environment=environment)
    )
    with pytest.raises(ValueError, match="MODE_FORBIDDEN"):
        create_position_episode_from_simulated_accounting_v1(
            **_args(tmp_path, identity), session=session, fills=fills
        )
    assert not (tmp_path / "sources").exists()


def test_archived_source_tampering_does_not_change_existing_episode(tmp_path):
    identity, session, fills = _history()
    context = create_position_episode_from_simulated_accounting_v1(
        **_args(tmp_path, identity), session=session, fills=fills
    )
    source = next((tmp_path / "sources").glob("*.json"))
    payload = json.loads(source.read_text())
    payload["payload"]["fills"][0]["event_time_unix"] = 1.0
    source.write_text(json.dumps(payload))
    before = context.binding.to_canonical_state().to_dict()
    args = _args(tmp_path, identity)
    args.pop("source_archive_root")
    with pytest.raises(ValueError, match="DIGEST_MISMATCH"):
        recover_position_episode_from_simulated_accounting_v1(**args, source_path=source)
    assert context.binding.to_canonical_state().to_dict() == before


def test_checkpoint_restored_by_original_owner_is_supported(tmp_path):
    identity, session, fills = _history()
    session = ProductiveFuturesAccountingSessionV1.from_durable_dict(session.to_durable_dict())
    context = create_position_episode_from_simulated_accounting_v1(
        **_args(tmp_path, identity), session=session, fills=fills
    )
    assert context.binding.entry_event_time == fills[0].event_time_unix


@pytest.mark.parametrize("direction", [1, -1])
def test_confirmed_simulated_close_and_reopen_receive_different_episode_keys(tmp_path, direction):
    identity, session, fills = _history(direction)
    original = create_position_episode_from_simulated_accounting_v1(
        **_args(tmp_path / "old", identity), session=session, fills=fills
    )
    close = build_simulated_fill_v1(
        fill_id="full-close",
        instrument_id=identity.venue_native_id,
        side="SELL" if direction == 1 else "BUY",
        quantity="0.4",
        mark_price="1040",
        contract=session.contract,
        reduce_only=True,
        event_time_unix=1700000400.0,
    )
    session.apply_fill(close)
    fills += (close,)
    with pytest.raises(ValueError, match="OPEN_EPISODE_REQUIRED"):
        create_position_episode_from_simulated_accounting_v1(
            **_args(tmp_path / "flat", identity), session=session, fills=fills
        )
    opening = build_simulated_fill_v1(
        fill_id="next-opening",
        instrument_id=identity.venue_native_id,
        side="SELL" if direction == 1 else "BUY",
        quantity="0.2",
        mark_price="1050",
        contract=session.contract,
        event_time_unix=1700000500.0,
    )
    session.apply_fill(opening)
    fills += (opening,)
    new_identity = bind_simulated_accounting_episode_identity_v1(
        identity=replace(identity, position_side="short" if direction == 1 else "long"),
        opening_fill=opening,
    )
    assert new_identity.episode_id != identity.episode_id
    with pytest.raises(ValueError):
        create_position_episode_from_simulated_accounting_v1(
            **_args(tmp_path / "wrong", identity), session=session, fills=fills
        )
    new = create_position_episode_from_simulated_accounting_v1(
        **_args(tmp_path / "new", new_identity), session=session, fills=fills
    )
    assert new.binding.entry_event_time == opening.event_time_unix
    assert original.binding.entry_event_time == fills[0].event_time_unix
    assert original.identity.episode_id != new.identity.episode_id


def test_funding_without_ordered_replay_is_rejected_without_guessing(tmp_path):
    identity, session, fills = _history()
    session.apply_funding_observation_v1(
        event_id="funding", amount="-1", currency="USDT", instrument_id=identity.venue_native_id
    )
    with pytest.raises(ValueError, match="FUNDING_REPLAY_NOT_SUPPORTED"):
        create_position_episode_from_simulated_accounting_v1(
            **_args(tmp_path, identity), session=session, fills=fills
        )
    assert not (tmp_path / "sources").exists()


def test_changed_mark_after_last_fill_cannot_become_average_entry(tmp_path):
    identity, session, fills = _history()
    session.mark_to_market(Decimal("1200"))
    context = create_position_episode_from_simulated_accounting_v1(
        **_args(tmp_path, identity), session=session, fills=fills
    )
    assert context.binding.entry_price == float(session.position.entry_price)
    assert context.binding.entry_price != float(session.last_mark)


@pytest.mark.parametrize("time", [True, float("nan"), float("inf"), -1.0])
def test_invalid_source_fill_times_are_not_converted_to_entry_clock(tmp_path, time):
    identity, session, fills = _history()
    fills = (replace(fills[0], event_time_unix=time), *fills[1:])
    with pytest.raises(ValueError, match="INVALID_FILL_TIME"):
        create_position_episode_from_simulated_accounting_v1(
            **_args(tmp_path, identity), session=session, fills=fills
        )
    assert not (tmp_path / "sources").exists()


@pytest.mark.parametrize("direction", [1, -1])
def test_accounting_source_reaches_actual_n1_remaining_position_close(
    tmp_path, monkeypatch, direction
):
    from tests.ops import test_position_episode_exit_continuity_v1 as scenario

    opened = {}

    def accounting_open(root, direction=1, mode="create", **overrides):
        if mode == "create":
            identity, session, fills = _history(direction, time=overrides["entry_event_time"])
            assert session.position.qty == Decimal("0.4")
            identity = bind_simulated_accounting_episode_identity_v1(
                identity=overrides["identity"], opening_fill=fills[0]
            )
            args = _args(root.parent / "accounting", identity)
            args["state_root"] = root
            context = create_position_episode_from_simulated_accounting_v1(
                **args, session=session, fills=fills
            )
            source = next(args["source_archive_root"].glob("*.json"))
            args.pop("source_archive_root")
            opened[root] = (args, source)
            return context
        args, source = opened[root]
        return recover_position_episode_from_simulated_accounting_v1(**args, source_path=source)

    monkeypatch.setattr(scenario, "_open", accounting_open)
    scenario.test_lane_host_uses_reloaded_time_anchor_for_full_remaining_close(
        tmp_path, monkeypatch, direction, "LANE_1"
    )


def test_existing_archive_is_never_overwritten_or_repaired(tmp_path):
    identity, session, fills = _history()
    create_position_episode_from_simulated_accounting_v1(
        **_args(tmp_path, identity), session=session, fills=fills
    )
    source = next((tmp_path / "sources").glob("*.json"))
    source.write_text("retained interrupted source")
    args = _args(tmp_path, identity)
    args["state_root"] = tmp_path / "new-episode"
    with pytest.raises(ValueError, match="SOURCE_ARCHIVE_CONFLICT"):
        create_position_episode_from_simulated_accounting_v1(**args, session=session, fills=fills)
    assert source.read_text() == "retained interrupted source"
    assert not args["state_root"].exists()


def test_reused_episode_id_for_a_different_opening_is_rejected(tmp_path):
    identity, session, fills = _history()
    identity = replace(identity, episode_id="different-opening")
    with pytest.raises(ValueError, match="EPISODE_ID_MISMATCH"):
        create_position_episode_from_simulated_accounting_v1(
            **_args(tmp_path, identity), session=session, fills=fills
        )
    assert not (tmp_path / "sources").exists()
