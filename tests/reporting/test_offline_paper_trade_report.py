from pathlib import Path

import pandas as pd

from src.reporting.offline_paper_trade_report import (
    OfflinePaperTradeSessionMeta,
    build_offline_paper_trade_report,
)


def test_build_offline_paper_trade_report(tmp_path: Path) -> None:
    trades = pd.DataFrame(
        {
            "pnl": [10.0, -5.0, 3.5],
            "fees": [0.1, 0.2, 0.3],
        }
    )

    meta = OfflinePaperTradeSessionMeta(
        session_id="TEST_SESSION",
        environment="offline_paper_trade",
        symbol="BTCEUR",
        timeframe="1m",
        start_ts=pd.Timestamp("2025-01-01T00:00:00Z"),
        end_ts=pd.Timestamp("2025-01-01T01:00:00Z"),
        extra={"note": "unit test"},
    )

    report_path = build_offline_paper_trade_report(trades, meta, tmp_path)
    assert report_path.is_file()
    content = report_path.read_text(encoding="utf-8")
    assert "Offline Paper Trade Report" in content
    assert "TEST_SESSION" in content

