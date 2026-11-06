#!/usr/bin/env python3
"""
Demo-Script: Operator Meta Report aus mehreren Trigger-Training-Sessions generieren.

Dieses Script zeigt, wie man aus mehreren Offline-Drills (oder gespeicherten Event-Daten)
einen aggregierten Meta-Report erstellt.

Usage:
    python scripts/generate_operator_meta_report_demo.py
"""

from pathlib import Path

import pandas as pd

from src.trigger_training.operator_meta_report import build_operator_meta_report
from src.reporting.trigger_training_report import TriggerTrainingEvent, TriggerOutcome


def create_demo_sessions():
    """Erstellt 3 Demo-Sessions mit unterschiedlichen Profilen."""

    # Session 1: Gutes Training (hohe Hit-Rate)
    session1_events = [
        TriggerTrainingEvent(
            timestamp=pd.Timestamp("2025-01-01T10:00:00Z"),
            symbol="BTCEUR",
            signal_state=1,
            recommended_action="ENTER_LONG",
            user_action="EXECUTED",
            outcome=TriggerOutcome.HIT,
            reaction_delay_s=1.2,
            pnl_after_bars=15.0,
            tags=["rule_follow"],
            note="Quick reaction",
        ),
        TriggerTrainingEvent(
            timestamp=pd.Timestamp("2025-01-01T10:15:00Z"),
            symbol="BTCEUR",
            signal_state=1,
            recommended_action="ENTER_LONG",
            user_action="EXECUTED",
            outcome=TriggerOutcome.HIT,
            reaction_delay_s=2.5,
            pnl_after_bars=20.0,
            tags=["rule_follow"],
            note="Good timing",
        ),
        TriggerTrainingEvent(
            timestamp=pd.Timestamp("2025-01-01T10:30:00Z"),
            symbol="BTCEUR",
            signal_state=0,
            recommended_action="EXIT_LONG",
            user_action="EXECUTED",
            outcome=TriggerOutcome.HIT,
            reaction_delay_s=1.8,
            pnl_after_bars=10.0,
            tags=["rule_follow"],
            note="Clean exit",
        ),
        TriggerTrainingEvent(
            timestamp=pd.Timestamp("2025-01-01T10:45:00Z"),
            symbol="BTCEUR",
            signal_state=1,
            recommended_action="ENTER_LONG",
            user_action="",
            outcome=TriggerOutcome.MISSED,
            reaction_delay_s=0.0,
            pnl_after_bars=8.0,
            tags=["missed_opportunity"],
            note="Distracted",
        ),
    ]

    # Session 2: Schlechteres Training (viele MISSED, hoher Pain-Score)
    session2_events = [
        TriggerTrainingEvent(
            timestamp=pd.Timestamp("2025-01-02T10:00:00Z"),
            symbol="BTCEUR",
            signal_state=1,
            recommended_action="ENTER_LONG",
            user_action="",
            outcome=TriggerOutcome.MISSED,
            reaction_delay_s=0.0,
            pnl_after_bars=120.0,
            tags=["missed_opportunity"],
            note="Big miss - looking at phone",
        ),
        TriggerTrainingEvent(
            timestamp=pd.Timestamp("2025-01-02T10:15:00Z"),
            symbol="BTCEUR",
            signal_state=-1,
            recommended_action="ENTER_SHORT",
            user_action="",
            outcome=TriggerOutcome.MISSED,
            reaction_delay_s=0.0,
            pnl_after_bars=95.0,
            tags=["missed_opportunity"],
            note="Missed again",
        ),
        TriggerTrainingEvent(
            timestamp=pd.Timestamp("2025-01-02T10:30:00Z"),
            symbol="BTCEUR",
            signal_state=1,
            recommended_action="ENTER_LONG",
            user_action="EXECUTED",
            outcome=TriggerOutcome.LATE,
            reaction_delay_s=8.2,
            pnl_after_bars=60.0,
            tags=["late_entry"],
            note="Too slow, hesitated",
        ),
        TriggerTrainingEvent(
            timestamp=pd.Timestamp("2025-01-02T10:45:00Z"),
            symbol="BTCEUR",
            signal_state=1,
            recommended_action="ENTER_LONG",
            user_action="EXECUTED",
            outcome=TriggerOutcome.HIT,
            reaction_delay_s=2.1,
            pnl_after_bars=25.0,
            tags=["rule_follow"],
            note="Finally focused",
        ),
    ]

    # Session 3: Gemischt mit emotionalen Trades
    session3_events = [
        TriggerTrainingEvent(
            timestamp=pd.Timestamp("2025-01-03T10:00:00Z"),
            symbol="BTCEUR",
            signal_state=1,
            recommended_action="ENTER_LONG",
            user_action="EXECUTED",
            outcome=TriggerOutcome.HIT,
            reaction_delay_s=2.8,
            pnl_after_bars=18.0,
            tags=["rule_follow"],
            note="Good start",
        ),
        TriggerTrainingEvent(
            timestamp=pd.Timestamp("2025-01-03T10:15:00Z"),
            symbol="BTCEUR",
            signal_state=-1,
            recommended_action="ENTER_SHORT",
            user_action="EXECUTED_FOMO",
            outcome=TriggerOutcome.FOMO,
            reaction_delay_s=0.3,
            pnl_after_bars=-12.0,
            tags=[],
            note="Jumped in too fast, emotional",
        ),
        TriggerTrainingEvent(
            timestamp=pd.Timestamp("2025-01-03T10:30:00Z"),
            symbol="BTCEUR",
            signal_state=1,
            recommended_action="ENTER_LONG",
            user_action="EXECUTED_OVERSIZE",
            outcome=TriggerOutcome.RULE_BREAK,
            reaction_delay_s=1.5,
            pnl_after_bars=45.0,
            tags=[],
            note="Position 2x max size - revenge trading",
        ),
        TriggerTrainingEvent(
            timestamp=pd.Timestamp("2025-01-03T10:45:00Z"),
            symbol="BTCEUR",
            signal_state=0,
            recommended_action="EXIT_LONG",
            user_action="EXECUTED",
            outcome=TriggerOutcome.HIT,
            reaction_delay_s=1.9,
            pnl_after_bars=5.0,
            tags=["rule_follow"],
            note="Back to discipline",
        ),
        TriggerTrainingEvent(
            timestamp=pd.Timestamp("2025-01-03T11:00:00Z"),
            symbol="BTCEUR",
            signal_state=1,
            recommended_action="ENTER_LONG",
            user_action="",
            outcome=TriggerOutcome.MISSED,
            reaction_delay_s=0.0,
            pnl_after_bars=32.0,
            tags=["missed_opportunity"],
            note="Tired, took break",
        ),
    ]

    return [
        ("SESSION_GOOD_2025_01_01", session1_events),
        ("SESSION_BAD_2025_01_02", session2_events),
        ("SESSION_MIXED_2025_01_03", session3_events),
    ]


def main():
    print("[INFO] Generating Operator Meta Report (Demo)...")

    # 1. Demo-Sessions erstellen
    sessions = create_demo_sessions()
    print(f"[INFO] Created {len(sessions)} demo sessions")

    # 2. Sessions im Store speichern (optional, für Demo-Zwecke)
    from src.trigger_training.session_store import save_session_to_store

    store_path = Path("live_runs/trigger_training_sessions_demo.jsonl")
    for session_id, events in sessions:
        save_session_to_store(session_id, events, store_path)
    print(f"[INFO] Sessions gespeichert in: {store_path}")

    # 3. Output-Pfad
    output_path = Path("reports/trigger_training/meta/operator_stats_overview_demo.html")

    # 4. Report generieren
    result_path = build_operator_meta_report(sessions, output_path)

    print(f"[SUCCESS] Meta-Report generiert: {result_path}")
    print(f"[INFO] Öffne im Browser: file://{result_path.absolute()}")


if __name__ == "__main__":
    main()
