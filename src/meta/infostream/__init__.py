"""
InfoStream v1 – Vollautomatisiertes Informationsverarbeitungssystem für Peak_Trade.

Dieses Modul definiert die Kern-Datenstrukturen und Komponenten für den InfoStream:
- IntelEvent: High-level Informations-Event aus verschiedenen Quellen
- InfoPacket: Container für Routing durch das System
- LearningSnippet: Normalisierte Lerneinheit für Knowledge-Base
- IntelEval: KI-Auswertung eines Events (EVAL_PACKAGE)

Komponenten:
- collector: Sammelt Events aus verschiedenen Quellen (TestHealth, TriggerTraining, etc.)
- evaluator: KI-gestützte Auswertung von Events
- router: Schreibt Learnings in das zentrale Learning-Log
- run_cycle: Orchestrierung des vollständigen InfoStream-Zyklus

Verwendung:
    from src.meta.infostream import IntelEvent, InfoPacket, LearningSnippet, IntelEval
    from src.meta.infostream.run_cycle import run_infostream_cycle

    # Manuell ein Event erstellen
    event = IntelEvent(
        source="test_health_automation",
        category="test_automation",
        severity="info",
        summary="Nightly Health-Check erfolgreich.",
        tags=["test_health", "nightly"],
    )

    # Vollständigen Zyklus ausführen
    run_infostream_cycle(project_root=Path("."))
"""

from .models import IntelEvent, InfoPacket, LearningSnippet, IntelEval

__all__ = [
    "IntelEvent",
    "InfoPacket",
    "LearningSnippet",
    "IntelEval",
]
