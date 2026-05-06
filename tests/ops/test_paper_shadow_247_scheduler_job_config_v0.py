"""Scheduler job surface for Paper-Shadow 247 read-only preflight reporter."""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parents[2]
JOBS_CONFIG = REPO_ROOT / "config" / "scheduler" / "jobs.toml"


def _paper_shadow_job() -> dict:
    payload = tomllib.loads(JOBS_CONFIG.read_text(encoding="utf-8"))
    jobs = payload.get("job", [])
    return next(
        job for job in jobs if job.get("name") == "paper_shadow_247_paper_only_preflight_status_v0"
    )


def test_paper_shadow_247_scheduler_job_is_present_and_non_authorizing() -> None:
    target = _paper_shadow_job()

    assert target["enabled"] is True
    assert target["schedule_type"] == "once"
    assert target["paper_only"] is True
    assert target["dry_run_visible"] is True
    assert target["command"] == "python"
    assert target["args"]["script"] == "scripts/ops/report_paper_shadow_247_preflight_status.py"
    assert target["args"]["json"] is True

    for key in (
        "testnet_authorized",
        "live_authorized",
        "broker_authorized",
        "exchange_authorized",
        "order_submission_authorized",
    ):
        assert target[key] is False


def test_paper_shadow_247_scheduler_job_command_is_status_only() -> None:
    command = _paper_shadow_job()["command"].lower()
    args = _paper_shadow_job()["args"]

    assert "report_paper_shadow_247_preflight_status.py" in args["script"].lower()
    assert "run_scheduler.py" not in command
    assert "run_scheduler.py" not in args["script"].lower()
    assert "p7_ctl.py run-shadow" not in command

    combined = (command + " " + args["script"]).lower()
    assert "--live" not in combined
    assert "--testnet" not in combined
    assert "submit_order" not in combined
    assert "real_order" not in combined
    assert "broker_connect" not in combined
    assert "exchange_connect" not in combined
    assert "api_key" not in combined
    assert "secret" not in combined
