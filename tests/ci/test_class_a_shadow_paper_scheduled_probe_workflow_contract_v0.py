"""Contract tests for the Class-A shadow paper scheduled probe workflow.

These tests parse the workflow YAML as a static contract only.
They never dispatch the workflow and never touch secrets or providers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

WORKFLOW = Path(".github/workflows/class-a-shadow-paper-scheduled-probe-v1.yml")


def _workflow() -> dict[str, Any]:
    assert WORKFLOW.exists()
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _trigger_section(data: dict[str, Any]) -> dict[str, Any]:
    """GitHub workflows use `on:` which PyYAML 1.1 may parse as bool key True."""
    triggers = data.get("on")
    if triggers is None:
        triggers = data.get(True)
    assert isinstance(triggers, dict)
    return triggers


def _jobs(data: dict[str, Any]) -> dict[str, Any]:
    jobs = data.get("jobs")
    assert isinstance(jobs, dict)
    return jobs


def _single_job(jobs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    assert len(jobs) == 1
    job_id, job_body = next(iter(jobs.items()))
    assert isinstance(job_body, dict)
    return job_id, job_body


def test_workflow_exists_parseable_and_named() -> None:
    data = _workflow()
    assert data.get("name") == "Class A Shadow Paper Scheduled Probe v1"


def test_workflow_has_dispatch_and_schedule_triggers() -> None:
    triggers = _trigger_section(_workflow())

    assert "workflow_dispatch" in triggers

    schedule = triggers.get("schedule")
    assert isinstance(schedule, list)
    assert len(schedule) >= 1
    assert any(isinstance(entry, dict) and "cron" in entry for entry in schedule)


def test_workflow_permissions_are_read_only_contents() -> None:
    data = _workflow()
    permissions = data.get("permissions")

    assert permissions != "write-all"
    assert isinstance(permissions, dict)
    assert permissions.get("contents") == "read"

    forbidden_write_scopes = (
        "actions",
        "checks",
        "deployments",
        "issues",
        "packages",
        "pull-requests",
        "repository-projects",
        "security-events",
        "statuses",
    )
    for scope in forbidden_write_scopes:
        assert permissions.get(scope) != "write"


def test_workflow_has_non_writing_contents_permissions_only() -> None:
    """No contents: write at workflow scope."""
    text = _workflow_text()
    lowered = text.lower()
    assert "contents: write" not in lowered


def test_workflow_defensive_live_env_strings_on_job() -> None:
    _, job = _single_job(_jobs(_workflow()))

    env = job.get("env")
    assert isinstance(env, dict)
    assert env.get("PEAK_TRADE_LIVE_ENABLED") == "false"
    assert env.get("PEAK_TRADE_LIVE_ARMED") == "false"


def test_workflow_schedule_gate_mentions_var_and_manual_dispatch_in_source() -> None:
    text = _workflow_text()

    assert "CLASS_A_SHADOW_PAPER_SCHEDULE_ENABLED" in text
    assert "workflow_dispatch" in text


def test_workflow_has_cancel_in_progress_concurrency() -> None:
    data = _workflow()
    conc = data.get("concurrency")
    assert isinstance(conc, dict)
    assert conc.get("cancel-in-progress") is True


def test_workflow_does_not_reference_github_secrets() -> None:
    text = _workflow_text()

    assert "${{ secrets." not in text


def test_workflow_run_surface_is_shadow_paper_probe_only() -> None:
    text = _workflow_text()

    assert "scripts.run_shadow_paper_session" in text or "scripts/run_shadow_paper_session" in text


def test_workflow_avoids_obvious_live_order_execution_provider_terms() -> None:
    lowered = _workflow_text().lower()

    forbidden = (
        "live_authorization",
        "place_order",
        "submit_order",
        "exchange_order",
        "testnet_order",
        "${{ secrets.",
        "armed=true",
        "live_enabled=true",
        "confirm_token_env",
    )

    for term in forbidden:
        assert term not in lowered


def test_workflow_job_has_reasonable_timeout() -> None:
    _, job = _single_job(_jobs(_workflow()))

    timeout = job.get("timeout-minutes")
    assert isinstance(timeout, int)
    assert 1 <= timeout <= 180


def test_workflow_uploads_probe_artifacts_without_readiness_claim() -> None:
    text = _workflow_text()

    assert "actions/upload-artifact@v4" in text
    assert "out/ops/gh_class_a_shadow_paper" in text

    lowered = text.lower()
    assert "futures_ready" not in lowered
    assert "live_ready" not in lowered
    assert "gate_passed" not in lowered
