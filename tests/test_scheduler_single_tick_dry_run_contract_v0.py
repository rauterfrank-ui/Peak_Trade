# tests/test_scheduler_single_tick_dry_run_contract_v0.py
"""
Bounded single-tick contract: scripts.run_scheduler.run_scheduler_tick_once.

No daemon, no ``run_scheduler_loop``, no sleeps in assertions.
Uses tmp_path TOML, deterministic ``now`` / ``utcnow``, and fake ``subprocess_run``.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

NOW = datetime(2026, 5, 15, 19, 0, 0)


def _utc() -> datetime:
    return NOW


def _three_jobs_toml() -> str:
    return """
[[job]]
name = "due_once"
enabled = true
command = "python"
args = { script = "scripts/offline_tick.py", lane = "due" }
schedule_type = "once"

[[job]]
name = "future_iv"
enabled = true
command = "python"
args = { script = "scripts/offline_tick.py", lane = "future" }
schedule_type = "interval"
interval_seconds = 3600

[[job]]
name = "disabled_once"
enabled = false
command = "python"
args = { script = "scripts/offline_tick.py", lane = "off" }
schedule_type = "once"
"""


@pytest.fixture()
def patched_tick_loader(monkeypatch: pytest.MonkeyPatch):
    """Patch loader so future_iv is not-yet-due; due_once is due."""

    import scripts.run_scheduler as rs

    real_load = rs.load_jobs_from_toml

    def _wrap(path):  # noqa: ARG001
        jobs = real_load(path)
        due_once = next(j for j in jobs if j.name == "due_once")
        fut = next(j for j in jobs if j.name == "future_iv")
        due_once.schedule.next_run_at = NOW - timedelta(seconds=2)
        fut.schedule.next_run_at = NOW + timedelta(hours=2)
        return jobs

    monkeypatch.setattr(rs, "load_jobs_from_toml", _wrap)
    return rs


def test_tick_loads_dispatches_one_due_job_once(tmp_path: Path, patched_tick_loader) -> None:
    cfg = tmp_path / "tick.toml"
    cfg.write_text(_three_jobs_toml(), encoding="utf-8")

    invocations: list[int] = []

    def fake_run(cmd, **_kwargs):
        invocations.append(1)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    summary = patched_tick_loader.run_scheduler_tick_once(
        cfg,
        now=NOW,
        dry_run=False,
        subprocess_run=fake_run,
        utcnow=_utc,
    )

    assert summary.loaded == 3
    assert summary.eligible_after_tags == 3
    assert summary.due == 1
    assert summary.dispatched == 1
    assert summary.succeeded == 1
    assert summary.failed == 0
    assert summary.skipped_not_due == 2
    assert len(invocations) == 1


def test_tick_skips_not_due_job(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = tmp_path / "tick.toml"
    cfg.write_text(_three_jobs_toml(), encoding="utf-8")

    import scripts.run_scheduler as rs

    real_load = rs.load_jobs_from_toml

    def wrap(p):
        jobs = real_load(p)
        for j in jobs:
            j.schedule.next_run_at = NOW + timedelta(days=1)
        return jobs

    monkeypatch.setattr(rs, "load_jobs_from_toml", wrap)

    called: list[int] = []

    def fake_run(*_a, **_k):
        called.append(1)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    summary = rs.run_scheduler_tick_once(
        cfg,
        now=NOW,
        subprocess_run=fake_run,
        utcnow=_utc,
    )
    assert summary.due == 0
    assert summary.dispatched == 0
    assert summary.skipped_not_due == 3
    assert called == []


def test_tick_skips_disabled_job(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = tmp_path / "tick.toml"
    cfg.write_text(_three_jobs_toml(), encoding="utf-8")

    import scripts.run_scheduler as rs

    real_load = rs.load_jobs_from_toml

    def wrap(p):
        jobs = real_load(p)
        for j in jobs:
            if j.name != "disabled_once":
                j.schedule.next_run_at = NOW + timedelta(days=7)
            else:
                j.schedule.next_run_at = NOW - timedelta(seconds=9)
        return jobs

    monkeypatch.setattr(rs, "load_jobs_from_toml", wrap)

    summary = rs.run_scheduler_tick_once(
        cfg,
        now=NOW,
        subprocess_run=lambda *_a, **_k: SimpleNamespace(returncode=0, stdout="", stderr=""),
        utcnow=_utc,
    )
    assert summary.due == 0
    assert summary.dispatched == 0


def test_tick_records_failed_fake_dispatch_without_network(
    tmp_path: Path, patched_tick_loader
) -> None:
    cfg = tmp_path / "tick.toml"
    cfg.write_text(_three_jobs_toml(), encoding="utf-8")

    def bad_run(cmd, **_kwargs):  # noqa: ARG001
        return SimpleNamespace(returncode=3, stdout="", stderr="offline-fatal")

    summary = patched_tick_loader.run_scheduler_tick_once(
        cfg,
        now=NOW,
        subprocess_run=bad_run,
        utcnow=_utc,
    )
    assert summary.due == 1
    assert summary.dispatched == 1
    assert summary.succeeded == 0
    assert summary.failed == 1


def test_tick_updates_schedule_after_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = tmp_path / "tick.toml"
    cfg.write_text(
        """
