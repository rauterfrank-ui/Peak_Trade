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
from .config_loader import (
    load_jobs_from_toml,
)
from .models import (
    JobDefinition,
    JobResult,
    JobSchedule,
    ScheduleType,
)
from .runner import (
    build_command_args,
    compute_next_run_at,
    get_due_jobs,
    is_job_due,
    run_job,
)

__all__ = [
    "JobDefinition",
    "JobResult",
    "JobSchedule",
    # Models
    "ScheduleType",
    "build_command_args",
    # Runner
    "compute_next_run_at",
    "get_due_jobs",
    "is_job_due",
    # Config Loader
    "load_jobs_from_toml",
    "run_job",
]
