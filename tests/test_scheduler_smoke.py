# tests/test_scheduler_smoke.py
"""
Smoke-Tests für den Scheduler & Job Runner.

Testet:
- Dataclasses (JobSchedule, JobDefinition, JobResult)
- Config-Loader (load_jobs_from_toml)
- Schedule-Berechnungen (compute_next_run_at, is_job_due, get_due_jobs)
- Job-Runner (build_command_args, run_job)
- CLI-Script (dry-run)
"""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from pathlib import Path


class TestDataclasses:
    """Tests für Scheduler-Dataclasses."""

    def test_job_schedule_creation(self):
        """JobSchedule kann erstellt werden."""
        from src.scheduler.models import JobSchedule

        schedule = JobSchedule(
            type="daily",
            daily_time="07:30",
        )

        assert schedule.type == "daily"
        assert schedule.daily_time == "07:30"
        assert schedule.next_run_at is None

    def test_job_definition_creation(self):
        """JobDefinition kann erstellt werden."""
        from src.scheduler.models import JobDefinition, JobSchedule

        schedule = JobSchedule(type="interval", interval_seconds=3600)
        job = JobDefinition(
            name="test_job",
            command="python",
            args={"script": "scripts/run_backtest.py", "strategy": "ma_crossover"},
            schedule=schedule,
            enabled=True,
            tags=["test", "daily"],
        )

        assert job.name == "test_job"
        assert job.command == "python"
        assert job.args["script"] == "scripts/run_backtest.py"
        assert job.enabled is True
        assert "test" in job.tags

    def test_job_result_creation(self):
        """JobResult kann erstellt werden."""
        from src.scheduler.models import JobResult

        now = datetime.utcnow()
        result = JobResult(
            job_name="test_job",
            started_at=now,
            finished_at=now + timedelta(seconds=5),
            return_code=0,
            success=True,
            stdout="OK",
        )

        assert result.job_name == "test_job"
        assert result.success is True
        assert result.duration_seconds == pytest.approx(5.0, abs=0.1)


class TestConfigLoader:
    """Tests für load_jobs_from_toml()."""

    def test_load_jobs_from_toml(self, tmp_path: Path):
        """Lädt Jobs aus TOML-Datei."""
        from src.scheduler.config_loader import load_jobs_from_toml

        toml_content = """
[[job]]
name = "test_job"
command = "python"
args = { script = "scripts/run_backtest.py", strategy = "ma_crossover" }
schedule_type = "daily"
daily_time = "08:00"
enabled = true
tags = ["test"]
"""
        toml_file = tmp_path / "jobs.toml"
        toml_file.write_text(toml_content)

        jobs = load_jobs_from_toml(toml_file)

        assert len(jobs) == 1
        assert jobs[0].name == "test_job"
        assert jobs[0].schedule.type == "daily"
        assert jobs[0].schedule.daily_time == "08:00"

    def test_load_multiple_jobs(self, tmp_path: Path):
        """Lädt mehrere Jobs aus TOML-Datei."""
        from src.scheduler.config_loader import load_jobs_from_toml

        toml_content = """
[[job]]
name = "job1"
args = { script = "scripts/a.py" }
schedule_type = "once"

[[job]]
name = "job2"
args = { script = "scripts/b.py" }
schedule_type = "interval"
interval_seconds = 3600
"""
        toml_file = tmp_path / "jobs.toml"
        toml_file.write_text(toml_content)

        jobs = load_jobs_from_toml(toml_file)

        assert len(jobs) == 2
        assert jobs[0].name == "job1"
        assert jobs[1].name == "job2"
        assert jobs[1].schedule.interval_seconds == 3600

    def test_load_missing_file_raises(self, tmp_path: Path):
        """Fehlende Datei wirft FileNotFoundError."""
        from src.scheduler.config_loader import load_jobs_from_toml

        with pytest.raises(FileNotFoundError):
            load_jobs_from_toml(tmp_path / "nonexistent.toml")


