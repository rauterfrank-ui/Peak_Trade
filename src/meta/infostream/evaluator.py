"""
InfoStream v1 – Evaluator-Modul.

Führt KI-gestützte Auswertung von IntelEvents durch:
1. Rendert Events als INFO_PACKET (strukturierter Textblock)
2. Ruft KI-Modell mit InfoStream-Systemprompt auf
3. Parst EVAL_PACKAGE und LEARNING_SNIPPET aus der Antwort

Verwendung:
    from src.meta.infostream.evaluator import call_ai_for_event, render_event_as_infopacket
    from src.ai_orchestration.model_client import create_model_client

    client = create_model_client("live")
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

DEFAULT_INFOSTREAM_MODEL = "gpt-4o-mini"
_ENV_INFOSTREAM_MODEL = "INFOSTREAM_MODEL"
_VALID_RISK_LEVELS = frozenset({"none", "low", "medium", "high", "critical"})

_EVAL_START = "=== EVAL_PACKAGE ==="
_EVAL_END = "=== /EVAL_PACKAGE ==="
_LEARN_START = "=== LEARNING_SNIPPET ==="
_LEARN_END = "=== /LEARNING_SNIPPET ==="


def resolve_infostream_model(explicit: Optional[str] = None) -> str:
    """
    Modell-ID für InfoStream-KI-Aufrufe.

    Reihenfolge: explizites Argument → :envvar:`INFOSTREAM_MODEL` →
    :data:`DEFAULT_INFOSTREAM_MODEL`.
    """
    if explicit is not None and str(explicit).strip():
        return str(explicit).strip()
    env = os.environ.get(_ENV_INFOSTREAM_MODEL, "").strip()
    return env if env else DEFAULT_INFOSTREAM_MODEL


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
            def create(model: str, messages: List[Dict[str, str]], **kwargs) -> Any: ...


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
    if hasattr(event.created_at, "isoformat"):
        created_at_str = event.created_at.isoformat()
    else:
        created_at_str = str(event.created_at)

    # Details formatieren
    details_str = (
        "\n".join(f"  - {d}" for d in event.details) if event.details else "  - (keine Details)"
    )

    # Links formatieren
    links_str = (
        "\n".join(f"  - {link}" for link in event.links) if event.links else "  - (keine Links)"
    )

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


def _extract_tagged_block(text: str, start_marker: str, end_marker: str) -> Optional[str]:
    """Erster vollständiger Block zwischen Start- und End-Marker (End nur nach Start)."""
    start_idx = text.find(start_marker)
    if start_idx == -1:
        return None
    search_from = start_idx + len(start_marker)
    end_idx = text.find(end_marker, search_from)
    if end_idx == -1:
        return None
    return text[search_from:end_idx].strip()


def _strip_outer_markdown_fence(block: str) -> str:
    """Entfernt optionales äußeres ``` … ```, falls das Modell den Block einrahmt."""
    b = block.strip()
    if not b.startswith("```"):
        return b
    first_nl = b.find("\n")
    if first_nl == -1:
        return b
    inner = b[first_nl + 1 :].rstrip()
    if inner.endswith("```"):
        inner = inner[:-3].rstrip()
    return inner


def _normalize_risk_level(raw: str) -> str:
    s = (raw or "").strip().lower()
    return s if s in _VALID_RISK_LEVELS else "none"


def _bullet_payload(line: str) -> Optional[str]:
    """Liefert Listeneintrag ohne Präfix oder ``None``."""
    s = line.strip()
    for prefix in ("- ", "* ", "• "):
        if s.startswith(prefix):
            return s[len(prefix) :].strip()
    return None


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
    - Erster vollständiger ``EVAL_PACKAGE``-Block; End-Marker nur nach dem Start-Marker.
    - Optionale Markdown-Codefences um den Block werden entfernt.
    - ``risk_level`` wird auf ``none|low|medium|high|critical`` normalisiert.
    - Listeneinträge unterstützen ``- ``, ``* `` und ``• ``.
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

    raw_block = _extract_tagged_block(text, _EVAL_START, _EVAL_END)
    if raw_block is None:
        logger.warning("EVAL_PACKAGE-Block nicht gefunden in Antwort")
        return result

    block = _strip_outer_markdown_fence(raw_block)
    current_section: Optional[str] = None
    current_list: List[str] = []

    def flush_list() -> None:
        if current_section == "key_findings":
            result["key_findings"] = list(current_list)
        elif current_section == "recommendations":
            result["recommendations"] = list(current_list)
        elif current_section == "tags_out":
            result["tags_out"] = list(current_list)

    for raw_line in block.splitlines():
        line_stripped = raw_line.strip()

        if line_stripped.startswith("event_id:"):
            flush_list()
            current_list = []
            result["event_id"] = line_stripped.split(":", 1)[1].strip()
            current_section = None
        elif line_stripped.startswith("short_eval:"):
            flush_list()
            current_list = []
            current_section = "short_eval"
            rest = line_stripped.split(":", 1)[1].strip()
            if rest:
                result["short_eval"] = rest
        elif line_stripped.startswith("key_findings:"):
            flush_list()
            current_section = "key_findings"
            current_list = []
        elif line_stripped.startswith("recommendations:"):
            flush_list()
            current_section = "recommendations"
            current_list = []
        elif line_stripped.startswith("risk_assessment:"):
            flush_list()
            current_section = "risk_assessment"
            current_list = []
        elif line_stripped.startswith("tags_out:"):
            flush_list()
            current_section = "tags_out"
            current_list = []
        elif current_section == "risk_assessment" and line_stripped.startswith("level:"):
            result["risk_level"] = _normalize_risk_level(line_stripped.split(":", 1)[1])
        elif current_section == "risk_assessment" and line_stripped.startswith("notes:"):
            result["risk_notes"] = line_stripped.split(":", 1)[1].strip()
        else:
            item = _bullet_payload(raw_line)
            if item is not None and current_section in (
                "key_findings",
                "recommendations",
                "tags_out",
            ):
                current_list.append(item)
            elif current_section == "short_eval" and line_stripped:
                result["short_eval"] = (result["short_eval"] + " " + line_stripped).strip()

    flush_list()
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
        Liste der Learning-Zeilen (ohne Bullet-Präfix)

    Notes
    -----
    - Erster vollständiger Block; Fences werden wie bei ``parse_eval_package`` entfernt.
    - Bullets: ``- ``, ``* ``, ``• ``.
    """
    raw_block = _extract_tagged_block(text, _LEARN_START, _LEARN_END)
    if raw_block is None:
        logger.warning("LEARNING_SNIPPET-Block nicht gefunden in Antwort")
        return []

    block = _strip_outer_markdown_fence(raw_block)
    lines: List[str] = []
    for raw_line in block.splitlines():
        item = _bullet_payload(raw_line)
        if item is not None:
            lines.append(item)

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
        ModelClient (complete(request)); single egress via ai_orchestration.
    model : str, optional
        Modellname. Falls nicht angegeben, wird aus ENV oder Default geladen.

    Returns
    -------
    Tuple[IntelEval, LearningSnippet]
        (Bewertung, Learning)

    Notes
    -----
    ModelClient aus ai_orchestration (client.complete(ModelRequest(...))).
    Modell: Parameter ``model`` oder Umgebungsvariable ``INFOSTREAM_MODEL`` oder
    ``DEFAULT_INFOSTREAM_MODEL`` (``gpt-4o-mini``). API-Credentials verwaltet der Client.
    """
    model = resolve_infostream_model(model)

    # INFO_PACKET rendern
    info_packet = render_event_as_infopacket(event)

    logger.info(f"Rufe KI-Modell auf für Event: {event.event_id}")

    try:
        from src.ai_orchestration.model_client import ModelRequest

        req = ModelRequest(
            model_id=model,
            messages=[
                {"role": "system", "content": INFOSTREAM_SYSTEM_PROMPT},
                {"role": "user", "content": info_packet},
            ],
        )
        resp = client.complete(req)
        response_text = resp.content

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

    logger.info(
        f"KI-Auswertung abgeschlossen für {event.event_id}: {len(learning_lines)} Learnings"
    )

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
