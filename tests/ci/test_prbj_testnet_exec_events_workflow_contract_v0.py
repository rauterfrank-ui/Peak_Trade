"""Static contract for PR-BJ Kraken testnet exec-events workflow cron gate.

Parses workflow YAML as UTF-8 text only. Never dispatches workflows, never
reads secret values, and never touches runtime/testnet execution paths.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

WORKFLOW = Path(".github/workflows/prbj-testnet-exec-events.yml")


def _workflow() -> dict[str, Any]:
    assert WORKFLOW.exists()
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _trigger_section(data: dict[str, Any]) -> dict[str, Any]:
    triggers = data.get("on")
    if triggers is None:
        triggers = data.get(True)
    assert isinstance(triggers, dict)
    return triggers


def _run_testnet_job() -> dict[str, Any]:
    jobs = _workflow().get("jobs")
    assert isinstance(jobs, dict)
    job = jobs.get("run-testnet")
    assert isinstance(job, dict)
    return job


def test_workflow_has_schedule_and_workflow_dispatch_triggers() -> None:
    triggers = _trigger_section(_workflow())

    assert "workflow_dispatch" in triggers

    schedule = triggers.get("schedule")
    assert isinstance(schedule, list)
    assert len(schedule) >= 1
    assert any(isinstance(entry, dict) and "cron" in entry for entry in schedule)


def test_workflow_schedule_requires_kraken_testnet_cron_enabled_var() -> None:
    text = _workflow_text()

    assert "KRAKEN_TESTNET_CRON_ENABLED" in text
    assert "vars.KRAKEN_TESTNET_CRON_ENABLED == 'true'" in text
    assert "github.event_name != 'schedule'" in text


def test_workflow_job_gate_preserves_manual_dispatch() -> None:
    job_if = _run_testnet_job().get("if")
    assert isinstance(job_if, str)

    assert "github.event_name != 'schedule'" in job_if
    assert "workflow_dispatch" not in job_if.lower()
    assert "KRAKEN_TESTNET_CRON_ENABLED" in job_if


def test_workflow_references_kraken_testnet_secrets_without_exposing_values() -> None:
    text = _workflow_text()

    assert "${{ secrets.KRAKEN_TESTNET_API_KEY }}" in text
    assert "${{ secrets.KRAKEN_TESTNET_API_SECRET }}" in text
    assert "sk-" not in text
    assert "AKIA" not in text


def test_workflow_does_not_introduce_live_authority_or_aws_paths() -> None:
    lowered = _workflow_text().lower()

    forbidden = (
        "live_authority",
        "live_enabled=true",
        "armed=true",
        "s3://",
        "ssh ",
        "openai_api_key",
        "anthropic",
        "promptfoo",
        "master_v2",
        "double_play",
    )

    for term in forbidden:
        assert term not in lowered


def test_workflow_permissions_remain_read_only_contents() -> None:
    permissions = _workflow().get("permissions")
    assert isinstance(permissions, dict)
    assert permissions.get("contents") == "read"
