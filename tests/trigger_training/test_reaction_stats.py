"""Tests für Trigger Reaction Stats Modul."""

import pandas as pd
import pytest

from src.trigger_training.reaction_stats import (
    TriggerReactionCategory,
    TriggerReactionConfig,
    TriggerReactionRecord,
    TriggerReactionSummary,
    compute_reaction_records,
    reaction_records_to_df,
    reaction_summary_to_dict,
    summarize_reaction_records,
)


class TestTriggerReactionStats:
    """Test-Suite für Trigger Reaction Stats."""

    def test_compute_reaction_records_impulsive(self):
        """Test: Impulsive Reaktion (< 300 ms)."""
        signals_df = pd.DataFrame({
            "signal_id": [1],
            "timestamp": [pd.Timestamp("2025-01-01 10:00:00")],
            "recommended_action": ["ENTER_LONG"],
            "symbol": ["BTCEUR"]
        })

        actions_df = pd.DataFrame({
            "signal_id": [1],
            "timestamp": [pd.Timestamp("2025-01-01 10:00:00.100")],  # 100 ms
            "user_action": ["EXECUTED"]
        })

        config = TriggerReactionConfig(impulsive_threshold_ms=300)
        records = compute_reaction_records(signals_df, actions_df, config)

        assert len(records) == 1
        assert records[0].category == TriggerReactionCategory.IMPULSIVE
        assert records[0].reaction_ms == pytest.approx(100.0, abs=1.0)

    def test_compute_reaction_records_on_time(self):
        """Test: On-Time Reaktion (300 ms - 3 s)."""
        signals_df = pd.DataFrame({
            "signal_id": [1],
            "timestamp": [pd.Timestamp("2025-01-01 10:00:00")],
            "recommended_action": ["ENTER_LONG"],
        })

        actions_df = pd.DataFrame({
            "signal_id": [1],
            "timestamp": [pd.Timestamp("2025-01-01 10:00:00.500")],  # 500 ms
            "user_action": ["EXECUTED"]
        })

        config = TriggerReactionConfig(impulsive_threshold_ms=300, late_threshold_ms=3000)
        records = compute_reaction_records(signals_df, actions_df, config)

        assert len(records) == 1
        assert records[0].category == TriggerReactionCategory.ON_TIME
        assert records[0].reaction_ms == pytest.approx(500.0, abs=1.0)

    def test_compute_reaction_records_late(self):
        """Test: Late Reaktion (> 3 s)."""
        signals_df = pd.DataFrame({
            "signal_id": [1],
            "timestamp": [pd.Timestamp("2025-01-01 10:00:00")],
            "recommended_action": ["ENTER_LONG"],
        })

        actions_df = pd.DataFrame({
            "signal_id": [1],
            "timestamp": [pd.Timestamp("2025-01-01 10:00:10")],  # 10 s
            "user_action": ["EXECUTED"]
        })

        config = TriggerReactionConfig(late_threshold_ms=3000)
        records = compute_reaction_records(signals_df, actions_df, config)

        assert len(records) == 1
        assert records[0].category == TriggerReactionCategory.LATE
        assert records[0].reaction_ms == pytest.approx(10000.0, abs=1.0)

    def test_compute_reaction_records_missed(self):
        """Test: Missed Signal (keine Aktion)."""
        signals_df = pd.DataFrame({
            "signal_id": [1],
            "timestamp": [pd.Timestamp("2025-01-01 10:00:00")],
            "recommended_action": ["ENTER_LONG"],
        })

        actions_df = pd.DataFrame(columns=["signal_id", "timestamp", "user_action"])

        records = compute_reaction_records(signals_df, actions_df)

        assert len(records) == 1
        assert records[0].category == TriggerReactionCategory.MISSED
        assert records[0].reaction_ms is None

    def test_compute_reaction_records_skipped(self):
        """Test: Skipped Signal (bewusst übersprungen)."""
        signals_df = pd.DataFrame({
            "signal_id": [1],
            "timestamp": [pd.Timestamp("2025-01-01 10:00:00")],
            "recommended_action": ["ENTER_LONG"],
        })

        actions_df = pd.DataFrame({
            "signal_id": [1],
            "timestamp": [pd.Timestamp("2025-01-01 10:00:00.100")],
            "user_action": ["SKIPPED"]
        })

        config = TriggerReactionConfig(consider_skipped=True)
        records = compute_reaction_records(signals_df, actions_df, config)

        assert len(records) == 1
        assert records[0].category == TriggerReactionCategory.SKIPPED

    def test_compute_reaction_records_multiple_signals(self):
        """Test: Mehrere Signale mit verschiedenen Kategorien."""
        signals_df = pd.DataFrame({
            "signal_id": [1, 2, 3, 4, 5],
            "timestamp": pd.date_range("2025-01-01 10:00:00", periods=5, freq="1min"),
            "recommended_action": ["ENTER_LONG"] * 5,
        })

        actions_df = pd.DataFrame({
            "signal_id": [1, 2, 4, 5],  # Signal 3 hat keine Aktion
            "timestamp": [
                pd.Timestamp("2025-01-01 10:00:00.100"),   # 100 ms -> IMPULSIVE
                pd.Timestamp("2025-01-01 10:01:00.500"),   # 500 ms -> ON_TIME
                pd.Timestamp("2025-01-01 10:03:10"),       # 10 s -> LATE
                pd.Timestamp("2025-01-01 10:04:00.100"),   # 100 ms, aber SKIPPED
            ],
            "user_action": ["EXECUTED", "EXECUTED", "EXECUTED", "SKIPPED"]
        })

        config = TriggerReactionConfig(
            impulsive_threshold_ms=300,
            late_threshold_ms=3000,
            consider_skipped=True
        )
        records = compute_reaction_records(signals_df, actions_df, config)

        assert len(records) == 5
        assert records[0].category == TriggerReactionCategory.IMPULSIVE
        assert records[1].category == TriggerReactionCategory.ON_TIME
        assert records[2].category == TriggerReactionCategory.MISSED
        assert records[3].category == TriggerReactionCategory.LATE
        assert records[4].category == TriggerReactionCategory.SKIPPED

    def test_summarize_reaction_records(self):
        """Test: Zusammenfassung von Reaktions-Records."""
        # Erstelle künstliche Records
        records = [
            TriggerReactionRecord(
                signal_id=i,
                session_id="TEST",
                signal_timestamp=pd.Timestamp("2025-01-01 10:00:00"),
                first_action_timestamp=pd.Timestamp("2025-01-01 10:00:00.100") if i < 3 else None,
                reaction_ms=100.0 + i * 100 if i < 3 else None,
                category=cat,
            )
            for i, cat in enumerate([
                TriggerReactionCategory.IMPULSIVE,    # 0: 100 ms
                TriggerReactionCategory.ON_TIME,      # 1: 200 ms
                TriggerReactionCategory.LATE,         # 2: 300 ms
                TriggerReactionCategory.MISSED,
                TriggerReactionCategory.SKIPPED,
            ])
        ]

        summary = summarize_reaction_records(records)

        assert summary.count_total == 5
        assert summary.count_impulsive == 1
        assert summary.count_on_time == 1
        assert summary.count_late == 1
        assert summary.count_missed == 1
        assert summary.count_skipped == 1
        assert summary.mean_reaction_ms == pytest.approx(200.0, abs=1.0)  # (100+200+300)/3
        assert summary.median_reaction_ms == pytest.approx(200.0, abs=1.0)

    def test_summarize_reaction_records_empty(self):
        """Test: Leere Records-Liste."""
        summary = summarize_reaction_records([])

        assert summary.count_total == 0
        assert summary.mean_reaction_ms is None

    def test_reaction_records_to_df(self):
        """Test: Konvertierung zu DataFrame."""
        records = [
            TriggerReactionRecord(
                signal_id=1,
                session_id="TEST",
                signal_timestamp=pd.Timestamp("2025-01-01 10:00:00"),
                first_action_timestamp=pd.Timestamp("2025-01-01 10:00:00.100"),
                reaction_ms=100.0,
                category=TriggerReactionCategory.IMPULSIVE,
                symbol="BTCEUR",
            )
        ]

        df = reaction_records_to_df(records)

        assert len(df) == 1
        assert df["signal_id"].iloc[0] == 1
        assert df["category"].iloc[0] == "IMPULSIVE"
        assert df["reaction_ms"].iloc[0] == pytest.approx(100.0)

    def test_reaction_records_to_df_empty(self):
        """Test: Leere Records-Liste zu DataFrame."""
        df = reaction_records_to_df([])

        assert df.empty
        assert "signal_id" in df.columns

    def test_reaction_summary_to_dict(self):
        """Test: Summary zu Dictionary."""
        summary = TriggerReactionSummary(
            count_total=10,
            count_impulsive=2,
            count_on_time=5,
            count_late=2,
            count_missed=1,
            mean_reaction_ms=500.0,
        )

        d = reaction_summary_to_dict(summary)

        assert d["count_total"] == 10
        assert d["count_impulsive"] == 2
        assert d["mean_reaction_ms"] == 500.0

    def test_compute_reaction_records_with_session_id(self):
        """Test: Session-ID wird korrekt übernommen."""
        signals_df = pd.DataFrame({
            "signal_id": [1],
            "timestamp": [pd.Timestamp("2025-01-01 10:00:00")],
            "recommended_action": ["ENTER_LONG"],
        })

        actions_df = pd.DataFrame({
            "signal_id": [1],
            "timestamp": [pd.Timestamp("2025-01-01 10:00:00.100")],
            "user_action": ["EXECUTED"]
        })

        records = compute_reaction_records(signals_df, actions_df, session_id="MY_SESSION")

        assert len(records) == 1
        assert records[0].session_id == "MY_SESSION"
