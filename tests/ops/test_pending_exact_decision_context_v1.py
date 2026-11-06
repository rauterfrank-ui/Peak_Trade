"""Exact DP/cycle transport and rejection of unrelated or ambiguous observations."""

import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from scripts.ops.pre_external_convergence_natural_enter_reporting_v1 import (
    evaluate_natural_enter_reporting_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_pending_decision_context_v1 import (
    canonical_payload_json_v1,
    pending_decision_context_from_invocation_v1,
)
from tests.trading.master_v2.test_double_play_entry_exit_policy_v0 import _evaluate


def _invocation():
    decision = _evaluate()
    market = SimpleNamespace(
        instrument_id=decision.instrument_id,
        trading_epoch=decision.trading_epoch,
        decision_time="2026-11-04T10:00:01+00:00",
        mark_price=1234.5,
        context_id="ctx-test",
    )
    return SimpleNamespace(
        bound_instrument=SimpleNamespace(
            instrument_id=decision.instrument_id, venue_native_id="ETH-USDT-SWAP"
        ),
        cycle_result=SimpleNamespace(
            cycle_id="persistent-natural-enter-live-c1:s5:LANE_1:LANE_1",
            outgoing_cursor=SimpleNamespace(now_tick=7),
            replay=SimpleNamespace(
                replay_pass=True,
                intermediate=SimpleNamespace(market_context=market, entry_exit_decision=decision),
            ),
        ),
    )


def _report(tmp_path, context, rows):
    path = tmp_path / "ddo.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    return evaluate_natural_enter_reporting_v1(
        cycle_records=[
            SimpleNamespace(
                cycle_index=2,
                s5_disposition="PRE_EXTERNAL_EFFECT",
                pending_decision_context=context,
            )
        ],
        terminal_disposition="PRE_EXTERNAL_EFFECT",
        ddo_jsonl=path,
    )


def _row(context):
    return dict(
        record_type="double_play_entry_exit_observation",
        record_id="ddo.dpo.test",
        payload=dict(
            cycle_id=context.cycle_id,
            decision_event_ref="ddo.dec.test",
            producer_canonical_payload=json.loads(context.producer_payload_json),
        ),
    )


def test_exact_match_uses_producer_price_and_time_independent_of_ordinal(tmp_path):
    context = pending_decision_context_from_invocation_v1(_invocation())
    report = _report(tmp_path, context, [_row(context)])
    assert report.natural_pre_external_reached
    assert report.decision_context.reference_price == 1234.5
    assert report.decision_context.decision_timestamp_unix == 1793786401.0
    assert report.dpo["s5_cycle_index"] == "2"
    assert report.dpo["cycle_id"].endswith(":cycle:7")


@pytest.mark.parametrize(
    "field,value",
    [
        ("policy_decision_id", "other"),
        ("instrument_id", "other"),
        ("trading_epoch", 999),
        ("input_digest", "a" * 64),
        ("decision_outcome", "enter_short"),
        ("selected_side", "short"),
        ("execution_eligible", True),
    ],
)
def test_different_producer_payload_cannot_fall_back_to_epoch_or_ordinal(tmp_path, field, value):
    context = pending_decision_context_from_invocation_v1(_invocation())
    row = _row(context)
    payload = row["payload"]["producer_canonical_payload"]
    assert payload[field] != value
    payload[field] = value
    report = _report(tmp_path, context, [row])
    assert not report.natural_pre_external_reached
    assert report.decision_context is None and report.dpo == {}


def test_wrong_cycle_and_duplicate_matches_are_rejected(tmp_path):
    context = pending_decision_context_from_invocation_v1(_invocation())
    row = _row(context)
    row["payload"]["cycle_id"] += "-other"
    assert not _report(tmp_path, context, [row]).natural_enter_observed
    assert not _report(tmp_path, context, [_row(context), _row(context)]).natural_enter_observed


@pytest.mark.parametrize(
    "field,value",
    [
        ("mark_price", float("nan")),
        ("mark_price", True),
        ("mark_price", 0),
        ("decision_time", "2026-11-04T10:00:01"),
        ("instrument_id", "wrong"),
        ("trading_epoch", 99),
    ],
)
def test_invalid_or_different_market_context_is_not_bound(field, value):
    invocation = _invocation()
    setattr(invocation.cycle_result.replay.intermediate.market_context, field, value)
    assert pending_decision_context_from_invocation_v1(invocation) is None


def test_missing_or_failed_replay_has_no_context():
    assert pending_decision_context_from_invocation_v1(None) is None
    invocation = _invocation()
    invocation.cycle_result.replay.replay_pass = False
    assert pending_decision_context_from_invocation_v1(invocation) is None


def test_unrelated_later_enter_cannot_override_selected_context(tmp_path):
    context = pending_decision_context_from_invocation_v1(_invocation())
    other = replace(context, cycle_id=context.cycle_id.replace(":cycle:7", ":cycle:99"))
    payload = json.loads(other.producer_payload_json)
    payload["trading_epoch"] += 100
    other = replace(other, producer_payload_json=canonical_payload_json_v1(payload))
    report = _report(tmp_path, context, [_row(context), _row(other)])
    assert report.decision_context == context
    assert report.dpo["cycle_id"] == context.cycle_id
