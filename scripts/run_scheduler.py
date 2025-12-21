#!/usr/bin/env python3
"""
Peak_Trade Scheduler
=====================
Leichtgewichtiger CLI-Scheduler für automatisierte Jobs.

Features:
- Lädt Jobs aus TOML-Config
- Unterstützt Schedule-Typen: once, interval, daily
- Tag-basiertes Filtern
- Dry-Run-Modus
- Integration mit Registry & Notifications

Usage:
    # Scheduler dauerhaft laufen lassen
    python scripts/run_scheduler.py --config config/scheduler/jobs.toml

    # Einmal fällige Jobs ausführen (z.B. via cron)
    python scripts/run_scheduler.py --config config/scheduler/jobs.toml --once

    # Dry-Run (nur anzeigen)
    python scripts/run_scheduler.py --config config/scheduler/jobs.toml --once --dry-run

    # Nur bestimmte Tags
    python scripts/run_scheduler.py --config config/scheduler/jobs.toml --include-tags daily,prod
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scheduler import (
    JobDefinition,
    JobResult,
    load_jobs_from_toml,
    get_due_jobs,
    run_job,
    compute_next_run_at,
)
from src.scheduler.config_loader import validate_job_config
from src.scheduler.runner import update_job_schedule_after_run

# Optionale Imports für Registry & Notifications
try:
    from src.core.experiments import log_scheduler_job_run

    REGISTRY_AVAILABLE = True
except ImportError:
    REGISTRY_AVAILABLE = False

try:
    from src.notifications import Alert, ConsoleNotifier, FileNotifier, CombinedNotifier

    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False


# Globaler Flag für graceful shutdown
_shutdown_requested = False


def signal_handler(signum, frame):
    """Handler für SIGINT/SIGTERM."""
    global _shutdown_requested
    print("\n[SCHEDULER] Shutdown angefordert...")
    _shutdown_requested = True


def parse_args(argv=None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Scheduler - Automatisierte Job-Ausführung",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scheduler dauerhaft laufen lassen
  python scripts/run_scheduler.py --config config/scheduler/jobs.toml

  # Einmal fällige Jobs ausführen
  python scripts/run_scheduler.py --config config/scheduler/jobs.toml --once

  # Dry-Run
  python scripts/run_scheduler.py --config config/scheduler/jobs.toml --once --dry-run

  # Nur daily-Jobs
  python scripts/run_scheduler.py --include-tags daily
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/scheduler/jobs.toml",
        help="Pfad zur Job-Config (default: config/scheduler/jobs.toml)",
    )

    parser.add_argument(
        "--poll-interval",
        type=int,
        default=30,
        help="Zeit in Sekunden zwischen Checks (default: 30)",
    )

    parser.add_argument(
        "--once", action="store_true", help="Nur einmal fällige Jobs ausführen, dann beenden"
    )

    parser.add_argument(
        "--include-tags",
        type=str,
        default=None,
        help="Nur Jobs mit diesen Tags ausführen (komma-separiert)",
    )

    parser.add_argument(
        "--exclude-tags",
        type=str,
        default=None,
        help="Jobs mit diesen Tags ausschließen (komma-separiert)",
    )

    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen was ausgeführt würde")

    parser.add_argument("--verbose", "-v", action="store_true", help="Ausführliche Ausgabe")

    parser.add_argument("--no-registry", action="store_true", help="Kein Logging in die Registry")

    parser.add_argument("--no-alerts", action="store_true", help="Keine Alerts senden")

    parser.add_argument(
        "--alert-log", type=str, default="logs/scheduler_alerts.log", help="Pfad zur Alert-Logdatei"
    )

    return parser.parse_args(argv)


def filter_jobs_by_tags(
    jobs: List[JobDefinition],
    include_tags: Optional[Set[str]] = None,
    exclude_tags: Optional[Set[str]] = None,
) -> List[JobDefinition]:
    """Filtert Jobs nach Tags."""
    filtered = []

    for job in jobs:
        job_tags = set(job.tags)

        # Include-Filter
        if include_tags:
            if not job_tags.intersection(include_tags):
                continue

        # Exclude-Filter
        if exclude_tags:
            if job_tags.intersection(exclude_tags):
                continue

        filtered.append(job)

    return filtered


def format_job_status(job: JobDefinition, now: datetime) -> str:
    """Formatiert den Status eines Jobs."""
    next_run = job.schedule.next_run_at or compute_next_run_at(job.schedule, now=now)
    status = "ENABLED" if job.enabled else "DISABLED"

    if next_run == datetime.max:
        next_str = "never"
    elif next_run <= now:
        next_str = "NOW"
    else:
        delta = next_run - now
        if delta.total_seconds() < 60:
            next_str = f"in {int(delta.total_seconds())}s"
        elif delta.total_seconds() < 3600:
            next_str = f"in {int(delta.total_seconds() / 60)}m"
        elif delta.total_seconds() < 86400:
            next_str = f"in {int(delta.total_seconds() / 3600)}h"
        else:
            next_str = f"in {int(delta.total_seconds() / 86400)}d"

    return f"{job.name:<30} {status:<10} {job.schedule.type:<10} next={next_str}"


def print_job_summary(jobs: List[JobDefinition], now: datetime) -> None:
    """Druckt eine Übersicht aller Jobs."""
    print("\n" + "=" * 70)
    print("JOB SUMMARY")
    print("=" * 70)

    enabled_count = sum(1 for j in jobs if j.enabled)
    print(f"Total: {len(jobs)} jobs ({enabled_count} enabled)")
    print("-" * 70)

    for job in jobs:
        print(f"  {format_job_status(job, now)}")

    print("=" * 70 + "\n")


def create_notifier(args):
    """Erstellt den Notifier basierend auf Args."""
    if not NOTIFICATIONS_AVAILABLE or args.no_alerts:
        return None

    notifiers = [ConsoleNotifier()]

    if args.alert_log:
        alert_log_path = Path(args.alert_log)
        alert_log_path.parent.mkdir(parents=True, exist_ok=True)
        notifiers.append(FileNotifier(alert_log_path))

    return CombinedNotifier(notifiers)


def send_job_alert(notifier, result: JobResult, level: str = "info") -> None:
    """Sendet Alert für Job-Ergebnis."""
    if notifier is None:
        return

    duration_str = f"{result.duration_seconds:.1f}s"

    if result.success:
        message = f"Job {result.job_name} finished (return_code={result.return_code}, duration={duration_str})"
    else:
        if result.exception:
            message = f"Job {result.job_name} failed: {result.exception}"
        else:
            message = f"Job {result.job_name} failed (return_code={result.return_code})"

    alert = Alert(
        level=level,
        source="scheduler",
        message=message,
        timestamp=result.finished_at,
        context={
            "job_name": result.job_name,
            "return_code": result.return_code,
            "duration": result.duration_seconds,
        },
    )
    notifier.send(alert)


def log_job_to_registry(result: JobResult, job: JobDefinition) -> Optional[str]:
    """Loggt Job-Ergebnis in die Registry."""
    if not REGISTRY_AVAILABLE:
        return None

    try:
        run_id = log_scheduler_job_run(
            job_name=result.job_name,
            command=job.command,
            args=job.args,
            return_code=result.return_code,
            started_at=result.started_at,
            finished_at=result.finished_at,
            tag=",".join(job.tags) if job.tags else None,
        )
        return run_id
    except Exception as e:
        print(f"[WARNING] Registry-Logging fehlgeschlagen: {e}")
        return None


def run_scheduler_loop(
    config_path: Path,
    poll_interval: int,
    once: bool,
    include_tags: Optional[Set[str]],
    exclude_tags: Optional[Set[str]],
    dry_run: bool,
    verbose: bool,
    use_registry: bool,
    notifier,
) -> int:
    """Hauptschleife des Schedulers."""
    global _shutdown_requested

    print("\n" + "=" * 70)
    print("PEAK_TRADE SCHEDULER")
    print("=" * 70)
    print(f"Config: {config_path}")
    print(f"Poll Interval: {poll_interval}s")
    print(f"Mode: {'ONCE' if once else 'CONTINUOUS'}")
    if dry_run:
        print("DRY-RUN: Keine echte Ausführung")
    print("=" * 70)

    # Jobs laden
    try:
        all_jobs = load_jobs_from_toml(config_path)
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        return 1

    # Jobs filtern
    jobs = filter_jobs_by_tags(all_jobs, include_tags, exclude_tags)

    if not jobs:
        print("\nKeine passenden Jobs gefunden.")
        return 0

    # Validierung
    for job in jobs:
        warnings = validate_job_config(job)
        for w in warnings:
            print(f"[WARNING] {w}")

    # Jobs initialisieren (next_run_at berechnen)
    now = datetime.utcnow()
    for job in jobs:
        if job.schedule.next_run_at is None:
            job.schedule.next_run_at = compute_next_run_at(job.schedule, now=now)

    # Job-Summary
    print_job_summary(jobs, now)

    # Schleife
    iteration = 0
    total_jobs_run = 0

    while not _shutdown_requested:
        iteration += 1
        now = datetime.utcnow()

        if verbose:
            print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] Check #{iteration}")

        # Fällige Jobs finden
        due_jobs = get_due_jobs(jobs, now=now)

        if due_jobs:
            print(f"\n[SCHEDULER] {len(due_jobs)} fällige Jobs:")

            for job in due_jobs:
                print(f"\n  -> Starte: {job.name}")

                # Job ausführen
                result = run_job(job, dry_run=dry_run)
                total_jobs_run += 1

                # Schedule aktualisieren
                update_job_schedule_after_run(job, result)

                # Ergebnis ausgeben
                if result.success:
                    print(f"     ✅ Erfolgreich ({result.duration_seconds:.1f}s)")
                    if verbose and result.stdout:
                        print(f"     stdout: {result.stdout[:200]}...")

                    # Alert
                    send_job_alert(notifier, result, level="info")
                else:
                    print(f"     ❌ Fehlgeschlagen (return_code={result.return_code})")
                    if result.exception:
                        print(f"     Exception: {result.exception}")
                    if result.stderr:
                        print(f"     stderr: {result.stderr[:200]}...")

                    # Alert
                    send_job_alert(notifier, result, level="critical")

                # Registry-Logging
                if use_registry and not dry_run:
                    run_id = log_job_to_registry(result, job)
                    if run_id and verbose:
                        print(f"     Registry: {run_id[:8]}...")

        elif verbose:
            print("  Keine fälligen Jobs")

        # Once-Modus -> beenden
        if once:
            break

        # Warten
        if not _shutdown_requested:
            time.sleep(poll_interval)

    # Summary
    print("\n" + "=" * 70)
    print("SCHEDULER BEENDET")
    print("=" * 70)
    print(f"Iterationen: {iteration}")
    print(f"Jobs ausgeführt: {total_jobs_run}")
    print("=" * 70 + "\n")

    return 0


def main(argv=None) -> int:
    """Main entry point."""
    args = parse_args(argv)

    # Signal-Handler registrieren
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Tags parsen
    include_tags = None
    if args.include_tags:
        include_tags = set(t.strip() for t in args.include_tags.split(","))

    exclude_tags = None
    if args.exclude_tags:
        exclude_tags = set(t.strip() for t in args.exclude_tags.split(","))

    # Notifier erstellen
    notifier = create_notifier(args)

    # Registry-Nutzung
    use_registry = REGISTRY_AVAILABLE and not args.no_registry

    # Scheduler starten
    return run_scheduler_loop(
        config_path=Path(args.config),
        poll_interval=args.poll_interval,
        once=args.once,
        include_tags=include_tags,
        exclude_tags=exclude_tags,
        dry_run=args.dry_run,
        verbose=args.verbose,
        use_registry=use_registry,
        notifier=notifier,
    )


if __name__ == "__main__":
    sys.exit(main())
