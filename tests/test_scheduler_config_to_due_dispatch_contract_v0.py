# tests/test_scheduler_config_to_due_dispatch_contract_v0.py
"""
Offline contract: TOML config → JobDefinition → due selection → fake dispatch.

Deliberately uses the same canonical loader as ``scripts/run_scheduler.py``
(``src.scheduler.config_loader.load_jobs_from_toml`` / ``src.scheduler`` export).

 Boundaries:
- No Testnet / Paper / Shadow runtime
- No ``run_scheduler_loop``, no daemon, no scheduler sleep ticks in tests
- No real subprocess/network/exchange/order paths (``subprocess_run`` injection + dry fakes only)
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from src.scheduler.config_loader import load_jobs_from_toml
from src.scheduler.models import JobDefinition, JobSchedule
from src.scheduler.runner import get_due_jobs, run_job, update_job_schedule_after_run

NOW = datetime(2026, 5, 15, 18, 0, 0)


def _utcnow_fixture() -> datetime:
    return NOW


def three_job_toml() -> str:
    return """
[[job]]
name = "due_once"
enabled = true
command = "python"
args = { script = "scripts/offline_fixture.py", marker = "due" }
schedule_type = "once"

[[job]]
name = "future_iv"
enabled = true
command = "python"
args = { script = "scripts/offline_fixture.py", marker = "future" }
schedule_type = "interval"
interval_seconds = 3600

