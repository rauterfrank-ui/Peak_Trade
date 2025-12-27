"""
Tests für Psychologie-Heatmap-Integration in Trigger-Training-Report
=====================================================================

Unit-Tests für die neuen Psychologie-Funktionen in trigger_training_report.py
"""

import pytest
import pandas as pd
from pathlib import Path
from tempfile import TemporaryDirectory

from src.reporting.trigger_training_report import (
    TriggerTrainingEvent,
    TriggerOutcome,
    _determine_cluster_from_tags,
    calculate_psychology_scores_from_events,
    _build_psychology_heatmap_html,
    build_trigger_training_report,
)


class TestDetermineClusterFromTags:
    """Tests für _determine_cluster_from_tags."""

    def test_trend_follow_cluster(self):
        """Test für Trend-Follow-Erkennung."""
        assert _determine_cluster_from_tags(["TREND_FOLLOW", "DISCIPLINE"]) == "trend_follow"
        assert _determine_cluster_from_tags(["trend", "WITH_TREND"]) == "trend_follow"

    def test_counter_trend_cluster(self):
        """Test für Counter-Trend-Erkennung."""
        assert _determine_cluster_from_tags(["COUNTER", "REVERSAL"]) == "counter_trend"

    def test_breakout_cluster(self):
        """Test für Breakout-Erkennung."""
        assert _determine_cluster_from_tags(["BREAKOUT", "FOMO"]) == "breakout"

    def test_exit_cluster(self):
        """Test für Exit-Erkennung."""
        assert _determine_cluster_from_tags(["EXIT", "TAKE_PROFIT"]) == "exit"

    def test_reentry_cluster(self):
        """Test für Re-Entry-Erkennung."""
        assert _determine_cluster_from_tags(["REENTRY", "SCALING"]) == "reentry"

    def test_other_cluster(self):
        """Test für unbekannte Tags."""
        assert _determine_cluster_from_tags(["UNKNOWN", "RANDOM"]) == "other"

    def test_empty_tags(self):
        """Test für leere Tag-Liste."""
        assert _determine_cluster_from_tags([]) == "other"


class TestCalculatePsychologyScoresFromEvents:
    """Tests für calculate_psychology_scores_from_events."""

    def test_empty_events(self):
        """Test für leere Event-Liste."""
        scores = calculate_psychology_scores_from_events([])
        assert scores == {}

    def test_fomo_detection(self):
        """Test für FOMO-Score-Berechnung."""
        events = [
            TriggerTrainingEvent(
                timestamp=pd.Timestamp("2025-01-01 00:00:00"),
                symbol="BTCEUR",
                signal_state=1,
                recommended_action="ENTER_LONG",
                user_action="EXECUTED",
                outcome=TriggerOutcome.FOMO,
                reaction_delay_s=15.0,
                pnl_after_bars=-50.0,
                tags=["BREAKOUT", "FOMO"],
                note="Zu spät",
            )
        ]

        scores = calculate_psychology_scores_from_events(events)

        assert "breakout" in scores
        assert scores["breakout"]["fomo"] > 0.0

    def test_hesitation_detection(self):
        """Test für Zögern-Score-Berechnung."""
        events = [
            TriggerTrainingEvent(
                timestamp=pd.Timestamp("2025-01-01 00:00:00"),
                symbol="BTCEUR",
                signal_state=1,
                recommended_action="ENTER_LONG",
                user_action="",
                outcome=TriggerOutcome.MISSED,
                reaction_delay_s=0.0,
                pnl_after_bars=100.0,
                tags=["TREND_FOLLOW", "HESITATION"],
                note="Verpasst",
            )
        ]

        scores = calculate_psychology_scores_from_events(events)

        assert "trend_follow" in scores
        assert scores["trend_follow"]["hesitation"] > 0.0

    def test_rule_break_detection(self):
        """Test für Regelbruch-Score-Berechnung."""
        events = [
            TriggerTrainingEvent(
                timestamp=pd.Timestamp("2025-01-01 00:00:00"),
                symbol="BTCEUR",
                signal_state=1,
                recommended_action="ENTER_LONG",
                user_action="EXECUTED_WRONG",
                outcome=TriggerOutcome.RULE_BREAK,
                reaction_delay_s=1.0,
                pnl_after_bars=-30.0,
                tags=["COUNTER", "VIOLATION"],  # Klarere Tags ohne "BREAK"
                note="Ohne Setup",
            )
        ]

        scores = calculate_psychology_scores_from_events(events)

        assert "counter_trend" in scores
        assert scores["counter_trend"]["rule_break"] > 0.0

    def test_impulsivity_detection(self):
        """Test für Impulsivitäts-Score-Berechnung."""
        events = [
            TriggerTrainingEvent(
                timestamp=pd.Timestamp("2025-01-01 00:00:00"),
                symbol="BTCEUR",
                signal_state=1,
                recommended_action="ENTER_LONG",
                user_action="EXECUTED",
                outcome=TriggerOutcome.HIT,
                reaction_delay_s=0.5,  # Sehr schnell
                pnl_after_bars=50.0,
                tags=["REENTRY"],
                note="",
            )
        ]

        scores = calculate_psychology_scores_from_events(events)

        assert "reentry" in scores
        assert scores["reentry"]["impulsivity"] > 0.0

    def test_score_normalization(self):
        """Test dass Scores auf 0-3 normalisiert sind."""
        # Viele FOMO-Events generieren
        events = [
            TriggerTrainingEvent(
                timestamp=pd.Timestamp("2025-01-01 00:00:00"),
                symbol="BTCEUR",
                signal_state=1,
                recommended_action="ENTER_LONG",
                user_action="EXECUTED",
                outcome=TriggerOutcome.FOMO,
                reaction_delay_s=15.0,
                pnl_after_bars=-50.0,
                tags=["BREAKOUT"],
                note="",
            )
            for _ in range(10)
        ]

        scores = calculate_psychology_scores_from_events(events)

        # Alle Scores sollten <= 3.0 sein
        for cluster_scores in scores.values():
            for metric_value in cluster_scores.values():
                assert 0.0 <= metric_value <= 3.0


