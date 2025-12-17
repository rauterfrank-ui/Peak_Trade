# src/scheduler/models.py
"""
Peak_Trade Scheduler – Datenmodelle
====================================
Dataclasses für Jobs, Schedules und Ergebnisse.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

# Schedule-Typen
ScheduleType = Literal["once", "interval", "daily"]


@dataclass
class JobSchedule:
    """
    Schedule-Definition für einen Job.

    Attributes:
        type: Schedule-Typ ("once", "interval", "daily")
        interval_seconds: Intervall in Sekunden (für type="interval")
        daily_time: Uhrzeit im Format "HH:MM" (für type="daily")
        next_run_at: Berechneter nächster Ausführungszeitpunkt (interner Zustand)
        last_run_at: Letzter Ausführungszeitpunkt
    """

    type: ScheduleType = "once"
    interval_seconds: int | None = None
    daily_time: str | None = None
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None


@dataclass
class JobDefinition:
    """
    Definition eines Jobs.

    Attributes:
        name: Eindeutiger Job-Name
        command: Auszuführendes Kommando (z.B. "python")
        args: Argumente als Dict (script, strategy, etc.)
        env: Zusätzliche Umgebungsvariablen
        schedule: Schedule-Definition
        enabled: Ob der Job aktiv ist
        tags: Tags für Filterung
        timeout_seconds: Timeout für Job-Ausführung
        description: Optionale Beschreibung
    """

    name: str
    command: str = "python"
    args: dict[str, Any] = field(default_factory=dict)
    env: dict[str, str] = field(default_factory=dict)
    schedule: JobSchedule = field(default_factory=lambda: JobSchedule(type="once"))
    enabled: bool = True
    tags: list[str] = field(default_factory=list)
    timeout_seconds: int = 300  # 5 Minuten Default
    description: str = ""


@dataclass
class JobResult:
    """
    Ergebnis einer Job-Ausführung.

    Attributes:
        job_name: Name des Jobs
        started_at: Startzeitpunkt
        finished_at: Endzeitpunkt
        return_code: Exit-Code (0 = Erfolg)
        success: Ob der Job erfolgreich war
        stdout: Standard-Output (gekürzt)
        stderr: Standard-Error (gekürzt)
        exception: Exception-Nachricht falls vorhanden
        duration_seconds: Ausführungsdauer
    """

    job_name: str
    started_at: datetime
    finished_at: datetime
    return_code: int
    success: bool
    stdout: str = ""
    stderr: str = ""
    exception: str | None = None
    duration_seconds: float = 0.0

    def __post_init__(self):
        """Berechnet duration_seconds falls nicht gesetzt."""
        if self.duration_seconds == 0.0 and self.started_at and self.finished_at:
            self.duration_seconds = (self.finished_at - self.started_at).total_seconds()
