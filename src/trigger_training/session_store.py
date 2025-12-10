"""
Peak_Trade: Trigger Training Session Store
===========================================

Persistentes Speichern und Laden von Trigger-Training-Sessions für Meta-Reports.

Konzept:
    Jedes Mal, wenn ein Offline-Drill läuft, können die Events als Session gespeichert werden.
    Später können mehrere Sessions geladen und in einem Meta-Report aggregiert werden.

Storage-Format:
    JSON-Lines (.jsonl) – eine Session pro Zeile
    Struktur: {"session_id": str, "timestamp": ISO, "events": [Event-Dicts]}

Standard-Pfad:
    live_runs/trigger_training_sessions.jsonl
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Sequence, Tuple

from src.reporting.trigger_training_report import TriggerTrainingEvent, TriggerOutcome


def save_session_to_store(
    session_id: str,
    events: Sequence[TriggerTrainingEvent],
    store_path: Path | str = "live_runs/trigger_training_sessions.jsonl",
) -> None:
    """Speichert eine Trigger-Training-Session im Store.
    
    Parameters
    ----------
    session_id:
        Eindeutige ID der Session (z.B. "DRILL_2025_01_15_MORNING").
    events:
        Liste von TriggerTrainingEvent-Objekten.
    store_path:
        Pfad zur JSON-Lines-Datei (wird bei Bedarf angelegt).
    """
    store_path = Path(store_path)
    store_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Events zu Dicts konvertieren
    event_dicts = []
    for ev in events:
        event_dict = {
            "timestamp": ev.timestamp.isoformat() if hasattr(ev.timestamp, 'isoformat') else str(ev.timestamp),
            "symbol": ev.symbol,
            "signal_state": ev.signal_state,
            "recommended_action": ev.recommended_action,
            "user_action": ev.user_action,
            "outcome": ev.outcome.value if isinstance(ev.outcome, TriggerOutcome) else ev.outcome,
            "reaction_delay_s": ev.reaction_delay_s,
            "pnl_after_bars": ev.pnl_after_bars,
            "tags": ev.tags,
            "note": ev.note,
        }
        event_dicts.append(event_dict)
    
    # Session-Record erstellen
    session_record = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "n_events": len(events),
        "events": event_dicts,
    }
    
    # Append to JSONL file
    with store_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(session_record, ensure_ascii=False) + "\n")


def load_sessions_from_store(
    store_path: Path | str = "live_runs/trigger_training_sessions.jsonl",
    limit: int | None = None,
    session_ids: List[str] | None = None,
) -> List[Tuple[str, List[TriggerTrainingEvent]]]:
    """Lädt Trigger-Training-Sessions aus dem Store.
    
    Parameters
    ----------
    store_path:
        Pfad zur JSON-Lines-Datei.
    limit:
        Optional: Maximale Anzahl an Sessions zu laden (neueste zuerst).
    session_ids:
        Optional: Nur diese Session-IDs laden (falls None, alle laden).
    
    Returns
    -------
    List[Tuple[str, List[TriggerTrainingEvent]]]
        Liste von (session_id, events)-Tupeln.
    """
    store_path = Path(store_path)
    
    if not store_path.exists():
        return []
    
    all_sessions = []
    
    with store_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            record = json.loads(line)
            session_id = record["session_id"]
            
            # Filter nach session_ids
            if session_ids is not None and session_id not in session_ids:
                continue
            
            # Events rekonstruieren
            events = []
            for ev_dict in record["events"]:
                import pandas as pd
                
                event = TriggerTrainingEvent(
                    timestamp=pd.Timestamp(ev_dict["timestamp"]),
                    symbol=ev_dict["symbol"],
                    signal_state=ev_dict["signal_state"],
                    recommended_action=ev_dict["recommended_action"],
                    user_action=ev_dict["user_action"],
                    outcome=TriggerOutcome(ev_dict["outcome"]),
                    reaction_delay_s=ev_dict["reaction_delay_s"],
                    pnl_after_bars=ev_dict["pnl_after_bars"],
                    tags=ev_dict.get("tags", []),
                    note=ev_dict.get("note", ""),
                )
                events.append(event)
            
            all_sessions.append((session_id, events))
    
    # Limit anwenden (neueste zuerst)
    if limit is not None:
        all_sessions = all_sessions[-limit:]
    
    return all_sessions


def list_session_ids(
    store_path: Path | str = "live_runs/trigger_training_sessions.jsonl",
) -> List[str]:
    """Listet alle Session-IDs im Store auf.
    
    Parameters
    ----------
    store_path:
        Pfad zur JSON-Lines-Datei.
    
    Returns
    -------
    List[str]
        Liste von Session-IDs (chronologisch sortiert).
    """
    store_path = Path(store_path)
    
    if not store_path.exists():
        return []
    
    session_ids = []
    
    with store_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            record = json.loads(line)
            session_ids.append(record["session_id"])
    
    return session_ids
