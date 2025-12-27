from pathlib import Path

import pandas as pd

from src.reporting.offline_paper_trade_integration import (
    OfflinePaperTradeReportConfig,
    generate_reports_for_offline_paper_trade,
)
from src.reporting.trigger_training_report import (
    TriggerOutcome,
    TriggerTrainingEvent,
)


def test_generate_reports_for_offline_paper_trade_without_trigger_events(
    tmp_path: Path, monkeypatch
) -> None:
    # Wir überschreiben das base_reports_dir, damit alles in tmp_path landet.
    trades = pd.DataFrame(
        {
            "pnl": [10.0, -5.0, 3.5],
            "fees": [0.1, 0.2, 0.3],
        }
    )

    cfg = OfflinePaperTradeReportConfig(
        session_id="SESSION_NO_TRIGGER",
        environment="offline_paper_trade",
        symbol="BTCEUR",
        timeframe="1m",
        start_ts=pd.Timestamp("2025-01-01T00:00:00Z"),
        end_ts=pd.Timestamp("2025-01-01T01:00:00Z"),
        extra_meta={"strategy": "MA_Crossover"},
        base_reports_dir=tmp_path,
    )

    result = generate_reports_for_offline_paper_trade(trades, cfg)
    assert "paper_report" in result
    assert result["paper_report"].is_file()
    content = result["paper_report"].read_text(encoding="utf-8")
    assert "Offline Paper Trade Report" in content
    assert "SESSION_NO_TRIGGER" in content
    assert "MA_Crossover" in content


def test_generate_reports_for_offline_paper_trade_with_trigger_events(tmp_path: Path) -> None:
    trades = pd.DataFrame(
        {
            "pnl": [5.0, -1.0],
            "fees": [0.1, 0.1],
        }
    )

    cfg = OfflinePaperTradeReportConfig(
        session_id="SESSION_WITH_TRIGGER",
        environment="offline_paper_trade",
        symbol="BTCEUR",
        timeframe="1m",
        start_ts=pd.Timestamp("2025-01-01T00:00:00Z"),
        end_ts=pd.Timestamp("2025-01-01T01:00:00Z"),
        extra_meta=None,
        base_reports_dir=tmp_path,
    )

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
            note="Unit test event",
        )
    ]

    session_meta_for_trigger = {
        "session_id": cfg.session_id,
        "mode": cfg.environment,
        "label": "unit_test",
    }

    result = generate_reports_for_offline_paper_trade(
        trades,
        cfg,
        trigger_events=events,
        session_meta_for_trigger=session_meta_for_trigger,
    )

    assert "paper_report" in result
    assert "trigger_report" in result

    paper_content = result["paper_report"].read_text(encoding="utf-8")
    trigger_content = result["trigger_report"].read_text(encoding="utf-8")

    assert "Offline Paper Trade Report" in paper_content
    assert "Trigger Training Report" in trigger_content
    assert "SESSION_WITH_TRIGGER" in trigger_content
    assert "unit_test" in trigger_content