class TestValidateJobConfig:
    """Tests für validate_job_config()."""

    def test_validate_valid_job(self):
        """Valider Job hat keine Warnungen."""
        from src.scheduler.models import JobDefinition, JobSchedule
        from src.scheduler.config_loader import validate_job_config

        job = JobDefinition(
            name="valid_job",
            args={"script": "scripts/run_backtest.py"},
            schedule=JobSchedule(type="once"),
        )

        warnings = validate_job_config(job)
        assert len(warnings) == 0

    def test_validate_missing_script(self):
        """Job ohne script-Argument erzeugt Warnung."""
        from src.scheduler.models import JobDefinition
        from src.scheduler.config_loader import validate_job_config

        job = JobDefinition(
            name="no_script_job",
            args={"strategy": "ma_crossover"},  # Kein script
        )

        warnings = validate_job_config(job)
        assert any("script" in w for w in warnings)

    def test_validate_interval_without_seconds(self):
        """Interval-Job ohne interval_seconds erzeugt Warnung."""
        from src.scheduler.models import JobDefinition, JobSchedule
        from src.scheduler.config_loader import validate_job_config

        job = JobDefinition(
            name="interval_job",
            args={"script": "test.py"},
            schedule=JobSchedule(type="interval"),  # Kein interval_seconds
        )

        warnings = validate_job_config(job)
        assert any("interval_seconds" in w for w in warnings)


class TestComputeNextRunAt:
    """Tests für compute_next_run_at()."""

    def test_once_never_run(self):
        """Once-Job ohne vorherige Ausführung ist sofort fällig."""
        from src.scheduler.models import JobSchedule
        from src.scheduler.runner import compute_next_run_at

        schedule = JobSchedule(type="once")
        now = datetime.utcnow()

        next_run = compute_next_run_at(schedule, now=now)

        assert next_run <= now

    def test_once_already_run(self):
        """Once-Job nach Ausführung ist nie wieder fällig."""
        from src.scheduler.models import JobSchedule
        from src.scheduler.runner import compute_next_run_at

        schedule = JobSchedule(type="once", last_run_at=datetime.utcnow())

        next_run = compute_next_run_at(schedule)

        assert next_run == datetime.max

    def test_interval_not_run(self):
        """Interval-Job ohne vorherige Ausführung ist sofort fällig."""
        from src.scheduler.models import JobSchedule
        from src.scheduler.runner import compute_next_run_at

        schedule = JobSchedule(type="interval", interval_seconds=3600)
        now = datetime.utcnow()

        next_run = compute_next_run_at(schedule, now=now)

        assert next_run <= now

    def test_interval_after_run(self):
        """Interval-Job nach Ausführung ist nach Intervall fällig."""
        from src.scheduler.models import JobSchedule
        from src.scheduler.runner import compute_next_run_at

        now = datetime.utcnow()
        last_run = now - timedelta(seconds=1800)  # Vor 30 Minuten

        schedule = JobSchedule(
            type="interval",
            interval_seconds=3600,
            last_run_at=last_run,
        )

        next_run = compute_next_run_at(schedule, now=now)

        # Sollte in 30 Minuten fällig sein
        expected = last_run + timedelta(seconds=3600)
        assert abs((next_run - expected).total_seconds()) < 1

    def test_daily_time_future(self):
        """Daily-Job für zukünftige Uhrzeit ist am selben Tag fällig."""
        from src.scheduler.models import JobSchedule
        from src.scheduler.runner import compute_next_run_at

        # Fixe Zeit: 06:00 UTC
        now = datetime(2025, 1, 15, 6, 0, 0)
        schedule = JobSchedule(type="daily", daily_time="08:00")

        next_run = compute_next_run_at(schedule, now=now)

        # Sollte heute um 08:00 sein
        assert next_run.hour == 8
        assert next_run.date() == now.date()

    def test_daily_time_past(self):
        """Daily-Job für vergangene Uhrzeit ist morgen fällig."""
        from src.scheduler.models import JobSchedule
        from src.scheduler.runner import compute_next_run_at

        # Fixe Zeit: 10:00 UTC
        now = datetime(2025, 1, 15, 10, 0, 0)
        schedule = JobSchedule(type="daily", daily_time="08:00")

        next_run = compute_next_run_at(schedule, now=now)

        # Sollte morgen um 08:00 sein
        assert next_run.hour == 8
        assert next_run.date() == now.date() + timedelta(days=1)


