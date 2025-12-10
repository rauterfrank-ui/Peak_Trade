"""Tests für Trigger Training Session Store."""
from pathlib import Path

import pandas as pd

from src.reporting.trigger_training_report import TriggerTrainingEvent, TriggerOutcome
from src.trigger_training.session_store import (
    save_session_to_store,
    load_sessions_from_store,
    list_session_ids,
)


def _make_event(
    ts: str,
    outcome: TriggerOutcome,
    pnl: float = 10.0,
    delay_s: float = 2.0,
) -> TriggerTrainingEvent:
    return TriggerTrainingEvent(
        timestamp=pd.Timestamp(ts),
        symbol="BTCEUR",
        signal_state=1,
        recommended_action="ENTER_LONG",
        user_action="EXECUTED" if outcome == TriggerOutcome.HIT else "SKIPPED",
        outcome=outcome,
        reaction_delay_s=delay_s,
        pnl_after_bars=pnl,
        tags=["test"],
        note="unit test",
    )


def test_save_and_load_single_session(tmp_path: Path) -> None:
    store_path = tmp_path / "sessions.jsonl"
    
    # Session erstellen und speichern
    events = [
        _make_event("2025-01-01T10:00:00Z", TriggerOutcome.HIT),
        _make_event("2025-01-01T10:15:00Z", TriggerOutcome.MISSED),
    ]
    
    save_session_to_store("SESSION_TEST_001", events, store_path)
    
    # Laden
    sessions = load_sessions_from_store(store_path)
    
    assert len(sessions) == 1
    session_id, loaded_events = sessions[0]
    assert session_id == "SESSION_TEST_001"
    assert len(loaded_events) == 2
    assert loaded_events[0].outcome == TriggerOutcome.HIT
    assert loaded_events[1].outcome == TriggerOutcome.MISSED


def test_save_and_load_multiple_sessions(tmp_path: Path) -> None:
    store_path = tmp_path / "sessions.jsonl"
    
    # Mehrere Sessions speichern
    events1 = [_make_event("2025-01-01T10:00:00Z", TriggerOutcome.HIT)]
    events2 = [_make_event("2025-01-02T10:00:00Z", TriggerOutcome.MISSED)]
    events3 = [_make_event("2025-01-03T10:00:00Z", TriggerOutcome.LATE)]
    
    save_session_to_store("SESSION_A", events1, store_path)
    save_session_to_store("SESSION_B", events2, store_path)
    save_session_to_store("SESSION_C", events3, store_path)
    
    # Alle laden
    sessions = load_sessions_from_store(store_path)
    assert len(sessions) == 3
    assert sessions[0][0] == "SESSION_A"
    assert sessions[1][0] == "SESSION_B"
    assert sessions[2][0] == "SESSION_C"


def test_load_with_limit(tmp_path: Path) -> None:
    store_path = tmp_path / "sessions.jsonl"
    
    # 5 Sessions speichern
    for i in range(5):
        events = [_make_event(f"2025-01-0{i+1}T10:00:00Z", TriggerOutcome.HIT)]
        save_session_to_store(f"SESSION_{i}", events, store_path)
    
    # Nur letzte 3 laden
    sessions = load_sessions_from_store(store_path, limit=3)
    assert len(sessions) == 3
    assert sessions[0][0] == "SESSION_2"  # Neueste 3: 2, 3, 4
    assert sessions[1][0] == "SESSION_3"
    assert sessions[2][0] == "SESSION_4"


def test_load_with_session_ids_filter(tmp_path: Path) -> None:
    store_path = tmp_path / "sessions.jsonl"
    
    # 3 Sessions speichern
    save_session_to_store("SESSION_A", [_make_event("2025-01-01T10:00:00Z", TriggerOutcome.HIT)], store_path)
    save_session_to_store("SESSION_B", [_make_event("2025-01-02T10:00:00Z", TriggerOutcome.MISSED)], store_path)
    save_session_to_store("SESSION_C", [_make_event("2025-01-03T10:00:00Z", TriggerOutcome.LATE)], store_path)
    
    # Nur SESSION_A und SESSION_C laden
    sessions = load_sessions_from_store(store_path, session_ids=["SESSION_A", "SESSION_C"])
    assert len(sessions) == 2
    assert sessions[0][0] == "SESSION_A"
    assert sessions[1][0] == "SESSION_C"


def test_list_session_ids(tmp_path: Path) -> None:
    store_path = tmp_path / "sessions.jsonl"
    
    # Leerer Store
    session_ids = list_session_ids(store_path)
    assert session_ids == []
    
    # Sessions hinzufügen
    save_session_to_store("SESSION_X", [_make_event("2025-01-01T10:00:00Z", TriggerOutcome.HIT)], store_path)
    save_session_to_store("SESSION_Y", [_make_event("2025-01-02T10:00:00Z", TriggerOutcome.MISSED)], store_path)
    
    # Liste prüfen
    session_ids = list_session_ids(store_path)
    assert len(session_ids) == 2
    assert "SESSION_X" in session_ids
    assert "SESSION_Y" in session_ids


def test_load_from_nonexistent_store(tmp_path: Path) -> None:
    # Sollte leere Liste zurückgeben, nicht crashen
    store_path = tmp_path / "nonexistent.jsonl"
    sessions = load_sessions_from_store(store_path)
    assert sessions == []

