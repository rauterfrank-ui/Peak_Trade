"""
InfoStream v1 – Core Models.

Definiert die Kern-Datenstrukturen für den InfoStream:

1. IntelEvent: Semantische Einheit einer Information (z.B. "Fed senkt Zinsen")
2. InfoPacket: Container für Routing durch das System (Event + Metadaten)
3. LearningSnippet: Normalisierte Lerneinheit für Knowledge-Base/Docs
4. IntelEval: KI-Auswertung eines Events (EVAL_PACKAGE)

Alle Modelle unterstützen JSON-freundliche Serialisierung via to_dict()/from_dict().
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional


def _now_utc() -> datetime:
    """Helper für konsistente UTC-Timestamps."""
    return datetime.now(timezone.utc)


def _generate_id(prefix: str) -> str:
    """Erzeugt eine kurze, gut lesbare ID mit Prefix."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# Type aliases für bessere Lesbarkeit
SeverityLevel = Literal["info", "warning", "error", "critical"]
EventStatus = Literal["new", "evaluated", "logged"]
RiskLevel = Literal["none", "low", "medium", "high", "critical"]


@dataclass
class IntelEvent:
    """
    High-level Informations-Event, produziert von InfoStream-Quellen
    (z.B. GlobalMacro, MarketPrognose, TestHealth, Automation-Reports, ...).

    Das ist die semantische Einheit, die du im Kopf hast, wenn du sagst:
    "Das ist ein wichtiges INFO_PACKET".

    Attributes:
        event_id: Eindeutige ID (z.B. "INF-20251211_143920_daily_quick")
        created_at: Erstellungszeitpunkt (UTC oder ISO-String)
        source: Wer liefert die Info? z.B. "test_health_automation"
        category: Kategorie z.B. "test_automation", "macro", "operator_training"
        severity: Schweregrad ("info", "warning", "error", "critical")
        summary: 1–3 Sätze, warum das wichtig ist
        details: Liste von Detail-Punkten
        links: Liste von relevanten Links/Pfaden
        tags: Freie Tags, z.B. ["test_health", "nightly"]
        status: Lebenszyklus-Status ("new", "evaluated", "logged")

        # Legacy-Felder für Rückwärtskompatibilität
        topic: Kurzer Titel (deprecated, use summary)
        importance: 1=low, 5=kritisch (deprecated, use severity)
        payload: Optionaler Roh-Payload
    """

    event_id: str = field(default_factory=lambda: _generate_id("INF"))
    created_at: datetime = field(default_factory=_now_utc)

    # Wer liefert die Info?
    source: str = "unknown"

    # Kategorie
    category: str = "general"

    # Severity-Level
    severity: SeverityLevel = "info"

    # Worum geht es?
    summary: str = ""

    # Details als Liste
    details: List[str] = field(default_factory=list)

    # Relevante Links
    links: List[str] = field(default_factory=list)

    # Freie Tags
    tags: List[str] = field(default_factory=list)

    # Status im Lebenszyklus
    status: EventStatus = "new"

    # Legacy-Felder
    topic: str = ""
    importance: int = 3
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """JSON-freundliche Repräsentation (z.B. für JSON/HTML/Reports)."""
        data = asdict(self)
        if isinstance(self.created_at, datetime):
            data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> IntelEvent:
        """Rekonstruiert ein IntelEvent aus einem Dict."""
        data = dict(data)
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            data["created_at"] = datetime.fromisoformat(created_at)
        return cls(**data)


