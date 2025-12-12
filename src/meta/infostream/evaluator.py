"""
InfoStream v1 – Evaluator-Modul.

Führt KI-gestützte Auswertung von IntelEvents durch:
1. Rendert Events als INFO_PACKET (strukturierter Textblock)
2. Ruft KI-Modell mit InfoStream-Systemprompt auf
3. Parst EVAL_PACKAGE und LEARNING_SNIPPET aus der Antwort

Verwendung:
    from src.meta.infostream.evaluator import call_ai_for_event, render_event_as_infopacket
    from openai import OpenAI
    
    client = OpenAI()
    intel_eval, learning = call_ai_for_event(event, client)
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Protocol

from .models import IntelEvent, IntelEval, LearningSnippet

logger = logging.getLogger(__name__)


# =============================================================================
# InfoStream System Prompt
# =============================================================================

INFOSTREAM_SYSTEM_PROMPT = """Du bist der InfoStream- & Datenauswertungsspezialist für das Projekt Peak_Trade.

Peak_Trade ist ein algorithmisches Trading-System mit Fokus auf:
- Systematische Strategien (MA-Crossover, RSI-Reversion, etc.)
- Test-Health-Automation für Qualitätssicherung
- Trigger-Training für Operator-Entscheidungen
- Regime-Detection und Portfolio-Management

Deine Aufgabe ist es, aus INFO_PACKET-Blöcken strukturierte Bewertungen zu erzeugen.

## Eingabe

Du erhältst INFO_PACKETs im folgenden Format:

```
=== INFO_PACKET ===
source: <quelle>
event_id: <id>
category: <kategorie>
severity: <info|warning|error|critical>
created_at: <timestamp>

summary:
  <zusammenfassung>

details:
  - <detail 1>
  - <detail 2>

links:
  - <link1>

tags:
  - <tag1>

status: <new|evaluated|logged>
=== /INFO_PACKET ===
```

## Ausgabe

Antworte IMMER mit exakt zwei Blöcken:

### 1. EVAL_PACKAGE

```
=== EVAL_PACKAGE ===
event_id: <id>
short_eval:
  <1-2 Sätze Bewertung>
key_findings:
  - <Erkenntnis 1>
  - <Erkenntnis 2>
recommendations:
  - <Empfehlung 1>
  - <Empfehlung 2>
risk_assessment:
  level: <none|low|medium|high|critical>
  notes: <Erläuterung>
tags_out:
  - <tag1>
  - <tag2>
=== /EVAL_PACKAGE ===
```

### 2. LEARNING_SNIPPET

```
=== LEARNING_SNIPPET ===
- <Learning 1: Was wurde gelernt?>
- <Learning 2: Was sollte dokumentiert werden?>
- <Learning 3: Was könnte verbessert werden?>
=== /LEARNING_SNIPPET ===
```

## Richtlinien

1. **Sei präzise**: Keine Floskeln, keine unnötigen Wiederholungen.
2. **Sei konstruktiv**: Fokus auf actionable Insights.
3. **Sei kontextbewusst**: Berücksichtige die Kategorie (test_health, macro, etc.).
4. **Sei konsistent**: Halte dich strikt an das Format.

## Beispiel für TestHealth-Event

Wenn ein TestHealth-Report zeigt:
- Health-Score 85/100
- 1 fehlgeschlagener Check
- 2 Trigger-Violations

