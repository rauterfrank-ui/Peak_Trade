"""Contract tests for the CI scheduled paper + export smoke orchestrator workflow.

These tests parse the workflow YAML as a static contract only.
They never dispatch workflows, never access secret values, and never run scripts.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

WORKFLOW = Path(".github/workflows/ci-scheduled-paper-and-export-smoke.yml")

_ALLOWED_SECRETS = frozenset(
    {
        "PT_RCLONE_CONF_B64",
        "PT_EXPORT_REMOTE",
        "PT_EXPORT_PREFIX",
    }
)

_SECRETS_TOKEN_RE = re.compile(r"\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*\}\}")


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


def _secret_names_in_text(text: str) -> set[str]:
    return set(_SECRETS_TOKEN_RE.findall(text))


def test_workflow_exists_parseable_and_named() -> None:
    data = _workflow()
    assert data.get("name") == "CI / Scheduled Paper + Export Smoke"


def test_workflow_has_dispatch_and_schedule_triggers() -> None:
    triggers = _trigger_section(_workflow())

    assert "workflow_dispatch" in triggers

    schedule = triggers.get("schedule")
    assert isinstance(schedule, list)
    assert len(schedule) >= 1
    assert any(isinstance(entry, dict) and "cron" in entry for entry in schedule)


def test_workflow_permissions_allow_dispatch_and_read_contents() -> None:
    data = _workflow()
    permissions = data.get("permissions")

    assert permissions != "write-all"
    assert isinstance(permissions, dict)
    assert permissions.get("actions") == "write"
    assert permissions.get("contents") == "read"
    assert set(permissions.keys()) <= {"actions", "contents"}

    extra_write_scopes = (
        "checks",
        "deployments",
        "issues",
        "packages",
        "pull-requests",
        "repository-projects",
        "security-events",
        "statuses",
    )
    for scope in extra_write_scopes:
        assert permissions.get(scope) != "write"


def test_workflow_has_cancel_in_progress_concurrency() -> None:
    data = _workflow()
    conc = data.get("concurrency")
    assert isinstance(conc, dict)
    assert conc.get("cancel-in-progress") is True


def test_workflow_jobs_have_expected_timeouts() -> None:
    jobs = _jobs(_workflow())
    assert len(jobs) >= 2
    for job_body in jobs.values():
        assert isinstance(job_body, dict)
        timeout = job_body.get("timeout-minutes")
        assert isinstance(timeout, int)
        assert 30 <= timeout <= 120


def test_workflow_schedule_gate_vars_present() -> None:
    text = _workflow_text()
    assert "vars.PT_SCHEDULED_PAPER_TESTS_ENABLED" in text
    assert "vars.PT_SCHEDULED_EXPORT_VERIFY_ENABLED" in text


def test_workflow_only_uses_allowlisted_secrets() -> None:
    names = _secret_names_in_text(_workflow_text())
    assert names == _ALLOWED_SECRETS


def test_workflow_export_secret_placeholder_names_in_env() -> None:
    text = _workflow_text()
    assert "${{ secrets.PT_RCLONE_CONF_B64 }}" in text
    assert "${{ secrets.PT_EXPORT_REMOTE }}" in text
    assert "${{ secrets.PT_EXPORT_PREFIX }}" in text


def test_workflow_runs_guardrails_before_each_dispatch() -> None:
    text = _workflow_text()
    guard = "bash scripts/ci/scheduled_guardrails.sh"
    dispatch_token = "gh workflow run"

    assert text.count(guard) >= 2
    chunks = text.split(dispatch_token)
    assert len(chunks) >= 3
    for chunk in chunks[:-1]:
        assert guard in chunk


def test_workflow_dispatches_expected_downstream_workflows() -> None:
    text = _workflow_text()
    assert 'gh workflow run "paper-tests-audit-evidence"' in text
    assert 'gh workflow run "CI / Export Pack Download + Verify"' in text


def test_workflow_dispatch_steps_use_github_token() -> None:
    text = _workflow_text()
    assert "${{ github.token }}" in text


def test_workflow_avoids_readiness_promotion_claim_tokens() -> None:
    lowered = _workflow_text().lower()
    assert "live_ready" not in lowered
    assert "futures_ready" not in lowered
    assert "gate_passed" not in lowered
