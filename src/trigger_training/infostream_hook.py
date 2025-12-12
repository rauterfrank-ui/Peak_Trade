"""
InfoStream Integration für Trigger-Training v0

Dieser Hook ermöglicht die automatische Generierung von INFO_PACKETs
nach Trigger-Training-Sessions.

Verwendung:
    from src.trigger_training.infostream_hook import emit_infostream_packet
    
    # Nach Abschluss einer Session
    emit_infostream_packet(
        session_id="abc123",
        session_data=session_dict,
        output_dir="reports/infostream/events/"
    )

Siehe: docs/infostream/README.md
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def generate_event_id(suffix: str = "") -> str:
    """Generiert eine Event-ID im Format INF-YYYYMMDD-HHMMSS-kurzer_name."""
    now = datetime.now()
    date_part = now.strftime("%Y%m%d")
    time_part = now.strftime("%H%M%S")
    short_name = f"trigger_{suffix[:8]}" if suffix else "trigger"
    return f"INF-{date_part}-{time_part}-{short_name}"


def build_info_packet_from_session(
    session_id: str,
    session_data: dict[str, Any],
) -> str:
    """
    Baut ein INFO_PACKET aus Trigger-Training-Session-Daten.
    
    Parameters
    ----------
    session_id : str
        Eindeutige Session-ID
    session_data : dict
        Session-Daten mit Feldern wie:
        - operator_name
        - strategy_name
        - total_triggers
        - decisions_made
        - correct_decisions
        - created_at
        - psychology_tags (optional)
        
    Returns
    -------
    str
        Formatiertes INFO_PACKET
    """
    # Daten extrahieren mit Fallbacks
    operator_name = session_data.get("operator_name", "unknown")
    strategy_name = session_data.get("strategy_name", "unknown")
    total_triggers = session_data.get("total_triggers", 0)
    decisions_made = session_data.get("decisions_made", 0)
    correct_decisions = session_data.get("correct_decisions", 0)
    created_at_str = session_data.get("created_at", datetime.now().isoformat())
    psychology_tags = session_data.get("psychology_tags", [])
    duration_minutes = session_data.get("duration_minutes", 0)
    
    # Accuracy berechnen
    accuracy = (correct_decisions / decisions_made * 100) if decisions_made > 0 else 0.0
    
    # Severity bestimmen
    if accuracy >= 80:
        severity = "info"
    elif accuracy >= 60:
        severity = "warning"
    else:
        severity = "warning"
    
    # Summary erstellen
    summary_text = (
        f"Trigger-Training-Session für {strategy_name} abgeschlossen. "
        f"{decisions_made} Entscheidungen, {accuracy:.0f}% korrekt."
    )
    
    # Details erstellen
    details = [
        f"Session-ID: {session_id}",
        f"Operator: {operator_name}",
        f"Strategy: {strategy_name}",
        f"Total Triggers: {total_triggers}",
        f"Decisions Made: {decisions_made}",
        f"Correct Decisions: {correct_decisions}",
        f"Accuracy: {accuracy:.1f}%",
    ]
    
    if duration_minutes > 0:
        details.append(f"Duration: {duration_minutes:.0f} Minuten")
    
    # Psychology-Tags als Details hinzufügen
    if psychology_tags:
        if isinstance(psychology_tags, str):
            psychology_tags = [t.strip() for t in psychology_tags.split(",")]
        details.append(f"Psychology-Tags: {', '.join(psychology_tags)}")
    
    # Links
    links = [
        f"reports/trigger_training/session_{session_id}.html",
        f"reports/trigger_training/meta/operator_stats_overview.html",
    ]
    
    # Tags
    tags = ["trigger_training", "operator_training", strategy_name]
    if accuracy < 70:
        tags.append("needs_improvement")
    if accuracy >= 90:
        tags.append("excellent")
    if psychology_tags:
        tags.extend([f"psych.{t}" for t in psychology_tags[:3]])
    
    # Event-ID
    event_id = generate_event_id(session_id[:8])
    
    # Timestamp
    try:
        created_at = datetime.fromisoformat(
            created_at_str.replace("Z", "+00:00")
        ).astimezone()
    except (ValueError, AttributeError):
        created_at = datetime.now().astimezone()
    
    # INFO_PACKET formatieren
    details_str = "\n".join(f"  - {d}" for d in details)
    links_str = "\n".join(f"  - {link}" for link in links)
    tags_str = "\n".join(f"  - {tag}" for tag in tags)
    
    packet = f"""=== INFO_PACKET ===
