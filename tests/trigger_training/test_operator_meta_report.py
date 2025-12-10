from pathlib import Path

import pandas as pd

from src.reporting.trigger_training_report import TriggerTrainingEvent, TriggerOutcome
from src.trigger_training.operator_meta_report import build_operator_meta_report


def _make_event(
    ts: str,
    outcome: TriggerOutcome,
    pnl: float,
    delay_s: float,
    symbol: str = "BTCEUR",
) -> TriggerTrainingEvent:
    return TriggerTrainingEvent(
        timestamp=pd.Timestamp(ts),
        symbol=symbol,
        signal_state=1,
        recommended_action="ENTER_LONG",
        user_action="EXECUTED" if outcome == TriggerOutcome.HIT else "SKIPPED",
        outcome=outcome,
        reaction_delay_s=delay_s,
        pnl_after_bars=pnl,
        tags=[],
        note="unit test",
    )


def test_build_operator_meta_report(tmp_path: Path) -> None:
    # Session A: eher gut (mehr HITs, wenig Pain)
    session_a_events = [
        _make_event("2025-01-01T00:00:00Z", TriggerOutcome.HIT, 1.0, 1.0),
        _make_event("2025-01-01T00:01:00Z", TriggerOutcome.HIT, 0.5, 2.0),
        _make_event("2025-01-01T00:02:00Z", TriggerOutcome.MISSED, 0.5, 0.0),
    ]

    # Session B: eher schlecht (mehr MISSED, hoher Pain)
    session_b_events = [
        _make_event("2025-01-02T00:00:00Z", TriggerOutcome.MISSED, 2.0, 0.0),
        _make_event("2025-01-02T00:01:00Z", TriggerOutcome.LATE, 1.5, 10.0),
        _make_event("2025-01-02T00:02:00Z", TriggerOutcome.HIT, 0.2, 3.0),
    ]

    sessions = [
        ("SESSION_A", session_a_events),
        ("SESSION_B", session_b_events),
    ]

    output_path = tmp_path / "operator_stats_overview.html"
    result_path = build_operator_meta_report(sessions, output_path)

    assert result_path.is_file()
    content = result_path.read_text(encoding="utf-8")

    # Grundlegende Checks
    assert "Trigger Training – Operator Meta Report" in content
    assert "SESSION_A" in content
    assert "SESSION_B" in content
    # Outcomes sollten erwähnt werden
    assert "HIT" in content
    assert "MISSED" in content
