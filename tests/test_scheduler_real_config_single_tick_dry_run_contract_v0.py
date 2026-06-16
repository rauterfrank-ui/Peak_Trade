# tests/test_scheduler_real_config_single_tick_dry_run_contract_v0.py
"""
Bounded single-tick dry-run against a **copy** of the real repo scheduler config.

- Uses ``config/scheduler/jobs.toml`` as the canonical candidate (must exist).
- Never mutates repository config files; only ``tmp_path`` copies are patched.
- Uses ``dry_run=True`` so no subprocess executes real scripts (exchange/network).
"""

from __future__ import annotations

import shutil
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEDULER_JOBS_TOML = REPO_ROOT / "config" / "scheduler" / "jobs.toml"

# Deterministic clock bucket (matches other scheduler contract tests).
NOW = datetime(2026, 5, 15, 19, 30, 0)


def _utc() -> datetime:
    return NOW


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


@pytest.mark.skipif(
    not SCHEDULER_JOBS_TOML.is_file(),
    reason="Real scheduler config candidate config/scheduler/jobs.toml missing",
)
def test_safe_scheduler_config_candidate_exists() -> None:
    assert SCHEDULER_JOBS_TOML.is_file()
    raw = _read_bytes(SCHEDULER_JOBS_TOML)
    assert len(raw) > 50
    assert b"[[job]]" in raw


def test_copy_to_tmp_leaves_repo_config_bytes_unchanged(tmp_path: Path) -> None:
    if not SCHEDULER_JOBS_TOML.is_file():
        pytest.skip("scheduler jobs.toml not present")

    before = _read_bytes(SCHEDULER_JOBS_TOML)
    dest = tmp_path / "jobs.toml"
    shutil.copyfile(SCHEDULER_JOBS_TOML, dest)
    after = _read_bytes(SCHEDULER_JOBS_TOML)
    assert before == after
    assert dest.read_bytes() == before


def boom_sub(*_a, **_k):
    raise AssertionError("subprocess_run must not run in dry_run tick")


def test_single_tick_loads_tmp_copy_dry_run_summary(tmp_path: Path) -> None:
    if not SCHEDULER_JOBS_TOML.is_file():
        pytest.skip("scheduler jobs.toml not present")

    dest = tmp_path / "jobs.toml"
    shutil.copyfile(SCHEDULER_JOBS_TOML, dest)

    import scripts.run_scheduler as rs

    summary = rs.run_scheduler_tick_once(
        dest,
        now=NOW,
        dry_run=True,
        subprocess_run=boom_sub,
        utcnow=_utc,
    )

    assert summary.loaded >= 1
    assert summary.eligible_after_tags >= 1
    assert summary.due >= 0
    assert summary.dispatched == summary.due
    assert summary.succeeded + summary.failed == summary.dispatched


def test_dry_run_subprocess_not_invoked_even_when_injected(tmp_path: Path) -> None:
    if not SCHEDULER_JOBS_TOML.is_file():
        pytest.skip("scheduler jobs.toml not present")

    dest = tmp_path / "jobs.toml"
    shutil.copyfile(SCHEDULER_JOBS_TOML, dest)

    called: list[int] = []

    def must_not_run(*_a, **_k):
        called.append(1)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    import scripts.run_scheduler as rs

    rs.run_scheduler_tick_once(
        dest,
        now=NOW,
        dry_run=True,
        subprocess_run=must_not_run,
        utcnow=_utc,
    )
    assert called == []


def test_tmp_copy_force_one_due_job_only_in_copy(tmp_path: Path, monkeypatch) -> None:
    if not SCHEDULER_JOBS_TOML.is_file():
        pytest.skip("scheduler jobs.toml not present")

    dest = tmp_path / "jobs.toml"
    shutil.copyfile(SCHEDULER_JOBS_TOML, dest)
    repo_before = _read_bytes(SCHEDULER_JOBS_TOML)

    import scripts.run_scheduler as rs

    real_load = rs.load_jobs_from_toml

    def wrap(p: Path):
        jobs = real_load(p)
        if Path(p).resolve() != dest.resolve():
            return jobs
        anchor = next(j for j in jobs if j.name == "daily_forward_signals_btc")
        for j in jobs:
            j.schedule.next_run_at = NOW + timedelta(days=30)
        anchor.schedule.next_run_at = NOW - timedelta(seconds=5)
        return jobs

    monkeypatch.setattr(rs, "load_jobs_from_toml", wrap)

    summary = rs.run_scheduler_tick_once(
        dest,
        now=NOW,
        dry_run=True,
        utcnow=_utc,
    )
    assert repo_before == _read_bytes(SCHEDULER_JOBS_TOML)
    assert summary.due >= 1
    assert summary.dispatched == summary.due


def test_no_sleep_and_loop_hooks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if not SCHEDULER_JOBS_TOML.is_file():
        pytest.skip("scheduler jobs.toml not present")

    dest = tmp_path / "jobs.toml"
    shutil.copyfile(SCHEDULER_JOBS_TOML, dest)

    import scripts.run_scheduler as rs

    def boom_sleep(_s=None):
        raise AssertionError("sleep must not be called")

    def boom_loop(*_a, **_k):
        raise AssertionError("run_scheduler_loop must not be called")

    monkeypatch.setattr(rs.time, "sleep", boom_sleep)
    monkeypatch.setattr(rs, "run_scheduler_loop", boom_loop)

    rs.run_scheduler_tick_once(
        dest,
        now=NOW,
        dry_run=True,
        utcnow=_utc,
    )


def test_no_exchange_order_exec_in_command_strings_inspection(tmp_path: Path) -> None:
    """Offline guard: tmp copy tick does not execute brokers; dry_run prevents subprocess."""
    if not SCHEDULER_JOBS_TOML.is_file():
        pytest.skip("scheduler jobs.toml not present")

    dest = tmp_path / "jobs.toml"
    shutil.copyfile(SCHEDULER_JOBS_TOML, dest)
    text = dest.read_text(encoding="utf-8")
    # Config references scripts — we never exec them in this test (dry_run only).
    assert "scripts/" in text
    import scripts.run_scheduler as rs

    rs.run_scheduler_tick_once(dest, now=NOW, dry_run=True, utcnow=_utc)


def test_real_config_contract_tests_stay_importable_stack() -> None:
    """Lightweight sentinel that the scheduler stack still imports."""
    import scripts.run_scheduler as rs

    assert hasattr(rs, "run_scheduler_tick_once")
    assert hasattr(rs, "SchedulerTickSummary")
