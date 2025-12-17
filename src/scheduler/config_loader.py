# src/scheduler/config_loader.py
"""
Peak_Trade Scheduler – Config Loader
=====================================
Lädt Job-Definitionen aus TOML-Dateien.
"""
from __future__ import annotations

from pathlib import Path

from .models import JobDefinition, JobSchedule

# tomllib ist Python 3.11+, tomli ist Fallback
try:
    import tomllib
except ImportError:
    import tomli as tomllib


def load_jobs_from_toml(path: Path) -> list[JobDefinition]:
    """
    Lädt Job-Definitionen aus einer TOML-Datei.

    Args:
        path: Pfad zur TOML-Datei

    Returns:
        Liste von JobDefinition-Objekten

    Raises:
        FileNotFoundError: Wenn die Datei nicht existiert
        ValueError: Bei ungültigem Format

    Example TOML:
        [[job]]
        name = "daily_forward_signals"
        command = "python"
        args = { script = "scripts/run_forward_signals.py", strategy = "ma_crossover" }
        schedule_type = "daily"
        daily_time = "07:30"
        enabled = true
        tags = ["forward", "prod"]
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Job-Config nicht gefunden: {path}")

    with path.open("rb") as f:
        data = tomllib.load(f)

    jobs: list[JobDefinition] = []

    for raw in data.get("job", []):
        # Schedule aufbauen
        schedule = JobSchedule(
            type=raw.get("schedule_type", "once"),
            interval_seconds=raw.get("interval_seconds"),
            daily_time=raw.get("daily_time"),
        )

        # Job-Definition aufbauen
        job = JobDefinition(
            name=raw.get("name", "unnamed_job"),
            command=raw.get("command", "python"),
            args=raw.get("args", {}),
            env=raw.get("env", {}),
            schedule=schedule,
            enabled=raw.get("enabled", True),
            tags=raw.get("tags", []),
            timeout_seconds=raw.get("timeout_seconds", 300),
            description=raw.get("description", ""),
        )
        jobs.append(job)

    return jobs


def validate_job_config(job: JobDefinition) -> list[str]:
    """
    Validiert eine Job-Definition und gibt Warnungen zurück.

    Args:
        job: Job-Definition

    Returns:
        Liste von Warnungen (leer wenn alles ok)
    """
    warnings: list[str] = []

    # Name prüfen
    if not job.name or job.name == "unnamed_job":
        warnings.append("Job hat keinen Namen")

    # Script-Argument prüfen
    if "script" not in job.args:
        warnings.append(f"Job '{job.name}' hat kein 'script' in args")

    # Schedule-Type-spezifische Prüfungen
    if job.schedule.type == "interval" and not job.schedule.interval_seconds:
        warnings.append(f"Job '{job.name}' hat type='interval' aber kein interval_seconds")

    if job.schedule.type == "daily" and not job.schedule.daily_time:
        warnings.append(f"Job '{job.name}' hat type='daily' aber kein daily_time")

    # daily_time Format prüfen
    if job.schedule.daily_time:
        try:
            parts = job.schedule.daily_time.split(":")
            if len(parts) != 2:
                raise ValueError("Ungültiges Format")
            hour, minute = int(parts[0]), int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Ungültige Zeit")
        except (ValueError, IndexError):
            warnings.append(f"Job '{job.name}' hat ungültiges daily_time: {job.schedule.daily_time}")

    return warnings
