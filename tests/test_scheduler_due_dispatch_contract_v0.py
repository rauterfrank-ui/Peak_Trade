# tests/test_scheduler_due_dispatch_contract_v0.py
"""
Offline contract: scheduler due classification and single-job dispatch.

Boundaries (this file):
- No Testnet / Paper / Shadow runtime
- No ``run_scheduler`` daemon or ``run_scheduler_loop``
- No network, broker, exchange, or order lifecycle
- No sleep; deterministic ``now`` / ``utcnow`` and tmp_path-only artifacts
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from src.scheduler.config_loader import load_jobs_from_toml
from src.scheduler.models import JobDefinition, JobSchedule
from src.scheduler.runner import (
    get_due_jobs,
    is_job_due,
    run_job,
    update_job_schedule_after_run,
)

NOW = datetime(2026, 5, 15, 18, 0, 0)


def _fixed_utcnow() -> datetime:
    return NOW


def test_jobs_toml_on_tmp_path_classifies_as_due(tmp_path: Path) -> None:
    cfg = tmp_path / "jobs.toml"
    cfg.write_text(
        """
[[job]]
name = "solo"
command = "python"
args = { script = "scripts/noop.py" }
schedule_type = "once"
""",
        encoding="utf-8",
    )
    jobs = load_jobs_from_toml(cfg)
    jobs[0].schedule.next_run_at = NOW - timedelta(seconds=1)
    assert [j.name for j in get_due_jobs(jobs, now=NOW)] == ["solo"]


def test_synthetic_interval_job_past_next_run_is_due() -> None:
    job = JobDefinition(
        name="due_interval",
        args={"script": "scripts/noop.py"},
        schedule=JobSchedule(
            type="interval",
            interval_seconds=3600,
            next_run_at=NOW - timedelta(seconds=1),
        ),
    )
    assert is_job_due(job, now=NOW) is True
    assert [j.name for j in get_due_jobs([job], now=NOW)] == ["due_interval"]


def test_synthetic_interval_job_future_next_run_is_not_due() -> None:
    job = JobDefinition(
        name="future_interval",
        args={"script": "scripts/noop.py"},
        schedule=JobSchedule(
            type="interval",
            interval_seconds=3600,
            next_run_at=NOW + timedelta(hours=1),
        ),
    )
    assert is_job_due(job, now=NOW) is False
    assert get_due_jobs([job], now=NOW) == []


def test_disabled_job_is_never_due() -> None:
    job = JobDefinition(
        name="disabled_once",
        enabled=False,
        args={"script": "scripts/noop.py"},
        schedule=JobSchedule(
            type="once",
            next_run_at=NOW - timedelta(seconds=1),
        ),
    )
    assert is_job_due(job, now=NOW) is False
    assert get_due_jobs([job], now=NOW) == []


def test_due_job_dispatches_injected_runner_exactly_once(tmp_path: Path) -> None:
    """Exactly one due job invokes ``subprocess_run``; not-due and disabled do not."""
    tmp_path.joinpath("offline_contract").write_text("tmp_path only", encoding="utf-8")

    due_once = JobDefinition(
        name="due_once",
        args={"script": "scripts/noop.py"},
        schedule=JobSchedule(
            type="once",
            next_run_at=NOW - timedelta(seconds=5),
        ),
    )
    future_iv = JobDefinition(
        name="future_interval",
        args={"script": "scripts/other.py"},
        schedule=JobSchedule(
            type="interval",
            interval_seconds=3600,
            next_run_at=NOW + timedelta(hours=1),
        ),
    )
    disabled = JobDefinition(
        name="disabled_once",
        enabled=False,
        args={"script": "scripts/nope.py"},
        schedule=JobSchedule(
            type="once",
            next_run_at=NOW - timedelta(seconds=1),
        ),
    )

    roster = [due_once, future_iv, disabled]
    due_jobs = get_due_jobs(roster, now=NOW)
    assert [j.name for j in due_jobs] == ["due_once"]

    invoked: list[list[str]] = []

    def fake_subprocess_run(cmd, **_kwargs):
        invoked.append(list(cmd))
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    for job in due_jobs:
        res = run_job(
            job,
            subprocess_run=fake_subprocess_run,
            utcnow=_fixed_utcnow,
        )
        assert res.success is True
        update_job_schedule_after_run(job, res)

    assert len(invoked) == 1
    assert any("noop.py" in part for part in invoked[0])


def test_not_due_roster_does_not_invoke_subprocess(tmp_path: Path) -> None:
    job = JobDefinition(
        name="later",
        args={"script": "scripts/noop.py"},
        schedule=JobSchedule(
            type="interval",
            interval_seconds=300,
            next_run_at=NOW + timedelta(minutes=5),
        ),
    )
    assert get_due_jobs([job], now=NOW) == []

    calls: list[int] = []

    def fake_subprocess_run(cmd, **_kwargs):
        calls.append(1)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    for j in get_due_jobs([job], now=NOW):
        run_job(j, subprocess_run=fake_subprocess_run, utcnow=_fixed_utcnow)

    assert calls == []


def test_subprocess_failure_is_classified_without_success() -> None:
    job = JobDefinition(
        name="fails_cmd",
        args={"script": "scripts/noop.py"},
        schedule=JobSchedule(type="once", next_run_at=NOW - timedelta(seconds=1)),
        timeout_seconds=30,
    )

    def failing_run(_cmd, **_kwargs):
        return SimpleNamespace(returncode=7, stdout="", stderr="offline-fail")

    res = run_job(
        job,
        subprocess_run=failing_run,
        utcnow=_fixed_utcnow,
    )
    assert res.success is False
    assert res.return_code == 7
    assert "offline-fail" in res.stderr


def test_subprocess_exception_is_recorded_without_network() -> None:
    job = JobDefinition(
        name="boom",
        args={"script": "scripts/noop.py"},
        schedule=JobSchedule(type="once", next_run_at=NOW - timedelta(seconds=1)),
    )

    def raises(*args, **kwargs):  # noqa: ARG001
        raise RuntimeError("offline handler boom")

    res = run_job(
        job,
        subprocess_run=raises,
        utcnow=_fixed_utcnow,
    )
    assert res.success is False
    assert res.return_code == -1
    assert res.exception is not None
    assert "offline handler boom" in res.exception


def test_schedule_advances_after_successful_interval_run() -> None:
    interval_secs = 120
    job = JobDefinition(
        name="adv_interval",
        args={"script": "scripts/noop.py"},
        schedule=JobSchedule(
            type="interval",
            interval_seconds=interval_secs,
            next_run_at=NOW - timedelta(seconds=1),
        ),
    )

    def ok_run(_cmd, **_kwargs):
        return SimpleNamespace(returncode=0, stdout="x", stderr="")

    res = run_job(
        job,
        subprocess_run=ok_run,
        utcnow=_fixed_utcnow,
    )
    assert res.success is True
    before_next = job.schedule.next_run_at
    update_job_schedule_after_run(job, res)
    assert job.schedule.last_run_at == res.finished_at
    assert job.schedule.next_run_at == res.finished_at + timedelta(seconds=interval_secs)
    assert before_next is not None
    assert job.schedule.next_run_at > before_next


def test_once_job_after_success_sets_next_to_datetime_max_semantics() -> None:
    job = JobDefinition(
        name="once_done",
        args={"script": "scripts/noop.py"},
        schedule=JobSchedule(
            type="once",
            next_run_at=NOW - timedelta(seconds=1),
        ),
    )

    def ok_run(_cmd, **_kwargs):
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    res = run_job(job, subprocess_run=ok_run, utcnow=_fixed_utcnow)
    assert res.success is True
    update_job_schedule_after_run(job, res)
    assert job.schedule.next_run_at == datetime.max