[[job]]
name = "disabled_once"
enabled = false
command = "python"
args = { script = "scripts/offline_fixture.py", marker = "disabled" }
schedule_type = "once"
"""


def test_tmp_toml_loads_into_scheduler_job_models(tmp_path: Path) -> None:
    cfg = tmp_path / "scheduler_jobs.toml"
    cfg.write_text(three_job_toml(), encoding="utf-8")

    jobs = load_jobs_from_toml(cfg)
    names = sorted(j.name for j in jobs)
    assert names == ["disabled_once", "due_once", "future_iv"]
    for j in jobs:
        assert isinstance(j, JobDefinition)
        assert isinstance(j.schedule, JobSchedule)


def test_loaded_due_job_selected_by_get_due_jobs(tmp_path: Path) -> None:
    cfg = tmp_path / "scheduler_jobs.toml"
    cfg.write_text(three_job_toml(), encoding="utf-8")
    jobs = load_jobs_from_toml(cfg)

    due_once = next(j for j in jobs if j.name == "due_once")
    future_iv = next(j for j in jobs if j.name == "future_iv")
    due_once.schedule.next_run_at = NOW - timedelta(seconds=2)
    future_iv.schedule.next_run_at = NOW + timedelta(hours=1)

    selected = get_due_jobs(jobs, now=NOW)
    assert [j.name for j in selected] == ["due_once"]


def test_loaded_due_job_dispatches_fake_subprocess_exactly_once(
    tmp_path: Path,
) -> None:
    cfg = tmp_path / "scheduler_jobs.toml"
    cfg.write_text(three_job_toml(), encoding="utf-8")
    jobs = load_jobs_from_toml(cfg)

    due_once = next(j for j in jobs if j.name == "due_once")
    future_iv = next(j for j in jobs if j.name == "future_iv")
    due_once.schedule.next_run_at = NOW - timedelta(seconds=2)
    future_iv.schedule.next_run_at = NOW + timedelta(hours=1)

    invocations: list[list[str]] = []

    def fake_subprocess_run(cmd, **_kwargs):
        invocations.append(list(cmd))
        return SimpleNamespace(returncode=0, stdout="offline-ok", stderr="")

    for job in get_due_jobs(jobs, now=NOW):
        result = run_job(
            job,
            subprocess_run=fake_subprocess_run,
            utcnow=_utcnow_fixture,
        )
        assert result.success is True
        update_job_schedule_after_run(job, result)

    assert len(invocations) == 1
    joined = " ".join(invocations[0])
    assert "offline_fixture.py" in joined
    assert "--marker" in joined
    assert "due" in joined


def test_loaded_not_due_job_does_not_dispatch(tmp_path: Path) -> None:
    cfg = tmp_path / "scheduler_jobs.toml"
    cfg.write_text(three_job_toml(), encoding="utf-8")
    jobs = load_jobs_from_toml(cfg)

    due_once = next(j for j in jobs if j.name == "due_once")
    future_iv = next(j for j in jobs if j.name == "future_iv")
    due_once.schedule.next_run_at = NOW + timedelta(minutes=10)
    future_iv.schedule.next_run_at = NOW + timedelta(hours=3)

    assert get_due_jobs(jobs, now=NOW) == []

    recorded: list[int] = []

    def recorder(*_a, **_k):
        recorded.append(1)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    # Defensive scan: iterate would-be roster (none due)
    for job in jobs:
        if job in get_due_jobs(jobs, now=NOW):
            run_job(job, subprocess_run=recorder, utcnow=_utcnow_fixture)

    assert recorded == []


def test_loaded_disabled_job_does_not_dispatch(tmp_path: Path) -> None:
    cfg = tmp_path / "scheduler_jobs.toml"
    cfg.write_text(three_job_toml(), encoding="utf-8")
    jobs = load_jobs_from_toml(cfg)

    disabled = next(j for j in jobs if j.name == "disabled_once")
    for j in jobs:
        if j.name != "disabled_once":
            j.schedule.next_run_at = NOW + timedelta(days=1)
    disabled.schedule.next_run_at = NOW - timedelta(seconds=1)

    assert get_due_jobs(jobs, now=NOW) == []


def test_successful_dispatch_updates_schedule_without_daemon(tmp_path: Path) -> None:
    cfg = tmp_path / "scheduler_jobs.toml"
    cfg.write_text(three_job_toml(), encoding="utf-8")
    jobs = load_jobs_from_toml(cfg)

    future_iv = next(j for j in jobs if j.name == "future_iv")
    interval_secs = future_iv.schedule.interval_seconds or 3600
    future_iv.schedule.last_run_at = None
    future_iv.schedule.next_run_at = NOW - timedelta(seconds=1)

    due = get_due_jobs([future_iv], now=NOW)
    assert due == [future_iv]

    before_next = future_iv.schedule.next_run_at

    def ok_run(_cmd, **_kw):
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    res = run_job(future_iv, subprocess_run=ok_run, utcnow=_utcnow_fixture)
    update_job_schedule_after_run(future_iv, res)

    assert before_next is not None
    expected_next = res.finished_at + timedelta(seconds=interval_secs)
    assert future_iv.schedule.next_run_at == expected_next


def test_failure_dispatch_no_network_classification(tmp_path: Path) -> None:
    cfg = tmp_path / "scheduler_jobs.toml"
    cfg.write_text(three_job_toml(), encoding="utf-8")
    jobs = load_jobs_from_toml(cfg)

    due_once = next(j for j in jobs if j.name == "due_once")
    due_once.schedule.next_run_at = NOW - timedelta(seconds=1)

    def bad_run(_cmd, **_kw):
        return SimpleNamespace(returncode=9, stdout="", stderr="offline-failure")

    res = run_job(due_once, subprocess_run=bad_run, utcnow=_utcnow_fixture)
    assert res.success is False
    assert res.return_code == 9
    assert "offline-failure" in res.stderr


def test_standalone_process_load_jobs_does_not_import_run_scheduler_package(
    tmp_path: Path,
) -> None:
    """Fresh interpreter + load_jobs_from_toml must not execute or import daemon loop."""
    repo_root = Path(__file__).resolve().parents[1]
    cfg_path = tmp_path / "solo.toml"
    cfg_path.write_text(
        """
[[job]]
name = "solo_once"
enabled = true
command = "python"
args = { script = "scripts/x.py" }
schedule_type = "once"
""",
        encoding="utf-8",
    )
    checker = tmp_path / "standalone_load_checker.py"
    checker.write_text(
        f"""\
import sys
from pathlib import Path
ROOT = Path({str(repo_root)!r})
CONFIG = Path({str(cfg_path)!r})

sys.path.insert(0, str(ROOT.resolve()))
assert "scripts.run_scheduler" not in sys.modules

from src.scheduler.config_loader import load_jobs_from_toml

load_jobs_from_toml(CONFIG)

assert __import__("sys").modules.get("scripts.run_scheduler") is None
""",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [sys.executable, str(checker)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
