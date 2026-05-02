"""Contract tests for the CI export-pack download/verify workflow.

These tests parse the workflow YAML as a static contract only.
They never dispatch the workflow, never access secrets, never run rclone,
and never touch remote export-pack storage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

WORKFLOW = Path(".github/workflows/ci-export-pack-download-verify.yml")


def _workflow() -> dict[str, Any]:
    assert WORKFLOW.exists()
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _jobs(data: dict[str, Any]) -> dict[str, Any]:
    jobs = data.get("jobs")
    assert isinstance(jobs, dict)
    return jobs


def _export_verify_job(data: dict[str, Any]) -> dict[str, Any]:
    job = _jobs(data).get("export-pack-verify")
    assert isinstance(job, dict)
    return job


def _all_steps(data: dict[str, Any]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for job in _jobs(data).values():
        assert isinstance(job, dict)
        job_steps = job.get("steps", [])
        assert isinstance(job_steps, list)
        for step in job_steps:
            assert isinstance(step, dict)
            steps.append(step)
    return steps


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_identity_and_triggers_are_stable() -> None:
    data = _workflow()

    assert data.get("name") == "CI / Export Pack Download + Verify"

    on = data.get("on")
    assert isinstance(on, dict)
    assert "workflow_dispatch" in on
    assert "pull_request" in on
    assert "schedule" not in on


def test_workflow_job_permissions_do_not_grant_write_all() -> None:
    data = _workflow()
    job = _export_verify_job(data)
    permissions = job.get("permissions")

    assert permissions != "write-all"
    assert isinstance(permissions, dict)

    forbidden_write_scopes = {
        "actions",
        "checks",
        "contents",
        "deployments",
        "issues",
        "packages",
        "pull-requests",
        "repository-projects",
        "security-events",
        "statuses",
    }

    for scope in forbidden_write_scopes:
        assert permissions.get(scope) != "write"


def test_workflow_uses_expected_pinned_core_actions_only() -> None:
    data = _workflow()
    uses_values = [step["uses"] for step in _all_steps(data) if isinstance(step.get("uses"), str)]

    assert "actions/checkout@v5" in uses_values
    assert any(value.startswith("actions/setup-python@v") for value in uses_values)

    for value in uses_values:
        assert "@" in value
        assert not value.endswith("@main")
        assert not value.endswith("@master")


def test_workflow_contains_guardrails_before_rclone_steps() -> None:
    text = _workflow_text()

    assert "scheduled_guardrails.sh" in text
    assert "rclone" in text

    guardrail_index = text.index("scheduled_guardrails.sh")
    rclone_index = text.index("rclone")
    assert guardrail_index < rclone_index


def test_workflow_remote_rclone_copy_is_dispatch_only() -> None:
    text = _workflow_text()

    assert "workflow_dispatch" in text
    assert "rclone copy" in text
    assert "github.event_name == 'workflow_dispatch'" in text


def test_workflow_does_not_include_live_testnet_or_trading_authority_terms() -> None:
    text = _workflow_text().lower()

    forbidden_terms = [
        "live_authorization",
        "place_order",
        "create_order",
        "submit_order",
        "exchange_order",
        "testnet_order",
        "armed=true",
        "confirm_token",
    ]

    for term in forbidden_terms:
        assert term not in text


def test_workflow_has_expected_export_paths_and_manifest_contract() -> None:
    text = _workflow_text()

    assert "out/ops/exports_ci" in text
    assert "manifest.json" in text
    assert "SHA256SUMS.stable.txt" in text
    assert "sha256sum -c" in text