source: trigger_training_sessions
event_id: {event_id}
category: operator_training
severity: {severity}
created_at: {created_at.isoformat()}

summary:
  {summary_text}

details:
{details_str}

links:
{links_str}

tags:
{tags_str}

status: new
=== /INFO_PACKET ==="""
    
    return packet


def emit_infostream_packet(
    session_id: str,
    session_data: dict[str, Any],
    output_dir: Optional[str | Path] = None,
    quiet: bool = False,
) -> Optional[Path]:
    """
    Erzeugt und speichert ein INFO_PACKET für eine Trigger-Training-Session.
    
    Parameters
    ----------
    session_id : str
        Eindeutige Session-ID
    session_data : dict
        Session-Daten (siehe build_info_packet_from_session)
    output_dir : str | Path, optional
        Output-Verzeichnis. Wenn None, wird nur das Paket zurückgegeben.
    quiet : bool
        Wenn True, keine Konsolenausgabe
        
    Returns
    -------
    Path | None
        Pfad zur gespeicherten Datei, oder None wenn nicht gespeichert
    """
    packet = build_info_packet_from_session(session_id, session_data)
    
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        event_id = generate_event_id(session_id[:8])
        filepath = output_path / f"{event_id}.txt"
        filepath.write_text(packet, encoding="utf-8")
        
        if not quiet:
            print(f"✓ InfoStream: INFO_PACKET gespeichert: {filepath}")
        
        return filepath
    
    if not quiet:
        print(packet)
    
    return None


def hook_on_session_complete(
    session_id: str,
    session_data: dict[str, Any],
    auto_emit: bool = True,
    output_dir: str = "reports/infostream/events/",
) -> Optional[str]:
    """
    Hook der nach Abschluss einer Trigger-Training-Session aufgerufen wird.
    
    Dieser Hook kann in bestehende Trigger-Training-Pipelines integriert werden.
    
    Parameters
    ----------
    session_id : str
        Session-ID
    session_data : dict
        Session-Daten
    auto_emit : bool
        Wenn True, wird das Paket automatisch gespeichert
    output_dir : str
        Output-Verzeichnis
        
    Returns
    -------
    str | None
        Das INFO_PACKET als String, oder None bei Fehler
    """
    try:
        packet = build_info_packet_from_session(session_id, session_data)
        
        if auto_emit:
            emit_infostream_packet(
                session_id=session_id,
                session_data=session_data,
                output_dir=output_dir,
                quiet=True,
            )
        
        return packet
        
    except Exception as e:
        print(f"⚠️ InfoStream Hook Fehler: {e}")
        return None


# Beispiel-Integration für Session-Store
def integrate_with_session_store():
    """
    Beispiel-Code für die Integration mit TriggerTrainingSessionStore.
    
    Dieser Code zeigt, wie der Hook in den Session-Store integriert werden kann.
    
    ```python
    from src.trigger_training.session_store import TriggerTrainingSessionStore
    from src.trigger_training.infostream_hook import hook_on_session_complete
    
    store = TriggerTrainingSessionStore()
    
    # Nach Session-Abschluss
    def on_session_end(session_id: str):
        session_data = store.get_session(session_id)
        if session_data:
            hook_on_session_complete(session_id, session_data)
    ```
    """
    pass