Dann könnte deine Bewertung sein:
- short_eval: "Guter Health-Score, aber 1 Check fehlgeschlagen. Ursache prüfen."
- key_findings: ["Health-Score im grünen Bereich", "1 Check bedarf Aufmerksamkeit"]
- recommendations: ["Fehlgeschlagenen Check analysieren", "Violations dokumentieren"]
- risk_level: low
- learnings: ["Regelmäßige Checks finden Issues frühzeitig", "Doku für Violations hilfreich"]
"""


# =============================================================================
# Client Protocol (für Dependency Injection)
# =============================================================================

class ChatCompletionClient(Protocol):
    """Protocol für Chat-Completion-Clients (OpenAI-kompatibel)."""
    
    class chat:
        class completions:
            @staticmethod
            def create(
                model: str,
                messages: List[Dict[str, str]],
                **kwargs
            ) -> Any:
                ...


# =============================================================================
# INFO_PACKET Renderer
# =============================================================================

def render_event_as_infopacket(event: IntelEvent) -> str:
    """
    Rendert ein IntelEvent als INFO_PACKET-Textblock.
    
    Parameters
    ----------
    event : IntelEvent
        Das zu rendernde Event
        
    Returns
    -------
    str
        Formatierter INFO_PACKET-Block
        
    Notes
    -----
    Format:
    
    === INFO_PACKET ===
    source: ...
    event_id: ...
    category: ...
    severity: ...
    created_at: ...

    summary:
      <summary-text>

    details:
      - <detail 1>
      - <detail 2>

    links:
      - <link1>

    tags:
      - <tag1>

    status: <event.status>
    === /INFO_PACKET ===
    """
    # created_at als ISO-String
    if hasattr(event.created_at, 'isoformat'):
        created_at_str = event.created_at.isoformat()
    else:
        created_at_str = str(event.created_at)
    
    # Details formatieren
    details_str = "\n".join(f"  - {d}" for d in event.details) if event.details else "  - (keine Details)"
    
    # Links formatieren
    links_str = "\n".join(f"  - {link}" for link in event.links) if event.links else "  - (keine Links)"
    
    # Tags formatieren
    tags_str = "\n".join(f"  - {tag}" for tag in event.tags) if event.tags else "  - (keine Tags)"
    
    packet = f"""=== INFO_PACKET ===
source: {event.source}
event_id: {event.event_id}
category: {event.category}
severity: {event.severity}
created_at: {created_at_str}

summary:
  {event.summary}

details:
{details_str}

links:
{links_str}

tags:
{tags_str}