[[job]]
name = "iv_only"
enabled = true
command = "python"
args = { script = "scripts/offline_tick.py" }
schedule_type = "interval"
interval_seconds = 90
""",
        encoding="utf-8",
    )

    import scripts.run_scheduler as rs

    iv_job_holder: dict[str, object] = {}

    real_load = rs.load_jobs_from_toml

    def wrap(p):
        jobs = real_load(p)
        job = jobs[0]
        job.schedule.last_run_at = None
        job.schedule.next_run_at = NOW - timedelta(seconds=2)
        iv_job_holder["job"] = job
        return jobs

    monkeypatch.setattr(rs, "load_jobs_from_toml", wrap)

    fake_res = SimpleNamespace(returncode=0, stdout="", stderr="")

    summary = rs.run_scheduler_tick_once(
        cfg,
        now=NOW,
        subprocess_run=lambda *_a, **_k: fake_res,
        utcnow=_utc,
    )

    job = iv_job_holder["job"]
    assert summary.succeeded == 1
    assert job.schedule.last_run_at is not None
    assert job.schedule.next_run_at == job.schedule.last_run_at + timedelta(seconds=90)


def test_tick_summary_counts_stable_shape(tmp_path: Path, patched_tick_loader) -> None:
    cfg = tmp_path / "tick.toml"
    cfg.write_text(_three_jobs_toml(), encoding="utf-8")

    summary = patched_tick_loader.run_scheduler_tick_once(
        cfg,
        now=NOW,
        subprocess_run=lambda *_a, **_k: SimpleNamespace(returncode=0, stdout="", stderr=""),
        utcnow=_utc,
    )
    dispatch_total = summary.succeeded + summary.failed
    assert summary.dispatched == dispatch_total


def test_tick_does_not_call_sleep(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import scripts.run_scheduler as rs

    def boom_sleep(_secs=None):
        raise AssertionError("time.sleep must not be used in bounded tick")

    monkeypatch.setattr(rs.time, "sleep", boom_sleep)

    cfg = tmp_path / "solo.toml"
    cfg.write_text(
        """
[[job]]
name = "solo"
args = { script = "scripts/solo.py" }
schedule_type = "once"
""",
        encoding="utf-8",
    )

    real_load = rs.load_jobs_from_toml

    def wrap(p):
        jobs = real_load(p)
        jobs[0].schedule.next_run_at = NOW - timedelta(seconds=1)
        return jobs

    monkeypatch.setattr(rs, "load_jobs_from_toml", wrap)

    rs.run_scheduler_tick_once(
        cfg,
        now=NOW,
        subprocess_run=lambda *_a, **_k: SimpleNamespace(returncode=0, stdout="", stderr=""),
        utcnow=_utc,
    )


def test_tick_does_not_invoke_run_scheduler_loop(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import scripts.run_scheduler as rs

    def crash_loop(*args, **kwargs):  # noqa: ARG001
        raise AssertionError("run_scheduler_loop must not run in bounded tick contract")

    monkeypatch.setattr(rs, "run_scheduler_loop", crash_loop)

    cfg = tmp_path / "solo2.toml"
    cfg.write_text(
        """
[[job]]
name = "solo2"
args = { script = "scripts/solo.py" }
schedule_type = "once"
""",
        encoding="utf-8",
    )

    real_load = rs.load_jobs_from_toml

    def wrap(p):
        jobs = real_load(p)
        jobs[0].schedule.next_run_at = NOW - timedelta(seconds=1)
        return jobs

    monkeypatch.setattr(rs, "load_jobs_from_toml", wrap)

    summary = rs.run_scheduler_tick_once(
        cfg,
        now=NOW,
        subprocess_run=lambda *_a, **_k: SimpleNamespace(returncode=0, stdout="", stderr=""),
        utcnow=_utc,
    )
    assert summary.dispatched == 1


def test_scheduler_tick_summary_dataclass_defaults() -> None:
    import scripts.run_scheduler as rs

    s = rs.SchedulerTickSummary()
    assert s.loaded == 0
    assert s.due == 0