class TestBuildPsychologyHeatmapHtml:
    """Tests für _build_psychology_heatmap_html."""

    def test_empty_scores(self):
        """Test für leere Score-Dictionary."""
        html = _build_psychology_heatmap_html({})

        assert "Psychologie-Heatmap" in html
        assert "Keine Psychologie-Daten verfügbar" in html

    def test_valid_scores(self):
        """Test für valide Scores."""
        scores = {
            "trend_follow": {
                "fomo": 0.5,
                "loss_fear": 1.5,
                "impulsivity": 2.5,
                "hesitation": 0.0,
                "rule_break": 1.0,
            }
        }

        html = _build_psychology_heatmap_html(scores)

        assert "Psychologie-Heatmap" in html
        assert "Trend-Folge Einstiege" in html
        assert "heat-1" in html  # loss_fear=1.5
        assert "heat-2" in html  # impulsivity=2.5

    def test_heat_level_classes(self):
        """Test dass alle Heat-Level-Klassen vorhanden sind."""
        scores = {
            "test": {
                "fomo": 0.0,  # heat-0
                "loss_fear": 1.0,  # heat-1
                "impulsivity": 2.0,  # heat-2
                "hesitation": 3.0,  # heat-3
                "rule_break": 0.0,
            }
        }

        html = _build_psychology_heatmap_html(scores)

        assert "heat-0" in html
        assert "heat-1" in html
        assert "heat-2" in html
        assert "heat-3" in html


class TestBuildTriggerTrainingReportIntegration:
    """Integrations-Tests für den vollständigen Report mit Psychologie-Heatmap."""

    def test_report_with_psychology_heatmap(self):
        """Test dass der Report die Psychologie-Heatmap enthält."""
        events = [
            TriggerTrainingEvent(
                timestamp=pd.Timestamp("2025-01-01 00:00:00"),
                symbol="BTCEUR",
                signal_state=1,
                recommended_action="ENTER_LONG",
                user_action="EXECUTED",
                outcome=TriggerOutcome.FOMO,
                reaction_delay_s=15.0,
                pnl_after_bars=-50.0,
                tags=["BREAKOUT", "FOMO"],
                note="Test",
            ),
            TriggerTrainingEvent(
                timestamp=pd.Timestamp("2025-01-01 00:05:00"),
                symbol="BTCEUR",
                signal_state=1,
                recommended_action="ENTER_LONG",
                user_action="",
                outcome=TriggerOutcome.MISSED,
                reaction_delay_s=0.0,
                pnl_after_bars=100.0,
                tags=["TREND_FOLLOW", "HESITATION"],
                note="Verpasst",
            ),
        ]

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            report_path = build_trigger_training_report(
                events=events,
                output_dir=output_dir,
                session_meta={"session_id": "TEST"},
            )

            assert report_path.exists()

            # Report-Inhalt prüfen
            html_content = report_path.read_text(encoding="utf-8")

            # Grundlegende Report-Elemente
            assert "Trigger Training Report" in html_content
            assert "Outcome Übersicht" in html_content

            # Psychologie-Heatmap-Elemente
            assert "Psychologie-Heatmap" in html_content
            assert "psychology-heatmap" in html_content
            assert "FOMO" in html_content
            assert "Zögern" in html_content

            # Heat-Level-Styles
            assert ".heat-0" in html_content
            assert ".heat-1" in html_content
            assert ".heat-2" in html_content
            assert ".heat-3" in html_content

    def test_report_without_events(self):
        """Test dass der Report auch ohne Events funktioniert."""
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            report_path = build_trigger_training_report(
                events=[],
                output_dir=output_dir,
            )

            assert report_path.exists()
            html_content = report_path.read_text(encoding="utf-8")

            # Sollte trotzdem generiert werden, aber ohne Heatmap
            assert "Trigger Training Report" in html_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
