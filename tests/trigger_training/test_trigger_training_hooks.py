from datetime import timedelta

import pandas as pd

from src.trigger_training.hooks import (
    TriggerTrainingHookConfig,
    build_trigger_training_events_from_dfs,
)
from src.reporting.trigger_training_report import TriggerOutcome


def test_build_trigger_training_events_from_dfs_basic() -> None:
    # Zeitachse
    base_ts = pd.Timestamp("2025-01-01T00:00:00Z")

    # Zwei Signals: eins mit Aktion (HIT), eins ohne Aktion (MISSED)
    signals = pd.DataFrame(
        {
            "signal_id": [1, 2],
            "timestamp": [base_ts, base_ts + timedelta(minutes=1)],
            "symbol": ["BTCEUR", "BTCEUR"],
            "signal_state": [1, 1],
            "recommended_action": ["ENTER_LONG", "ENTER_LONG"],
        }
    )

    actions = pd.DataFrame(
        {
            "signal_id": [1],
            "timestamp": [base_ts + timedelta(seconds=1)],
            "user_action": ["EXECUTED"],
        }
    )

    prices = pd.DataFrame(
        {
            "timestamp": [
                base_ts,
                base_ts + timedelta(minutes=1),
                base_ts + timedelta(minutes=2),
            ],
            "symbol": ["BTCEUR", "BTCEUR", "BTCEUR"],
            "close": [100.0, 101.0, 102.0],
        }
    )

    cfg = TriggerTrainingHookConfig(
        lookahead_bars=1,
        late_threshold_s=5.0,
        pain_threshold=0.0,
    )

    events = build_trigger_training_events_from_dfs(
        signals=signals,
        actions=actions,
        prices=prices,
        config=cfg,
    )

    assert len(events) == 2

    # Sortierung konsistent halten
    events_sorted = sorted(events, key=lambda e: e.timestamp)

    first, second = events_sorted[0], events_sorted[1]

    # Erstes Signal: Aktion innerhalb 1s -> HIT
    assert first.outcome == TriggerOutcome.HIT
    assert abs(first.reaction_delay_s - 1.0) < 1e-6
    assert "rule_follow" in first.tags

    # PnL nach 1 Bar: von 100 auf 101 -> +1
    assert first.pnl_after_bars == 1.0

    # Zweites Signal: keine Aktion -> MISSED
    assert second.outcome == TriggerOutcome.MISSED
    assert "missed_opportunity" in second.tags
    # PnL nach 1 Bar: von 101 auf 102 -> +1
    assert second.pnl_after_bars == 1.0
