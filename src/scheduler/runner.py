# src/scheduler/runner.py
"""
Peak_Trade Scheduler – Runner
==============================
Ausführungslogik für Jobs.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from .models import JobDefinition, JobResult, JobSchedule


def compute_next_run_at(
    schedule: JobSchedule,
    *,
    now: datetime | None = None,
    reference: datetime | None = None,
) -> datetime:
    """
    Berechnet den nächsten Ausführungszeitpunkt.

    Args:
        schedule: Schedule-Definition
        now: Aktueller Zeitpunkt (Default: datetime.utcnow())
        reference: Referenz-Zeitpunkt (für interval: letzte Ausführung)

    Returns:
        Nächster Ausführungszeitpunkt
    """
    if now is None:
        now = datetime.utcnow()

    if schedule.type == "once":
        # Sofort fällig, wenn noch nicht gelaufen
        if schedule.last_run_at is None:
            return now
        else:
            # Bereits gelaufen, nie wieder fällig
            return datetime.max

    elif schedule.type == "interval":
        interval = schedule.interval_seconds or 3600  # Default: 1 Stunde

        if reference is not None:
            return reference + timedelta(seconds=interval)
        elif schedule.last_run_at is not None:
            return schedule.last_run_at + timedelta(seconds=interval)
        else:
            # Noch nie gelaufen -> sofort fällig
            return now

    elif schedule.type == "daily":
        # daily_time im Format "HH:MM"
        time_str = schedule.daily_time or "00:00"
        try:
            hour, minute = map(int, time_str.split(":"))
        except (ValueError, AttributeError):
            hour, minute = 0, 0

        # Heute zur angegebenen Zeit
        target_today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Wenn heute schon vorbei, morgen
        if target_today <= now:
            target = target_today + timedelta(days=1)
        else:
            target = target_today

        # Wenn bereits heute gelaufen, morgen
        if schedule.last_run_at is not None:
            last_date = schedule.last_run_at.date()
            if last_date == now.date():
                target = target_today + timedelta(days=1)

        return target

    else:
        # Unbekannter Typ -> sofort
        return now


def is_job_due(job: JobDefinition, *, now: datetime | None = None) -> bool:
    """
    Prüft ob ein Job fällig ist.

    Args:
        job: Job-Definition
        now: Aktueller Zeitpunkt

    Returns:
        True wenn fällig
    """
    if not job.enabled:
        return False

    if now is None:
        now = datetime.utcnow()

    # next_run_at berechnen falls nicht gesetzt
    next_run = job.schedule.next_run_at
    if next_run is None:
        next_run = compute_next_run_at(job.schedule, now=now)

    return next_run <= now


def get_due_jobs(
    jobs: list[JobDefinition],
    *,
    now: datetime | None = None,
) -> list[JobDefinition]:
    """
    Findet alle fälligen Jobs.

    Args:
        jobs: Liste von Job-Definitionen
        now: Aktueller Zeitpunkt

    Returns:
        Liste fälliger Jobs
    """
    if now is None:
        now = datetime.utcnow()

    due: list[JobDefinition] = []

    for job in jobs:
        if is_job_due(job, now=now):
            due.append(job)

    return due


def build_command_args(job: JobDefinition) -> list[str]:
    """
    Baut die Kommandozeilen-Argumente für einen Job.

    Args:
        job: Job-Definition

    Returns:
        Liste von Argumenten für subprocess

    Example:
        args = {"script": "scripts/run_forward_signals.py", "strategy": "ma_crossover"}
        -> ["scripts/run_forward_signals.py", "--strategy", "ma_crossover"]
    """
    cmd_args: list[str] = []

    # Script zuerst
    script = job.args.get("script", "")
    if script:
        cmd_args.append(script)

    # Restliche Argumente
    for key, value in job.args.items():
        if key == "script":
            continue

        # Key als CLI-Flag
        flag = f"--{key.replace('_', '-')}"

        # Wert konvertieren
        if isinstance(value, bool):
            if value:
                cmd_args.append(flag)
        elif value is not None:
            cmd_args.append(flag)
            cmd_args.append(str(value))

    return cmd_args


def run_job(
    job: JobDefinition,
    *,
    dry_run: bool = False,
    cwd: Path | None = None,
) -> JobResult:
    """
    Führt einen Job aus.

    Args:
        job: Job-Definition
        dry_run: Wenn True, nur simulieren
        cwd: Arbeitsverzeichnis

    Returns:
        JobResult mit Ausführungsergebnis
    """
    started_at = datetime.utcnow()

    # Kommando bauen
    if job.command == "python":
        cmd = [sys.executable, *build_command_args(job)]
    else:
        cmd = [job.command, *build_command_args(job)]

    if dry_run:
        # Nur simulieren
        finished_at = datetime.utcnow()
        return JobResult(
            job_name=job.name,
            started_at=started_at,
            finished_at=finished_at,
            return_code=0,
            success=True,
            stdout=f"[DRY-RUN] Would execute: {' '.join(cmd)}",
            stderr="",
        )

    try:
        # Job ausführen
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=job.timeout_seconds,
            cwd=cwd,
        )

        finished_at = datetime.utcnow()

        # Output kürzen (max 2000 Zeichen)
        stdout = result.stdout[:2000] if result.stdout else ""
        stderr = result.stderr[:2000] if result.stderr else ""

        return JobResult(
            job_name=job.name,
            started_at=started_at,
            finished_at=finished_at,
            return_code=result.returncode,
            success=result.returncode == 0,
            stdout=stdout,
            stderr=stderr,
        )

    except subprocess.TimeoutExpired:
        finished_at = datetime.utcnow()
        return JobResult(
            job_name=job.name,
            started_at=started_at,
            finished_at=finished_at,
            return_code=-1,
            success=False,
            stdout="",
            stderr="",
            exception=f"Timeout nach {job.timeout_seconds}s",
        )

    except Exception as e:
        finished_at = datetime.utcnow()
        return JobResult(
            job_name=job.name,
            started_at=started_at,
            finished_at=finished_at,
            return_code=-1,
            success=False,
            stdout="",
            stderr="",
            exception=str(e),
        )


def update_job_schedule_after_run(
    job: JobDefinition,
    result: JobResult,
) -> None:
    """
    Aktualisiert den Schedule nach einer Ausführung.

    Args:
        job: Job-Definition (wird in-place modifiziert)
        result: Ausführungsergebnis
    """
    job.schedule.last_run_at = result.finished_at
    job.schedule.next_run_at = compute_next_run_at(
        job.schedule,
        now=result.finished_at,
    )