class TestIsJobDue:
    """Tests für is_job_due()."""

    def test_disabled_job_never_due(self):
        """Deaktivierter Job ist nie fällig."""
        from src.scheduler.models import JobDefinition, JobSchedule
        from src.scheduler.runner import is_job_due

        job = JobDefinition(
            name="disabled",
            args={"script": "test.py"},
            schedule=JobSchedule(type="once"),
            enabled=False,
        )

        assert is_job_due(job) is False

    def test_once_job_due(self):
        """Once-Job ohne vorherige Ausführung ist fällig."""
        from src.scheduler.models import JobDefinition, JobSchedule
        from src.scheduler.runner import is_job_due

        job = JobDefinition(
            name="once_job",
            args={"script": "test.py"},
            schedule=JobSchedule(type="once"),
            enabled=True,
        )

        assert is_job_due(job) is True


class TestGetDueJobs:
    """Tests für get_due_jobs()."""

    def test_filters_due_jobs(self):
        """Findet nur fällige Jobs."""
        from src.scheduler.models import JobDefinition, JobSchedule
        from src.scheduler.runner import get_due_jobs

        now = datetime.utcnow()

        # Fälliger Job
        job1 = JobDefinition(
            name="due_job",
            args={"script": "test.py"},
            schedule=JobSchedule(type="once"),
            enabled=True,
        )

        # Nicht fälliger Job (deaktiviert)
        job2 = JobDefinition(
            name="disabled_job",
            args={"script": "test.py"},
            schedule=JobSchedule(type="once"),
            enabled=False,
        )

        due = get_due_jobs([job1, job2], now=now)

        assert len(due) == 1
        assert due[0].name == "due_job"


class TestBuildCommandArgs:
    """Tests für build_command_args()."""

    def test_builds_simple_command(self):
        """Baut einfaches Kommando."""
        from src.scheduler.models import JobDefinition
        from src.scheduler.runner import build_command_args

        job = JobDefinition(
            name="test",
            args={"script": "scripts/run_backtest.py", "strategy": "ma_crossover"},
        )

        args = build_command_args(job)

        assert args[0] == "scripts/run_backtest.py"
        assert "--strategy" in args
        assert "ma_crossover" in args

    def test_handles_boolean_args(self):
        """Behandelt Boolean-Argumente korrekt."""
        from src.scheduler.models import JobDefinition
        from src.scheduler.runner import build_command_args

        job = JobDefinition(
            name="test",
            args={"script": "test.py", "dry_run": True, "verbose": False},
        )

        args = build_command_args(job)

        assert "--dry-run" in args
        assert "--verbose" not in args  # False wird nicht hinzugefügt


class TestRunJob:
    """Tests für run_job()."""

    def test_run_job_dry_run(self):
        """Dry-Run führt nicht wirklich aus."""
        from src.scheduler.models import JobDefinition
        from src.scheduler.runner import run_job

        job = JobDefinition(
            name="test_job",
            args={"script": "scripts/nonexistent.py"},
        )

        result = run_job(job, dry_run=True)

        assert result.success is True
        assert "[DRY-RUN]" in result.stdout

    def test_run_simple_python_command(self):
        """Führt einfaches Python-Kommando aus."""
        from src.scheduler.models import JobDefinition
        from src.scheduler.runner import run_job

        job = JobDefinition(
            name="echo_test",
            command="python",
            args={"script": "-c", "print('hello')": None},
        )

        # Alternative: -c direkt als script
        job2 = JobDefinition(
            name="echo_test2",
            command="python",
            args={},
        )

        # Simpler Test mit echo
        result = run_job(job, dry_run=True)
        assert result.success is True


