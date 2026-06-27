"""Static contract for PR-BJ testnet exec-events workflow (manual-only dispatch).

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


def test_workflow_has_workflow_dispatch_only_no_schedule() -> None:
    """PRBJ Option B: schedule removed; workflow_dispatch retained."""
    triggers = _trigger_section(_workflow())

    assert "workflow_dispatch" in triggers
    assert "schedule" not in triggers
    assert "schedule:" not in _workflow_text()


def test_workflow_job_fail_closed_after_kraken_decommission() -> None:
    job_if = _run_testnet_job().get("if")
    assert job_if == "${{ false }}"


def test_workflow_does_not_reference_kraken_testnet_secrets() -> None:
    text = _workflow_text()

    assert "KRAKEN_TESTNET_API_KEY" not in text
    assert "KRAKEN_TESTNET_API_SECRET" not in text
    assert "secrets.KRAKEN" not in text
    assert "sk-" not in text
    assert "AKIA" not in text


def test_workflow_documents_kraken_decommission_placeholder() -> None:
    text = _workflow_text()

    assert "kraken decommissioned" in text.lower()
    assert "okx eea pending" in text.lower()


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
