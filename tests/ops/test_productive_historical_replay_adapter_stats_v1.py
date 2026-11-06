"""Regression: historical qualification stats use canonical DecisionOutcome values."""

from __future__ import annotations

from dataclasses import dataclass

from scripts.ops.productive_historical_replay_adapter_v1 import DecisionEpochStatsV1
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome


@dataclass
class _FakeEvidence:
    decision_outcome: str
    execution_eligible: bool = False
    reason_codes: tuple[str, ...] = ()
    selected_side: str | None = None


@dataclass
class _FakeIntermediate:
    canonical_order_intent: object | None = None


@dataclass
class _FakeResult:
    evidence: _FakeEvidence
    intermediate: _FakeIntermediate | None = None
    replay_pass: bool = True


def test_decision_epoch_stats_counts_lowercase_canonical_outcomes() -> None:
    stats = DecisionEpochStatsV1()
    for outcome in (
        DecisionOutcome.NO_ACTION,
        DecisionOutcome.OBSERVE,
        DecisionOutcome.ENTER_LONG,
        DecisionOutcome.ENTER_SHORT,
        DecisionOutcome.REDUCE,
        DecisionOutcome.EXIT,
        DecisionOutcome.BLOCKED,
    ):
        stats.record_replay(
            result=_FakeResult(evidence=_FakeEvidence(decision_outcome=outcome.value)),
        )
    assert stats.no_action_count == 1
    assert stats.observe_count == 1
    assert stats.enter_long_count == 1
    assert stats.enter_short_count == 1
    assert stats.reduce_count == 1
    assert stats.exit_count == 1
    assert stats.blocked_count == 1


def test_decision_epoch_stats_does_not_count_legacy_uppercase_literals() -> None:
    stats = DecisionEpochStatsV1()
    stats.record_replay(
        result=_FakeResult(evidence=_FakeEvidence(decision_outcome="ENTER_LONG")),
    )
    stats.record_replay(
        result=_FakeResult(evidence=_FakeEvidence(decision_outcome="OBSERVE_HOLD")),
    )
    assert stats.enter_long_count == 0
    assert stats.observe_count == 0