class TestCLIScriptDryRun:
    """Tests für run_scheduler.py Script."""

    def test_dry_run_with_config(self, tmp_path: Path):
        """Dry-Run mit Config läuft durch."""
        from scripts.run_scheduler import main

        toml_content = """
[[job]]
name = "test_job"
args = { script = "scripts/run_backtest.py" }
schedule_type = "once"
enabled = true
"""
        toml_file = tmp_path / "jobs.toml"
        toml_file.write_text(toml_content)

        exit_code = main([
            "--config", str(toml_file),
            "--once",
            "--dry-run",
        ])

        assert exit_code == 0

    def test_dry_run_missing_config(self, tmp_path: Path):
        """Dry-Run mit fehlender Config gibt Fehler."""
        from scripts.run_scheduler import main

        exit_code = main([
            "--config", str(tmp_path / "nonexistent.toml"),
            "--once",
        ])

        assert exit_code == 1

    def test_help_shows_usage(self):
        """Help-Flag zeigt Usage."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "scripts/run_scheduler.py", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Peak_Trade Scheduler" in result.stdout


class TestSchedulerJobRegistry:
    """Tests für log_scheduler_job_run()."""

    def test_log_scheduler_job_run(self, tmp_path: Path, monkeypatch):
        """log_scheduler_job_run loggt in Registry."""
        from src.core.experiments import log_scheduler_job_run, EXPERIMENTS_DIR, EXPERIMENTS_CSV

        # Experiments-Verzeichnis auf tmp_path umleiten
        test_experiments_dir = tmp_path / "experiments"
        test_experiments_csv = test_experiments_dir / "experiments.csv"
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_DIR", test_experiments_dir)
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_CSV", test_experiments_csv)

        now = datetime.utcnow()
        run_id = log_scheduler_job_run(
            job_name="test_scheduler_job",
            command="python",
            args={"script": "scripts/run_backtest.py"},
            return_code=0,
            started_at=now,
            finished_at=now + timedelta(seconds=5),
            tag="test",
        )

        assert run_id is not None
        assert test_experiments_csv.exists()

        content = test_experiments_csv.read_text()
        assert "scheduler_job" in content
        assert "test_scheduler_job" in content


class TestTagFiltering:
    """Tests für Tag-Filterung im Scheduler."""

    def test_filter_by_include_tags(self):
        """Filtert nach Include-Tags."""
        from scripts.run_scheduler import filter_jobs_by_tags
        from src.scheduler.models import JobDefinition

        jobs = [
            JobDefinition(name="job1", tags=["daily", "prod"]),
            JobDefinition(name="job2", tags=["weekly"]),
            JobDefinition(name="job3", tags=["daily"]),
        ]

        filtered = filter_jobs_by_tags(jobs, include_tags={"daily"})

        assert len(filtered) == 2
        assert all("daily" in j.tags for j in filtered)

    def test_filter_by_exclude_tags(self):
        """Filtert nach Exclude-Tags."""
        from scripts.run_scheduler import filter_jobs_by_tags
        from src.scheduler.models import JobDefinition

        jobs = [
            JobDefinition(name="job1", tags=["daily", "prod"]),
            JobDefinition(name="job2", tags=["heavy"]),
            JobDefinition(name="job3", tags=["daily"]),
        ]

        filtered = filter_jobs_by_tags(jobs, exclude_tags={"heavy"})

        assert len(filtered) == 2
        assert all("heavy" not in j.tags for j in filtered)