@dataclass
class IntelEval:
    """
    KI-Auswertung eines IntelEvents (EVAL_PACKAGE).

    Enthält die strukturierte Bewertung durch das KI-Modell.

    Attributes:
        event_id: Referenz zum ursprünglichen Event
        short_eval: Kurze Bewertung (1-2 Sätze)
        key_findings: Liste der wichtigsten Erkenntnisse
        recommendations: Liste von Handlungsempfehlungen
        risk_level: Risiko-Einschätzung ("none", "low", "medium", "high", "critical")
        risk_notes: Erläuterungen zur Risiko-Einschätzung
        tags_out: Tags, die das KI-Modell vorschlägt
    """

    event_id: str = ""
    short_eval: str = ""
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_level: RiskLevel = "none"
    risk_notes: str = ""
    tags_out: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """JSON-freundliche Repräsentation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> IntelEval:
        """Rekonstruiert ein IntelEval aus einem Dict."""
        return cls(**data)


@dataclass
class InfoPacket:
    """
    Container, der ein IntelEvent durch das InfoStream-System routet.

    Typische Reise:
    1. Quelle erzeugt IntelEvent
    2. Wir packen es in ein InfoPacket (mit Channel/Meta)
    3. Dashboard zeigt InfoPackets an
    4. KI-Evaluator verarbeitet InfoPacket → LearningSnippet

    Attributes:
        packet_id: Eindeutige ID (auto-generiert)
        created_at: Erstellungszeitpunkt (UTC)
        intel_event: Das eigentliche fachliche Event
        channel: Logischer Kanal, z.B. "GLOBAL_MACRO_DAILY", "TEST_HEALTH_NIGHTLY"
        status: Lebenszyklus-Status ("new", "in_review", "processed")
        meta: Beliebige Zusatzinfos (Run-IDs, Verweise, UI-Metadaten)
    """

    packet_id: str = field(default_factory=lambda: _generate_id("packet"))
    created_at: datetime = field(default_factory=_now_utc)

    # Das eigentliche fachliche Event
    intel_event: IntelEvent = field(default_factory=IntelEvent)

    # Logischer Kanal / Stream
    channel: str = "default"

    # Lebenszyklus-Status im InfoStream
    status: Literal["new", "in_review", "processed"] = "new"

    # Beliebige Zusatzinformationen
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """JSON-freundliche Repräsentation für Speicherung/Transport."""
        return {
            "packet_id": self.packet_id,
            "created_at": self.created_at.isoformat(),
            "intel_event": self.intel_event.to_dict(),
            "channel": self.channel,
            "status": self.status,
            "meta": self.meta,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InfoPacket:
        """Rekonstruiert ein InfoPacket aus einem Dict."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        intel_event_data = data.get("intel_event", {})
        intel_event = IntelEvent.from_dict(intel_event_data)

        return cls(
            packet_id=data.get("packet_id") or _generate_id("packet"),
            created_at=created_at or _now_utc(),
            intel_event=intel_event,
            channel=data.get("channel", "default"),
            status=data.get("status", "new"),
            meta=data.get("meta", {}),
        )


@dataclass
class LearningSnippet:
    """
    Normalisierte 'Lerneinheit', erzeugt von KI-Evaluatoren aus InfoPackets.

    Das ist das Objekt, das später in deine Knowledge-Base, Docs oder
    Mindmap übernommen werden kann.

    Attributes:
        event_id: Verweis zurück auf das Event (primary key für Learning-Log)
        lines: Liste von Bullet-Point-Zeilen
        snippet_id: Eindeutige ID (auto-generiert, für Persistenz)
        created_at: Erstellungszeitpunkt (UTC)
        source_packet_id: Verweis zurück auf das InfoPacket (legacy)
        topic: Kurzbeschreibung / Kategorie
        content: Kanonischer Text für Docs/Knowledge-Base
        tags: Freie Tags, z.B. ["macro", "liquidity", "learning"]
        quality_score: Optionaler Qualitäts-Score (0..1)
        extra: Zusatzdaten (Modellname, Prompt, Quellen-Link)
    """

    # Primary: event_id + lines für Learning-Log
    event_id: str = ""
    lines: List[str] = field(default_factory=list)

    # Auto-generated
    snippet_id: str = field(default_factory=lambda: _generate_id("learn"))
    created_at: datetime = field(default_factory=_now_utc)

    # Legacy: Verweis zurück auf das InfoPacket
    source_packet_id: str = ""

    # Kurzbeschreibung / Kategorie
    topic: str = ""

    # Kanonischer Text
    content: str = ""

    # Freie Tags
    tags: List[str] = field(default_factory=list)

    # Optional: Qualitäts-Score (0..1) oder None
    quality_score: Optional[float] = None

    # Zusatzdaten
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_markdown_block(self) -> str:
        """
        Erzeugt einen Markdown-Block für das Learning-Log.

        Returns:
            str: Formatierter Markdown-Block

        Beispiel:
            ### INF-20251211_143920_daily_quick
            - Punkt 1
            - Punkt 2
        """
        lines_md = (
            "\n".join(f"- {line}" for line in self.lines) if self.lines else "- (keine Learnings)"
        )
        return f"### {self.event_id}\n{lines_md}\n"

    def to_dict(self) -> Dict[str, Any]:
        """JSON-freundliche Repräsentation für Speicherung/Reports."""
        data = asdict(self)
        if isinstance(self.created_at, datetime):
            data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LearningSnippet:
        """Rekonstruiert einen LearningSnippet aus einem Dict."""
        data = dict(data)
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            data["created_at"] = datetime.fromisoformat(created_at)
        return cls(**data)
