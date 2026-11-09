"""Applied signed funding follows original fills, source proofs and Exit recovery."""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import json

import pytest

from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
    AccountingEngineError,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    create_position_episode_from_simulated_accounting_v1,
    economic_journal_events_v1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_progress_v1 import (
    verify_simulated_accounting_progress_v1,
)
from tests.ops.test_simulated_accounting_entry_source_v1 import _history, _args
from tests.ops.test_simulated_accounting_episode_progress_v1 import _setup, _advance, _recover
from tests.ops.test_simulated_accounting_episode_close_v1 import _close, _seal, _inspect
from tests.ops.test_current_productive_occupied_scope_continuity_v1 import _cycle


def funding(session, *, event_id="z-first", amount="-0.25", time=1700000250.0):
    return session.apply_funding_observation_v1(
        event_id=event_id,
        amount=amount,
        currency=session.contract.quote_currency,
        instrument_id=session.contract.symbol,
        event_time_unix=time,
    )


@pytest.mark.parametrize("direction", [1, -1])
@pytest.mark.parametrize("amount", ["-0.25", "0.30", "0"])
def test_signed_funding_only_progress_reaches_original_exit_and_cold_read(
    tmp_path, direction, amount
):
    episode, session, fills, cursor = _setup(tmp_path, direction)
    before = session.portfolio_state()
    old_entry = (episode.binding.entry_price, episode.binding.entry_event_time, episode.identity)
    funding(session, amount=amount)
    assert session.portfolio_state().equity == before.equity + Decimal(amount)
    assert session.position.qty == Decimal("0.4")
    assert session.cumulative_fees == before.cumulative_fees
    assert _advance(tmp_path, episode, session, fills)["status"] == "APPLIED"
    progress = verify_simulated_accounting_progress_v1(episode)
    assert progress["latest_fill_event_time"] == 1700000240.0
    assert progress["latest_economic_event_time"] == 1700000250.0
    assert episode.binding.simulated_accounting_progress["applied_fill_count"] == 3
    assert episode.binding.simulated_accounting_progress["applied_funding_count"] == 1
    assert old_entry == (
        episode.binding.entry_price,
        episode.binding.entry_event_time,
        episode.identity,
    )
    checkpoint = session.to_durable_dict()
    assert funding(session, amount=amount)["idempotent_replay"]
    assert session.to_durable_dict() == checkpoint
    sequence = episode.binding.commit_sequence
    assert _advance(tmp_path, episode, session, fills)["status"] == "ALREADY_APPLIED"
    assert episode.binding.commit_sequence == sequence
    restored = _recover(tmp_path, episode)
    result = _cycle(
        tmp_path / "core",
        direction=direction,
        step=63,
        incoming=cursor,
        occupied=True,
        position_episode_binding=restored,
    )
    assert result.replay_pass == "true", result.fail_reasons
    assert result.replay.intermediate.entry_exit_decision.exit_class.value == "time_exit"


@pytest.mark.parametrize("direction", [1, -1])
def test_actual_interleaving_is_replayed_and_not_sorted_by_funding_id(tmp_path, direction):
    identity, base, fills = _history(direction)
    session = ProductiveFuturesAccountingSessionV1(contract=base.contract)
    session.apply_fill(fills[0])
    funding(session, time=1700000121.0)
    session.apply_fill(fills[1])
    funding(session, event_id="a-second", amount="0.1", time=1700000181.0)
    session.apply_fill(fills[2])
    checkpoint = json.loads(json.dumps(session.to_durable_dict(), sort_keys=True))
    restored = ProductiveFuturesAccountingSessionV1.from_durable_dict(checkpoint)
    episode = create_position_episode_from_simulated_accounting_v1(
        **_args(tmp_path, identity), session=restored, fills=fills
    )
    assert episode.binding.entry_event_time == fills[0].event_time_unix
    payload = dict(accounting_checkpoint=checkpoint, fills=[fill.to_dict() for fill in fills])
    events = economic_journal_events_v1(payload)
    assert [event["kind"] for event in events] == ["FILL", "FUNDING", "FILL", "FUNDING", "FILL"]
    assert [event["event_id"] for event in events if event["kind"] == "FUNDING"] == [
        "z-first",
        "a-second",
    ]


def test_funding_and_full_close_are_sealed_by_original_owner(tmp_path):
    episode, session, fills, _ = _setup(tmp_path)
    funding(session)
    _advance(tmp_path, episode, session, fills)
    fills = _close(session, fills)
    sealed = _seal(tmp_path, episode, session, fills)
    assert sealed["status"] == "SEALED"
    assert _inspect(tmp_path, episode) == sealed
    assert sealed["source_payload"]["accounting_checkpoint"]["funding_pnl"] == "-0.25"


