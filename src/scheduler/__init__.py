# src/scheduler/__init__.py
"""
Peak_Trade Scheduler & Job Runner
==================================
Leichtgewichtiger CLI-Scheduler für automatisierte Jobs.

Features:
- Deklarative Job-Definitionen in TOML
- Schedule-Typen: once, interval, daily
- Integration mit Registry & Notifications
- Dry-Run-Modus

Usage:
    from src.scheduler import (
        JobDefinition,
        JobSchedule,
        JobResult,
        load_jobs_from_toml,
        run_job,
    )
"""
from .models import (
    ScheduleType,
    JobSchedule,
    JobDefinition,
    JobResult,
)

from .config_loader import (
    load_jobs_from_toml,
)

from .runner import (
    compute_next_run_at,
    is_job_due,
    get_due_jobs,
    build_command_args,
    run_job,
)

__all__ = [
    # Models
    "ScheduleType",
    "JobSchedule",
    "JobDefinition",
    "JobResult",
    # Config Loader
    "load_jobs_from_toml",
    # Runner
    "compute_next_run_at",
    "is_job_due",
    "get_due_jobs",
    "build_command_args",
    "run_job",
]
