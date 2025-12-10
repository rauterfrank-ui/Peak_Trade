from pathlib import Path

import pandas as pd

from src.reporting.trigger_training_report import (
    TriggerOutcome,
    TriggerTrainingEvent,
    build_trigger_training_report,
    events_to_dataframe,
)


def test_build_trigger_training_report(tmp_path: Path) -> None:
    events = [
        TriggerTrainingEvent(
            timestamp=pd.Timestamp("2025-01-01T00:00:00Z"),
            symbol="BTCEUR",
            signal_state=1,
            recommended_action="ENTER_LONG",
            user_action="EXECUTED",
            outcome=TriggerOutcome.HIT,
            reaction_delay_s=1.2,
            pnl_after_bars=25.0,
            tags=["focus"],
        ),
        TriggerTrainingEvent(
            timestamp=pd.Timestamp("2025-01-01T00:05:00Z"),
            symbol="BTCEUR",
            signal_state=1,
            recommended_action="ENTER_LONG",
            user_action="SKIPPED",
            outcome=TriggerOutcome.MISSED,
            reaction_delay_s=10.0,
            pnl_after_bars=40.0,
            tags=["hesitation", "fear"],
        ),
    ]

    df = events_to_dataframe(events)
    assert not df.empty
    assert "outcome" in df.columns

    report_path = build_trigger_training_report(
        events,
        tmp_path,
        session_meta={"session_id": "TEST_TRIGGER", "mode": "offline_training"},
    )
    assert report_path.is_file()
    content = report_path.read_text(encoding="utf-8")
    assert "Trigger Training Report" in content
    assert "TEST_TRIGGER" in content