@pytest.mark.parametrize("time", [True, float("nan"), float("inf"), 10**1000, 0, -1, 1700000239.0])
def test_bad_funding_time_leaves_all_original_accounting_unchanged(time):
    _, session, _ = _history()
    before = session.to_durable_dict()
    with pytest.raises(ValueError):
        funding(session, time=time)
    assert session.to_durable_dict() == before


@pytest.mark.parametrize("change", ["time", "amount", "currency", "instrument"])
def test_conflicting_funding_identity_cannot_change_saved_money(change):
    _, session, _ = _history()
    funding(session)
    before = session.to_durable_dict()
    args = dict(
        event_id="z-first",
        amount="-0.25",
        currency=session.contract.quote_currency,
        instrument_id=session.contract.symbol,
        event_time_unix=1700000250.0,
    )
    args.update(
        {
            "time": dict(event_time_unix=1700000251.0),
            "amount": dict(amount="-0.2"),
            "currency": dict(currency="USDC"),
            "instrument": dict(instrument_id="foreign"),
        }[change]
    )
    with pytest.raises(AccountingEngineError, match="FUNDING_(ID_CONFLICT|SCOPE_MISMATCH)"):
        session.apply_funding_observation_v1(**args)
    assert session.to_durable_dict() == before


def test_fill_cannot_arrive_before_already_applied_funding():
    _, session, fills = _history()
    funding(session)
    before = session.to_durable_dict()
    late = replace(fills[-1], fill_id="late-new", event_time_unix=1700000245.0)
    with pytest.raises(AccountingEngineError, match="LATE_FILL"):
        session.apply_fill(late)
    assert session.to_durable_dict() == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("funding_sequence", True),
        ("funding_sequence", 2),
        ("applied_after_fill_count", True),
        ("applied_after_fill_count", 4),
        ("event_time_unix", float("nan")),
        ("unknown", "x"),
    ],
)
def test_bad_durable_funding_order_is_rejected(field, value):
    _, session, _ = _history()
    funding(session)
    checkpoint = session.to_durable_dict()
    checkpoint["funding_events"]["z-first"][field] = value
    with pytest.raises(ValueError):
        ProductiveFuturesAccountingSessionV1.from_durable_dict(checkpoint)


def test_durable_funding_values_are_detached_in_both_directions():
    _, session, _ = _history()
    funding(session)
    checkpoint = session.to_durable_dict()
    original = deepcopy(checkpoint)
    checkpoint["funding_events"]["z-first"]["amount"] = "-100"
    assert session.to_durable_dict() == original
    restored = ProductiveFuturesAccountingSessionV1.from_durable_dict(original)
    original["funding_events"]["z-first"]["amount"] = "-200"
    assert restored.funding_pnl == Decimal("-0.25")
    assert restored.funding_events["z-first"]["amount"] == "-0.25"


@pytest.mark.parametrize("initial_source", [False, True])
def test_original_cycle_cannot_use_funding_from_after_its_observation(tmp_path, initial_source):
    if initial_source:
        identity, session, fills = _history()
        funding(session, time=1700005000.0)
        episode = create_position_episode_from_simulated_accounting_v1(
            **_args(tmp_path, identity), session=session, fills=fills
        )
    else:
        episode, session, fills, _ = _setup(tmp_path)
        funding(session, time=1700005000.0)
        _advance(tmp_path, episode, session, fills)
    restored = _recover(tmp_path, episode)
    before = restored.binding.to_canonical_state().to_dict()
    with pytest.raises(ValueError, match="SIMULATED_ENTRY_(PROGRESS|FUNDING)_AFTER_OBSERVATION"):
        restored.prepare_for_cycle_v1(
            instrument_id=restored.identity.instrument_id,
            venue_native_id=restored.identity.venue_native_id,
            position_side=restored.identity.position_side,
            venue_flat=False,
            event_time=1700004000.0,
            lane_id=restored.identity.lane_id,
            expected_scope=restored.identity.account_scope,
        )
    assert restored.binding.to_canonical_state().to_dict() == before


def test_funding_after_flat_observation_cannot_be_sealed_as_already_known(tmp_path):
    episode, session, fills, _ = _setup(tmp_path)
    fills = _close(session, fills)
    funding(session, time=1700005000.0)
    before = episode.binding.to_canonical_state().to_dict()
    with pytest.raises(ValueError, match="SIMULATED_CLOSE_OBSERVATION_TIME_UNPROVEN"):
        _seal(tmp_path, episode, session, fills)
    assert episode.binding.to_canonical_state().to_dict() == before


def test_unfunded_legacy_unknown_open_time_can_still_close_from_explicit_flat(tmp_path):
    episode, session, fills, _ = _setup(tmp_path, time=None)
    fills = _close(session, fills)
    sealed = _seal(tmp_path, episode, session, fills)
    assert sealed["status"] == "SEALED"
    assert _inspect(tmp_path, episode) == sealed