status: {event.status}
=== /INFO_PACKET ==="""
    
    return packet


# =============================================================================
# Response Parser
# =============================================================================

def parse_eval_package(text: str) -> Dict[str, Any]:
    """
    Parst ein EVAL_PACKAGE aus der KI-Antwort.
    
    Parameters
    ----------
    text : str
        Die vollständige KI-Antwort
        
    Returns
    -------
    Dict[str, Any]
        Geparste Daten mit Keys:
        - event_id: str
        - short_eval: str
        - key_findings: List[str]
        - recommendations: List[str]
        - risk_level: str
        - risk_notes: str
        - tags_out: List[str]
        
    Notes
    -----
    TODO: Robustere Parser-Implementierung mit besserer Error-Handlung.
    v0: Einfache String-Suche und naive Zeilen-Parsing-Logik.
    """
    result: Dict[str, Any] = {
        "event_id": "",
        "short_eval": "",
        "key_findings": [],
        "recommendations": [],
        "risk_level": "none",
        "risk_notes": "",
        "tags_out": [],
    }
    
    # Extrahiere Block zwischen === EVAL_PACKAGE === und === /EVAL_PACKAGE ===
    start_marker = "=== EVAL_PACKAGE ==="
    end_marker = "=== /EVAL_PACKAGE ==="
    
    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        logger.warning("EVAL_PACKAGE-Block nicht gefunden in Antwort")
        return result
    
    block = text[start_idx + len(start_marker):end_idx].strip()
    
    # Naive Zeilen-Parsing
    current_section: Optional[str] = None
    current_list: List[str] = []
    
    for line in block.split("\n"):
        line = line.strip()
        
        # Sektion erkennen
        if line.startswith("event_id:"):
            result["event_id"] = line.split(":", 1)[1].strip()
        elif line.startswith("short_eval:"):
            current_section = "short_eval"
            value = line.split(":", 1)[1].strip()
            if value:
                result["short_eval"] = value
        elif line.startswith("key_findings:"):
            current_section = "key_findings"
            current_list = []
        elif line.startswith("recommendations:"):
            # Speichere vorherige Liste
            if current_section == "key_findings":
                result["key_findings"] = current_list
            current_section = "recommendations"
            current_list = []
        elif line.startswith("risk_assessment:"):
            # Speichere vorherige Liste
            if current_section == "recommendations":
                result["recommendations"] = current_list
            current_section = "risk_assessment"
            current_list = []
        elif line.startswith("level:"):
            result["risk_level"] = line.split(":", 1)[1].strip()
        elif line.startswith("notes:"):
            result["risk_notes"] = line.split(":", 1)[1].strip()
        elif line.startswith("tags_out:"):
            current_section = "tags_out"
            current_list = []
        elif line.startswith("- "):
            # Bullet-Point
            item = line[2:].strip()
            if current_section in ("key_findings", "recommendations", "tags_out"):
                current_list.append(item)
        elif current_section == "short_eval" and line:
            # Multi-line short_eval
            result["short_eval"] = (result["short_eval"] + " " + line).strip()
    
    # Letzte Liste speichern
    if current_section == "key_findings":
        result["key_findings"] = current_list
    elif current_section == "recommendations":
        result["recommendations"] = current_list
    elif current_section == "tags_out":
        result["tags_out"] = current_list
    
    return result


def parse_learning_snippet(text: str) -> List[str]:
    """
    Parst ein LEARNING_SNIPPET aus der KI-Antwort.
    
    Parameters
    ----------
    text : str
        Die vollständige KI-Antwort
        
    Returns
    -------
    List[str]
        Liste der Learning-Zeilen (ohne führendes "- ")
        
    Notes
    -----
    TODO: Robustere Parser-Implementierung.
    v0: Extrahiert alle Zeilen, die mit '-' beginnen, aus dem LEARNING_SNIPPET-Block.
    """
    lines: List[str] = []
    
    # Extrahiere Block
    start_marker = "=== LEARNING_SNIPPET ==="
    end_marker = "=== /LEARNING_SNIPPET ==="
    
    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        logger.warning("LEARNING_SNIPPET-Block nicht gefunden in Antwort")
        return lines
    
    block = text[start_idx + len(start_marker):end_idx].strip()
    
    # Extrahiere Bullet-Points
    for line in block.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            lines.append(line[2:].strip())
    
    return lines


# =============================================================================
# KI-Aufruf
# =============================================================================

def call_ai_for_event(
    event: IntelEvent,
    client: Any,
    model: Optional[str] = None,
) -> Tuple[IntelEval, LearningSnippet]:
    """
    Ruft das KI-Modell für ein Event auf und parst die Antwort.
    
    Parameters
    ----------
    event : IntelEvent
        Das zu bewertende Event
    client : Any
        OpenAI-kompatibler Client mit .chat.completions.create(...)
    model : str, optional
        Modellname. Falls nicht angegeben, wird aus ENV oder Default geladen.
        
    Returns
    -------
    Tuple[IntelEval, LearningSnippet]
        (Bewertung, Learning)
        
    Notes
    -----
    Der Client sollte die OpenAI-API-Struktur haben:
    client.chat.completions.create(model=..., messages=[...])
    
    TODO: Saubere Konfiguration für Modellname und API-Key.
    """
    # Modellname aus Parameter, ENV oder Default
    if model is None:
        model = os.environ.get("INFOSTREAM_MODEL", "gpt-4o-mini")
    
    # INFO_PACKET rendern
    info_packet = render_event_as_infopacket(event)
    
    logger.info(f"Rufe KI-Modell auf für Event: {event.event_id}")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": INFOSTREAM_SYSTEM_PROMPT},
                {"role": "user", "content": info_packet},
            ],
        )
        
        response_text = response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Fehler beim KI-Aufruf: {e}")
        # Fallback: Leere Ergebnisse
        return (
            IntelEval(event_id=event.event_id, short_eval=f"KI-Aufruf fehlgeschlagen: {e}"),
            LearningSnippet(event_id=event.event_id, lines=["KI-Auswertung nicht verfügbar"]),
        )
    
    # Response parsen
    eval_data = parse_eval_package(response_text)
    learning_lines = parse_learning_snippet(response_text)
    
    # Objekte erstellen
    intel_eval = IntelEval(
        event_id=event.event_id,
        short_eval=eval_data.get("short_eval", ""),
        key_findings=eval_data.get("key_findings", []),
        recommendations=eval_data.get("recommendations", []),
        risk_level=eval_data.get("risk_level", "none"),
        risk_notes=eval_data.get("risk_notes", ""),
        tags_out=eval_data.get("tags_out", []),
    )
    
    learning = LearningSnippet(
        event_id=event.event_id,
        lines=learning_lines,
    )
    
    logger.info(f"KI-Auswertung abgeschlossen für {event.event_id}: {len(learning_lines)} Learnings")
    
    return intel_eval, learning


def save_intel_eval(intel_eval: IntelEval, base_dir: Path) -> Path:
    """
    Speichert ein IntelEval als JSON.
    
    Parameters
    ----------
    intel_eval : IntelEval
        Das zu speichernde Eval
    base_dir : Path
        Basis-Verzeichnis, z.B. reports/infostream/evals
        
    Returns
    -------
    Path
        Pfad zur gespeicherten Datei
    """
    base_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = base_dir / f"{intel_eval.event_id}.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(intel_eval.to_dict(), f, indent=2, ensure_ascii=False)
    
    logger.info(f"IntelEval gespeichert: {output_path}")
    return output_path
